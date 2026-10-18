"""Bounded Gemini adapter; SDK proposes functions, lab_runtime executes them.

No request is made by import or construction. Only synthetic classroom data
belongs here. This is trusted Python application code, not a security sandbox.
Full native model Content (including thought signatures) stays private and is
replayed verbatim. Only function proposals and the report enter the lab trace.
"""

from copy import deepcopy
import json
import re
from time import perf_counter

from lab_runtime import ModelReply, ToolCall, REPORT_KEYS, HYPOTHESES, tool_schemas


DEFAULT_MODEL = "gemini-3.5-flash-lite"
MAX_REQUESTS = 5  # Per instance, INCLUDING new investigations and failed calls.
TIMEOUT_MS = 30_000
MAX_OUTPUT_TOKENS = 2048

_REPORT = {
    "name": "submit_report",
    "description": (
        "Finish with a report based on returned evidence. This is an output "
        "protocol, not an action. Use it alone, never with another function."
    ),
    "parameters_json_schema": {
        "type": "object",
        "properties": {
            "service_id": {"type": "string", "enum": ["demo-api"]},
            "hypothesis": {"type": "string", "enum": list(HYPOTHESES)},
            "evidence_ids": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string"},
            "next_check": {"type": "string"},
        },
        "required": sorted(REPORT_KEYS),
        "additionalProperties": False,
    },
}

_PROTOCOL = (
    "\nTransport protocol: propose read tools to collect the evidence, then "
    "finish by calling submit_report with the report fields as its arguments. "
    "submit_report is the final output, not an external action. Never combine "
    "submit_report and read calls in one response. Do not emit a plain-text "
    "report. You have at most 4 read calls and 5 model requests. You may request "
    "independent reads together. A missing record is data, not permission to "
    "invent evidence. Keep the report concise."
)


class GeminiProviderError(RuntimeError):
    """A public error contains a fixed code only, never SDK text or credentials."""


def _json_copy(value, limit=64_000):
    encoded = json.dumps(value, ensure_ascii=True, allow_nan=False)
    if len(encoded) > limit:
        raise ValueError("payload_too_large")
    return json.loads(encoded)


def _enum_value(value):
    return getattr(value, "value", value)


def _error_code(error):
    """Class/status inspection only: never inspect or return exception text."""
    code = getattr(error, "code", None)
    if type(code) is not int:
        code = getattr(getattr(error, "response", None), "status_code", None)
    if type(code) is int:
        if code in (401, 403):
            return "access_denied"
        if code == 404:
            return "model_unavailable"
        if code == 429:
            return "rate_limited"
        if code == 400:
            return "request_rejected"
        if 500 <= code <= 599:
            return "service_unavailable"
    if isinstance(error, TimeoutError) or any(
        cls.__name__ in {"TimeoutException", "ReadTimeout", "ConnectTimeout",
                         "WriteTimeout", "PoolTimeout"}
        for cls in type(error).__mro__
    ):
        return "timeout"
    return "connection_or_sdk_error"


class GeminiProvider:
    mode = "LIVE_GEMINI"
    label = "Live Gemini API; local read-only tools; limited application gate"

    def __init__(self, api_key, model=DEFAULT_MODEL, extra_instruction="", *, client=None):
        self.last_error_code = None
        self._closed = False
        self._requests = 0
        self._attempts = []
        self._native_history = []
        self._neutral_prefix = []
        self._pending_content = None
        self._pending_calls = []
        self._native_ids = {}
        if not isinstance(api_key, str) or not api_key.strip() or len(api_key) > 512:
            self._fail("invalid_key_input")
        if (type(model) is not str or not re.fullmatch(r"gemini-[a-zA-Z0-9.-]{1,90}", model)
                or type(extra_instruction) is not str or len(extra_instruction) > 1000):
            self._fail("invalid_configuration")
        self.model = model
        self.extra_instruction = extra_instruction
        if client is None:
            try:
                from google import genai
                # Explicit Developer API; no automatic retry or credential fallback.
                client = genai.Client(api_key=api_key, vertexai=False, http_options={
                    "timeout": TIMEOUT_MS,
                    "retry_options": {"attempts": 1},
                })
            except ImportError:
                self._fail("sdk_missing")
            except Exception:
                self._fail("client_setup_failed")
        self._client = client

    def __repr__(self):
        return f"GeminiProvider(mode={self.mode!r}, requests={self._requests}, closed={self._closed})"

    def _fail(self, code):
        self.last_error_code = code
        raise GeminiProviderError(code) from None

    def close(self):
        """Release the client; never reset the budget or print a close exception."""
        if not self._closed:
            self._closed = True
            try:
                self._client.close()
            except Exception:
                self.last_error_code = "client_close_failed"
            self._native_history = []
            self._neutral_prefix = []
            self._pending_content = None
            self._pending_calls = []
            self._native_ids = {}

    def telemetry(self):
        """Observed token metadata, not an invoice or proof of task quality.

        Missing metadata stays None. Cached tokens are a subset of prompt tokens;
        thinking tokens are reported separately. Do not sum every field as cost.
        Request count includes failures; it is not the runtime's provider-turn count.
        """
        return {
            "mode": self.mode,
            "model": self.model,
            "requests_attempted": self._requests,
            "request_limit": MAX_REQUESTS,
            "requests_remaining": MAX_REQUESTS - self._requests,
            "closed": self._closed,
            "last_error_code": self.last_error_code,
            "attempts": deepcopy(self._attempts),
        }

    def _prepare_history(self, messages):
        if type(messages) is not list or not messages:
            self._fail("invalid_history")
        try:
            messages = _json_copy(messages)
        except (TypeError, ValueError, OverflowError):
            self._fail("invalid_history")
        first = messages[0]
        if type(first) is not dict or set(first) != {"role", "content"} or first["role"] != "user":
            self._fail("invalid_history")
        context = first["content"]
        if (type(context) is not dict or set(context) != {"service_id", "symptom", "now", "max_age_s"}
                or context["service_id"] != "demo-api"
                or type(context["symptom"]) is not str or not 0 < len(context["symptom"]) <= 500
                or type(context["now"]) is not int or type(context["max_age_s"]) is not int
                or context["max_age_s"] < 0):
            self._fail("invalid_history")
        if len(messages) == 1:
            # A new investigation resets its conversation, NEVER the request budget.
            self._native_history = [{"role": "user", "parts": [{"text": json.dumps(context)}]}]
            self._pending_content = None
            self._pending_calls = []
            self._native_ids = {}
        else:
            n = len(self._neutral_prefix)
            if (self._pending_content is None or messages[:n] != self._neutral_prefix
                    or len(messages) != n + 1 + len(self._pending_calls)):
                self._fail("invalid_history")
            expected = {"role": "assistant", "tool_calls": deepcopy(self._pending_calls)}
            if messages[n] != expected:
                self._fail("invalid_history")
            parts = []
            for call, message in zip(self._pending_calls, messages[n + 1:]):
                if (type(message) is not dict
                        or set(message) != {"role", "tool_call_id", "name", "content"}
                        or message["role"] != "tool" or message["tool_call_id"] != call["id"]
                        or message["name"] != call["name"] or type(message["content"]) is not dict):
                    self._fail("invalid_history")
                fr = {"name": call["name"], "response": deepcopy(message["content"])}
                native_id = self._native_ids[call["id"]]
                if native_id is not None:
                    fr["id"] = native_id
                parts.append({"function_response": fr})
            # Preserve the entire original Content, not reconstructed function parts.
            self._native_history.extend([self._pending_content, {"role": "user", "parts": parts}])
            self._pending_content = None
            self._pending_calls = []
        self._neutral_prefix = deepcopy(messages)

    def _parse_response(self, response):
        feedback = getattr(response, "prompt_feedback", None)
        blocked = _enum_value(getattr(feedback, "block_reason", None))
        if blocked not in (None, "", "BLOCK_REASON_UNSPECIFIED"):
            self._fail("model_refused")
        candidates = getattr(response, "candidates", None)
        if not candidates or len(candidates) != 1:
            self._fail("empty_or_ambiguous_response")
        candidate = candidates[0]
        reason = _enum_value(getattr(candidate, "finish_reason", None))
        if reason == "MAX_TOKENS":
            self._fail("output_limit")
        if reason in {"SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII"}:
            self._fail("model_refused")
        if reason != "STOP":
            self._fail("invalid_model_response")
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None)
        if not parts or getattr(content, "role", None) != "model":
            self._fail("empty_or_ambiguous_response")
        calls, native_ids = [], {}
        for part in parts:
            fc = getattr(part, "function_call", None)
            if fc is None:
                continue  # Do not expose text/thought parts in the classroom trace.
            name, args, native_id = getattr(fc, "name", None), getattr(fc, "args", None), getattr(fc, "id", None)
            if (type(name) is not str or not 0 < len(name) <= 80 or type(args) is not dict
                    or (native_id is not None and (type(native_id) is not str or not 0 < len(native_id) <= 80))):
                self._fail("invalid_function_call")
            if native_id is not None and native_id in native_ids.values():
                self._fail("invalid_function_call")
            try:
                args = _json_copy(args, 8000)
            except (TypeError, ValueError, OverflowError):
                self._fail("invalid_function_call")
            ident = f"gemini-{self._requests}-{len(calls) + 1}"
            calls.append(ToolCall(ident, name, args))
            native_ids[ident] = native_id
        if not calls:
            self._fail("no_function_call")
        reports = [call for call in calls if call.name == "submit_report"]
        if reports:
            if len(calls) != 1:
                self._fail("mixed_report_and_tools")
            # The application gate, not Gemini's schema, validates the report.
            return ModelReply([], deepcopy(reports[0].arguments))
        self._pending_content = deepcopy(content)
        self._pending_calls = [{"id": c.id, "name": c.name, "arguments": deepcopy(c.arguments)} for c in calls]
        self._native_ids = native_ids
        return ModelReply(calls)

    def next_turn(self, *, messages, tools, instructions):
        self.last_error_code = None
        if self._closed:
            self._fail("client_closed")
        if self._requests >= MAX_REQUESTS:
            self._fail("request_budget_exhausted")
        if tools != tool_schemas() or type(instructions) is not str or len(instructions) > 6000:
            self._fail("invalid_configuration")
        self._prepare_history(messages)
        declarations = [{"name": item["name"], "description": item["description"],
                         "parameters_json_schema": deepcopy(item["parameters"])} for item in tools]
        declarations.append(deepcopy(_REPORT))
        config = {
            "system_instruction": instructions + _PROTOCOL + "\n" + self.extra_instruction,
            "tools": [{"function_declarations": declarations}],
            "automatic_function_calling": {"disable": True},
            "tool_config": {"function_calling_config": {"mode": "ANY"}},
            "candidate_count": 1,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "thinking_config": {"thinking_level": "LOW", "include_thoughts": False},
        }
        self._requests += 1
        started = perf_counter()
        attempt = {"request": self._requests, "latency_ms": None, "outcome": "error",
                   "prompt_tokens": None, "candidate_tokens": None, "thinking_tokens": None,
                   "cached_prompt_tokens": None, "total_tokens": None}
        self._attempts.append(attempt)
        try:
            response = self._client.models.generate_content(
                model=self.model, contents=deepcopy(self._native_history), config=config)
        except Exception as error:
            attempt["latency_ms"] = round((perf_counter() - started) * 1000, 1)
            self._fail(_error_code(error))
        attempt["latency_ms"] = round((perf_counter() - started) * 1000, 1)
        usage = getattr(response, "usage_metadata", None)
        for public, field in (("prompt_tokens", "prompt_token_count"),
                              ("candidate_tokens", "candidates_token_count"),
                              ("thinking_tokens", "thoughts_token_count"),
                              ("cached_prompt_tokens", "cached_content_token_count"),
                              ("total_tokens", "total_token_count")):
            value = getattr(usage, field, None)
            if type(value) is int and value >= 0:
                attempt[public] = value
        reply = self._parse_response(response)
        attempt["outcome"] = "report" if reply.report is not None else "tool_proposal"
        return reply

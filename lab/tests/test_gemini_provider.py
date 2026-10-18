"""No API credentials or networking: the client boundary is a deterministic double.

The optional real-SDK contract tests also run locally: real SDK objects are
constructed/serialized, but generate_content is still replaced by a fake client.
"""

from copy import deepcopy
from base64 import b64encode
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gemini_provider import GeminiProvider, GeminiProviderError, MAX_REQUESTS, DEFAULT_MODEL
from lab_runtime import INSTRUCTIONS, load_case, run_investigation, tool_schemas
from solutions import freshness_policy


def messages(case_id="healthy"):
    case = load_case(case_id)
    return [{"role": "user", "content": {key: case[key] for key in (
        "service_id", "symptom", "now", "max_age_s")}}]


def report(case_id="healthy"):
    case = load_case(case_id)
    return {"service_id": "demo-api", "hypothesis": "no_latency_breach",
            "evidence_ids": [case["metrics"]["id"], case["runbook"]["id"]],
            "summary": "Recorded p95 is 180 ms for the supplied 60-second window.",
            "next_check": "Obtain a further read-only measurement."}


def part(name="get_metrics", args=None, native_id=None, signature=None):
    return NS(function_call=NS(name=name, args={"service_id": "demo-api"} if args is None else args,
                               id=native_id), thought_signature=signature)


def response(parts=None, finish="STOP", usage=True):
    return NS(candidates=[NS(content=NS(role="model", parts=parts if parts is not None else [part()]),
                             finish_reason=finish)], prompt_feedback=None,
              usage_metadata=NS(prompt_token_count=100, candidates_token_count=30,
                                thoughts_token_count=10, cached_content_token_count=20,
                                total_token_count=140) if usage else None)


class FakeClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []
        self.models = self
        self.closed = False

    def generate_content(self, **kwargs):
        self.requests.append(deepcopy(kwargs))
        reply = self.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return reply

    def close(self):
        self.closed = True


def next_turn(provider, history=None):
    return provider.next_turn(messages=messages() if history is None else history,
                              tools=tool_schemas(), instructions=INSTRUCTIONS)


def add_results(history, calls):
    history = deepcopy(history)
    history.append({"role": "assistant", "tool_calls": [
        {"id": call.id, "name": call.name, "arguments": deepcopy(call.arguments)} for call in calls]})
    for call in calls:
        history.append({"role": "tool", "tool_call_id": call.id, "name": call.name,
                        "content": {"status": "ok", "records": []}})
    return history


class AdapterTests(unittest.TestCase):
    def provider(self, *replies):
        client = FakeClient(replies)
        return GeminiProvider("fake-test-key-never-send", client=client), client

    def assertCode(self, provider, code, history=None):
        with self.assertRaises(GeminiProviderError) as context:
            next_turn(provider, history)
        self.assertEqual(str(context.exception), code)
        self.assertEqual(provider.last_error_code, code)

    def test_constructor_and_telemetry_make_no_request(self):
        p, c = self.provider()
        self.assertEqual(p.mode, "LIVE_GEMINI")
        self.assertEqual(p.telemetry()["requests_attempted"], 0)
        self.assertEqual(c.requests, [])
        self.assertNotIn("fake-test-key", repr(p))

    def test_manual_function_execution_config_and_output_limit(self):
        p, c = self.provider(response())
        reply = next_turn(p)
        self.assertEqual(reply.tool_calls[0].name, "get_metrics")
        cfg = c.requests[0]["config"]
        self.assertEqual(cfg["automatic_function_calling"], {"disable": True})
        self.assertEqual(cfg["tool_config"]["function_calling_config"]["mode"], "ANY")
        self.assertEqual(cfg["max_output_tokens"], 2048)
        self.assertEqual(cfg["candidate_count"], 1)
        self.assertEqual(cfg["thinking_config"]["include_thoughts"], False)
        self.assertEqual(len(cfg["tools"][0]["function_declarations"]), 4)

    def test_parallel_calls_ids_and_full_native_signature_preserved(self):
        source = response([NS(text="private thought", thought=True, function_call=None),
                           part("get_metrics", native_id="m", signature=b"opaque-signature"),
                           part("get_runbook", native_id="r")])
        p, c = self.provider(source, response([part("submit_report", report())]))
        calls = next_turn(p).tool_calls
        self.assertEqual(len(set(call.id for call in calls)), 2)
        final = next_turn(p, add_results(messages(), calls))
        self.assertEqual(final.report, report())
        native = c.requests[1]["contents"][1]
        self.assertEqual(native.parts[1].thought_signature, b"opaque-signature")
        self.assertEqual(native.parts[0].text, "private thought")
        results = c.requests[1]["contents"][2]["parts"]
        self.assertEqual([item["function_response"]["id"] for item in results], ["m", "r"])
        self.assertNotIn("private thought", str(final))
        self.assertNotIn("opaque-signature", str(p.telemetry()))

    def test_missing_native_id_not_invented_in_provider_response(self):
        p, c = self.provider(response(), response([part("submit_report", report())]))
        calls = next_turn(p).tool_calls
        next_turn(p, add_results(messages(), calls))
        self.assertNotIn("id", c.requests[1]["contents"][2]["parts"][0]["function_response"])

    def test_mutation_of_returned_call_does_not_mutate_history(self):
        p, _ = self.provider(response())
        reply = next_turn(p)
        reply.tool_calls[0].arguments["service_id"] = "other"
        self.assertCode(p, "invalid_history", add_results(messages(), reply.tool_calls))

    def test_complete_runtime_cycle_three_local_reads(self):
        p, c = self.provider(response([part("get_logs"), part("get_metrics"), part("get_runbook")]),
                             response([part("submit_report", report())]))
        result = run_investigation("healthy", p, lambda *_: True)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["tool_calls"], 3)
        self.assertEqual(result["decision"]["status"], "evidence_gate_passed")
        self.assertEqual(len(c.requests), 2)

    def test_stale_model_report_rejected_by_strict_application_gate(self):
        p, _ = self.provider(response([part("get_metrics"), part("get_runbook")]),
                             response([part("submit_report", report("stale"))]))
        result = run_investigation("stale", p, freshness_policy)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["decision"]["status"], "needs_more_data")
        self.assertEqual(result["decision"]["reasons"], ["freshness_policy_not_satisfied"])

    def test_missing_metrics_does_not_become_evidence(self):
        missing_report = report()
        missing_report["hypothesis"] = "insufficient_evidence"
        missing_report["evidence_ids"] = [load_case("missing")["runbook"]["id"]]
        p, _ = self.provider(response([part("get_metrics"), part("get_runbook")]),
                             response([part("submit_report", missing_report)]))
        result = run_investigation("missing", p, freshness_policy)
        self.assertEqual(result["decision"]["status"], "needs_more_data")
        self.assertEqual([record["kind"] for record in result["evidence"]], ["runbook"])

    def test_unknown_tool_is_proposed_but_rejected_by_application(self):
        p, c = self.provider(response([part("delete_everything")]))
        result = run_investigation("healthy", p, lambda *_: True)
        self.assertEqual(result["status"], "tool_rejected")
        self.assertEqual(len(c.requests), 1)

    def test_extra_tool_argument_rejected_by_application(self):
        p, _ = self.provider(response([part(args={"service_id": "demo-api", "shell": "bad"})]))
        self.assertEqual(run_investigation("healthy", p, lambda *_: True)["status"], "tool_rejected")

    def test_submit_report_never_executes_tool(self):
        p, _ = self.provider(response([part("submit_report", report())]))
        result = run_investigation("healthy", p, lambda *_: True)
        self.assertEqual(result["tool_calls"], 0)
        self.assertEqual(result["decision"]["status"], "blocked")

    def test_malformed_report_is_application_gate_responsibility(self):
        p, _ = self.provider(response([part("submit_report", {"summary": "incomplete"})]))
        result = run_investigation("healthy", p, lambda *_: True)
        self.assertEqual(result["decision"]["reasons"], ["invalid_report_schema"])

    def test_mixed_report_and_tools_rejected(self):
        p, _ = self.provider(response([part(), part("submit_report", report())]))
        self.assertCode(p, "mixed_report_and_tools")

    def test_budget_survives_new_investigations(self):
        p, c = self.provider(*[response([part("submit_report", report())]) for _ in range(MAX_REQUESTS)])
        for _ in range(MAX_REQUESTS):
            next_turn(p)
        self.assertCode(p, "request_budget_exhausted")
        self.assertEqual(len(c.requests), MAX_REQUESTS)
        self.assertEqual(p.telemetry()["requests_remaining"], 0)

    def test_failures_consume_budget_and_are_not_retried(self):
        p, c = self.provider(TimeoutError("secret-key-should-never-leak"))
        self.assertCode(p, "timeout")
        self.assertEqual(len(c.requests), 1)
        self.assertEqual(p.telemetry()["requests_attempted"], 1)
        self.assertNotIn("secret-key", json.dumps(p.telemetry()))

    def test_status_codes_are_sanitized(self):
        for status, code in ((400, "request_rejected"), (401, "access_denied"),
                             (403, "access_denied"), (404, "model_unavailable"),
                             (429, "rate_limited"), (503, "service_unavailable")):
            with self.subTest(status=status):
                error = RuntimeError("secret endpoint and key")
                error.code = status
                p, _ = self.provider(error)
                self.assertCode(p, code)

    def test_unknown_error_never_exposes_raw_text(self):
        p, _ = self.provider(ValueError("SECRET"))
        self.assertCode(p, "connection_or_sdk_error")
        self.assertNotIn("SECRET", json.dumps(p.telemetry()))

    def test_empty_candidates(self):
        r = response()
        r.candidates = []
        p, _ = self.provider(r)
        self.assertCode(p, "empty_or_ambiguous_response")

    def test_ambiguous_candidates(self):
        r = response()
        r.candidates *= 2
        p, _ = self.provider(r)
        self.assertCode(p, "empty_or_ambiguous_response")

    def test_empty_parts(self):
        p, _ = self.provider(response([]))
        self.assertCode(p, "empty_or_ambiguous_response")

    def test_text_only_not_silently_parsed(self):
        p, _ = self.provider(response([NS(text=json.dumps(report()), function_call=None)]))
        self.assertCode(p, "no_function_call")

    def test_truncated_output(self):
        p, _ = self.provider(response(finish="MAX_TOKENS"))
        self.assertCode(p, "output_limit")

    def test_safety_refusal(self):
        p, _ = self.provider(response(finish="SAFETY"))
        self.assertCode(p, "model_refused")

    def test_prompt_refusal(self):
        r = response()
        r.prompt_feedback = NS(block_reason="SAFETY")
        p, _ = self.provider(r)
        self.assertCode(p, "model_refused")

    def test_unknown_finish_reason(self):
        p, _ = self.provider(response(finish="MALFORMED_FUNCTION_CALL"))
        self.assertCode(p, "invalid_model_response")

    def test_invalid_function_arguments(self):
        r = response()
        r.candidates[0].content.parts[0].function_call.args = "not a dict"
        p, _ = self.provider(r)
        self.assertCode(p, "invalid_function_call")

    def test_nonfinite_function_arguments(self):
        p, _ = self.provider(response([part(args={"service_id": float("nan")})]))
        self.assertCode(p, "invalid_function_call")

    def test_duplicate_native_ids(self):
        p, _ = self.provider(response([part(native_id="same"), part(native_id="same")]))
        self.assertCode(p, "invalid_function_call")

    def test_telemetry_reports_observed_tokens_and_copies(self):
        p, _ = self.provider(response())
        next_turn(p)
        first = p.telemetry()
        self.assertEqual(first["attempts"][0]["total_tokens"], 140)
        self.assertEqual(first["attempts"][0]["cached_prompt_tokens"], 20)
        first["attempts"][0]["total_tokens"] = 999
        self.assertEqual(p.telemetry()["attempts"][0]["total_tokens"], 140)

    def test_unknown_token_counts_stay_none_not_zero(self):
        p, _ = self.provider(response(usage=False))
        next_turn(p)
        self.assertIsNone(p.telemetry()["attempts"][0]["total_tokens"])

    def test_close_is_idempotent_and_prevents_requests(self):
        p, c = self.provider()
        p.close()
        p.close()
        self.assertTrue(c.closed)
        self.assertCode(p, "client_closed")
        self.assertEqual(c.requests, [])

    def test_bad_initial_context_no_request(self):
        p, c = self.provider()
        history = messages()
        history[0]["content"]["service_id"] = "production"
        self.assertCode(p, "invalid_history", history)
        self.assertEqual(c.requests, [])

    def test_wrong_tool_result_pairing_no_second_request(self):
        p, c = self.provider(response())
        calls = next_turn(p).tool_calls
        history = add_results(messages(), calls)
        history[-1]["tool_call_id"] = "unrelated"
        self.assertCode(p, "invalid_history", history)
        self.assertEqual(len(c.requests), 1)

    def test_invalid_key_input_is_safe(self):
        with self.assertRaisesRegex(GeminiProviderError, "^invalid_key_input$"):
            GeminiProvider("", client=FakeClient([]))

    def test_invalid_model_input_is_safe(self):
        with self.assertRaisesRegex(GeminiProviderError, "^invalid_configuration$"):
            GeminiProvider("fake", model="https://secret-host/", client=FakeClient([]))


try:
    from google import genai
    from google.genai import types
except ImportError:
    types = None


@unittest.skipIf(types is None, "google-genai not installed; no network is required by these tests")
class RealSdkContractTests(unittest.TestCase):
    def test_real_sdk_http_serialization_through_complete_runtime(self):
        """Real SDK serialization/parsing, intercepted before any network I/O."""
        import httpx

        captured = []
        signature = b64encode(b"opaque-http-signature").decode("ascii")
        native_content = {"role": "model", "parts": [
            {"functionCall": {"name": "get_logs", "args": {"service_id": "demo-api"}, "id": "logs-1"},
             "thoughtSignature": signature},
            {"functionCall": {"name": "get_metrics", "args": {"service_id": "demo-api"}, "id": "metrics-1"}},
            {"functionCall": {"name": "get_runbook", "args": {"service_id": "demo-api"}, "id": "runbook-1"}},
        ]}

        def handler(request):
            captured.append(json.loads(request.content))
            self.assertEqual(request.method, "POST")
            self.assertTrue(request.url.path.endswith(f"/{DEFAULT_MODEL}:generateContent"))
            if len(captured) == 1:
                content = native_content
            elif len(captured) == 2:
                content = {"role": "model", "parts": [{"functionCall": {
                    "name": "submit_report", "args": report(), "id": "report-1"}}]}
            else:
                self.fail("The bounded investigation unexpectedly made another HTTP request")
            return httpx.Response(200, json={
                "candidates": [{"content": content, "finishReason": "STOP", "index": 0}],
                "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 30,
                                  "thoughtsTokenCount": 10, "totalTokenCount": 140},
            })

        client = genai.Client(api_key="fake-http-test-key-never-send", vertexai=False,
                              http_options=types.HttpOptions(
                                  timeout=30000,
                                  retry_options=types.HttpRetryOptions(attempts=1),
                                  client_args={"transport": httpx.MockTransport(handler)}))
        provider = GeminiProvider("fake-http-test-key-never-send", client=client)
        try:
            result = run_investigation("healthy", provider, freshness_policy)
            self.assertEqual(result["status"], "completed", provider.last_error_code)
            self.assertEqual(result["decision"]["status"], "evidence_gate_passed")
            self.assertEqual(result["tool_calls"], 3)
            self.assertEqual(provider.telemetry()["requests_attempted"], 2)
            self.assertEqual(len(captured), 2)
            self.assertEqual(captured[1]["contents"][1], native_content)
            function_responses = captured[1]["contents"][2]["parts"]
            self.assertEqual([item["functionResponse"]["id"] for item in function_responses],
                             ["logs-1", "metrics-1", "runbook-1"])
            self.assertEqual([item["functionResponse"]["name"] for item in function_responses],
                             ["get_logs", "get_metrics", "get_runbook"])
            metrics_response = function_responses[1]["functionResponse"]["response"]
            self.assertEqual(metrics_response["records"][0]["p95_latency_ms"], 180)
            self.assertEqual(captured[0]["toolConfig"]["functionCallingConfig"]["mode"], "ANY")
            self.assertEqual(captured[0]["generationConfig"]["maxOutputTokens"], 2048)
            self.assertEqual(provider.telemetry()["attempts"][1]["total_tokens"], 140)
        finally:
            provider.close()

    def test_real_sdk_response_signature_and_request_serialization(self):
        original = types.Content(role="model", parts=[types.Part(
            function_call=types.FunctionCall(name="get_metrics", args={"service_id": "demo-api"}),
            thought_signature=b"opaque-signature")])
        first = types.GenerateContentResponse(candidates=[types.Candidate(
            content=original, finish_reason=types.FinishReason.STOP)])
        final = types.GenerateContentResponse(candidates=[types.Candidate(
            content=types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(
                name="submit_report", args=report()))]), finish_reason=types.FinishReason.STOP)])
        client = FakeClient([first, final])
        provider = GeminiProvider("fake", client=client)
        calls = next_turn(provider).tool_calls
        next_turn(provider, add_results(messages(), calls))
        request = client.requests[1]
        cfg = types.GenerateContentConfig.model_validate(request["config"])
        self.assertTrue(cfg.automatic_function_calling.disable)
        contents = [types.Content.model_validate(value) for value in request["contents"]]
        self.assertEqual(contents[1].model_dump(), original.model_dump())
        self.assertEqual(contents[1].parts[0].thought_signature, b"opaque-signature")
        self.assertEqual(contents[2].parts[0].function_response.name, "get_metrics")
        types.HttpOptions.model_validate({"timeout": 30000, "retry_options": {"attempts": 1}})

    def test_constructor_sets_timeout_and_no_retry_without_network(self):
        fake = FakeClient([])
        with patch.object(genai, "Client", return_value=fake) as factory:
            provider = GeminiProvider("fake")
        args = factory.call_args.kwargs
        self.assertEqual(args["http_options"]["timeout"], 30000)
        self.assertEqual(args["http_options"]["retry_options"]["attempts"], 1)
        self.assertIs(args["vertexai"], False)
        self.assertEqual(provider.telemetry()["requests_attempted"], 0)


if __name__ == "__main__":
    unittest.main()

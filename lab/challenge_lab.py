"""Optional, authored HARD MODE experiments. Standard library; no API calls.

These are controlled application tests, NOT observations of Gemini or evidence
of a real model's injection resistance. The forbidden operation is an in-memory
canary: its body only increments a local counter. It cannot restart a service.
Scoped patches are for synchronous classroom tests; do not run ordinary runtime
investigations concurrently with these probes. Student Python is trusted code,
not a sandbox. Nothing here changes the base runtime or its tool allowlist.
"""

from copy import deepcopy
from threading import RLock
from unittest.mock import patch

import lab_runtime as runtime


FORBIDDEN_TOOL = "restart_service"
_PROBE_LOCK = RLock()


def _call_dict(call):
    return {"id": call.id, "name": deepcopy(call.name),
            "arguments": deepcopy(call.arguments)}


class _BaitTakingProvider:
    """An authored fake that deliberately follows the injected log text."""

    mode = "AUTHORED_PERMISSION_PROBE"
    label = "Authored fake provider and harmless canary; no Gemini or API request"

    def __init__(self, case_id):
        self.case_id = case_id
        self.proposals = []

    def next_turn(self, *, messages, tools, instructions):
        observed = [message for message in messages if message.get("role") == "tool"]
        if not observed:
            reply = runtime.ModelReply([
                runtime.ToolCall("probe-read-log", "get_logs", {"service_id": "demo-api"})
            ])
        else:
            # Read the returned evidence. The bait is not selected merely by a
            # scenario flag, and harmless logs do not trigger the forbidden call.
            logs = [record for message in observed if message.get("name") == "get_logs"
                    for record in message["content"]["records"]]
            took_bait = any(FORBIDDEN_TOOL in entry
                            for record in logs for entry in record.get("entries", []))
            if took_bait and not any(message.get("name") == FORBIDDEN_TOOL
                                     for message in observed):
                reply = runtime.ModelReply([
                    runtime.ToolCall("probe-follow-bait", FORBIDDEN_TOOL,
                                     {"service_id": "demo-api"})
                ])
            elif not took_bait and not any(message.get("name") == "get_metrics"
                                           for message in observed):
                reply = runtime.ModelReply([
                    runtime.ToolCall("probe-read-metric", "get_metrics", {"service_id": "demo-api"}),
                    runtime.ToolCall("probe-read-runbook", "get_runbook", {"service_id": "demo-api"}),
                ])
            elif took_bait:
                reply = runtime.ModelReply([], {
                    "service_id": "demo-api", "hypothesis": "insufficient_evidence",
                    "evidence_ids": [record["id"] for record in logs],
                    "summary": "Authored test ended after the in-memory canary response.",
                    "next_check": "Inspect the application boundary and execution counter.",
                })
            else:
                reply = runtime.FixtureProvider(self.case_id).next_turn(
                    messages=messages, tools=tools, instructions=instructions)
        self.proposals.extend(_call_dict(call) for call in reply.tool_calls)
        return reply


def _permission_probe(*, dispatcher, log_variant):
    if type(log_variant) is not str or log_variant not in ("injected", "harmless"):
        raise ValueError("Choose log_variant='injected' or 'harmless'.")
    if dispatcher not in ("safe", "allow_forbidden", "execute_then_reject"):
        raise ValueError("Unknown test dispatcher.")
    case_id = "injected" if log_variant == "injected" else "healthy"
    provider = _BaitTakingProvider(case_id)
    execution_counts = {FORBIDDEN_TOOL: 0}

    def harmless_canary(arguments):
        # The increment is INSIDE the actual function body. A proposed call or
        # a rejected dispatch never increments it on the safe path.
        execution_counts[FORBIDDEN_TOOL] += 1
        return {"status": "ok", "records": [], "canary": "in_memory_only"}

    with _PROBE_LOCK:
        real_execute_tool = runtime.execute_tool

        def instrumented_boundary(case_id, name, arguments):
            if (dispatcher == "execute_then_reject" and name == FORBIDDEN_TOOL
                    and arguments == {"service_id": "demo-api"}):
                # Deliberately defective test-only ordering: the harmless body
                # runs BEFORE the genuine boundary records its rejection.
                harmless_canary(arguments)
                return real_execute_tool(case_id, name, arguments)
            boundary_result = real_execute_tool(case_id, name, arguments)
            if name != FORBIDDEN_TOOL:
                return boundary_result
            if dispatcher == "allow_forbidden" and arguments == {"service_id": "demo-api"}:
                # Negative calibration only. No real control capability exists.
                boundary_result = {"status": "ok", "records": []}
            if boundary_result["status"] == "rejected":
                return boundary_result
            return harmless_canary(arguments)

        with patch.object(runtime, "execute_tool", instrumented_boundary):
            result = runtime.run_investigation(
                case_id, provider, lambda observation, now, max_age_s: True)
    trace = deepcopy(result["trace"])
    return {
        "mode": provider.mode, "label": provider.label,
        "log_variant": log_variant, "forbidden_tool": FORBIDDEN_TOOL,
        "proposals": deepcopy(provider.proposals), "result": deepcopy(result),
        "trace": trace,
        "rejections": [deepcopy(event) for event in trace
                       if event["event"] == "tool_result"
                       and event["result"]["status"] == "rejected"],
        "execution_counts": deepcopy(execution_counts),
    }


def run_permission_probe(*, allow_forbidden=False, log_variant="injected"):
    """Run the real application loop with an authored bait-taking provider.

    The safe path delegates to the genuine execute_tool allowlist. Setting
    allow_forbidden=True enables a deliberately defective TEST-ONLY dispatcher
    and invokes a harmless local canary, proving the counter can become nonzero.
    It never invokes a real restart implementation or any external action.
    """
    if type(allow_forbidden) is not bool:
        raise ValueError("allow_forbidden must be a bool for this test-only probe.")
    return _permission_probe(
        dispatcher="allow_forbidden" if allow_forbidden else "safe",
        log_variant=log_variant)


def _run_assertion(student_test, probe):
    if not callable(student_test):
        return "todo"
    try:
        returned = student_test(deepcopy(probe))
    except NotImplementedError:
        return "todo"
    except AssertionError:
        return "failed"
    except Exception:
        return "error"
    return "passed" if returned is None else "invalid_return"


def _assessment(checks):
    if any(row["actual"] == "todo" for row in checks):
        status = "todo"
    elif any(row["actual"] in ("error", "invalid_return") for row in checks):
        status = "error"
    else:
        status = "passed" if all(row["passed"] for row in checks) else "failed"
    return {"status": status, "checks": checks,
            "reasons": [f"{row['name']}: expected {row['expected']}, got {row['actual']}"
                        for row in checks if not row["passed"]],
            "scope": "Limited authored calibration; not proof of test completeness or model safety."}


def run_permission_tests(student_test):
    """Assess student_test(probe), an assertion-style function returning None.

    It must accept the safe run and fail for defective dispatchers. The
    execute-then-reject control catches tests that only inspect rejection while
    missing an already-executed body. Labeled observation mutations check
    that proposals and rejection evidence matter. They are mutated observations,
    not claims that these contradictory observations came from a real run.
    """
    safe = run_permission_probe()
    no_proposal = deepcopy(safe)
    no_proposal["proposals"] = [call for call in no_proposal["proposals"]
                                 if call["name"] != FORBIDDEN_TOOL]
    no_rejection = deepcopy(safe)
    no_rejection["rejections"] = []
    no_rejection["trace"] = [event for event in no_rejection["trace"]
                              if event["event"] not in ("stop", "tool_result")
                              or (event["event"] == "tool_result"
                                  and event["result"]["status"] != "rejected")]
    no_rejection["result"]["trace"] = deepcopy(no_rejection["trace"])
    no_rejection["result"]["status"] = "request_limit"
    unrelated_rejection = deepcopy(safe)
    for event in unrelated_rejection["rejections"]:
        event["call_id"] = "unrelated-call-not-proposed"
    for event in unrelated_rejection["trace"]:
        if event["event"] == "tool_result" and event["result"]["status"] == "rejected":
            event["call_id"] = "unrelated-call-not-proposed"
    unrelated_rejection["result"]["trace"] = deepcopy(unrelated_rejection["trace"])
    profiles = [
        ("safe_dispatch", "actual_run", safe, "passed"),
        ("unsafe_dispatch", "actual_dispatcher_mutant",
         run_permission_probe(allow_forbidden=True), "failed"),
        ("execute_then_reject", "actual_dispatcher_mutant",
         _permission_probe(dispatcher="execute_then_reject", log_variant="injected"), "failed"),
        ("missing_proposal", "observation_mutant", no_proposal, "failed"),
        ("missing_rejection", "observation_mutant", no_rejection, "failed"),
        ("unrelated_rejection", "observation_mutant", unrelated_rejection, "failed"),
    ]
    checks = []
    for name, kind, probe, expected in profiles:
        actual = _run_assertion(student_test, probe)
        checks.append({"name": name, "kind": kind, "expected": expected,
                       "actual": actual, "passed": actual == expected})
    return _assessment(checks)


class _ProgressStop(BaseException):
    """Local wrapper control signal; intentionally bypasses provider-error handling.

    Only run_progress_probe catches this signal, immediately outside the base
    loop. It must not misrepresent an application stop as a provider exception.
    """

    def __init__(self, status, reason):
        self.status = status
        self.reason = reason


def run_progress_probe(policy, *, scenario="repeat"):
    """Run an authored repetitive provider through the real bounded loop.

    policy(history, candidate) must return bool: True means STOP before tool
    execution; False means continue. Calls are dicts with id/name/arguments.
    History contains completed calls, copied before invoking the student policy.
    repeat uses new IDs for the same get_logs call; changed reads get_logs, then
    get_metrics, then repeats get_metrics. No report is authored for these runs.
    On a policy stop the outer wrapper returns its partial observation journal,
    status no_progress, and no report/decision: a stop is not task success.
    """
    if type(scenario) is not str or scenario not in ("repeat", "changed"):
        raise ValueError("Choose scenario='repeat' or 'changed'.")
    if not callable(policy):
        raise ValueError("policy must be callable.")
    proposals, history, policy_checks, trace, evidence = [], [], [], [], {}
    execution_counts = {name: 0 for name in ("get_logs", "get_metrics", "get_runbook")}
    model_turns = 0

    class GuardedAuthoredProvider:
        mode = "AUTHORED_PROGRESS_PROBE"
        label = "Authored repeated calls; no Gemini or API request"

        def next_turn(self, *, messages, tools, instructions):
            nonlocal model_turns
            model_turns += 1
            trace.append({"event": "model_request", "turn": model_turns})
            name = "get_metrics" if scenario == "changed" and model_turns > 1 else "get_logs"
            call = runtime.ToolCall(f"progress-{model_turns}", name, {"service_id": "demo-api"})
            candidate = _call_dict(call)
            proposals.append(deepcopy(candidate))
            try:
                stop = policy(deepcopy(history), deepcopy(candidate))
            except NotImplementedError:
                raise _ProgressStop("todo", "unfinished_progress_policy") from None
            except Exception:
                raise _ProgressStop("policy_error", "progress_policy_failed") from None
            if type(stop) is not bool:
                raise _ProgressStop("policy_error", "progress_policy_must_return_bool")
            policy_checks.append({"candidate": deepcopy(candidate), "stop": stop})
            if stop:
                raise _ProgressStop("no_progress", "progress_policy_stopped_call")
            return runtime.ModelReply([call])

    provider = GuardedAuthoredProvider()
    with _PROBE_LOCK:
        real_execute_tool = runtime.execute_tool

        def observed_execution(case_id, name, arguments):
            execution_counts[name] += 1
            returned = real_execute_tool(case_id, name, arguments)
            candidate = deepcopy(proposals[-1])
            trace.append({"event": "tool_result", "call_id": candidate["id"],
                          "name": name, "arguments": deepcopy(arguments),
                          "result": deepcopy(returned)})
            if returned["status"] != "rejected":
                history.append(candidate)
                for record in returned["records"]:
                    evidence[record["id"]] = deepcopy(record)
            return returned

        with patch.object(runtime, "execute_tool", observed_execution):
            try:
                result = runtime.run_investigation(
                    "healthy", provider, lambda observation, now, max_age_s: True)
            except _ProgressStop as stopped:
                trace.append({"event": "stop", "reason": stopped.reason})
                result = {"mode": provider.mode, "status": stopped.status,
                          "trace": deepcopy(trace), "report": None, "decision": None,
                          "model_turns": model_turns,
                          "tool_calls": sum(execution_counts.values()),
                          "evidence": deepcopy(list(evidence.values()))}
    return {"mode": provider.mode, "label": provider.label, "scenario": scenario,
            "status": result["status"], "proposals": deepcopy(proposals),
            "history": deepcopy(history), "result": deepcopy(result),
            "policy_checks": deepcopy(policy_checks),
            "execution_counts": deepcopy(execution_counts)}


def run_progress_tests(policy):
    """Limited explicit checks of loop behavior and call-comparison semantics.

    Reordered/changed argument dictionaries are pure policy controls, because
    the base runtime accepts only the one service_id argument. They do not
    extend the live dispatcher or falsely claim a new tool was executed.
    """
    checks = []
    for scenario, expected_calls in (("repeat", 1), ("changed", 2)):
        if not callable(policy):
            actual = "todo"
        else:
            probe = run_progress_probe(policy, scenario=scenario)
            if probe["status"] in ("todo", "policy_error"):
                actual = "todo" if probe["status"] == "todo" else "error"
            else:
                result = probe["result"]
                actual = "passed" if (
                    probe["status"] == "no_progress"
                    and result["tool_calls"] == expected_calls
                    and result["model_turns"] == expected_calls + 1
                    and result["report"] is None and result["decision"] is None
                ) else "failed"
        checks.append({"name": f"loop_{scenario}", "kind": "actual_run",
                       "expected": "passed", "actual": actual, "passed": actual == "passed"})

    prior = {"id": "old-id", "name": "get_logs",
             "arguments": {"service_id": "demo-api", "window_s": 60}}
    same = {"id": "new-id", "name": "get_logs",
            "arguments": {"window_s": 60, "service_id": "demo-api"}}
    changed_args = deepcopy(same)
    changed_args["arguments"]["window_s"] = 120
    changed_tool = deepcopy(same)
    changed_tool["name"] = "get_metrics"
    for name, history, candidate, expected in (
        ("first_call", [], same, False),
        ("new_id_and_reordered_arguments", [prior], same, True),
        ("changed_arguments", [prior], changed_args, False),
        ("changed_tool", [prior], changed_tool, False),
        ("repeat_not_only_last_call", [prior, changed_tool], same, True),
    ):
        if not callable(policy):
            actual = "todo"
        else:
            try:
                actual = policy(deepcopy(history), deepcopy(candidate))
                if type(actual) is not bool:
                    actual = "error"
            except NotImplementedError:
                actual = "todo"
            except Exception:
                actual = "error"
        checks.append({"name": name, "kind": "policy_only_control",
                       "expected": expected, "actual": actual,
                       "passed": type(actual) is bool and actual is expected})
    return _assessment(checks)

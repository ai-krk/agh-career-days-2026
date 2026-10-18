"""Deterministic runtime/policy tests; no live model, credentials or network.

Run from AGH_AI_Engineering_v0.5 with:
    python -B -m unittest discover -s tests -v
Passing these tests does not establish diagnostic truth or service safety.
"""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import lab_runtime as rt
from solutions import freshness_policy


SECRET_MARKER = "TEST_SECRET_DO_NOT_PRINT_91b3"


def starter_policy(observation, now, max_age_s):
    """Deliberately unfinished learner starting point, not the solution."""
    return True


def records_for(case):
    return [deepcopy(case[key]) for key in ("metrics", "logs", "runbook")
            if case[key] is not None]


def report_for(case, hypothesis="no_latency_breach"):
    return {
        "service_id": case["service_id"],
        "hypothesis": hypothesis,
        "evidence_ids": [record["id"] for record in records_for(case)],
        "summary": "Synthetic teaching example, not a real service diagnosis.",
        "next_check": "Ask for a fresh synthetic observation and review it.",
    }


class ScriptedProvider:
    """Authored protocol fake. It tests application behavior, not reasoning."""

    mode = "AUTHORED_FIXTURE"
    label = "AUTHORED testing fixture, no model or network"

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def next_turn(self, *, messages, tools, instructions):
        self.calls += 1
        if not self.replies:
            raise AssertionError("Unexpected extra provider turn")
        reply = self.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return reply


def tool_call(case, name="get_logs", call_id="call-1", arguments=None):
    return rt.ToolCall(call_id, name, {"service_id": case["service_id"]}
                       if arguments is None else arguments)


class CaseAndToolTests(unittest.TestCase):
    def setUp(self):
        self.case = rt.load_case("healthy")

    def test_six_required_synthetic_cases_are_available(self):
        self.assertTrue({"healthy", "high_latency", "stale", "missing", "future", "injected"}
                        .issubset(set(rt.CASE_IDS)))
        for name in rt.CASE_IDS:
            with self.subTest(case=name):
                case = rt.load_case(name)
                self.assertEqual(case["case_id"], name)
                self.assertEqual(case["max_age_s"], 300)
                self.assertIs(type(case["now"]), int)
                json.dumps(case, allow_nan=False)

    def test_case_data_has_expected_boundary_conditions(self):
        for name, age in (("healthy", 30), ("stale", 301), ("future", -1)):
            case = rt.load_case(name)
            self.assertEqual(case["now"] - case["metrics"]["observed_at"], age)
        self.assertIsNone(rt.load_case("missing")["metrics"])
        self.assertEqual(self.case["metrics"]["p95_latency_ms"], 180)
        self.assertEqual(self.case["metrics"]["window_s"], 60)
        hot = rt.load_case("high_latency")
        self.assertEqual(hot["metrics"]["p95_latency_ms"], 900)
        self.assertEqual(hot["metrics"]["window_s"], 60)
        self.assertEqual(hot["runbook"]["max_p95_latency_ms"], 500)

    def test_load_case_returns_independent_deep_copies(self):
        original = deepcopy(self.case)
        self.case["metrics"]["p95_latency_ms"] = -999
        self.case["logs"]["entries"].append(SECRET_MARKER)
        self.case["runbook"]["max_p95_latency_ms"] = 9999
        self.assertEqual(rt.load_case("healthy"), original)

    def test_metric_window_and_meaning_are_explicit_in_synthetic_data(self):
        for case_id in rt.CASE_IDS:
            with self.subTest(case=case_id):
                case = rt.load_case(case_id)
                self.assertEqual(case["service_id"], "demo-api")
                self.assertEqual(case["runbook"]["max_p95_latency_ms"], 500)
                self.assertIn("95th percentile", case["runbook"]["metric_definition"])
                self.assertIn("60-second window", case["runbook"]["metric_definition"])
                self.assertIn("not the time", case["runbook"]["observed_at_definition"])
                if case["metrics"] is not None:
                    self.assertIs(type(case["metrics"]["window_s"]), int)
                    self.assertEqual(case["metrics"]["window_s"], 60)

    def test_unknown_case_fails_closed(self):
        with self.assertRaises((ValueError, KeyError)):
            rt.load_case("../../untrusted")

    def test_schemas_have_exact_required_argument_and_no_extra_properties(self):
        schemas = rt.tool_schemas()
        self.assertEqual(len(schemas), 3)
        by_name = {schema["name"]: schema for schema in schemas}
        self.assertEqual(set(by_name), {"get_logs", "get_metrics", "get_runbook"})
        for schema in schemas:
            with self.subTest(tool=schema["name"]):
                params = schema["parameters"]
                self.assertEqual(params["type"], "object")
                self.assertEqual(set(params["properties"]), {"service_id"})
                self.assertEqual(params["required"], ["service_id"])
                self.assertIs(params["additionalProperties"], False)
                service = params["properties"]["service_id"]
                self.assertEqual(service["type"], "string")
                self.assertIn(self.case["service_id"], service["enum"])
        json.dumps(schemas, allow_nan=False)

    def test_schema_copies_do_not_mutate_future_schemas(self):
        original = rt.tool_schemas()
        changed = rt.tool_schemas()
        changed[0]["parameters"]["properties"]["service_id"]["enum"].append(SECRET_MARKER)
        self.assertEqual(rt.tool_schemas(), original)

    def test_tools_return_only_their_record_kinds(self):
        for name, kind in (("get_logs", "logs"), ("get_metrics", "metrics"),
                           ("get_runbook", "runbook")):
            with self.subTest(tool=name):
                result = rt.execute_tool("healthy", name, {"service_id": self.case["service_id"]})
                self.assertEqual(result["status"], "ok")
                self.assertEqual(len(result["records"]), 1)
                self.assertEqual(result["records"][0]["kind"], kind)

    def test_missing_metrics_is_explicit(self):
        result = rt.execute_tool("missing", "get_metrics", {"service_id": self.case["service_id"]})
        self.assertEqual(result["status"], "missing")
        self.assertEqual(result["records"], [])

    def test_tool_name_and_argument_allowlist(self):
        cases = [
            ("send_email", {"service_id": self.case["service_id"]}),
            ("GET_LOGS", {"service_id": self.case["service_id"]}),
            ("get_logs", {}),
            ("get_logs", {"service_id": self.case["service_id"], "extra": "ignored?"}),
            ("get_logs", {"service_id": "unknown-service"}),
            ("get_logs", {"service_id": 1}),
            ("get_logs", {"service_id": True}),
            ("get_logs", {"service_id": None}),
            ("get_logs", {"service_id": [self.case["service_id"]]}),
            ("get_logs", []),
            ("get_logs", None),
            (None, {"service_id": self.case["service_id"]}),
        ]
        for name, arguments in cases:
            with self.subTest(name=name, arguments=arguments):
                result = rt.execute_tool("healthy", name, arguments)
                self.assertEqual(result["status"], "rejected")
                self.assertEqual(result["records"], [])

    def test_tool_results_do_not_mutate_source(self):
        args = {"service_id": self.case["service_id"]}
        first = rt.execute_tool("healthy", "get_logs", args)
        first["records"][0]["entries"].append(SECRET_MARKER)
        second = rt.execute_tool("healthy", "get_logs", args)
        self.assertNotIn(SECRET_MARKER, second["records"][0]["entries"])
        self.assertNotIn(SECRET_MARKER, rt.load_case("healthy")["logs"]["entries"])

    def test_case_loading_is_independent_of_working_directory(self):
        import os
        original_directory = Path.cwd()
        try:
            os.chdir(Path(__file__).resolve().parent)
            self.assertEqual(rt.load_case("healthy"), self.case)
        finally:
            os.chdir(original_directory)


class ReferencePolicyTests(unittest.TestCase):
    def setUp(self):
        self.now = rt.load_case("healthy")["now"]

    def test_accepts_age_zero_through_three_hundred_inclusive(self):
        for age in (0, 1, 30, 299, 300):
            with self.subTest(age=age):
                self.assertIs(freshness_policy({"observed_at": self.now - age}, self.now, 300), True)

    def test_rejects_stale_future_and_missing_timestamp(self):
        for observation in ({"observed_at": self.now - 301},
                            {"observed_at": self.now + 1}, {}):
            with self.subTest(observation=observation):
                self.assertIs(freshness_policy(observation, self.now, 300), False)

    def test_rejects_non_integer_timestamps_including_bool_and_nan(self):
        for value in (True, False, str(self.now), float(self.now), float("nan"),
                      float("inf"), None, [], {}):
            with self.subTest(value=repr(value)):
                self.assertIs(freshness_policy({"observed_at": value}, self.now, 300), False)

    def test_uses_supplied_clock_and_window_not_wall_clock(self):
        self.assertIs(freshness_policy({"observed_at": 10}, 10, 0), True)
        self.assertIs(freshness_policy({"observed_at": 9}, 10, 0), False)
        self.assertIs(freshness_policy({"observed_at": 1}, 10, 9), True)
        self.assertIs(freshness_policy({"observed_at": 1}, 10, 8), False)


class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.case = rt.load_case("healthy")
        self.evidence = records_for(self.case)
        self.report = report_for(self.case)

    def verify(self, report=None, evidence=None, policy=freshness_policy):
        return rt.verify_report(self.report if report is None else report,
                                self.evidence if evidence is None else evidence,
                                now=self.case["now"], freshness_policy=policy,
                                max_age_s=self.case["max_age_s"])

    def test_ordinary_report_passes_gate_but_not_a_truth_or_safety_claim(self):
        decision = self.verify()
        self.assertEqual(decision["status"], "evidence_gate_passed")
        self.assertIsInstance(decision["reasons"], list)

    def test_malformed_report_schema_is_blocked(self):
        bad_reports = [[], "not a report", {}, {**self.report, "confidence": 0.99},
                       {**self.report, "hypothesis": "certain_diagnosis"},
                       {**self.report, "summary": ""},
                       {**self.report, "next_check": 123},
                       {**self.report, "service_id": False},
                       {**self.report, "evidence_ids": "metrics-1"},
                       {**self.report, "evidence_ids": [1]},
                       {**self.report, "summary": "x" * 100_000}]
        for report in bad_reports:
            with self.subTest(report_type=type(report).__name__, keys=list(report) if isinstance(report, dict) else None):
                self.assertEqual(self.verify(report=report)["status"], "blocked")
        self.assertEqual(rt.verify_report(None, self.evidence, now=self.case["now"],
                                         freshness_policy=freshness_policy)["status"], "blocked")

    def test_fabricated_citation_is_blocked(self):
        self.report["evidence_ids"].append("fabricated-record-999")
        self.assertEqual(self.verify()["status"], "blocked")

    def test_cross_service_report_and_record_are_blocked(self):
        wrong_report = {**self.report, "service_id": "other-service"}
        self.assertEqual(self.verify(report=wrong_report)["status"], "blocked")
        self.evidence[0]["service_id"] = "other-service"
        self.assertEqual(self.verify()["status"], "blocked")

    def test_required_metrics_and_runbook_must_be_returned_and_cited(self):
        for kind in ("metrics", "runbook"):
            with self.subTest(missing_kind=kind):
                remaining = [record for record in self.evidence if record["kind"] != kind]
                report = deepcopy(self.report)
                report["evidence_ids"] = [record["id"] for record in remaining]
                self.assertEqual(self.verify(report=report, evidence=remaining)["status"], "needs_more_data")
                self.assertEqual(self.verify(report=report)["status"], "needs_more_data")

    def test_policy_requires_literal_true_and_sanitizes_exceptions(self):
        for value in (False, None, 1, "True", [], {}):
            with self.subTest(value=repr(value)):
                self.assertEqual(self.verify(policy=lambda *args, v=value: v)["status"], "needs_more_data")

        def failing_policy(*args):
            raise RuntimeError(SECRET_MARKER)

        decision = self.verify(policy=failing_policy)
        self.assertEqual(decision["status"], "needs_more_data")
        self.assertNotIn(SECRET_MARKER, json.dumps(decision))

    def test_policy_evaluates_only_cited_metrics_and_receives_copies(self):
        calls = []
        original = deepcopy(self.evidence)

        def observing_policy(record, now, max_age_s):
            calls.append((record["id"], record["kind"], now, max_age_s))
            record["p95_latency_ms"] = -999
            record["new_field"] = SECRET_MARKER
            return True

        self.assertEqual(self.verify(policy=observing_policy)["status"], "evidence_gate_passed")
        self.assertEqual(calls, [(self.case["metrics"]["id"], "metrics", self.case["now"], 300)])
        self.assertEqual(self.evidence, original)

    def test_uncited_historical_metrics_does_not_trigger_policy(self):
        historical = deepcopy(self.case["metrics"])
        historical["id"] = "uncited-historical-record"
        historical["observed_at"] = self.case["now"] - 1000
        self.evidence.append(historical)
        self.assertEqual(self.verify()["status"], "evidence_gate_passed")

    def test_invalid_authoritative_measurements_need_more_data(self):
        for kind, field in (("metrics", "p95_latency_ms"), ("metrics", "window_s"),
                            ("runbook", "max_p95_latency_ms")):
            for invalid in (True, False, None, "180", float("nan"), float("inf"), float("-inf")):
                with self.subTest(kind=kind, field=field, value=repr(invalid)):
                    changed = deepcopy(self.evidence)
                    next(record for record in changed if record["kind"] == kind)[field] = invalid
                    self.assertEqual(self.verify(evidence=changed)["status"], "needs_more_data")

    def test_wrong_or_missing_metric_window_is_inconclusive(self):
        for value in (0, 59, 61, -1, 60.0, True, None, "60"):
            with self.subTest(window=value):
                changed = deepcopy(self.evidence)
                record = next(record for record in changed if record["kind"] == "metrics")
                record["window_s"] = value
                decision = self.verify(evidence=changed)
                self.assertEqual(decision["status"], "needs_more_data")
                self.assertEqual(decision["reasons"], ["invalid_metrics_window"])
        changed = deepcopy(self.evidence)
        next(record for record in changed if record["kind"] == "metrics").pop("window_s")
        self.assertEqual(self.verify(evidence=changed)["status"], "needs_more_data")

    def test_negative_latency_or_runbook_limit_is_inconclusive(self):
        for kind, field in (("metrics", "p95_latency_ms"), ("runbook", "max_p95_latency_ms")):
            for value in (-1, -0.01):
                with self.subTest(kind=kind, value=value):
                    changed = deepcopy(self.evidence)
                    next(record for record in changed if record["kind"] == kind)[field] = value
                    self.assertEqual(self.verify(evidence=changed)["status"], "needs_more_data")

    def test_summary_counterexample_does_not_change_authoritative_metrics(self):
        original = deepcopy(self.evidence)
        self.report["summary"] = "The returned metrics record reports p95 request latency of 950 ms."
        self.assertEqual(self.verify()["status"], "evidence_gate_passed")
        self.assertEqual(self.evidence, original)
        self.assertEqual(next(record["p95_latency_ms"] for record in self.evidence
                              if record["kind"] == "metrics"), 180)

    def test_no_latency_breach_above_supplied_limit_is_blocked(self):
        hot = rt.load_case("high_latency")
        decision = rt.verify_report(report_for(hot, "no_latency_breach"), records_for(hot),
                                    now=hot["now"], freshness_policy=freshness_policy)
        self.assertEqual(decision["status"], "blocked")

    def test_model_supplied_extra_measurements_are_not_authority(self):
        self.report["p95_latency_ms"] = 1
        self.assertEqual(self.verify()["status"], "blocked")

    def test_duplicate_or_malformed_ledger_records_are_blocked(self):
        bad_ledgers = [{}, "not-a-ledger", [None],
                       [*self.evidence, deepcopy(self.evidence[0])],
                       [{"id": "", "service_id": self.case["service_id"]}]]
        for evidence in bad_ledgers:
            with self.subTest(evidence_type=type(evidence).__name__):
                self.assertEqual(self.verify(evidence=evidence)["status"], "blocked")

    def test_duplicate_report_citations_are_blocked(self):
        self.report["evidence_ids"].append(self.report["evidence_ids"][0])
        self.assertEqual(self.verify()["status"], "blocked")

    def test_invalid_time_context_cannot_pass_even_with_starter_policy(self):
        for now, window in ((True, 300), (float(self.case["now"]), 300),
                            (self.case["now"], True), (self.case["now"], -1)):
            with self.subTest(now=now, window=window):
                decision = rt.verify_report(self.report, self.evidence, now=now,
                                            freshness_policy=starter_policy, max_age_s=window)
                self.assertEqual(decision["status"], "needs_more_data")

    def test_timestamp_solution_is_applied_inside_gate(self):
        metrics = next(record for record in self.evidence if record["kind"] == "metrics")
        for invalid in (None, True, str(self.case["now"]), float(self.case["now"]),
                        float("nan"), self.case["now"] + 1, self.case["now"] - 301):
            with self.subTest(timestamp=repr(invalid)):
                metrics["observed_at"] = invalid
                self.assertEqual(self.verify()["status"], "needs_more_data")
        metrics.pop("observed_at")
        self.assertEqual(self.verify()["status"], "needs_more_data")

    def test_no_latency_breach_p95_contradiction_boundary_is_strictly_above(self):
        metrics = next(record for record in self.evidence if record["kind"] == "metrics")
        limit = self.case["runbook"]["max_p95_latency_ms"]
        metrics["p95_latency_ms"] = limit
        self.assertEqual(self.verify()["status"], "evidence_gate_passed")
        metrics["p95_latency_ms"] = limit + 0.01
        self.assertEqual(self.verify()["status"], "blocked")

    def test_gate_is_deliberately_not_a_general_diagnosis_evaluator(self):
        self.report["hypothesis"] = "latency_breach"
        # Healthy data does not establish this hypothesis; the limited gate does not decide it.
        self.assertEqual(self.verify()["status"], "evidence_gate_passed")

    def test_insufficient_evidence_report_stays_inconclusive(self):
        self.report["hypothesis"] = "insufficient_evidence"
        self.assertEqual(self.verify()["status"], "needs_more_data")


class InvestigationTests(unittest.TestCase):
    def setUp(self):
        self.case = rt.load_case("healthy")

    def run_provider(self, provider, **limits):
        return rt.run_investigation("healthy", provider, freshness_policy, **limits)

    def test_authored_fixtures_have_expected_deterministic_outcomes(self):
        expected = {"healthy": "evidence_gate_passed", "high_latency": "evidence_gate_passed",
                    "stale": "needs_more_data", "future": "needs_more_data",
                    "missing": "needs_more_data", "injected": "evidence_gate_passed"}
        for case_id, status in expected.items():
            with self.subTest(case=case_id):
                provider = rt.FixtureProvider(case_id)
                self.assertEqual(provider.mode, "AUTHORED_FIXTURE")
                self.assertIsInstance(provider.label, str)
                self.assertTrue(provider.label.strip())
                result = rt.run_investigation(case_id, provider, freshness_policy)
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["decision"]["status"], status)
                self.assertEqual(result["mode"], "AUTHORED_FIXTURE")
                self.assertEqual(result["tool_calls"], 3)
                self.assertLessEqual(result["model_turns"], 5)

    def test_deliberate_starter_exposes_stale_and_future_false_pass(self):
        for case_id in ("stale", "future"):
            with self.subTest(case=case_id):
                result = rt.run_investigation(case_id, rt.FixtureProvider(case_id), starter_policy)
                self.assertEqual(result["decision"]["status"], "evidence_gate_passed")
                fixed = rt.run_investigation(case_id, rt.FixtureProvider(case_id), freshness_policy)
                self.assertEqual(fixed["decision"]["status"], "needs_more_data")

    def test_control_report_describes_its_window_without_claiming_current_health(self):
        result = self.run_provider(rt.FixtureProvider("healthy"))
        summary = result["report"]["summary"]
        self.assertIn("recorded window", summary)
        self.assertNotIn("currently", summary)
        self.assertNotIn("healthy", summary)
        self.assertEqual(result["report"]["hypothesis"], "no_latency_breach")

    def test_display_prominently_labels_authored_fixture(self):
        result = self.run_provider(rt.FixtureProvider("healthy"))
        output = io.StringIO()
        with redirect_stdout(output):
            rt.show_result(result)
        self.assertIn("AUTHORED_FIXTURE", output.getvalue())
        self.assertIn(result["decision"]["status"], output.getvalue())

    def test_no_orphan_tools_on_last_available_model_turn(self):
        provider = ScriptedProvider([rt.ModelReply([tool_call(self.case)])])
        result = self.run_provider(provider, max_model_turns=1)
        self.assertEqual(result["status"], "request_limit")
        self.assertEqual(result["model_turns"], 1)
        self.assertEqual(result["tool_calls"], 0)
        self.assertEqual(result["evidence"], [])

    def test_zero_model_turns_permits_no_provider_or_tool_calls(self):
        provider = ScriptedProvider([])
        result = self.run_provider(provider, max_model_turns=0)
        self.assertEqual(result["status"], "request_limit")
        self.assertEqual(provider.calls, 0)
        self.assertEqual(result["model_turns"], 0)
        self.assertEqual(result["tool_calls"], 0)

    def test_zero_tool_budget_rejects_batch_before_execution(self):
        result = self.run_provider(ScriptedProvider([rt.ModelReply([tool_call(self.case)])]), max_tool_calls=0)
        self.assertEqual(result["status"], "tool_limit")
        self.assertEqual(result["tool_calls"], 0)
        self.assertEqual(result["evidence"], [])

    def test_oversized_tool_batch_is_atomic(self):
        calls = [tool_call(self.case, call_id=f"call-{i}") for i in range(5)]
        result = self.run_provider(ScriptedProvider([rt.ModelReply(calls)]))
        self.assertEqual(result["status"], "tool_limit")
        self.assertEqual(result["tool_calls"], 0)
        self.assertEqual(result["evidence"], [])

    def test_cumulative_tool_budget_and_hard_model_turn_cap(self):
        replies = [rt.ModelReply([tool_call(self.case, call_id=f"turn-{i}")]) for i in range(5)]
        result = self.run_provider(ScriptedProvider(replies), max_tool_calls=2)
        self.assertEqual(result["status"], "tool_limit")
        self.assertEqual(result["tool_calls"], 2)
        result = self.run_provider(ScriptedProvider(replies))
        self.assertEqual(result["status"], "request_limit")
        self.assertEqual(result["model_turns"], 5)
        self.assertEqual(result["tool_calls"], 4)

    def test_invalid_limits_cannot_raise_hard_caps(self):
        for argument, value in (("max_model_turns", 6), ("max_tool_calls", 5),
                                ("max_model_turns", -1), ("max_tool_calls", -1),
                                ("max_model_turns", True), ("max_tool_calls", False),
                                ("max_model_turns", 2.0), ("max_tool_calls", "2")):
            with self.subTest(argument=argument, value=value):
                with self.assertRaises(ValueError):
                    self.run_provider(ScriptedProvider([]), **{argument: value})

    def test_duplicate_or_empty_call_ids_rejected_before_batch(self):
        for calls in ([tool_call(self.case, call_id="")],
                      [tool_call(self.case), tool_call(self.case, name="get_runbook")]):
            with self.subTest(ids=[call.id for call in calls]):
                result = self.run_provider(ScriptedProvider([rt.ModelReply(calls)]))
                self.assertEqual(result["status"], "invalid_call_ids")
                self.assertEqual(result["tool_calls"], 0)

    def test_non_string_and_blank_call_ids_are_rejected(self):
        for call_id in (None, True, 1, [], "   "):
            with self.subTest(call_id=repr(call_id)):
                result = self.run_provider(ScriptedProvider([
                    rt.ModelReply([tool_call(self.case, call_id=call_id)])]))
                self.assertEqual(result["status"], "invalid_call_ids")
                self.assertEqual(result["tool_calls"], 0)

    def test_call_ids_must_be_unique_across_turns(self):
        replies = [rt.ModelReply([tool_call(self.case)]),
                   rt.ModelReply([tool_call(self.case, name="get_runbook")])]
        result = self.run_provider(ScriptedProvider(replies))
        self.assertEqual(result["status"], "invalid_call_ids")
        self.assertEqual(result["tool_calls"], 1)

    def test_rejected_tool_request_stops_and_never_completes(self):
        for call in (tool_call(self.case, name="restart_service"),
                     tool_call(self.case, arguments={"service_id": self.case["service_id"], "force": True})):
            with self.subTest(name=call.name, arguments=call.arguments):
                result = self.run_provider(ScriptedProvider([rt.ModelReply([call])]))
                self.assertEqual(result["status"], "tool_rejected")
                self.assertEqual(result["evidence"], [])

    def test_invalid_or_ambiguous_provider_replies_fail_closed(self):
        replies = [None, {}, [], "not a reply", rt.ModelReply([]),
                   rt.ModelReply([tool_call(self.case)], report=report_for(self.case)),
                   rt.ModelReply("not-a-list"), rt.ModelReply([{}])]
        for reply in replies:
            with self.subTest(reply_type=type(reply).__name__):
                result = self.run_provider(ScriptedProvider([reply]))
                self.assertEqual(result["status"], "invalid_reply")
                self.assertEqual(result["tool_calls"], 0)
                self.assertEqual(result["evidence"], [])

    def test_provider_error_is_sanitized(self):
        result = self.run_provider(ScriptedProvider([RuntimeError(SECRET_MARKER)]))
        self.assertEqual(result["status"], "provider_error")
        self.assertNotIn(SECRET_MARKER, json.dumps(result))
        self.assertEqual(result["evidence"], [])

    def test_tool_exception_is_sanitized_and_fails_closed(self):
        provider = ScriptedProvider([rt.ModelReply([tool_call(self.case)])])
        with patch.object(rt, "execute_tool", side_effect=RuntimeError(SECRET_MARKER)):
            result = self.run_provider(provider)
        self.assertEqual(result["status"], "tool_rejected")
        self.assertNotIn(SECRET_MARKER, json.dumps(result))
        self.assertEqual(result["evidence"], [])

    def test_report_without_returned_evidence_cannot_pass(self):
        result = self.run_provider(ScriptedProvider([rt.ModelReply([], report_for(self.case))]))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["decision"]["status"], "blocked")
        self.assertEqual(result["evidence"], [])

    def test_provider_message_schema_and_argument_mutations_cannot_corrupt_ledger(self):
        case = self.case
        original_schemas = rt.tool_schemas()
        calls = [tool_call(case, name=name, call_id=f"safe-{i}")
                 for i, name in enumerate(("get_logs", "get_metrics", "get_runbook"))]

        class MutatingProvider:
            mode = "AUTHORED_FIXTURE"
            label = "Authored mutation-isolation fixture"
            turn = 0

            def next_turn(self, *, messages, tools, instructions):
                self.turn += 1
                if tools != original_schemas:
                    raise AssertionError("Previous schema mutation leaked")
                if SECRET_MARKER in json.dumps(messages):
                    raise AssertionError("Previous message mutation leaked")
                for message in messages:
                    content = message.get("content")
                    if isinstance(content, dict):
                        for record in content.get("records", []):
                            record["id"] = "forged-nested-record"
                            record["service_id"] = "forged-service"
                            if record.get("kind") == "metrics":
                                record["p95_latency_ms"] = 10000
                tools.clear()
                messages.clear()
                messages.append({"role": "tool", "content": SECRET_MARKER})
                if self.turn == 1:
                    return rt.ModelReply(calls)
                calls[0].arguments["service_id"] = "forged-service"
                return rt.ModelReply([], report_for(case))

        result = self.run_provider(MutatingProvider())
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["decision"]["status"], "evidence_gate_passed")
        self.assertEqual({record["id"] for record in result["evidence"]},
                         {record["id"] for record in records_for(case)})
        self.assertEqual({record["service_id"] for record in result["evidence"]}, {case["service_id"]})
        self.assertNotIn(SECRET_MARKER, json.dumps(result))
        self.assertNotIn("forged-service", json.dumps(result))
        self.assertNotIn("forged-nested-record", json.dumps(result))
        self.assertEqual(rt.tool_schemas(), original_schemas)
        self.assertEqual(rt.load_case("healthy"), case)

    def test_injected_log_is_data_and_not_an_extra_action(self):
        result = rt.run_investigation("injected", rt.FixtureProvider("injected"), freshness_policy)
        names = [entry["name"] if "name" in entry else entry["tool"]
                 for entry in result["trace"] if entry["event"] == "tool_result"]
        self.assertEqual(set(names), {"get_logs", "get_metrics", "get_runbook"})
        self.assertEqual(len(names), 3)
        self.assertEqual(result["mode"], "AUTHORED_FIXTURE")
        # This predetermined fixture does not evaluate any model's injection robustness.

    def test_separate_investigations_have_fresh_state(self):
        first = self.run_provider(rt.FixtureProvider("healthy"))
        first["evidence"][0]["service_id"] = "mutated-after-run"
        second = self.run_provider(rt.FixtureProvider("healthy"))
        self.assertNotIn("mutated-after-run", json.dumps(second))
        self.assertEqual(second["tool_calls"], 3)

    def test_same_fixture_instance_can_be_reused_without_stale_progress(self):
        provider = rt.FixtureProvider("healthy")
        first = self.run_provider(provider)
        second = self.run_provider(provider)
        self.assertEqual(first, second)

    def test_initial_provider_message_contains_context_not_hidden_case_answers(self):
        captured = []

        class InspectingProvider:
            mode = "AUTHORED_FIXTURE"
            label = "Initial-message inspection fixture"

            def next_turn(self, *, messages, tools, instructions):
                captured.extend(deepcopy(messages))
                return rt.ModelReply([])

        self.run_provider(InspectingProvider())
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0]["role"], "user")
        self.assertEqual(set(captured[0]["content"]),
                         {"service_id", "symptom", "now", "max_age_s"})
        self.assertNotIn("healthy", json.dumps(captured))

    def test_returned_report_is_independent_of_provider_owned_dictionary(self):
        report = report_for(self.case)
        provider = ScriptedProvider([rt.ModelReply([], report)])
        result = self.run_provider(provider)
        report["summary"] = SECRET_MARKER
        report["evidence_ids"].clear()
        self.assertNotIn(SECRET_MARKER, json.dumps(result))
        self.assertTrue(result["report"]["evidence_ids"])


if __name__ == "__main__":
    unittest.main()

"""Offline checks only. These tests never instantiate a real Gemini client."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lab_runtime import FixtureProvider
from live_lab import (freeze_run, replay_comparison, reverify_frozen,
                      run_lab, summary_counterexample)
from solutions import freshness_policy


def starter_policy(*args):
    return True


class SnapshotTests(unittest.TestCase):
    def test_fixed_snapshot_exposes_policy_change_without_provider(self):
        result = run_lab("A", FixtureProvider("stale"), starter_policy)
        snapshot = freeze_run(result)
        with patch("live_lab.run_investigation", side_effect=AssertionError("No new run allowed")):
            comparison = replay_comparison(snapshot, starter_policy, freshness_policy)
        self.assertEqual(comparison["api_requests"], 0)
        self.assertEqual(comparison["before"]["status"], "evidence_gate_passed")
        self.assertEqual(comparison["after"]["status"], "needs_more_data")

    def test_original_mutation_does_not_change_snapshot(self):
        result = run_lab("B", FixtureProvider("healthy"), starter_policy)
        snapshot = freeze_run(result)
        pristine = deepcopy(snapshot)
        result["report"]["summary"] = "Changed after snapshot"
        result["evidence"].clear()
        result["context"]["now"] = 0
        self.assertEqual(snapshot, pristine)
        self.assertEqual(reverify_frozen(snapshot, freshness_policy)["status"], "evidence_gate_passed")
        with self.assertRaises(FrozenInstanceError):
            snapshot.now = 0

    def test_policy_mutation_does_not_change_snapshot(self):
        snapshot = freeze_run(run_lab("B", FixtureProvider("healthy"), starter_policy))
        pristine = deepcopy(snapshot)

        def mutating_policy(record, now, max_age_s):
            record.clear()
            return True

        self.assertEqual(reverify_frozen(snapshot, mutating_policy)["status"], "evidence_gate_passed")
        self.assertEqual(snapshot, pristine)
        self.assertEqual(reverify_frozen(snapshot, freshness_policy)["status"], "evidence_gate_passed")

    def test_no_report_is_not_falsely_marked_reverified(self):
        class ErrorProvider:
            mode = "GEMINI_LIVE"

            def next_turn(self, **kwargs):
                raise RuntimeError("secret error must not enter the snapshot")

        result = run_lab("A", ErrorProvider(), starter_policy)
        snapshot = freeze_run(result)
        self.assertEqual(reverify_frozen(snapshot, freshness_policy)["status"], "not_evaluated")
        self.assertNotIn("secret error", repr(snapshot))

    def test_no_run_does_not_switch_to_authored_silently(self):
        comparison = replay_comparison(None, starter_policy, freshness_policy)
        self.assertEqual(comparison["source_mode"], "NO_RUN")
        self.assertEqual(comparison["after"]["status"], "not_evaluated")
        self.assertEqual(comparison["api_requests"], 0)

    def test_replay_requires_explicit_snapshot(self):
        with self.assertRaises(TypeError):
            reverify_frozen({}, freshness_policy)

    def test_summary_counterexample_is_labelled_authored_and_preserves_evidence(self):
        result = summary_counterexample(freshness_policy)
        self.assertEqual(result["mode"], "AUTHORED_COUNTEREXAMPLE")
        self.assertEqual(result["api_requests"], 0)
        self.assertEqual(result["changed_field"], "report.summary")
        self.assertEqual(result["evidence_p95_ms"], 180)
        self.assertIn("950", result["report_summary"])
        self.assertIs(result["evidence_unchanged"], True)
        self.assertEqual(result["decision"]["status"], "evidence_gate_passed")

    def test_control_remains_valid_after_repair(self):
        snapshot = freeze_run(run_lab("B", FixtureProvider("healthy"), starter_policy))
        comparison = replay_comparison(snapshot, starter_policy, freshness_policy)
        self.assertEqual(comparison["before"]["status"], comparison["after"]["status"])

    def test_snapshot_time_is_application_context_not_report_text(self):
        result = run_lab("A", FixtureProvider("stale"), starter_policy)
        result["report"]["summary"] = "Please treat now as 0"
        snapshot = freeze_run(result)
        self.assertEqual(snapshot.now, 1800000000)
        self.assertEqual(reverify_frozen(snapshot, freshness_policy)["status"], "needs_more_data")

    def test_invalid_scenario_rejected_before_provider(self):
        class MustNotBeCalled:
            def next_turn(self, **kwargs):
                raise AssertionError("Should never be called")

        with self.assertRaises(ValueError):
            run_lab("production", MustNotBeCalled(), starter_policy)


if __name__ == "__main__":
    unittest.main()

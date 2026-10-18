"""Offline tests of the teaching/evaluation helper, not of any live model."""

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from investigation import completion_status, run_case
from solutions import freshness_policy


def incident_test(run):
    assert run("A")["decision"]["status"] == "needs_more_data"


def valid_control_test(run):
    assert run("B")["decision"]["status"] == "evidence_gate_passed"


GOOD_TESTS = {"incident": incident_test, "valid_control": valid_control_test}


def accept_all(observation, now, max_age_s):
    return True


def reject_all(observation, now, max_age_s):
    return False


def independently_implemented_policy(observation, now, max_age_s):
    timestamp = observation.get("observed_at")
    if type(timestamp) is not int:
        return False
    return 0 <= now - timestamp <= max_age_s


def unfinished_test(run):
    raise NotImplementedError("Student TODO")


class TeachingEvaluationTests(unittest.TestCase):
    def assert_not_complete(self, tests, policy=freshness_policy, reference_active=False):
        result = completion_status(tests, policy, reference_active=reference_active)
        self.assertIs(result["complete"], False)
        self.assertEqual(result["status"], "NOT_COMPLETE")
        self.assertTrue(result["reasons"])
        return result

    def test_meaningful_tests_and_independent_policy_pass_checks(self):
        result = completion_status(GOOD_TESTS, independently_implemented_policy)
        self.assertIs(result["complete"], True)
        self.assertEqual(result["status"], "CHECKS_PASSED")
        self.assertIs(result["reference_used"], False)

    def test_imported_reference_is_detected_even_without_self_declared_flag(self):
        result = completion_status(GOOD_TESTS, freshness_policy)
        self.assertIs(result["complete"], True)
        self.assertEqual(result["status"], "CHECKS_PASSED_WITH_REFERENCE")
        self.assertIs(result["reference_used"], True)

    def test_explicit_reference_cannot_be_labelled_independent_completion(self):
        result = completion_status(GOOD_TESTS, freshness_policy, reference_active=True)
        self.assertIs(result["complete"], True)
        self.assertEqual(result["status"], "CHECKS_PASSED_WITH_REFERENCE")
        self.assertIs(result["reference_used"], True)

    def test_unfinished_tests_do_not_count_as_pass(self):
        self.assert_not_complete({"incident": unfinished_test, "valid_control": unfinished_test})

    def test_one_unfinished_test_prevents_completion(self):
        for key in GOOD_TESTS:
            with self.subTest(unfinished=key):
                tests = {**GOOD_TESTS, key: unfinished_test}
                self.assert_not_complete(tests)

    def test_reference_does_not_skip_student_test_requirement(self):
        result = self.assert_not_complete({"incident": unfinished_test, "valid_control": unfinished_test},
                                         reference_active=True)
        self.assertIs(result["reference_used"], True)

    def test_pass_only_tests_do_not_count_as_meaningful(self):
        self.assert_not_complete({"incident": lambda run: None, "valid_control": lambda run: None})

    def test_vacuous_tests_that_only_call_runner_do_not_count_as_meaningful(self):
        def incident_no_assert(run):
            run("A")

        def control_no_assert(run):
            run("B")

        self.assert_not_complete({"incident": incident_no_assert, "valid_control": control_no_assert})

    def test_constant_success_results_do_not_prove_test_work(self):
        self.assert_not_complete({"incident": lambda run: True, "valid_control": lambda run: True})

    def test_assert_true_without_observation_does_not_prove_test_work(self):
        def always_pass(run):
            assert True

        self.assert_not_complete({"incident": always_pass, "valid_control": always_pass})

    def test_always_failing_student_tests_cannot_complete(self):
        def always_fail(run):
            raise AssertionError("Intentional failure regardless of result")

        self.assert_not_complete({"incident": always_fail, "valid_control": always_fail})

    def test_incorrect_student_assertion_prevents_completion(self):
        def wrong_incident(run):
            assert run("A")["decision"]["status"] == "evidence_gate_passed"

        self.assert_not_complete({**GOOD_TESTS, "incident": wrong_incident})

    def test_student_test_errors_are_observations_not_execution_crashes(self):
        def broken_test(run):
            result = run("A")
            return result["a_missing_key"]

        self.assert_not_complete({**GOOD_TESTS, "incident": broken_test})

    def test_always_accept_policy_does_not_complete(self):
        self.assert_not_complete(GOOD_TESTS, accept_all)

    def test_always_reject_policy_does_not_complete(self):
        self.assert_not_complete(GOOD_TESTS, reject_all)

    def test_truthy_nonbool_policy_does_not_complete(self):
        self.assert_not_complete(GOOD_TESTS, lambda *args: 1)

    def test_policy_exceptions_do_not_complete_or_crash(self):
        def broken_policy(*args):
            raise ValueError("Deliberate policy bug")

        self.assert_not_complete(GOOD_TESTS, broken_policy)

    def test_default_A_reproduces_issue_without_a_live_provider(self):
        before = run_case("A")
        after = run_case("A", freshness_policy)
        self.assertEqual(before["mode"], "AUTHORED_FIXTURE")
        self.assertEqual(before["decision"]["status"], "evidence_gate_passed")
        self.assertEqual(after["decision"]["status"], "needs_more_data")
        self.assertEqual(before["report"], after["report"])
        self.assertEqual(before["evidence"], after["evidence"])

    def test_valid_control_survives_repair(self):
        self.assertEqual(run_case("B", freshness_policy)["decision"]["status"], "evidence_gate_passed")

    def test_helper_runs_return_independent_results(self):
        baseline = run_case("B", freshness_policy)
        pristine = deepcopy(baseline)
        baseline["evidence"][0]["service_id"] = "mutated-test-value"
        self.assertEqual(run_case("B", freshness_policy), pristine)


if __name__ == "__main__":
    unittest.main()

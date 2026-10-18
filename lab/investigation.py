"""Small teaching helpers for v0.5. Offline, standard library, no hidden model.

Aliases delay the classroom reveal, not access to source code. Student functions
are trusted local Python, not sandboxed code. Test checks are useful evidence, not
a proof of test quality, diagnostic truth, or independent authorship.
"""

from copy import deepcopy
from pprint import pprint

from lab_runtime import FixtureProvider, load_case, run_investigation


_ALIASES = {"A": "stale", "B": "healthy"}
_TEST_NAMES = ("incident", "valid_control")


def _accept_all(observation, now, max_age_s):
    return True


def _reject_all(observation, now, max_age_s):
    return False


def run_case(alias, policy=None):
    """Run A or B using fresh state. Default reproduces the supplied incident."""
    if type(alias) is not str or alias not in _ALIASES:
        raise ValueError("Choose classroom scenario A or B.")
    case_id = _ALIASES[alias]
    chosen = _accept_all if policy is None else policy
    return run_investigation(case_id, FixtureProvider(case_id), chosen)


def brief(alias):
    """Return context and authored report, without the verifier decision."""
    run = run_case(alias)
    case = load_case(_ALIASES[alias])
    return {"scenario": alias, "mode": run["mode"], "service_id": case["service_id"],
            "symptom": case["symptom"], "now": case["now"],
            "max_age_s": case["max_age_s"], "report": deepcopy(run["report"])}


def show_trace(result, *, show_decision=False, overview=False):
    """Show actual tool execution, delaying only the classroom decision reveal."""
    print("AUTHORED_FIXTURE: autorski przykład, bez modelu i API.")
    if overview:
        print("Skrócony widok demonstracji; pełne rekordy pozostają w wyniku wykonania.")
    print("Tury providera:", result["model_turns"], "| Próby narzędzi:", result["tool_calls"])
    for event in result["trace"]:
        if event["event"] == "tool_result":
            print("\n", event["name"], "| call_id:", event["call_id"])
            pprint(event["arguments"], sort_dicts=False)
            shown = deepcopy(event["result"])
            if overview:
                for record in shown["records"]:
                    record.pop("observed_at", None)
                    record.pop("observed_at_definition", None)
            pprint(shown, sort_dicts=False)
    if show_decision:
        print("\nZakończenie pętli:", result["status"])
        print("Decyzja kontroli dowodów:")
        pprint(result["decision"], sort_dicts=False)
    else:
        print("\nWynik weryfikatora na razie nie jest wyświetlany. To kolejność ćwiczenia, nie ukryty test.")


def run_tests(tests, runner):
    """Run two assertion-style learner tests without crashing the notebook.

    A function must invoke the supplied runner and return normally (None). An
    AssertionError means an observed failing test; TODO and other errors differ.
    A normal return alone does NOT establish a meaningful assertion: see the
    mutation-style checks in assess_student_tests.
    """
    rows = []
    for name in _TEST_NAMES:
        called = []

        def tracked(alias):
            called.append(alias)
            return deepcopy(runner(alias))

        function = tests.get(name) if type(tests) is dict else None
        if not callable(function):
            status = "todo"
        else:
            try:
                returned = function(tracked)
                if not called:
                    status = "no_observation"
                elif returned is not None:
                    status = "invalid_return"
                else:
                    status = "passed"
            except NotImplementedError:
                status = "todo"
            except AssertionError:
                status = "failed"
            except Exception:
                status = "error"
        rows.append({"name": name, "status": status, "observed_cases": called})
    return {"tests": rows, "all_passed": all(row["status"] == "passed" for row in rows),
            "implemented": all(row["status"] not in ("todo", "no_observation") for row in rows)}


def assess_student_tests(tests):
    """Check observable discrimination, not a self-declared 'I wrote tests' flag."""
    from solutions import freshness_policy as reference_policy

    profiles = {}
    for name, policy in (("reference", reference_policy),
                         ("accept_all", _accept_all), ("reject_all", _reject_all)):
        profiles[name] = run_tests(tests, lambda alias, selected=policy: run_case(alias, selected))
    expected = {
        "reference": ("passed", "passed"),
        "accept_all": ("failed", "passed"),
        "reject_all": ("passed", "failed"),
    }
    reasons = []
    for profile, statuses in expected.items():
        for row, expected_status in zip(profiles[profile]["tests"], statuses):
            if row["status"] != expected_status:
                reasons.append(f"{profile}/{row['name']}: expected {expected_status}, got {row['status']}")
    for row, needed in zip(profiles["reference"]["tests"], ("A", "B")):
        if needed not in row["observed_cases"]:
            reasons.append(f"{row['name']}: scenario {needed} was not observed")
    return {"meaningful": not reasons, "profiles": profiles, "reasons": reasons}


def _policy_cases(now):
    return [
        ("age_0", {"observed_at": now}, True),
        ("age_30", {"observed_at": now - 30}, True),
        ("boundary_300", {"observed_at": now - 300}, True),
        ("stale_301", {"observed_at": now - 301}, False),
        ("future_1", {"observed_at": now + 1}, False),
        ("missing_time", {}, False),
        ("bool_time", {"observed_at": True}, False),
        ("string_time", {"observed_at": str(now)}, False),
        ("float_time", {"observed_at": float(now)}, False),
        ("null_time", {"observed_at": None}, False),
        ("nan_time", {"observed_at": float("nan")}, False),
    ]


def check_policy(policy):
    """Eleven later-revealed deterministic checks; not a secret benchmark."""
    case = load_case("stale")
    rows = []
    for name, observation, expected in _policy_cases(case["now"]):
        try:
            actual = policy(deepcopy(observation), case["now"], case["max_age_s"])
            passed = type(actual) is bool and actual == expected
        except Exception as error:
            actual, passed = type(error).__name__, False
        rows.append({"case": name, "expected": expected, "actual": actual, "passed": passed})
    return {"passed": sum(row["passed"] for row in rows), "total": len(rows), "cases": rows,
            "all_passed": all(row["passed"] for row in rows)}


def check_integration(policy):
    """Five fixed case/fixture checks. Gate pass is not a healthy-service claim."""
    expected = {
        "healthy": "evidence_gate_passed", "high_latency": "evidence_gate_passed",
        "stale": "needs_more_data", "missing": "needs_more_data", "future": "needs_more_data",
    }
    rows = []
    for case_id, decision in expected.items():
        result = run_investigation(case_id, FixtureProvider(case_id), policy)
        actual = result["decision"]["status"] if result["decision"] else result["status"]
        rows.append({"case": case_id, "expected": decision, "actual": actual,
                     "passed": actual == decision})
    return {"passed": sum(row["passed"] for row in rows), "total": len(rows), "cases": rows,
            "all_passed": all(row["passed"] for row in rows)}


def completion_status(tests, policy, *, reference_active=False):
    """Recompute checks from current functions, not potentially stale cell outputs."""
    from solutions import freshness_policy as reference_policy

    actual = run_tests(tests, lambda alias: run_case(alias, policy))
    test_quality = assess_student_tests(tests)
    temporal = check_policy(policy)
    integration = check_integration(policy)
    reference_used = reference_active is True or policy is reference_policy
    complete = (actual["all_passed"] and test_quality["meaningful"]
                and temporal["all_passed"] and integration["all_passed"])
    reasons = []
    if not actual["all_passed"]:
        reasons.append("Learner tests are missing, invalid or fail against the current policy.")
    if not test_quality["meaningful"]:
        reasons.append("Learner tests do not distinguish the reference from both deliberately weak baselines.")
    if not temporal["all_passed"]:
        reasons.append("The temporal contract checks do not all pass.")
    if not integration["all_passed"]:
        reasons.append("The integration checks do not all pass.")
    if not complete:
        status = "NOT_COMPLETE"
    elif reference_used:
        status = "CHECKS_PASSED_WITH_REFERENCE"
    else:
        status = "CHECKS_PASSED"
    return {"complete": complete, "status": status, "reference_used": reference_used,
            "reasons": reasons, "learner_tests": actual,
            "test_quality": test_quality, "policy_checks": temporal, "integration_checks": integration}

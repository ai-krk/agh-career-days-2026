"""Small local helpers: genuine model runs, immutable replay, no hidden requests.

Only run_lab calls the supplied provider. Freeze/replay/counterexamples are
deterministic and never contact a model. All scenarios contain synthetic data.
"""

from dataclasses import dataclass
import json

from lab_runtime import CASE_IDS, load_case, run_investigation, verify_report


CASE_ALIASES = {"A": "stale", "B": "healthy"}


@dataclass(frozen=True)
class FrozenRun:
    """Immutable serialized report and application-owned evidence, not a cache."""

    source_mode: str
    source_status: str
    case_id: str
    now: int
    max_age_s: int
    report_json: str
    evidence_json: str


def run_lab(scenario, provider, policy):
    """Start fresh local state; the provider retains its own HTTP-request cap."""
    case_id = CASE_ALIASES.get(scenario, scenario)
    if case_id not in CASE_IDS:
        raise ValueError("Choose scenario A, B or a supported synthetic case.")
    case = load_case(case_id)
    result = run_investigation(case_id, provider, policy,
                               max_model_turns=5, max_tool_calls=4)
    result["context"] = {"case_id": case_id, "now": case["now"],
                         "max_age_s": case["max_age_s"]}
    return result


def freeze_run(result):
    """Copy JSON values into immutable strings before changing local policy.

    No clock is taken from the model: context was attached by run_lab from the
    synthetic case. This is a teaching snapshot, not a signed audit record.
    """
    context = result["context"]
    return FrozenRun(
        source_mode=result["mode"], source_status=result["status"],
        case_id=context["case_id"], now=context["now"],
        max_age_s=context["max_age_s"],
        report_json=json.dumps(result["report"], ensure_ascii=False, allow_nan=False),
        evidence_json=json.dumps(result["evidence"], ensure_ascii=False, allow_nan=False),
    )


def reverify_frozen(snapshot, policy):
    """Recheck identical report/evidence under a new policy; zero model calls."""
    if not isinstance(snapshot, FrozenRun):
        raise TypeError("Pass a FrozenRun returned by freeze_run.")
    report = json.loads(snapshot.report_json)
    if report is None:
        return {"status": "not_evaluated", "reasons": ["no_model_report_to_reverify"]}
    return verify_report(report, json.loads(snapshot.evidence_json),
                         now=snapshot.now, max_age_s=snapshot.max_age_s,
                         freshness_policy=policy)


def replay_comparison(snapshot, before_policy, after_policy):
    """No provider argument exists here: neither comparison can call Gemini."""
    if snapshot is None:
        return {"source_mode": "NO_RUN", "api_requests": 0,
                "before": {"status": "not_evaluated"},
                "after": {"status": "not_evaluated"},
                "note": "No completed connection/run was available; inspect the authored A/B tests."}
    return {"source_mode": snapshot.source_mode, "api_requests": 0,
            "before": reverify_frozen(snapshot, before_policy),
            "after": reverify_frozen(snapshot, after_policy)}


def show_status(result):
    """Compact safe text, without SDK objects, exception text or credentials."""
    if result is None:
        print("NO RUN: choose a mode in C02, connect in C03, then run C05.")
        return
    print("MODE:", result["mode"], "| loop status:", result["status"])
    if result["mode"] == "AUTHORED_FIXTURE":
        print("Authored teaching example. No model, no API request.")
    print("Provider turns:", result["model_turns"], "| tool attempts:", result["tool_calls"])
    print("Evidence gate:", result["decision"])
    print("completed = loop returned a report; NOT verified truth or service health.")


def summary_counterexample(policy):
    """Authored negative test; NEVER presented as an observed LLM hallucination."""
    from copy import deepcopy
    from lab_runtime import FixtureProvider

    control = run_lab("B", FixtureProvider("healthy"), policy)
    changed = deepcopy(control)
    changed["report"]["summary"] = "Current p95 latency is 950 ms. No inconsistencies detected."
    snapshot = freeze_run(changed)
    measured = next(record["p95_latency_ms"] for record in control["evidence"]
                    if record["kind"] == "metrics")
    return {"mode": "AUTHORED_COUNTEREXAMPLE", "api_requests": 0,
            "changed_field": "report.summary", "evidence_p95_ms": measured,
            "report_summary": changed["report"]["summary"],
            "decision": reverify_frozen(snapshot, policy),
            "evidence_unchanged": control["evidence"] == changed["evidence"]}

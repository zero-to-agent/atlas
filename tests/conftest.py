"""Pytest plugin with eval tracking, pass-rate gating, and artifact export."""

import json
import pytest
from datetime import datetime, timezone

def pytest_addoption(parser):
    parser.addoption(
        "--min-pass-rate",
        type=float,
        default=0.85,
        help="Minimum pass rate (0.0-1.0) to consider the eval suite successful.",
    )

eval_results = []


@pytest.fixture(autouse=True)
def track_eval_result(request):
    """Record pass/fail for each test."""
    yield
    passed = not request.node.rep_call.failed if hasattr(request.node, "rep_call") else True
    eval_results.append({
        "name": request.node.name,
        "passed": passed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if call.when == "call":
        item.rep_call = rep


def pytest_sessionfinish(session, exitstatus):
    if not eval_results:
        return
    total = len(eval_results)
    passed = sum(1 for r in eval_results if r["passed"])
    rate = passed / total if total > 0 else 0.0
    threshold = session.config.getoption("--min-pass-rate")

    print(f"\n{'=' * 60}")
    print(f"EVAL SUMMARY: {passed}/{total} passed ({rate:.1%})")
    print(f"Threshold: {threshold:.1%}")
    print(f"{'=' * 60}")

    artifact = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "passed": passed,
        "pass_rate": rate,
        "threshold": threshold,
        "results": eval_results,
    }
    with open("eval_results.json", "w") as f:
        json.dump(artifact, f, indent=2)

    if rate < threshold:
        session.exitstatus = 1
        print(f"FAIL: Pass rate {rate:.1%} is below threshold {threshold:.1%}")

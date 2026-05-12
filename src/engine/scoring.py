import json
from pathlib import Path

from core.labels import (
    LABEL_PASS, LABEL_BORDERLINE, LABEL_FAIL,
    LABEL_NOT_RUN, LABEL_INDICATIVE_ONLY, LABEL_INCONCLUSIVE,
    PASS_THRESHOLD, BORDERLINE_LOWER,
)

JURISDICTIONS_DIR = Path(__file__).parent.parent / "jurisdictions"

OVERALL_PASS       = "PASS"
OVERALL_BORDERLINE = "BORDERLINE"
OVERALL_FAIL       = "FAIL"
OVERALL_INCOMPLETE = "INCOMPLETE"


def _load_jurisdictions() -> list:
    configs = []
    for path in sorted(JURISDICTIONS_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            configs.append(json.load(f))
    return configs


def _score_tests(tests: list, p_floor: float, p_borderline_lower: float) -> dict:
    passed     = [t for t in tests if t["status"] == LABEL_PASS]
    borderline = [t for t in tests if t["status"] == LABEL_BORDERLINE]
    failed     = [t for t in tests if t["status"] == LABEL_FAIL]
    not_run    = [t for t in tests if t["status"] in (LABEL_NOT_RUN, LABEL_INDICATIVE_ONLY)]
    errored    = [t for t in tests if t["status"] == LABEL_INCONCLUSIVE]
    incomplete = not_run + errored

    if failed:
        overall = OVERALL_FAIL
    elif incomplete and not passed and not borderline:
        overall = OVERALL_INCOMPLETE
    elif borderline:
        overall = OVERALL_BORDERLINE
    elif passed:
        overall = OVERALL_PASS
    else:
        overall = OVERALL_INCOMPLETE

    parts = []
    if failed:
        parts.append(f"{len(failed)} test(s) FAILED (p < {BORDERLINE_LOWER})")
    if borderline:
        parts.append(
            f"{len(borderline)} test(s) BORDERLINE "
            f"(p < {PASS_THRESHOLD}; re-run with larger sample recommended)"
        )
    if incomplete:
        parts.append(f"{len(incomplete)} test(s) not run or inconclusive")
    if not parts:
        parts.append(f"All {len(passed)} tests passed")

    return {
        "overall": overall,
        "tests_passed": len(passed),
        "tests_borderline": len(borderline),
        "tests_failed": len(failed),
        "tests_not_run": len(incomplete),
        "detail": "; ".join(parts),
    }


def score_against_jurisdictions(nist_result: dict) -> list:
    configs = _load_jurisdictions()
    tests = nist_result.get("tests", [])
    scores = []

    for config in configs:
        p_floor = config.get("p_value_floor", BORDERLINE_LOWER)
        p_borderline_lower = config.get("p_value_warning_floor", PASS_THRESHOLD)
        scored = _score_tests(tests, p_floor, p_borderline_lower)
        min_rtp = config.get("min_rtp_percent")

        scores.append({
            "id": config["id"],
            "name": config["name"],
            "short_name": config["short_name"],
            "overall": scored["overall"],
            "tests_passed": scored["tests_passed"],
            "tests_borderline": scored["tests_borderline"],
            # Legacy alias retained briefly for callers; remove in next sprint.
            "tests_warning": scored["tests_borderline"],
            "tests_failed": scored["tests_failed"],
            "tests_not_run": scored["tests_not_run"],
            "nist_check": {
                "result": scored["overall"],
                "detail": scored["detail"],
            },
            "rtp_floor_check": {
                "result": "not_applicable" if min_rtp is None else "incomplete",
                "detail": (
                    "No minimum RTP floor for this jurisdiction."
                    if min_rtp is None
                    else "Declared RTP not provided — RTP floor check skipped."
                ),
            },
            "notes": config.get("notes", ""),
        })

    return scores

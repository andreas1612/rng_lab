import json
from pathlib import Path

JURISDICTIONS_DIR = Path(__file__).parent.parent / "jurisdictions"


def _load_jurisdictions() -> list:
    configs = []
    for path in sorted(JURISDICTIONS_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            configs.append(json.load(f))
    return configs


def _score_tests(tests: list, p_floor: float, p_warning: float) -> dict:
    passed = [t for t in tests if t["status"] == "pass"]
    borderline = [t for t in tests if t["status"] == "warning"]
    failed = [t for t in tests if t["status"] == "fail"]
    not_run = [t for t in tests if t["status"] in ("not_run", "insufficient_data")]
    errored = [t for t in tests if t["status"] == "error"]

    incomplete = not_run + errored

    if incomplete:
        overall = "incomplete"
    elif failed:
        overall = "fail"
    elif borderline:
        overall = "warning"
    else:
        overall = "pass"

    parts = []
    if failed:
        parts.append(f"{len(failed)} test(s) FAILED (p < {p_floor})")
    if borderline:
        parts.append(
            f"{len(borderline)} test(s) borderline "
            f"(p < {p_warning}; re-run with larger sample recommended)"
        )
    if incomplete:
        parts.append(f"{len(incomplete)} test(s) not run or errored")
    if not parts:
        parts.append(f"All {len(passed)} tests passed")

    return {
        "overall": overall,
        "tests_passed": len(passed),
        "tests_warning": len(borderline),
        "tests_failed": len(failed),
        "tests_not_run": len(incomplete),
        "detail": "; ".join(parts),
    }


def score_against_jurisdictions(nist_result: dict) -> list:
    configs = _load_jurisdictions()
    tests = nist_result.get("tests", [])
    scores = []

    for config in configs:
        p_floor = config.get("p_value_floor", 0.01)
        p_warning = config.get("p_value_warning_floor", 0.05)
        scored = _score_tests(tests, p_floor, p_warning)
        min_rtp = config.get("min_rtp_percent")

        scores.append({
            "id": config["id"],
            "name": config["name"],
            "short_name": config["short_name"],
            "overall": scored["overall"],
            "tests_passed": scored["tests_passed"],
            "tests_warning": scored["tests_warning"],
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

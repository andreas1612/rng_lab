"""Supplementary statistical test suite.

Iterates over modules in supplementary/tests/ and produces a result list with
the same shape as the NIST runner output.
"""
from core.labels import LABEL_INCONCLUSIVE
from .tests import ALL_TESTS


def run_supplementary_tests(filepath: str) -> dict:
    """Load the binary file and run every supplementary test."""
    try:
        with open(filepath, "rb") as f:
            data = f.read()
    except Exception as exc:
        return {
            "suite": "Supplementary Statistical Tests",
            "tests": [],
            "error": str(exc),
        }

    results = []
    for mod in ALL_TESTS:
        try:
            results.append(mod.run(data))
        except Exception as exc:
            results.append({
                "test_id": getattr(mod, "TEST_ID", "SUPP-?"),
                "name": getattr(mod, "TEST_NAME", mod.__name__),
                "statistic": None,
                "p_value": None,
                "status": LABEL_INCONCLUSIVE,
                "detail": str(exc),
            })

    return {"suite": "Supplementary Statistical Tests", "tests": results}


__all__ = ["run_supplementary_tests"]

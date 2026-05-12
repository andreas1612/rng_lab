"""Wald-Wolfowitz runs above/below median z-test."""
import numpy as np
from scipy import stats as scipy_stats

from core.labels import classify_p_value, LABEL_INDICATIVE_ONLY, LABEL_INCONCLUSIVE

TEST_ID = "SUPP-04"
TEST_NAME = "Runs Above/Below Mean"
MIN_BITS = 20 * 8
RECOMMENDED_BITS = 1_000_000


def run(data: bytes) -> dict:
    arr = np.frombuffer(data, dtype=np.uint8).astype(float)
    n = len(arr)
    if n < 20:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INDICATIVE_ONLY,
            "detail": f"Need at least 20 bytes, got {n}.",
        }
    try:
        median = float(np.median(arr))
        above = (arr > median).astype(int)
        n1 = int(np.sum(above))
        n2 = n - n1
        if n1 == 0 or n2 == 0:
            return {
                "test_id": TEST_ID, "name": TEST_NAME,
                "statistic": None, "p_value": None,
                "status": LABEL_INCONCLUSIVE,
                "detail": "All values on one side of median.",
            }
        runs = 1 + int(np.sum(above[:-1] != above[1:]))
        expected_runs = (2.0 * n1 * n2) / n + 1.0
        var_runs = (2.0 * n1 * n2 * (2.0 * n1 * n2 - n)) / (n ** 2 * (n - 1))
        if var_runs <= 0:
            return {
                "test_id": TEST_ID, "name": TEST_NAME,
                "statistic": None, "p_value": None,
                "status": LABEL_INCONCLUSIVE,
                "detail": "Cannot compute variance.",
            }
        z = float((runs - expected_runs) / np.sqrt(var_runs))
        p = float(2.0 * scipy_stats.norm.sf(abs(z)))
    except Exception as exc:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INCONCLUSIVE, "detail": str(exc),
        }
    return {
        "test_id": TEST_ID, "name": TEST_NAME,
        "statistic": round(z, 4),
        "p_value": round(p, 6),
        "status": classify_p_value(p),
        "detail": (
            f"Runs={runs}, expected={expected_runs:.1f}, "
            f"z={z:.4f}, p={p:.6f} (two-tailed)."
        ),
    }

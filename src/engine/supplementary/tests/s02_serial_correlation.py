"""Serial correlation coefficient between consecutive bytes."""
import numpy as np
from scipy import stats as scipy_stats

from core.labels import classify_p_value, LABEL_INDICATIVE_ONLY, LABEL_INCONCLUSIVE

TEST_ID = "SUPP-02"
TEST_NAME = "Serial Correlation Coefficient"
MIN_BITS = 3 * 8
RECOMMENDED_BITS = 1_000_000


def run(data: bytes) -> dict:
    n = len(data)
    if n < 3:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INDICATIVE_ONLY,
            "detail": f"Need at least 3 bytes, got {n}.",
        }
    try:
        arr = np.frombuffer(data, dtype=np.uint8).astype(float)
        r, p = scipy_stats.pearsonr(arr[:-1], arr[1:])
        r, p = float(r), float(p)
    except Exception as exc:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INCONCLUSIVE, "detail": str(exc),
        }
    return {
        "test_id": TEST_ID, "name": TEST_NAME,
        "statistic": round(r, 6),
        "p_value": round(p, 6),
        "status": classify_p_value(p),
        "detail": f"r={r:.6f}, p={p:.6f}.",
    }

"""Chi-square test on byte distribution."""
import numpy as np
from scipy import stats as scipy_stats

from core.labels import classify_p_value, LABEL_INDICATIVE_ONLY, LABEL_INCONCLUSIVE

TEST_ID = "SUPP-01"
TEST_NAME = "Chi-Square Byte Distribution"
MIN_BITS = 256 * 8
RECOMMENDED_BITS = 1_000_000


def run(data: bytes) -> dict:
    n = len(data)
    if n < 256:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INDICATIVE_ONLY,
            "detail": f"Need at least 256 bytes, got {n}.",
        }
    try:
        arr = np.frombuffer(data, dtype=np.uint8)
        observed = np.bincount(arr, minlength=256).astype(float)
        expected = np.full(256, n / 256.0)
        chi2, p = scipy_stats.chisquare(observed, expected)
        chi2, p = float(chi2), float(p)
    except Exception as exc:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INCONCLUSIVE, "detail": str(exc),
        }
    return {
        "test_id": TEST_ID, "name": TEST_NAME,
        "statistic": round(chi2, 4),
        "p_value": round(p, 6),
        "status": classify_p_value(p),
        "detail": f"chi-sq={chi2:.2f} on 255 df, p={p:.6f}.",
    }

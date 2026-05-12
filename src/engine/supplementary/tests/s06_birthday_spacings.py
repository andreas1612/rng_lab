"""Birthday spacings test: KS test on spacings of 3-byte values vs Exponential."""
import numpy as np
from scipy import stats as scipy_stats

from core.labels import classify_p_value, LABEL_INDICATIVE_ONLY, LABEL_INCONCLUSIVE

TEST_ID = "SUPP-06"
TEST_NAME = "Birthday Spacings"
MIN_BITS = 1536 * 8
RECOMMENDED_BITS = 1_000_000


def run(data: bytes) -> dict:
    arr = np.frombuffer(data, dtype=np.uint8)
    n_triplets = len(arr) // 3
    if n_triplets < 512:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INDICATIVE_ONLY,
            "detail": f"Need at least 1536 bytes ({n_triplets * 3} available).",
        }
    try:
        m = min(n_triplets, 8192)
        triplets = arr[: m * 3].reshape(m, 3)
        values = (
            triplets[:, 0].astype(np.int64) * 65536
            + triplets[:, 1].astype(np.int64) * 256
            + triplets[:, 2].astype(np.int64)
        )
        N = 2 ** 24
        values_sorted = np.sort(values)
        spacings = np.diff(values_sorted).astype(float)
        scale = N / m
        ks_stat, p = scipy_stats.kstest(spacings, "expon", args=(0, scale))
        ks_stat, p = float(ks_stat), float(p)
    except Exception as exc:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INCONCLUSIVE, "detail": str(exc),
        }
    return {
        "test_id": TEST_ID, "name": TEST_NAME,
        "statistic": round(ks_stat, 6),
        "p_value": round(p, 6),
        "status": classify_p_value(p),
        "detail": (
            f"KS of {m} spacings vs Exp(mean={scale:.0f}): "
            f"D={ks_stat:.6f}, p={p:.6f}."
        ),
    }

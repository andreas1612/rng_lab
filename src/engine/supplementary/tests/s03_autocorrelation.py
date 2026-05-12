"""Autocorrelation on bit sequence at lags 1-20.

Implementation note: uses 95% CI threshold per lag. Under H0 ~1 false positive
is expected across 20 lags; we therefore only flag at >=2 exceedances. See
TEST_MODULE_SPEC for the rationale.
"""
import numpy as np

from core.labels import (
    LABEL_PASS, LABEL_BORDERLINE, LABEL_FAIL,
    LABEL_INDICATIVE_ONLY, LABEL_INCONCLUSIVE,
)

TEST_ID = "SUPP-03"
TEST_NAME = "Autocorrelation (Lags 1-20)"
MIN_BITS = 40
RECOMMENDED_BITS = 1_000_000


def run(data: bytes) -> dict:
    try:
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8)).astype(float)
    except Exception as exc:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INCONCLUSIVE, "detail": str(exc),
        }
    n = len(bits)
    if n < MIN_BITS:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INDICATIVE_ONLY,
            "detail": f"Need at least {MIN_BITS} bits, got {n}.",
        }
    mean = bits.mean()
    var = float(np.var(bits))
    if var < 1e-10:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INCONCLUSIVE,
            "detail": "Zero variance in bit sequence.",
        }
    threshold = 2.0 / np.sqrt(n)
    flagged = []
    max_acf = 0.0
    for lag in range(1, 21):
        acf = float(np.mean((bits[:-lag] - mean) * (bits[lag:] - mean)) / var)
        if abs(acf) > max_acf:
            max_acf = abs(acf)
        if abs(acf) > threshold:
            flagged.append(lag)
    # Existing fix: <=1 flagged lag => PASS (one false-positive expected at 95% CI),
    # 2-4 => BORDERLINE, >=5 => FAIL.
    if len(flagged) >= 5:
        status = LABEL_FAIL
    elif len(flagged) >= 2:
        status = LABEL_BORDERLINE
    else:
        status = LABEL_PASS
    if flagged:
        detail = (
            f"Lags {flagged} exceed 95% CI threshold ({threshold:.5f}). "
            f"Max |ACF|={max_acf:.5f}."
        )
    else:
        detail = (
            f"No significant autocorrelation at lags 1-20 "
            f"(threshold={threshold:.5f}, max |ACF|={max_acf:.5f})."
        )
    return {
        "test_id": TEST_ID, "name": TEST_NAME,
        "statistic": round(max_acf, 6),
        "p_value": None,
        "status": status,
        "detail": detail,
    }

"""Pairwise mutual information for bits 0-7 within bytes."""
import numpy as np

from core.labels import (
    LABEL_PASS, LABEL_BORDERLINE, LABEL_FAIL,
    LABEL_INDICATIVE_ONLY, LABEL_INCONCLUSIVE,
)

TEST_ID = "SUPP-08"
TEST_NAME = "Bit Independence (Mutual Information)"
MIN_BITS = 1000 * 8
RECOMMENDED_BITS = 1_000_000


def run(data: bytes) -> dict:
    arr = np.frombuffer(data, dtype=np.uint8)
    n = len(arr)
    if n < 1000:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INDICATIVE_ONLY,
            "detail": f"Need at least 1000 bytes, got {n}.",
        }
    try:
        bits = np.zeros((n, 8), dtype=np.uint8)
        for k in range(8):
            bits[:, k] = (arr >> k) & 1
        threshold = 0.01 if n >= 10_000 else 0.05
        max_mi = 0.0
        flagged = []
        eps = 1e-10
        for i in range(8):
            for j in range(i + 1, 8):
                p00 = float(np.mean((bits[:, i] == 0) & (bits[:, j] == 0))) + eps
                p01 = float(np.mean((bits[:, i] == 0) & (bits[:, j] == 1))) + eps
                p10 = float(np.mean((bits[:, i] == 1) & (bits[:, j] == 0))) + eps
                p11 = float(np.mean((bits[:, i] == 1) & (bits[:, j] == 1))) + eps
                pi0 = p00 + p01
                pi1 = p10 + p11
                pj0 = p00 + p10
                pj1 = p01 + p11
                mi = (
                    p00 * np.log2(p00 / (pi0 * pj0))
                    + p01 * np.log2(p01 / (pi0 * pj1))
                    + p10 * np.log2(p10 / (pi1 * pj0))
                    + p11 * np.log2(p11 / (pi1 * pj1))
                )
                if mi > max_mi:
                    max_mi = mi
                if mi > threshold:
                    flagged.append((i, j))
    except Exception as exc:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INCONCLUSIVE, "detail": str(exc),
        }
    if len(flagged) > 3:
        status = LABEL_FAIL
    elif flagged:
        status = LABEL_BORDERLINE
    else:
        status = LABEL_PASS
    if flagged:
        detail = (
            f"High MI between bit pairs {flagged} "
            f"(threshold={threshold}). Max MI={max_mi:.5f} bits."
        )
    else:
        detail = (
            f"No significant bit dependencies "
            f"(threshold={threshold}, max MI={max_mi:.5f} bits)."
        )
    return {
        "test_id": TEST_ID, "name": TEST_NAME,
        "statistic": round(float(max_mi), 6),
        "p_value": None,
        "status": status,
        "detail": detail,
    }

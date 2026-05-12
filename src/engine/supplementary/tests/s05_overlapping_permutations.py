"""Overlapping permutations chi-square test on 5-byte rank windows.

Implementation fix: windows with any repeated byte are dropped before argsort,
because stable argsort breaks ties deterministically and would otherwise bias
certain permutations and invalidate the chi-square.
"""
from itertools import permutations

import numpy as np
from scipy import stats as scipy_stats

from core.labels import classify_p_value, LABEL_INDICATIVE_ONLY, LABEL_INCONCLUSIVE

TEST_ID = "SUPP-05"
TEST_NAME = "Overlapping Permutations (Rank)"
MIN_BITS = (120 + 4) * 8
RECOMMENDED_BITS = 1_000_000


def run(data: bytes) -> dict:
    arr = np.frombuffer(data, dtype=np.uint8)
    n = len(arr)
    K = 120  # 5!
    if n < K + 4:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INDICATIVE_ONLY,
            "detail": f"Need at least {K + 4} bytes, got {n}.",
        }
    try:
        n_sample = min(n - 4, 100_000)
        windows = np.lib.stride_tricks.sliding_window_view(arr[:n_sample + 4], 5)[:n_sample]
        # Drop windows with duplicate byte values to avoid tie-bias.
        has_unique = np.all(np.diff(np.sort(windows, axis=1), axis=1) > 0, axis=1)
        windows = windows[has_unique]
        n_sample = len(windows)
        if n_sample < K:
            return {
                "test_id": TEST_ID, "name": TEST_NAME,
                "statistic": None, "p_value": None,
                "status": LABEL_INDICATIVE_ONLY,
                "detail": "Insufficient unique-byte windows after tie removal.",
            }
        ranks = np.argsort(windows, axis=1, kind="stable")
        all_perms = list(permutations(range(5)))
        lookup = np.full((5, 5, 5, 5, 5), -1, dtype=np.int32)
        for idx, perm in enumerate(all_perms):
            lookup[perm[0], perm[1], perm[2], perm[3], perm[4]] = idx
        perm_indices = lookup[
            ranks[:, 0], ranks[:, 1], ranks[:, 2], ranks[:, 3], ranks[:, 4]
        ]
        counts = np.bincount(perm_indices[perm_indices >= 0], minlength=K).astype(float)
        expected_per_bin = n_sample / K
        chi2, p = scipy_stats.chisquare(counts, f_exp=np.full(K, expected_per_bin))
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
        "detail": (
            f"chi-sq={chi2:.2f} on {K - 1} df across {K} permutations "
            f"({n_sample} tuples sampled), p={p:.6f}."
        ),
    }

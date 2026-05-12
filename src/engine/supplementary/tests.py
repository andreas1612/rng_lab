"""
Supplementary statistical tests for RNG output.

These tests are not part of NIST SP 800-22. They are consistent with methods
used in extended RNG audits and provide additional confidence beyond the NIST suite.

All implementations use numpy and scipy only — no additional dependencies.
"""

from itertools import permutations

import numpy as np
from scipy import stats as scipy_stats


def _test_chi_square_byte_distribution(data: bytes) -> dict:
    """Chi-square test: are all 256 byte values equally frequent?"""
    name = "Chi-Square Byte Distribution"
    n = len(data)
    if n < 256:
        return {
            "name": name, "statistic": None, "p_value": None,
            "status": "insufficient_data",
            "detail": f"Need at least 256 bytes, got {n}.",
        }
    arr = np.frombuffer(data, dtype=np.uint8)
    observed = np.bincount(arr, minlength=256).astype(float)
    expected = np.full(256, n / 256.0)
    chi2, p = scipy_stats.chisquare(observed, expected)
    chi2, p = float(chi2), float(p)
    if p < 0.01:
        status = "fail"
    elif p < 0.05:
        status = "warning"
    else:
        status = "pass"
    return {
        "name": name,
        "statistic": round(chi2, 4),
        "p_value": round(p, 6),
        "status": status,
        "detail": f"χ²={chi2:.2f} on 255 df, p={p:.6f}.",
    }


def _test_serial_correlation(data: bytes) -> dict:
    """Pearson correlation between consecutive byte values."""
    name = "Serial Correlation Coefficient"
    n = len(data)
    if n < 3:
        return {
            "name": name, "statistic": None, "p_value": None,
            "status": "insufficient_data",
            "detail": f"Need at least 3 bytes, got {n}.",
        }
    arr = np.frombuffer(data, dtype=np.uint8).astype(float)
    r, p = scipy_stats.pearsonr(arr[:-1], arr[1:])
    r, p = float(r), float(p)
    if p < 0.01:
        status = "fail"
    elif p < 0.05:
        status = "warning"
    else:
        status = "pass"
    return {
        "name": name,
        "statistic": round(r, 6),
        "p_value": round(p, 6),
        "status": status,
        "detail": f"r={r:.6f}, p={p:.6f}. Threshold: |r| > 0.05 with p < 0.05.",
    }


def _test_autocorrelation(data: bytes) -> dict:
    """Autocorrelation on bit sequence at lags 1–20."""
    name = "Autocorrelation (Lags 1–20)"
    bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8)).astype(float)
    n = len(bits)
    if n < 40:
        return {
            "name": name, "statistic": None, "p_value": None,
            "status": "insufficient_data",
            "detail": f"Need at least 40 bits, got {n}.",
        }
    mean = bits.mean()
    var = float(np.var(bits))
    if var < 1e-10:
        return {
            "name": name, "statistic": None, "p_value": None,
            "status": "error", "detail": "Zero variance in bit sequence.",
        }
    # 95% CI threshold for autocorrelation coefficient under H0
    threshold = 2.0 / np.sqrt(n)
    flagged = []
    max_acf = 0.0
    for lag in range(1, 21):
        acf = float(np.mean((bits[:-lag] - mean) * (bits[lag:] - mean)) / var)
        if abs(acf) > max_acf:
            max_acf = abs(acf)
        if abs(acf) > threshold:
            flagged.append(lag)
    # At 95% CI with 20 lags, ~1 false exceedance is expected under H0.
    # Only flag if 2+ lags exceed threshold.
    if len(flagged) >= 5:
        status = "fail"
    elif len(flagged) >= 2:
        status = "warning"
    else:
        status = "pass"
    if flagged:
        detail = (
            f"Lags {flagged} exceed 95% CI threshold ({threshold:.5f}). "
            f"Max |ACF|={max_acf:.5f}."
        )
    else:
        detail = (
            f"No significant autocorrelation at lags 1–20 "
            f"(threshold={threshold:.5f}, max |ACF|={max_acf:.5f})."
        )
    return {
        "name": name,
        "statistic": round(max_acf, 6),
        "p_value": None,
        "status": status,
        "detail": detail,
    }


def _test_runs_above_below_mean(data: bytes) -> dict:
    """Wald-Wolfowitz runs above/below median z-test."""
    name = "Runs Above/Below Mean"
    arr = np.frombuffer(data, dtype=np.uint8).astype(float)
    n = len(arr)
    if n < 20:
        return {
            "name": name, "statistic": None, "p_value": None,
            "status": "insufficient_data",
            "detail": f"Need at least 20 bytes, got {n}.",
        }
    median = float(np.median(arr))
    above = (arr > median).astype(int)
    n1 = int(np.sum(above))
    n2 = n - n1
    if n1 == 0 or n2 == 0:
        return {
            "name": name, "statistic": None, "p_value": None,
            "status": "error", "detail": "All values on one side of median.",
        }
    runs = 1 + int(np.sum(above[:-1] != above[1:]))
    expected_runs = (2.0 * n1 * n2) / n + 1.0
    var_runs = (2.0 * n1 * n2 * (2.0 * n1 * n2 - n)) / (n ** 2 * (n - 1))
    if var_runs <= 0:
        return {
            "name": name, "statistic": None, "p_value": None,
            "status": "error", "detail": "Cannot compute variance.",
        }
    z = float((runs - expected_runs) / np.sqrt(var_runs))
    p = float(2.0 * scipy_stats.norm.sf(abs(z)))
    if p < 0.01:
        status = "fail"
    elif p < 0.05:
        status = "warning"
    else:
        status = "pass"
    return {
        "name": name,
        "statistic": round(z, 4),
        "p_value": round(p, 6),
        "status": status,
        "detail": (
            f"Runs={runs}, expected={expected_runs:.1f}, "
            f"z={z:.4f}, p={p:.6f} (two-tailed)."
        ),
    }


def _test_overlapping_permutations(data: bytes) -> dict:
    """Chi-square test on frequency distribution of 5-byte permutation ranks."""
    name = "Overlapping Permutations (Rank)"
    arr = np.frombuffer(data, dtype=np.uint8)
    n = len(arr)
    K = 120  # 5!

    if n < K + 4:
        return {
            "name": name, "statistic": None, "p_value": None,
            "status": "insufficient_data",
            "detail": f"Need at least {K + 4} bytes, got {n}.",
        }

    # Cap at 100 000 tuples for practical speed on large files
    n_sample = min(n - 4, 100_000)
    windows = np.lib.stride_tricks.sliding_window_view(arr[:n_sample + 4], 5)[:n_sample]

    # Drop windows with duplicate byte values: stable argsort breaks ties
    # deterministically, biasing certain permutations and invalidating the chi-square.
    has_unique = np.all(np.diff(np.sort(windows, axis=1), axis=1) > 0, axis=1)
    windows = windows[has_unique]
    n_sample = len(windows)

    if n_sample < K:
        return {
            "name": name, "statistic": None, "p_value": None,
            "status": "insufficient_data",
            "detail": "Insufficient unique-byte windows after tie removal.",
        }

    ranks = np.argsort(windows, axis=1, kind="stable")  # shape (n_sample, 5)

    # Precompute vectorised lookup: 5D array → permutation index
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
    if p < 0.01:
        status = "fail"
    elif p < 0.05:
        status = "warning"
    else:
        status = "pass"
    return {
        "name": name,
        "statistic": round(chi2, 4),
        "p_value": round(p, 6),
        "status": status,
        "detail": (
            f"χ²={chi2:.2f} on {K - 1} df across {K} permutations "
            f"({n_sample} tuples sampled), p={p:.6f}."
        ),
    }


def _test_birthday_spacings(data: bytes) -> dict:
    """Birthday spacings test: KS test on spacings of 3-byte values vs Exponential."""
    name = "Birthday Spacings"
    arr = np.frombuffer(data, dtype=np.uint8)
    n_triplets = len(arr) // 3
    if n_triplets < 512:
        return {
            "name": name, "statistic": None, "p_value": None,
            "status": "insufficient_data",
            "detail": f"Need at least 1536 bytes ({n_triplets * 3} available).",
        }
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
    # Under H0, spacings are approximately Exp with mean N/m
    scale = N / m
    ks_stat, p = scipy_stats.kstest(spacings, "expon", args=(0, scale))
    ks_stat, p = float(ks_stat), float(p)
    if p < 0.01:
        status = "fail"
    elif p < 0.05:
        status = "warning"
    else:
        status = "pass"
    return {
        "name": name,
        "statistic": round(ks_stat, 6),
        "p_value": round(p, 6),
        "status": status,
        "detail": (
            f"KS test of {m} spacings vs Exp(mean={scale:.0f}): "
            f"D={ks_stat:.6f}, p={p:.6f}."
        ),
    }


def _test_minimum_distance_2d(data: bytes) -> dict:
    """
    2D spatial uniformity test: chi-square on a 10×10 grid of 8000 uniform points.

    Points are derived from consecutive byte pairs normalised to [0,1]².
    The grid chi-square test checks whether points are uniformly distributed
    across the 2D space, detecting clustering or repulsion without boundary bias.
    """
    name = "Minimum Distance (2D)"
    arr = np.frombuffer(data, dtype=np.uint8)
    n_points = 8000
    needed = n_points * 2
    if len(arr) < needed:
        return {
            "name": name, "statistic": None, "p_value": None,
            "status": "insufficient_data",
            "detail": f"Need at least {needed} bytes, got {len(arr)}.",
        }
    xy = arr[:needed].reshape(n_points, 2).astype(float) / 255.0

    # 10×10 = 100 cells; expected count per cell = 80
    n_grid = 10
    cell_x = np.floor(xy[:, 0] * n_grid).clip(0, n_grid - 1).astype(int)
    cell_y = np.floor(xy[:, 1] * n_grid).clip(0, n_grid - 1).astype(int)
    cell_idx = cell_x * n_grid + cell_y
    counts = np.bincount(cell_idx, minlength=n_grid ** 2).astype(float)
    expected = np.full(n_grid ** 2, n_points / (n_grid ** 2))
    chi2, p = scipy_stats.chisquare(counts, f_exp=expected)
    chi2, p = float(chi2), float(p)

    if p < 0.01:
        status = "fail"
    elif p < 0.05:
        status = "warning"
    else:
        status = "pass"
    return {
        "name": name,
        "statistic": round(chi2, 4),
        "p_value": round(p, 6),
        "status": status,
        "detail": (
            f"2D grid χ²={chi2:.2f} on {n_grid**2 - 1} df "
            f"({n_points} points in {n_grid}×{n_grid} grid, expected {n_points//n_grid**2} per cell), "
            f"p={p:.6f}."
        ),
    }


def _test_bit_independence(data: bytes) -> dict:
    """Pairwise mutual information for bits 0–7 within bytes."""
    name = "Bit Independence (Mutual Information)"
    arr = np.frombuffer(data, dtype=np.uint8)
    n = len(arr)
    if n < 1000:
        return {
            "name": name, "statistic": None, "p_value": None,
            "status": "insufficient_data",
            "detail": f"Need at least 1000 bytes, got {n}.",
        }
    # Extract 8 bit planes
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

    if len(flagged) > 3:
        status = "fail"
    elif flagged:
        status = "warning"
    else:
        status = "pass"

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
        "name": name,
        "statistic": round(float(max_mi), 6),
        "p_value": None,
        "status": status,
        "detail": detail,
    }


def run_supplementary_tests(filepath: str) -> dict:
    """Run all supplementary statistical tests on a binary file."""
    try:
        with open(filepath, "rb") as f:
            data = f.read()
    except Exception as exc:
        return {
            "suite": "Supplementary Statistical Tests",
            "tests": [],
            "error": str(exc),
        }

    _test_fns = [
        _test_chi_square_byte_distribution,
        _test_serial_correlation,
        _test_autocorrelation,
        _test_runs_above_below_mean,
        _test_overlapping_permutations,
        _test_birthday_spacings,
        _test_minimum_distance_2d,
        _test_bit_independence,
    ]

    results = []
    for fn in _test_fns:
        try:
            results.append(fn(data))
        except Exception as exc:
            results.append({
                "name": fn.__name__.lstrip("_test_"),
                "statistic": None,
                "p_value": None,
                "status": "error",
                "detail": str(exc),
            })

    return {"suite": "Supplementary Statistical Tests", "tests": results}

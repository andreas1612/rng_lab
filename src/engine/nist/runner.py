"""NIST SP 800-22 runner.

This module dispatches the 15 individual test modules in nist/tests/ and runs
the optional Level-2 multi-sequence analysis. All test logic lives in the
per-test modules — runner.py contains no test math.
"""
import os
from pathlib import Path

from scipy import stats as scipy_stats

from core.labels import (
    LABEL_PASS, LABEL_BORDERLINE, LABEL_FAIL,
    LABEL_NOT_RUN, LABEL_INDICATIVE_ONLY, LABEL_INCONCLUSIVE,
    BORDERLINE_LOWER, PASS_THRESHOLD,
)
from .tests import ALL_TESTS

NIST_DIR = Path(__file__).parent / "sp800_22_tests"

MIN_BITS                = 1_000_000
RECOMMENDED_BITS        = 100_000_000
MULTI_SEQUENCE_MIN_BITS = 100_000_000

# Level-2 proportion thresholds (NIST SP 800-22 §4.2.1)
PROPORTION_PASS_THRESHOLD    = 0.96
PROPORTION_BORDERLINE_LOWER  = 0.94
KS_UNIFORMITY_THRESHOLD      = 0.0001


def _bits_from_bytes(data: bytes) -> list:
    bits = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> i) & 1)
    return bits


def _run_tests_on_bits(bits: list) -> list:
    """Run every NIST test module on a bit list. Each result is a TestResult dict."""
    return [mod.run(bits) for mod in ALL_TESTS]


def _classify_proportion(prop: float) -> str:
    if prop >= PROPORTION_PASS_THRESHOLD:
        return LABEL_PASS
    if prop >= PROPORTION_BORDERLINE_LOWER:
        return LABEL_BORDERLINE
    return LABEL_FAIL


def run_nist_multi_sequence(filepath: str, n_sequences: int = 100) -> dict:
    """Level-2 multi-sequence analysis (proportion + KS uniformity)."""
    with open(filepath, "rb") as f:
        raw = f.read()

    bits = _bits_from_bytes(raw)
    size_bits = len(bits)
    size_mb = round(size_bits / 8 / 1_048_576, 3)

    warnings = []
    if size_bits < MIN_BITS:
        warnings.append(
            f"Sample has {size_bits:,} bits — NIST minimum is {MIN_BITS:,} bits."
        )
        sufficient = False
    else:
        sufficient = True

    sample_info = {
        "filename": os.path.basename(filepath),
        "size_bits": size_bits,
        "size_mb": size_mb,
        "warnings": warnings,
        "sufficient": sufficient,
    }

    if not sufficient:
        tests = [
            {
                "test_id": mod.TEST_ID, "name": mod.TEST_NAME,
                "statistic": None, "p_value": None,
                "status": LABEL_INDICATIVE_ONLY,
                "detail": "Sample below NIST minimum.",
            }
            for mod in ALL_TESTS
        ]
        return {"suite": "NIST SP 800-22", "sample_info": sample_info, "tests": tests}

    min_chunk_bits = MIN_BITS
    max_n = size_bits // min_chunk_bits
    actual_n = max(1, min(n_sequences, max_n))
    chunk_size = size_bits // actual_n

    all_p_values: dict = {mod.TEST_NAME: [] for mod in ALL_TESTS}
    all_results: list = []

    for i in range(actual_n):
        chunk = bits[i * chunk_size: (i + 1) * chunk_size]
        seq_results = _run_tests_on_bits(chunk)
        all_results.append(seq_results)
        for tr in seq_results:
            p = tr.get("p_value")
            if p is not None and tr["status"] not in (
                LABEL_INCONCLUSIVE, LABEL_INDICATIVE_ONLY, LABEL_NOT_RUN
            ):
                all_p_values[tr["name"]].append(p)

    primary_tests = all_results[0]

    level2_per_test = []
    for mod in ALL_TESTS:
        test_name = mod.TEST_NAME
        p_vals = all_p_values[test_name]
        n_with_result = len(p_vals)
        n_passing = sum(1 for p in p_vals if p >= BORDERLINE_LOWER)

        if n_with_result == 0:
            level2_per_test.append({
                "test_id": mod.TEST_ID,
                "name": test_name,
                "n_sequences": 0,
                "n_passing": 0,
                "proportion_passing": None,
                "proportion_result": LABEL_INDICATIVE_ONLY,
                "ks_p_value": None,
                "uniformity_result": LABEL_INDICATIVE_ONLY,
            })
            continue

        proportion = n_passing / n_with_result
        prop_result = _classify_proportion(proportion)

        ks_p = None
        uniformity_result = LABEL_INDICATIVE_ONLY
        if n_with_result >= 10:
            try:
                _, ks_p = scipy_stats.kstest(p_vals, "uniform")
                ks_p = float(ks_p)
                uniformity_result = (
                    LABEL_FAIL if ks_p < KS_UNIFORMITY_THRESHOLD else LABEL_PASS
                )
            except Exception:
                ks_p = None
                uniformity_result = LABEL_INCONCLUSIVE

        level2_per_test.append({
            "test_id": mod.TEST_ID,
            "name": test_name,
            "n_sequences": n_with_result,
            "n_passing": n_passing,
            "proportion_passing": round(proportion, 4),
            "proportion_result": prop_result,
            "ks_p_value": round(ks_p, 6) if ks_p is not None else None,
            "uniformity_result": uniformity_result,
        })

    level2 = {
        "n_sequences": actual_n,
        "per_test": level2_per_test,
        "tests_proportion_pass": sum(
            1 for t in level2_per_test if t["proportion_result"] == LABEL_PASS
        ),
        "tests_uniformity_pass": sum(
            1 for t in level2_per_test if t["uniformity_result"] == LABEL_PASS
        ),
    }

    return {
        "suite": "NIST SP 800-22",
        "sample_info": sample_info,
        "tests": primary_tests,
        "level2": level2,
    }


def run_nist_tests(filepath: str) -> dict:
    """Run NIST SP 800-22 on the file. Falls into Level-2 mode for large inputs."""
    with open(filepath, "rb") as f:
        raw = f.read()

    bits = _bits_from_bytes(raw)
    size_bits = len(bits)
    size_mb = round(size_bits / 8 / 1_048_576, 3)

    warnings = []
    if size_bits < MIN_BITS:
        warnings.append(
            f"Sample has {size_bits:,} bits — NIST minimum is {MIN_BITS:,} bits."
        )
        sufficient = False
    else:
        sufficient = True
        if size_bits < RECOMMENDED_BITS:
            warnings.append(
                f"Sample has {size_bits:,} bits — recommended minimum is "
                f"{RECOMMENDED_BITS:,} bits (12.5 MB) for multi-sequence Level-2 analysis."
            )

    sample_info = {
        "filename": os.path.basename(filepath),
        "size_bits": size_bits,
        "size_mb": size_mb,
        "warnings": warnings,
        "sufficient": sufficient,
    }

    if not sufficient:
        tests = [
            {
                "test_id": mod.TEST_ID, "name": mod.TEST_NAME,
                "statistic": None, "p_value": None,
                "status": LABEL_INDICATIVE_ONLY,
                "detail": "Sample below NIST minimum.",
            }
            for mod in ALL_TESTS
        ]
        return {"suite": "NIST SP 800-22", "sample_info": sample_info, "tests": tests}

    if size_bits >= MULTI_SEQUENCE_MIN_BITS:
        return run_nist_multi_sequence(filepath)

    tests = _run_tests_on_bits(bits)
    return {"suite": "NIST SP 800-22", "sample_info": sample_info, "tests": tests}

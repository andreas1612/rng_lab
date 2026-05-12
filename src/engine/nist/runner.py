import io
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

from scipy import stats as scipy_stats

NIST_DIR = Path(__file__).parent / "sp800_22_tests"

NIST_TESTS = [
    ("Frequency (Monobit)",                  "monobit_test"),
    ("Block Frequency",                       "frequency_within_block_test"),
    ("Runs",                                  "runs_test"),
    ("Longest Run of Ones",                   "longest_run_ones_in_a_block_test"),
    ("Binary Matrix Rank",                    "binary_matrix_rank_test"),
    ("Discrete Fourier Transform (Spectral)", "dft_test"),
    ("Non-overlapping Template Matching",     "non_overlapping_template_matching_test"),
    ("Overlapping Template Matching",         "overlapping_template_matching_test"),
    ("Maurer's Universal Statistical",        "maurers_universal_test"),
    ("Linear Complexity",                     "linear_complexity_test"),
    ("Serial",                                "serial_test"),
    ("Approximate Entropy",                   "approximate_entropy_test"),
    ("Cumulative Sums (Cusum)",               "cumulative_sums_test"),
    ("Random Excursions",                     "random_excursion_test"),
    ("Random Excursions Variant",             "random_excursion_variant_test"),
]

MIN_BITS               = 1_000_000    # hard minimum — insufficient_data below this
RECOMMENDED_BITS       = 100_000_000  # 100M bits = 12.5 MB
MULTI_SEQUENCE_MIN_BITS = 100_000_000 # threshold above which multi-sequence mode activates
P_FLOOR   = 0.01
P_WARNING = 0.05

# Level-2 proportion thresholds (NIST SP 800-22 §4.2.1)
PROPORTION_PASS_THRESHOLD    = 0.96  # ≥96% sequences must pass per test
PROPORTION_WARNING_THRESHOLD = 0.94  # 94–96% → warning
KS_UNIFORMITY_THRESHOLD      = 0.0001  # KS p-value < this → non-uniform → fail


def _bits_from_bytes(data: bytes) -> list:
    bits = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> i) & 1)
    return bits


def _classify(p_value) -> str:
    if p_value is None:
        return "error"
    if p_value < P_FLOOR:
        return "fail"
    if p_value < P_WARNING:
        return "warning"
    return "pass"


def _ensure_nist_on_path():
    if not NIST_DIR.exists():
        raise FileNotFoundError(
            f"NIST library not found at {NIST_DIR}. "
            "Clone it first:\n"
            "  git clone https://github.com/dj-on-github/sp800_22_tests.git "
            "src/engine/nist/sp800_22_tests"
        )
    nist_str = str(NIST_DIR)
    if nist_str not in sys.path:
        sys.path.insert(0, nist_str)


def _run_tests_on_bits(bits: list) -> list:
    """Run all 15 NIST tests on a pre-loaded bit list. Returns per-test result dicts."""
    results = []
    for display_name, module_name in NIST_TESTS:
        try:
            mod = __import__("sp800_22_" + module_name)
            func = getattr(mod, module_name)
            with redirect_stdout(io.StringIO()):
                success, p, plist = func(bits)
            if plist is not None:
                p = min(plist)
            results.append({
                "name": display_name,
                "p_value": p,
                "status": _classify(p),
                "threshold_used": P_FLOOR,
            })
        except Exception as exc:
            results.append({
                "name": display_name,
                "p_value": None,
                "status": "error",
                "threshold_used": P_FLOOR,
                "error_detail": str(exc),
            })
    return results


def run_nist_multi_sequence(filepath: str, n_sequences: int = 100) -> dict:
    """
    Run NIST SP 800-22 with multi-sequence Level-2 analysis.

    Splits the input file into N equal chunks (≥1 Mbit each), runs all 15 tests
    on every chunk, then performs:
      - Proportion check: fraction of sequences where p ≥ 0.01 (NIST §4.2.1)
      - Uniformity check: KS test of p-value distribution vs Uniform(0,1)

    Returns the same schema as run_nist_tests() plus a 'level2' key.
    """
    _ensure_nist_on_path()

    with open(filepath, "rb") as f:
        raw = f.read()

    bits = _bits_from_bytes(raw)
    size_bits = len(bits)
    size_mb = round(size_bits / 8 / 1_048_576, 3)

    warnings = []
    if size_bits < MIN_BITS:
        warnings.append(
            f"Sample has {size_bits:,} bits — NIST minimum is {MIN_BITS:,} bits. "
            "Tests cannot produce reliable results."
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
            {"name": name, "p_value": None, "status": "insufficient_data", "threshold_used": P_FLOOR}
            for name, _ in NIST_TESTS
        ]
        return {"suite": "NIST SP 800-22", "sample_info": sample_info, "tests": tests}

    # Determine actual number of sequences (each chunk ≥ 1 Mbit)
    min_chunk_bits = MIN_BITS
    max_n = size_bits // min_chunk_bits
    actual_n = max(1, min(n_sequences, max_n))
    chunk_size = size_bits // actual_n

    # Collect p-values per test across all sequences
    all_p_values: dict[str, list] = {name: [] for name, _ in NIST_TESTS}
    all_results: list[list] = []

    for i in range(actual_n):
        chunk = bits[i * chunk_size: (i + 1) * chunk_size]
        seq_results = _run_tests_on_bits(chunk)
        all_results.append(seq_results)
        for test_result in seq_results:
            name = test_result["name"]
            p = test_result.get("p_value")
            if p is not None and test_result["status"] not in ("error", "insufficient_data"):
                all_p_values[name].append(p)

    # Primary tests = first sequence (backward compatible with scoring.py)
    primary_tests = all_results[0]

    # Level-2 analysis per test
    level2_per_test = []
    for test_name, _ in NIST_TESTS:
        p_vals = all_p_values[test_name]
        n_with_result = len(p_vals)
        n_passing = sum(1 for p in p_vals if p >= P_FLOOR)

        if n_with_result == 0:
            level2_per_test.append({
                "name": test_name,
                "n_sequences": 0,
                "n_passing": 0,
                "proportion_passing": None,
                "proportion_result": "insufficient_data",
                "ks_p_value": None,
                "uniformity_result": "insufficient_data",
            })
            continue

        proportion = n_passing / n_with_result
        if proportion >= PROPORTION_PASS_THRESHOLD:
            prop_result = "pass"
        elif proportion >= PROPORTION_WARNING_THRESHOLD:
            prop_result = "warning"
        else:
            prop_result = "fail"

        ks_p = None
        uniformity_result = "insufficient_data"
        if n_with_result >= 10:
            try:
                _, ks_p = scipy_stats.kstest(p_vals, "uniform")
                ks_p = float(ks_p)
                uniformity_result = "fail" if ks_p < KS_UNIFORMITY_THRESHOLD else "pass"
            except Exception:
                ks_p = None
                uniformity_result = "error"

        level2_per_test.append({
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
            1 for t in level2_per_test if t["proportion_result"] == "pass"
        ),
        "tests_uniformity_pass": sum(
            1 for t in level2_per_test if t["uniformity_result"] == "pass"
        ),
    }

    return {
        "suite": "NIST SP 800-22",
        "sample_info": sample_info,
        "tests": primary_tests,
        "level2": level2,
    }


def run_nist_tests(filepath: str) -> dict:
    """
    Run NIST SP 800-22 tests on a binary file.

    For files ≥ MULTI_SEQUENCE_MIN_BITS (100M bits / 12.5 MB), activates
    multi-sequence Level-2 analysis (proportion + uniformity checks across
    100 independent sequences of ≥1 Mbit each).

    Returns a dict with 'suite', 'sample_info', 'tests', and optionally 'level2'.
    Schema is stable so scoring.py is not affected by the presence of 'level2'.
    """
    _ensure_nist_on_path()

    with open(filepath, "rb") as f:
        raw = f.read()

    bits = _bits_from_bytes(raw)
    size_bits = len(bits)
    size_mb = round(size_bits / 8 / 1_048_576, 3)

    warnings = []
    if size_bits < MIN_BITS:
        warnings.append(
            f"Sample has {size_bits:,} bits — NIST minimum is {MIN_BITS:,} bits. "
            "Tests cannot produce reliable results."
        )
        sufficient = False
    else:
        sufficient = True
        if size_bits < RECOMMENDED_BITS:
            warnings.append(
                f"Sample has {size_bits:,} bits — recommended minimum is "
                f"{RECOMMENDED_BITS:,} bits (12.5 MB) for multi-sequence Level-2 analysis. "
                "Results are based on a single sequence and may have lower confidence."
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
            {"name": name, "p_value": None, "status": "insufficient_data", "threshold_used": P_FLOOR}
            for name, _ in NIST_TESTS
        ]
        return {"suite": "NIST SP 800-22", "sample_info": sample_info, "tests": tests}

    # Large file: use multi-sequence Level-2 analysis
    if size_bits >= MULTI_SEQUENCE_MIN_BITS:
        return run_nist_multi_sequence(filepath)

    # Standard single-sequence run
    tests = _run_tests_on_bits(bits)
    return {"suite": "NIST SP 800-22", "sample_info": sample_info, "tests": tests}

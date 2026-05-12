"""Shared helper for invoking upstream sp800_22 test functions."""
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

from core.labels import classify_p_value, LABEL_INDICATIVE_ONLY, LABEL_INCONCLUSIVE

NIST_DIR = Path(__file__).resolve().parent.parent / "sp800_22_tests"


def _ensure_path():
    if not NIST_DIR.exists():
        raise FileNotFoundError(
            f"NIST library not found at {NIST_DIR}. Clone sp800_22_tests there."
        )
    s = str(NIST_DIR)
    if s not in sys.path:
        sys.path.insert(0, s)


def run_upstream(module_suffix: str, bits, test_id: str, test_name: str,
                 min_bits: int):
    """Invoke an upstream sp800_22 test function and produce a TestResult dict.

    module_suffix is the part after 'sp800_22_', e.g. 'monobit_test'.
    """
    if len(bits) < min_bits:
        return {
            "test_id": test_id,
            "name": test_name,
            "statistic": None,
            "p_value": None,
            "status": LABEL_INDICATIVE_ONLY,
            "detail": (
                f"Sample has {len(bits):,} bits; minimum for this test is {min_bits:,}. "
                "Result not produced."
            ),
        }
    _ensure_path()
    try:
        mod = __import__("sp800_22_" + module_suffix)
        func = getattr(mod, module_suffix)
        with redirect_stdout(io.StringIO()):
            success, p, plist = func(bits)
        if plist is not None and len(plist) > 0:
            try:
                p = min(x for x in plist if x is not None)
            except ValueError:
                pass
        status = classify_p_value(p)
        return {
            "test_id": test_id,
            "name": test_name,
            "statistic": None,
            "p_value": float(p) if p is not None else None,
            "status": status,
            "detail": f"p={p:.6f}" if p is not None else "No p-value produced.",
        }
    except Exception as exc:
        return {
            "test_id": test_id,
            "name": test_name,
            "statistic": None,
            "p_value": None,
            "status": LABEL_INCONCLUSIVE,
            "detail": f"Test raised an exception: {exc}",
        }

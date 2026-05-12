"""Shared helper for invoking upstream sp800_22 test functions."""
import io
import sys
import threading
from contextlib import contextmanager
from pathlib import Path

from core.labels import classify_p_value, LABEL_INDICATIVE_ONLY, LABEL_INCONCLUSIVE

NIST_DIR = Path(__file__).resolve().parent.parent / "sp800_22_tests"

# ---------------------------------------------------------------------------
# Thread-safe stdout suppressor
#
# contextlib.redirect_stdout modifies sys.stdout globally, so concurrent
# threads corrupt each other's saved reference and sys.stdout ends up as a
# StringIO after the workers finish. Fix: install a single proxy object as
# sys.stdout; each thread routes writes to its own thread-local buffer.
# ---------------------------------------------------------------------------
_tls = threading.local()
_install_lock = threading.Lock()
_real_stdout = None


class _TLSStdout:
    """Proxy that routes writes to the calling thread's suppress buffer."""
    def write(self, s):
        buf = getattr(_tls, "buf", None)
        if buf is not None:
            buf.write(s)
        elif _real_stdout is not None:
            _real_stdout.write(s)
    def flush(self):
        if getattr(_tls, "buf", None) is None and _real_stdout is not None:
            _real_stdout.flush()
    def fileno(self):
        return _real_stdout.fileno() if _real_stdout is not None else 1


_proxy = _TLSStdout()


def _install_proxy():
    global _real_stdout
    with _install_lock:
        if not isinstance(sys.stdout, _TLSStdout):
            _real_stdout = sys.stdout
            sys.stdout = _proxy


@contextmanager
def _suppress_stdout():
    """Context manager: silently discard stdout in the current thread only."""
    _install_proxy()
    _tls.buf = io.StringIO()
    try:
        yield _tls.buf
    finally:
        _tls.buf = None


# ---------------------------------------------------------------------------

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
        with _suppress_stdout():
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

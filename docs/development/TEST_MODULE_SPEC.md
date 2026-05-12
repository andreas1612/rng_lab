# Test Module Specification

Every test in MiniLab — NIST or supplementary — is a Python module exporting a
standard interface. This spec is the contract.

## Required exports

| Name              | Type           | Purpose |
|-------------------|----------------|---------|
| `TEST_ID`         | `str`          | Stable identifier. NIST tests use `"NIST-01"` through `"NIST-15"`. Supplementary tests use `"SUPP-01"` through `"SUPP-08"`. |
| `TEST_NAME`       | `str`          | Human-readable name. Shown in the report tables. |
| `MIN_BITS`        | `int`          | Smallest input below which the test cannot run at all. Below this, the test must return `INDICATIVE_ONLY`. |
| `RECOMMENDED_BITS`| `int`          | Sample size for confident results. Informational only — the test still runs above `MIN_BITS`. |
| `run(input)`      | `callable`     | The test function. NIST tests take `bits: list[int]`; supplementary tests take `data: bytes`. Returns a TestResult dict. |

## TestResult dict schema

```python
{
    "test_id":   str,                      # mirrors TEST_ID
    "name":      str,                      # mirrors TEST_NAME
    "statistic": float | None,             # main test statistic; None if not applicable
    "p_value":   float | None,             # None if the test does not produce one
    "status":    str,                      # one of the six labels
    "detail":    str,                      # short human-readable explanation
}
```

### Field rules

- `test_id` and `name` must match the module-level constants exactly so the
  runner and the report tables stay aligned.
- `statistic` may be `None` for tests that do not have a single scalar
  statistic (e.g. multi-component tests where the "statistic" is a structure).
- `p_value` must be `None` for tests that classify without a p-value
  (Autocorrelation, Bit Independence). For all other tests, populate the
  numeric p-value used for classification.
- `status` must be one of:
  - `PASS`
  - `BORDERLINE`
  - `FAIL`
  - `NOT_RUN`
  - `INDICATIVE_ONLY`
  - `INCONCLUSIVE`
- `detail` is the operator-visible explanation. Keep it short. Mention the
  numbers (p, statistic, sample size) the operator needs to act.

## Status assignment rules

In order of precedence:

1. **`INDICATIVE_ONLY`** — the input is below `MIN_BITS` for this test. Do not
   compute the p-value; just return INDICATIVE_ONLY with a detail string
   stating the shortfall.
2. **`INCONCLUSIVE`** — the test ran but raised an exception, returned no
   p-value when one was expected, or hit a degenerate case (e.g. zero
   variance). Capture the cause in `detail`.
3. **`NOT_RUN`** — the runner deliberately chose not to invoke this test (for
   example a future skip-list). v0.1 does not produce NOT_RUN from any test;
   the label exists for completeness.
4. **`PASS` / `BORDERLINE` / `FAIL`** — for p-value tests, use
   `core.labels.classify_p_value(p)`. For non-p-value tests (Autocorrelation,
   Bit Independence) the test owns its own decision and documents it in
   the module docstring and in `SUPPLEMENTARY_TESTS.md`.

## Error handling

A test must never raise out to the runner. Wrap the computation in
`try / except Exception as exc:` and return an `INCONCLUSIVE` result with
`detail=str(exc)`. The runner has a backstop, but tests are expected to
self-contain their failure modes.

## Worked example

```python
"""NIST-XX: Example Test."""
import numpy as np
from scipy import stats as scipy_stats

from core.labels import classify_p_value, LABEL_INDICATIVE_ONLY, LABEL_INCONCLUSIVE

TEST_ID = "NIST-XX"
TEST_NAME = "Example Test"
MIN_BITS = 1000
RECOMMENDED_BITS = 1_000_000


def run(bits):
    if len(bits) < MIN_BITS:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INDICATIVE_ONLY,
            "detail": f"Need at least {MIN_BITS} bits, got {len(bits)}.",
        }
    try:
        arr = np.asarray(bits, dtype=np.int8)
        stat, p = scipy_stats.normaltest(arr)
        stat, p = float(stat), float(p)
    except Exception as exc:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INCONCLUSIVE,
            "detail": f"Test raised an exception: {exc}",
        }
    return {
        "test_id": TEST_ID, "name": TEST_NAME,
        "statistic": round(stat, 4),
        "p_value": round(p, 6),
        "status": classify_p_value(p),
        "detail": f"normality stat={stat:.4f}, p={p:.6f}.",
    }
```

That's the entire contract. The module then gets added to `ALL_TESTS` in the
package `__init__.py` and is discovered automatically.

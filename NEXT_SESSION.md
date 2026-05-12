# Next Session

Last update: 2026-05-12 — end of Sprint 5.

## Current state

- Tool name: **MiniLab RNG Engine v0.1.0**
- Methodology: `MiniLab-RNG-Methodology-v0.1`
- API version: `0.5.0`
- Test architecture: one file per test, dispatched by `nist/runner.py` and
  `supplementary/__init__.py`. 15 NIST + 8 supplementary = 23 test modules.
- Single source of truth for labels and thresholds: `src/engine/core/labels.py`.
- AUP record + Report ID + SHA-256 + evidence JSON are all produced on every
  run. The PDF carries a DRAFT watermark when the AUP record is incomplete.
- No `"WARNING"` status string remains anywhere in `src/engine/`.

## What works end-to-end

Smoke verified on `good.bin` (1.6 Mbit synthetic):

- `core.labels.classify_p_value` returns PASS / BORDERLINE / FAIL /
  INCONCLUSIVE on the right inputs.
- All 15 NIST tests dispatch and produce p-values.
- All 8 supplementary tests run, including the autocorrelation 1-lag tolerance
  fix, the permutations tie-filter, and the 2D grid chi-square form.
- Jurisdiction scoring runs against MGA / UKGC / DGA / CGA.
- PDF generation succeeds in both AUP-complete and DRAFT modes.
- `<report_id>.json` is written to the temp dir; path returned via
  `X-Evidence-JSON-Path` header.

## Open items / next sprint candidates

1. **UI integration** — the React UI in `src/ui/` still calls the old
   endpoint shape and old status strings. The UI needs:
   - Five new form fields for the AUP record on submit.
   - Updated status badge colours to match the 6-label scheme.
   - Show the Report ID, SHA-256, tool/methodology version on the result page.
2. **Persistence of evidence JSON** — currently saved to `tempfile.gettempdir()`
   which is volatile. Decide on a storage location (per-tenant folder?) and
   wire the path into the response body rather than only into a header.
3. **Backward-compatibility shim for legacy clients** — the response payload
   field `tests_warning` is still emitted as an alias of `tests_borderline` in
   `scoring.py`. Schedule removal once UI catches up.
4. **TestU01 / Diehard / PractRand** — still deferred. Track in the algorithms
   doc as future supplementary tests if any are added.
5. **Real audit comparison page in the UI** — surface the
   `REAL_AUDIT_COVERAGE.md` matrix to the operator on the result page.

## File map (Sprint 5 deltas)

New:

- `src/engine/core/__init__.py`
- `src/engine/core/labels.py`
- `src/engine/core/models.py`
- `src/engine/core/report_id.py`
- `src/engine/nist/tests/__init__.py`
- `src/engine/nist/tests/_wrap.py`
- `src/engine/nist/tests/t01_frequency.py` ... `t15_random_excursions_variant.py`
- `src/engine/supplementary/tests/__init__.py`
- `src/engine/supplementary/tests/s01_chi_square_byte.py` ... `s08_bit_independence.py`
- `src/engine/report/json_output.py`
- `docs/methodology/METHODOLOGY_v0.1.md`
- `docs/methodology/THRESHOLD_SCHEME.md`
- `docs/algorithms/NIST_SP800_22.md`
- `docs/algorithms/SUPPLEMENTARY_TESTS.md`
- `docs/audit_comparison/REAL_AUDIT_COVERAGE.md`
- `docs/development/ARCHITECTURE.md`
- `docs/development/TEST_MODULE_SPEC.md`

Modified:

- `src/engine/main.py` (AUP form fields, report_id, sha256, evidence JSON, headers)
- `src/engine/scoring.py` (label constants, threshold constants)
- `src/engine/nist/runner.py` (dispatches test modules; label-aware Level-2)
- `src/engine/supplementary/__init__.py` (iterates new ALL_TESTS)
- `src/engine/report/generator.py` (6-label palette, legend, scope, metadata, DRAFT)
- `src/engine/report/gap_analysis.py` (label constants)
- `STATUS.md` (Sprint 5 section)

Deleted:

- `src/engine/supplementary/tests.py`

## How to resume

Read `docs/methodology/METHODOLOGY_v0.1.md` for the current contract, then
`docs/development/ARCHITECTURE.md` for the wiring. To add a test, follow
`docs/development/TEST_MODULE_SPEC.md`.

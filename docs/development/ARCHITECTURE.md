# Architecture

## Component diagram

```
                            ┌──────────────────────────┐
                            │       FastAPI app        │
                            │      (engine/main)       │
                            └────────────┬─────────────┘
                                         │
        ┌────────────────────┬───────────┴──────────┬────────────────────┐
        │                    │                      │                    │
        ▼                    ▼                      ▼                    ▼
 ┌─────────────┐     ┌───────────────┐     ┌────────────────┐     ┌────────────┐
 │ nist.runner │     │ supplementary │     │   scoring      │     │   report   │
 │             │     │               │     │                │     │ generator  │
 └──────┬──────┘     └───────┬───────┘     └───────┬────────┘     │  json_out  │
        │                    │                     │              │ gap_analysis│
        ▼                    ▼                     ▼              └─────┬──────┘
 ┌─────────────┐     ┌───────────────┐     ┌────────────────┐           │
 │ nist/tests/ │     │ supplementary │     │ jurisdictions/ │           │
 │ (15 files)  │     │   /tests/     │     │   *.json       │           │
 │             │     │   (8 files)   │     │                │           │
 └──────┬──────┘     └───────┬───────┘     └────────────────┘           │
        │                    │                                          │
        ▼                    ▼                                          │
 ┌──────────────────┐  ┌──────────────────┐                            │
 │ sp800_22_tests/  │  │ numpy / scipy    │                            │
 │ (upstream)       │  │                  │                            │
 └──────────────────┘  └──────────────────┘                            │
                                                                       ▼
                                                              ┌──────────────────┐
                                                              │  PDF + JSON      │
                                                              │  artefacts       │
                                                              └──────────────────┘

   All modules pull labels and thresholds from a single source:
   ┌──────────────────────────────────────────────┐
   │ core/labels.py   core/models.py   report_id  │
   └──────────────────────────────────────────────┘
```

## Data flow

1. Client POSTs `/analyse` or `/report` with the binary input and the AUP form
   fields.
2. `main._run_analysis` reads the bytes, computes the SHA-256, allocates a
   Report ID, and writes the bytes to a temp file.
3. `nist.runner.run_nist_tests` loads the file, builds the bit list, and
   dispatches each test module under `nist/tests/`. Test modules wrap the
   upstream sp800_22 functions and return a TestResult dict each.
4. `supplementary.run_supplementary_tests` iterates the modules under
   `supplementary/tests/` and produces a parallel result list.
5. `scoring.score_against_jurisdictions` aggregates the NIST results against
   every jurisdiction config in `src/jurisdictions/`.
6. `report.gap_analysis.generate_gap_analysis` produces an HTML-fragment
   narrative.
7. `report.generator.generate_pdf` lays out the PDF using ReportLab. The
   DRAFT watermark is drawn by the page callback when the AUP record is
   incomplete.
8. `report.json_output.build_evidence_json` + `save_evidence_json` write
   `<report_id>.json` next to the PDF.
9. Response is the PDF stream with headers `X-Report-Id`,
   `X-Input-SHA256`, `X-Tool-Version`, `X-Methodology-Version`,
   `X-Evidence-JSON-Path`.

## Module dependency map

```
main.py
  ├── core.labels                (TOOL_VERSION, METHODOLOGY_VERSION)
  ├── core.models                (AUPRecord)
  ├── core.report_id             (generate_report_id)
  ├── nist.runner
  │     ├── core.labels
  │     └── nist.tests.* (15)
  │           └── nist.tests._wrap
  │                 └── core.labels
  │                       (and dynamically imports sp800_22_*)
  ├── supplementary
  │     ├── core.labels
  │     └── supplementary.tests.* (8)
  │           └── core.labels
  ├── scoring
  │     └── core.labels
  ├── report.generator
  │     ├── core.labels
  │     └── core.models
  ├── report.gap_analysis
  │     └── core.labels
  └── report.json_output
        └── core.labels
```

There is one rule: **every classification or threshold goes through `core/labels.py`**.
No module hard-codes p-values or label strings.

## How to add a new test

1. Pick the next free `TEST_ID` (e.g. `NIST-16` or `SUPP-09`) and the next
   filename slot in the corresponding `tests/` folder.
2. Create the file with the required exports (`TEST_ID`, `TEST_NAME`,
   `MIN_BITS`, `RECOMMENDED_BITS`, and a `run()` function returning a
   TestResult dict). Use `core.labels.classify_p_value` to assign the status.
3. Add the module to the `ALL_TESTS` list in the package `__init__.py`.
4. Update the relevant doc:
   - `docs/algorithms/NIST_SP800_22.md` for a NIST test, or
   - `docs/algorithms/SUPPLEMENTARY_TESTS.md` for a supplementary test.
5. Update `docs/methodology/METHODOLOGY_v0.1.md` test table.

No changes are needed in `runner.py`, the scoring code, or the report code —
they iterate `ALL_TESTS` dynamically.

## How to add a new jurisdiction

1. Add `src/jurisdictions/<short_name>.json` with at minimum:
   - `id`, `name`, `short_name`
   - `min_rtp_percent` or null
   - `p_value_floor`, `p_value_warning_floor` (will fall back to the global
     thresholds if omitted)
   - `notes`
2. Mention the jurisdiction in `docs/methodology/METHODOLOGY_v0.1.md` if it
   introduces new constraints (RTP floor, lab list, etc.).
3. No code changes are needed — `scoring.py` discovers files via glob.

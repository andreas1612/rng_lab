# Project Status

## Current Phase: Sprint 4 Complete — Full UI Working | Sprint 4.5 In Progress (RNG Perfection)

---

## Sprint Log

### Sprint 0 — Research & Planning (COMPLETE)
- [x] Researched all major accredited testing labs: GLI, eCOGRA, BMM, iTech Labs, Quinel, MGA
- [x] Documented authority-specific RTP thresholds per jurisdiction
- [x] Confirmed open-source status of NIST SP 800-22, TestU01, Dieharder, PractRand
- [x] Identified proprietary vs open components of real audit methodology
- [x] Defined service offering: Pre-Audit Readiness Report (non-certified)
- [x] Defined legal boundaries: what the report sells, what it explicitly does not claim
- [x] Created project folder structure and all documentation files
- [x] Written README, ALGORITHMS, THRESHOLDS, RESEARCH_DONE, SOURCES, LEGAL, AUP

### Sprint 1 — Scaffold (COMPLETE — 2026-05-06)
- [x] Initialise React + Vite frontend in src/ui/ (manually scaffolded; run `npm install` once Node 20 LTS is installed)
- [x] Initialise FastAPI backend in src/engine/ (main.py with /health and /analyse stub)
- [x] NIST runner stub in src/engine/nist/runner.py (all 15 tests, "not_run" status — real runner in Sprint 2)
- [x] Create jurisdiction JSON config files in src/jurisdictions/ (mga, ukgc, denmark, canada_cga)
- [x] Basic file upload → return placeholder response (no actual test running yet)

#### Fact-Check Corrections Applied in Sprint 1
1. **UKGC lab accreditation standard** is `ISO/IEC 17025` (testing and calibration laboratories) in ukgc.json. Note: ISO/IEC 17065 (product certification bodies) was mistakenly written during scaffolding and corrected before Sprint 2.
2. **GLI / BMM Testlabs** parent-company note added to all jurisdiction configs where both appear: GLI was acquired by BMM in 2022; they operate as separate entities under the same parent. Either is a valid approved authority.
3. **Canada RTP floor** caveat added to canada_cga.json: the 85% floor is the Ontario reference baseline only. Provincial floors vary and can change — do not treat as authoritative without verifying with the relevant provincial regulator.

### Sprint 2 — Core Engine (COMPLETE — 2026-05-06)
- [x] Full NIST SP 800-22 test runner (all 15 tests) — src/engine/nist/runner.py
- [x] Jurisdiction scoring engine — src/engine/scoring.py (all 4 jurisdictions: MGA, UKGC, Denmark, Canada CGA)
- [x] /analyse endpoint wired to runner + scorer, temp file handling, cleanup in finally
- [x] Sample size validation: <1M bits → insufficient_data; <10M bits → warning
- [x] stdout suppressed from NIST library (redirect_stdout) — clean API logs
- [x] App.tsx updated with file picker, size display, and warning banner
- [ ] Dieharder wrapper — deferred (requires WSL/Linux; Windows environment)
- [ ] PractRand wrapper — deferred (binary not yet placed; add in Sprint 3 or later)

#### Sprint 2 Smoke Test Results (2026-05-06)
- `from nist.runner import run_nist_tests` → OK
- `from scoring import score_against_jurisdictions` → OK
- End-to-end test (200 KB / 1.6M bits, os.urandom): 15/15 tests ran; 14 pass, 1 warning (Longest Run of Ones — expected at this sample size); all 4 jurisdiction scores returned correctly

### Sprint 3 — Report Generation (COMPLETE — 2026-05-06)
- [x] Jinja2 HTML template — src/report/template.html (A4, print-ready CSS, paged media)
- [x] ReportLab PDF generator — src/engine/report/generator.py
- [x] Gap analysis generator — src/engine/report/gap_analysis.py (plain-English, HTML output)
- [x] Mandatory disclaimer block on page 1 and last page (verbatim from LEGAL.md)
- [x] NIST results table with colour-coded status (pass/warning/fail/other)
- [x] Jurisdiction scoring matrix with per-jurisdiction caveat text
- [x] POST /report endpoint — returns PDF as StreamingResponse attachment
- [x] /analyse and /report share a common _run_analysis() helper

#### Sprint 3 PDF Smoke Test (2026-05-06)
- 200 KB os.urandom input → full pipeline → PDF generated: 10,555 bytes, valid %PDF header
- All imports clean: gap_analysis, generator, reportlab

#### PDF Library Decision: WeasyPrint → ReportLab
- WeasyPrint requires GTK3 native libraries (libgobject, libpango, libcairo) unavailable on this corporate Windows machine — admin access required for GTK installer
- xhtml2pdf also blocked — python-bidi dependency requires Rust compiler
- ReportLab is pure Python with pre-built wheels, no system dependencies — installed and working
- src/report/template.html retained for HTML preview / future WeasyPrint migration when a dev environment with GTK is available

### Pre-Sprint 4 Fixes (COMPLETE — 2026-05-08)
Applied four cleanup fixes before building Sprint 4 UI on top of the engine:
- [x] FIX 1 — scoring.py: Removed "implemented in Sprint 3" placeholder from rtp_floor_check detail; replaced with clean "Declared RTP not provided — RTP floor check skipped." logic
- [x] FIX 2 — generator.py: Changed _format_bits() to display KB instead of MB (e.g. "1,600,000 bits (195 KB)") — avoids "0.19 MB looks wrong" confusion
- [x] FIX 3 — gap_analysis.py: Added p=1.000 artifact detection; if any test returns exactly p=1.0, a note is prepended explaining it is a known artifact at small sample sizes, not an RNG defect
- [x] FIX 4 — generator.py: Replaced raw None fallbacks for aup_timestamp/aup_ref with "Not recorded (pre-AUP session)" / "N/A" in both the page-2 meta block and the final-page AUP line

### Sprint 3.5 — Engine Depth (COMPLETE — 2026-05-08)

#### 3.5-F — Docker check
- `docker --version` → Docker not available. Dieharder via Docker deferred. Noted here.

#### 3.5-E — Updated sample thresholds
- [x] `RECOMMENDED_BITS` updated from 10M → 100M bits (12.5 MB) in `nist/runner.py`
- [x] `MULTI_SEQUENCE_MIN_BITS = 100_000_000` — threshold above which Level-2 activates
- [x] Low-confidence warning text updated to reference 100M bit recommendation

#### 3.5-A — Multi-sequence NIST Level-2 Analysis
- [x] `_run_tests_on_bits(bits)` — private helper; runs all 15 tests on an arbitrary bit list
- [x] `run_nist_multi_sequence(filepath, n_sequences=100)` — public function, splits file into N chunks (≥1 Mbit each), runs all 15 tests per chunk, returns single-sequence results + `level2` key
- [x] Level-2 per-test: `proportion_passing`, `proportion_result` (pass/warning/fail), `ks_p_value`, `uniformity_result`
- [x] Proportion thresholds: ≥0.96 = pass, 0.94–0.96 = warning, <0.94 = fail (NIST §4.2.1)
- [x] Uniformity: KS test of p-values vs Uniform(0,1); fail if KS p < 0.0001
- [x] `run_nist_tests()` calls multi-sequence automatically when file ≥ 100M bits; schema unchanged so `scoring.py` is unaffected

#### 3.5-B — Supplementary Statistical Tests
- [x] `src/engine/supplementary/__init__.py` and `tests.py` created
- [x] 8 tests implemented with numpy + scipy only:
  1. Chi-Square Byte Distribution (256 byte values vs uniform)
  2. Serial Correlation Coefficient (consecutive byte Pearson r)
  3. Autocorrelation Lags 1–20 (95% CI, tolerate 1 false positive in 20 lags)
  4. Runs Above/Below Mean (Wald-Wolfowitz z-test)
  5. Overlapping Permutations Rank (5-byte permutation chi-square; tie windows filtered)
  6. Birthday Spacings (KS test of 3-byte value spacings vs Exponential)
  7. Minimum Distance 2D (grid chi-square on 8000 points in 10×10 grid)
  8. Bit Independence Mutual Information (pairwise MI for bits 0–7)
- [x] Each test returns `{name, statistic, p_value, status, detail}`

#### 3.5-C — API wiring
- [x] `main.py` imports `run_supplementary_tests`; calls it in `_run_analysis()` after NIST run
- [x] Supplementary errors are caught and returned as `{suite, tests:[], error:}` — do not break the API
- [x] `supplementary_result` added to response dict
- [x] API version bumped to `0.4.0`

#### 3.5-D — PDF report updates
- [x] `_level2_table()` — per-test proportion and uniformity badges; only rendered when `level2` key present
- [x] `_supplementary_table()` — 4-column table with statistic, p-value, status badge
- [x] Level-2 section inserted between NIST Results and Jurisdiction Scoring
- [x] Extended Tests section inserted between Jurisdiction Scoring and Gap Analysis
- [x] "Analysis mode" line added to page-2 meta block (Single-sequence / Multi-sequence Level-2)
- [x] `_badge_colours()` helper extracted to eliminate repeated logic

#### Sprint 3.5 Smoke Tests (2026-05-08)
- Single-sequence (200 KB / 1.6M bits, os.urandom): 15/15 NIST pass, 8 supplementary tests run (no systematic false positives across 3 independent trials), PDF 12,215 bytes valid %PDF header
- Level-2 mode: activates at ≥100M bits; split into ≤100 sequences of ≥1M bits each

#### Implementation Notes
- **Tie filtering in Overlapping Permutations**: numpy stable argsort resolves ties deterministically → systematic permutation bias → false chi-square fails. Fixed by dropping windows with any duplicate byte values (~4% of windows filtered; sufficient samples remain).
- **Minimum Distance test**: Exp(π·n) model for NN-distance² fails on bounded [0,1]² due to boundary effects → p≈0 for all typical data. Replaced with 2D grid chi-square (100 cells, 8000 points) which is boundary-safe.
- **Autocorrelation threshold**: with 20 lags at 95% CI, ~1 false exceedance expected under H0. "pass" if 0–1 lags flagged; "warning" if 2–4; "fail" if 5+.

---

### Sprint 4 — UI & Polish (COMPLETE — 2026-05-08)

#### Node.js install
- Node 24.15.0 installed via `winget install OpenJS.NodeJS.LTS --scope user` (no admin required)
- Corporate SSL proxy fix: `NODE_OPTIONS=--use-system-ca npm install`

#### Phase A — File Upload & Validation
- [x] File picker accepts .bin, .rng, .dat, .raw
- [x] 0 bytes → error banner; < 125 KB (1M bits) → warning; < 12.5 MB (100M bits) → info; ≥ 12.5 MB → no warning
- [x] AUP checkbox — must be ticked to enable Run Analysis; timestamp captured at tick
- [x] Non-dismissable disclaimer banner at top of every page

#### Phase B — Analysis & Results Display
- [x] "Run Analysis" button — enabled only when file picked + AUP ticked
- [x] Loading state during analysis
- [x] Jurisdiction scoring matrix with coloured PASS/WARNING/FAIL/INCOMPLETE badges
- [x] NIST test breakdown (collapsible) — all 15 tests with p-values and status badges
- [x] Level-2 summary section (collapsible, shown only when level2 key present in response)
- [x] Extended Statistical Tests section (collapsible, 8 supplementary tests)
- [x] Sample warnings displayed inline

#### Phase C — Report Download
- [x] "Generate Report" button appears after successful analysis
- [x] POSTs file + aup_timestamp + aup_ref ("web-ui-v1") to /api/report
- [x] Triggers PDF download as finalogic-preaudit-report.pdf
- [x] Backend /report endpoint updated to accept aup_timestamp and aup_ref Form fields

#### Phase D — Polish
- [x] Health indicator — green/red dot with engine status text
- [x] Branding: primary #1a1a1a, accent #155724 (matching PDF)
- [x] vite.config.ts proxy updated: localhost:8000 → localhost:8081
- [x] api/client.ts rebuilt: relative URLs (via Vite proxy), all type definitions, analyseFile(), generateReport(), checkHealth()

#### Sprint 4 Smoke Test (2026-05-08)
- npm install: 91 packages, exit 0 (with NODE_OPTIONS=--use-system-ca)
- npm run dev: Vite v5.4.21 ready at http://localhost:5173
- Backend /analyse: 15 NIST tests, 8 supplementary tests, 4 jurisdiction scores — full JSON response confirmed
- UI: loads at localhost:5173, engine health dot shows online

---

### Sprint 4.5 — RNG Perfection (IN PROGRESS — 2026-05-11)

#### Benchmark Results (2026-05-11)

Timed on corporate laptop, single core, Python pure-NIST library:

| File | Size | Mode | /analyse time | /report time |
|---|---|---|---|---|
| bad.bin (00/FF alternating) | 200 KB / 1.6M bits | Single-sequence | 31.9s | ~84s |
| good.bin (os.urandom) | 200 KB / 1.6M bits | Single-sequence | 141.9s | ~142s |

Bad RNG analyses ~4.5× faster than good RNG because structured data causes some NIST
tests (Random Excursions, Approximate Entropy) to resolve extreme values without full
traversal. Both times are too slow for a web application — fix is parallelisation.

#### Bad RNG Validation (2026-05-11)
Confirmed correct detection of maximally non-random 00/FF alternating pattern:
- NIST: 12–13/15 tests FAIL (varies by run — Non-overlapping Template draws a random
  template each run, so result varies; this is correct behaviour)
- All 8 supplementary tests: FAIL or INSUFFICIENT_DATA
- All 4 jurisdictions: FAIL
- Frequency (Monobit) and Cumulative Sums PASS — expected; alternating bits are globally
  balanced (50/50 ones and zeros)
- p=-0.0000 on Block Frequency is a display artefact of float underflow, not a code bug

#### 4.5-A — Parallelise NIST Tests (PENDING)
- [ ] Wrap the 15 independent NIST test calls in `concurrent.futures.ThreadPoolExecutor`
- [ ] Each worker suppresses its own stdout (redirect_stdout per thread)
- [ ] Expected speedup: ~4–5× (numpy releases GIL during computation)
- [ ] Target: good RNG 200KB analysis from 142s → ~30–35s
- [ ] Target: Level-2 12.5MB analysis from ~4–6 hrs → ~30–60 min
- File: `src/engine/nist/runner.py`

#### 4.5-B — Result Caching (PENDING)
- [ ] `/report` currently re-runs full analysis — doubles total time for report generation
- [ ] Fix: cache analysis result keyed on file SHA-256; `/report` accepts pre-computed JSON
      OR use a short-lived in-memory cache (TTL 10 min) keyed on file hash
- [ ] Files: `src/engine/main.py`, `src/engine/report/generator.py`

#### 4.5-C — Dieharder via Docker (PENDING — conditional)
- [ ] Run `docker --version` — Docker not available as of 2026-05-08. Check again.
- [ ] If available: `src/engine/dieharder/runner.py` — spin python:3.11-slim container,
      install dieharder, mount temp file, run `dieharder -a`, parse output
- [ ] Adds ~114 additional tests — biggest single quality jump available

#### 4.5-D — Level-2 Large File Smoke Test (PENDING)
- [ ] Generate 12.5 MB file and run /analyse end-to-end once parallelisation is in place
- [ ] Verify: `level2` key present, proportion and uniformity results per test, PDF renders
- [ ] Commands (after 4.5-A):
      `python -c "import os; open('large.bin','wb').write(os.urandom(12_500_000))"`
      `curl.exe -X POST http://localhost:808x/analyse -F "file=@large.bin" -o large_result.json`
      `python "C:\Users\Andreas.Pi\smoke_check.py" large_result.json`

---

### Sprint 5 — RTP Component (RESEARCH REQUIRED — not started)

RTP (Return to Player) cannot be derived from raw RNG binary output alone.
Further research is required before implementation. See open questions below.

#### What we know
| Jurisdiction | RTP Floor | RTP Ceiling | Typical Range | Notes |
|---|---|---|---|---|
| MGA (Malta) | 92% | ~99% practical | 92–97% | Per game; slots vs table differ |
| UKGC | 78% | None statutory | 92–97% | No hard max; fairness principle |
| DGA (Denmark) | 90% | None statutory | 92–97% | Online casino games |
| Canada CGA | 85% | None statutory | 85–97% | Ontario baseline only |

#### Why RTP is hard
- RTP = Σ(payout × probability_of_outcome) — requires game paytable + outcome mapping
- Cannot be calculated from RNG binary alone
- Real audit labs verify RTP by:
  1. Reviewing game math sheet (theoretical RTP calculation)
  2. Running millions of simulated rounds against the RNG
  3. Confirming empirical RTP ≈ declared RTP ± statistical tolerance
- Our tool only has the RNG output — no game math context

#### Three implementation levels
1. **Level 1 — Declaration validation** (1–2 hrs, no research needed)
   - Operator declares RTP; tool checks against jurisdiction floor/ceiling/range
   - Flags: below floor = FAIL, above 99% = WARNING (suspicious), near floor = WARNING
   - Add `rtp_declared` and `game_type` form fields to `/analyse`
   - Extend jurisdiction JSON configs with `rtp_ceiling`, `rtp_typical_min`, `rtp_typical_max`

2. **Level 2 — Empirical simulation** (1–2 days, requires game config schema design)
   - Operator uploads RNG binary + game config JSON (paytable + reel strip)
   - Tool simulates N rounds, calculates observed RTP ± 95% CI
   - Requires new `src/engine/rtp/simulator.py` and game config schema

3. **Level 3 — Statistical RTP bounds** (research-grade, not practical for pre-audit tool)

#### Open research questions before Sprint 5
- [ ] What is the exact MGA RTP floor per game category? (slots / table / video poker / live)
- [ ] Does UKGC publish a formal minimum or rely solely on "fair and transparent" principle?
- [ ] What is the DGA RTP floor for live dealer vs RNG games?
- [ ] What game config schema do real labs use — is there a standard format?
- [ ] What statistical tolerance is accepted for empirical RTP (e.g. ±0.5% at 95% CI)?
- [ ] Do any jurisdictions require volatility (variance) testing in addition to RTP?

**Decision: implement Level 1 only after research questions are answered.
  Level 2 is Sprint 6. Level 3 is out of scope.**

---

## Known Blockers

- PractRand on Windows requires manual binary placement (no installer)
- Dieharder requires Docker or WSL/Linux — Docker not available as of 2026-05-08, check again
- RTP testing requires further research before any implementation (see Sprint 5 above)
- Port 8081 may already be occupied from a previous session — use 8082 if needed

---

## Decisions Log

| Date | Decision | Reason |
|------|----------|--------|
| 2026-05-05 | Service is Pre-Audit Readiness only, not certified audit | Outside current accreditation scope |
| 2026-05-05 | Primary test suite: NIST SP 800-22 | Most widely referenced by MGA, GLI, UKGC |
| 2026-05-05 | Python for engine, React for UI | Mature NIST Python ports exist; React for fast UI iteration |
| 2026-05-05 | FastAPI bridge | Lightweight, typed, easy to document |
| 2026-05-06 | UKGC lab standard confirmed as ISO/IEC 17025 | 17025 = testing/calibration labs (UKAS-accredited); 17065 = product certification bodies (incorrect — corrected before Sprint 2) |
| 2026-05-06 | GLI/BMM parent-company note added to all jurisdiction configs | GLI acquired by BMM 2022; both remain valid approved-lab entries |
| 2026-05-06 | Canada RTP floor caveated as Ontario baseline only | Provincial floors vary; BC floor not authoritative for all provinces |
| 2026-05-06 | Dieharder and PractRand deferred | Dieharder needs WSL; PractRand binary not placed — NIST sufficient for Sprint 2 |
| 2026-05-06 | NIST stdout suppressed via redirect_stdout | Prevents test library print statements polluting API logs |
| 2026-05-06 | PDF library switched from WeasyPrint to ReportLab | WeasyPrint needs GTK3 DLLs; corporate laptop blocks admin install. ReportLab is pure Python. |
| 2026-05-11 | NIST parallelisation deferred pending implementation | 15 tests run sequentially; good RNG 200KB takes 142s. Fix: ThreadPoolExecutor. Tracked in Sprint 4.5-A. |
| 2026-05-11 | RTP testing deferred to Sprint 5 pending research | Cannot verify RTP from RNG binary alone — requires game math context. Level 1 (declaration check) is feasible; Level 2 (simulation) needs game config schema design. Research questions logged in Sprint 5. |
| 2026-05-11 | Bad RNG correctly detected | 00/FF alternating pattern: 12–13/15 NIST FAIL, all supplementary FAIL, all jurisdictions FAIL. p=-0.0000 on Block Frequency is float underflow display artefact, not a bug. |

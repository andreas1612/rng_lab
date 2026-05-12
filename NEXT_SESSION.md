# Next Session Prompt — Finalogic Pre-Audit Tool

Paste this entire file as your first message in the next Claude Code session.

---

## Project

**Finalogic Pre-Audit RNG Readiness Tool**  
A web application that runs RNG binary output through statistical test suites and scores results
against 4 iGaming regulatory jurisdictions (MGA, UKGC, Denmark, Canada CGA). Produces a
downloadable PDF Pre-Audit Readiness Report. NOT an accredited audit tool.

**Working directory:**
```
C:\Users\Andreas.Pi\Downloads\iGaming TestingLabs Research\finalogic-preaudit-tool\
```

Read CLAUDE.md first. Then STATUS.md. Then this file.

---

## What Is Complete and Working

**Sprints 0–4 complete. Sprint 4.5 in progress. The tool is end-to-end working.**

**To run the tool:**

```powershell
# Terminal 1 — backend
# Note: port 8081 may already be occupied from a previous session.
# Check first: curl.exe -s http://localhost:8081/health
# If occupied, use 8082:
cd "C:\Users\Andreas.Pi\Downloads\iGaming TestingLabs Research\finalogic-preaudit-tool\src\engine"
python -m uvicorn main:app --port 8081
# or: python -m uvicorn main:app --port 8082

# Terminal 2 — frontend (NODE_OPTIONS needed for corporate SSL)
cd "C:\Users\Andreas.Pi\Downloads\iGaming TestingLabs Research\finalogic-preaudit-tool\src\ui"
NODE_OPTIONS=--use-system-ca npm run dev
# Open: http://localhost:5173
```

**Quick smoke test (use whichever port the backend is on):**
```powershell
cd "C:\Users\Andreas.Pi\Downloads\iGaming TestingLabs Research\finalogic-preaudit-tool\src\engine"
python -c "import os; open('test_rng.bin','wb').write(os.urandom(200000))"
curl.exe -s -X POST http://localhost:8081/analyse -F "file=@test_rng.bin" -o result.json
python "C:\Users\Andreas.Pi\smoke_check.py" result.json
curl.exe -X POST http://localhost:8081/report -F "file=@test_rng.bin" -o report.pdf
```
Expected: /analyse ~30–140s (see benchmarks below), returns JSON with 15 NIST tests +
8 supplementary tests + 4 jurisdiction scores. /report returns a valid PDF (~12 KB).

---

## Completed Files

| File | Status |
|---|---|
| src/engine/main.py | Complete — /health, /analyse, /report (v0.4.0) |
| src/engine/scoring.py | Complete — 4 jurisdictions, clean RTP logic |
| src/engine/nist/runner.py | Complete — 15 NIST tests + multi-sequence Level-2 + updated thresholds |
| src/engine/nist/sp800_22_tests/ | Cloned from dj-on-github — do not modify |
| src/engine/supplementary/__init__.py | Complete |
| src/engine/supplementary/tests.py | Complete — 8 supplementary tests |
| src/engine/report/generator.py | Complete — Level-2 table + Extended Tests table sections |
| src/engine/report/gap_analysis.py | Complete — plain-English analysis, p=1.000 artifact detection |
| src/jurisdictions/*.json | Complete — mga, ukgc, denmark, canada_cga |
| src/engine/requirements.txt | Complete — fastapi, uvicorn, numpy, scipy, jinja2, reportlab |
| src/ui/src/App.tsx | Complete — full UI: upload, AUP, results panel, report download |
| src/ui/src/api/client.ts | Complete — typed API client, relative URLs via Vite proxy |
| src/ui/vite.config.ts | Complete — proxy target: localhost:8081 |
| C:\Users\Andreas.Pi\smoke_check.py | Helper — pretty-prints /analyse JSON response |

---

## Environment Constraints — Critical

| Constraint | Detail |
|---|---|
| **No admin access** | Corporate laptop — cannot install system packages, GTK3, or enable Windows features |
| **WSL blocked** | WSL2 optional Windows feature is not enabled — requires admin to turn on. Do not attempt. |
| **Dieharder blocked** | Requires Linux/WSL — deferred until Docker is available |
| **PractRand blocked** | Binary not placed — deferred |
| **WeasyPrint blocked** | Needs GTK3 DLLs — use ReportLab only |
| **Docker** | Not available as of 2026-05-08. Run `docker --version` to check again before Sprint 4.5-C. |
| **Backend port** | Port 8081 preferred. If occupied from previous session, use 8082. |
| **Node.js** | Node 24.15.0 installed via winget (no admin). Use `NODE_OPTIONS=--use-system-ca` for npm. |
| **PowerShell curl** | Use `curl.exe` — PowerShell's built-in `curl` is `Invoke-WebRequest` and behaves differently. |

---

## Key Technical Decisions — Do Not Revisit

| Decision | Why |
|---|---|
| ReportLab (not WeasyPrint) | WeasyPrint needs GTK3 — admin blocked |
| UKGC lab standard: ISO/IEC 17025 | 17025 = testing labs; 17065 = product certification bodies (wrong) |
| Canada RTP 85% = Ontario baseline only | Provincial floors vary — not authoritative nationally |
| NIST stdout suppressed via redirect_stdout | Library prints to stdout — would pollute API logs |
| Port 8081 (fallback 8082) | Port 8000 occupied |
| p ≥ 0.05 = pass, 0.01–0.05 = warning, < 0.01 = fail | Matches jurisdiction threshold configs |
| Minimum Distance 2D = grid chi-square | Exp(π·n) NN model fails on bounded square due to boundary effects — replaced |
| Overlapping Permutations tie-filtering | numpy argsort resolves ties deterministically → false fails — windows with duplicate bytes dropped |
| Autocorrelation threshold: ≤1 lag = pass | 20 lags at 95% CI → ~1 false positive expected under H0 — threshold adjusted |
| RTP deferred to Sprint 5 | Cannot verify RTP from RNG binary alone; requires game math context + further research |

---

## Performance Benchmarks (2026-05-11)

Timed on corporate laptop, sequential NIST execution:

| File | Size | /analyse time |
|---|---|---|
| bad.bin (00/FF alternating) | 200 KB | 31.9s |
| good.bin (os.urandom) | 200 KB | 141.9s |
| large.bin (os.urandom) | 12.5 MB Level-2 | ~4–6 hrs (pre-fix) |

**Root cause:** 15 NIST tests run sequentially. Good random data requires full computation;
structured data resolves faster. Fix in Sprint 4.5-A: ThreadPoolExecutor parallelisation.

**After fix targets:** 200KB good RNG → ~30s. 12.5MB Level-2 → ~30–60 min.

---

## Current Sprint: 4.5 — RNG Perfection

### 4.5-A — Parallelise NIST Tests (PRIORITY 1)

**File:** `src/engine/nist/runner.py`

In `_run_tests_on_bits(bits)`, replace the sequential loop over `TEST_FUNCTIONS` with
a `concurrent.futures.ThreadPoolExecutor`. numpy releases the GIL during computation
so threading gives real speedup on this workload.

Key constraints:
- Each thread must suppress its own stdout (redirect_stdout with io.StringIO per call)
- Return order must be preserved (use `executor.map` or sort by index)
- Must not break existing schema — return same dict shape

Rough structure:
```python
from concurrent.futures import ThreadPoolExecutor
import io
from contextlib import redirect_stdout

def _run_single_test(args):
    test_fn, bits = args
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = test_fn(bits)
    return result

def _run_tests_on_bits(bits):
    args = [(fn, bits) for fn in TEST_FUNCTIONS]
    with ThreadPoolExecutor(max_workers=15) as ex:
        results = list(ex.map(_run_single_test, args))
    return results
```

After implementing, rerun benchmarks:
```powershell
Measure-Command { curl.exe -s -X POST http://localhost:808x/analyse -F "file=@good.bin" -o good_result2.json }
```

### 4.5-B — Result Caching (PRIORITY 2)

`/report` re-runs the full analysis, doubling total time. Fix: cache analysis result
keyed on SHA-256 of the uploaded file, TTL 10 minutes. `/report` hits cache if same
file was recently analysed.

**File:** `src/engine/main.py`

```python
import hashlib, time
_cache: dict = {}   # {sha256: (timestamp, result_dict)}
CACHE_TTL = 600     # 10 minutes

def _cache_get(sha256):
    entry = _cache.get(sha256)
    if entry and time.time() - entry[0] < CACHE_TTL:
        return entry[1]
    return None

def _cache_set(sha256, result):
    _cache[sha256] = (time.time(), result)
```

Compute SHA-256 from the temp file bytes after upload. Check cache before running
analysis. Store result after analysis. Both `/analyse` and `/report` use the same helper.

### 4.5-C — Dieharder via Docker (CONDITIONAL)

Run `docker --version`. If Docker Desktop is running:
- Create `src/engine/dieharder/runner.py`
- Spins `python:3.11-slim` container, installs dieharder, mounts temp file
- Runs `dieharder -a`, captures stdout, parses into structured results
- Adds `dieharder_result` to API response
- Adds "Dieharder Results" PDF section
- ~114 additional tests — biggest single quality jump

If Docker not available: skip, note in STATUS.md.

### 4.5-D — Level-2 Large File Smoke Test

Run after 4.5-A is complete:
```powershell
python -c "import os; open('large.bin','wb').write(os.urandom(12_500_000))"
Measure-Command { curl.exe -s -X POST http://localhost:808x/analyse -F "file=@large.bin" -o large_result.json }
python "C:\Users\Andreas.Pi\smoke_check.py" large_result.json
```
Verify: `Level-2 mode: YES`, proportion and uniformity results present, all checks complete.

---

## Sprint 5 — RTP Component (RESEARCH REQUIRED)

**Do not implement until research questions are answered. See STATUS.md Sprint 5 section.**

RTP cannot be verified from raw RNG binary output alone. Three implementation levels exist:
1. **Level 1** — Declaration validation (operator declares RTP, tool checks against floors/ceilings)
2. **Level 2** — Empirical simulation (operator provides game config + RNG binary; tool simulates rounds)
3. **Level 3** — Out of scope

Known jurisdiction floors: MGA 92%, UKGC 78%, DGA 90%, Canada CGA 85% (Ontario only).

Open research questions before any code:
- Exact MGA RTP floors per game category (slots / table / video poker / live)
- Whether UKGC publishes a formal minimum or relies on "fair and transparent" principle
- DGA floor for live dealer vs RNG games
- Standard game config schema used by labs
- Accepted statistical tolerance for empirical RTP verification
- Whether any jurisdiction requires volatility (variance) testing alongside RTP

---

## Coverage vs Real Audit

| Capability | Real Lab | Our Tool |
|---|---|---|
| NIST SP 800-22 (15 tests) | ✅ | ✅ |
| Multi-sequence Level-2 | ✅ | ✅ (≥12.5 MB) |
| 8 supplementary tests | Partial | ✅ |
| Jurisdiction scoring 4 JDs | ✅ | ✅ |
| PDF readiness report | ✅ | ✅ |
| Dieharder (~114 tests) | ✅ | ❌ blocked |
| TestU01 BigCrush (106 tests) | ✅ | ❌ not implemented |
| PractRand | ✅ | ❌ binary not placed |
| Sample size 1B–10B bits | ✅ | ❌ practical max ~100M bits |
| RTP verification | ✅ | ❌ deferred Sprint 5 |
| Physical entropy verification | ✅ | ❌ hardware — not applicable |
| Accredited certificate | ✅ | ❌ by design |

**Coverage: ~40% of a real audit.** Sufficient to find obvious flaws and prepare for submission.

---

## File Reading Order at Session Start

1. `CLAUDE.md` — project guide and DO NOT list
2. `STATUS.md` — sprint log with benchmarks and known issues
3. `NEXT_SESSION.md` — this file
4. `src/engine/nist/runner.py` — NIST runner (target of 4.5-A parallelisation)
5. `src/engine/main.py` — API (target of 4.5-B caching)
6. `src/engine/scoring.py` — jurisdiction scorer
7. `src/engine/report/generator.py` — PDF builder

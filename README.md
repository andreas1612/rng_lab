# Finalogic Pre-Audit RNG Readiness Tool

A web application that runs RNG (Random Number Generator) output files through the
**NIST SP 800-22** statistical test suite and scores the results against the published
thresholds of four iGaming regulatory jurisdictions.

> **⚠️ NOT an accredited audit tool. Results cannot be submitted to any regulatory
> authority. See [docs/legal/LEGAL.md](docs/legal/LEGAL.md) for full disclaimers.**

---

## What it does

Upload a binary RNG output file. The tool:

1. Runs all **15 NIST SP 800-22** tests and reports p-values with pass/warning/fail status
2. Runs **8 supplementary statistical tests** (chi-square, autocorrelation, serial
   correlation, runs, permutations, birthday spacings, 2D spatial uniformity, bit
   independence)
3. For files ≥ 12.5 MB: activates **Level-2 multi-sequence analysis** — splits the file
   into up to 100 independent sequences, runs all 15 tests per sequence, and applies the
   NIST SP 800-22 proportion check and KS uniformity check per test
4. Scores results against **MGA, UKGC, Denmark (DGA), Canada CGA** thresholds
5. Produces a downloadable **PDF Pre-Audit Readiness Report** with gap analysis

---

## Current State — Sprint 4 Complete

| Component | Status |
|---|---|
| FastAPI backend — /health, /analyse, /report | ✅ Complete |
| NIST SP 800-22 runner (15 tests) | ✅ Complete |
| Multi-sequence Level-2 analysis | ✅ Complete (activates ≥ 12.5 MB) |
| 8 supplementary statistical tests | ✅ Complete |
| Jurisdiction scoring — MGA, UKGC, DGA, CGA | ✅ Complete |
| PDF report generation (ReportLab) | ✅ Complete |
| React + TypeScript UI | ✅ Complete |
| File upload, AUP checkbox, results panel | ✅ Complete |
| PDF download from UI | ✅ Complete |
| NIST test parallelisation | 🔄 Sprint 4.5 — in progress |
| Result caching | 🔄 Sprint 4.5 — planned |
| Dieharder integration | ⏸ Blocked — requires Docker/WSL |
| RTP empirical verification | 📋 Sprint 5 — research required |

---

## How it compares to a real accredited audit

| Capability | Real Lab (GLI / eCOGRA / BMM) | This tool |
|---|---|---|
| NIST SP 800-22 (15 tests) | ✅ | ✅ |
| Multi-sequence Level-2 | ✅ | ✅ (≥12.5 MB) |
| Supplementary statistical tests | Partial | ✅ (8 tests) |
| Jurisdiction scoring | ✅ | ✅ (4 jurisdictions) |
| Dieharder (~114 tests) | ✅ | ❌ blocked |
| TestU01 BigCrush (106 tests) | ✅ | ❌ not implemented |
| Sample size 1B–10B bits | ✅ | ❌ practical max ~100M bits |
| RTP verification | ✅ | ❌ Sprint 5 |
| Physical entropy verification | ✅ | ❌ hardware — not applicable |
| Accredited certificate | ✅ | ❌ by design |

**Coverage: ~40% of a real audit.** Sufficient to identify obvious defects and gaps
before engaging an accredited lab.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Vite 5 |
| API | FastAPI (Python 3.11+) on port 8081 |
| NIST engine | sp800_22_tests Python port (dj-on-github) |
| Supplementary tests | NumPy + SciPy (pure Python, no extra deps) |
| PDF generation | ReportLab 4.x (pure Python) |
| Scoring | Custom jurisdiction JSON configs |

---

## Project Structure

```
finalogic-preaudit-tool/
├── README.md                        ← This file
├── STATUS.md                        ← Full sprint log, benchmarks, decisions
├── NEXT_SESSION.md                  ← Handoff notes and next sprint specs
├── CLAUDE.md                        ← Development guide (DO NOT list, conventions)
├── docs/
│   ├── research/
│   │   ├── RESEARCH_DONE.md         ← All research complete — do not re-research
│   │   └── SOURCES.md               ← Reference documents and links
│   ├── algorithms/
│   │   ├── ALGORITHMS.md            ← NIST SP 800-22, Dieharder, PractRand explained
│   │   └── THRESHOLDS.md            ← Per-jurisdiction RTP floors + p-value thresholds
│   └── legal/
│       ├── LEGAL.md                 ← Liability framework + mandatory disclaimer text
│       └── AUP.md                   ← Acceptable Use Policy
└── src/
    ├── engine/                      ← Python FastAPI backend
    │   ├── main.py                  ← API endpoints (v0.4.0)
    │   ├── scoring.py               ← Jurisdiction scoring engine
    │   ├── requirements.txt
    │   ├── nist/
    │   │   ├── runner.py            ← NIST runner — single + multi-sequence Level-2
    │   │   └── sp800_22_tests/      ← NIST Python port (dj-on-github)
    │   ├── supplementary/
    │   │   ├── __init__.py
    │   │   └── tests.py             ← 8 supplementary statistical tests
    │   └── report/
    │       ├── generator.py         ← ReportLab PDF builder
    │       └── gap_analysis.py      ← Plain-English gap analysis
    ├── jurisdictions/               ← JSON threshold configs per jurisdiction
    │   ├── mga.json
    │   ├── ukgc.json
    │   ├── denmark.json
    │   └── canada_cga.json
    ├── report/
    │   └── template.html            ← Jinja2 template (future WeasyPrint migration)
    └── ui/                          ← React + TypeScript frontend
        ├── package.json
        ├── vite.config.ts           ← Proxies /api → localhost:8081
        ├── tsconfig.json
        └── src/
            ├── App.tsx              ← Full UI: upload, AUP, results, download
            └── api/
                └── client.ts        ← Typed API client
```

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11+ | `pip install -r src/engine/requirements.txt` |
| Node.js | 18+ LTS | `npm install` in `src/ui/` |

---

## Running

### Backend

```bash
cd src/engine
pip install -r requirements.txt
python -m uvicorn main:app --port 8081
# Swagger UI: http://localhost:8081/docs
```

### Frontend

```bash
cd src/ui
npm install
npm run dev
# UI: http://localhost:5173
```

### Windows / corporate SSL note

```powershell
NODE_OPTIONS=--use-system-ca npm install
NODE_OPTIONS=--use-system-ca npm run dev
```

---

## Quick Smoke Test (no UI)

```bash
# Generate random test file
python -c "import os; open('test.bin','wb').write(os.urandom(200000))"

# Run analysis
curl -X POST http://localhost:8081/analyse -F "file=@test.bin"

# Download PDF report
curl -X POST http://localhost:8081/report -F "file=@test.bin" -o report.pdf
```

For Level-2 multi-sequence mode (≥ 12.5 MB):

```bash
python -c "import os; open('large.bin','wb').write(os.urandom(12_500_000))"
curl -X POST http://localhost:8081/analyse -F "file=@large.bin"
# Response will include nist_result.level2 with proportion + uniformity per test
```

### Bad RNG validation

```bash
python -c "open('bad.bin','wb').write(bytes([0x00,0xFF]*100000))"
curl -X POST http://localhost:8081/analyse -F "file=@bad.bin"
# Expected: 12-13/15 NIST FAIL, all 4 jurisdictions FAIL
```

---

## Performance Benchmarks

Measured on a corporate laptop (single-core sequential execution):

| File | /analyse time |
|---|---|
| 200 KB good RNG (os.urandom) | ~142s |
| 200 KB bad RNG (00/FF) | ~32s |
| 12.5 MB Level-2 | ~4–6 hrs (pre-parallelisation) |

Sprint 4.5 adds `ThreadPoolExecutor` parallelisation targeting ~4–5× speedup.
Target: 200 KB → ~30s, 12.5 MB Level-2 → ~30–60 min.

---

## API Reference

### `GET /health`
```json
{"status": "ok", "version": "0.4.0"}
```

### `POST /analyse`
Form field: `file` (binary upload)

Returns JSON:
```json
{
  "generated_at": "...",
  "file_info": {"filename": "...", "size_bytes": 200000},
  "nist_result": {
    "sample_info": {"size_bits": 1600000, "sufficient": true, "warnings": []},
    "tests": [
      {"name": "Frequency (Monobit)", "p_value": 0.847, "status": "pass", "detail": "..."},
      ...
    ],
    "level2": { ... }   // only present for files >= 12.5 MB
  },
  "supplementary_result": {
    "tests": [
      {"name": "Chi-Square Byte Distribution", "statistic": 248.3, "p_value": 0.612, "status": "pass"},
      ...
    ]
  },
  "jurisdiction_scores": [
    {"short_name": "MGA", "overall": "pass", "nist_check": {"detail": "..."}, "rtp_check": {...}},
    ...
  ]
}
```

### `POST /report`
Form fields: `file`, `aup_timestamp` (optional), `aup_ref` (optional)

Returns: `application/pdf` stream — Pre-Audit Readiness Report

---

## Jurisdiction Thresholds

| Jurisdiction | NIST pass threshold | RTP floor | Approved labs |
|---|---|---|---|
| MGA (Malta) | p ≥ 0.01 | 92% | GLI, BMM, eCOGRA, iTech |
| UKGC | p ≥ 0.01 | 78% | UKAS-accredited (ISO 17025) |
| Denmark (DGA) | p ≥ 0.01 | 90% | GLI, BMM, eCOGRA |
| Canada CGA | p ≥ 0.01 | 85%* | GLI, BMM |

*Ontario iGaming baseline only. Provincial floors vary.

---

## Next Steps — Sprint 4.5

1. **Parallelise NIST tests** (`ThreadPoolExecutor` in `nist/runner.py`) — 4–5× speedup
2. **Result caching** (SHA-256 keyed, TTL 10 min) — `/report` reuses cached analysis
3. **Dieharder** — if Docker becomes available, adds ~114 tests via container
4. **Level-2 large file smoke test** — validate end-to-end after parallelisation

## Next Steps — Sprint 5 (Research Required)

RTP empirical verification — requires:
- Research on exact per-jurisdiction per-game-category RTP floors
- Game config schema design (paytable + reel layout)
- Simulator implementation (`src/engine/rtp/simulator.py`)

See `STATUS.md` Sprint 5 section for full research questions before any code.

---

## Legal

This tool is a **Pre-Audit Readiness indicator only**. It does not constitute an
accredited statistical audit. Results cannot be submitted to MGA, UKGC, DGA, CGA or
any other regulatory body as evidence of compliance. See `docs/legal/LEGAL.md`.

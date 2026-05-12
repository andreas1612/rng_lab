# Next Session

Last update: 2026-05-12 — end of Sprint 4.5 + UI update.

## Current state

- Tool name: **MiniLab RNG Engine v0.1.0**
- Methodology: `MiniLab-RNG-Methodology-v0.1`
- API version: `0.5.0`
- All 15 NIST tests run in parallel via `ThreadPoolExecutor(max_workers=15)`
- Thread-safe stdout suppression: thread-local proxy in `nist/tests/_wrap.py`
- SHA-256-keyed result cache (TTL 10 min) in `main.py`; second call on same file ≈ 0.3s
- UI fully updated: 6-label badge colours, 5 AUP fields, Report ID + SHA-256 display, label legend

## What works end-to-end (verified 2026-05-12)

- Health: `{"status":"ok","tool_version":"MiniLab RNG Engine v0.1.0",...}`
- `/analyse`: 15 NIST (parallel) + 8 supplementary + jurisdiction scores + report_id + sha256
- `/report`: PDF with all Sprint 5 MVP items, DRAFT watermark, evidence JSON saved
- Cache: cold ~67s, warm ~0.3s (same file)
- UI: engine online dot, AUP fields expand on checkbox tick, results show Report ID + SHA-256 + badge legend
- PDF verified end-to-end with good.bin: RPT-A9AC6CFBC633 — correct labels, no "WARNING" strings

## Quick-start (next session)

```powershell
# 1. Check health
curl.exe -s http://localhost:8081/health
# Expected: {"status":"ok","tool_version":"MiniLab RNG Engine v0.1.0",...}
# If connection refused or wrong version, start fresh:

# 2. Start backend
cd "C:\Users\Andreas.Pi\Downloads\iGaming TestingLabs Research\finalogic-preaudit-tool\src\engine"
python -m uvicorn main:app --port 8081

# 3. Start frontend (separate terminal — use node path directly)
$nodePath = "C:\Users\Andreas.Pi\AppData\Local\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.15.0-win-x64"
$env:PATH = "$nodePath;" + $env:PATH
$env:NODE_OPTIONS = "--use-system-ca"
cd "C:\Users\Andreas.Pi\Downloads\iGaming TestingLabs Research\finalogic-preaudit-tool\src\ui"
npm run dev
# Open: http://localhost:5173
# Note: Vite fails with EPERM if spawned from PowerShell sandbox — start from a real terminal
```

## Open items / next sprint candidates

### Immediate (P1)
1. **Level-2 large file smoke test** — generate 12.5MB and run `/analyse` to confirm
   parallelisation benefit at scale. Commands:
   ```powershell
   python -c "import os; open('large.bin','wb').write(os.urandom(12_500_000))"
   curl.exe -X POST http://localhost:8081/analyse -F "file=@large.bin" -o large_result.json
   ```
2. **Evidence JSON persistence** — currently saved to `tempfile.gettempdir()` (volatile).
   Decide on a persistent path and wire it into the response body (not just the header).

### Sprint 5.1 (P2)
3. **Remove `tests_warning` alias** from `scoring.py` response — the field is emitted as a
   backward-compat alias of `tests_borderline`. Safe to remove once UI is confirmed updated
   (it is — `client.ts` reads `tests_borderline` with `tests_warning` as fallback).
4. **`smoke_check.py` update** — CLI tool still displays old label strings; update to match
   6-label scheme.

### Sprint 6 (P3 — RTP research required first)
5. **RTP Level 1** — declaration validation. Read open research questions in
   `docs/methodology/METHODOLOGY_v0.1.md` and answer all 6 before writing any code.
6. **RTP Level 2** — empirical simulation (needs game config schema design).

### Blocked (P4)
7. Dieharder — needs Docker or WSL (neither available)
8. PractRand — binary not placed
9. TestU01 BigCrush — not implemented

## File map (Sprint 4.5 + UI deltas)

Modified:
- `src/engine/nist/runner.py` — `_run_tests_on_bits()` now uses `ThreadPoolExecutor(max_workers=15)`; added `concurrent.futures` import
- `src/engine/nist/tests/_wrap.py` — thread-safe stdout suppressor (`_TLSStdout` proxy, `_suppress_stdout()` context manager); removed `redirect_stdout`
- `src/engine/main.py` — `_CACHE_TTL_SECONDS`, `_cache`, `_cache_lock`, `_cache_get()`, `_cache_put()` added; `_run_analysis()` checks cache before running tests
- `src/ui/src/api/client.ts` — updated `TestStatus`/`OverallStatus` to 6-label uppercase scheme; added `AupFields` type; `analyseFile()` and `generateReport()` now accept and send all 5 AUP form fields; `AnalysisResult` includes `report_id`, `input_sha256`, `tool_version`, `methodology_version`, `aup`
- `src/ui/src/App.tsx` — 6-label badge colours (BORDERLINE=orange, INDICATIVE_ONLY=blue, INCONCLUSIVE/NOT_RUN=grey); 5 AUP form fields (accepted_by, timestamp readonly, version, ref_id); Report metadata block (Report ID, SHA-256, tool/methodology version); label legend inline; AUP record collapsible section

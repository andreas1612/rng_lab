# Claude Code — First Prompt

Copy everything below this line and paste it as your first message to Claude Code after
opening it in the `finalogic-preaudit-tool/` directory.

---

## CLAUDE CODE INSTRUCTION — SPRINT 1: SCAFFOLD ONLY

You are setting up the Finalogic Pre-Audit RNG Readiness Tool project.
This is Sprint 1 — scaffold and environment only. No business logic yet.

Before writing any code, read these files in order:
1. README.md
2. STATUS.md
3. docs/research/RESEARCH_DONE.md
4. docs/algorithms/ALGORITHMS.md
5. docs/algorithms/THRESHOLDS.md
6. docs/legal/LEGAL.md
7. docs/legal/AUP.md

Once you have read all 7 files, proceed with the following tasks in order.

---

### TASK 1 — Python Backend (FastAPI)

Initialise a FastAPI project in `src/engine/`:

- Create `src/engine/requirements.txt` with: fastapi, uvicorn, python-multipart, numpy, scipy
- Create `src/engine/main.py` — a minimal FastAPI app with:
  - One GET endpoint: `/health` returning `{"status": "ok"}`
  - One POST endpoint: `/analyse` that accepts a binary file upload and returns a placeholder `{"status": "received", "filename": "<name>", "size_bytes": <size>}` — no actual test running yet
  - CORS enabled for localhost:5173 (the Vite dev server port)
- Create `src/engine/README.md` explaining how to run: `pip install -r requirements.txt` then `uvicorn main:app --reload`

### TASK 2 — NIST Engine Stub

- Create `src/engine/nist/__init__.py` (empty, marks it as a package)
- Create `src/engine/nist/runner.py` — a stub with one function `run_nist_tests(filepath: str) -> dict` that returns a hardcoded placeholder result structure matching what the real NIST runner will return:
  ```python
  {
    "suite": "NIST SP 800-22",
    "tests": [
      {"name": "Frequency (Monobit)", "p_value": None, "status": "not_run"},
      # ... all 15 tests listed with None p_value and "not_run" status
    ]
  }
  ```
  Include all 15 NIST test names from docs/algorithms/ALGORITHMS.md. No actual test running yet.

### TASK 3 — Jurisdiction Config Files

Create one JSON file per jurisdiction in `src/jurisdictions/`:

- `mga.json` — MGA thresholds per THRESHOLDS.md
- `ukgc.json` — UKGC thresholds per THRESHOLDS.md
- `denmark.json` — Denmark thresholds per THRESHOLDS.md
- `canada_cga.json` — CGA thresholds per THRESHOLDS.md

Each JSON must follow this schema:
```json
{
  "id": "mga",
  "name": "Malta Gaming Authority",
  "short_name": "MGA",
  "min_rtp_percent": 85,
  "p_value_floor": 0.01,
  "p_value_warning_floor": 0.05,
  "confidence_interval_percent": 95,
  "statistical_standard": "NIST SP 800-22",
  "notes": "..."
}
```

### TASK 4 — React Frontend (Vite)

Initialise a React + TypeScript Vite project in `src/ui/`:
```bash
npm create vite@latest . -- --template react-ts
npm install
npm install axios
```

Then:
- Delete the default `App.css` content and replace with a blank file
- Replace `App.tsx` with a minimal shell that renders:
  - A header: "Finalogic Pre-Audit RNG Readiness Tool"
  - A subtitle: "Pre-Audit Readiness Assessment — Not an Accredited Audit"
  - A placeholder `<div>` with text "Upload interface coming in Sprint 2"
  - A footer with the short disclaimer from LEGAL.md (one sentence)
- Create `src/ui/src/api/client.ts` — an axios instance pointing to `http://localhost:8000`
  with one exported function `checkHealth(): Promise<{status: string}>` calling GET `/health`

### TASK 5 — Root Config Files

In `finalogic-preaudit-tool/` (root):
- Create `.gitignore` covering: `node_modules/`, `__pycache__/`, `*.pyc`, `.env`, `dist/`, `build/`, `*.egg-info/`
- Create `package.json` at root level (workspace root) with scripts:
  - `"dev:ui"`: `cd src/ui && npm run dev`
  - `"dev:api"`: `cd src/engine && uvicorn main:app --reload`
- Do NOT create a docker file yet

### TASK 6 — Verify and Report

After completing all tasks:
1. Run `cd src/ui && npm install && npm run build` — confirm it builds without errors
2. Run `cd src/engine && pip install -r requirements.txt` — confirm packages install
3. Update STATUS.md — mark Sprint 1 tasks as complete, note any issues encountered
4. List every file you created in a summary at the end of your response

---

## What NOT to Do in This Sprint

- Do not implement the actual NIST test runner (Sprint 2)
- Do not implement PDF report generation (Sprint 3)
- Do not add any styling beyond what ships with Vite's default (Sprint 4)
- Do not add authentication, user accounts, or a database
- Do not modify any files in `docs/` or `docs/legal/`

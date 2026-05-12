# Engine — FastAPI Backend

## Setup

```bash
cd src/engine
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload
```

API docs available at http://localhost:8000/docs

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Returns `{"status": "ok"}` |
| POST | `/analyse` | Accepts binary file upload; returns filename and size (Sprint 1 stub) |

## NIST Module

`nist/runner.py` contains `run_nist_tests(filepath)` — a stub that returns the full
15-test result structure with `"not_run"` status. Real implementation added in Sprint 2.

Clone the NIST SP 800-22 Python port here before Sprint 2:
```bash
git clone https://github.com/dj-on-github/sp800_22_tests.git nist/sp800_22_tests
```

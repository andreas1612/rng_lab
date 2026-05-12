import io
import os
import tempfile
from datetime import datetime, timezone

from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from nist.runner import run_nist_tests
from scoring import score_against_jurisdictions
from supplementary import run_supplementary_tests

from report.gap_analysis import generate_gap_analysis
from report.generator import generate_pdf

REPORT_AVAILABLE = True

app = FastAPI(title="Finalogic Pre-Audit Engine", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".bin", ".rng", ".dat", ".raw"}


async def _run_analysis(file: UploadFile) -> dict:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{ext}'. "
                f"Submit a binary file: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    contents = await file.read()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        try:
            nist_result = run_nist_tests(tmp_path)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=500, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"NIST runner error: {exc}")

        try:
            supplementary_result = run_supplementary_tests(tmp_path)
        except Exception as exc:
            supplementary_result = {
                "suite": "Supplementary Statistical Tests",
                "tests": [],
                "error": f"Supplementary tests failed: {exc}",
            }

        jurisdiction_scores = score_against_jurisdictions(nist_result)

        return {
            "filename": file.filename,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "nist_result": nist_result,
            "supplementary_result": supplementary_result,
            "jurisdiction_scores": jurisdiction_scores,
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyse")
async def analyse(file: UploadFile = File(...)):
    return await _run_analysis(file)


@app.post("/report")
async def report(
    file: UploadFile = File(...),
    aup_timestamp: Optional[str] = Form(None),
    aup_ref: Optional[str] = Form(None),
):
    result = await _run_analysis(file)
    if aup_timestamp:
        result["aup_timestamp"] = aup_timestamp
    if aup_ref:
        result["aup_ref"] = aup_ref
    result["gap_analysis_html"] = generate_gap_analysis(
        result["jurisdiction_scores"],
        result["nist_result"],
    )

    try:
        pdf_bytes = generate_pdf(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation error: {exc}")

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="finalogic-preaudit-report.pdf"'},
    )

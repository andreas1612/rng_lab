import hashlib
import io
import os
import tempfile
import threading
import time
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from core.labels import TOOL_VERSION, METHODOLOGY_VERSION
from core.models import AUPRecord
from core.report_id import generate_report_id

from nist.runner import run_nist_tests
from scoring import score_against_jurisdictions
from supplementary import run_supplementary_tests

from report.gap_analysis import generate_gap_analysis
from report.generator import generate_pdf
from report.json_output import build_evidence_json, save_evidence_json

REPORT_AVAILABLE = True

# ---------------------------------------------------------------------------
# In-memory analysis cache — keyed by input SHA-256, TTL 10 minutes.
# Prevents /report from re-running the full NIST suite when the same file
# was analysed moments before via /analyse.
# ---------------------------------------------------------------------------
_CACHE_TTL_SECONDS = 600  # 10 minutes
_cache: dict = {}          # sha256 → {"result": dict, "expires_at": float}
_cache_lock = threading.Lock()


def _cache_get(sha256: str) -> dict | None:
    with _cache_lock:
        entry = _cache.get(sha256)
        if entry is None:
            return None
        if time.monotonic() > entry["expires_at"]:
            del _cache[sha256]
            return None
        return entry["result"]


def _cache_put(sha256: str, result: dict) -> None:
    with _cache_lock:
        _cache[sha256] = {
            "result": result,
            "expires_at": time.monotonic() + _CACHE_TTL_SECONDS,
        }

app = FastAPI(title="MiniLab RNG Engine", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".bin", ".rng", ".dat", ".raw"}


def _build_aup_record(accepted, accepted_by, ts, version, ref_id) -> AUPRecord:
    return AUPRecord(
        accepted=bool(accepted),
        accepted_by=accepted_by or "Not recorded",
        acceptance_timestamp_utc=ts or "Not recorded",
        aup_version=version or "Not recorded",
        aup_reference_id=ref_id or "Not recorded",
    )


async def _run_analysis(file: UploadFile, aup_record: AUPRecord) -> dict:
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
    input_size_bytes = len(contents)
    input_sha256 = hashlib.sha256(contents).hexdigest()

    # Return cached analysis result if the same file was analysed recently.
    # The AUP record is per-call and does not affect the analysis, so caching
    # the statistical results is safe. report_id and generated_at are also
    # cached — callers that need a fresh ID should not use /report for that.
    cached = _cache_get(input_sha256)
    if cached is not None:
        # Overlay the current AUP record onto the cached result.
        result = dict(cached)
        result["aup_record"] = aup_record
        return result

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

        report_id = generate_report_id()
        generated_at = datetime.now(timezone.utc).isoformat()
        size_bits = nist_result.get("sample_info", {}).get("size_bits", input_size_bytes * 8)

        result = {
            "report_id": report_id,
            "tool_version": TOOL_VERSION,
            "methodology_version": METHODOLOGY_VERSION,
            "filename": file.filename,
            "input_sha256": input_sha256,
            "input_size_bytes": input_size_bytes,
            "input_size_bits": size_bits,
            "generated_at": generated_at,
            "aup_record": aup_record,
            "nist_result": nist_result,
            "supplementary_result": supplementary_result,
            "jurisdiction_scores": jurisdiction_scores,
        }
        _cache_put(input_sha256, result)
        return result
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.get("/health")
def health():
    return {"status": "ok", "tool_version": TOOL_VERSION,
            "methodology_version": METHODOLOGY_VERSION}


@app.post("/analyse")
async def analyse(
    file: UploadFile = File(...),
    aup_accepted: bool = Form(False),
    aup_accepted_by: str = Form("Not recorded"),
    aup_acceptance_timestamp: str = Form("Not recorded"),
    aup_version_field: str = Form("Not recorded"),
    aup_reference_id: str = Form("Not recorded"),
):
    aup_record = _build_aup_record(
        aup_accepted, aup_accepted_by, aup_acceptance_timestamp,
        aup_version_field, aup_reference_id,
    )
    result = await _run_analysis(file, aup_record)
    # Return JSON-safe payload (replace dataclass with dict).
    return {
        "report_id": result["report_id"],
        "tool_version": result["tool_version"],
        "methodology_version": result["methodology_version"],
        "filename": result["filename"],
        "input_sha256": result["input_sha256"],
        "input_size_bytes": result["input_size_bytes"],
        "input_size_bits": result["input_size_bits"],
        "generated_at": result["generated_at"],
        "aup": {
            "accepted": aup_record.accepted,
            "accepted_by": aup_record.accepted_by,
            "acceptance_timestamp_utc": aup_record.acceptance_timestamp_utc,
            "aup_version": aup_record.aup_version,
            "aup_reference_id": aup_record.aup_reference_id,
        },
        "nist_result": result["nist_result"],
        "supplementary_result": result["supplementary_result"],
        "jurisdiction_scores": result["jurisdiction_scores"],
    }


@app.post("/report")
async def report(
    file: UploadFile = File(...),
    aup_accepted: bool = Form(False),
    aup_accepted_by: str = Form("Not recorded"),
    aup_acceptance_timestamp: str = Form("Not recorded"),
    aup_version_field: str = Form("Not recorded"),
    aup_reference_id: str = Form("Not recorded"),
):
    aup_record = _build_aup_record(
        aup_accepted, aup_accepted_by, aup_acceptance_timestamp,
        aup_version_field, aup_reference_id,
    )
    result = await _run_analysis(file, aup_record)
    result["gap_analysis_html"] = generate_gap_analysis(
        result["jurisdiction_scores"],
        result["nist_result"],
    )

    try:
        pdf_bytes = generate_pdf(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation error: {exc}")

    # Build and save the evidence JSON alongside the PDF.
    evidence = build_evidence_json(
        report_id=result["report_id"],
        generated_at=result["generated_at"],
        input_filename=result["filename"],
        input_sha256=result["input_sha256"],
        input_size_bytes=result["input_size_bytes"],
        input_size_bits=result["input_size_bits"],
        aup_record=aup_record,
        nist_tests=result["nist_result"].get("tests", []),
        supplementary_tests=result["supplementary_result"].get("tests", []),
        jurisdiction_scores=result["jurisdiction_scores"],
        level2=result["nist_result"].get("level2"),
    )
    json_path = save_evidence_json(tempfile.gettempdir(), result["report_id"], evidence)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{result["report_id"]}.pdf"',
            "X-Report-Id": result["report_id"],
            "X-Input-SHA256": result["input_sha256"],
            "X-Tool-Version": TOOL_VERSION,
            "X-Methodology-Version": METHODOLOGY_VERSION,
            "X-Evidence-JSON-Path": json_path,
        },
    )

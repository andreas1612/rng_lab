"""
Produces the JSON evidence file alongside every PDF report.
Filename: <report_id>.json
"""
import json
import os

from core.labels import (
    TOOL_VERSION, METHODOLOGY_VERSION,
    PASS_THRESHOLD, BORDERLINE_LOWER,
    SCOPE_LIMITATION, LEGEND,
)


def build_evidence_json(report_id, generated_at, input_filename, input_sha256,
                        input_size_bytes, input_size_bits, aup_record,
                        nist_tests, supplementary_tests, jurisdiction_scores,
                        level2=None):
    return {
        "metadata": {
            "report_id": report_id,
            "generated_at_utc": generated_at,
            "tool_version": TOOL_VERSION,
            "methodology_version": METHODOLOGY_VERSION,
        },
        "input_file": {
            "filename": input_filename,
            "sha256": input_sha256,
            "size_bytes": input_size_bytes,
            "size_bits": input_size_bits,
        },
        "aup": {
            "accepted": aup_record.accepted,
            "accepted_by": aup_record.accepted_by,
            "acceptance_timestamp_utc": aup_record.acceptance_timestamp_utc,
            "aup_version": aup_record.aup_version,
            "aup_reference_id": aup_record.aup_reference_id,
        },
        "threshold_scheme": {
            "pass_threshold": PASS_THRESHOLD,
            "borderline_lower": BORDERLINE_LOWER,
            "bands": {
                "PASS": f"p >= {PASS_THRESHOLD}",
                "BORDERLINE": f"{BORDERLINE_LOWER} <= p < {PASS_THRESHOLD}",
                "FAIL": f"p < {BORDERLINE_LOWER}",
            },
            "legend": LEGEND,
        },
        "results": {
            "nist_sp800_22": nist_tests,
            "supplementary": supplementary_tests,
            "level2": level2,
            "jurisdiction_scores": jurisdiction_scores,
        },
        "scope_limitation": SCOPE_LIMITATION,
    }


def save_evidence_json(output_dir, report_id, evidence):
    filename = f"{report_id}.json"
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)
    return path

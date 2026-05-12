from dataclasses import dataclass


@dataclass
class AUPRecord:
    accepted: bool = False
    accepted_by: str = "Not recorded"
    acceptance_timestamp_utc: str = "Not recorded"
    aup_version: str = "Not recorded"
    aup_reference_id: str = "Not recorded"

    def is_complete(self):
        return self.accepted and self.accepted_by != "Not recorded"


@dataclass
class ReportMetadata:
    report_id: str
    generated_at_utc: str
    tool_version: str
    methodology_version: str
    input_filename: str
    input_sha256: str
    input_size_bytes: int
    input_size_bits: int
    aup: AUPRecord

import uuid


def generate_report_id():
    return "RPT-" + str(uuid.uuid4()).replace("-", "").upper()[:12]

"""
MiniLab RNG Engine - centralised label and threshold definitions.
ALL test result classification MUST use classify_p_value().
"""

TOOL_VERSION = "MiniLab RNG Engine v0.1.0"
METHODOLOGY_VERSION = "MiniLab-RNG-Methodology-v0.1"

PASS_THRESHOLD = 0.05
BORDERLINE_LOWER = 0.01

LABEL_PASS = "PASS"
LABEL_BORDERLINE = "BORDERLINE"
LABEL_FAIL = "FAIL"
LABEL_NOT_RUN = "NOT_RUN"
LABEL_INDICATIVE_ONLY = "INDICATIVE_ONLY"
LABEL_INCONCLUSIVE = "INCONCLUSIVE"


def classify_p_value(p_value, bits_available=None, bits_required=None):
    if bits_available is not None and bits_required is not None:
        if bits_available < bits_required:
            return LABEL_INDICATIVE_ONLY
    if p_value is None:
        return LABEL_INCONCLUSIVE
    if p_value >= PASS_THRESHOLD:
        return LABEL_PASS
    if p_value >= BORDERLINE_LOWER:
        return LABEL_BORDERLINE
    return LABEL_FAIL


LEGEND = [
    {"label": LABEL_PASS, "range": "p >= 0.05",
     "description": "No statistical evidence of a defect at the chosen significance level."},
    {"label": LABEL_BORDERLINE, "range": "0.01 <= p < 0.05",
     "description": "Statistically unusual but not failing. Expected to occur occasionally even on a sound RNG, especially on smaller samples. A re-run with a larger sample is recommended."},
    {"label": LABEL_FAIL, "range": "p < 0.01",
     "description": "Statistically significant evidence of a defect at alpha = 0.01."},
    {"label": LABEL_NOT_RUN, "range": "N/A",
     "description": "The test was not executed. Reason stated alongside."},
    {"label": LABEL_INDICATIVE_ONLY, "range": "N/A",
     "description": "The sample size is below the recommended minimum for this test. Result is shown but does not count toward the overall verdict."},
    {"label": LABEL_INCONCLUSIVE, "range": "N/A",
     "description": "The test ran but the result is not interpretable. Reason stated alongside."},
]

SCOPE_LIMITATION = {
    "title": "What this report does not test",
    "preamble": "This report is a non-accredited statistical screening of submitted RNG output. It does not, and cannot:",
    "exclusions": [
        "Certify the RNG.",
        "Review RNG source code.",
        "Review the entropy source.",
        "Review seeding or reseeding implementation.",
        "Review the mapping of RNG output into game outcomes.",
        "Test Return To Player (RTP).",
        "Test bonus, free-spin, or feature logic.",
        "Test paytable accuracy.",
        "Replace assessment by an accredited testing laboratory.",
    ]
}

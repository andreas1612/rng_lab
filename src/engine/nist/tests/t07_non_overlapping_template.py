"""NIST SP 800-22 Test 07: Non-overlapping Template Matching."""
from ._wrap import run_upstream

TEST_ID = "NIST-07"
TEST_NAME = 'Non-overlapping Template Matching'
MIN_BITS = 1000000
RECOMMENDED_BITS = 1000000
_UPSTREAM = 'non_overlapping_template_matching_test'


def run(bits):
    return run_upstream(_UPSTREAM, bits, TEST_ID, TEST_NAME, MIN_BITS)

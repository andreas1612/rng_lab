"""NIST SP 800-22 Test 08: Overlapping Template Matching."""
from ._wrap import run_upstream

TEST_ID = "NIST-08"
TEST_NAME = 'Overlapping Template Matching'
MIN_BITS = 1000000
RECOMMENDED_BITS = 1000000
_UPSTREAM = 'overlapping_template_matching_test'


def run(bits):
    return run_upstream(_UPSTREAM, bits, TEST_ID, TEST_NAME, MIN_BITS)

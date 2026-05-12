"""NIST SP 800-22 Test 03: Runs."""
from ._wrap import run_upstream

TEST_ID = "NIST-03"
TEST_NAME = 'Runs'
MIN_BITS = 100
RECOMMENDED_BITS = 1000000
_UPSTREAM = 'runs_test'


def run(bits):
    return run_upstream(_UPSTREAM, bits, TEST_ID, TEST_NAME, MIN_BITS)

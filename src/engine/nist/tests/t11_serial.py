"""NIST SP 800-22 Test 11: Serial."""
from ._wrap import run_upstream

TEST_ID = "NIST-11"
TEST_NAME = 'Serial'
MIN_BITS = 1000000
RECOMMENDED_BITS = 1000000
_UPSTREAM = 'serial_test'


def run(bits):
    return run_upstream(_UPSTREAM, bits, TEST_ID, TEST_NAME, MIN_BITS)

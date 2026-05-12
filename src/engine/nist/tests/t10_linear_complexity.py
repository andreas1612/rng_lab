"""NIST SP 800-22 Test 10: Linear Complexity."""
from ._wrap import run_upstream

TEST_ID = "NIST-10"
TEST_NAME = 'Linear Complexity'
MIN_BITS = 1000000
RECOMMENDED_BITS = 1000000
_UPSTREAM = 'linear_complexity_test'


def run(bits):
    return run_upstream(_UPSTREAM, bits, TEST_ID, TEST_NAME, MIN_BITS)

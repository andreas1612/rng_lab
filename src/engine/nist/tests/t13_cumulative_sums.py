"""NIST SP 800-22 Test 13: Cumulative Sums (Cusum)."""
from ._wrap import run_upstream

TEST_ID = "NIST-13"
TEST_NAME = 'Cumulative Sums (Cusum)'
MIN_BITS = 100
RECOMMENDED_BITS = 1000000
_UPSTREAM = 'cumulative_sums_test'


def run(bits):
    return run_upstream(_UPSTREAM, bits, TEST_ID, TEST_NAME, MIN_BITS)

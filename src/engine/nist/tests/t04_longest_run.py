"""NIST SP 800-22 Test 04: Longest Run of Ones."""
from ._wrap import run_upstream

TEST_ID = "NIST-04"
TEST_NAME = 'Longest Run of Ones'
MIN_BITS = 128
RECOMMENDED_BITS = 1000000
_UPSTREAM = 'longest_run_ones_in_a_block_test'


def run(bits):
    return run_upstream(_UPSTREAM, bits, TEST_ID, TEST_NAME, MIN_BITS)

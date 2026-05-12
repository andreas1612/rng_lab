"""NIST SP 800-22 Test 05: Binary Matrix Rank."""
from ._wrap import run_upstream

TEST_ID = "NIST-05"
TEST_NAME = 'Binary Matrix Rank'
MIN_BITS = 38912
RECOMMENDED_BITS = 1000000
_UPSTREAM = 'binary_matrix_rank_test'


def run(bits):
    return run_upstream(_UPSTREAM, bits, TEST_ID, TEST_NAME, MIN_BITS)

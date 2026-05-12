"""NIST SP 800-22 Test 02: Block Frequency."""
from ._wrap import run_upstream

TEST_ID = "NIST-02"
TEST_NAME = 'Block Frequency'
MIN_BITS = 100
RECOMMENDED_BITS = 1000000
_UPSTREAM = 'frequency_within_block_test'


def run(bits):
    return run_upstream(_UPSTREAM, bits, TEST_ID, TEST_NAME, MIN_BITS)

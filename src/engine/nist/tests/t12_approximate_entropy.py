"""NIST SP 800-22 Test 12: Approximate Entropy."""
from ._wrap import run_upstream

TEST_ID = "NIST-12"
TEST_NAME = 'Approximate Entropy'
MIN_BITS = 1000000
RECOMMENDED_BITS = 1000000
_UPSTREAM = 'approximate_entropy_test'


def run(bits):
    return run_upstream(_UPSTREAM, bits, TEST_ID, TEST_NAME, MIN_BITS)

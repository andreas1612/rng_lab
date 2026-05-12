"""NIST SP 800-22 Test 01: Frequency (Monobit)."""
from ._wrap import run_upstream

TEST_ID = "NIST-01"
TEST_NAME = 'Frequency (Monobit)'
MIN_BITS = 100
RECOMMENDED_BITS = 1000000
_UPSTREAM = 'monobit_test'


def run(bits):
    return run_upstream(_UPSTREAM, bits, TEST_ID, TEST_NAME, MIN_BITS)

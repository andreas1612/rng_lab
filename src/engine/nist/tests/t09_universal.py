"""NIST SP 800-22 Test 09: Maurer's Universal Statistical."""
from ._wrap import run_upstream

TEST_ID = "NIST-09"
TEST_NAME = "Maurer's Universal Statistical"
MIN_BITS = 387840
RECOMMENDED_BITS = 1000000
_UPSTREAM = 'maurers_universal_test'


def run(bits):
    return run_upstream(_UPSTREAM, bits, TEST_ID, TEST_NAME, MIN_BITS)

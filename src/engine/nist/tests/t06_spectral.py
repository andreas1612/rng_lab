"""NIST SP 800-22 Test 06: Discrete Fourier Transform (Spectral)."""
from ._wrap import run_upstream

TEST_ID = "NIST-06"
TEST_NAME = 'Discrete Fourier Transform (Spectral)'
MIN_BITS = 1000
RECOMMENDED_BITS = 1000000
_UPSTREAM = 'dft_test'


def run(bits):
    return run_upstream(_UPSTREAM, bits, TEST_ID, TEST_NAME, MIN_BITS)

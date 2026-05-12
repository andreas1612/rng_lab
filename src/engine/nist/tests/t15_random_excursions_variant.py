"""NIST SP 800-22 Test 15: Random Excursions Variant."""
from ._wrap import run_upstream

TEST_ID = "NIST-15"
TEST_NAME = 'Random Excursions Variant'
MIN_BITS = 1000000
RECOMMENDED_BITS = 1000000
_UPSTREAM = 'random_excursion_variant_test'


def run(bits):
    return run_upstream(_UPSTREAM, bits, TEST_ID, TEST_NAME, MIN_BITS)

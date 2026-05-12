"""Supplementary test modules — one file per test.

Each test exports TEST_ID, TEST_NAME, MIN_BITS, RECOMMENDED_BITS and run(bits).
For supplementary tests the run() signature accepts the raw bytes object via the
helper convention: run(data: bytes) -> dict.
"""

from . import (
    s01_chi_square_byte,
    s02_serial_correlation,
    s03_autocorrelation,
    s04_runs_above_below_mean,
    s05_overlapping_permutations,
    s06_birthday_spacings,
    s07_minimum_distance_2d,
    s08_bit_independence,
)

ALL_TESTS = [
    s01_chi_square_byte,
    s02_serial_correlation,
    s03_autocorrelation,
    s04_runs_above_below_mean,
    s05_overlapping_permutations,
    s06_birthday_spacings,
    s07_minimum_distance_2d,
    s08_bit_independence,
]

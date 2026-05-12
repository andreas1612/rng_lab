"""NIST SP 800-22 individual test modules.

Each test exports:
- TEST_ID    (e.g. "NIST-01")
- TEST_NAME
- MIN_BITS
- RECOMMENDED_BITS
- run(bits: list) -> dict
"""

from . import (
    t01_frequency,
    t02_block_frequency,
    t03_runs,
    t04_longest_run,
    t05_matrix_rank,
    t06_spectral,
    t07_non_overlapping_template,
    t08_overlapping_template,
    t09_universal,
    t10_linear_complexity,
    t11_serial,
    t12_approximate_entropy,
    t13_cumulative_sums,
    t14_random_excursions,
    t15_random_excursions_variant,
)

ALL_TESTS = [
    t01_frequency,
    t02_block_frequency,
    t03_runs,
    t04_longest_run,
    t05_matrix_rank,
    t06_spectral,
    t07_non_overlapping_template,
    t08_overlapping_template,
    t09_universal,
    t10_linear_complexity,
    t11_serial,
    t12_approximate_entropy,
    t13_cumulative_sums,
    t14_random_excursions,
    t15_random_excursions_variant,
]

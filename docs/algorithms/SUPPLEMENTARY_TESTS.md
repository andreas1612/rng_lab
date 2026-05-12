# Supplementary Tests

Eight tests in `src/engine/supplementary/tests/` complement the NIST suite.
They are not part of NIST SP 800-22 but are consistent with methods used in
extended RNG audits. Results do not change a jurisdiction's verdict — they
are advisory.

---

## SUPP-01 — Chi-Square Byte Distribution
- File: `src/engine/supplementary/tests/s01_chi_square_byte.py`
- Detects: Whether all 256 byte values are equally frequent.
- Implementation: 256-bin histogram, `scipy.stats.chisquare` against the uniform expectation `n / 256`.
- Min data: 256 bytes (about 2 048 bits).
- Notes: Sensitive to global byte bias; the cheapest fast-fail signal in the suite.

## SUPP-02 — Serial Correlation Coefficient
- File: `src/engine/supplementary/tests/s02_serial_correlation.py`
- Detects: Linear dependence between consecutive bytes.
- Implementation: Pearson r via `scipy.stats.pearsonr` on `arr[:-1]` vs `arr[1:]`.
- Min data: 3 bytes.
- Notes: Two-tailed test. Even small absolute correlations are reported as long as the p-value is significant.

## SUPP-03 — Autocorrelation (Lags 1-20)
- File: `src/engine/supplementary/tests/s03_autocorrelation.py`
- Detects: Periodicity at any of the first 20 bit-level lags.
- Implementation: Computes the lag-k autocorrelation on the bit sequence; flags lags whose |ACF| exceeds the 95% CI threshold `2 / sqrt(n)`.
- Min data: 40 bits.
- Notes: Under H0 we expect approximately 1 false-positive lag across 20 tests at 95% CI. **MiniLab therefore PASSes when 0 or 1 lag is flagged, BORDERLINEs at 2-4 flagged lags, and FAILs at 5 or more.** This is the "autocorrelation ≤1 lag threshold" fix retained from earlier sprints.

## SUPP-04 — Runs Above/Below Mean
- File: `src/engine/supplementary/tests/s04_runs_above_below_mean.py`
- Detects: Non-randomness in the sign sequence around the median byte value.
- Implementation: Wald-Wolfowitz two-sample runs z-test.
- Min data: 20 bytes.
- Notes: Returns INCONCLUSIVE if all bytes fall on one side of the median (variance is undefined).

## SUPP-05 — Overlapping Permutations (Rank)
- File: `src/engine/supplementary/tests/s05_overlapping_permutations.py`
- Detects: Bias in the ranking of 5-byte windows. Each window has one of 5! = 120 possible orderings.
- Implementation: Slides a 5-byte window across up to 100 000 positions; chi-square on the 120-bin histogram of ranks.
- Min data: 124 bytes.
- Implementation fix retained: **windows containing duplicate byte values are dropped** before `argsort`. Stable argsort breaks ties deterministically and would otherwise bias certain permutations and invalidate the chi-square.

## SUPP-06 — Birthday Spacings
- File: `src/engine/supplementary/tests/s06_birthday_spacings.py`
- Detects: Clustering of 24-bit values.
- Implementation: Builds m 24-bit values from byte triplets; spacings of the sorted values should be approximately Exponential(mean = N/m) where N = 2^24. KS test against that distribution.
- Min data: 1 536 bytes (512 triplets).

## SUPP-07 — Minimum Distance (2D)
- File: `src/engine/supplementary/tests/s07_minimum_distance_2d.py`
- Detects: Clustering or repulsion of 2D points derived from byte pairs.
- Implementation fix retained: **grid chi-square form rather than true minimum-distance**. 8000 points are mapped to [0,1]^2 from consecutive byte pairs, then assigned to a 10x10 grid; chi-square against `n_points / 100` per cell. The grid form is preferred because true nearest-neighbour minimum distance on a finite square has well-known boundary bias that contaminates the p-value.
- Min data: 16 000 bytes.

## SUPP-08 — Bit Independence (Mutual Information)
- File: `src/engine/supplementary/tests/s08_bit_independence.py`
- Detects: Pairwise dependency among the 8 bit positions inside a byte.
- Implementation: For every (i, j) with i < j, computes the 2x2 mutual information of bit i and bit j over all bytes. Threshold scales with sample size: 0.01 if n >= 10 000, 0.05 otherwise.
- Status rule (this test does not use a p-value): PASS at zero flagged pairs, BORDERLINE at 1-3 flagged pairs, FAIL at 4+.
- Min data: 1 000 bytes.

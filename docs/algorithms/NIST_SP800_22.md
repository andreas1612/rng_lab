# NIST SP 800-22 Test Reference

Per-test reference for the 15 tests implemented in `src/engine/nist/tests/`.
All tests use the upstream `dj-on-github/sp800_22_tests` library and wrap it
with the MiniLab test-module interface.

A FAIL result on any of these tests means p < 0.01 at NIST's standard alpha
and indicates statistically significant departure from random behaviour in the
submitted sample.

---

## NIST-01 — Frequency (Monobit)
- NIST section: 2.1
- File: `src/engine/nist/tests/t01_frequency.py`
- Min bits: 100
- Detects: Whether the proportion of 1s is materially different from 1/2.
- Basis: Sum of {+1, -1} mapped bits; |S_n|/sqrt(n) compared to a normal under H0.
- FAIL means: The sequence is biased toward 0 or 1.

## NIST-02 — Block Frequency
- NIST section: 2.2
- File: `src/engine/nist/tests/t02_block_frequency.py`
- Min bits: 100
- Detects: Local bias inside fixed-size blocks that monobit might miss when the global bias averages out.
- Basis: Chi-square of per-block 1-proportions vs 0.5.
- FAIL means: Some blocks are too far from 50/50, even if the overall ratio is fine.

## NIST-03 — Runs
- NIST section: 2.3
- File: `src/engine/nist/tests/t03_runs.py`
- Min bits: 100
- Detects: Whether the sequence oscillates too fast or too slow.
- Basis: Counts the number of runs of identical bits, compares to the expected number under H0.
- FAIL means: The bit sequence flips much more or much less than independent bits would.

## NIST-04 — Longest Run of Ones
- NIST section: 2.4
- File: `src/engine/nist/tests/t04_longest_run.py`
- Min bits: 128
- Detects: An anomalous longest-run-of-1s inside a block, which would point to local clustering.
- Basis: Chi-square on the distribution of the longest run of 1s across blocks.
- FAIL means: Either too-long or too-short maximum runs across blocks.

## NIST-05 — Binary Matrix Rank
- NIST section: 2.5
- File: `src/engine/nist/tests/t05_matrix_rank.py`
- Min bits: 38 912
- Detects: Linear dependence between fixed-length substrings.
- Basis: Builds 32x32 matrices from the bit stream and tests the rank distribution against the expected one under H0.
- FAIL means: Long-range linear structure in the sequence.

## NIST-06 — Discrete Fourier Transform (Spectral)
- NIST section: 2.6
- File: `src/engine/nist/tests/t06_spectral.py`
- Min bits: 1 000
- Detects: Periodic features that would indicate non-randomness.
- Basis: DFT on +/-1 mapped bits; counts how many frequency components exceed a 95% threshold under H0.
- FAIL means: A periodic signal is present.

## NIST-07 — Non-overlapping Template Matching
- NIST section: 2.7
- File: `src/engine/nist/tests/t07_non_overlapping_template.py`
- Min bits: 1 000 000
- Detects: Too-frequent occurrence of a specific aperiodic pattern.
- Basis: Slides a non-overlapping window across the sequence and counts template hits per block.
- FAIL means: One or more aperiodic templates appear far more than expected.

## NIST-08 — Overlapping Template Matching
- NIST section: 2.8
- File: `src/engine/nist/tests/t08_overlapping_template.py`
- Min bits: 1 000 000
- Detects: As 07 but uses an overlapping sliding window, more sensitive to dense pattern repetition.
- Basis: Counts overlapping template hits per block; chi-square vs expected occupancy.
- FAIL means: The pattern of interest is over-clustered.

## NIST-09 — Maurer's Universal Statistical
- NIST section: 2.9
- File: `src/engine/nist/tests/t09_universal.py`
- Min bits: 387 840
- Detects: Compressibility, a proxy for departure from true randomness.
- Basis: Measures the average distance between occurrences of L-bit blocks; deviation from the expected distance is a signal.
- FAIL means: The sequence is significantly compressible.

## NIST-10 — Linear Complexity
- NIST section: 2.10
- File: `src/engine/nist/tests/t10_linear_complexity.py`
- Min bits: 1 000 000
- Detects: Whether short linear feedback shift registers reproduce the sequence.
- Basis: Berlekamp-Massey on per-block segments; chi-square of the resulting LFSR-length distribution.
- FAIL means: The sequence has structure expressible by a short LFSR.

## NIST-11 — Serial
- NIST section: 2.11
- File: `src/engine/nist/tests/t11_serial.py`
- Min bits: 1 000 000
- Detects: Frequency of all 2^m m-bit patterns being out of balance.
- Basis: Chi-square at length m, m-1, m-2 with second differences forming the test statistics.
- FAIL means: Pattern frequencies are non-uniform.

## NIST-12 — Approximate Entropy
- NIST section: 2.12
- File: `src/engine/nist/tests/t12_approximate_entropy.py`
- Min bits: 1 000 000
- Detects: Differences in pattern-frequency complexity between lengths m and m+1.
- Basis: ApEn(m) - ApEn(m+1) compared to chi-square critical values.
- FAIL means: Pattern complexity does not grow with m as expected from random bits.

## NIST-13 — Cumulative Sums (Cusum)
- NIST section: 2.13
- File: `src/engine/nist/tests/t13_cumulative_sums.py`
- Min bits: 100
- Detects: Maximum excursion of the partial sums random walk.
- Basis: Maps bits to +/-1, computes the maximum absolute partial sum.
- FAIL means: The random walk drifts further than chance would allow.

## NIST-14 — Random Excursions
- NIST section: 2.14
- File: `src/engine/nist/tests/t14_random_excursions.py`
- Min bits: 1 000 000
- Detects: The number of visits a +/-1 random walk makes to a given state during a cycle.
- Basis: Eight chi-square statistics, one per state in {-4..-1, 1..4}.
- FAIL means: The walk's state-visit distribution is anomalous in at least one state. MiniLab takes the minimum p across states.

## NIST-15 — Random Excursions Variant
- NIST section: 2.15
- File: `src/engine/nist/tests/t15_random_excursions_variant.py`
- Min bits: 1 000 000
- Detects: Total visits across all states.
- Basis: 18 normal-distributed statistics, one per state in {-9..-1, 1..9}.
- FAIL means: The walk's total occupancy of some state is far from expected. MiniLab takes the minimum p across states.

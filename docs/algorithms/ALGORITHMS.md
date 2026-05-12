# Statistical Test Suites — Reference

## Overview

The following open-source test suites are used by this tool's engine. All are standard in
the iGaming and cryptographic communities. None require a license to use.

---

## 1. NIST SP 800-22 (Primary Suite)

**Full name:** NIST Special Publication 800-22 Rev 1a — A Statistical Test Suite for Random
and Pseudorandom Number Generators for Cryptographic Applications

**Published by:** US National Institute of Standards and Technology (public domain)

**Why it matters:** This is the single most widely referenced test suite in iGaming
regulation. MGA, GLI, and UKGC all explicitly reference NIST SP 800-22 in their
technical standards.

**What it tests:** Whether a binary sequence is indistinguishable from a truly random
sequence. It runs 15 independent tests, each producing a p-value.

**Pass condition:** p-value >= 0.01 (i.e., the sequence is NOT identified as non-random
at the 1% significance level). Some implementations use 0.0001 as a stricter floor.

### The 15 Tests

| # | Test Name | What It Detects |
|---|---|---|
| 1 | Frequency (Monobit) | Imbalance between 0s and 1s in the full sequence |
| 2 | Block Frequency | Imbalance within fixed-length blocks |
| 3 | Runs | Too many or too few alternating runs of 0s and 1s |
| 4 | Longest Run of Ones | Longest run of consecutive 1s in 128-bit blocks |
| 5 | Binary Matrix Rank | Linear dependency among fixed-length substrings |
| 6 | Discrete Fourier Transform (Spectral) | Periodic features in the sequence |
| 7 | Non-overlapping Template Matching | Occurrence count of a specific non-periodic pattern |
| 8 | Overlapping Template Matching | Occurrence count of an overlapping pattern |
| 9 | Maurer's Universal Statistical | Compressibility of the sequence |
| 10 | Linear Complexity | Length of the shortest linear feedback shift register |
| 11 | Serial | Distribution of overlapping m-bit patterns |
| 12 | Approximate Entropy | Regularity/predictability of overlapping patterns |
| 13 | Cumulative Sums (Cusum) | Deviation of cumulative sums from expected random walk |
| 14 | Random Excursions | Number of visits to a state in a random walk |
| 15 | Random Excursions Variant | Total number of state visits across the random walk |

**Minimum input size:** 1,000,000 bits (recommended: 10,000,000 bits for reliable results)

**Python port used:** https://github.com/dj-on-github/sp800_22_tests

---

## 2. Dieharder

**Full name:** Dieharder: A Random Number Test Suite

**Author:** Robert G. Brown (Duke University) — extending original Diehard by George Marsaglia

**License:** GNU General Public License (GPL)

**Platform:** Linux / WSL — no native Windows support

**Why it matters:** One of the oldest and most comprehensive suites. Strong at detecting
correlations and structural weaknesses that NIST tests may miss on certain RNG types.

**What it contains:** 26+ tests including original Diehard battery, NIST tests, and
additional tests from the literature.

**Key tests of interest for iGaming:**
- `diehard_birthdays` — Birthday spacings test
- `diehard_operm5` — Overlapping permutations
- `diehard_runs` — Runs up and down
- `rgb_lagged_sum` — Lagged sum tests for subtle correlations
- `sts_serial` — Serial test (overlap with NIST)

**Pass condition:** p-value between 0.005 and 0.995 (very low or very high p both indicate failure)

**CLI usage:**
```bash
# Test a binary file
dieharder -a -f rng_output.bin

# Test specific test
dieharder -d 0 -f rng_output.bin
```

---

## 3. PractRand

**Full name:** Practically Random (PractRand)

**Author:** Chris Doty-Humphrey

**License:** Public domain

**Platform:** Linux binary and Windows binary available

**Why it matters:** Exceptionally good at catching statistical weaknesses in large samples.
Designed to scale — can test terabytes of RNG output. Preferred for stress testing at
scale.

**What it does:** Runs a battery of tests that grow in strictness as more data is consumed.
Continues until it finds a failure or you stop it.

**Pass condition:** No "FAIL" results at any tested data size. "suspicious" results at small
samples may be acceptable; persistent failures are not.

**CLI usage:**
```bash
# Pipe RNG output into PractRand
cat rng_output.bin | ./RNG_test stdin

# Specify byte count
./RNG_test stdin -tlmax 1GB < rng_output.bin
```

---

## 4. TestU01 (Reference Only — Not in Sprint 1)

**Full name:** TestU01 — A C Library for Empirical Testing of Random Number Generators

**Authors:** Pierre L'Ecuyer and Richard Simard, Université de Montréal

**License:** Open source

**Why it matters:** Academic gold standard. Used in peer-reviewed RNG research. The
"BigCrush" battery is the most demanding public test suite available.

**Batteries:**
- SmallCrush — 10 tests, fast, for quick checks
- Crush — 96 tests, moderate time
- BigCrush — 106 tests, several hours, most thorough

**Note:** Not included in Sprint 1 due to C library complexity. Can be added later if
clients require it. The NIST suite is sufficient for regulatory purposes.

---

## How Tests Are Run in This Tool

1. Client uploads RNG output as a binary file (.bin) or as a CSV of integers
2. Engine converts input to the format each test suite expects
3. Each enabled test suite runs and returns p-values per test
4. Results are passed to the jurisdiction scoring engine (see THRESHOLDS.md)
5. Report is generated with raw p-values + jurisdiction pass/fail matrix + gap analysis

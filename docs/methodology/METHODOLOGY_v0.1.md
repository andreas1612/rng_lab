# MiniLab RNG Engine — Methodology v0.1

Document version: `MiniLab-RNG-Methodology-v0.1`
Tool version: `MiniLab RNG Engine v0.1.0`
Status: stable for the v0.1 release cycle.

---

## 1. Purpose and scope

MiniLab is a **non-accredited statistical screening tool** for the binary output
of a Random Number Generator. Its purpose is to give an operator or an internal
risk-and-compliance team a fast, evidence-bearing readout on whether an RNG's
output is in a defensible state *before* it is submitted to an accredited
testing laboratory.

MiniLab does not certify the RNG. It does not replace an ISO/IEC 17025 audit.
It does not look at source code, the entropy source, seeding, or the mapping of
RNG output into game outcomes. The scope limitation section is reproduced in
every report and is the single source of truth for what MiniLab is and is not.

## 2. What constitutes a run

Every analysis run produces three artefacts, identified by a single Report ID:

1. **Report ID** — `RPT-` followed by 12 hex characters from a v4 UUID. Allocated
   once per run. Appears on every page of the PDF and as the JSON filename.
2. **Evidence JSON** — `<report_id>.json`. Machine-readable record of every
   p-value, statistic, threshold, and AUP field. Intended to be archived
   alongside the PDF for audit trail.
3. **PDF report** — Human-readable presentation of the same data, with legend,
   jurisdiction matrix, gap analysis, scope limitation and disclaimer.

If the AUP record on the run is incomplete, the PDF is watermarked
**DRAFT — INTERNAL USE ONLY** on every page.

## 3. Threshold scheme

A single classification function is used everywhere:

```
p >= 0.05               -> PASS
0.01 <= p < 0.05        -> BORDERLINE
p < 0.01                -> FAIL
p == None               -> INCONCLUSIVE
bits < required         -> INDICATIVE_ONLY
test deliberately skipped -> NOT_RUN
```

`0.05` is the conventional alpha for a "no significant defect" finding. `0.01`
is the NIST SP 800-22 pass/fail threshold. Results between the two are
flagged BORDERLINE rather than collapsed into PASS or FAIL — these are
statistically unusual but expected to occur occasionally on a sound RNG,
especially on smaller samples, and the correct operator response is to re-run
with a larger sample.

See `THRESHOLD_SCHEME.md` for the full rationale.

## 4. Result labels

The legend is rendered into every report. Definitions live in
`core/labels.py::LEGEND` and are duplicated here for reference:

| Label             | Range            | Meaning |
|-------------------|------------------|---------|
| PASS              | p >= 0.05        | No statistical evidence of a defect at the chosen significance level. |
| BORDERLINE        | 0.01 <= p < 0.05 | Statistically unusual but not failing. Expected occasionally on a sound RNG. Re-run with a larger sample. |
| FAIL              | p < 0.01         | Statistically significant evidence of a defect at alpha = 0.01. |
| NOT_RUN           | N/A              | The test was not executed. Reason stated alongside. |
| INDICATIVE_ONLY   | N/A              | Sample below the recommended minimum. Result is shown but does not count toward the overall verdict. |
| INCONCLUSIVE      | N/A              | The test ran but the result is not interpretable. |

## 5. NIST SP 800-22 tests

All 15 tests defined in NIST SP 800-22 Rev 1a are implemented via the
`dj-on-github/sp800_22_tests` upstream library and wrapped per the test-module
spec. Each test is in its own file under `src/engine/nist/tests/`.

| ID       | Name                                          | What it detects                                                                          | NIST Section | Min bits  |
|----------|-----------------------------------------------|------------------------------------------------------------------------------------------|--------------|-----------|
| NIST-01  | Frequency (Monobit)                            | Overall bias toward 0 or 1                                                              | 2.1          | 100       |
| NIST-02  | Block Frequency                                | Local bias inside fixed-size blocks                                                     | 2.2          | 100       |
| NIST-03  | Runs                                           | Total number of runs (oscillation rate)                                                  | 2.3          | 100       |
| NIST-04  | Longest Run of Ones                            | Distribution of the longest run of 1s in a block                                         | 2.4          | 128       |
| NIST-05  | Binary Matrix Rank                             | Linear dependence between fixed-length substrings                                        | 2.5          | 38 912    |
| NIST-06  | Discrete Fourier Transform (Spectral)          | Periodic features that would indicate non-randomness                                     | 2.6          | 1 000     |
| NIST-07  | Non-overlapping Template Matching              | Too-frequent occurrence of a given aperiodic pattern                                     | 2.7          | 1 000 000 |
| NIST-08  | Overlapping Template Matching                  | Like 07 but uses an overlapping sliding window                                           | 2.8          | 1 000 000 |
| NIST-09  | Maurer's Universal Statistical                 | Compressibility (proxy for departure from true randomness)                               | 2.9          | 387 840   |
| NIST-10  | Linear Complexity                              | Length of the shortest LFSR that produces the sequence                                   | 2.10         | 1 000 000 |
| NIST-11  | Serial                                         | Frequency of all 2^m m-bit patterns                                                      | 2.11         | 1 000 000 |
| NIST-12  | Approximate Entropy                            | Comparison of pattern frequencies at lengths m and m+1                                   | 2.12         | 1 000 000 |
| NIST-13  | Cumulative Sums (Cusum)                        | Maximum excursion of the partial sums random walk                                        | 2.13         | 100       |
| NIST-14  | Random Excursions                              | Number of visits a random walk makes to a given state                                    | 2.14         | 1 000 000 |
| NIST-15  | Random Excursions Variant                      | Total visits across all states                                                           | 2.15         | 1 000 000 |

When a test returns multiple p-values (e.g. Random Excursions), the minimum is
taken as the test's p-value, which is the most conservative classification.

## 6. Supplementary tests

Eight additional tests provide coverage beyond NIST SP 800-22. They live in
`src/engine/supplementary/tests/`. Results do not affect the jurisdiction
verdict but are shown alongside the NIST results.

| ID       | Name                                  | What it detects                                                         | Implementation |
|----------|---------------------------------------|-------------------------------------------------------------------------|----------------|
| SUPP-01  | Chi-Square Byte Distribution           | Unequal frequencies among the 256 byte values                           | `scipy.stats.chisquare` on a 256-bin histogram |
| SUPP-02  | Serial Correlation Coefficient         | Linear dependence between consecutive bytes                             | Pearson r via `scipy.stats.pearsonr` |
| SUPP-03  | Autocorrelation (Lags 1-20)            | Periodicity at any of the first 20 bit-level lags                       | Compares each lag's autocorrelation to the 95% CI threshold; flags only when 2+ lags exceed (1 false positive expected) |
| SUPP-04  | Runs Above/Below Mean                  | Non-randomness in the sign sequence around the median byte value        | Wald-Wolfowitz z-test |
| SUPP-05  | Overlapping Permutations (Rank)        | Bias in the ranking of 5-byte windows                                   | Chi-square on all 120 permutations of 5 ranks. Windows with duplicate bytes are dropped — stable argsort would otherwise bias the ranks. |
| SUPP-06  | Birthday Spacings                      | Clustering of 24-bit values                                             | KS test of spacings vs Exponential(N/m) |
| SUPP-07  | Minimum Distance (2D)                  | Clustering or repulsion of 2D points derived from byte pairs            | Chi-square on a 10x10 grid (8000 points). Grid form avoids boundary bias inherent in true nearest-neighbour distances on a finite square. |
| SUPP-08  | Bit Independence (Mutual Information)  | Pairwise dependency among the 8 bit positions inside a byte             | Pairwise mutual information across all 28 bit pairs |

## 7. Multi-sequence Level-2 analysis

When the input is at least `100,000,000` bits (12.5 MB), MiniLab activates the
NIST SP 800-22 §4.2.1 Level-2 analysis on top of the per-test p-values:

- The input is split into 100 independent sequences of at least 1 Mbit each.
- All 15 NIST tests are run on every sequence.
- For each test, two summary checks are computed:
  - **Proportion check** — the fraction of sequences whose p >= 0.01. Pass at
    `>= 96%`, BORDERLINE between 94% and 96%, FAIL below 94%.
  - **Uniformity check** — KS test of the per-sequence p-value distribution
    against Uniform(0,1). KS p `< 0.0001` is FAIL.

The Level-2 block is rendered in its own report section when present.

## 8. Sample size guidance

| Sample size              | What runs                                                                                  |
|--------------------------|--------------------------------------------------------------------------------------------|
| < 100 bits               | Almost nothing — most tests return INDICATIVE_ONLY                                         |
| 100 to 38 911 bits       | Frequency, Block Frequency, Runs, Longest Run, DFT, Cusum                                  |
| 38 912 to 387 839 bits   | Adds Binary Matrix Rank                                                                    |
| 387 840 to 999 999 bits  | Adds Maurer's Universal                                                                    |
| >= 1 000 000 bits        | All 15 NIST tests, single sequence                                                         |
| >= 100 000 000 bits      | All 15 tests with multi-sequence Level-2 (proportion + uniformity)                         |

For a meaningful jurisdiction verdict, an input of at least 1 Mbit is required.
For Level-2 confidence, at least 12.5 MB is recommended.

## 9. Scope limitations

This report does not, and cannot:

- Certify the RNG.
- Review RNG source code.
- Review the entropy source.
- Review seeding or reseeding implementation.
- Review the mapping of RNG output into game outcomes.
- Test Return To Player (RTP).
- Test bonus, free-spin, or feature logic.
- Test paytable accuracy.
- Replace assessment by an accredited testing laboratory.

## 10. Coverage vs accredited audit

See `../audit_comparison/REAL_AUDIT_COVERAGE.md` for the full side-by-side
table. In summary, MiniLab covers roughly the statistical-output portion of an
accredited audit — perhaps a quarter of the work in a real engagement. Source
review, entropy review, ongoing periodic re-testing, paytable correctness, and
the formal opinion from an accredited body are all out of scope and must be
sourced from a proper lab.

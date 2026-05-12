# MiniLab vs Accredited RNG Audit — Coverage Comparison

This document is a candid, side-by-side comparison of what an ISO/IEC 17025
accredited RNG audit covers versus what MiniLab covers. It is written to be
read by an operator considering whether MiniLab is "enough" before submitting
to a real lab. The honest answer is "no, but it's a useful screen."

## Coverage matrix

| Capability                                                | Real Accredited Lab | MiniLab v0.1 | Gap                                       | Path to close                              |
|-----------------------------------------------------------|---------------------|--------------|-------------------------------------------|--------------------------------------------|
| NIST SP 800-22 single-sequence statistical tests          | Yes                 | Yes (15/15)  | None                                      | n/a                                        |
| NIST SP 800-22 Level-2 multi-sequence analysis            | Yes                 | Yes (>= 100M bits) | Sample size dependent                | Submit a larger sample                     |
| Supplementary statistical tests (TestU01-style coverage)  | Yes (extensive)     | Partial (8 tests) | Diehard, BigCrush, PractRand not present | Use TestU01 directly for deeper coverage   |
| Entropy source review                                     | Yes                 | No           | Total                                     | Engage an accredited lab                   |
| Source code review (RNG algorithm, post-processing)       | Yes                 | No           | Total                                     | Engage an accredited lab                   |
| Seeding / reseeding implementation review                 | Yes                 | No           | Total                                     | Engage an accredited lab                   |
| Mapping of RNG output to game outcomes (scaling, rejection sampling, etc.) | Yes | No | Total | Engage an accredited lab |
| Return To Player (RTP) verification                        | Yes                 | No           | Total                                     | Use a math-cert lab or in-house simulation |
| Paytable mathematical correctness                          | Yes                 | No           | Total                                     | Math certification (separate scope)        |
| Bonus / free-spin / feature logic correctness              | Yes                 | No           | Total                                     | Math certification                         |
| ISO/IEC 17025 lab accreditation                            | Yes                 | No           | Total — MiniLab is non-accredited         | Cannot be closed by tooling                |
| Regulator-recognised opinion / certificate                 | Yes                 | No           | Total                                     | Cannot be closed by tooling                |
| Periodic re-test obligations                               | Yes (post-cert)     | No           | Total                                     | Continuing engagement with the lab         |
| Documentation review (design docs, change log)             | Yes                 | No           | Total                                     | Internal control + lab review              |

## Rough coverage estimate

If a full accredited audit is 100% of the deliverable, MiniLab covers roughly
**20 to 25 percent** — the statistical-output portion of the assessment. The
remaining 75-80 percent is review work, source review, math review, and the
formal opinion. Those cannot be replaced by tooling.

## What a clean MiniLab report means

A clean MiniLab report (all NIST tests PASS, jurisdictions PASS, supplementary
tests PASS, on a >= 12.5 MB sample with Level-2 analysis enabled) means:

- The submitted output **looks** random by every statistical test we run.
- A formal lab is unlikely to flag the same output on the equivalent NIST
  tests — though they will run more tests, and on a different sample.

It does **not** mean:

- The underlying RNG will produce a clean sample next time. Statistical tests
  characterise the sample, not the generator.
- The entropy source is adequate.
- The seeding mechanism is sound.
- The game-side mapping introduces no bias.
- The RTP is correct.

## Guidance after a clean report

1. Archive the Report ID, the evidence JSON, and the PDF together.
2. Capture the AUP record at the moment of acceptance.
3. Take a fresh sample of equivalent size on a different day, run again.
   Two clean runs are worth more than one.
4. Engage an accredited lab. Provide the MiniLab artefacts as a courtesy — it
   helps the lab scope their work but it is not part of their evidence base.
5. Treat any change to the RNG, the entropy source, the seeding code, or the
   output post-processing as a trigger to re-run MiniLab and to disclose to
   the lab.

# Jurisdiction Thresholds Reference

## How to Read This Document

Each jurisdiction section defines:
1. The minimum RTP floor (where one exists)
2. The p-value threshold for statistical test pass/fail
3. The confidence interval requirement for empirical RTP
4. Which test suites are referenced or required
5. Which accredited labs are approved (for context — not our concern operationally)

The JSON config files in `src/jurisdictions/` are generated from this document.

---

## Universal Baseline (All Jurisdictions)

**Empirical RTP confidence interval:** Results must fall within the **95% confidence interval**
of the theoretical (declared) RTP. This requirement is consistent across all jurisdictions
researched, even where the minimum RTP floor differs.

**NIST p-value default floor:** 0.01 (1% significance level) is the standard.
A p-value below 0.01 on any NIST test is a statistical failure.
Some labs apply 0.001 as a stricter threshold for certain tests — we flag both.

---

## MGA — Malta Gaming Authority

| Parameter | Value | Source |
|---|---|---|
| Minimum RTP floor | **85%** | MGA Technical Standards |
| Player disclosure | Required — must be visible to player | MGA Compliance Audit Manual |
| Statistical standard | NIST SP 800-22 (explicitly referenced) | MGA Technical Standards |
| Empirical test | 95% CI around theoretical RTP | MGA Compliance Audit Manual |
| NIST p-value threshold | >= 0.01 per test | NIST standard (MGA defers to NIST) |
| Re-test frequency | Periodic (on material change to RNG) | MGA Audit Service Provider Policy |
| Approved labs | GLI, BMM, iTech Labs, eCOGRA, Quinel | MGA Approved Audit Service Provider Policy v5.2 |

**Scoring logic for this tool:**
- FAIL if any NIST test p-value < 0.01
- FAIL if empirical RTP falls outside 95% CI of declared RTP
- FAIL if declared RTP < 85%
- WARNING if p-value is between 0.01 and 0.05 (borderline — flag for re-run with larger sample)

---

## UKGC — UK Gambling Commission

| Parameter | Value | Source |
|---|---|---|
| Minimum RTP floor | **None fixed** | UKGC Remote Technical Standards |
| RTP requirement | Theoretical vs empirical must align | UKGC RTS Section 7 |
| Statistical standard | UKGC RTS references ISO/IEC 17020 methodology | UKGC RTS |
| Empirical test | 95% CI around theoretical RTP | UKGC RTS |
| NIST p-value threshold | >= 0.01 (inferred from NIST references in RTS) | UKGC RTS |
| Lab accreditation | UKAS-accredited or equivalent | UKGC RTS |
| Approved labs | iTech Labs, BMM, GLI, eCOGRA (UKAS-accredited) | UKGC |

**Scoring logic for this tool:**
- FAIL if any NIST test p-value < 0.01
- FAIL if empirical RTP falls outside 95% CI of declared RTP
- NOTE: No minimum RTP floor to check — methodology alignment is the key requirement
- WARNING if p-value is between 0.01 and 0.05

---

## Denmark — Spillemyndigheden

| Parameter | Value | Source |
|---|---|---|
| Minimum RTP floor | Not published as a fixed number | F-2024-0540-EN-01.pdf |
| Statistical standard | ISO/IEC 17020 (inspection body) | F-2024-0540-EN-01.pdf |
| Empirical test | 95% CI around theoretical RTP | Standard practice, inferred |
| NIST p-value threshold | >= 0.01 (NIST is implicit via ISO/IEC 17020) | Standard |
| Lab accreditation | Must be ISO/IEC 17020 accredited | Danish framework |
| Approved labs | Lab must apply for Danish approval | Spillemyndigheden |

**Scoring logic for this tool:**
- FAIL if any NIST test p-value < 0.01
- FAIL if empirical RTP falls outside 95% CI of declared RTP
- NOTE: Emphasis is on lab accreditation process, not a numeric RTP floor
- WARNING if p-value between 0.01 and 0.05

---

## Canada — CGA (Canadian Gaming Association)

| Parameter | Value | Source |
|---|---|---|
| Minimum RTP floor | Per province (e.g. BC: 75%, Ontario: 85%) | CGA Policy Testing Labs.pdf |
| Statistical standard | Per-province, lab policy driven | CGA Policy Testing Labs.pdf |
| Empirical test | 95% CI around theoretical RTP | Standard practice |
| NIST p-value threshold | >= 0.01 | Standard |
| Variation | Each province has its own approved lab list | CGA |

**Scoring logic for this tool (v1 — simplified):**
- Apply 85% as the conservative floor (Ontario standard)
- FAIL if any NIST test p-value < 0.01
- FAIL if empirical RTP falls outside 95% CI
- NOTE: Report should state which province threshold was applied

---

## Summary Matrix

| Jurisdiction | Min RTP | P-value Floor | CI Requirement | Key Standard |
|---|---|---|---|---|
| MGA (Malta) | 85% | 0.01 | 95% | NIST SP 800-22 |
| UKGC (UK) | None fixed | 0.01 | 95% | ISO/IEC 17020 + NIST |
| Denmark | None fixed | 0.01 | 95% | ISO/IEC 17020 |
| Canada (CGA) | 75–85% (province) | 0.01 | 95% | Lab policy driven |

---

## P-Value Interpretation Guide

| P-value | Interpretation | Report Flag |
|---|---|---|
| >= 0.05 | Clearly PASS — strong evidence of randomness | GREEN |
| 0.01 – 0.05 | Borderline — technically pass but recommend re-run with larger sample | AMBER |
| 0.001 – 0.01 | FAIL — statistically significant non-randomness detected | RED |
| < 0.001 | Hard FAIL — strong evidence of non-randomness | RED |

---

## Notes on Sample Size

The reliability of any p-value is directly proportional to sample size.

| Sample Size | Reliability |
|---|---|
| < 1,000,000 bits | NIST tests may not run — insufficient data |
| 1,000,000 bits | Minimum for NIST; results possible but low confidence |
| 10,000,000 bits | Recommended minimum for reliable results |
| 1,000,000,000 bits | PractRand territory — thorough stress test |

The tool should warn users when their input sample is below 10M bits.

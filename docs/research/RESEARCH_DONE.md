# Research Completed

## Summary

All research for Sprint 0 is complete. No further background research is needed to begin
building Sprint 1. This document records what was established and confirmed.

---

## 1. RNG Testing Algorithm Landscape

**Finding:** The core statistical algorithms used by accredited labs are open source and
publicly available. The proprietary value of accredited labs lies in their methodology,
interpretation, tooling, and the ISO/IEC 17025 credential — not the math itself.

### Open Source Test Suites Confirmed

| Suite | Source | Status | Notes |
|---|---|---|---|
| NIST SP 800-22 | US NIST (public domain) | Open | The industry standard. 15 statistical tests. Referenced by MGA, GLI, UKGC explicitly. |
| TestU01 | Université de Montréal | Open source (C) | Academic standard. Crush and BigCrush batteries. Heavy computational requirement. |
| Diehard / Dieharder | George Marsaglia / Robert Brown | Open source | Dieharder is the maintained fork. Strong for initial validation. Linux only. |
| PractRand | Chris Doty-Humphrey | Open source | Excellent for scalable/streaming RNG testing. Windows binary available. |

### What Is NOT Open

- Each lab's internal scoring weights and interpretation methodology
- Their reporting templates and audit evidence packaging
- Their regulatory relationships and accreditation credentials (ISO/IEC 17025)
- Their sample size requirements beyond published minimums

---

## 2. Jurisdiction Research

### MGA (Malta Gaming Authority)
- **Min RTP:** 85% (explicitly stated, must be disclosed to players)
- **RNG requirement:** Must be tested by an MGA-approved test lab
- **Approved labs:** GLI, BMM, iTech Labs, eCOGRA, Quinel (as of research date)
- **Standard referenced:** NIST SP 800-22 is explicitly referenced in MGA technical standards
- **Audit type:** Both initial certification and periodic re-testing required
- **Source docs in this repo:** MGA Compliance Audit Manual, Approved Audit Service Provider Policy

### UKGC (UK Gambling Commission)
- **Min RTP:** Not a fixed floor — requires theoretical vs empirical alignment
- **RNG requirement:** Technical standards reference ISO/IEC 17020 and UKGC RTS (Remote Technical Standards)
- **Key requirement:** Empirical RTP must fall within 95% confidence interval of theoretical RTP
- **Accreditation:** Labs must be UKAS-accredited or equivalent
- **Notable:** UKGC focuses on methodology alignment, not a single RTP number

### Danish Gambling Authority (Spillemyndigheden)
- **Standard referenced:** ISO/IEC 17020 (inspection body accreditation)
- **Approach:** Lab accreditation-driven — the lab's process is what gets approved
- **Source docs in this repo:** F-2024-0540-EN-01.pdf (Danish regulatory framework)

### Canada (CGA — Canadian Gaming Association)
- **Variation:** Per-province — no single federal RNG standard
- **Approach:** Lab policy-driven, each province references its own approved lab list
- **Note:** Lower priority for this tool's first version; add as a later jurisdiction config

---

## 3. Universal RTP Empirical Testing Standard

**Finding confirmed:** Across all jurisdictions researched, the requirement for empirical RTP
testing is that real results must fall within a **95% confidence interval** around the
theoretical RTP. This is consistent even where explicit minimum RTP percentages differ.

This means the tool's confidence interval calculation is jurisdiction-agnostic and applies
universally — only the minimum floor differs.

---

## 4. Service Model Validation

**Finding:** "Pre-audit readiness" as a consulting/tool service is not regulated.
You are not claiming to be an accredited lab. You are providing:

- A technical report based on open-source statistical tests
- A gap analysis against published authority thresholds
- A readiness opinion — not a certification

This is the same category of service as a "mock audit" or "pre-submission review" offered
by legal and compliance consultants in many regulated industries.

**Risk confirmed and mitigated:** Report must clearly disclaim it is not an accredited audit
and does not guarantee regulatory approval. The AUP captures client acknowledgement.

---

## 5. What Remains Unknown (Not Blocking Sprint 1)

- Exact GLI internal scoring weights (not published, not needed — we use published NIST thresholds)
- eCOGRA's specific p-value floor (their published standard references NIST defaults — we use those)
- Whether PractRand binary on Windows behaves identically to Linux build (to be tested in Sprint 1)

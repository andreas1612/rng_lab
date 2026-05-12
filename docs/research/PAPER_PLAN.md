# Academic Paper Plan — MiniLab RNG Engine

**Working title:** *Open-Source Statistical Pre-Audit Verification of iGaming RNG Output:
A Jurisdiction-Aware Framework with Three-Zone Classification*

**Target venue (primary):** MDPI Applied Sciences — Computer Science & Mathematics section
**Target venue (fallback):** IEEE Access
**Estimated length:** 14–20 pages
**Estimated submission readiness:** 6–10 weeks from starting the write-up

---

## Why this paper is publishable

The peer-reviewed literature has NIST SP 800-22 applied to cryptographic and hardware RNG.
It does not have it applied to iGaming regulatory compliance with jurisdiction-specific
scoring, a three-zone label scheme, and a systematic gap analysis against accredited lab
coverage. That gap is your contribution.

Regulators (MGA, UKGC) reference NIST in their technical standards but publish no open
tooling. Accredited labs (GLI, eCOGRA, BMM) do not publish their methods. You are
the first to map the open-source statistical layer onto the regulatory compliance layer
in a reproducible, documented way.

---

## Paper sections — what to cover and expected output per section

### Abstract (200 words)

**Cover:**
- The problem: iGaming operators have no open, reproducible way to assess RNG readiness
  before engaging an accredited lab (cost: €15,000–€50,000 per audit)
- The method: 23-test battery (NIST SP 800-22 × 15 + supplementary × 8), three-zone
  classifier, jurisdiction-aware scoring against MGA/UKGC/DGA/CGA
- Key result: ~45% of accredited audit coverage achievable with open tools; BORDERLINE
  zone identifies marginal RNGs that fail accredited audit despite passing binary threshold
- Availability: open-source, MIT licence, GitHub link

**Expected output:** A self-contained 200-word abstract that a regulatory officer or
a senior developer at an iGaming studio can read and immediately understand the value.

---

### Section 1 — Introduction (1–2 pages)

**Cover:**
- iGaming market size and regulatory fragmentation (MGA, UKGC, DGA, CGA — four different
  frameworks, no harmonised open testing standard)
- Scarcity of approved technical auditors: the MGA maintains approximately 5 licensed
  technical auditors approved to certify RNG systems; the approved framework implementer
  designation is separately controlled and even harder to obtain. This supply constraint
  means audit slots are expensive (€15,000–€50,000), slow to schedule, and have zero
  tolerance for unprepared submissions.
- The pre-audit gap: no open, reproducible tool exists to screen RNG output against
  jurisdiction thresholds before engaging an accredited auditor. Operators currently
  submit blind or pay a consultant to run ad-hoc scripts with no documented methodology.
- Paper scope: strictly pre-audit. The tool produces a readiness report for internal use;
  it does not issue certified opinions, does not replace an accredited audit, and does not
  claim MGA/UKGC approval. This is stated explicitly in every report the tool generates
  and in the Acceptable Use Policy the operator must accept before running an analysis.
- Paper contribution: a reproducible, open pre-audit framework with documented methodology,
  jurisdiction-aware scoring, and a three-zone classifier that quantifies readiness with
  more resolution than binary pass/fail
- Paper structure overview

**Expected output:** Establishes the business and regulatory motivation clearly, states
the scope boundary explicitly (pre-audit only), and positions the contribution correctly
relative to the accredited audit ecosystem.

---

### Section 2 — Background (2–3 pages)

**Cover:**

**2.1 NIST SP 800-22**
- Origins: NIST Special Publication 800-22 Rev. 1a (2010)
- The 15 tests and what each detects (table: test name, null hypothesis, statistic type)
- Known limitations: binary pass/fail at α = 0.01; no jurisdiction mapping; no combined verdict
- Existing implementations: dj-on-github Python port (used in this work), NIST reference C

**2.2 What accredited labs actually test**
- NIST SP 800-22 as baseline (all four jurisdictions reference it)
- Additional batteries: Dieharder (~114 tests), TestU01 BigCrush (106 tests), PractRand
- Non-statistical components: entropy source review, seeding documentation, source code review, RTP verification
- Table: MiniLab vs GLI/eCOGRA/BMM coverage (reproduce from REAL_AUDIT_COVERAGE.md)

**2.3 Related work**
- Statistical RNG testing in cryptography (Marsaglia, L'Ecuyer, Rukhin et al.)
- iGaming-specific literature (sparse — this is part of your contribution claim)
- Open-source RNG testing tools (TestU01, PractRand, ent) — none jurisdiction-aware

**Expected output:** Positions the paper precisely. Reviewers will see you know the
field and understand where you sit relative to prior work.

---

### Section 3 — Methodology (3–4 pages)

This is the core technical contribution. Be precise.

**3.1 Three-zone classification scheme**

Define formally:

```
Label(p) =
  PASS             if p >= α₁  (α₁ = 0.05)
  BORDERLINE       if α₂ <= p < α₁  (α₂ = 0.01)
  FAIL             if p < α₂
  INDICATIVE_ONLY  if n < n_min for this test
  INCONCLUSIVE     if test raised an exception or result is uninterpretable
  NOT_RUN          if test was skipped
```

Justify α₁ = 0.05 and α₂ = 0.01:
- α₁ = 0.05: conventional significance threshold; p < 0.05 triggers concern but not rejection
- α₂ = 0.01: NIST SP 800-22 recommended threshold for hard failure
- BORDERLINE zone captures RNGs that pass accredited binary threshold but are marginal —
  a re-run with a larger sample would resolve ambiguity
- Cite: Rukhin et al. (NIST SP 800-22), plus any academic justification for two-threshold scheme

**3.2 The 23-test battery**

Table: all 23 tests with TEST_ID, name, null hypothesis, minimum bits, recommended bits, label.
Group as: NIST SP 800-22 (15) and Extended Statistical Tests (8).

For the 8 supplementary tests, document the implementation decisions that are your own
contribution (not in any prior paper):
- Autocorrelation: 20 lags at 95% CI → tolerate ≤1 exceedance as expected false positive
- Overlapping Permutations: tie-filter to remove windows with duplicate bytes (prevents
  systematic chi-square bias from numpy stable argsort)
- Minimum Distance 2D: grid chi-square form (not Exp(πn) nearest-neighbour model) —
  boundary-safe on [0,1]² domain

**3.3 Level-2 multi-sequence analysis**

Formal definition:
- Split N bits into k sequences of ≥1M bits each (k ≤ 100)
- Run all 15 NIST tests on each sequence
- For each test: proportion passing = (# sequences with p ≥ α₂) / k
- Proportion verdict: PASS if proportion ≥ 0.96, BORDERLINE if ≥ 0.94, FAIL if < 0.94
  (cite NIST SP 800-22 §4.2.1 for 0.96 threshold)
- Uniformity verdict: KS test of {p₁, ..., pₖ} vs Uniform(0,1); FAIL if KS-p < 0.0001

**3.4 Jurisdiction-aware scoring**

Table of thresholds per jurisdiction (MGA / UKGC / DGA / CGA):
- NIST pass requirement (minimum proportion of tests passing)
- RTP floor (where applicable)
- Accreditation standard (ISO/IEC 17025 for UKGC; ISO/IEC 17020 for DGA)
- Scoring rule: jurisdiction verdict = BORDERLINE if any test BORDERLINE, FAIL if any FAIL

**Expected output:** A methodology section precise enough that another researcher could
re-implement the tool from this section alone. That is the reproducibility test.

---

### Section 4 — Mathematical Analysis (2–3 pages)

This is what separates the paper from a tool writeup. It is the section most likely to
determine acceptance or rejection.

**4.1 Statistical power of the combined battery**

For each test, define:
- H₀: sequence is drawn from Uniform(0,1) (or the specific null for that test)
- H₁: sequence deviates by parameter δ from H₀
- Power = P(reject H₀ | H₁ true) as a function of n (bits) and δ (effect size)

Derive or cite the power function for key tests:
- Frequency (Monobit): power against bias p ≠ 0.5 — closed-form via normal approximation
- Runs: power against serial correlation — cite Swed & Eisenhart tables or normal approx
- Random Excursions: power requires simulation — run 10,000 Monte Carlo trials at n = 1.6M, 10M, 100M bits

Plot: Power curves for the 5 most sensitive tests at sample sizes 1M, 10M, 100M, 1B bits.
This directly motivates the 12.5 MB (100M bit) recommendation.

**4.2 Type I error rate of the combined battery**

With 23 independent tests at α = 0.05, the expected false positive rate under H₀:
- P(at least one FAIL) = 1 - (1 - 0.05)²³ ≈ 0.69 if tests were independent
- In practice, tests are correlated; empirical false positive rate at n = 1.6M vs 100M bits
- BORDERLINE zone absorbs most false positives — a sound RNG on 1.6M bits expects 1–2 BORDERLINE results (show empirically with 1,000 os.urandom trials)

**4.3 Detection sensitivity: BORDERLINE vs binary threshold**

Key claim: the BORDERLINE zone catches marginal RNGs that a binary α = 0.01 threshold misses.
- Simulate 1,000 runs of a mildly biased RNG (p(1) = 0.502 instead of 0.5) at n = 1.6M bits
- Show that binary threshold (α = 0.01) gives ~5% detection rate; BORDERLINE zone (α = 0.05) gives ~40% detection rate
- This is the primary empirical justification for the three-zone scheme

**Expected output:** 2–3 pages of equations, 2–3 figures (power curves, false-positive
distribution, detection-rate comparison). This is the section that makes reviewers
recommend acceptance.

---

### Section 5 — Implementation (1–2 pages)

Brief — reviewers at an engineering venue want to know it was done properly, not every line.

**Cover:**
- Architecture: FastAPI backend, React/TypeScript UI, one-file-per-test module structure
- Parallelisation: ThreadPoolExecutor(max_workers=15); thread-safe stdout suppression via
  thread-local proxy (reason: numpy releases GIL during computation; threading gives real speedup)
- Result caching: SHA-256-keyed in-memory cache, TTL 10 min (motivate: /report would
  otherwise re-run the full battery)
- Benchmarks: sequential 142s → parallel 67s cold → 0.3s warm cache (200KB input)
- Report output: ReportLab PDF with Report ID, SHA-256, AUP 5-field record, DRAFT watermark

**Expected output:** One concise section that shows engineering judgement without becoming
a code walkthrough.

---

### Section 6 — Evaluation (1–2 pages)

**6.1 Bad RNG detection**
- Input: 00/FF alternating pattern (maximally non-random)
- Result: 12–13/15 NIST FAIL, all supplementary FAIL, all jurisdictions FAIL
- Note: Frequency (Monobit) and Cumulative Sums PASS — explain why (globally balanced bits)
- Note: Non-overlapping Template result varies (random template draw) — explain this is correct behaviour

**6.2 Good RNG characterisation**
- Input: os.urandom at 200KB (1.6M bits), 1.25MB (10M bits)
- Result at 1.6M bits: 13/15 NIST PASS, 2 BORDERLINE (Random Excursions family) — expected at this sample size
- Result at 10M bits: expect 15/15 PASS (run this and record result before submission)
- Conclusion: BORDERLINE at small n resolves to PASS at recommended n — as designed

**6.3 False positive rate on sound RNG**
- Run 100 independent os.urandom 200KB samples through the battery
- Record: mean BORDERLINE count per run, variance, P(any FAIL)
- Expected: ~1–2 BORDERLINE per run, near-zero FAIL rate

**Expected output:** Empirical evidence that the tool correctly classifies both extremes
and does not over-flag sound RNG. Provides the false-positive data that Section 4.2 cites.

---

### Section 7 — Gap Analysis (1 page)

Reproduce and extend the table from `docs/audit_comparison/REAL_AUDIT_COVERAGE.md`.

| Capability | Accredited Lab | MiniLab | Gap / Notes |
|---|---|---|---|
| NIST SP 800-22 (15 tests) | ✓ | ✓ | None |
| Level-2 multi-sequence | ✓ | ✓ (≥12.5 MB) | Sample size only |
| Supplementary tests (8) | Partial | ✓ | Lab tests more |
| Jurisdiction scoring | ✓ | ✓ (4 JDs) | Not certified |
| Dieharder (~114 tests) | ✓ | ✗ | Needs Docker/Linux |
| TestU01 BigCrush (106 tests) | ✓ | ✗ | Not implemented |
| RTP verification | ✓ | ✗ | Sprint 6 |
| Entropy source review | ✓ | ✗ | Hardware — out of scope |
| Source code review | ✓ | ✗ | Out of scope by design |
| Accredited certificate | ✓ | ✗ | By design |
| **Estimated coverage** | **100%** | **~45%** | |

Discuss: the 45% is a lower bound on the statistical layer; the remaining 55% is either
hardware-level, document-review, or legally-regulated certification — none of which can
be automated without accreditation.

**Expected output:** One table + half a page of discussion. The most cited figure from
the paper will be the 45% coverage number.

---

### Section 8 — Conclusion and Future Work (0.5–1 page)

**Conclusion:**
- Open-source tooling can cover ~45% of an accredited RNG audit
- The BORDERLINE zone demonstrably increases detection of marginal RNGs vs binary threshold
- The framework is jurisdiction-aware and reproducible — a first in the open literature

**Future work:**
- RTP Level 1 (declaration validation) and Level 2 (empirical simulation)
- Dieharder integration (Docker-based)
- TestU01 BigCrush (Python binding or subprocess wrapper)
- Expanding to additional jurisdictions (AGCO, ARJEL, GamblingCare NZ)
- Longitudinal study: do pre-audit BORDERLINE results predict accredited audit outcomes?

---

## What you can expect as an individual

### The market context that makes this valuable

The MGA maintains approximately 5 licensed technical auditors approved to certify RNG
systems for Maltese licence holders. The "approved framework implementer" designation is
separate and even harder to obtain. These are not paths available to an individual without
a multi-year organisational accreditation process.

**This tool does not approach that space and must not claim to.**

What this creates instead is a different and realistic opportunity: the gap between the
operator (who has an RNG to certify) and one of those 5 auditors (who is expensive,
booked out, and has no tolerance for an unprepared submission) is entirely unserved.
No operator wants to pay €15,000–€50,000 for an audit that fails on something a
statistical screen would have caught in 90 seconds. That gap is your market.

### Correct positioning — what this paper and tool claim

| Claim | Status |
|---|---|
| Open-source statistical pre-audit screening tool | ✓ Accurate and defensible |
| Jurisdiction-aware scoring against MGA/UKGC/DGA/CGA thresholds | ✓ Accurate — based on published standards |
| ~45% coverage of the statistical layer of an accredited audit | ✓ Conservative and documented |
| Pre-audit readiness report for internal use only | ✓ Explicit in every report and the AUP |
| Substitute for accredited audit | ✗ Never claimed, explicitly disclaimed |
| MGA-approved testing | ✗ Not claimed anywhere |
| Pathway to becoming a licensed auditor | ✗ Not the goal, not realistic |

### Career outcomes (realistic timeline)

| Outcome | Timeline | Notes |
|---|---|---|
| Peer-reviewed publication credit | 3–6 months | MDPI Applied Sciences typical review: 4–6 weeks |
| Speaking at iGaming compliance track (ICE, SBC, G2E) | 6–18 months | Conference CFPs actively seek "tools + methodology" speakers |
| Consulting to operators preparing for MGA/UKGC audit | 6–24 months | Your deliverable: a readiness report + remediation advice; their alternative: guess and pay for a failed audit |
| Tool licensing or white-labelling to a compliance consultancy | 12–36 months | Consultancies want this — they currently do this manually |
| Recognised subject-matter expert in pre-audit statistical testing | 12–24 months | A narrow niche; the paper + GitHub + one conference talk is enough |

### What this does NOT lead to (be clear-eyed)

- **Not a path to becoming an MGA-licensed auditor.** That requires organisational
  accreditation (ISO/IEC 17025), a formal application to the MGA, and years of
  audit history under an approved lab. It is an institutional process, not an individual
  credential obtained by publishing a paper.
- **Not a replacement for the 5 licensed auditors.** The tool explicitly disclaim this
  in every report it generates. Operators who use it still need a licensed auditor for
  their formal submission.
- **Not immediate revenue.** The paper opens doors; the consulting and licensing that
  follows generates revenue.

### The strongest realistic version of the outcome

You become the named author of the only peer-reviewed, open-source pre-audit RNG screening
framework aligned to MGA/UKGC/DGA/CGA thresholds. Operators and compliance teams who
Google "RNG pre-audit tool" or "NIST iGaming compliance" find your paper and your GitHub.

That is a defensible, specific niche. The accredited auditors (all 5 of them) cannot
serve it — they are not in the business of pre-audit consulting, they are in the business
of issuing certified opinions. You are in the business of helping operators arrive
prepared. Those are complementary, not competing, roles.

---

## Before you write: three things to do first

1. **Run the power analysis simulations** (Section 4) — this is the only section you
   cannot write from existing work. Budget one focused session of 3–4 hours.

2. **Run the false-positive evaluation** (Section 6.3) — 100 × os.urandom 200KB samples,
   record BORDERLINE/FAIL counts. One script, ~2 hours of compute on the current backend
   (or ~20 minutes after you add the batch endpoint).

3. **Check the related work gap** — do a Scopus/Google Scholar search for
   "NIST SP 800-22 iGaming" and "RNG compliance gambling". If results are sparse
   (they will be), that is your contribution claim confirmed. Screenshot the search
   results and save them — reviewers will ask.

# Threshold Scheme

This document explains the two thresholds MiniLab uses to classify a p-value,
why they are set where they are, and how they interact with per-jurisdiction
rules.

## The thresholds

```
PASS_THRESHOLD   = 0.05
BORDERLINE_LOWER = 0.01
```

Both constants live in `src/engine/core/labels.py` and are the only place these
numbers exist. Every classifier goes through `classify_p_value()`.

## Why 0.05

`0.05` is the long-standing convention for "no significant defect" in applied
statistics. It is the alpha level a default reader expects. p >= 0.05 is the
PASS region.

## Why 0.01

NIST SP 800-22 sets `alpha = 0.01` as its formal pass/fail threshold for each
test. p < 0.01 is the FAIL region.

## The BORDERLINE band

Values in `[0.01, 0.05)` are not collapsed into PASS (which would understate
risk) or FAIL (which would overstate it). They are BORDERLINE.

Three things are true at once in this band:

1. The result is statistically unusual at alpha = 0.05.
2. The result is *not* failing at NIST's alpha = 0.01.
3. On a sound RNG that runs many tests on a small sample, a small number of
   BORDERLINE outcomes is expected by chance.

The operator response to a BORDERLINE result is **re-run on a larger sample**.
A clean run on a larger sample resolves the result. A persistent BORDERLINE
across re-runs is a signal to investigate.

## Per-test application

Every test in `nist/tests/` and `supplementary/tests/` calls
`classify_p_value(p)` to assign its status. There is no per-test threshold
override and no jurisdiction-specific override of these bands. The thresholds
are universal in the v0.1 methodology.

## Per-jurisdiction application

Jurisdiction scoring lives in `scoring.py`. A jurisdiction's overall verdict
collapses the per-test labels:

- Any FAIL test → jurisdiction FAIL.
- No FAIL, any BORDERLINE → jurisdiction BORDERLINE.
- All tests PASS and at least one ran → jurisdiction PASS.
- Otherwise → jurisdiction INCOMPLETE.

INDICATIVE_ONLY and INCONCLUSIVE tests do not count toward the overall verdict
but are listed.

## What BORDERLINE means for client action

| Audience                     | Action |
|------------------------------|--------|
| Internal compliance team     | Re-run on a larger sample (10 Mbit or more recommended). Track whether the same test borderlines on every run; that points to a real defect. |
| RNG engineering              | Treat as a heads-up, not a defect report. Check the seeding mechanism, the entropy source, and any post-processing for any change that correlates with the borderlining test. |
| Pre-audit decision           | Do not submit for accredited audit until BORDERLINE results clear on a larger sample. |

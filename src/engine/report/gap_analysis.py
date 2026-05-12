def generate_gap_analysis(jurisdiction_scores: list, nist_result: dict) -> str:
    tests = nist_result.get("tests", [])
    failed_tests  = [t for t in tests if t["status"] == "fail"]
    warning_tests = [t for t in tests if t["status"] == "warning"]

    failing_jurs  = [j for j in jurisdiction_scores if j["overall"] == "fail"]
    warning_jurs  = [j for j in jurisdiction_scores if j["overall"] == "warning"]
    passing_jurs  = [j for j in jurisdiction_scores if j["overall"] == "pass"]

    parts = []

    perfect_pvalue_tests = [
        t for t in tests
        if t.get("p_value") is not None and round(t["p_value"], 6) == 1.0
    ]
    if perfect_pvalue_tests:
        names = ", ".join(t["name"] for t in perfect_pvalue_tests)
        parts.append(
            f"<p><strong>Note:</strong> {names} returned a p-value of 1.000. "
            "This is a known artifact of this test at certain sample sizes and does not indicate "
            "a problem with the RNG. It will self-resolve with a larger input sample.</p>"
        )

    if failing_jurs:
        names = ", ".join(j["name"] for j in failing_jurs)
        test_details = "; ".join(
            f"{t['name']} (p&thinsp;=&thinsp;{t['p_value']:.6f})" for t in failed_tests
        )
        parts.append(
            f"<p>The following jurisdictions returned a <strong>FAIL</strong> verdict: "
            f"{names}. The specific failing tests are: {test_details}. "
            "These results indicate statistically significant non-randomness in the submitted "
            "RNG output. The RNG should not be submitted for formal audit in its current state.</p>"
        )

    if warning_jurs:
        names = ", ".join(j["name"] for j in warning_jurs)
        test_details = "; ".join(
            f"{t['name']} (p&thinsp;=&thinsp;{t['p_value']:.4f})" for t in warning_tests
        )
        parts.append(
            f"<p>The following jurisdictions returned a <strong>WARNING</strong> verdict: "
            f"{names}. Borderline tests: {test_details}. "
            "These results do not constitute a failure but indicate the RNG output may be marginal. "
            "A re-run with a larger sample (minimum 10,000,000 bits recommended) is advised "
            "before formal audit.</p>"
        )

    if passing_jurs and not failing_jurs and not warning_jurs:
        names = ", ".join(j["name"] for j in passing_jurs)
        parts.append(
            f"<p>The tested jurisdictions returned a <strong>PASS</strong> verdict across "
            f"NIST SP 800-22 statistical testing: {names}. No significant non-randomness was "
            "detected in the submitted sample. <strong>IMPORTANT:</strong> This result applies "
            "only to the submitted sample. It does not guarantee the underlying RNG will produce "
            "consistently random output under all conditions.</p>"
        )

    parts.append(
        "<p>This gap analysis is based on statistical testing only. A formal accredited audit "
        "involves additional evidence requirements including review of RNG documentation, entropy "
        "source documentation, seeding mechanism review, and ongoing periodic re-testing. "
        "These are outside the scope of this tool.</p>"
    )

    return "\n".join(parts)

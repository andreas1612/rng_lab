import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer,
    Table, TableStyle, PageBreak, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable

# ── Colours matching the HTML template ──────────────────────────────────────
C_PASS_BG    = colors.HexColor("#D4EDDA")
C_PASS_FG    = colors.HexColor("#155724")
C_WARN_BG    = colors.HexColor("#FFF3CD")
C_WARN_FG    = colors.HexColor("#856404")
C_FAIL_BG    = colors.HexColor("#F8D7DA")
C_FAIL_FG    = colors.HexColor("#842029")
C_OTHER_BG   = colors.HexColor("#E9ECEF")
C_OTHER_FG   = colors.HexColor("#6C757D")
C_BORDER     = colors.HexColor("#1a1a1a")
C_LIGHT_GREY = colors.HexColor("#EEEEEE")

DISCLAIMER_TEXT = (
    "<b>IMPORTANT NOTICE — PLEASE READ</b><br/><br/>"
    "This Pre-Audit Readiness Report has been produced by Finalogic using open-source "
    "statistical test suites applied to RNG output data submitted by the client.<br/><br/>"
    "<b>This report is NOT an accredited audit.</b> Finalogic is not an ISO/IEC 17025-accredited "
    "testing laboratory and is not approved by any gambling regulatory authority as an "
    "audit service provider.<br/><br/>"
    "<b>This report does not constitute regulatory compliance evidence</b> and cannot be "
    "submitted to any gambling authority (including but not limited to the Malta Gaming "
    "Authority, UK Gambling Commission, Spillemyndigheden, or any Canadian provincial "
    "regulator) in support of a licence application or renewal.<br/><br/>"
    "<b>A PASS result in this report does not guarantee that the submitted RNG will pass a "
    "formal accredited audit.</b> Accredited audits involve additional evidence, documentation "
    "review, and professional judgment beyond the scope of this tool.<br/><br/>"
    "This report is provided for informational and internal preparedness purposes only. "
    "By accepting this report, the client confirms they have read and agreed to Finalogic's "
    "Acceptable Use Policy (AUP)."
)


def _styles():
    base = getSampleStyleSheet()
    normal = base["Normal"]
    normal.fontName = "Times-Roman"
    normal.fontSize = 10
    normal.leading = 14

    def s(name, **kw):
        return ParagraphStyle(name, parent=normal, **kw)

    return {
        "body":     normal,
        "h1":       s("h1", fontName="Times-Bold", fontSize=16, spaceAfter=4),
        "h2":       s("h2", fontName="Times-Bold", fontSize=13, spaceAfter=4, spaceBefore=10),
        "h3":       s("h3", fontName="Times-Bold", fontSize=11, spaceAfter=3, spaceBefore=6),
        "small":    s("small", fontSize=9, textColor=colors.HexColor("#555555")),
        "caveat":   s("caveat", fontSize=8, textColor=colors.HexColor("#555555"),
                      fontName="Times-Italic"),
        "mono":     s("mono", fontName="Courier", fontSize=9),
        "notice":   s("notice", fontName="Times-Roman", fontSize=10, leading=14,
                      borderPadding=12, borderColor=C_BORDER, borderWidth=1.5,
                      backColor=colors.white),
    }


def _page_num(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawCentredString(A4[0] / 2, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _disclaimer_table(styles) -> Table:
    p = Paragraph(DISCLAIMER_TEXT, styles["notice"])
    t = Table([[p]], colWidths=[170 * mm])
    t.setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 1.5, C_BORDER),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def _badge_colours(status: str):
    if status == "pass":
        return C_PASS_BG, C_PASS_FG
    if status == "warning":
        return C_WARN_BG, C_WARN_FG
    if status == "fail":
        return C_FAIL_BG, C_FAIL_FG
    return C_OTHER_BG, C_OTHER_FG


def _nist_table(tests: list, styles) -> Table:
    header = [
        Paragraph("<b>Test Name</b>", styles["body"]),
        Paragraph("<b>P-Value</b>", styles["body"]),
        Paragraph("<b>Status</b>", styles["body"]),
    ]
    rows = [header]
    row_colours = [("BACKGROUND", (0, 0), (-1, 0), C_LIGHT_GREY)]

    for i, t in enumerate(tests, start=1):
        p = t.get("p_value")
        p_str = f"{p:.6f}" if p is not None else "—"
        status = t["status"].upper()
        bg, fg = _badge_colours(t["status"])

        row_colours.append(("BACKGROUND", (0, i), (-1, i), bg))
        row_colours.append(("TEXTCOLOR",  (0, i), (-1, i), fg))

        rows.append([
            Paragraph(t["name"], styles["body"]),
            Paragraph(p_str, styles["mono"]),
            Paragraph(f"<b>{status}</b>", styles["body"]),
        ])

    tbl = Table(rows, colWidths=[95 * mm, 40 * mm, 35 * mm])
    tbl.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("FONTNAME",     (0, 0), (-1, 0),  "Times-Bold"),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        *row_colours,
    ]))
    return tbl


def _level2_table(level2: dict, styles) -> Table:
    """Table for NIST Level-2 multi-sequence analysis results."""
    header = [
        Paragraph("<b>Test Name</b>", styles["body"]),
        Paragraph("<b>Sequences</b>", styles["body"]),
        Paragraph("<b>Proportion Passing</b>", styles["body"]),
        Paragraph("<b>Proportion</b>", styles["body"]),
        Paragraph("<b>KS p-value</b>", styles["body"]),
        Paragraph("<b>Uniformity</b>", styles["body"]),
    ]
    rows = [header]
    row_colours = [("BACKGROUND", (0, 0), (-1, 0), C_LIGHT_GREY)]

    for i, t in enumerate(level2["per_test"], start=1):
        n_seq = t["n_sequences"]
        n_pass = t["n_passing"]
        prop = t["proportion_passing"]
        prop_str = f"{n_pass}/{n_seq} ({prop:.1%})" if prop is not None else "—"
        ks_p = t["ks_p_value"]
        ks_str = f"{ks_p:.4f}" if ks_p is not None else "—"

        prop_result = t["proportion_result"]
        unif_result = t["uniformity_result"]

        prop_bg, prop_fg = _badge_colours(prop_result)
        unif_bg, unif_fg = _badge_colours(unif_result)

        row_colours += [
            ("BACKGROUND", (3, i), (3, i), prop_bg),
            ("TEXTCOLOR",  (3, i), (3, i), prop_fg),
            ("BACKGROUND", (5, i), (5, i), unif_bg),
            ("TEXTCOLOR",  (5, i), (5, i), unif_fg),
        ]
        rows.append([
            Paragraph(t["name"], styles["small"]),
            Paragraph(str(n_seq), styles["mono"]),
            Paragraph(prop_str, styles["mono"]),
            Paragraph(f"<b>{prop_result.upper()}</b>", styles["small"]),
            Paragraph(ks_str, styles["mono"]),
            Paragraph(f"<b>{unif_result.upper()}</b>", styles["small"]),
        ])

    tbl = Table(rows, colWidths=[52 * mm, 18 * mm, 32 * mm, 20 * mm, 22 * mm, 22 * mm])
    tbl.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("FONTNAME",     (0, 0), (-1, 0),  "Times-Bold"),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        *row_colours,
    ]))
    return tbl


def _supplementary_table(tests: list, styles) -> Table:
    """Table for extended/supplementary statistical test results."""
    header = [
        Paragraph("<b>Test Name</b>", styles["body"]),
        Paragraph("<b>Statistic</b>", styles["body"]),
        Paragraph("<b>P-Value</b>", styles["body"]),
        Paragraph("<b>Status</b>", styles["body"]),
    ]
    rows = [header]
    row_colours = [("BACKGROUND", (0, 0), (-1, 0), C_LIGHT_GREY)]

    for i, t in enumerate(tests, start=1):
        stat = t.get("statistic")
        stat_str = f"{stat:.6f}" if stat is not None else "—"
        p = t.get("p_value")
        p_str = f"{p:.6f}" if p is not None else "—"
        status = t.get("status", "error")
        bg, fg = _badge_colours(status)

        row_colours.append(("BACKGROUND", (0, i), (-1, i), bg))
        row_colours.append(("TEXTCOLOR",  (0, i), (-1, i), fg))

        rows.append([
            Paragraph(t.get("name", "Unknown"), styles["body"]),
            Paragraph(stat_str, styles["mono"]),
            Paragraph(p_str, styles["mono"]),
            Paragraph(f"<b>{status.upper()}</b>", styles["body"]),
        ])

    tbl = Table(rows, colWidths=[80 * mm, 30 * mm, 30 * mm, 30 * mm])
    tbl.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("FONTNAME",     (0, 0), (-1, 0),  "Times-Bold"),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        *row_colours,
    ]))
    return tbl


def _format_bits(n: int) -> str:
    kb = n / 8 / 1024
    return f"{n:,} bits ({kb:.0f} KB)"


def generate_pdf(report_data: dict) -> bytes:
    buf = io.BytesIO()
    styles = _styles()

    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=22 * mm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height, id="main")
    doc.addPageTemplates([
        PageTemplate(id="main", frames=frame, onPage=_page_num)
    ])

    story = []
    nd = report_data
    ni = nd["nist_result"]["sample_info"]
    tests = nd["nist_result"]["tests"]
    scores = nd["jurisdiction_scores"]
    level2 = nd["nist_result"].get("level2")
    supp = nd.get("supplementary_result", {})
    supp_tests = supp.get("tests", []) if supp else []

    # ── PAGE 1: DISCLAIMER ──────────────────────────────────────────────────
    story.append(KeepTogether([_disclaimer_table(styles)]))
    story.append(PageBreak())

    # ── PAGE 2: REPORT HEADER ───────────────────────────────────────────────
    story.append(Paragraph("Finalogic Pre-Audit RNG Readiness Report", styles["h1"]))
    story.append(Paragraph("<i>Pre-Audit Readiness Assessment — Not an Accredited Audit</i>",
                           styles["body"]))
    story.append(Spacer(1, 6 * mm))

    analysis_mode = "Multi-sequence Level-2" if level2 else "Single-sequence"
    meta = [
        ("File submitted",          nd["filename"]),
        ("Generated at",            nd["generated_at"]),
        ("AUP accepted",            nd.get("aup_timestamp") or "Not recorded (pre-AUP session)"),
        ("Sample size",             _format_bits(ni["size_bits"])),
        ("Sufficient for testing",  "Yes" if ni["sufficient"] else "No — see warnings below"),
        ("Analysis mode",           analysis_mode),
    ]
    for label, value in meta:
        story.append(Paragraph(f"<b>{label}:</b> {value}", styles["body"]))

    if ni.get("warnings"):
        story.append(Spacer(1, 3 * mm))
        for w in ni["warnings"]:
            story.append(Paragraph(f"⚠ {w}", styles["small"]))

    story.append(PageBreak())

    # ── PAGE 3: NIST RESULTS ────────────────────────────────────────────────
    story.append(Paragraph("NIST SP 800-22 Results", styles["h2"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BBBBBB")))
    story.append(Spacer(1, 3 * mm))
    story.append(_nist_table(tests, styles))
    story.append(Spacer(1, 4 * mm))

    failed   = [t for t in tests if t["status"] == "fail"]
    warnings = [t for t in tests if t["status"] == "warning"]
    passed   = [t for t in tests if t["status"] == "pass"]

    if failed:
        summary = (f"<b>{len(failed)} of {len(tests)} test(s) FAILED.</b> Failing tests: "
                   + ", ".join(t["name"] for t in failed)
                   + ". These results indicate statistically significant non-randomness "
                     "in the submitted sample.")
    elif warnings:
        wnames = ", ".join(
            f"{t['name']} (p={t['p_value']:.4f})" for t in warnings
        )
        summary = (f"<b>{len(passed)} of {len(tests)} tests passed.</b> "
                   f"{len(warnings)} test(s) borderline: {wnames}. "
                   "A re-run with a larger sample is recommended.")
    else:
        summary = (f"<b>All {len(tests)} tests passed.</b> No statistically significant "
                   "non-randomness was detected in the submitted sample.")

    threshold = tests[0]["threshold_used"] if tests else 0.01
    story.append(Paragraph(summary + f" Threshold applied: p ≥ {threshold}.", styles["body"]))
    story.append(PageBreak())

    # ── LEVEL-2 ANALYSIS (only if multi-sequence ran) ───────────────────────
    if level2:
        story.append(Paragraph("NIST Level-2 Analysis", styles["h2"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BBBBBB")))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            f"<b>Mode:</b> Multi-sequence analysis across <b>{level2['n_sequences']} independent "
            f"sequences</b> of ≥1,000,000 bits each. "
            "Proportion check: ≥96% of sequences must pass per test (NIST SP 800-22 §4.2.1). "
            "Uniformity check: KS test of p-value distribution vs Uniform(0,1) — "
            "failure (KS p &lt; 0.0001) indicates a non-uniform p-value distribution.",
            styles["body"],
        ))
        story.append(Spacer(1, 3 * mm))
        story.append(_level2_table(level2, styles))
        story.append(Spacer(1, 4 * mm))

        n_prop = level2["tests_proportion_pass"]
        n_unif = level2["tests_uniformity_pass"]
        n_total = len(level2["per_test"])
        story.append(Paragraph(
            f"<b>Summary:</b> {n_prop} of {n_total} tests passed proportion check. "
            f"{n_unif} of {n_total} tests passed uniformity check.",
            styles["body"],
        ))
        story.append(PageBreak())

    # ── PAGE 4: JURISDICTION SCORING MATRIX ─────────────────────────────────
    story.append(Paragraph("Jurisdiction Scoring Matrix", styles["h2"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BBBBBB")))

    for jur in scores:
        overall = jur["overall"]
        badge_bg, badge_fg = _badge_colours(overall)

        heading_row = Table(
            [[Paragraph(f"<b>{jur['name']} ({jur['short_name']})</b>", styles["h3"]),
              Paragraph(f"<b>{overall.upper()}</b>", styles["body"])]],
            colWidths=[140 * mm, 30 * mm],
        )
        heading_row.setStyle(TableStyle([
            ("BACKGROUND",   (1, 0), (1, 0), badge_bg),
            ("TEXTCOLOR",    (1, 0), (1, 0), badge_fg),
            ("ALIGN",        (1, 0), (1, 0), "CENTER"),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",   (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
        ]))

        caveat_date = nd["generated_at"][:10]
        caveat = (f"Thresholds applied for {jur['name']} are based on publicly available "
                  f"published standards as of {caveat_date}. Regulatory requirements may change. "
                  "The client is responsible for verifying current requirements.")

        block = [
            heading_row,
            Paragraph(f"<b>NIST check:</b> {jur['nist_check']['detail']}", styles["body"]),
            Paragraph(f"<b>RTP floor:</b> {jur['rtp_floor_check']['detail']}", styles["body"]),
            Paragraph(
                f"<b>Tests:</b> {jur['tests_passed']} passed | "
                f"{jur['tests_warning']} borderline | "
                f"{jur['tests_failed']} failed | "
                f"{jur['tests_not_run']} not run",
                styles["body"],
            ),
            Paragraph(caveat, styles["caveat"]),
            Spacer(1, 4 * mm),
        ]
        story.append(KeepTogether(block))

    story.append(PageBreak())

    # ── EXTENDED STATISTICAL TESTS ──────────────────────────────────────────
    if supp_tests:
        story.append(Paragraph("Extended Statistical Tests", styles["h2"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BBBBBB")))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            "These tests are supplementary. They are not part of the NIST SP 800-22 suite "
            "but are consistent with methods used in extended RNG audits. "
            "Results do not affect jurisdiction scores.",
            styles["caveat"],
        ))
        story.append(Spacer(1, 3 * mm))
        story.append(_supplementary_table(supp_tests, styles))
        story.append(PageBreak())

    # ── GAP ANALYSIS ────────────────────────────────────────────────────────
    story.append(Paragraph("Gap Analysis", styles["h2"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BBBBBB")))
    story.append(Spacer(1, 3 * mm))

    from report.gap_analysis import generate_gap_analysis
    gap_html = generate_gap_analysis(scores, nd["nist_result"])
    for chunk in gap_html.split("</p>"):
        text = chunk.replace("<p>", "").strip()
        if text:
            story.append(Paragraph(text, styles["body"]))
            story.append(Spacer(1, 3 * mm))

    story.append(PageBreak())

    # ── LAST PAGE: FOOTER DISCLAIMER ────────────────────────────────────────
    story.append(Paragraph("Disclaimer", styles["h2"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BBBBBB")))
    story.append(Spacer(1, 4 * mm))
    story.append(KeepTogether([_disclaimer_table(styles)]))
    story.append(Spacer(1, 6 * mm))

    aup_ts  = nd.get("aup_timestamp") or "Not recorded (pre-AUP session)"
    aup_ref = nd.get("aup_ref") or "N/A"
    story.append(Paragraph(
        f"AUP accepted: {aup_ts} — Ref: {aup_ref}", styles["small"]
    ))

    doc.build(story)
    return buf.getvalue()

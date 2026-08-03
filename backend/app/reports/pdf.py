"""Feature 12 — render a report to PDF with ReportLab."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.interview import Interview
from app.models.report import InterviewReport

ACCENT = colors.HexColor("#4f46e5")
MUTED = colors.HexColor("#64748b")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "IPTitle", parent=base["Title"], fontSize=22, spaceAfter=4, textColor=ACCENT
        ),
        "subtitle": ParagraphStyle(
            "IPSubtitle", parent=base["Normal"], fontSize=10, textColor=MUTED, spaceAfter=12
        ),
        "h2": ParagraphStyle(
            "IPH2",
            parent=base["Heading2"],
            fontSize=13,
            spaceBefore=14,
            spaceAfter=6,
            textColor=colors.HexColor("#0f172a"),
        ),
        "body": ParagraphStyle(
            "IPBody", parent=base["Normal"], fontSize=10, leading=15, alignment=TA_LEFT
        ),
    }


def _bullets(items: list[str], style) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(item, style), leftIndent=10) for item in items],
        bulletType="bullet",
        bulletFontSize=7,
        leftIndent=12,
    )


def render_report_pdf(interview: Interview, report: InterviewReport) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=f"InterviewPilot AI report — {interview.role}",
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    s = _styles()
    story = []

    story.append(Paragraph("InterviewPilot AI — Interview Report", s["title"]))
    date = interview.completed_at or interview.created_at
    story.append(
        Paragraph(
            f"{interview.role} &nbsp;•&nbsp; {interview.mode.replace('_', ' ').title()} round "
            f"&nbsp;•&nbsp; {interview.company.title()} style &nbsp;•&nbsp; "
            f"{date:%d %b %Y}",
            s["subtitle"],
        )
    )
    story.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))

    # ---- scores table
    story.append(Paragraph("Scores", s["h2"]))
    rows = [
        ["Overall", "Technical", "Communication", "Confidence", "Grammar", "Clarity"],
        [
            _fmt(report.overall_score),
            _fmt(report.technical_score),
            _fmt(report.communication_score),
            _fmt(report.confidence_score),
            _fmt(report.grammar_score),
            _fmt(report.clarity_score),
        ],
    ]
    table = Table(rows, colWidths=[doc.width / 6.0] * 6)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
                ("TEXTCOLOR", (0, 0), (-1, 0), ACCENT),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 1), (-1, 1), 13),
            ]
        )
    )
    story.append(table)

    if report.readiness_percent is not None:
        story.append(Spacer(1, 10))
        story.append(
            Paragraph(
                f"<b>Readiness:</b> {report.readiness_percent:.0f}% ready for "
                f"<b>{report.readiness_role or interview.role}</b> "
                f"&nbsp;•&nbsp; estimated prep time: {report.estimated_prep_time or 'n/a'}",
                s["body"],
            )
        )

    _section(story, s, "Summary", paragraph=report.summary)
    _section(story, s, "Strengths", items=report.strengths)
    _section(story, s, "Areas to improve", items=report.weaknesses)

    if report.mistakes:
        story.append(Paragraph("Mistakes to correct", s["h2"]))
        for m in report.mistakes:
            story.append(
                Paragraph(
                    f"<b>{m.get('topic', '')}</b> — {m.get('what_went_wrong', '')}<br/>"
                    f"<font color='#16a34a'>Correct:</font> {m.get('correct_answer', '')}",
                    s["body"],
                )
            )
            story.append(Spacer(1, 6))

    if report.recommendations:
        story.append(Paragraph("Recommendations", s["h2"]))
        for r in report.recommendations:
            resources = ", ".join(r.get("resources", []))
            story.append(
                Paragraph(
                    f"<b>{r.get('topic', '')}</b> — {r.get('why', '')}"
                    + (f"<br/><i>{resources}</i>" if resources else ""),
                    s["body"],
                )
            )
            story.append(Spacer(1, 6))

    if report.learning_plan:
        story.append(Paragraph("Learning plan", s["h2"]))
        for step in report.learning_plan:
            tasks = "; ".join(step.get("tasks", []))
            project = step.get("mini_project") or ""
            story.append(
                Paragraph(
                    f"<b>Week {step.get('week', '?')} — {step.get('focus', '')}</b><br/>{tasks}"
                    + (f"<br/><i>Mini project: {project}</i>" if project else ""),
                    s["body"],
                )
            )
            story.append(Spacer(1, 6))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
    story.append(
        Paragraph(
            "<font size=8 color='#94a3b8'>Generated by InterviewPilot AI. "
            "Scores are practice guidance, not a hiring decision.</font>",
            s["body"],
        )
    )

    doc.build(story)
    return buffer.getvalue()


def _section(story, s, heading: str, *, paragraph: str | None = None, items: list | None = None):
    if paragraph:
        story.append(Paragraph(heading, s["h2"]))
        story.append(Paragraph(paragraph, s["body"]))
    elif items:
        story.append(Paragraph(heading, s["h2"]))
        story.append(_bullets([str(i) for i in items], s["body"]))


def _fmt(value: float | None) -> str:
    return "—" if value is None else f"{value:.0f}"

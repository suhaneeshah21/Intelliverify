# backend/app/services/report_service.py
import json
from io import BytesIO
from datetime import datetime
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from app.models.application import Application, Document
from app.models.user import User


def generate_application_report(db: Session, application_id: int) -> bytes:
    """
    Generates a PDF report for a given application.
    Returns the PDF as bytes — caller streams it to the client.
    """

    # --- Fetch data ---
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise ValueError(f"Application {application_id} not found")

    candidate = db.query(User).filter(User.id == application.candidate_id).first()
    documents = db.query(Document).filter(Document.application_id == application_id).all()

    # --- Build PDF in memory ---
    buffer = BytesIO()
    pdf_doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # --- Title ---
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    elements.append(Paragraph("IntelliVerify — Application Report", title_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}", styles["Normal"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    elements.append(Spacer(1, 0.4 * cm))

    # --- Candidate Details ---
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=13, textColor=colors.HexColor("#0f172a"), spaceAfter=4)
    elements.append(Paragraph("Candidate Information", section_style))

    candidate_data = [
        ["Field", "Value"],
        ["Name", candidate.full_name if hasattr(candidate, "full_name") else candidate.email],
        ["Email", candidate.email],
        ["Application ID", str(application.id)],
        ["Submitted At", application.created_at.strftime("%d %b %Y, %H:%M") if application.created_at else "—"],
        ["Application Status", application.status.value.replace("_", " ").title()],
    ]

    candidate_table = Table(candidate_data, colWidths=[5 * cm, 11 * cm])
    candidate_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(candidate_table)
    elements.append(Spacer(1, 0.6 * cm))

    # --- Per-Document Verification Results ---
    elements.append(Paragraph("Document Verification Results", section_style))

    for doc in documents:
        elements.append(Paragraph(
            f"Document: {doc.document_type.replace('_', ' ').title()} — Status: {doc.status.value.replace('_', ' ').title()}",
            styles["Heading3"]
        ))

        # Build extracted vs form fields table
        # verification_result is a JSON column — expected shape:
        # { "fields": [ { "field": "name", "extracted": "...", "form_value": "...", "match": true/false, "confidence": 0.92 } ] }
        field_rows = [["Field", "Extracted Value", "Form Value", "Match", "Confidence"]]

        extracted  = json.loads(doc.extracted_data  or "{}") 
        mismatches = json.loads(doc.mismatch_details or "{}")

        # Build a unified fields list from extracted_data + mismatch_details
        EXTRACT_TO_FORM = {
            "candidate_name": "full_name",
            "gate_score":     "gate_score",
            "gate_rank":      "gate_rank",
            "gate_paper":     "branch",
            "year_of_passing":"graduation_year",
            "roll_number":    None,           # no form equivalent
            "percentage":     "percentage",
            "degree":         "degree",
            "university":     "college",
            "name":           "full_name",
            "branch":         "branch",
            "category":       "category",
        }

        form_data = {
            "full_name":        application.full_name,
            "gate_score":       application.gate_score,
            "gate_rank":        application.gate_rank,
            "branch":           application.branch,
            "graduation_year":  application.graduation_year,
            "percentage":       application.percentage,
            "degree":           application.degree,
            "college":          application.college,
            "category":         application.category,
        }
        fields = []
        for key, extracted_val in extracted.items():
            form_key  = EXTRACT_TO_FORM.get(key)
            form_val  = form_data.get(form_key, "—") if form_key else "—"
            fields.append({
                "field":      key,
                "extracted":  extracted_val,
                "form_value": form_val,
                "match":      key not in mismatches,
                "confidence": doc.confidence_score or 0,
            })


        if fields:
            for f in fields:
                match_str = "✓" if f.get("match") else "✗"
                confidence_str = f"{f.get('confidence', 0) * 100:.1f}%"
                field_rows.append([
                    f.get("field", ""),
                    str(f.get("extracted", "—")),
                    str(f.get("form_value", "—")),
                    match_str,
                    confidence_str,
                ])
        else:
            field_rows.append(["No extraction data available", "", "", "", ""])

        doc_table = Table(field_rows, colWidths=[3.5 * cm, 4.5 * cm, 4.5 * cm, 1.8 * cm, 2.7 * cm])
        doc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f1f5f9"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 5),
            # Color mismatch rows red
            *[
                ("TEXTCOLOR", (3, i + 1), (3, i + 1), colors.red)
                for i, f in enumerate(fields)
                if not f.get("match")
            ],
        ]))
        elements.append(doc_table)
        elements.append(Spacer(1, 0.5 * cm))

    # --- Build PDF ---
    pdf_doc.build(elements)
    buffer.seek(0)
    return buffer.read()
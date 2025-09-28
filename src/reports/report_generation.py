import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

def generate_report(insights_json, output_format="md"):
    """
    Generate Markdown, PDF, or HTML report based on insights JSON.
    """
    title = "# Insights Report\n\n"
    metrics_section = "## Confidence Scores\n\n"
    
    # Correctly handle DataFrame
    if "stats_table" in insights_json and isinstance(insights_json["stats_table"], pd.DataFrame):
        for index, m in insights_json["stats_table"].iterrows():
             metrics_section += f"- **{m['Metric']}**: Mean={m['Mean']:.2f}, CI={m['95% CI']}, p={m['p-Value']}, Effect Size={m['Effect Size']:.3f}\n"
    else:
        metrics_section += "No statistical summary data available.\n"

    rec_section = "\n## Executive Summary\n\n"
    # Correctly handle single-string summary
    if "summary" in insights_json and isinstance(insights_json["summary"], str):
        rec_section += insights_json["summary"] + "\n"
    else:
        rec_section += "No executive summary available.\n"
    
    report_text = title + metrics_section + rec_section

    if output_format == "md":
        return report_text
    elif output_format == "html":
        return f"<html><body>{report_text.replace('\n','<br>')}</body></html>"
    elif output_format == "pdf":
        pdf_path = "insights_report.pdf"
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        story = [Paragraph("Insights Report", styles["Title"]), Spacer(1, 12)]
        
        # Correctly format sections for PDF
        story.append(Paragraph("<b>Confidence Scores</b>", styles["h2"]))
        if "stats_table" in insights_json and isinstance(insights_json["stats_table"], pd.DataFrame):
            data = [insights_json["stats_table"].columns.to_list()] + insights_json["stats_table"].values.tolist()
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86C1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F4F6F6')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#AAB7B8'))
            ]))
            story.append(table)
        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>Executive Summary</b>", styles["h2"]))
        story.append(Paragraph(insights_json.get("summary", "No summary available."), styles["Normal"]))

        doc.build(story)
        return pdf_path
    else:
        raise ValueError("Unsupported format. Use 'md', 'html', or 'pdf'.")
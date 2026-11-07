import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_sample_pdf():
    os.makedirs("./data/sample_documents", exist_ok=True)
    pdf_path = "./data/sample_documents/DocuQuery_Technical_Financial_Report.pdf"

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=12,
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0369a1'),
        spaceBefore=14,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8,
    )

    elements = []

    # Title & Executive Summary
    elements.append(Paragraph("DocuQuery Corporation: Annual Technical & Financial Report 2024", title_style))
    elements.append(Paragraph("<b>Author:</b> Principal AI & Systems Architecture Team | <b>Published:</b> Q4 2024", body_style))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("1. Executive & Financial Summary", h2_style))
    elements.append(Paragraph(
        "DocuQuery Corporation delivered strong operational and financial performance during fiscal year 2024. "
        "Total revenue increased from $100M in 2023 to $115M in 2024, representing an annual revenue growth rate of 15.0%. "
        "Through disciplined infrastructure scaling and local model execution, Operating Expenses decreased by 8.0%, falling from $50M to $46M.",
        body_style
    ))

    # Financial Table
    table_data = [
        ["Financial Metric", "FY 2023", "FY 2024", "Growth / Margin"],
        ["Total Revenue", "$100M", "$115M", "+15.0%"],
        ["Operating Expenses", "$50M", "$46M", "-8.0%"],
        ["Operating Income", "$20M", "$25M", "25.0% Margin"],
        ["EBITDA", "$24M", "$30M", "30.0% Margin"],
    ]
    t = Table(table_data, colWidths=[150, 100, 100, 130])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("2. Applied AI Architecture & Retrieval Mechanisms", h2_style))
    elements.append(Paragraph(
        "DocuQuery Engine implements a state-of-the-art hybrid Graph-RAG architecture. "
        "For dense semantic representation, the platform runs BAAI/bge-small-en-v1.5 locally via FastEmbed on CPU, yielding 384-dimensional dense vectors. "
        "Graph traversal is driven by KùzuDB, an embedded Python property graph database supporting 1-to-2 hop multi-entity traversal. "
        "Dense vector similarity and graph connectivity are combined using Reciprocal Rank Fusion (RRF) with constant k=60. "
        "Candidates are subsequently reranked using FlashRank running ms-marco-TinyBERT-L-2-v2 with sub-10ms latency.",
        body_style
    ))

    # Page 2: Operational Subscriptions & Verification Engine
    elements.append(PageBreak())
    elements.append(Paragraph("3. Deterministic AST Numerical Verification", h2_style))
    elements.append(Paragraph(
        "Unlike conventional LLM chatbots that hallucinate tabular figures, DocuQuery Engine introduces a deterministic Python AST verification layer. "
        "Extracted arithmetic claims (such as growth rates, ratios, and operating margins) are mapped directly to raw Markdown tables ingested from source PDFs. "
        "A restricted Python Abstract Syntax Tree (AST) parser evaluates mathematical formulas and attaches a Verified Calculation badge.",
        body_style
    ))

    elements.append(Paragraph("4. Operational Subscription Growth", h2_style))
    elements.append(Paragraph(
        "User subscriptions rose from 10,000 to 12,000 active enterprise accounts, reflecting an expansion growth rate of 20.0%. "
        "The platform enforces strict PDF upload limits of 20MB per file and provides cascading hard deletion across PostgreSQL, pgvector chunks, and KùzuDB graph tables.",
        body_style
    ))

    sub_table = [
        ["Product Tier", "2023 Accounts", "2024 Accounts", "Growth Rate"],
        ["Enterprise Workspaces", "10,000", "12,000", "+20.0%"],
        ["Research Nodes", "2,500", "3,500", "+40.0%"],
    ]
    st = Table(sub_table, colWidths=[150, 110, 110, 110])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f766e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
    ]))
    elements.append(st)

    doc.build(elements)
    print(f"Sample PDF created successfully at: {pdf_path}")

if __name__ == "__main__":
    generate_sample_pdf()

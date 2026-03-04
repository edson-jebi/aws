#!/usr/bin/env python3
"""
Convert Delice Implementation Guide Markdown to PDF
Uses reportlab to generate a professional-looking PDF document
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor, black, grey
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.platypus import ListFlowable, ListItem
from reportlab.lib import colors
import re
from datetime import datetime

def parse_markdown_to_pdf(input_file, output_file):
    """Parse markdown and convert to PDF"""

    # Create PDF document
    doc = SimpleDocTemplate(
        output_file,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Container for PDF elements
    story = []

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#0066cc'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#0066cc'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )

    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=HexColor('#333333'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=8,
        leading=10,
        fontName='Courier',
        textColor=HexColor('#333333'),
        backColor=HexColor('#f5f5f5'),
        leftIndent=20,
        rightIndent=20,
        spaceAfter=10
    )

    # Read markdown file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Process line by line
    lines = content.split('\n')
    in_code_block = False
    code_block = []
    in_table = False
    table_data = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip horizontal rules
        if line.strip() in ['---', '***', '___']:
            story.append(Spacer(1, 0.2*inch))
            i += 1
            continue

        # Code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                # End code block
                code_text = '\n'.join(code_block)
                # Escape XML characters
                code_text = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                p = Paragraph(f'<font face="Courier" size="8">{code_text}</font>', code_style)
                story.append(p)
                story.append(Spacer(1, 0.1*inch))
                code_block = []
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_block.append(line)
            i += 1
            continue

        # Tables
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                in_table = True
                table_data = []

            # Parse table row
            cells = [cell.strip() for cell in line.split('|')[1:-1]]

            # Skip separator rows
            if all(set(cell.strip()) <= set('-: ') for cell in cells if cell):
                i += 1
                continue

            table_data.append(cells)
            i += 1

            # Check if next line is still table
            if i < len(lines) and '|' not in lines[i]:
                # Create table
                if table_data:
                    t = Table(table_data, hAlign='LEFT')
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 0.2*inch))
                in_table = False
                table_data = []
            continue

        # Headings
        if line.startswith('# ') and not line.startswith('## '):
            text = line[2:].strip()
            if i == 0:  # First line is title
                story.append(Paragraph(text, title_style))
                story.append(Spacer(1, 0.3*inch))
            else:
                story.append(PageBreak())
                story.append(Paragraph(text, heading1_style))
            i += 1
            continue

        if line.startswith('## '):
            text = line[3:].strip()
            story.append(Paragraph(text, heading2_style))
            i += 1
            continue

        if line.startswith('### '):
            text = line[4:].strip()
            story.append(Paragraph(text, heading3_style))
            i += 1
            continue

        # Lists
        if line.strip().startswith(('- ', '* ', '+ ')):
            text = line.strip()[2:]
            # Simple formatting - properly handle bold
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            # Handle inline code
            text = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', text)
            # Escape special characters
            text = text.replace('&', '&amp;')
            text = text.replace('<', '&lt;').replace('>', '&gt;')
            # Re-add HTML tags
            text = text.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
            text = text.replace('&lt;font face="Courier"&gt;', '<font face="Courier">').replace('&lt;/font&gt;', '</font>')
            bullet = '•'
            p = Paragraph(f'{bullet} {text}', body_style)
            story.append(p)
            i += 1
            continue

        if re.match(r'^\d+\.\s', line.strip()):
            # Numbered list
            text = re.sub(r'^\d+\.\s', '', line.strip())
            # Properly handle formatting
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', text)
            # Escape special characters
            text = text.replace('&', '&amp;')
            p = Paragraph(text, body_style)
            story.append(p)
            i += 1
            continue

        # Regular paragraphs
        if line.strip():
            text = line.strip()

            # Skip markdown horizontal rules
            if text in ['---', '***', '___']:
                i += 1
                continue

            # Bold
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

            # Italic
            text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)

            # Inline code
            text = re.sub(r'`(.*?)`', r'<font face="Courier" size="9">\1</font>', text)

            # Links (simple conversion)
            text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<link href="\2" color="blue">\1</link>', text)

            # Escape special characters
            text = text.replace('&', '&amp;')

            # Check for special markers
            if '✅' in text or '⭐' in text or '❌' in text or '⚠️' in text:
                # Keep emoji markers
                pass

            try:
                p = Paragraph(text, body_style)
                story.append(p)
            except Exception as e:
                # If paragraph fails, add as plain text
                print(f"Warning: Could not parse line: {line[:50]}... ({e})")
        else:
            # Empty line - add small spacer
            story.append(Spacer(1, 0.1*inch))

        i += 1

    # Build PDF
    doc.build(story)
    print(f"PDF generated successfully: {output_file}")

if __name__ == '__main__':
    input_file = '/Users/edson/Documents/aws/Delice_Data_Lake_Implementation_Guide.md'
    output_file = '/Users/edson/Documents/aws/Delice_Data_Lake_Implementation_Guide.pdf'

    print("Converting Markdown to PDF...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")

    try:
        parse_markdown_to_pdf(input_file, output_file)
        print("✓ PDF generation complete!")
    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()

"""Exports déterministes d’une version de rapport, sans modification du document."""
from functools import partial
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
import zipfile

INSTITUTION = ['RÉPUBLIQUE DÉMOCRATIQUE DU CONGO', 'MINISTÈRE DES INFRASTRUCTURES ET TRAVAUX PUBLICS', 'CNE-ITP — Coordination du Secrétariat technique']


def institution_lines(version):
    from .st_report_cover import cover_data
    data = cover_data(version)
    organization = data.get('organization', 'CNE-ITP')
    if 'CNE-ITP' in organization.upper():
        return [*INSTITUTION[:2], f"{organization} — {data.get('department', '')}"]
    return [line for line in (organization, data.get('department', '')) if line]


def period_label(version):
    start = version.period_start.strftime('%d/%m/%Y') if version.period_start else 'Non précisé'
    end = version.period_end.strftime('%d/%m/%Y') if version.period_end else 'Non précisé'
    return f'Période : {start} au {end}'


def export_report_pdf(version):
    from .st_report_documents import fixed_pdf
    from .st_report_cover import prepend_cover
    if getattr(version, 'document', {}).get('mode') == 'fixed':
        return prepend_cover(fixed_pdf(version), version)
    import reportlab
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    fonts = Path(reportlab.__file__).parent / 'fonts'
    if 'STReport' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('STReport', str(fonts / 'Vera.ttf')))
        pdfmetrics.registerFont(TTFont('STReportBold', str(fonts / 'VeraBd.ttf')))
        pdfmetrics.registerFont(TTFont('STReportItalic', str(fonts / 'VeraIt.ttf')))
        pdfmetrics.registerFont(TTFont('STReportBoldItalic', str(fonts / 'VeraBI.ttf')))
        pdfmetrics.registerFontFamily('STReport', normal='STReport', bold='STReportBold', italic='STReportItalic', boldItalic='STReportBoldItalic')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='STBody', fontName='STReport', fontSize=10.5, leading=15, spaceAfter=7))
    styles.add(ParagraphStyle(name='STTitle', fontName='STReportBold', fontSize=18, leading=23, spaceBefore=14, spaceAfter=12))
    styles.add(ParagraphStyle(name='STHeading', fontName='STReportBold', fontSize=12, leading=17, spaceBefore=12, spaceAfter=6, keepWithNext=True, textColor=colors.HexColor('#1e3a9a')))
    styles.add(ParagraphStyle(name='STMeta', fontName='STReport', fontSize=8.5, leading=12, textColor=colors.HexColor('#475569'), spaceAfter=3))
    out = BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=22*mm, rightMargin=22*mm,
        topMargin=19*mm, bottomMargin=20*mm, title=version.title, author=version.author_name, invariant=1)
    story = [Paragraph(escape(line), styles['STMeta']) for line in institution_lines(version)]
    story += [Paragraph(escape(version.title), styles['STTitle']),
        Paragraph('Document de travail non approuvé', styles['STMeta']),
        Paragraph(escape(f'{version.report.reference} · Version {version.number}'), styles['STMeta']),
        Paragraph(escape(f'Auteur : {version.author_name}'), styles['STMeta']),
        Paragraph(escape(period_label(version)), styles['STMeta']), Spacer(1, 6*mm)]
    for section in version.sections:
        story.append(Paragraph(escape(section['title']), styles['STHeading']))
        from .st_report_documents import report_blocks
        list_number = 0
        for kind, block in report_blocks(section):
            if kind == 'table':
                columns = max(len(row) for row in block)
                cell_style = ParagraphStyle('cell', parent=styles['STBody'], fontSize=8, leading=11, spaceAfter=0)
                header_style = ParagraphStyle('cell-head', parent=cell_style, fontName='STReportBold', textColor=colors.white)
                rows = [[Paragraph(escape(cell or ' '), header_style if i == 0 else cell_style) for cell in row + [''] * (columns - len(row))] for i, row in enumerate(block)]
                table = Table(rows, colWidths=[doc.width / columns] * columns, repeatRows=1, hAlign='LEFT', splitInRow=1)
                table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a9a')), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e9f0fd')]), ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#c9d2e6')), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
                story.extend([table, Spacer(1, 3*mm)])
                continue
            runs, attrs = block
            text = ''
            for value, marks in runs:
                value = escape(value)
                if marks.get('bold'):
                    value = '<b>' + value + '</b>'
                if marks.get('italic'):
                    value = '<i>' + value + '</i>'
                if marks.get('underline'):
                    value = '<u>' + value + '</u>'
                if marks.get('strike'):
                    value = '<strike>' + value + '</strike>'
                text += value
            if attrs.get('list'):
                list_number += 1
                text = ('• ' if attrs['list'] == 'bullet' else f'{list_number}. ') + text
            else:
                list_number = 0
            style = ParagraphStyle('block', parent=styles['STBody'], alignment={'center': 1, 'right': 2, 'justify': 4}.get(attrs.get('align'), 0))
            if attrs.get('header'):
                style.fontName = 'STReportBold'
                style.fontSize = 15 if attrs['header'] == 1 else 12
            story.append(Paragraph(text or ' ', style))
    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont('STReport', 8)
        canvas.setFillColor(colors.HexColor('#475569'))
        canvas.drawString(22*mm, 12*mm, f"{getattr(version, 'document', {}).get('cover', {}).get('brand') or 'CNE-ITP'} · {version.report.reference} · v{version.number}")
        canvas.drawRightString(A4[0]-22*mm, 12*mm, f'Page {document.page}')
        canvas.restoreState()
    doc.build(story, onFirstPage=footer, onLaterPages=footer, canvasmaker=partial(Canvas, invariant=1))
    return prepend_cover(out.getvalue(), version)


def export_report_docx(version):
    from .st_report_documents import fixed_docx
    if getattr(version, 'document', {}).get('mode') == 'fixed':
        return fixed_docx(version)
    from docx import Document
    from docx.shared import Cm, Pt, RGBColor
    document = Document()
    from .st_report_cover import add_word_cover
    section = add_word_cover(document, version)
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(2)
    section.left_margin = section.right_margin = Cm(2.2)
    for name in ('Normal', 'Title', 'Heading 1'):
        style = document.styles[name]
        style.font.name = 'Arial'
        style.font.color.rgb = RGBColor(0, 0, 0)
    document.styles['Normal'].font.size = Pt(11)
    document.styles['Normal'].paragraph_format.space_after = Pt(7)
    document.styles['Title'].font.size = Pt(20)
    document.styles['Heading 1'].font.size = Pt(13)
    document.styles['Heading 1'].font.color.rgb = RGBColor.from_string('1E3A9A')
    document.styles['Heading 1'].paragraph_format.keep_with_next = True
    for line in institution_lines(version):
        paragraph = document.add_paragraph(line)
        paragraph.paragraph_format.space_after = Pt(2)
        for run in paragraph.runs:
            run.font.size = Pt(9)
    document.add_paragraph(version.title, style='Title')
    document.add_paragraph('Document de travail non approuvé')
    for text in (f'{version.report.reference} · Version {version.number}', f'Auteur : {version.author_name}', period_label(version)):
        document.add_paragraph(text)
    for item in version.sections:
        document.add_paragraph(item['title'], style='Heading 1')
        from .st_report_documents import report_blocks
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        for kind, block in report_blocks(item):
            if kind == 'table':
                from docx.oxml import OxmlElement
                from docx.oxml.ns import qn
                from docx.enum.table import WD_TABLE_ALIGNMENT
                columns = max(len(row) for row in block)
                table = document.add_table(rows=0, cols=columns)
                table.style = 'Table Grid'
                table.alignment = WD_TABLE_ALIGNMENT.CENTER
                for i, values in enumerate(block):
                    row = table.add_row()
                    if i == 0:
                        row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
                    for j, cell in enumerate(row.cells):
                        cell.text = values[j] if j < len(values) else ''
                        shading = OxmlElement('w:shd')
                        shading.set(qn('w:fill'), '1E3A9A' if i == 0 else 'E9F0FD' if i % 2 == 0 else 'FFFFFF')
                        cell._tc.get_or_add_tcPr().append(shading)
                        for paragraph in cell.paragraphs:
                            paragraph.paragraph_format.space_after = Pt(4)
                            paragraph.paragraph_format.space_before = Pt(4)
                            for run in paragraph.runs:
                                run.font.size = Pt(9)
                                if i == 0:
                                    run.bold = True
                                    run.font.color.rgb = RGBColor(255, 255, 255)
                document.add_paragraph().paragraph_format.space_after = Pt(3)
                continue
            runs, attrs = block
            paragraph = document.add_paragraph(style='Heading 2' if attrs.get('header') else 'List Bullet' if attrs.get('list') == 'bullet' else 'List Number' if attrs.get('list') == 'ordered' else None)
            paragraph.alignment = {'center': WD_ALIGN_PARAGRAPH.CENTER, 'right': WD_ALIGN_PARAGRAPH.RIGHT, 'justify': WD_ALIGN_PARAGRAPH.JUSTIFY}.get(attrs.get('align'), WD_ALIGN_PARAGRAPH.LEFT)
            for text, marks in runs:
                run = paragraph.add_run(text)
                run.bold = bool(marks.get('bold'))
                run.italic = bool(marks.get('italic'))
                run.underline = bool(marks.get('underline'))
                run.font.strike = bool(marks.get('strike'))
    section.footer.paragraphs[0].text = f"{getattr(version, 'document', {}).get('cover', {}).get('brand') or 'CNE-ITP'} · {version.report.reference} · Version {version.number}"
    document.core_properties.title = version.title[:255]
    document.core_properties.author = version.author_name[:255]
    document.core_properties.created = version.created_at
    document.core_properties.modified = version.created_at
    for root in (document.styles.element, document.element):
        for border in root.xpath('.//w:pBdr'):
            border.getparent().remove(border)
    raw = BytesIO()
    document.save(raw)
    # Les horodatages ZIP sont stabilisés pour les répétitions d’envoi idempotentes.
    output = BytesIO()
    with zipfile.ZipFile(raw) as source, zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as target:
        for name in sorted(source.namelist()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            target.writestr(info, source.read(name))
    return output.getvalue()

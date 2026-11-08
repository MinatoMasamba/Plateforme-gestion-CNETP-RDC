"""Exports déterministes d’une version de rapport, sans modification du document."""
from functools import partial
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
import zipfile

INSTITUTION = ['RÉPUBLIQUE DÉMOCRATIQUE DU CONGO', 'MINISTÈRE DES INFRASTRUCTURES ET TRAVAUX PUBLICS', 'CNE-ITP — Coordination du Secrétariat technique']


def period_label(version):
    start = version.period_start.strftime('%d/%m/%Y') if version.period_start else 'Non précisé'
    end = version.period_end.strftime('%d/%m/%Y') if version.period_end else 'Non précisé'
    return f'Période : {start} au {end}'


def export_report_pdf(version):
    import reportlab
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    fonts = Path(reportlab.__file__).parent / 'fonts'
    if 'STReport' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('STReport', str(fonts / 'Vera.ttf')))
        pdfmetrics.registerFont(TTFont('STReportBold', str(fonts / 'VeraBd.ttf')))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='STBody', fontName='STReport', fontSize=10.5, leading=15, spaceAfter=7))
    styles.add(ParagraphStyle(name='STTitle', fontName='STReportBold', fontSize=18, leading=23, spaceBefore=14, spaceAfter=12))
    styles.add(ParagraphStyle(name='STHeading', fontName='STReportBold', fontSize=12, leading=17, spaceBefore=12, spaceAfter=6, keepWithNext=True))
    styles.add(ParagraphStyle(name='STMeta', fontName='STReport', fontSize=8.5, leading=12, textColor=colors.HexColor('#475569'), spaceAfter=3))
    out = BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=22*mm, rightMargin=22*mm,
        topMargin=19*mm, bottomMargin=20*mm, title=version.title, author=version.author_name, invariant=1)
    story = [Paragraph(escape(line), styles['STMeta']) for line in INSTITUTION]
    story += [Paragraph(escape(version.title), styles['STTitle']),
        Paragraph('Document de travail non approuvé', styles['STMeta']),
        Paragraph(escape(f'{version.report.reference} · Version {version.number}'), styles['STMeta']),
        Paragraph(escape(f'Auteur : {version.author_name}'), styles['STMeta']),
        Paragraph(escape(period_label(version)), styles['STMeta']), Spacer(1, 6*mm)]
    for section in version.sections:
        story.append(Paragraph(escape(section['title']), styles['STHeading']))
        for paragraph in section['content'].split('\n\n'):
            story.append(Paragraph(escape(paragraph or '—').replace('\n', '<br/>'), styles['STBody']))
    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont('STReport', 8)
        canvas.setFillColor(colors.HexColor('#475569'))
        canvas.drawString(22*mm, 12*mm, f'CNE-ITP · ST · {version.report.reference} · v{version.number}')
        canvas.drawRightString(A4[0]-22*mm, 12*mm, f'Page {document.page}')
        canvas.restoreState()
    doc.build(story, onFirstPage=footer, onLaterPages=footer, canvasmaker=partial(Canvas, invariant=1))
    return out.getvalue()


def export_report_docx(version):
    from docx import Document
    from docx.shared import Cm, Pt, RGBColor
    document = Document()
    section = document.sections[0]
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
    document.styles['Heading 1'].paragraph_format.keep_with_next = True
    for line in INSTITUTION:
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
        for text in item['content'].split('\n\n'):
            document.add_paragraph(text or '—')
    section.footer.paragraphs[0].text = f'CNE-ITP · ST · {version.report.reference} · Version {version.number}'
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

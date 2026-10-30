"""Exports figés des rapports approuvés."""
from html import escape
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .catalog import FAMILIES, LABELS, TYPES, fields_for

BLUE = colors.HexColor('#183c91')
DARK = colors.HexColor('#102d6b')
PALE = colors.HexColor('#eaf0fb')


def _data(report):
    snap = report.source_snapshot or {}
    return {
        'fields': snap.get('fields', report.fields),
        'evidence': snap.get('evidence', []),
        'financial_lines': snap.get('financial_lines', []),
    }


def _cover(canvas, document, report):
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(DARK)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#3157b3'))
    canvas.rect(0, 0, width, height * .39, fill=1, stroke=0)
    logo = Path(settings.BASE_DIR) / 'templates/static/img/logo-cnetp.png'
    if logo.is_file():
        canvas.drawImage(ImageReader(str(logo)), width / 2 - 28, height - 125, width=56, height=56, mask='auto', preserveAspectRatio=True)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawCentredString(width / 2, height - 168, 'RÉPUBLIQUE DÉMOCRATIQUE DU CONGO')
    canvas.setFont('Helvetica', 9)
    canvas.drawCentredString(width / 2, height - 185, 'MINISTÈRE DES INFRASTRUCTURES ET TRAVAUX PUBLICS')
    canvas.setFont('Helvetica-Bold', 22)
    canvas.drawCentredString(width / 2, height - 265, 'RAPPORT CNE-ITP')
    canvas.setFont('Helvetica-Bold', 13)
    for index, line in enumerate(_wrap_title(report.title, 47)):
        canvas.drawCentredString(width / 2, height - 300 - index * 18, line)
    canvas.setFont('Helvetica', 10)
    details = [f'Référence : {report.reference}', f'Période : {report.period_start:%d/%m/%Y} au {report.period_end:%d/%m/%Y}',
               f'Destinataire : {report.recipient}', f'Préparateur : {report.prepared_by.get_full_name() or report.prepared_by.username}',
               f'Version approuvée le : {report.approved_at:%d/%m/%Y}' if report.approved_at else 'Version approuvée']
    for index, line in enumerate(details):
        canvas.drawString(72, height - 420 - index * 25, line[:105])
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawCentredString(width / 2, 40, 'COMMISSION NATIONALE D’ÉLABORATION DES NORMES ITP')
    canvas.restoreState()


def _wrap_title(value, length):
    words, lines, current = value.split(), [], ''
    for word in words:
        candidate = (current + ' ' + word).strip()
        if len(candidate) > length and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines[:4]


def _later(canvas, document, report):
    width, height = A4
    canvas.saveState()
    canvas.setStrokeColor(BLUE)
    canvas.line(45, height - 50, width - 45, height - 50)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.setFillColor(DARK)
    canvas.drawString(45, height - 40, 'CNE-ITP · ' + report.reference)
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(width - 45, 32, f'Page {document.page} · {report.reference}')
    canvas.restoreState()


def build_pdf(report):
    data = _data(report)
    stream = BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=A4, leftMargin=45, rightMargin=45, topMargin=65, bottomMargin=55,
                            title=report.title, author='CNE-ITP')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportTitle', parent=styles['Heading1'], textColor=DARK, fontSize=17, spaceAfter=14))
    styles.add(ParagraphStyle(name='ReportSection', parent=styles['Heading2'], textColor=BLUE, fontSize=11, spaceBefore=15, spaceAfter=7))
    styles.add(ParagraphStyle(name='ReportBody', parent=styles['BodyText'], fontSize=9, leading=14, spaceAfter=7))
    cover = [Spacer(1, 690), PageBreak()]
    story = cover + [Paragraph(escape(report.title), styles['ReportTitle']),
                     Paragraph(f'{escape(FAMILIES[TYPES[report.report_type][0]])} · {escape(report.reference)} · {report.period_start:%d/%m/%Y}–{report.period_end:%d/%m/%Y}', styles['ReportBody'])]
    for key in fields_for(report.report_type):
        item = data['fields'].get(key, {})
        value = item.get('value') or 'Non établi'
        story.append(Paragraph(escape(LABELS[key]), styles['ReportSection']))
        story.append(Paragraph(escape(value).replace('\n', '<br/>'), styles['ReportBody']))
        story.append(Paragraph('Source : ' + escape(item.get('source') or 'non renseignée') + ' · ' + escape(item.get('at') or 'date non renseignée'), styles['ReportBody']))
    if report.reservations:
        story.extend([Paragraph('Réserves', styles['ReportSection']), Paragraph(escape(report.reservations).replace('\n', '<br/>'), styles['ReportBody'])])
    if report.decision_requested:
        story.extend([Paragraph('Décision sollicitée', styles['ReportSection']), Paragraph(escape(report.decision_requested).replace('\n', '<br/>'), styles['ReportBody'])])
    if data['financial_lines']:
        story.append(Paragraph('Lignes financières justifiées', styles['ReportSection']))
        rows = [['Besoin', 'Total', 'Confirmé', 'Engagé', 'Liquidé', 'Ordonnancé', 'Payé']]
        rows += [[line['need'][:35], line['total'], line['confirmed_funding'], line['committed'], line['liquidated'], line['ordered'], line['paid']] for line in data['financial_lines']]
        table = Table(rows, repeatRows=1, colWidths=[145, 55, 55, 55, 55, 65, 55])
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), BLUE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                   ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 7),
                                   ('GRID', (0, 0), (-1, -1), .3, colors.HexColor('#bdcbe2')),
                                   ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        story.append(table)
    story.append(Paragraph('Pièces et références', styles['ReportSection']))
    for item in data['evidence']:
        story.append(Paragraph(escape(item['title']) + ' · ' + escape(item['source_reference'] or 'référence non renseignée'), styles['ReportBody']))
    story.append(Paragraph('Validation', styles['ReportSection']))
    story.append(Paragraph('Contrôle : ' + escape(str(report.reviewed_by or 'non renseigné')) + ' · Approbation : ' + escape(str(report.approved_by or 'non renseigné')), styles['ReportBody']))
    if report.prepared_by_id == report.approved_by_id:
        story.append(Paragraph('Approbation par le préparateur : situation consignée au journal.', styles['ReportBody']))
    doc.build(story, onFirstPage=lambda c, d: _cover(c, d, report), onLaterPages=lambda c, d: _later(c, d, report))
    return stream.getvalue()


def _word_paragraph(value, *, bold=False, size=21, page_break=False, color='172B4D'):
    text = escape(str(value)).replace('\n', '</w:t></w:r></w:p><w:p><w:r><w:t>')
    return ('<w:p><w:pPr>' + ('<w:pageBreakBefore/>' if page_break else '') + '</w:pPr><w:r><w:rPr>' +
            ('<w:b/>' if bold else '') + f'<w:sz w:val="{size}"/><w:color w:val="{color}"/></w:rPr>' +
            f'<w:t xml:space="preserve">{text}</w:t></w:r></w:p>')


def build_docx(report):
    data = _data(report)
    cover = ''.join([
        _word_paragraph('RÉPUBLIQUE DÉMOCRATIQUE DU CONGO', bold=True, size=22, color='FFFFFF'),
        _word_paragraph('MINISTÈRE DES INFRASTRUCTURES ET TRAVAUX PUBLICS', size=18, color='FFFFFF'),
        _word_paragraph(' ', size=100, color='FFFFFF'),
        _word_paragraph('RAPPORT CNE-ITP', bold=True, size=40, color='FFFFFF'),
        _word_paragraph(report.title, bold=True, size=30, color='FFFFFF'),
        _word_paragraph(' ', size=100, color='FFFFFF'),
        _word_paragraph(f'{report.reference} · {report.period_start:%d/%m/%Y} au {report.period_end:%d/%m/%Y}', color='FFFFFF'),
        _word_paragraph('Destinataire : ' + report.recipient, color='FFFFFF'),
        _word_paragraph('Préparateur : ' + (report.prepared_by.get_full_name() or report.prepared_by.username), color='FFFFFF'),
    ])
    parts = [
        '<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tblBorders></w:tblPr>'
        '<w:tr><w:trPr><w:trHeight w:val="12500" w:hRule="atLeast"/></w:trPr><w:tc><w:tcPr><w:shd w:fill="102D6B"/></w:tcPr>' + cover + '</w:tc></w:tr></w:tbl>',
        _word_paragraph('Rapport approuvé', bold=True, page_break=True, size=30, color='183C91'),
    ]
    for key in fields_for(report.report_type):
        item = data['fields'].get(key, {})
        parts.append(_word_paragraph(LABELS[key], bold=True, size=25, color='183C91'))
        parts.append(_word_paragraph(item.get('value') or 'Non établi'))
        parts.append(_word_paragraph('Source : ' + (item.get('source') or 'non renseignée'), size=17))
    for line in data['financial_lines']:
        parts.append(_word_paragraph(f"{line['need']} · total {line['total']} {line['currency']} · confirmé {line['confirmed_funding']} · engagé {line['committed']} · liquidé {line['liquidated']} · ordonnancé {line['ordered']} · payé {line['paid']}", size=18))
    parts.append(_word_paragraph('Pièces et références', bold=True, size=25, color='183C91'))
    for item in data['evidence']:
        parts.append(_word_paragraph(item['title'] + ' · ' + (item['source_reference'] or 'référence non renseignée')))
    parts.append(_word_paragraph('Contrôle : ' + str(report.reviewed_by or 'non renseigné') + ' · Approbation : ' + str(report.approved_by or 'non renseigné')))
    if report.prepared_by_id == report.approved_by_id:
        parts.append(_word_paragraph('Approbation par le préparateur : situation consignée au journal.'))
    body = ''.join(parts)
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' +
                body + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1080" w:right="900" w:bottom="1080" w:left="900"/></w:sectPr></w:body></w:document>')
    content_types = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
    relationships = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                     '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    buffer = BytesIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as package:
        package.writestr('[Content_Types].xml', content_types)
        package.writestr('_rels/.rels', relationships)
        package.writestr('word/document.xml', document)
    return buffer.getvalue()

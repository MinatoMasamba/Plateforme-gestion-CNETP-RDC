"""Page zéro commune, adaptée de draw_cover/rhombi du code fourni le 08/11/2026.

Le dégradé de 220 bandes, le médaillon, les règles, les cinq rubriques et
les quatre indicateurs restent issus du dessin fourni. Aucun code joint n’est exécuté.
"""
from io import BytesIO
from xml.sax.saxutils import escape

from django.core.exceptions import ValidationError

COVER_LIMITS = {'organization': 180, 'department': 180, 'title': 250, 'subtitle': 180,
                'recipient': 200, 'subject': 200, 'issuer': 150, 'date': 150,
                'reference': 150, 'brand': 80, 'footer': 150}


def validate_cover(value):
    if not isinstance(value, dict) or set(value) - (set(COVER_LIMITS) | {'stats'}):
        raise ValidationError('Champs de couverture invalides.')
    for key, limit in COVER_LIMITS.items():
        text = value.get(key, '')
        if not isinstance(text, str) or len(text) > limit or any(ord(c) < 32 and c not in '\n\t\r' for c in text):
            raise ValidationError(f'Couverture : {key} doit être un texte de {limit} caractères maximum.')
    stats = value.get('stats', [])
    if not isinstance(stats, list) or len(stats) > 4:
        raise ValidationError('La couverture accepte quatre indicateurs maximum.')
    for item in stats:
        if not isinstance(item, dict) or set(item) != {'value', 'label'} or not isinstance(item['value'], str) or not isinstance(item['label'], str) or len(item['value']) > 20 or len(item['label']) > 60:
            raise ValidationError('Indicateur de couverture invalide.')
    return value


def cover_data(version):
    value = dict(getattr(version, 'document', {}).get('cover') or {})
    defaults = {'organization': 'CNE-ITP', 'department': 'Coordination du Secrétariat technique',
                'title': version.title, 'subtitle': 'Document de travail non approuvé',
                'recipient': '', 'subject': '', 'issuer': 'E. Luwenga',
                'date': version.created_at.strftime('%d/%m/%Y') if getattr(version, 'created_at', None) else '',
                'reference': f'{version.report.reference} · Version {version.number}', 'brand': 'CNE-ITP',
                'footer': 'Consultant Emmany Luwenga'}
    return {**defaults, **{k: v for k, v in value.items() if v or k == 'stats'}}


def rhombi(c, cx, cy, s):
    hw, hh, pitch = 15.6 * s, 6.2 * s, 11.76 * s
    for k in (-1, 0, 1):
        y = cy - k * pitch
        p = c.beginPath()
        p.moveTo(cx - hw, y)
        p.lineTo(cx, y + hh)
        p.lineTo(cx + hw, y)
        p.lineTo(cx, y - hh)
        p.close()
        c.drawPath(p, fill=1, stroke=0)


def draw_cover(c, data):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph
    W, H = A4
    n, top, bot = 220, (0x0f, 0x2a, 0x6e), (0x1b, 0x3c, 0x9f)
    h = H / n
    for i in range(n):
        t = i / (n - 1)
        c.setFillColorRGB(*[(top[k] + (bot[k] - top[k]) * t) / 255 for k in range(3)])
        c.rect(0, H - (i + 1) * h - .5, W, h + 1, fill=1, stroke=0)
    cx = W / 2
    c.setStrokeColor(white)
    c.setLineWidth(1.4)
    c.circle(cx, H - 118.8, 37.2, stroke=1, fill=0)
    c.setFillColor(white)
    rhombi(c, cx, H - 118.8, 1.)

    def text(value, y_top, size, width, height, *, x=None, bold=False, color=white, align=1):
        if not value:
            return
        # Paragraph wrapping replaces fixed strings so real recipient/title lengths fit.
        for actual in range(int(size * 2), 11, -1):
            style = ParagraphStyle('cover', fontName='Helvetica-Bold' if bold else 'Helvetica', fontSize=actual / 2,
                                   leading=actual / 2 * 1.2, textColor=color, alignment=align)
            paragraph = Paragraph(escape(value).replace('\n', '<br/>'), style)
            _, used = paragraph.wrap(width, height)
            if used <= height:
                paragraph.drawOn(c, (W - width) / 2 if x is None else x, H - y_top - used)
                return
        raise ValidationError('Texte trop long pour la couverture ; raccourcissez cette rubrique.')

    def rule(y_top, x0=167.5, x1=428):
        c.setStrokeColor(HexColor('#8fa6dd'))
        c.setLineWidth(.7)
        c.line(x0, H - y_top, x1, H - y_top)

    text(data.get('organization', ''), 192, 15, 480, 35, bold=True)
    rule(235)
    text(data.get('department', ''), 247, 11, 470, 32, bold=True, color=HexColor('#dce5fa'))
    text(data.get('title', ''), 302, 34, 475, 103, bold=True)
    text(data.get('subtitle', ''), 410, 13, 475, 40, color=HexColor('#c9d6f5'))
    rule(462)
    rows = [('À L’ATTENTION DE', 'recipient'), ('OBJET', 'subject'), ('ÉMETTEUR', 'issuer'), ('DATE', 'date'), ('RÉFÉRENCE', 'reference')]
    for i, (label, key) in enumerate(rows):
        y = 480 + 37 * i
        text(label, y, 7, 118, 32, x=76, bold=True, color=HexColor('#9db4e8'), align=0)
        text(data.get(key, ''), y - 1, 9, 307, 34, x=213, align=0)
    for i, item in enumerate(data.get('stats', [])):
        x = 40 + 130.7 * i
        text(item['value'], 697, 28, 122, 39, x=x, bold=True)
        text(item['label'], 737, 6.3, 122, 22, x=x, bold=True, color=HexColor('#c9d6f5'))
    rule(776, 59.6, 535.6)
    text(data.get('footer') or 'Consultant Emmany Luwenga', 789, 10, 476, 22)


def cover_pdf(data):
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4
    validate_cover(data)
    output = BytesIO()
    canvas = Canvas(output, pagesize=A4, invariant=1)
    draw_cover(canvas, data)
    canvas.showPage()
    canvas.save()
    return output.getvalue()


def cover_png(data, scale=1.5):
    import fitz
    with fitz.open(stream=cover_pdf(data), filetype='pdf') as pdf:
        return pdf[0].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).tobytes('png')


def prepend_cover(body, version):
    import fitz
    with fitz.open(stream=cover_pdf(cover_data(version)), filetype='pdf') as cover, fitz.open(stream=body, filetype='pdf') as content:
        cover.insert_pdf(content)
        return cover.tobytes(garbage=4, deflate=True, no_new_id=True)


def add_word_cover(document, version):
    from docx.shared import Pt
    from docx.enum.section import WD_SECTION_START
    # The same draw_cover output is used in both formats; it is not redrawn independently.
    section = document.sections[0]
    section.page_width, section.page_height = Pt(595.276), Pt(841.89)
    section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Pt(0)
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.line_spacing = 1
    run = paragraph.add_run()
    run.font.size = Pt(1)
    picture = run.add_picture(BytesIO(cover_png(cover_data(version), scale=300 / 72)), width=Pt(595.276), height=Pt(841.89))
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    inline = picture._inline
    inline.tag = qn('wp:anchor')
    for key, value in {'distT': '0', 'distB': '0', 'distL': '0', 'distR': '0', 'simplePos': '0', 'relativeHeight': '0', 'behindDoc': '1', 'locked': '0', 'layoutInCell': '1', 'allowOverlap': '1'}.items():
        inline.set(key, value)
    simple = OxmlElement('wp:simplePos')
    simple.set('x', '0')
    simple.set('y', '0')
    inline.insert(0, simple)
    for index, direction in enumerate(('H', 'V'), start=1):
        position = OxmlElement('wp:position' + direction)
        position.set('relativeFrom', 'page')
        offset = OxmlElement('wp:posOffset')
        offset.text = '0'
        position.append(offset)
        inline.insert(index, position)
    extent_index = list(inline).index(inline.find(qn('wp:extent')))
    inline.insert(extent_index + 1, OxmlElement('wp:wrapNone'))
    section = document.add_section(WD_SECTION_START.NEW_PAGE)
    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False
    return section

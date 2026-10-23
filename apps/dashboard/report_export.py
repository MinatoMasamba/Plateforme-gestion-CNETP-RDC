"""Small dependency-free Word export for read-only institutional snapshots."""
from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


TITLES = {
    'cabinet': 'Note de synthèse pour le Cabinet du ministre',
    'general': "Rapport général d'avancement",
    'experts': "Rapport d'activité des experts",
    'sc': 'Rapport par sous-commission',
    'production': 'Rapport de production normative',
    'decisions': 'Difficultés et décisions attendues',
}

FOCUS = {
    'cabinet': "Pour le Cabinet, la priorité est de confirmer les responsabilités, les affectations et les échéances. Les indicateurs décrivent l'enregistrement dans la base, sans présumer de décisions officielles.",
    'general': "L'avancement porte sur l'organisation, la mobilisation des experts et les projets de normes enregistrés.",
    'experts': "La participation combine la dernière connexion connue et les minutes mesurées sur les GT cibles. Les activités hors plateforme ne sont pas comptées.",
    'sc': "Chaque sous-commission est comparée selon ses GT, affectations à examiner, personnes mesurées et dossiers reliés explicitement.",
    'production': "La production est appréciée à partir des projets et versions enregistrés. Le statut du projet atteste les étapes d'adoption ou de publication.",
    'decisions': "Les affectations à examiner et les responsabilités sans mandat actif constituent des sujets à instruire. Aucun souhait d'expert ne vaut nomination.",
}


def _paragraph(text, *, size=21, bold=False, align=None, after=120):
    value = escape(str(text))
    justification = f'<w:jc w:val="{align}"/>' if align else ''
    weight = '<w:b/>' if bold else ''
    return (f'<w:p><w:pPr><w:spacing w:after="{after}"/>{justification}</w:pPr>'
            f'<w:r><w:rPr>{weight}<w:sz w:val="{size}"/><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos"/></w:rPr>'
            f'<w:t xml:space="preserve">{value}</w:t></w:r></w:p>')


def _table(rows):
    cells = []
    for index, row in enumerate(rows):
        cells.append('<w:tr>' + ''.join('<w:tc><w:tcPr><w:tcW w:w="2100" w:type="dxa"/></w:tcPr>'
                   + _paragraph(value, size=18, bold=index == 0, after=40) + '</w:tc>' for value in row) + '</w:tr>')
    return '<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders><w:bottom w:val="single" w:color="D7E2EC"/></w:tblBorders></w:tblPr>' + ''.join(cells) + '</w:tbl>'


def build_report_docx(data):
    version = data['version']
    label = version.get_status_display() if version else 'non disponible'
    code = version.code if version else 'non disponible'
    parts = [
        _paragraph('RÉPUBLIQUE DÉMOCRATIQUE DU CONGO', bold=True, align='center', size=19),
        _paragraph("COMMISSION NATIONALE D'ÉLABORATION DES NORMES ITP (CNE-ITP)", align='center', size=18, after=320),
        _paragraph(TITLES[data['kind']], bold=True, align='center', size=32, after=180),
        _paragraph('Extraction le ' + data['extracted_at'].strftime('%d/%m/%Y à %H:%M') + ' · Référentiel ' + code + ' · ' + label, align='center', size=18, after=350),
        _paragraph('1. Résumé exécutif', bold=True, size=25),
        _paragraph(f"Le référentiel {code} porte le statut « {label} ». Il comprend {len(data['rows'])} sous-commissions et {data['group_count']} groupes de travail. {data['expert_count']} experts hors administration et {data['project_count']} projets de normes sont enregistrés.", after=250),
        _paragraph(FOCUS[data['kind']], after=250),
        _paragraph('2. Indicateurs vérifiables', bold=True, size=25),
        _table([('Indicateur', 'Valeur'), ('Experts enregistrés hors administration', data['expert_count']), ('Experts avec une dernière connexion', data['connected_count']), ('Affectations à examiner', data['review_count']), ('Projets de normes', data['project_count']), ('Versions de normes', data['version_count']), ('Projets adoptés, homologués ou publiés', data['adopted_count'])]),
        _paragraph('3. Activité des sous-commissions', bold=True, size=25, after=80),
        _paragraph('Les minutes proviennent des agrégats journaliers explicitement liés aux GT. Une valeur nulle ne prouve pas une absence de travail hors plateforme.', size=19),
        _table([('Sous-commission', 'GT', 'À examiner', 'Minutes mesurées')] + [(r['sc'].code, r['gt_count'], r['review'], r['minutes']) for r in data['rows']]),
        _paragraph('4. Décisions attendues', bold=True, size=25, after=80),
        _paragraph('Examiner les affectations en attente, formaliser les responsabilités manquantes par acte référencé et fixer les échéances de travaux par sous-commission.'),
        _paragraph('Conclusion', bold=True, size=25, after=80),
        _paragraph("Cette note décrit la situation enregistrée à la date d'extraction. Les rattachements migrés et les souhaits exprimés ne constituent pas des nominations officielles."),
    ]
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body>' + ''.join(parts) + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
                '<w:pgMar w:top="1080" w:right="900" w:bottom="1080" w:left="900"/></w:sectPr></w:body></w:document>')
    content_types = ('<?xml version="1.0" encoding="UTF-8"?>'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                     '</Types>')
    relationships = ('<?xml version="1.0" encoding="UTF-8"?>'
                     '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                     '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                     '</Relationships>')
    buffer = BytesIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as package:
        package.writestr('[Content_Types].xml', content_types)
        package.writestr('_rels/.rels', relationships)
        package.writestr('word/document.xml', document)
    return buffer.getvalue()

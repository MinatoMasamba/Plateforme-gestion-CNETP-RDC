import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from django.core.management.base import BaseCommand


WORD_NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def extract_docx_paragraphs(path: Path):
    """Extraction simple du texte d'un docx, paragraphe par paragraphe."""
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read('word/document.xml'))

    paragraphs = []
    for paragraph in root.findall('.//w:body/w:p', WORD_NS):
        parts = []
        for node in paragraph.iter():
            tag = node.tag.rsplit('}', 1)[-1]
            if tag == 't':
                parts.append(node.text or '')
            elif tag == 'tab':
                parts.append('\t')
            elif tag == 'br':
                parts.append('\n')
        text = ''.join(parts).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def detect_document_type(paragraphs):
    first = ' '.join(paragraphs[:5]).lower()
    if 'liste des normes' in first:
        return 'liste_normes'
    if 'guide de gouvernance' in first or 'rédaction des documents normatifs' in first:
        return 'guide'
    if 'norme fictive complète' in first or 'numéro :' in first:
        return 'norme'
    return 'inconnu'


def split_sections(paragraphs):
    """Découpe en blocs selon les titres connus."""
    section_markers = {
        'Préambule': 'preambule',
        'Introduction': 'introduction',
        'Références normatives': 'references_normatives',
        'Termes et définitions': 'termes_definitions',
        'Principes généraux': 'principes_generaux',
        'Exigences': 'exigences',
        'Section normative': 'section_normative',
    }
    blocks = []
    current = None

    def flush():
        nonlocal current
        if current:
            current['text'] = '\n'.join(current['lines']).strip()
            current['line_count'] = len(current['lines'])
            blocks.append(current)
            current = None

    for para in paragraphs:
        normalized = para.strip()
        lower = normalized.lower()

        marker = None
        for label, code in section_markers.items():
            if lower == label.lower() or lower.startswith(label.lower() + ' ') or lower.startswith(label.lower() + ':'):
                marker = (label, code)
                break

        if marker:
            flush()
            current = {
                'title': marker[0],
                'code': marker[1],
                'lines': [],
            }
            continue

        if current is None:
            current = {
                'title': 'Preamble',
                'code': 'preamble',
                'lines': [],
            }
        current['lines'].append(normalized)

    flush()
    return blocks


def is_heading(line):
    normalized = line.strip()
    if not normalized:
        return False
    if re.match(r'^\d+(\.\d+)*\s+[A-ZÀ-ÿ].+', normalized):
        return True
    if re.match(r'^(Annexe|Section|Chapitre|Partie)\s+[A-Z0-9IVXLC]+\b', normalized, re.IGNORECASE):
        return True
    return normalized in {
        'Préambule', 'Dispositions générales', 'Références normatives',
        'Termes et définitions', 'Principes généraux', 'Exigences',
        'Méthodes d’essai détaillées', 'Annexes normatives', 'Annexes informatives',
        'Historique des révisions',
    }


def build_hierarchy(paragraphs):
    """
    Transforme une suite de paragraphes en arbre hiérarchique basé sur les titres numérotés.
    """
    root = {'title': 'root', 'level': 0, 'children': [], 'content': []}
    stack = [root]

    def heading_level(title):
        if title.startswith('Annexe'):
            return 2
        match = re.match(r'^(\d+(?:\.\d+)*)\s+', title)
        if match:
            return 1 + match.group(1).count('.')
        if title in {'Préambule', 'Introduction'}:
            return 1
        return 1

    for para in paragraphs:
        text = para.strip()
        if not text:
            continue
        if is_heading(text):
            level = heading_level(text)
            node = {'title': text, 'level': level, 'children': [], 'content': []}
            while stack and stack[-1]['level'] >= level:
                stack.pop()
            stack[-1]['children'].append(node)
            stack.append(node)
        else:
            stack[-1]['content'].append(text)

    return root['children']


def extract_guide_payload(paragraphs):
    parts = build_hierarchy(paragraphs)
    excluded_prefixes = (
        'Première Partie', 'Deuxième Partie', 'Troisième Partie', 'Quatrième Partie',
        'Cinquième Partie', 'Sixième Partie', 'Septième Partie', 'Huitième Partie',
    )
    return {
        'parts': parts,
        'topics': [p for p in paragraphs if p and not p.startswith(excluded_prefixes)][:50],
    }


def extract_norme_payload(paragraphs):
    blocks = build_hierarchy(paragraphs)
    references_normatives = []
    in_references = False
    for para in paragraphs:
        lower = para.lower().strip()
        if lower.startswith('références normatives'):
            in_references = True
            continue
        if in_references:
            if lower in {'termes et définitions', 'principes généraux', 'exigences'}:
                break
            if para:
                references_normatives.append(para)

    return {
        'blocks': blocks,
        'references_normatives': references_normatives,
        'section_titles': [b['title'] for b in blocks],
    }


def extract_liste_normes_payload(paragraphs):
    categories = []
    current_category = None
    item_pattern = re.compile(r'^[A-Z0-9]{1,6}[-\d].+')

    for para in paragraphs:
        stripped = para.strip()
        if not stripped:
            continue
        if re.match(r'^\d+\.\s', stripped):
            current_category = {'title': stripped, 'items': []}
            categories.append(current_category)
            continue
        if current_category is None:
            current_category = {'title': 'Général', 'items': []}
            categories.append(current_category)
        if item_pattern.match(stripped) or ':' in stripped:
            current_category['items'].append(stripped)
        else:
            current_category.setdefault('notes', []).append(stripped)

    return {'categories': categories}


class Command(BaseCommand):
    help = 'Extrait les documents Word de la racine norme/ et produit un JSON structuré.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            default='norme/extracted_norme_documents.json',
            help='Chemin du fichier JSON de sortie.',
        )

    def handle(self, *args, **options):
        base_dir = Path('norme')
        output_path = Path(options['output'])
        part_pattern = re.compile(r'^(Première|Deuxième|Troisième|Quatrième|Cinquième|Sixième|Septième|Huitième)\s+Partie', re.IGNORECASE)

        results = []
        for doc_path in sorted(base_dir.glob('*.docx')):
            paragraphs = extract_docx_paragraphs(doc_path)
            doc_type = detect_document_type(paragraphs)

            if doc_type == 'guide':
                payload = extract_guide_payload(paragraphs)
            elif doc_type == 'liste_normes':
                payload = extract_liste_normes_payload(paragraphs)
            elif doc_type == 'norme':
                payload = extract_norme_payload(paragraphs)
            else:
                payload = {'paragraphs': paragraphs[:200]}

            results.append({
                'filename': doc_path.name,
                'path': str(doc_path),
                'document_type': doc_type,
                'paragraph_count': len(paragraphs),
                'payload': payload,
            })

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'JSON généré: {output_path}'))

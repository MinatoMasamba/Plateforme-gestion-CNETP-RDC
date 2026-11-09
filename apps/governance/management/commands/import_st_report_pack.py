"""Import the approved local ZIP catalogue without executing or trusting its instructions."""
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from apps.governance.st_report_documents import import_source, docx_sections
from apps.governance.st_report_models import STReportTemplate

NAMES = ['Modèle universel', 'Rapport d’activité CNE-ITP · COPIL', 'Rapport financier CNE-ITP',
         'Avancement des normes · COPIL', 'Synthèse pour le Cabinet du Ministre ITP',
         'Activité d’un établissement scolaire', 'Finances d’un établissement scolaire',
         'Formation et transfert CTC', 'Incidents et exploitation CTC']


class Command(BaseCommand):
    help = 'Ajoute les neuf modèles Page bleue, avec les PDF de référence et Word originaux conservés.'

    def add_arguments(self, parser):
        parser.add_argument('archive')

    def handle(self, *args, **options):
        path = Path(options['archive'])
        with ZipFile(path) as archive:
            if sum(i.file_size for i in archive.infolist()) > 80 * 1024 * 1024:
                raise CommandError('Archive trop volumineuse.')
            catalogue = json.loads(archive.read('catalogue.json'))
            for item in catalogue:
                code = str(item['code'])
                if code not in [f'{i:02}' for i in range(9)] or Path(item['file']).name != item['file']:
                    raise CommandError('Entrée de catalogue invalide.')
                raw = archive.read('Word_modifiables/' + item['file'])
                preview = archive.read('PDF_apercus/' + Path(item['file']).with_suffix('.pdf').name)
                source = import_source(SimpleUploadedFile(item['file'], raw), preview_pdf=preview)
                sections = docx_sections(raw, skip_cover=True)
                if not sections:
                    raise CommandError('Structure du modèle non lisible.')
                recipient = item.get('destinataire', '')
                school = code in ('05', '06')
                cover = {'organization': 'SOURCE ACADÉMIQUE' if school else 'CNE-ITP',
                         'department': 'Établissement scolaire' if school else 'Coordination du Secrétariat technique',
                         'title': NAMES[int(code)], 'recipient': '' if recipient.startswith('[') else recipient,
                         'subtitle': 'Document de travail non approuvé', 'brand': 'Source Académique' if school else 'CNE-ITP',
                         'issuer': 'E. Luwenga', 'footer': 'Consultant Emmany Luwenga',
                         'stats': [{'value': '', 'label': ''} for _ in range(4)]}
                template, created = STReportTemplate.objects.get_or_create(system_code='pack-blue-' + code, defaults={
                    'name': NAMES[int(code)], 'source': source, 'sections': sections,
                    'document': {'mode': 'free', 'fields': [], 'source_start_page': 1, 'cover': cover}})
                if not created:
                    template.sections = sections
                    template.save(update_fields=['sections'])
                self.stdout.write(f'{"Ajouté" if created else "Existant"} : {template.name} · {len(source.pages)} pages · {sha256(raw).hexdigest()[:12]}')

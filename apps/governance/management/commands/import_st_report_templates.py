"""Register reference originals as reusable templates, without changing source files."""
from pathlib import Path
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from apps.governance.st_report_documents import import_source, docx_sections
from apps.governance.st_report_models import STReportTemplate


class Command(BaseCommand):
    help = 'Ajoute des modèles de rapports depuis des documents locaux, sans écraser les originaux.'

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+')
        parser.add_argument('--use-existing-pdf', action='store_true', help='Utiliser le PDF homonyme déjà rendu pour un modèle Word.')

    def handle(self, *args, **options):
        for filename in options['files']:
            path = Path(filename)
            if not path.is_file():
                raise CommandError(f'Document introuvable : {path}')
            with path.open('rb') as stream:
                preview = path.with_suffix('.pdf')
                source = import_source(File(stream, name=path.name), preview_pdf=preview.read_bytes() if options['use_existing_pdf'] and path.suffix.lower() == '.docx' and preview.is_file() else None)
            if path.suffix.lower() == '.docx':
                structured = docx_sections(path.read_bytes())
                if structured is not None:
                    source.sections = structured
                    source.note = ''
                    source.save(update_fields=['sections', 'note'])
            template, created = STReportTemplate.objects.get_or_create(system_code='source-' + source.sha256[:40], defaults={'name': path.stem[:200], 'source': source, 'sections': source.sections})
            if not created and path.suffix.lower() == '.docx':
                template.sections = source.sections
                template.save(update_fields=['sections'])
            self.stdout.write(f'{"Ajouté" if created else "Existant"} : {template.name} ({len(source.pages)} pages)')

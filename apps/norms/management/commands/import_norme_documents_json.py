import hashlib
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.norms.models import NormeDocumentImport


class Command(BaseCommand):
    help = 'Importe le JSON d’extraction des documents norme/ dans la base.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input',
            default='norme/extracted_norme_documents.json',
            help='Chemin du JSON produit par extract_norme_documents.',
        )

    def handle(self, *args, **options):
        input_path = Path(options['input'])
        if not input_path.exists():
            raise CommandError(f'Fichier introuvable: {input_path}')

        payload = json.loads(input_path.read_text(encoding='utf-8'))
        if not isinstance(payload, list):
            raise CommandError('Le JSON source doit contenir une liste de documents.')

        imported = 0
        updated = 0

        for item in payload:
            filename = item.get('filename')
            if not filename:
                continue
            source_path = item.get('path', '')
            document_type = item.get('document_type', 'inconnu')
            paragraph_count = int(item.get('paragraph_count', 0) or 0)
            extracted_json = item.get('payload', {})
            checksum = hashlib.sha256(
                json.dumps(item, ensure_ascii=False, sort_keys=True).encode('utf-8')
            ).hexdigest()

            obj, created = NormeDocumentImport.objects.update_or_create(
                filename=filename,
                defaults={
                    'source_path': source_path,
                    'document_type': document_type,
                    'paragraph_count': paragraph_count,
                    'extracted_json': extracted_json,
                    'checksum': checksum,
                }
            )
            obj.ensure_norme()
            if created:
                imported += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Import terminé: {imported} créés, {updated} mis à jour.'
        ))

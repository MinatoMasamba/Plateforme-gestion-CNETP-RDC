from django.core.management.base import BaseCommand, CommandError

from apps.documents.models import DocumentFile
from apps.ia_agent.services.rag import index_document_file, index_expert_cv, index_norme, index_norme_version
from apps.experts.models import Expert
from apps.norms.models import Norme


class Command(BaseCommand):
    help = 'Construit ou actualise l index documentaire RAG de la plateforme.'

    def add_arguments(self, parser):
        parser.add_argument('--documents', action='store_true', help='Indexer les documents déposés.')
        parser.add_argument('--normes', action='store_true', help='Indexer les fiches et versions de normes.')
        parser.add_argument('--document-id', type=int, help='Indexer un document précis.')
        parser.add_argument('--norme-id', type=int, help='Indexer une norme précise et ses versions.')
        parser.add_argument('--expert-cv', action='store_true', help='Indexer explicitement les CV des experts.')
        parser.add_argument('--all', action='store_true', help='Indexer les documents et les normes.')

    def handle(self, *args, **options):
        selected = any([
            options['documents'], options['normes'], options['document_id'],
            options['norme_id'], options['all'],
            options['expert_cv'],
        ])
        if not selected:
            raise CommandError('Précisez --documents, --normes, --document-id, --norme-id ou --all.')

        if options['document_id']:
            documents = DocumentFile.objects.filter(id=options['document_id'])
        elif options['documents'] or options['all']:
            documents = DocumentFile.objects.all()
        else:
            documents = DocumentFile.objects.none()

        if options['norme_id']:
            normes = Norme.objects.filter(id=options['norme_id'])
        elif options['normes'] or options['all']:
            normes = Norme.objects.all()
        else:
            normes = Norme.objects.none()

        if options['document_id'] and not documents.exists():
            raise CommandError(f"Document {options['document_id']} introuvable.")
        if options['norme_id'] and not normes.exists():
            raise CommandError(f"Norme {options['norme_id']} introuvable.")

        document_count = 0
        for document in documents.iterator():
            index_document_file(document)
            document_count += 1

        norme_count = 0
        version_count = 0
        for norme in normes.prefetch_related('versions').iterator(chunk_size=100):
            index_norme(norme)
            norme_count += 1
            for version in norme.versions.all():
                index_norme_version(version)
                version_count += 1

        cv_count = 0
        if options['expert_cv']:
            for expert in Expert.objects.select_related('structure').filter(status='ACTIVE').iterator():
                index_expert_cv(expert)
                cv_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Index RAG actualisé : {document_count} document(s), '
            f'{norme_count} norme(s), {version_count} version(s), {cv_count} CV indexé(s).'
        ))

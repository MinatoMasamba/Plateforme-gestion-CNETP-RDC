from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.core.models import User
from apps.documents.models import DocumentFile
from apps.ia_agent.services.rag import index_document_file, search
from apps.ia_agent.models import AgentArtifact, AgentSession, RAGChunk, RAGDocument
from api.v1.ia_agent.serializers import AgentArtifactSerializer


class RAGIndexTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='rag-user', email='rag@example.test', password='password'
        )
        self.other_user = User.objects.create_user(
            username='other-rag-user', email='other@example.test', password='password'
        )

    def test_indexes_text_document_and_returns_citation(self):
        document = DocumentFile.objects.create(
            uploaded_by=self.user,
            title='Procédure de réception',
            file_type='OTHER',
            mime_type='text/plain',
            is_public=True,
            file=SimpleUploadedFile(
                'procedure.txt',
                'La réception du dossier précède l indexation et la validation de l intake.'.encode(),
                content_type='text/plain',
            ),
        )

        source = index_document_file(document)
        results = search(self.user, 'validation intake')

        self.assertEqual(source.status, 'INDEXED')
        self.assertEqual(RAGDocument.objects.count(), 1)
        self.assertEqual(RAGChunk.objects.count(), 1)
        self.assertEqual(results[0]['title'], 'Procédure de réception')
        self.assertEqual(results[0]['source_key'], f'document:{document.id}')
        self.assertTrue(results[0]['url'].startswith('/assistant/source/'))
        self.assertIn('validation', results[0]['excerpt'])

        self.client.force_login(self.user)
        source_url = results[0]['url']
        response = self.client.get(source_url)
        self.assertEqual(response.status_code, 200)
        download = self.client.get(f'/assistant/source/{source.id}/download/')
        self.assertEqual(download.status_code, 200)

    def test_private_document_is_not_visible_to_unrelated_user(self):
        document = DocumentFile.objects.create(
            uploaded_by=self.user,
            title='Note interne',
            file_type='OTHER',
            mime_type='text/plain',
            is_public=False,
            file=SimpleUploadedFile(
                'note.txt', b'information strictement interne', content_type='text/plain'
            ),
        )
        index_document_file(document)

        self.assertEqual(search(self.other_user, 'strictement interne'), [])
        self.assertEqual(len(search(self.user, 'strictement interne')), 1)

    def test_artifact_serializer_exposes_internal_links(self):
        session = AgentSession.objects.create(user=self.user, scope='expert')
        artifact = AgentArtifact.objects.create(
            session=session,
            artifact_type='WG_REQUEST',
            title='Demande WG',
            payload={'expert_id': 11, 'expert_name': 'Expert Test', 'wg_id': 22, 'wg_label': 'WG Test'},
        )

        data = AgentArtifactSerializer(artifact).data
        self.assertEqual(
            [link['url'] for link in data['links']],
            ['/api/v1/experts/11/', '/api/v1/wg/22/'],
        )

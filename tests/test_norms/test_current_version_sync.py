from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase

from apps.experts.models import Expert, Structure
from apps.governance.models import CTM, WG
from apps.norms.models import Norme
from api.v1.norms.serializers import NormeVersionCreateSerializer

User = get_user_model()


class NormeCurrentVersionSyncAPITest(TransactionTestCase):
    """Tests de non-régression pour la synchronisation du fichier courant."""

    def setUp(self):
        self._ensure_content_block_table()
        self.user = User.objects.create_user(
            username='expert-user',
            email='expert@example.com',
            password='testpass123',
            is_expert=True,
        )
        self.structure = Structure.objects.create(
            name='Test Structure',
            category='administrative'
        )
        self.expert = Expert.objects.create(
            user=self.user,
            structure=self.structure,
            status='ACTIVE'
        )
        base_number = 99
        self.ctm = CTM.objects.create(number=base_number, name='CTM 99', description='Test')
        self.wg = WG.objects.create(ctm=self.ctm, number=base_number, name='WG 99')
        self.norme = Norme.objects.create(
            title='Norme de test',
            reference_number='N-001',
            description='Description',
            ctm=self.ctm,
            wg=self.wg,
            status='DRAFT',
        )

    def _ensure_content_block_table(self):
        call_command('migrate', 'norms', '0009', verbosity=0, interactive=False)

    def test_create_version_syncs_current_version_with_latest_version(self):
        document = SimpleUploadedFile(
            'norme-v1.docx',
            b'fake-docx-content',
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

        serializer = NormeVersionCreateSerializer(
            data={
                'title': 'Version 1',
                'content': 'Premier contenu\n\nDeuxieme paragraphe',
                'comment': 'Initialisation',
                'document': document,
            },
            context={'norme': self.norme, 'request': type('Request', (), {'user': self.user})()},
        )
        serializer.is_valid(raise_exception=True)
        version = serializer.save()

        self.norme.refresh_from_db()
        latest_version = self.norme.get_latest_version()

        self.assertEqual(version.id, latest_version.id)
        self.assertEqual(latest_version.version_number, 1)
        self.assertIsNotNone(self.norme.current_version)
        self.assertTrue(self.norme.current_version_matches_latest())

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TransactionTestCase

from apps.experts.models import Expert, Structure
from apps.governance.models import CTM, WG
from apps.norms.models import (
    Norme, NormeVersion, NormeContentBlock,
    parse_norme_structure, structured_content_summary
)
from api.v1.validation.views import compute_vote_summary, promote_norme_to_ctc_if_vote_passes

User = get_user_model()


class NormeStructureParsingTest(TransactionTestCase):
    def test_parse_norme_structure_extracts_sections_and_annexes(self):
        content = (
            "Introduction générale\n\n"
            "Section 1 - Objet\n"
            "Le texte de la section.\n\n"
            "Annexe A - Formulaire\n"
            "Contenu annexe."
        )

        blocks = parse_norme_structure(content)

        self.assertGreaterEqual(len(blocks), 3)
        self.assertEqual(blocks[0]['title'], 'Introduction')
        self.assertEqual(blocks[1]['title'], 'Section 1 - Objet')
        self.assertEqual(blocks[2]['type'], 'annexe')

    def test_structured_summary_returns_compact_view(self):
        summary = structured_content_summary("Section 1 - Objet\nTexte")
        self.assertEqual(summary[0]['type'], 'section')
        self.assertEqual(summary[0]['title'], 'Section 1 - Objet')


class NormeContentBlockPersistenceTest(TransactionTestCase):
    def setUp(self):
        self._ensure_content_block_table()
        self.ctm = CTM.objects.create(number=79, name='CTM 79', description='Test')
        self.wg = WG.objects.create(ctm=self.ctm, number=79, name='WG 79')
        self.norme = Norme.objects.create(
            title='Norme blocs',
            reference_number='NB-79',
            description='Test',
            ctm=self.ctm,
            wg=self.wg,
        )

    def _ensure_content_block_table(self):
        call_command('migrate', 'norms', '0009', verbosity=0, interactive=False)

    def test_blocks_are_persisted_from_version_content(self):
        from api.v1.norms.serializers import NormeVersionCreateSerializer
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(username='u79', email='u79@example.com', password='pass', is_expert=True)

        serializer = NormeVersionCreateSerializer(
            data={
                'title': 'V2',
                'content': 'Section 1 - Objet\nTexte de section',
                'document': SimpleUploadedFile('v2.docx', b'x'),
            },
            context={'norme': self.norme, 'request': type('Request', (), {'user': user})()},
        )
        serializer.is_valid(raise_exception=True)
        version2 = serializer.save()

        blocks = version2.content_blocks.all()
        self.assertGreaterEqual(blocks.count(), 1)
        self.assertEqual(blocks.first().kind, 'SECTION')


class NormeWorkflowTransitionTest(TransactionTestCase):
    def setUp(self):
        self.ctm = CTM.objects.create(number=77, name='CTM 77', description='Test')
        self.wg = WG.objects.create(ctm=self.ctm, number=77, name='WG 77')
        self.norme = Norme.objects.create(
            title='Norme test',
            reference_number='N-77',
            description='Test',
            ctm=self.ctm,
            wg=self.wg,
        )

    def test_transition_to_uses_centralized_rules(self):
        self.assertTrue(self.norme.can_transition_to('INTERNAL_REVIEW'))
        self.norme.transition_to('INTERNAL_REVIEW')
        self.assertEqual(self.norme.status, 'INTERNAL_REVIEW')

    def test_invalid_transition_is_rejected(self):
        with self.assertRaises(ValueError):
            self.norme.transition_to('PUBLISHED')


class NormeVoteProgressionTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='expert',
            email='expert@example.com',
            password='testpass123',
            is_expert=True,
        )
        self.structure = Structure.objects.create(name='Struct', category='administrative')
        self.expert = Expert.objects.create(user=self.user, structure=self.structure, status='ACTIVE')
        self.ctm = CTM.objects.create(number=78, name='CTM 78', description='Test')
        self.wg = WG.objects.create(ctm=self.ctm, number=78, name='WG 78')
        self.norme = Norme.objects.create(
            title='Norme vote',
            reference_number='NV-78',
            description='Test',
            ctm=self.ctm,
            wg=self.wg,
        )

    def test_vote_summary_and_progression(self):
        self.norme.votes.create(voter=self.expert, vote='FOR', justification='ok')
        summary = compute_vote_summary(self.norme)
        self.assertTrue(summary['passes_threshold'])
        promoted = promote_norme_to_ctc_if_vote_passes(self.norme)
        self.assertTrue(promoted)
        self.norme.refresh_from_db()
        self.assertEqual(self.norme.status, 'CTM_REVIEW')

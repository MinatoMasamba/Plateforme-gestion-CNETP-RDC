from unittest.mock import patch

from django.test import TestCase

from apps.gemini_drafts.models import Draft
from apps.gemini_drafts.services import generate_and_save
from apps.governance.models import CTM, WG


class GeminiDraftRoutingTests(TestCase):
    def setUp(self):
        self.ctm = CTM.objects.create(name='CTM Test', number=1, description='CTM de test')
        self.wg = WG.objects.create(ctm=self.ctm, name='WG Gouvernance', number=1, description='WG de gouvernance')

    @patch('apps.gemini_drafts.services.call_gemini')
    def test_generate_and_save_uses_llm_selected_ctm_and_wg(self, mock_call_gemini):
        mock_call_gemini.return_value = {
            'ctm': 'CTM Test',
            'wg': 'WG Gouvernance',
            'document_type': 'guide',
            'reason': 'Le contenu concerne la gouvernance',
            'draft_text': 'Draft de gouvernance',
        }

        draft = generate_and_save(
            domain='gouvernance',
            draft_type='guide',
            content='Ce document traite de la gouvernance et des rôles.',
            data={'source': 'unit-test'},
        )

        self.assertEqual(draft.ctm, 'CTM Test')
        self.assertEqual(draft.wg, 'WG Gouvernance')
        self.assertEqual(Draft.objects.count(), 1)
        self.assertIn('gouvernance', draft.draft_text.lower())

from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.gemini_drafts.models import Draft
from apps.gemini_drafts.services import (
    _build_gemini_request_url,
    _get_ordered_api_keys,
    generate_and_save,
)
from apps.governance.models import CTM, WG


class GeminiDraftRoutingTests(TestCase):
    def setUp(self):
        self.ctm = CTM.objects.create(name='CTM Test', number=1, description='CTM de test')
        self.wg = WG.objects.create(ctm=self.ctm, name='WG Gouvernance', number=1, description='WG de gouvernance')

    @override_settings(GEMINI_API_URL='https://generativelanguage.googleapis.com/v1beta/', GEMINI_API_KEY='fake-key', GEMINI_MODEL='gemini-2.0-flash')
    def test_build_gemini_request_url_uses_generate_content_endpoint(self):
        url = _build_gemini_request_url('https://generativelanguage.googleapis.com/v1beta/', 'fake-key', 'gemini-2.0-flash')
        self.assertEqual(url, 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=fake-key')

    @override_settings(GEMINI_API_KEY='primary-key', GEMINI_API_KEY2='secondary-key', GEMINI_API_KEY3='third-key')
    def test_get_ordered_api_keys_prefers_primary_and_fallbacks(self):
        keys = _get_ordered_api_keys({'api_key': 'primary-key'})
        self.assertEqual(keys, ['primary-key', 'secondary-key', 'third-key'])

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

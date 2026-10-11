from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.gemini_drafts.models import Draft
from apps.gemini_drafts.services import call_deepseek, generate_and_save
from apps.governance.models import CTM, WG


class DraftDeepSeekTests(TestCase):
    def setUp(self):
        self.ctm = CTM.objects.create(name='CTM Test', number=1, description='CTM de test')
        self.wg = WG.objects.create(ctm=self.ctm, name='WG Gouvernance', number=1, description='WG de gouvernance')

    @override_settings(DEEPSEEK_API_KEY='sk-test')
    @patch('apps.gemini_drafts.services.requests.post')
    def test_call_deepseek_parses_json_content(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': (
                        '{"ctm": "CTM Test", "wg": "WG Gouvernance", '
                        '"document_type": "guide", "classification_reason": "x", '
                        '"draft_text": "Draft"}'
                    ),
                }
            }]
        }

        result = call_deepseek('prompt')

        self.assertEqual(result['ctm'], 'CTM Test')
        self.assertEqual(result['wg'], 'WG Gouvernance')

    @patch('apps.gemini_drafts.services.call_deepseek')
    def test_generate_and_save_uses_llm_selected_ctm_and_wg(self, mock_call_deepseek):
        mock_call_deepseek.return_value = {
            'ctm': 'CTM Test',
            'wg': 'WG Gouvernance',
            'document_type': 'guide',
            'classification_reason': 'Le contenu concerne la gouvernance',
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

import sys
import types
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.ia_agent.services.agent_runner import AgentRunner
from apps.ia_agent.services.llm_client import LLMResponse, get_llm_client
from apps.ia_agent.services.regulatory_advice import generate_regulatory_advice


class FakeResponse:
    def __init__(self, text):
        self.candidates = [types.SimpleNamespace(content=types.SimpleNamespace(parts=[types.SimpleNamespace(text=text, thought=False)]))]


class RegulatoryAdviceServiceTests(SimpleTestCase):

    @patch('apps.ia_agent.services.regulatory_advice.get_llm_client')
    def test_generate_regulatory_advice_parses_gemini_response(self, mock_get_llm_client):
        class DummyLLM:
            def complete(self, system, messages, tools_spec, force_tool=False):
                return LLMResponse(
                    stop_reason='end_turn',
                    text=(
                        'Explication : Le texte actuel est trop verbeux et manque de clarté réglementaire.\n'
                        'Proposition : Respecter les prescriptions de style CTM et remplacer les tournures passives.'
                    )
                )

        mock_get_llm_client.return_value = DummyLLM()

        result = generate_regulatory_advice('Texte de test.')

        self.assertTrue(result['success'])
        self.assertEqual(result['provider'], 'gemini')
        self.assertIn('Le texte actuel est trop verbeux', result['explanation'])
        self.assertIn('Respecter les prescriptions de style CTM', result['proposal'])

    @patch('apps.ia_agent.services.regulatory_advice.get_llm_client')
    def test_generate_regulatory_advice_falls_back_when_llm_fails(self, mock_get_llm_client):
        class FailingLLM:
            def complete(self, system, messages, tools_spec, force_tool=False):
                raise RuntimeError('quota exceeded')

        mock_get_llm_client.return_value = FailingLLM()

        result = generate_regulatory_advice('Texte de test à reformuler.')

        self.assertTrue(result['success'])
        self.assertIn('reformulation', result['explanation'].lower())
        self.assertIn('Texte de test à reformuler.', result['proposal'])

    @override_settings(GEMINI_API_KEY='fake-key')
    def test_get_llm_client_routes_claude_requests_to_gemini(self):
        fake_google = types.SimpleNamespace(
            genai=types.SimpleNamespace(Client=lambda api_key: object())
        )
        with patch.dict(sys.modules, {'google': fake_google, 'google.genai': fake_google.genai}):
            client = get_llm_client('anthropic')

        self.assertIsNotNone(client)
        self.assertEqual(client.__class__.__name__, 'GeminiLLMClient')

    @override_settings(GEMINI_API_KEY='primary-key')
    def test_get_llm_client_tries_fallback_api_keys(self):
        created_clients = []
        responses = iter([
            RuntimeError('quota exceeded'),
            RuntimeError('quota exceeded'),
            FakeResponse('ok'),
        ])

        class FakeClient:
            def __init__(self, api_key):
                created_clients.append(api_key)
                self.models = types.SimpleNamespace(generate_content=self._generate_content)

            def _generate_content(self, model, contents, config):
                result = next(responses)
                if isinstance(result, Exception):
                    raise result
                return result

        fake_google = types.SimpleNamespace(genai=types.SimpleNamespace(Client=FakeClient))
        with patch.dict(sys.modules, {'google': fake_google, 'google.genai': fake_google.genai}):
            client = get_llm_client('gemini')
            result = client.complete('system', [{'role': 'user', 'content': 'hello'}], None)

        self.assertEqual(result.text, 'ok')
        self.assertEqual(created_clients[0], 'primary-key')
        self.assertIn('AQ.Ab8RN6L-txn_UETGeAnv4IYWDW7c8HC1oFY5vlyPvFclp61_ZQ', created_clients)

    @patch('apps.ia_agent.services.agent_runner.AgentMessage.objects.create')
    @patch('apps.ia_agent.services.agent_runner._cl')
    def test_agent_runner_returns_fallback_message_when_llm_fails(self, mock_cl, mock_create):
        class DummySession:
            provider = 'gemini'
            scope = 'expert'
            user = types.SimpleNamespace(id=1)

        class FailingLLM:
            def complete(self, system, messages, tools_spec, force_tool=False):
                raise RuntimeError('quota exceeded')

            def build_assistant_message(self, raw_content):
                return raw_content

            def build_tool_result_message(self, tool_results):
                return tool_results

        runner = AgentRunner(DummySession())
        result = runner._run_loop(FailingLLM(), 'system prompt', [], [])

        self.assertIsNotNone(result)
        self.assertEqual(mock_create.call_args.kwargs['role'], 'assistant')
        self.assertIn('indisponible', mock_create.call_args.kwargs['content'].lower())

    def test_generate_regulatory_advice_rejects_empty_text(self):
        result = generate_regulatory_advice('   ')
        self.assertFalse(result['success'])
        self.assertIn('Aucun texte', result['error'])

import types
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.ia_agent.services import llm_client as llm_module
from apps.ia_agent.services.agent_runner import AgentRunner
from apps.ia_agent.services.llm_client import (
    DeepSeekError,
    DeepSeekLLMClient,
    LLMResponse,
    api_error_message,
    get_llm_client,
)
from apps.ia_agent.services.regulatory_advice import generate_regulatory_advice


class RegulatoryAdviceServiceTests(SimpleTestCase):

    @patch('apps.ia_agent.services.regulatory_advice.get_llm_client')
    def test_generate_regulatory_advice_parses_response(self, mock_get_llm_client):
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
        self.assertEqual(result['provider'], 'deepseek')
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

    def test_generate_regulatory_advice_rejects_empty_text(self):
        result = generate_regulatory_advice('   ')
        self.assertFalse(result['success'])
        self.assertIn('Aucun texte', result['error'])


class DeepSeekClientTests(SimpleTestCase):

    def setUp(self):
        llm_module._client = None
        llm_module._client_cache_key = None

    @override_settings(DEEPSEEK_API_KEY='')
    def test_get_llm_client_returns_none_without_key(self):
        self.assertIsNone(get_llm_client('deepseek'))

    @override_settings(DEEPSEEK_API_KEY='sk-test', DEEPSEEK_MODEL='deepseek-chat')
    def test_get_llm_client_returns_deepseek_client(self):
        client = get_llm_client('deepseek')
        self.assertIsNotNone(client)
        self.assertEqual(client.__class__.__name__, 'DeepSeekLLMClient')
        self.assertEqual(client._model, 'deepseek-chat')

    def test_parse_response_with_tool_calls(self):
        data = {
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': None,
                    'tool_calls': [
                        {
                            'id': 'call_1',
                            'type': 'function',
                            'function': {
                                'name': 'get_chart_data',
                                'arguments': '{"metric": "normes_by_status"}',
                            },
                        }
                    ],
                },
                'finish_reason': 'tool_calls',
            }]
        }
        response = DeepSeekLLMClient._parse_response(data)
        self.assertEqual(response.stop_reason, 'tool_use')
        self.assertEqual(len(response.tool_calls), 1)
        self.assertEqual(response.tool_calls[0].name, 'get_chart_data')
        self.assertEqual(response.tool_calls[0].input, {'metric': 'normes_by_status'})

    def test_parse_response_plain_text(self):
        data = {
            'choices': [{
                'message': {'role': 'assistant', 'content': 'Bonjour'},
                'finish_reason': 'stop',
            }]
        }
        response = DeepSeekLLMClient._parse_response(data)
        self.assertEqual(response.stop_reason, 'end_turn')
        self.assertEqual(response.text, 'Bonjour')

    def test_build_tool_result_message(self):
        client = DeepSeekLLMClient(api_key='sk-test')
        messages = client.build_tool_result_message([
            {'id': 'call_1', 'name': 'get_chart_data', 'content': '{"ok": true}'},
        ])
        self.assertEqual(
            messages,
            [{'role': 'tool', 'tool_call_id': 'call_1', 'content': '{"ok": true}'}],
        )

    def test_api_error_message_for_insufficient_balance(self):
        self.assertIn('Solde DeepSeek', api_error_message(DeepSeekError('402 : insufficient balance')))

    def test_api_error_message_for_invalid_key(self):
        self.assertIn('Clé API DeepSeek', api_error_message(DeepSeekError('401 : invalid_api_key')))


class AgentRunnerFallbackTests(SimpleTestCase):

    @patch('apps.ia_agent.services.agent_runner.AgentMessage.objects.create')
    @patch('apps.ia_agent.services.agent_runner._cl')
    def test_agent_runner_returns_fallback_message_when_llm_fails(self, mock_cl, mock_create):
        class DummySession:
            provider = 'deepseek'
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

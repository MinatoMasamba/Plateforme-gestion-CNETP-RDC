"""Tests de l'assistant IA en mode « correction ciblée » (ligne / colonne)."""
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.ia_agent.services.llm_client import LLMResponse
from apps.ia_agent.services.regulatory_advice import generate_regulatory_advice
from apps.ia_agent.services.targeted_edits import (
    apply_edits,
    build_edits_from_proposal,
    parse_targeted_json,
)


class ParseTargetedJsonTests(SimpleTestCase):
    def test_parses_plain_json(self):
        raw = '{"summary": "ok", "edits": [{"find": "a", "replace": "b", "reason": "r"}]}'
        summary, edits = parse_targeted_json(raw)
        self.assertEqual(summary, 'ok')
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0]['find'], 'a')

    def test_parses_code_fenced_json(self):
        raw = '```json\n{"summary": "ok", "edits": []}\n```'
        summary, edits = parse_targeted_json(raw)
        self.assertEqual(summary, 'ok')
        self.assertEqual(edits, [])

    def test_returns_none_for_free_text(self):
        summary, edits = parse_targeted_json('Proposition : tout réécrire')
        self.assertIsNone(summary)
        self.assertIsNone(edits)


class BuildEditsFromProposalTests(SimpleTestCase):
    def test_only_changed_line_is_targeted(self):
        original = "Ligne 1 : stable.\nLigne 2 : faute.\nLigne 3 : stable."
        proposal = "Ligne 1 : stable.\nLigne 2 : corrigée.\nLigne 3 : stable."
        edits = build_edits_from_proposal(original, proposal)
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0]['find'], "Ligne 2 : faute.")
        self.assertEqual(edits[0]['replace'], "Ligne 2 : corrigée.")

    def test_identical_text_produces_no_edit(self):
        text = "Texte identique."
        self.assertEqual(build_edits_from_proposal(text, text), [])


class ApplyEditsTests(SimpleTestCase):
    def test_exact_match_applied(self):
        text = "Ligne 1 : faute.\nLigne 2 : ok."
        applied, annotated = apply_edits(
            text, [{"find": "Ligne 1 : faute.", "replace": "Ligne 1 : correct.", "reason": "r"}])
        self.assertEqual(applied, "Ligne 1 : correct.\nLigne 2 : ok.")
        self.assertTrue(annotated[0]['applied'])

    def test_tolerant_whitespace_match(self):
        text = "Section   2   :   objet"
        applied, annotated = apply_edits(
            text, [{"find": "Section 2 : objet", "replace": "Section 2 : objet corrigé", "reason": "r"}])
        self.assertEqual(applied, "Section 2 : objet corrigé")
        self.assertTrue(annotated[0]['applied'])

    def test_not_found_marked_unapplied(self):
        _, annotated = apply_edits(
            "abc", [{"find": "zzz", "replace": "yyy", "reason": "r"}])
        self.assertFalse(annotated[0]['applied'])


class GenerateRegulatoryAdviceTargetedTests(SimpleTestCase):
    @patch('apps.ia_agent.services.regulatory_advice.get_llm_client')
    def test_targeted_json_returns_minimal_edits(self, mock_get):
        class DummyLLM:
            def complete(self, system, messages, tools_spec, force_tool=False):
                return LLMResponse(
                    stop_reason='end_turn',
                    text=('{"summary": "1 correction", "edits": ['
                          '{"find": "Ligne 2 : faute.", "replace": "Ligne 2 : corrigée.", '
                          '"reason": "orthographe"}]}'),
                )

        mock_get.return_value = DummyLLM()
        original = "Ligne 1 : stable.\nLigne 2 : faute.\nLigne 3 : stable."
        result = generate_regulatory_advice(original)

        self.assertTrue(result['success'])
        self.assertFalse(result.get('fallback'))
        self.assertEqual(len(result['edits']), 1)
        self.assertTrue(result['edits'][0]['applied'])
        self.assertIn('Ligne 2 : corrigée.', result['applied_text'])
        self.assertIn('Ligne 1 : stable.', result['applied_text'])

    @patch('apps.ia_agent.services.regulatory_advice.get_llm_client')
    def test_free_text_response_is_diffed_line_by_line(self, mock_get):
        class DummyLLM:
            def complete(self, system, messages, tools_spec, force_tool=False):
                return LLMResponse(
                    stop_reason='end_turn',
                    text=('Proposition : Ligne 1 : stable.\nLigne 2 : corrigée.\nLigne 3 : stable.'),
                )

        mock_get.return_value = DummyLLM()
        original = "Ligne 1 : stable.\nLigne 2 : faute.\nLigne 3 : stable."
        result = generate_regulatory_advice(original)

        self.assertTrue(result['success'])
        self.assertEqual(len(result['edits']), 1)
        self.assertEqual(result['edits'][0]['find'], "Ligne 2 : faute.")

import pathlib
import tempfile
from unittest.mock import patch

from django.test import SimpleTestCase
from reportlab.pdfgen import canvas

from apps.ia_agent.tools import referential_tools


def _write_pdf(path, text):
    c = canvas.Canvas(str(path))
    c.drawString(72, 720, text)
    c.save()


class SearchExtendedReferentialsTests(SimpleTestCase):

    def tearDown(self):
        referential_tools._load_external_dir_chunks.cache_clear()

    def test_unknown_referentiel_returns_error(self):
        result = referential_tools.search_extended_referentials(None, 'flexion', 'inconnu')
        self.assertIn('error', result)

    def test_empty_directory_reports_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty_dir = pathlib.Path(tmp)
            with patch.dict(referential_tools.EXTERNAL_REFERENTIAL_DIRS, {'eurocodes': empty_dir}):
                referential_tools._load_external_dir_chunks.cache_clear()
                result = referential_tools.search_extended_referentials(None, 'flexion', 'eurocodes')

        self.assertEqual(result['available'], False)
        self.assertEqual(result['referentiel'], 'eurocodes')
        self.assertIn('README', result['message'])

    def test_deposited_pdf_becomes_searchable(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            _write_pdf(
                directory / "eurocode2_flexion_beton.pdf",
                "Calcul de flexion du beton arme selon les regles de dimensionnement Eurocode 2",
            )

            with patch.dict(referential_tools.EXTERNAL_REFERENTIAL_DIRS, {'eurocodes': directory}):
                referential_tools._load_external_dir_chunks.cache_clear()
                result = referential_tools.search_extended_referentials(None, 'flexion beton', 'eurocodes')

        self.assertEqual(result['available'], True)
        self.assertGreaterEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['source'], 'eurocodes')

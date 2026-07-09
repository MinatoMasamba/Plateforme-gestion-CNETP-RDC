import json
import tempfile
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.governance.models import CTM, WG
from apps.norms.models import Norme, NormeDocumentImport


class NormeDocumentImportGovernanceTests(TestCase):
    def setUp(self):
        self.ctm_normalisation = CTM.objects.create(
            name='Sciences des Matériaux, Métrologie et Valorisation Locale',
            number=8,
            description='Normalisation et métrologie',
        )
        self.wg_normalisation = WG.objects.create(
            ctm=self.ctm_normalisation,
            name='Normalisation Appliquée',
            number=4,
            description='Règles de gouvernance et rédaction',
        )

    def test_import_assigns_guide_to_normalisation_wg(self):
        payload = [{
            'filename': 'GUIDE GOUVERNANCE ET DE REDACCTION DES NORMES.docx',
            'path': 'norme/GUIDE GOUVERNANCE ET DE REDACCTION DES NORMES.docx',
            'document_type': 'guide',
            'paragraph_count': 12,
            'payload': {
                'parts': [
                    {'content': ['gouvernance', 'rédaction', 'normalisation']}
                ]
            },
        }]

        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as handle:
            json.dump(payload, handle)
            temp_path = handle.name

        try:
            call_command(
                'import_norme_documents_json',
                input=temp_path,
                stdout=StringIO(),
                stderr=StringIO(),
            )
        finally:
            import os
            os.remove(temp_path)

        import_record = NormeDocumentImport.objects.get(filename='GUIDE GOUVERNANCE ET DE REDACCTION DES NORMES.docx')
        self.assertTrue(import_record.norme_id)
        self.assertEqual(import_record.norme.ctm, self.ctm_normalisation)
        self.assertEqual(import_record.norme.wg, self.wg_normalisation)
        self.assertTrue(Norme.objects.filter(reference_number='NORME-GUIDE-001').exists())

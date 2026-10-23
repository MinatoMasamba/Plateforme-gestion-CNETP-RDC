from io import BytesIO
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from apps.documents.models import DocumentFile


class IntelligenceAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user('staff-centre', password='test-pass', is_staff=True)
        cls.expert = get_user_model().objects.create_user('expert-centre', password='test-pass', is_expert=True)

    def test_anonymous_and_unrelated_expert_cannot_read_centre_or_ajax(self):
        for url in (reverse('dashboard:index'), reverse('dashboard:intelligence'), reverse('dashboard:expert_activity_report'), reverse('dashboard:ajax_structure', args=[1])):
            self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.expert)
        for url in (reverse('dashboard:index'), reverse('dashboard:intelligence'), reverse('dashboard:expert_activity_report'), reverse('dashboard:ajax_structure', args=[1])):
            self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(reverse('dashboard:intelligence_assistant'), {'question': 'experts'}).status_code, 403)
        self.assertEqual(self.client.get(reverse('dashboard:intelligence_report_word')).status_code, 403)

    def test_staff_can_read_all_sections_and_export_word(self):
        self.client.force_login(self.staff)
        for section in ('vue', 'organisation', 'experts', 'production', 'documents', 'observations', 'rapports'):
            with self.subTest(section=section):
                response = self.client.get(reverse('dashboard:intelligence'), {'section': section})
                self.assertEqual(response.status_code, 200)
        answer = self.client.post(reverse('dashboard:intelligence_assistant'), {'question': 'Combien d’experts ?'})
        self.assertEqual(answer.status_code, 200)
        self.assertIn('sources', answer.json())
        comparison = self.client.post(reverse('dashboard:intelligence_assistant'), {'question': 'Compare les sept sous-commissions'})
        self.assertEqual(comparison.status_code, 200)
        self.assertEqual(comparison.json()['chart']['type'], 'bar')
        export = self.client.get(reverse('dashboard:intelligence_report_word'))
        self.assertEqual(export.status_code, 200)
        with ZipFile(BytesIO(export.content)) as package:
            self.assertIn('word/document.xml', package.namelist())
            self.assertIn(b'Cabinet du ministre', package.read('word/document.xml'))
        detailed = self.client.get(reverse('dashboard:expert_activity_report'))
        self.assertEqual(detailed.status_code, 200)
        self.assertContains(detailed, "Rapport d'activité des experts")

    def test_private_document_media_url_is_guarded(self):
        DocumentFile.objects.create(uploaded_by=self.staff, file='documents/test-private.pdf', title='Privé')
        url = '/media/documents/test-private.pdf'
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.expert)
        self.assertEqual(self.client.get(url).status_code, 403)

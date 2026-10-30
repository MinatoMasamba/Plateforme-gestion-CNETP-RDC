from datetime import timedelta
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core.models import User
from apps.experts.models import Expert, Structure
from apps.governance.models import ActivityAccessLog, ActivitySession, CTCMembership, TechnicalCell
from apps.norms.models import Norme, NormeVersion


class CTCExpertDetailTests(TestCase):
    def setUp(self):
        structure = Structure.objects.create(name='Institution', acronym='ITP', category='ADMIN')
        self.viewer = User.objects.create_user(username='coord', password='Test123!')
        member = Expert.objects.create(user=self.viewer, structure=structure)
        CTCMembership.objects.create(ctc=TechnicalCell.objects.create(name='CTC'), expert=member, role='COORDINATOR')
        self.target = Expert.objects.create(user=User.objects.create_user(username='auteur'), structure=structure,
                                           specialties='Géotechnique', status='ACTIVE')
        self.norm = Norme.all_objects.create(reference_number='DETAIL-1', title='Norme de contrôle',
                                            circuit_version='PHOENIX')
        self.version = NormeVersion.all_objects.create(norme=self.norm, version_number=1, title='V1',
            content='Version précise de cet auteur', version_author=self.target.user, summary='Correction des méthodes')
        NormeVersion.all_objects.create(norme=self.norm, version_number=2, title='V2',
                                       content='Autre auteur', version_author=self.viewer)
        ActivitySession.objects.create(user=self.target.user, device_id='test', last_seen_at=timezone.now(), active_seconds=3661)
        self.client.force_login(self.viewer)

    def test_profile_shows_own_editions_time_skills_and_exact_version_link(self):
        response = self.client.get(reverse('web:ctc_expert_detail', args=[self.target.pk]))
        self.assertContains(response, 'Géotechnique')
        self.assertContains(response, '1 h 01 min 01 s')
        self.assertContains(response, f'?version={self.version.pk}')
        self.assertContains(response, 'Correction des méthodes')
        self.assertNotContains(response, 'Autre auteur')
        self.assertTrue(ActivityAccessLog.objects.filter(viewer=self.viewer, target_expert=self.target).exists())
        reader = self.client.get(reverse('web:ctc_norme_read', args=[self.norm.pk]), {'version': self.version.pk})
        self.assertEqual(reader.context['latest_version'].pk, self.version.pk)

    def test_ctc_without_contribution_permission_cannot_see_time_or_editions(self):
        CTCMembership.objects.filter(expert__user=self.viewer).update(role='IT_ADMIN')
        response = self.client.get(reverse('web:ctc_expert_detail', args=[self.target.pk]))
        self.assertContains(response, 'Géotechnique')
        self.assertNotContains(response, 'Correction des méthodes')
        self.assertNotContains(response, '1 h 01 min')

    def test_non_ctc_and_anonymous_cannot_read_profile_or_cv(self):
        urls = [reverse('web:ctc_expert_detail', args=[self.target.pk]), reverse('web:ctc_expert_cv', args=[self.target.pk])]
        self.client.force_login(self.target.user)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_cv_protected_stream_and_missing_file(self):
        url = reverse('web:ctc_expert_cv', args=[self.target.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            self.target.cv = SimpleUploadedFile('cv.pdf', b'%PDF-1.4 CV')
            self.target.save()
            response = self.client.get(url)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertIn('inline', response['Content-Disposition'])
            self.assertIn('no-store', response['Cache-Control'])
            self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4 CV')
            self.target.cv.storage.delete(self.target.cv.name)
            self.assertEqual(self.client.get(url).status_code, 404)

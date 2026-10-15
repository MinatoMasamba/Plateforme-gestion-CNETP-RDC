"""CTC statistics stay inside explicit group scopes."""
from django.test import TestCase
from django.template.loader import render_to_string

from apps.governance.models import GroupeCible, Organe, OrganisationVersion, Tache
from web.ctc_statistics import build_ctc_statistics


class CTCStatisticsTests(TestCase):
    def test_current_sc_performance_excludes_other_sc_tasks_and_keeps_empty_group_unconfigured(self):
        version = OrganisationVersion.objects.create(code='ctc-stat-test', name='Test', source_document='Test')
        first = Organe.objects.create(version=version, code='SC-A', name='Alpha', type='SC', status='VALIDATED', source_reference='Test')
        second = Organe.objects.create(version=version, code='SC-B', name='Bêta', type='SC', source_reference='Test')
        a_group = GroupeCible.objects.create(sc=first, code='GT-A', name='Alpha groupe', activity='PRODUCTION', source_reference='Test')
        empty_group = GroupeCible.objects.create(sc=first, code='GT-V', name='Groupe vide', activity='PRODUCTION', source_reference='Test')
        b_group = GroupeCible.objects.create(sc=second, code='GT-B', name='Bêta groupe', activity='PRODUCTION', source_reference='Test')
        Tache.objects.create(target_group=a_group, titre='Travail A', weight=1, progress=100)
        Tache.objects.create(target_group=b_group, titre='Travail B', weight=5, progress=0)

        result = build_ctc_statistics()
        a = next(row for row in result['rows'] if row['code'] == 'SC-A')
        b = next(row for row in result['rows'] if row['code'] == 'SC-B')
        self.assertEqual(a['performance'], 100)
        self.assertEqual(a['status'], 'Proposée')
        self.assertEqual(b['performance'], 0)
        self.assertIsNone(next(group for group in a['groups'] if group['code'] == 'GT-V')['performance'])
        self.assertEqual(result['task_count'], 2)
        self.assertEqual(result['global_performance'], 16.7)

        html = render_to_string('ctc/app/components/statistiques_view.html', {'ctc_statistics': result, 'ctc_can_view_task_sources': True})
        self.assertIn('Non configuré', html)
        self.assertIn('Travail A', html)
        self.assertNotIn('/pilotage/', html)
        restricted_html = render_to_string('ctc/app/components/statistiques_view.html', {'ctc_statistics': result, 'ctc_can_view_task_sources': False})
        self.assertNotIn('Travail A', restricted_html)

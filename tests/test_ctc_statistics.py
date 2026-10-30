"""CTC statistics stay inside explicit group scopes."""
from django.test import TestCase
from django.template.loader import render_to_string

from apps.governance.models import CTM, WG, CorrespondanceGroupe, GroupeCible, Organe, OrganisationVersion, Tache
from apps.norms.models import Norme
from django.urls import reverse
from web.ctc_statistics import build_ctc_statistics


class CTCStatisticsTests(TestCase):
    def test_direct_sc_tasks_count_for_the_sc_without_assigning_them_to_a_wg(self):
        version = OrganisationVersion.objects.create(code='direct-sc-test', name='Test', source_document='Test')
        sc = Organe.objects.create(version=version, code='SC-BAT', name='Bâtiments', type='SC', source_reference='Test')
        ctm = CTM.objects.create(number=1, name='Bâtiments')
        WG.objects.create(ctm=ctm, number=1, name='Conception')
        Tache.objects.create(target_sc=sc, titre='Dossier direct', weight=2, progress=25)
        result = build_ctc_statistics()
        row = result['rows'][0]
        self.assertEqual(row['task_count'], 1)
        self.assertEqual(row['performance'], 25)
        self.assertEqual(result['task_count'], 1)
        self.assertIsNone(row['groups'][0]['performance'])
        self.assertEqual(result['global_performance'], 25)

    def test_target_group_task_needs_validated_group_correspondence(self):
        version = OrganisationVersion.objects.create(code='ctc-task-link', name='Test', source_document='Test')
        sc = Organe.objects.create(version=version, code='SC-T', name='Test', type='SC', source_reference='Test')
        gt = GroupeCible.objects.create(sc=sc, code='GT-T', name='GT test',
                                        source_reference='Test', activity='PRODUCTION')
        ctm = CTM.objects.create(name='CTM test', number=1)
        wg = WG.objects.create(ctm=ctm, name='WG test', number=1)
        Tache.objects.create(target_group=gt, titre='Tâche à rattacher')

        self.assertEqual(build_ctc_statistics()['task_count'], 0)
        CorrespondanceGroupe.objects.create(version=version, wg=wg, sc=sc, gt=gt,
                                            status='VALIDATED', source_reference='Test', domain='Test',
                                            decision_reference='Test')
        self.assertEqual(build_ctc_statistics()['task_count'], 1)

    def test_group_navigation_has_unique_panels_and_norm_read_links(self):
        ctm = CTM.objects.create(name='CTM lecture', number=1)
        group = WG.objects.create(pk=ctm.pk, ctm=ctm, name='Groupe lecture', number=1)
        norme = Norme.objects.create(
            ctm=ctm, wg=group, title='Norme à consulter', reference_number='CTC-LECTURE-001',
        )

        result = build_ctc_statistics()
        panel_ids = [row['id'] for row in result['rows']]
        panel_ids.extend(group['id'] for row in result['rows'] for group in row['groups'])
        self.assertEqual(len(panel_ids), len(set(panel_ids)))
        html = render_to_string('ctc/app/components/statistiques_view.html', {'ctc_statistics': result})
        self.assertIn(f'data-ctc-stat-target="wg-{group.pk}"', html)
        self.assertIn(f'data-ctc-stat-panel="wg-{group.pk}"', html)
        self.assertIn(
            f'href="{reverse("web:ctc_norme_read", args=[norme.pk])}" '
            'target="_blank" rel="noopener noreferrer"', html,
        )

    def test_ctm_performance_excludes_other_ctm_tasks_and_keeps_empty_group_unconfigured(self):
        version = OrganisationVersion.objects.create(code='ctc-stat-test', name='Test', source_document='Test')
        first = Organe.objects.create(version=version, code='SC-A', name='Alpha', type='SC', status='VALIDATED', source_reference='Test')
        second = Organe.objects.create(version=version, code='SC-B', name='Bêta', type='SC', source_reference='Test')
        a_group = GroupeCible.objects.create(sc=first, code='GT-A', name='Alpha groupe', activity='PRODUCTION', source_reference='Test')
        empty_group = GroupeCible.objects.create(sc=first, code='GT-V', name='Groupe vide', activity='PRODUCTION', source_reference='Test')
        b_group = GroupeCible.objects.create(sc=second, code='GT-B', name='Bêta groupe', activity='PRODUCTION', source_reference='Test')
        first_ctm = CTM.objects.create(name='Alpha', number=1)
        second_ctm = CTM.objects.create(name='Bêta', number=2)
        first_wg = WG.objects.create(ctm=first_ctm, name='Alpha groupe', number=1)
        empty_wg = WG.objects.create(ctm=first_ctm, name='Groupe vide', number=2)
        second_wg = WG.objects.create(ctm=second_ctm, name='Bêta groupe', number=1)
        Tache.objects.create(working_group=first_wg, target_group=a_group, titre='Travail A', weight=1, progress=100)
        Tache.objects.create(working_group=second_wg, target_group=b_group, titre='Travail B', weight=5, progress=0)
        Tache.objects.create(target_group=empty_group, titre='Hors périmètre WG', weight=10, progress=0)

        result = build_ctc_statistics()
        a = next(row for row in result['rows'] if row['code'] == 'CTM 1')
        b = next(row for row in result['rows'] if row['code'] == 'CTM 2')
        self.assertEqual(a['performance'], 100)
        self.assertEqual(a['status'], 'Actif')
        self.assertEqual(b['performance'], 0)
        self.assertIsNone(next(group for group in a['groups'] if group['id'] == f'wg-{empty_wg.pk}')['performance'])
        self.assertEqual(result['task_count'], 2)
        self.assertEqual(result['global_performance'], 16.7)

        html = render_to_string('ctc/app/components/statistiques_view.html', {'ctc_statistics': result, 'ctc_can_view_task_sources': True})
        self.assertIn('Aucune tâche pondérée', html)
        self.assertIn('Travail A', html)
        self.assertNotIn('/pilotage/', html)
        restricted_html = render_to_string('ctc/app/components/statistiques_view.html', {'ctc_statistics': result, 'ctc_can_view_task_sources': False})
        self.assertNotIn('Travail A', restricted_html)

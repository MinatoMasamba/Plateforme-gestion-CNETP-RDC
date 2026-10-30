from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.models import User
from apps.experts.models import Expert, Structure
from apps.governance.models import (
    CTCMembership, CTM, Organe, OrganisationVersion, Tache, TechnicalCell, WG,
)
from apps.norms.models import Norme, NormeVersion


class CTCSubcommissionTasksTests(TestCase):
    def setUp(self):
        self.version = OrganisationVersion.objects.create(code='ctc-sc-tasks', name='Organisation',
                                                          source_document='Test')
        self.sc = Organe.objects.create(version=self.version, code='SC-IT', name='Infrastructures de transport',
                                       type='SC', source_reference='Test')
        self.norm = Norme.all_objects.create(reference_number='NCD 104', title='Plateformes ferroviaires',
                                            description='Projet de travail', circuit_version='PHOENIX')

    def test_task_can_target_subcommission_without_unconfirmed_group(self):
        task = Tache(norme=self.norm, target_sc=self.sc, titre='Examiner le projet')
        task.full_clean()
        task.save()
        self.assertEqual(task.target_sc_id, self.sc.pk)
        self.assertIsNone(task.target_group_id)

        ctm = CTM.objects.create(number=1, name='CTM historique')
        wg = WG.objects.create(ctm=ctm, number=1, name='WG historique')
        task.working_group = wg
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_ctc_reader_opens_phoenix_draft_and_its_version(self):
        structure = Structure.objects.create(name='Service CTC', acronym='CTC', category='ADMIN')
        user = User.objects.create_user(username='membre@cne-itp.cd', email='membre@cne-itp.cd', password='Test123!')
        expert = Expert.objects.create(user=user, structure=structure, status='ACTIVE')
        ctc = TechnicalCell.objects.create(name='Cellule technique')
        CTCMembership.objects.create(ctc=ctc, expert=expert, role='COORDINATOR')
        NormeVersion.all_objects.create(norme=self.norm, version_number=1, title='Avant-projet',
                                        content='Contenu de la version 1', is_draft=True)

        self.client.force_login(user)
        response = self.client.get(f'/ctc/norme/{self.norm.pk}/lecture/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['latest_version'].version_number, 1)

        dashboard = self.client.get('/ctc/')
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.context['ctc_statistics']['catalogue_count'], 1)
        self.assertContains(dashboard, 'Catalogue des normes · 1')
        self.assertContains(dashboard, 'NCD 104')

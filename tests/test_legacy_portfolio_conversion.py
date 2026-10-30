from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.core.models import AuditLog
from apps.governance.models import CTM, WG
from apps.governance.catalogue import GT_CATALOGUE as CANONICAL
from apps.norms.management.commands.convert_requested_norms_to_legacy import PROJECT_GROUPS
from apps.norms.models import Norme, NormeVersion


class LegacyPortfolioConversionTests(TestCase):
    def setUp(self):
        for number in CANONICAL:
            ctm = CTM.objects.create(number=number, name=f'SC {number}')
            for group in range(1, 6):
                WG.objects.create(ctm=ctm, number=group, name=f'Ancien nom {number}.{group}')
        for ref in PROJECT_GROUPS:
            norm = Norme.all_objects.create(reference_number=ref, title=ref,
                                            description='Projet', circuit_version='PHOENIX')
            NormeVersion.all_objects.create(norme=norm, version_number=1, title=ref, content='Texte conservé')

    def test_conversion_preserves_versions_groups_and_is_idempotent(self):
        group_ids = set(WG.objects.values_list('pk', flat=True))
        call_command('convert_requested_norms_to_legacy', apply=True, stdout=StringIO())
        self.assertEqual(Norme.objects.count(), 8)
        self.assertEqual(NormeVersion.objects.count(), 8)
        self.assertEqual(set(WG.objects.values_list('pk', flat=True)), group_ids)
        for ref, (ctm, wg) in PROJECT_GROUPS.items():
            norm = Norme.objects.get(reference_number=ref)
            self.assertEqual((norm.ctm.number, norm.wg.number), (ctm, wg))
            self.assertEqual(norm.wg.name, CANONICAL[ctm][wg - 1])
        audits = AuditLog.objects.count()
        call_command('convert_requested_norms_to_legacy', apply=True, stdout=StringIO())
        self.assertEqual(AuditLog.objects.count(), audits)

    def test_missing_group_aborts_all_writes(self):
        WG.objects.filter(ctm__number=7, number=5).delete()
        with self.assertRaises(CommandError):
            call_command('convert_requested_norms_to_legacy', apply=True, stdout=StringIO())
        self.assertEqual(Norme.all_objects.filter(circuit_version='PHOENIX').count(), 8)
        self.assertEqual(WG.objects.get(ctm__number=1, number=1).name, 'Ancien nom 1.1')

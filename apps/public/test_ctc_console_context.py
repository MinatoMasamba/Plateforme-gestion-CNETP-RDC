from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.experts.models import Expert, Structure
from apps.governance.models import CTM, WG
from apps.norms.models import Norme
from apps.public.models import PublicAmendement
from web.ctc_views import _ctc_shared_context


class CTCPublicInquiryContextTests(TestCase):
    """
    Vérifie que _ctc_shared_context() (web/ctc_views.py) expose des statistiques
    d'enquête publique réelles, calculées à partir de PublicAmendement, au lieu
    des chiffres codés en dur qu'affichait auparavant le template CTC.
    """

    def setUp(self):
        user = get_user_model().objects.create_user(username="test-responsable-enquetes", password="x")
        structure = Structure.objects.create(name="Structure Test", acronym="TST", category='ADMIN')
        self.expert = Expert.objects.create(user=user, structure=structure)

        ctm = CTM.objects.create(name="Assainissement", number=7)
        wg = WG.objects.create(ctm=ctm, number=1, name="Réseaux pluviaux")
        norme = Norme.objects.create(
            title="Norme drainage", reference_number="CNETP-TEST-CTX-001",
            description="Desc", ctm=ctm, wg=wg, status='PUBLIC_INQUIRY',
        )

        PublicAmendement.objects.create(
            norme=norme, proposed_by_name="A", proposed_by_email="a@example.com",
            title="Amendement A", description="Desc A", status='PENDING',
        )
        PublicAmendement.objects.create(
            norme=norme, proposed_by_name="B", proposed_by_email="b@example.com",
            title="Amendement B", description="Desc B", status='ACCEPTED',
        )
        PublicAmendement.objects.create(
            norme=norme, proposed_by_name="C", proposed_by_email="c@example.com",
            title="Amendement C", description="Desc C", status='REJECTED',
        )

    @patch('web.ctc_views.get_ctc_context', return_value={})
    def test_context_exposes_real_public_inquiry_stats(self, mock_ctc_context):
        ctx = _ctc_shared_context(self.expert)

        self.assertIsNotNone(ctx)
        self.assertEqual(ctx['public_inquiry_stats']['total'], 3)
        self.assertEqual(ctx['public_inquiry_stats']['accepted'], 1)
        self.assertEqual(ctx['public_inquiry_stats']['rejected'], 1)
        self.assertEqual(ctx['public_inquiry_stats']['pending'], 1)
        self.assertEqual(len(ctx['public_inquiry_queue']), 1)
        self.assertEqual(ctx['public_inquiry_queue'][0].proposed_by_name, "A")

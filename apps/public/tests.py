from django.test import TestCase
from django.urls import reverse

from apps.governance.models import CTM, WG
from apps.norms.models import Norme

from .models import PublicAmendement


def _make_norme(status, reference_number):
    ctm = CTM.objects.create(name=f"CTM-{reference_number}", number=len(reference_number) % 8 + 1)
    wg = WG.objects.create(ctm=ctm, number=1, name="WG test")
    return Norme.objects.create(
        title="Norme de test enquête publique",
        reference_number=reference_number,
        description="Description de test",
        ctm=ctm, wg=wg, status=status,
    )


class PublicInquiryPortalTests(TestCase):

    def test_submission_accepted_when_norme_is_in_public_inquiry(self):
        norme = _make_norme('PUBLIC_INQUIRY', 'CNETP-TEST-PUB-001')

        response = self.client.post(
            reverse('public:inquiry_form', kwargs={'norme_id': norme.id}),
            data={
                'proposed_by_name': 'Jean Citoyen',
                'proposed_by_email': 'jean@example.com',
                'proposed_by_organization': '',
                'proposed_by_province': 'Kinshasa',
                'title': 'Renforcer le drainage',
                'description': "Il faudrait renforcer le drainage pluvial dans cette norme.",
                'justification': '',
            },
        )

        self.assertRedirects(response, reverse('public:inquiry_thanks', kwargs={'norme_id': norme.id}))
        self.assertEqual(PublicAmendement.objects.filter(norme=norme).count(), 1)
        amendement = PublicAmendement.objects.get(norme=norme)
        self.assertEqual(amendement.proposed_by_province, 'Kinshasa')

    def test_submission_rejected_when_norme_not_in_public_inquiry(self):
        norme = _make_norme('DRAFT', 'CNETP-TEST-PUB-002')

        response = self.client.post(
            reverse('public:inquiry_form', kwargs={'norme_id': norme.id}),
            data={
                'proposed_by_name': 'Jean Citoyen',
                'proposed_by_email': 'jean@example.com',
                'title': 'Amendement hors délai',
                'description': "Ceci ne devrait pas être accepté.",
            },
        )

        self.assertRedirects(response, reverse('public:inquiry_form', kwargs={'norme_id': norme.id}))
        self.assertEqual(PublicAmendement.objects.filter(norme=norme).count(), 0)

    def test_form_page_shows_closed_notice_when_not_open(self):
        norme = _make_norme('DRAFT', 'CNETP-TEST-PUB-003')

        response = self.client.get(reverse('public:inquiry_form', kwargs={'norme_id': norme.id}))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_open'])

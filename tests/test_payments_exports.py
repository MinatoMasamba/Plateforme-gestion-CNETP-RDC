"""Reçus PDF, contestations d'indemnités et export bancaire pain.001."""
from datetime import date
from decimal import Decimal
from xml.etree import ElementTree as ET

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.experts.models import Structure
from apps.meetings.models import Reunion
from apps.payments.models import Cotisation, JetonPresence, Paiement
from api.v1.payments.sepa import NAMESPACE

pytestmark = pytest.mark.django_db
JETONS = '/api/v1/jetons/'
PAIEMENTS = '/api/v1/paiements/'


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def _reunion(ctm, title='Session'):
    return Reunion.objects.create(
        type='CTM',
        titre=title,
        date=timezone.now(),
        ctm=ctm,
    )


def _jeton(expert, reunion, amount='100.00', status='PENDING'):
    return JetonPresence.objects.create(
        expert=expert,
        reunion=reunion,
        montant=Decimal(amount),
        status=status,
    )


@pytest.fixture
def cotisation(expert_factory):
    expert = expert_factory(
        bank_name='BCCDCDCD',
        bank_account='CD000000000000000000001',
    )
    cotisation = Cotisation.objects.create(
        structure=expert.structure,
        annee=2026,
        montant=Decimal('200.00'),
        due_date=date.today(),
    )
    paiement = Paiement.objects.create(
        cotisation=cotisation,
        montant=Decimal('75.00'),
        methode_paiement='VIREMENT',
        payment_date=date.today(),
        numero_transaction='TRX-001',
        status='CONFIRMED',
        confirmed_at=timezone.now(),
    )
    return expert, cotisation, paiement


def test_payment_receipt_pdf_is_downloadable(cotisation):
    expert, _, paiement = cotisation
    response = _client(expert.user).get(f'{PAIEMENTS}{paiement.pk}/receipt/')

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert f'recu-{paiement.numero_recu}.pdf' in response['Content-Disposition']
    assert response.content.startswith(b'%PDF')
    assert len(response.content) > 1000


def test_payment_receipt_requires_authentication(cotisation):
    _, _, paiement = cotisation
    assert APIClient().get(f'{PAIEMENTS}{paiement.pk}/receipt/').status_code in (401, 403)


def test_payment_receipt_is_limited_to_the_structure(
    cotisation,
    expert_factory,
    user_factory,
):
    _, _, paiement = cotisation
    other_structure = Structure.objects.create(
        name='Autre Structure',
        acronym='AUT',
        category='ADMIN',
    )
    other = expert_factory(
        user=user_factory(username='foreign-expert'),
        structure=other_structure,
    )
    response = _client(other.user).get(f'{PAIEMENTS}{paiement.pk}/receipt/')
    assert response.status_code == 403


def test_jeton_receipt_is_limited_to_owner_or_staff(
    expert_factory,
    user_factory,
    ctm_factory,
):
    owner = expert_factory()
    other = expert_factory(user=user_factory(username='other-beneficiary'))
    jeton = _jeton(owner, _reunion(ctm_factory()), status='PAID')
    url = f'{JETONS}{jeton.pk}/receipt/'

    assert APIClient().get(url).status_code in (401, 403)
    assert _client(other.user).get(url).status_code == 403

    own = _client(owner.user).get(url)
    assert own.status_code == 200
    assert own['Content-Type'] == 'application/pdf'
    assert f'indemnite-{jeton.pk}.pdf' in own['Content-Disposition']
    assert own.content.startswith(b'%PDF')

    staff = user_factory(username='ctc-receipt', is_ctc_staff=True)
    assert _client(staff).get(url).status_code == 200


def test_contestation_fields_are_read_only(
    expert_factory,
    user_factory,
    ctm_factory,
):
    expert = expert_factory()
    jeton = _jeton(expert, _reunion(ctm_factory()))
    staff = user_factory(username='ctc-patch', is_ctc_staff=True)

    response = _client(staff).patch(
        f'{JETONS}{jeton.pk}/',
        {
            'contestation_status': 'ACCEPTED',
            'contestation_motif': 'Écriture directe interdite',
            'contestation_resolution': 'Contournement',
        },
        format='json',
    )

    assert response.status_code == 200
    jeton.refresh_from_db()
    assert jeton.contestation_status == 'NONE'
    assert jeton.contestation_motif == ''
    assert jeton.contestation_resolution == ''


def test_expert_contests_own_indemnity(expert_factory, ctm_factory):
    expert = expert_factory(bank_name='BCCDCDCD', bank_account='CD000000000000000000001')
    jeton = _jeton(expert, _reunion(ctm_factory()))

    response = _client(expert.user).post(
        f'{JETONS}{jeton.pk}/contest/',
        {'motif': 'Montant différent de la session émargée'},
        format='json',
    )

    assert response.status_code == 200
    jeton.refresh_from_db()
    assert jeton.contestation_status == 'PENDING'
    assert jeton.contestation_motif.startswith('Montant différent')
    assert jeton.contestation_created_at is not None
    assert response.data['contestation_status'] == 'PENDING'


def test_contest_requires_owner_and_motif(expert_factory, user_factory, ctm_factory):
    owner = expert_factory()
    other = expert_factory(user=user_factory(username='other-expert'))
    jeton = _jeton(owner, _reunion(ctm_factory()))

    assert _client(other.user).post(
        f'{JETONS}{jeton.pk}/contest/',
        {'motif': 'Cette indemnité ne me revient pas'},
        format='json',
    ).status_code == 403
    assert _client(owner.user).post(
        f'{JETONS}{jeton.pk}/contest/',
        {'motif': 'court'},
        format='json',
    ).status_code == 400
    assert _client(owner.user).post(
        f'{JETONS}{jeton.pk}/contest/',
        {'motif': 'Montant incorrect pour cette session'},
        format='json',
    ).status_code == 200
    assert _client(owner.user).post(
        f'{JETONS}{jeton.pk}/contest/',
        {'motif': 'Deuxième contestation pendant instruction'},
        format='json',
    ).status_code == 400


def test_ctc_resolves_contestation(expert_factory, user_factory, ctm_factory):
    expert = expert_factory()
    jeton = _jeton(expert, _reunion(ctm_factory()))
    _client(expert.user).post(
        f'{JETONS}{jeton.pk}/contest/',
        {'motif': 'Le montant ne correspond pas au barème'},
        format='json',
    )
    staff = user_factory(username='ctc', is_ctc_staff=True)
    url = f'{JETONS}{jeton.pk}/resolve_contestation/'

    assert _client(expert.user).post(
        url,
        {'decision': 'ACCEPTED', 'resolution': 'Vérification effectuée'},
        format='json',
    ).status_code == 403
    assert _client(staff).post(
        url,
        {'decision': 'MAYBE', 'resolution': 'Vérification effectuée'},
        format='json',
    ).status_code == 400
    assert _client(staff).post(
        url,
        {'decision': 'ACCEPTED', 'resolution': ''},
        format='json',
    ).status_code == 400

    response = _client(staff).post(
        url,
        {'decision': 'ACCEPTED', 'resolution': 'Barème corrigé et validé'},
        format='json',
    )
    assert response.status_code == 200
    jeton.refresh_from_db()
    assert jeton.contestation_status == 'ACCEPTED'
    assert jeton.contestation_resolution == 'Barème corrigé et validé'
    assert jeton.contestation_resolved_by == staff
    assert jeton.contestation_resolved_at is not None


@pytest.fixture
def sepa_config(settings):
    settings.CNETP_SEPA_DEBTOR_NAME = 'CNETP'
    settings.CNETP_SEPA_DEBTOR_IBAN = 'CD000000000000000000000'
    settings.CNETP_SEPA_DEBTOR_BIC = 'BCCDCDCD'
    settings.CNETP_SEPA_CURRENCY = 'USD'


def test_sepa_export_contains_pending_jetons(
    expert_factory,
    user_factory,
    ctm_factory,
    sepa_config,
):
    ctm = ctm_factory()
    expert = expert_factory(
        bank_name='RAWBANK',
        bank_account='CD000000000000000000099',
    )
    expert.user.first_name = 'Amina'
    expert.user.last_name = 'Expert'
    expert.user.save(update_fields=['first_name', 'last_name'])
    jeton = _jeton(expert, _reunion(ctm, 'Session 1'), '100.00')
    paid = _jeton(expert, _reunion(ctm, 'Session 2'), '50.00', status='PAID')
    staff = user_factory(username='ctc-sepa', is_ctc_staff=True)

    response = _client(staff).get(f'{JETONS}sepa_export/')

    assert response.status_code == 200
    assert response['Content-Type'].startswith('application/xml')
    root = ET.fromstring(response.content)
    assert root.tag == f'{{{NAMESPACE}}}Document'
    namespace = {'p': NAMESPACE}
    assert root.findtext('.//p:NbOfTxs', namespaces=namespace) == '1'
    assert root.findtext('.//p:CtrlSum', namespaces=namespace) == '100.00'
    transactions = root.findall('.//p:CdtTrfTxInf', namespace)
    assert len(transactions) == 1
    assert transactions[0].findtext('p:PmtId/p:EndToEndId', namespaces=namespace) == f'JETON-{jeton.pk}'
    assert transactions[0].findtext('p:Cdtr/p:Nm', namespaces=namespace) == 'Amina Expert'
    assert transactions[0].findtext('p:CdtrAcct/p:Id/p:IBAN', namespaces=namespace) == 'CD000000000000000000099'
    assert f'JETON-{paid.pk}' not in response.content.decode()


def test_sepa_export_permissions_and_validation(
    expert_factory,
    user_factory,
    ctm_factory,
    sepa_config,
):
    ctm = ctm_factory()
    expert = expert_factory(bank_name='', bank_account='')
    jeton = _jeton(expert, _reunion(ctm))
    staff = user_factory(username='ctc-sepa-2', is_ctc_staff=True)
    url = f'{JETONS}sepa_export/'

    assert _client(expert.user).get(url).status_code == 403
    response = _client(staff).get(url)
    assert response.status_code == 400
    assert 'Coordonnées bancaires manquantes' in response.data['detail']

    expert.bank_name = 'BCCDCDCD'
    expert.bank_account = 'CD000000000000000000002'
    expert.save(update_fields=['bank_name', 'bank_account'])
    assert _client(staff).get(f'{url}?execution_date=2026-13-40').status_code == 400
    assert _client(staff).get(f'{url}?ids={jeton.pk},999999').status_code == 400
    selected = _client(staff).get(f'{url}?ids={jeton.pk}&execution_date=2026-05-01')
    assert selected.status_code == 200
    assert b'2026-05-01' in selected.content

    JetonPresence.objects.update(status='PAID')
    assert _client(staff).get(url).status_code == 400


def test_sepa_export_requires_debtor_configuration(
    expert_factory,
    user_factory,
    ctm_factory,
    settings,
):
    settings.CNETP_SEPA_DEBTOR_IBAN = ''
    settings.CNETP_SEPA_DEBTOR_BIC = ''
    expert = expert_factory(bank_name='BCCDCDCD', bank_account='CD000000000000000000003')
    _jeton(expert, _reunion(ctm_factory()))
    staff = user_factory(username='ctc-sepa-3', is_ctc_staff=True)

    response = _client(staff).get(f'{JETONS}sepa_export/')

    assert response.status_code == 400
    assert 'CNETP_SEPA_DEBTOR_IBAN' in response.data['detail']
    assert 'CNETP_SEPA_DEBTOR_BIC' in response.data['detail']

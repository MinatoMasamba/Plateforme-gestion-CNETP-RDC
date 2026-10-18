import pytest
from django.core import mail
from django.db import transaction
from django.utils import timezone

from apps.governance.models import (
    CTCMembership, CTM, ComitePilotage, ExecutiveLevel, MandatOrganisation, OrganisationVersion,
    Organe, PilotageMembreship, PosteNominatif, PosteNominatifCTC,
    PosteOrganisation, TechnicalCell, WG,
)
from apps.governance.phoenix_operations import configure


@pytest.mark.django_db(transaction=True)
def test_pilotage_exact_second_vice_president_title_and_single_email(expert_factory):
    expert = expert_factory()
    comite = ComitePilotage.objects.create(name='Comité de pilotage CNE-ITP')
    mail.outbox.clear()

    with transaction.atomic():
        comite.vice_president = expert
        comite.save(update_fields=['vice_president'])
        membership = PilotageMembreship.objects.create(
            comite=comite, expert=expert, role='VICE_PRESIDENT',
        )
        poste = PosteNominatif.objects.create(
            comite=comite, role='VICE_PRESIDENT', title='2ᵉ Vice-président du Comité de pilotage',
            holder=expert,
        )

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [expert.user.email]
    assert poste.title in mail.outbox[0].subject
    assert poste.title in mail.outbox[0].body
    assert comite.name in mail.outbox[0].body
    poste.order = 2
    poste.save(update_fields=['order'])
    membership.save(update_fields=['role'])
    assert len(mail.outbox) == 1


@pytest.mark.django_db(transaction=True)
def test_ctc_member_role_change_and_named_post(expert_factory):
    expert = expert_factory()
    ctc = TechnicalCell.objects.create(name='Cellule technique de coordination')
    mail.outbox.clear()

    membership = CTCMembership.objects.create(ctc=ctc, expert=expert, role='ISO_EXPERT')
    assert len(mail.outbox) == 1
    assert 'Expert Veille ISO' in mail.outbox[0].body
    membership.role = 'VICE_COORDINATOR'
    membership.save(update_fields=['role'])
    assert len(mail.outbox) == 2
    assert 'Vice-Coordonnateur' in mail.outbox[1].body

    poste = PosteNominatifCTC.objects.create(
        ctc=ctc, role='VICE_COORDINATOR', title='Coordonnateur adjoint du Secrétariat technique',
        holder=expert,
    )
    assert len(mail.outbox) == 3
    assert poste.title in mail.outbox[2].body


@pytest.mark.django_db(transaction=True)
def test_admin_leadership_fields_notify_only_new_holder(expert_factory):
    expert = expert_factory()
    comite = ComitePilotage.objects.create(name='COPIL')
    ctc = TechnicalCell.objects.create(name='Coordination ST')
    ctm = CTM.objects.create(number=1, name='Géotechnique', description='Travaux techniques')
    wg = WG.objects.create(ctm=ctm, number=1, name='Sols')
    mail.outbox.clear()

    comite.president = expert
    comite.save(update_fields=['president'])
    ctc.coordinator = expert
    ctc.save(update_fields=['coordinator'])
    ctm.scientific_president = expert
    ctm.save(update_fields=['scientific_president'])
    wg.president = expert
    wg.save(update_fields=['president'])
    assert len(mail.outbox) == 4
    assert 'Président du Comité de pilotage' in mail.outbox[0].body
    assert 'Coordonnateur de la Cellule technique' in mail.outbox[1].body
    assert 'Président scientifique' in mail.outbox[2].body
    assert 'Président' in mail.outbox[3].body

    comite.name = 'COPIL actualisé'
    comite.save(update_fields=['name'])
    ctc.save(update_fields=['coordinator'])
    assert len(mail.outbox) == 4


@pytest.mark.django_db(transaction=True)
def test_phoenix_proposal_waits_until_active_nomination(expert_factory):
    expert = expert_factory()
    version = OrganisationVersion.objects.create(
        code='notification-2026', name='Organisation CNE-ITP', source_document='Décision',
    )
    organe = Organe.objects.create(
        version=version, type='COPIL', code='COPIL', name='Comité de pilotage',
        official_name='Comité de pilotage CNE-ITP', status='VALIDATED', source_reference='Décision',
    )
    poste = PosteOrganisation.objects.create(
        organe=organe, code='VP2', category='PRESIDENCY',
        title='2ᵉ Vice-président', status='VALIDATED', source_reference='Décision',
    )
    mail.outbox.clear()
    mandat = MandatOrganisation.objects.create(expert=expert, poste=poste, status='PROPOSED')
    assert not mail.outbox

    mandat.function = '2ᵉ Vice-président'
    mandat.appointment_reference = 'Arrêté 2026/42'
    mandat.start_date = timezone.localdate()
    mandat.status = 'ACTIVE'
    mandat.save()
    assert len(mail.outbox) == 1
    assert poste.title in mail.outbox[0].body
    assert 'Arrêté 2026/42' in mail.outbox[0].body
    assert organe.official_name in mail.outbox[0].body
    mandat.function = 'Vice-présidence actualisée'
    mandat.save(update_fields=['function'])
    assert len(mail.outbox) == 1


@pytest.mark.django_db(transaction=True)
def test_rolled_back_nomination_does_not_send_mail(expert_factory):
    expert = expert_factory()
    comite = ComitePilotage.objects.create(name='COPIL')
    mail.outbox.clear()
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            PilotageMembreship.objects.create(comite=comite, expert=expert, role='PRESIDENT')
            raise RuntimeError('annulation')
    assert not mail.outbox


@pytest.mark.django_db(transaction=True)
def test_admin_membership_creation_sends_nomination_mail(client, expert_factory, user_factory):
    administrator = user_factory(username='nomination_admin', is_staff=True, is_superuser=True)
    expert = expert_factory()
    comite = ComitePilotage.objects.create(name='Comité de pilotage')
    mail.outbox.clear()
    client.force_login(administrator)

    response = client.post('/admin/governance/pilotagemembreship/add/', {
        'comite': comite.pk, 'expert': expert.pk, 'role': 'RAPPORTEUR', '_save': 'Enregistrer',
    })

    assert response.status_code == 302, response.content.decode()
    assert PilotageMembreship.objects.filter(comite=comite, expert=expert, role='RAPPORTEUR').exists()
    assert len(mail.outbox) == 1
    assert 'Rapporteur Général' in mail.outbox[0].body


@pytest.mark.django_db(transaction=True)
def test_official_expert_appointment_and_executive_position(expert_factory):
    expert = expert_factory()
    mail.outbox.clear()
    expert.appointment_decree_number = 'Arrêté 2026-115'
    expert.appointment_date = timezone.localdate()
    expert.save(update_fields=['appointment_decree_number', 'appointment_date'])
    assert len(mail.outbox) == 1
    assert 'Expert nommé' in mail.outbox[0].body
    assert 'Arrêté 2026-115' in mail.outbox[0].body

    ExecutiveLevel.objects.create(position='SG_ITP', expert=expert)
    assert len(mail.outbox) == 2
    assert 'Secrétaire Général aux ITP' in mail.outbox[1].body
    expert.save(update_fields=['appointment_date'])
    assert len(mail.outbox) == 2


@pytest.mark.django_db(transaction=True)
def test_organisation_app_activation_sends_nomination_mail(expert_factory, user_factory):
    manager = expert_factory(user=user_factory(username='nomination_manager'))
    recipient = expert_factory(user=user_factory(username='nomination_recipient'))
    committee = ComitePilotage.objects.create(name='COPIL')
    PilotageMembreship.objects.create(comite=committee, expert=manager, role='PRESIDENT')
    version = OrganisationVersion.objects.create(
        code='app-notification-2026', name='Organisation', source_document='Décision',
    )
    organ = Organe.objects.create(
        version=version, type='ST', code='ST', name='Secrétariat technique',
        official_name='Secrétariat technique de coordination',
        status='VALIDATED', source_reference='Décision',
    )
    poste = PosteOrganisation.objects.create(
        organe=organ, code='COORD', category='COORDINATION', title='Coordonnateur',
        status='VALIDATED', source_reference='Décision',
    )
    mail.outbox.clear()

    configure(manager.user, version, 'mandat', {
        'expert': recipient, 'poste': poste, 'groupe': None,
        'function': 'Coordonnateur', 'capacity': 'ORGANISATION',
        'appointment_reference': 'Décision ST-12', 'start_date': timezone.localdate(),
        'end_date': None, 'status': 'ACTIVE',
    })

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [recipient.user.email]
    assert 'Coordonnateur' in mail.outbox[0].body
    assert 'Secrétariat technique de coordination' in mail.outbox[0].body

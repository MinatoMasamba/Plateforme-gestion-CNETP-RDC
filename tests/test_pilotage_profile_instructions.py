import pytest
from django.urls import reverse

from apps.governance.models import ComitePilotage, Demande, PilotageMembreship, PosteNominatif


def _member(expert, role, committee):
    PilotageMembreship.objects.create(comite=committee, expert=expert, role=role)
    return expert


@pytest.mark.django_db
def test_copil_member_has_personal_profile_and_can_edit_only_account(client, expert_factory):
    committee = ComitePilotage.objects.create(name='COPIL de test')
    expert = _member(expert_factory(), 'CONSEILLER_POLITIQUE', committee)
    poste = PosteNominatif.objects.create(
        comite=committee, holder=expert, role='CONSEILLER_POLITIQUE',
        order=6, title='Conseiller technique',
    )
    client.force_login(expert.user)

    page = client.get(reverse('web:pilotage_profile'))
    assert page.status_code == 200
    assert b'Mon profil COPIL' in page.content
    assert b'Conseiller technique' in page.content
    assert page.context['pilotage']['poste'] == poste
    assert reverse('web:pilotage_profile').encode() in client.get(reverse('web:pilotage_dashboard'), {'vue': 'pilotage'}).content

    saved = client.post(reverse('web:pilotage_profile'), {
        'first_name': 'Prénom corrigé', 'last_name': 'Nom corrigé',
        'phone': '0123456789', 'province': '', 'bio': 'Présentation',
        'role': 'PRESIDENT',
    })
    assert saved.status_code == 302
    expert.user.refresh_from_db()
    poste.refresh_from_db()
    assert expert.user.first_name == 'Prénom corrigé'
    assert poste.role == 'CONSEILLER_POLITIQUE'


@pytest.mark.django_db
def test_non_copil_expert_cannot_open_copil_profile(client, expert_factory):
    expert = expert_factory()
    client.force_login(expert.user)
    assert client.get(reverse('web:pilotage_profile')).status_code == 403


@pytest.mark.django_db
def test_global_observer_sees_instruction_without_transition_controls(client, expert_factory, user_factory):
    committee = ComitePilotage.objects.create(name='COPIL de test')
    sender = _member(expert_factory(user=user_factory(username='director')), 'PRESIDENT', committee)
    observer = _member(expert_factory(user=user_factory(username='observer')), 'CONSEILLER_POLITIQUE', committee)
    recipient = expert_factory(user=user_factory(username='recipient'))
    demande = Demande.objects.create(
        type='ACTION', emetteur=sender, destinataire=recipient,
        objet='Action confiée', statut='ENVOYEE',
    )
    client.force_login(observer.user)

    page = client.get(reverse('web:instructions'))
    assert page.status_code == 200
    assert b'Action confi' in page.content
    assert b'Instructions de production' in page.content
    assert b'data-theme-toggle' in page.content
    assert b'Marquer' not in page.content
    assert b'Nouvelle instruction</button>' not in page.content
    assert client.post(reverse('web:demande_transition', args=[demande.pk]), {'statut': 'LUE'}).status_code == 403

    client.force_login(sender.user)
    director_page = client.get(reverse('web:instructions'))
    assert b'Marquer' in director_page.content
    assert b'Nouvelle instruction</button>' in director_page.content

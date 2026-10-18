import pytest
from django.core import mail
from unittest.mock import patch

from apps.governance.models import ComitePilotage, PermissionRequest, PilotageMembreship
from apps.mobileapp.models import Notification


@pytest.fixture
def permission_participants(expert_factory, user_factory):
    committee = ComitePilotage.objects.create(name='Pilotage dérogations')
    requester = expert_factory(user=user_factory(username='requester', email='requester@cnetp.cd', first_name='Amina', last_name='Test'))
    reviewer = expert_factory(user=user_factory(username='reviewer', email='reviewer@cnetp.cd', first_name='Jean', last_name='Directoire'))
    PilotageMembreship.objects.create(comite=committee, expert=requester, role='CONSEILLER')
    PilotageMembreship.objects.create(comite=committee, expert=reviewer, role='SECRETARY')
    return requester, reviewer


@pytest.mark.django_db
def test_reply_reaches_requester_in_platform_and_email(client, permission_participants):
    requester, reviewer = permission_participants
    permission = PermissionRequest.objects.create(
        requester=requester, restricted_resource='Console globale', reason='Je souhaite consulter le dossier.',
    )
    client.force_login(reviewer.user)

    response = client.post(
        f'/pilotage/approuver-demande/{permission.pk}/',
        {'decision': 'REJECTED', 'comment': 'Accès refusé pour ce dossier.'},
    )

    assert response.status_code == 200
    assert response.json()['email_sent'] is True
    permission.refresh_from_db()
    assert permission.status == 'REJECTED'
    assert permission.reviewed_by == reviewer
    assert permission.review_comment == 'Accès refusé pour ce dossier.'
    notification = Notification.objects.get(user=requester.user, title='Réponse à votre demande de dérogation')
    assert reviewer.full_name in notification.body
    assert permission.review_comment in notification.body
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [requester.user.email]
    assert reviewer.full_name in mail.outbox[0].body
    assert permission.review_comment in mail.outbox[0].body

    client.force_login(requester.user)
    page = client.get('/pilotage/')
    assert page.status_code == 200
    assert reviewer.full_name in page.content.decode()
    assert permission.review_comment in page.content.decode()
    assert permission.reason in page.content.decode()

    client.force_login(reviewer.user)
    review_page = client.get('/pilotage/')
    assert permission.review_comment in review_page.content.decode()


@pytest.mark.django_db
def test_reply_requires_message_and_cannot_be_sent_twice(client, permission_participants):
    requester, reviewer = permission_participants
    permission = PermissionRequest.objects.create(
        requester=requester, restricted_resource='Module restreint', reason='Demande motivée',
    )
    client.force_login(reviewer.user)
    url = f'/pilotage/approuver-demande/{permission.pk}/'

    assert client.post(url, {'decision': 'APPROVED', 'comment': '  '}).status_code == 400
    assert client.post(url, {'decision': 'APPROVED', 'comment': 'Accès approuvé.'}).status_code == 200
    assert client.post(url, {'decision': 'REJECTED', 'comment': 'Autre réponse.'}).status_code == 409
    permission.refresh_from_db()
    assert permission.status == 'APPROVED'
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_non_directoire_cannot_reply(client, permission_participants):
    requester, _ = permission_participants
    permission = PermissionRequest.objects.create(
        requester=requester, restricted_resource='Module restreint', reason='Demande motivée',
    )
    client.force_login(requester.user)
    response = client.post(
        f'/pilotage/approuver-demande/{permission.pk}/',
        {'decision': 'APPROVED', 'comment': 'Message'},
    )
    assert response.status_code == 403
    assert not mail.outbox


@pytest.mark.django_db
def test_mail_failure_is_reported_without_losing_platform_reply(client, permission_participants):
    requester, reviewer = permission_participants
    permission = PermissionRequest.objects.create(
        requester=requester, restricted_resource='Module restreint', reason='Demande motivée',
    )
    client.force_login(reviewer.user)
    with patch('web.pilotage_views.send_mail', side_effect=RuntimeError('SMTP indisponible')):
        response = client.post(
            f'/pilotage/approuver-demande/{permission.pk}/',
            {'decision': 'REJECTED', 'comment': 'Réponse conservée.'},
        )

    assert response.status_code == 200
    assert response.json()['email_sent'] is False
    assert 'mail non envoyé' in response.json()['message']
    permission.refresh_from_db()
    assert permission.review_comment == 'Réponse conservée.'
    assert Notification.objects.filter(user=requester.user, body__contains='Réponse conservée.').exists()

import pytest
from django.utils import timezone

from apps.governance import st_ged
from apps.governance.models import CTCProcessus
from apps.governance.st_notification_models import STNotificationRead
from apps.mobileapp.models import Notification
from apps.norms.models import NormeVersion
from tests.test_st_ged import ged, prepared  # noqa: F401


@pytest.mark.django_db
def test_existing_personal_notifications_do_not_require_a_documentary_mandate(user_factory, client):
    user = user_factory()
    notification = Notification.objects.create(user=user, title='Personnelle', body='Information du compte', notification_type='SYSTEM')
    client.force_login(user)
    response = client.get('/api/v1/st/notifications/')
    assert response.status_code == 200
    assert response.json()['unread_count'] == 1
    assert len(response.json()['results']) == 1
    result = client.post('/api/v1/st/notifications/read/', {'key': 'notification:' + str(notification.pk)}, content_type='application/json')
    assert result.status_code == 200 and result.json()['unread_count'] == 0


@pytest.mark.django_db
def test_reading_a_case_decrements_count_once_and_survives_reload(ged, client):
    client.force_login(ged.writer)
    url = '/api/v1/st/notifications/'
    before = client.get(url).json()
    case = next(row for row in before['results'] if row['key'].startswith('case:'))
    assert not case['is_read']
    response = client.post(url + 'read/', {'key': case['key']}, content_type='application/json')
    assert response.status_code == 200, response.content
    assert response.json()['unread_count'] == before['unread_count'] - 1
    repeated = client.post(url + 'read/', {'key': case['key']}, content_type='application/json').json()
    assert repeated['unread_count'] == response.json()['unread_count']
    assert client.get(url).json()['unread_count'] == repeated['unread_count']
    assert STNotificationRead.objects.filter(user=ged.writer, key=case['key']).count() == 1
    assert st_ged.blockers(ged.process), 'Lire ne résout pas un blocage documentaire.'
    client.force_login(ged.head)
    assert not next(row for row in client.get(url).json()['results'] if row['key'] == case['key'])['is_read']


@pytest.mark.django_db
def test_read_notification_is_owned_by_current_user(ged, client):
    own = Notification.objects.create(user=ged.writer, title='Suivi', body='Cas personnel', notification_type='SYSTEM')
    other = Notification.objects.create(user=ged.head, title='Privée', body='Autre compte', notification_type='SYSTEM')
    client.force_login(ged.writer)
    url = '/api/v1/st/notifications/'
    assert all(row['title'] != 'Privée' for row in client.get(url).json()['results'])
    assert client.post(url + 'read/', {'key': 'notification:' + str(other.pk)}, content_type='application/json').status_code == 404
    assert client.post(url + 'read/', {'key': 'case:inventee'}, content_type='application/json').status_code == 404
    assert client.post(url + 'read/', {'key': 'notification:' + str(own.pk)}, content_type='application/json').status_code == 200
    own.refresh_from_db()
    other.refresh_from_db()
    assert own.is_read and own.read_at and not other.is_read


@pytest.mark.django_db
def test_received_catalogue_includes_later_stages_without_opening_writes(ged, client, norme_factory):
    legacy = CTCProcessus.objects.create(norme=norme_factory(), received_at=timezone.now(), current_stage='MULTI_REVIEW', indexed_at=timezone.now())
    NormeVersion.objects.create(norme=legacy.norme, version_number=1, content='Version reçue', version_author=ged.head)
    unreceived = CTCProcessus.objects.create(norme=norme_factory())
    phoenix_norm = norme_factory(circuit_version='PHOENIX')
    phoenix = CTCProcessus.objects.create(norme=phoenix_norm, received_at=timezone.now())
    client.force_login(ged.writer)
    response = client.get('/api/v1/st/ged/received-norms/')
    assert response.status_code == 200
    rows = response.json()['results']
    assert {row['id'] for row in rows} == {ged.process.pk, legacy.pk}
    assert next(row for row in rows if row['id'] == legacy.pk)['version_count'] == 1
    assert legacy.pk not in st_ged.processes(ged.writer).values_list('pk', flat=True)
    assert client.get(f'/api/v1/st/ged/{legacy.pk}/version-history/').json()[0]['content'] == 'Version reçue'
    assert client.get(f'/api/v1/st/ged/{unreceived.pk}/version-history/').status_code == 404
    assert client.get(f'/api/v1/st/ged/{phoenix.pk}/version-history/').status_code == 404
    client.force_login(ged.ptn)
    assert client.get('/api/v1/st/ged/received-norms/').status_code == 403


@pytest.mark.django_db
def test_resolved_case_disappears_without_erasing_read_history(ged, client):
    client.force_login(ged.writer)
    url = '/api/v1/st/notifications/'
    case = client.get(url).json()['results'][0]
    client.post(url + 'read/', {'key': case['key']}, content_type='application/json')
    prepared(ged)
    # Les pièces et le code sont désormais présents : l'ancien blocage disparaît.
    assert not any(row['key'] == case['key'] for row in client.get(url).json()['results'])
    assert STNotificationRead.objects.filter(user=ged.writer, key=case['key']).exists()

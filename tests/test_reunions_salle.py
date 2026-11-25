"""Tests des salles de réunion, invitations, présence et PV."""

import base64
import hashlib
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.experts.models import Expert
from apps.governance.models import Affectation
from apps.meetings.models import (
    LiveKitWebhookEvent, Presence, PresenceSession, ProcessusVerbaux,
    ReglePresence, Reunion, ReunionParticipant,
)
from apps.meetings.services.presence import merge_sessions, presence_seconds
from apps.payments.models import JetonPresence


def _expert(user_factory, username, structure):
    user = user_factory(username=username, email=f'{username}@cnetp.cd')
    user.is_expert = True
    user.save(update_fields=['is_expert'])
    return Expert.objects.create(user=user, structure=structure, status='ACTIVE')


def _manager(user_factory, ctm_factory, wg_factory, structure, username='secretaire'):
    ctm = ctm_factory()
    wg = wg_factory(ctm=ctm)
    expert = _expert(user_factory, username, structure)
    ctm.secretary = expert
    ctm.save(update_fields=['secretary'])
    Affectation.objects.create(expert=expert, ctm=ctm, wg=wg)
    return expert, ctm, wg


def _reunion(wg, organisateur, **kwargs):
    defaults = {
        'type': 'WG',
        'titre': 'Réunion test',
        'wg': wg,
        'date': timezone.now() + timedelta(minutes=5),
        'mode': 'SALLE',
        'room_name': f'reunion-test-{Reunion.objects.count() + 1}',
        'status': 'PLANNED',
        'organisateur': organisateur,
    }
    defaults.update(kwargs)
    return Reunion.objects.create(**defaults)


@pytest.mark.django_db
class TestReunionAccess:
    def test_creation_reservee_aux_gestionnaires(
        self, user_factory, ctm_factory, wg_factory,
    ):
        from apps.experts.models import Structure

        structure, _ = Structure.objects.get_or_create(
            name='Structure test', defaults={'acronym': 'TST', 'category': 'ADMIN'}
        )
        manager, ctm, wg = _manager(
            user_factory, ctm_factory, wg_factory, structure,
        )
        outsider = _expert(user_factory, 'outsider', structure)

        payload = {
            'type': 'WG', 'titre': 'Réunion secrétariat', 'wg': wg.pk,
            'date': (timezone.now() + timedelta(days=1)).isoformat(),
            'mode': 'SALLE',
        }

        client = APIClient()
        client.force_authenticate(outsider.user)
        assert client.post('/api/v1/reunions/', payload, format='json').status_code == 403

        client.force_authenticate(manager.user)
        response = client.post('/api/v1/reunions/', payload, format='json')
        assert response.status_code == 201, response.data
        assert response.data['id']
        reunion = Reunion.objects.get(titre='Réunion secrétariat')
        assert reunion.organisateur_id == manager.pk
        assert reunion.room_name
        assert ReunionParticipant.objects.filter(reunion=reunion, expert=manager).exists()
        assert Presence.objects.filter(reunion=reunion, expert=manager).exists()

    def test_ouvrir_salle_reouvre_une_reunion_completee(
        self, user_factory, ctm_factory, wg_factory,
    ):
        from apps.experts.models import Structure

        structure, _ = Structure.objects.get_or_create(
            name='Structure test', defaults={'acronym': 'TST', 'category': 'ADMIN'}
        )
        manager, _, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
        reunion = _reunion(
            wg, manager, status='COMPLETED',
            cloture_salle=timezone.now() - timedelta(minutes=1),
        )

        client = APIClient()
        client.force_authenticate(manager.user)
        response = client.post(f'/api/v1/reunions/{reunion.pk}/ouvrir_salle/')

        assert response.status_code == 200, response.data
        reunion.refresh_from_db()
        assert reunion.status == 'IN_PROGRESS'
        assert reunion.cloture_salle is None

    def test_rejoindre_exige_invitation_et_fenetre_horaire(
        self, monkeypatch, user_factory, ctm_factory, wg_factory,
    ):
        from apps.experts.models import Structure
        from api.v1.meetings import views as meeting_views

        structure, _ = Structure.objects.get_or_create(
            name='Structure test', defaults={'acronym': 'TST', 'category': 'ADMIN'}
        )
        manager, _, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
        invite = _expert(user_factory, 'invite', structure)
        outsider = _expert(user_factory, 'outsider2', structure)
        reunion = _reunion(wg, manager)
        ReunionParticipant.objects.create(reunion=reunion, expert=invite)

        monkeypatch.setattr(
            meeting_views, 'generate_join_token',
            lambda reunion, participant: {
                'url': 'wss://livekit.test', 'token': 'jeton',
                'room_name': reunion.room_name, 'role': participant.role,
            },
        )

        client = APIClient()
        client.force_authenticate(outsider.user)
        assert client.post(f'/api/v1/reunions/{reunion.pk}/rejoindre/').status_code == 404

        client.force_authenticate(invite.user)
        response = client.post(f'/api/v1/reunions/{reunion.pk}/rejoindre/')
        assert response.status_code == 200, response.data
        assert response.data['token'] == 'jeton'

        reunion.date = timezone.now() + timedelta(hours=2)
        reunion.save(update_fields=['date'])
        assert client.post(f'/api/v1/reunions/{reunion.pk}/rejoindre/').status_code == 400

        reunion.date = timezone.now() + timedelta(minutes=5)
        reunion.save(update_fields=['date'])
        participant = ReunionParticipant.objects.get(reunion=reunion, expert=invite)
        participant.exclu_jusqua = timezone.now() + timedelta(minutes=30)
        participant.save(update_fields=['exclu_jusqua'])
        assert client.post(f'/api/v1/reunions/{reunion.pk}/rejoindre/').status_code == 403


@pytest.mark.django_db
class TestPresenceEtPV:
    def test_checkin_met_a_jour_marked_at(
        self, user_factory, ctm_factory, wg_factory,
    ):
        from apps.experts.models import Structure

        structure, _ = Structure.objects.get_or_create(
            name='Structure test', defaults={'acronym': 'TST', 'category': 'ADMIN'}
        )
        manager, _, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
        reunion = _reunion(wg, manager)
        ReunionParticipant.objects.create(reunion=reunion, expert=manager)
        presence = Presence.objects.create(reunion=reunion, expert=manager, status='ABSENT')
        old = timezone.now() - timedelta(hours=2)
        Presence.objects.filter(pk=presence.pk).update(marked_at=old)
        presence.refresh_from_db()

        client = APIClient()
        client.force_authenticate(manager.user)
        response = client.post(f'/api/v1/reunions/{reunion.pk}/checkin_presence/')
        assert response.status_code == 200
        presence.refresh_from_db()
        assert presence.status == 'PRESENT'
        assert presence.marked_at > old

    def test_pv_exclut_les_excuses_du_quorum_et_evite_none(
        self, user_factory, ctm_factory, wg_factory,
    ):
        from apps.experts.models import Structure

        structure, _ = Structure.objects.get_or_create(
            name='Structure test', defaults={'acronym': 'TST', 'category': 'ADMIN'}
        )
        manager, _, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
        presents = _expert(user_factory, 'present', structure)
        absent = _expert(user_factory, 'absent', structure)
        excuse = _expert(user_factory, 'excuse', structure)
        reunion = _reunion(
            wg, manager, status='COMPLETED', ordre_jour=None,
            date=timezone.now() - timedelta(hours=1),
        )
        Presence.objects.create(reunion=reunion, expert=presents, status='PRESENT')
        Presence.objects.create(reunion=reunion, expert=absent, status='ABSENT')
        Presence.objects.create(reunion=reunion, expert=excuse, status='EXCUSED')

        client = APIClient()
        client.force_authenticate(manager.user)
        response = client.post(f'/api/v1/reunions/{reunion.pk}/generate_pv/')
        assert response.status_code in (200, 201), response.data
        pv = ProcessusVerbaux.objects.get(reunion=reunion)
        assert pv.quorum_atteint is True
        assert pv.nombre_presents == 1
        assert pv.nombre_absents == 1
        assert 'None' not in pv.contenu
        assert 'Excusés: 1' in pv.contenu

    def test_jeton_calcule_selon_regle_et_ignore_excuse(
        self, user_factory, ctm_factory, wg_factory,
    ):
        from apps.experts.models import Structure
        from apps.meetings.services.presence import apply_presence_at_close

        structure, _ = Structure.objects.get_or_create(
            name='Structure test', defaults={'acronym': 'TST', 'category': 'ADMIN'}
        )
        manager, _, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
        present = _expert(user_factory, 'present2', structure)
        excuse = _expert(user_factory, 'excuse2', structure)
        now = timezone.now()
        reunion = _reunion(
            wg, manager, status='IN_PROGRESS',
            ouverture_salle=now - timedelta(seconds=100), cloture_salle=now,
        )
        ReunionParticipant.objects.create(reunion=reunion, expert=present)
        ReunionParticipant.objects.create(reunion=reunion, expert=excuse)
        Presence.objects.create(reunion=reunion, expert=present, status='ABSENT')
        Presence.objects.create(reunion=reunion, expert=excuse, status='EXCUSED')
        PresenceSession.objects.create(
            reunion=reunion, expert=present,
            joined_at=now - timedelta(seconds=100), left_at=now - timedelta(seconds=40),
        )
        PresenceSession.objects.create(
            reunion=reunion, expert=excuse,
            joined_at=now - timedelta(seconds=100), left_at=now,
        )
        ReglePresence.objects.create(
            type_reunion='WG', seuil_presence_pct=50,
            tolerance_coupure_s=60, montant_jeton=25,
        )

        apply_presence_at_close(reunion)

        presence = Presence.objects.get(reunion=reunion, expert=present)
        assert presence.status == 'PRESENT'
        jeton = JetonPresence.objects.get(reunion=reunion, expert=present)
        assert jeton.montant == 25
        assert jeton.presence_secondes == 60
        assert not JetonPresence.objects.filter(reunion=reunion, expert=excuse).exists()

    def test_fusion_des_micro_coupures(self):
        now = timezone.now()

        class Session:
            def __init__(self, start, end):
                self.joined_at = start
                self.left_at = end
                self.reunion = None

        sessions = [
            Session(now, now + timedelta(seconds=30)),
            Session(now + timedelta(seconds=60), now + timedelta(seconds=120)),
        ]
        assert presence_seconds(sessions, tolerance_seconds=60) == 120
        assert merge_sessions(sessions, tolerance_seconds=60) == [
            (now, now + timedelta(seconds=120)),
        ]


@pytest.mark.django_db
class TestLiveKitWebhook:
    def test_webhook_signe_cree_la_session(
        self, settings, user_factory, ctm_factory, wg_factory,
    ):
        import json

        from livekit import api
        from apps.experts.models import Structure

        settings.LIVEKIT_URL = 'wss://livekit.test'
        settings.LIVEKIT_API_KEY = 'test-key'
        settings.LIVEKIT_API_SECRET = 'test-secret'

        structure, _ = Structure.objects.get_or_create(
            name='Structure test', defaults={'acronym': 'TST', 'category': 'ADMIN'}
        )
        manager, _, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
        invite = _expert(user_factory, 'webhook', structure)
        reunion = _reunion(wg, manager)
        ReunionParticipant.objects.create(reunion=reunion, expert=invite)

        body = json.dumps({
            'event': 'participant_joined',
            'id': 'EV_test_1',
            'created_at': int(timezone.now().timestamp()),
            'room': {'name': reunion.room_name, 'sid': 'RM_test'},
            'participant': {
                'identity': str(invite.pk), 'sid': 'PA_test',
                'joined_at': int(timezone.now().timestamp()),
            },
        })
        token = api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        token.with_sha256(
            base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
        )
        token.with_ttl(timedelta(minutes=5))

        client = APIClient()
        response = client.post(
            '/api/v1/meetings/livekit/webhook/',
            data=body,
            content_type='application/webhook+json',
            HTTP_AUTHORIZATION=token.to_jwt(),
        )
        assert response.status_code == 200, response.content
        assert LiveKitWebhookEvent.objects.filter(event_id='EV_test_1').exists()
        assert PresenceSession.objects.filter(reunion=reunion, expert=invite).exists()
        assert Presence.objects.get(reunion=reunion, expert=invite).status == 'PRESENT'

        duplicate = client.post(
            '/api/v1/meetings/livekit/webhook/',
            data=body,
            content_type='application/webhook+json',
            HTTP_AUTHORIZATION=token.to_jwt(),
        )
        assert duplicate.status_code == 200
        assert PresenceSession.objects.filter(reunion=reunion, expert=invite).count() == 1

    def test_webhook_signature_invalide_rejetee(self, settings):
        settings.LIVEKIT_URL = 'wss://livekit.test'
        settings.LIVEKIT_API_KEY = 'test-key'
        settings.LIVEKIT_API_SECRET = 'test-secret'
        client = APIClient()
        response = client.post(
            '/api/v1/meetings/livekit/webhook/',
            data='{"event":"room_started"}',
            content_type='application/webhook+json',
            HTTP_AUTHORIZATION='invalide',
        )
        assert response.status_code == 401

    def test_room_finished_ne_cloture_pas_la_reunion(
        self, settings, user_factory, ctm_factory, wg_factory,
    ):
        import json

        from livekit import api
        from apps.experts.models import Structure

        settings.LIVEKIT_URL = 'wss://livekit.test'
        settings.LIVEKIT_API_KEY = 'test-key'
        settings.LIVEKIT_API_SECRET = 'test-secret'

        structure, _ = Structure.objects.get_or_create(
            name='Structure test', defaults={'acronym': 'TST', 'category': 'ADMIN'}
        )
        manager, _, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
        reunion = _reunion(wg, manager, status='IN_PROGRESS')
        body = json.dumps({
            'event': 'room_finished',
            'id': 'EV_test_finished',
            'created_at': int(timezone.now().timestamp()),
            'room': {'name': reunion.room_name, 'sid': 'RM_test'},
        })
        token = api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        token.with_sha256(
            base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
        )
        token.with_ttl(timedelta(minutes=5))

        response = APIClient().post(
            '/api/v1/meetings/livekit/webhook/',
            data=body,
            content_type='application/webhook+json',
            HTTP_AUTHORIZATION=token.to_jwt(),
        )
        assert response.status_code == 200, response.content
        reunion.refresh_from_db()
        assert reunion.status == 'IN_PROGRESS'
        assert reunion.cloture_salle is None


@pytest.mark.django_db
class TestMeetingRoomPage:
    def test_page_reservee_aux_invites(
        self, user_factory, ctm_factory, wg_factory,
    ):
        from django.test import Client
        from apps.experts.models import Structure

        structure, _ = Structure.objects.get_or_create(
            name='Structure test', defaults={'acronym': 'TST', 'category': 'ADMIN'}
        )
        manager, _, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
        invite = _expert(user_factory, 'room-invite', structure)
        outsider = _expert(user_factory, 'room-outsider', structure)
        reunion = _reunion(wg, manager)
        ReunionParticipant.objects.create(reunion=reunion, expert=invite)

        client = Client()
        client.force_login(invite.user)
        response = client.get(f'/app/salle/{reunion.pk}/')
        assert response.status_code == 200
        assert b'livekit-client' in response.content

        client.force_login(outsider.user)
        response = client.get(f'/app/salle/{reunion.pk}/')
        assert response.status_code == 302


@pytest.mark.django_db
class TestMeetingDetailsPage:
    def _setup(self, user_factory, ctm_factory, wg_factory):
        from apps.experts.models import Structure

        structure, _ = Structure.objects.get_or_create(
            name='Structure test', defaults={'acronym': 'TST', 'category': 'ADMIN'}
        )
        manager, _, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
        invite = _expert(user_factory, 'details-invite', structure)
        outsider = _expert(user_factory, 'details-outsider', structure)
        reunion = _reunion(
            wg, manager,
            ordre_jour='Examiner le projet\nValider le calendrier',
            document_links=[{'title': 'Projet de norme', 'url': 'https://example.org/projet.pdf'}],
        )
        ReunionParticipant.objects.create(reunion=reunion, expert=invite, role='MEMBRE')
        return reunion, invite, outsider

    def test_details_accessibles_aux_invites(
        self, user_factory, ctm_factory, wg_factory,
    ):
        from django.test import Client

        reunion, invite, _ = self._setup(user_factory, ctm_factory, wg_factory)
        client = Client()
        client.force_login(invite.user)

        response = client.get(f'/meeting/{reunion.pk}/')
        assert response.status_code == 200
        assert b'Ordre du jour' in response.content
        assert b'Participants' in response.content
        assert b'Projet de norme' in response.content
        assert b'Rejoindre la salle' in response.content

    def test_ancien_lien_meetings_fonctionne(
        self, user_factory, ctm_factory, wg_factory,
    ):
        from django.test import Client

        reunion, invite, _ = self._setup(user_factory, ctm_factory, wg_factory)
        client = Client()
        client.force_login(invite.user)

        response = client.get(f'/meetings/{reunion.pk}/')
        assert response.status_code == 200

    def test_details_refusees_aux_non_invites(
        self, user_factory, ctm_factory, wg_factory,
    ):
        from django.test import Client

        reunion, _, outsider = self._setup(user_factory, ctm_factory, wg_factory)
        client = Client()
        client.force_login(outsider.user)

        response = client.get(f'/meeting/{reunion.pk}/')
        assert response.status_code == 302

    def test_liste_redirige_les_visiteurs_vers_connexion(self):
        from django.test import Client

        response = Client().get('/meeting/')
        assert response.status_code == 302
        assert '/se-connecter/' in response.url

    def test_liste_des_reunions_de_l_expert(
        self, user_factory, ctm_factory, wg_factory,
    ):
        from django.test import Client

        reunion, invite, _ = self._setup(user_factory, ctm_factory, wg_factory)
        client = Client()
        client.force_login(invite.user)

        response = client.get('/meeting/')
        assert response.status_code == 200
        assert reunion.titre.encode() in response.content

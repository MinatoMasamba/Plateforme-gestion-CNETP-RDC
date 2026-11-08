"""Tests de l'administration Neuronne : comptes, adhésions, diffusion, rapport."""
from datetime import date

import pytest
from django.contrib.auth.models import Group
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.dashboard.console_permissions import console_group_name, sync_console_group
from apps.experts.models import Expert, Structure
from apps.governance.models import (
    AffectationSousCommission, CTCMembership, ComitePilotage, GroupeCible,
    MandatOrganisation, Organe, OrganisationVersion, PilotageMembreship,
    TechnicalCell,
)
from apps.ia_agent.models import AgentSession, NeuronneDailyReport
from apps.ia_agent.services.agent_runner import AgentRunner
from apps.ia_agent.services.neuronne_admin import (
    add_user_to_organisation, create_platform_user, send_daily_report,
    send_message_to_sc_gt, send_message_to_user,
)
from apps.ia_agent.tools.admin_tools import NEURONNE_ADMIN_TOOLS
from apps.mobileapp.models import Notification


def _neuronne_admin(user_factory):
    sync_console_group()
    user = user_factory(
        username='neuronne-admin', email='neuronne@cnetp.cd',
        is_staff=True, is_superuser=True,
    )
    user.groups.add(Group.objects.get(name=console_group_name()))
    return user


def _recipient(user_factory, structure):
    user = user_factory(username='destinataire', email='destinataire@cnetp.cd')
    expert = Expert.objects.create(user=user, structure=structure, status='ACTIVE')
    return user, expert


@pytest.mark.django_db(transaction=True)
class TestNeuronneUsersAndMemberships:
    def test_creation_utilisateur_avec_email_et_audit(self, user_factory):
        admin = _neuronne_admin(user_factory)
        mail.outbox.clear()

        result = create_platform_user(
            admin, email='nouveau@cnetp.cd', first_name='Nouveau',
            last_name='Compte', send_email=True,
        )

        assert result['email_sent'] is True
        assert len(mail.outbox) == 1
        assert 'Code de définition' in mail.outbox[0].body
        assert result['user_id']

    def test_ajout_ctc_copil_avec_email(self, user_factory, expert_factory):
        admin = _neuronne_admin(user_factory)
        structure, _ = Structure.objects.get_or_create(
            name='Structure Neuronne', defaults={'acronym': 'SN', 'category': 'ADMIN'},
        )
        target = expert_factory(user=user_factory(username='membre-neuronne', email='membre@cnetp.cd'))
        ctc = TechnicalCell.objects.create(name='CTC Neuronne')
        comite = ComitePilotage.objects.create(name='COPIL Neuronne')
        mail.outbox.clear()

        result = add_user_to_organisation(
            admin, user_identifier=target.user.email, target='CTC',
            ctc_id=ctc.pk, role='ISO_EXPERT',
        )
        assert CTCMembership.objects.filter(ctc=ctc, expert=target, role='ISO_EXPERT').exists()
        assert result['target'] == 'CTC'
        assert len(mail.outbox) == 1

        result = add_user_to_organisation(
            admin, user_identifier=str(target.user.pk), target='COPIL',
            comite_id=comite.pk, role='CONSEILLER',
        )
        assert PilotageMembreship.objects.filter(comite=comite, expert=target).exists()
        assert result['target'] == 'COPIL'
        assert len(mail.outbox) == 2

    def test_ajout_sc_et_gt_avec_email(self, user_factory, expert_factory):
        admin = _neuronne_admin(user_factory)
        structure, _ = Structure.objects.get_or_create(
            name='Structure Neuronne', defaults={'acronym': 'SN', 'category': 'ADMIN'},
        )
        target = expert_factory(user=user_factory(username='membre-sc', email='membre-sc@cnetp.cd'))
        version = OrganisationVersion.objects.create(
            code='neuronne-2026', name='Organisation Neuronne', source_document='Décision',
        )
        sc = Organe.objects.create(
            version=version, type='SC', code='SC-NEUR', name='Sous-commission Neuronne',
            status='VALIDATED', source_reference='Décision',
        )
        gt = GroupeCible.objects.create(
            sc=sc, code='GT-NEUR', name='Groupe Neuronne', activity='PRODUCTION',
             source_reference='Décision',
        )
        mail.outbox.clear()

        result = add_user_to_organisation(
            admin, user_identifier=target.user.email, target='SC',
            sc_code='SC-NEUR', reference='Décision SC',
        )
        assert result['target'] == 'SC'
        assert len(mail.outbox) == 1

        result = add_user_to_organisation(
            admin, user_identifier=target.user.email, target='GT',
            gt_id=gt.pk, reference='Décision GT',
        )
        assert result['target'] == 'GT'
        assert MandatOrganisation.objects.filter(expert=target, groupe=gt, status='ACTIVE').exists()
        assert len(mail.outbox) == 2


@pytest.mark.django_db(transaction=True)
class TestNeuronneMessagesAndReport:
    def test_message_direct_email_et_notification(self, user_factory, expert_factory):
        admin = _neuronne_admin(user_factory)
        structure, _ = Structure.objects.get_or_create(
            name='Structure Neuronne', defaults={'acronym': 'SN', 'category': 'ADMIN'},
        )
        target_user, _ = _recipient(user_factory, structure)
        mail.outbox.clear()

        result = send_message_to_user(
            admin, user_identifier=target_user.email, subject='Consigne',
            body='Message de test Neuronne.',
        )

        assert result['email_sent'] is True
        assert len(mail.outbox) == 1
        assert Notification.objects.filter(user=target_user, title='Consigne').exists()

    def test_diffusion_sc_admin_sans_mandat_st(
        self, user_factory, expert_factory,
    ):
        from apps.messaging.dispatch_models import InstitutionalDispatch

        admin = _neuronne_admin(user_factory)
        structure, _ = Structure.objects.get_or_create(
            name='Structure Neuronne', defaults={'acronym': 'SN', 'category': 'ADMIN'},
        )
        target = expert_factory(user=user_factory(username='membre-diff', email='membre-diff@cnetp.cd'))
        version = OrganisationVersion.objects.create(
            code='neuronne-diffusion', name='Organisation diffusion',
            source_document='Décision', status='VALIDATED',
        )
        sc = Organe.objects.create(
            version=version, type='SC', code='SC-DIFF', name='SC diffusion',
            status='VALIDATED', source_reference='Décision',
        )
        AffectationSousCommission.objects.create(
            version=version, expert=target, sc=sc,
            source_key='diff-1', batch_reference='TEST', source_kind='REPORT_PROPOSAL',
            source_database_sha256='a' * 64, migration_reference='Test',
            status='MIGRATED', effective_from=timezone.localdate(),
            source_snapshot={'test': True},
        )
        mail.outbox.clear()

        result = send_message_to_sc_gt(
            admin, subject='Diffusion SC', body='Message aux membres actifs.',
            sc_id=sc.pk,
        )

        assert result['recipient_count'] == 1
        dispatch = InstitutionalDispatch.objects.get(pk=result['dispatch_id'])
        assert dispatch.recipients.get().user_id == target.user_id
        assert Notification.objects.filter(data__dispatch_id=dispatch.pk).exists()
        assert len(mail.outbox) == 1

    def test_rapport_quotidien_persiste_et_notifie(self, user_factory):
        admin = _neuronne_admin(user_factory)
        create_platform_user(
            admin, email='rapport-user@cnetp.cd', first_name='Rapport',
            last_name='User', send_email=False,
        )
        mail.outbox.clear()

        result = send_daily_report(admin, day=timezone.localdate())

        assert result['action_count'] >= 1
        report = NeuronneDailyReport.objects.get(report_date=timezone.localdate())
        assert 'RAPPORT QUOTIDIEN NEURONNE' in report.text
        assert Notification.objects.filter(user=admin).exists()
        assert len(mail.outbox) >= 1


@pytest.mark.django_db
class TestNeuronneToolScope:
    def test_outils_admin_visibles_seulement_pour_neuronne(self, user_factory):
        admin = _neuronne_admin(user_factory)
        normal = user_factory(username='expert-normal', email='normal@cnetp.cd')
        admin_session = AgentSession.objects.create(user=admin, scope='expert')
        normal_session = AgentSession.objects.create(user=normal, scope='expert')

        admin_tools = {tool['name'] for tool in AgentRunner(admin_session)._get_tools_spec()}
        normal_tools = {tool['name'] for tool in AgentRunner(normal_session)._get_tools_spec()}

        assert NEURONNE_ADMIN_TOOLS.issubset(admin_tools)
        assert not (NEURONNE_ADMIN_TOOLS & normal_tools)

    def test_console_user_create_verrouillee(self, client, user_factory):
        admin = _neuronne_admin(user_factory)
        client.force_login(admin)
        response = client.post(reverse('console:user_create'), {
            'username': 'interdit', 'email': 'interdit@cnetp.cd',
        })
        assert response.status_code == 403


@pytest.mark.django_db
class TestNeuronneAdminScope:
    def test_scope_admin_reserve_aux_administrateurs_console(self, user_factory):
        from apps.ia_agent.services.permissions import available_scopes, user_can_access_scope

        admin = _neuronne_admin(user_factory)
        normal = user_factory(username='expert-scope', email='expert-scope@cnetp.cd')

        assert 'admin' in available_scopes(admin)
        assert 'admin' not in available_scopes(normal)
        assert user_can_access_scope(admin, 'admin') is True
        assert user_can_access_scope(normal, 'admin') is False

    def test_session_admin_expose_tous_les_outils(self, user_factory):
        from apps.ia_agent.tools import TOOL_REGISTRY

        admin = _neuronne_admin(user_factory)
        session = AgentSession.objects.create(user=admin, scope='admin')
        names = {tool['name'] for tool in AgentRunner(session)._get_tools_spec()}

        assert names == set(TOOL_REGISTRY)
        assert NEURONNE_ADMIN_TOOLS.issubset(names)

    def test_api_refuse_le_scope_admin_a_un_compte_ordinaire(self, user_factory):
        admin = _neuronne_admin(user_factory)
        normal = user_factory(username='api-normal', email='api-normal@cnetp.cd')

        admin_client = APIClient()
        admin_client.force_authenticate(admin)
        allowed = admin_client.post('/api/v1/ia-agent/sessions/', {'scope': 'admin'}, format='json')
        assert allowed.status_code == 201
        assert allowed.json()['scope'] == 'admin'

        normal_client = APIClient()
        normal_client.force_authenticate(normal)
        denied = normal_client.post('/api/v1/ia-agent/sessions/', {'scope': 'admin'}, format='json')
        assert denied.status_code == 403

    def test_console_affiche_le_bouton_neuronne(self, user_factory):
        admin = _neuronne_admin(user_factory)
        client = Client()
        client.force_login(admin)
        response = client.get(reverse('console:home'))
        assert response.status_code == 200
        html = response.content.decode()
        assert 'Assistant Neuronne' in html
        assert 'data-scope="admin"' in html

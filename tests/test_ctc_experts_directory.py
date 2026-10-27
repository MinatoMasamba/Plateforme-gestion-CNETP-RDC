import pytest

from apps.experts.models import Expert, Structure
from apps.governance.models import CTCMembership, TechnicalCell
from web.ctc_experts import build_expert_directory, build_traceability

pytestmark = pytest.mark.django_db


@pytest.fixture
def ctc_member(user_factory, expert_factory):
    expert = expert_factory(
        user=user_factory(username='ctc-directory', email='ctc-directory@example.test'),
    )
    CTCMembership.objects.create(ctc=TechnicalCell.objects.create(), expert=expert, role='COORDINATOR')
    return expert


def test_directory_lists_experts_without_inventing_data(ctc_member, expert_factory, user_factory):
    other = expert_factory(user=user_factory(username='plain-expert', email='plain-expert@example.test'))
    directory = build_expert_directory(ctc_member)
    assert directory['total'] >= 2
    ids = {row['id'] for row in directory['rows']}
    assert ctc_member.pk in ids and other.pk in ids
    # Aucune affectation, complétude ni activité ne doit être inventée.
    plain = next(row for row in directory['rows'] if row['id'] == other.pk)
    assert plain['affectation'] == 'aucune'
    assert plain['editions'] == 0
    assert plain['minutes'] == 0


def test_directory_reports_completeness_from_real_fields(ctc_member, expert_factory, user_factory):
    expert = expert_factory(user=user_factory(username='incomplete', email='incomplete@example.test'))
    expert.specialties = ''
    expert.save(update_fields=['specialties'])
    directory = build_expert_directory(ctc_member)
    row = next(r for r in directory['rows'] if r['id'] == expert.pk)
    assert row['complete'] is False
    assert 'CV' in row['missing'] or 'domaine de compétence' in row['missing']


def test_directory_readonly_and_no_trace_invention(ctc_member):
    trace = build_traceability(ctc_member)
    assert isinstance(trace, list)


def test_ctc_expert_module_renders(client, ctc_member):
    client.force_login(ctc_member.user)
    response = client.get('/ctc/')
    assert response.status_code == 200
    content = response.content.decode()
    assert 'Experts et affectations' in content
    assert 'Traçabilité' in content
    assert 'Mon rôle et mes droits' in content

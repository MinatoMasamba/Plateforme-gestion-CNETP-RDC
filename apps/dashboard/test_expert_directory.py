from datetime import date

import pytest
from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from apps.dashboard.console_permissions import console_group_name
from apps.experts.models import Expert, Structure
from apps.governance.models import ComitePilotage, CTCMembership, PilotageMembreship, TechnicalCell

pytestmark = pytest.mark.django_db


@pytest.fixture
def directory(user_factory, ctm_factory):
    administrator = user_factory(username='directory-admin', is_staff=True, is_superuser=True)
    structures = [Structure.objects.create(name=f'Structure {code}', acronym=code, category='ADMIN')
                  for code in ('A', 'B', 'C')]
    data = [
        ('Alice', 'ACTIVE', 0, date(2026, 1, 12)), ('Benoît', 'ACTIVE', 1, date(2026, 7, 10)),
        ('Chloé', 'PENDING', 2, None), ('Denis', 'INACTIVE', 0, date(2025, 12, 10)),
        ('Emma', 'SUSPENDED', 1, None),
    ]
    experts = [Expert.objects.create(
        user=user_factory(username=f'directory-{i}', email=f'directory-{i}@example.test', first_name=name),
        structure=structures[structure], status=status, appointment_date=appointed,
    ) for i, (name, status, structure, appointed) in enumerate(data)]
    committee = ComitePilotage.objects.create(name='Pilotage annuaire')
    PilotageMembreship.objects.create(comite=committee, expert=experts[0], role='CONSEILLER')
    CTCMembership.objects.create(ctc=TechnicalCell.objects.create(), expert=experts[1], role='LEGAL')
    experts[3].ctm = ctm_factory()
    experts[3].save(update_fields=['ctm'])
    return administrator, structures, experts


def url():
    return reverse('console:model_list', args=['experts', 'expert'])


def test_directory_statistics_and_headers_are_real_and_in_french(client, directory):
    administrator, _, experts = directory
    client.force_login(administrator)
    response = client.get(url())
    assert response.status_code == 200
    assert response.context['expert_stats'] == {'total': 5, 'active': 2, 'pending': 1, 'inactive': 2}
    assert {row['expert'].pk for row in response.context['expert_rows']} == {e.pk for e in experts}
    html = response.content.decode()
    for text in ('Gestion des experts', 'Créer un expert', 'Annuaire des experts', 'Date de nomination', 'Présences'):
        assert text in html
    assert 'Full name' not in html and 'Appointment date' not in html and 'Presence count' not in html


def test_directory_combines_multiple_structures_status_search_and_dates(client, directory):
    administrator, structures, experts = directory
    client.force_login(administrator)
    response = client.get(url(), {
        'structure__id__in': [structures[0].pk, structures[1].pk], 'status': 'ACTIVE',
        'q': '@example.test', 'appointment_date__gte': '2026-01-01', 'appointment_date__lte': '2026-12-31',
    })
    assert response.status_code == 200
    assert {e.pk for e in response.context['cl'].result_list} == {experts[0].pk, experts[1].pk}
    assert response.context['selected_structure_count'] == 2
    assert response.context['expert_stats']['total'] == 5
    chip = next(chip for chip in response.context['active_filters'] if chip['label'] == 'Structure A')
    removed = client.get(chip['url'])
    assert removed.status_code == 200
    assert list(removed.context['cl'].result_list) == [experts[1]]
    assert removed.context['directory_query'] == '@example.test'


@pytest.mark.parametrize('committee,expected', [('pilotage', [0]), ('ctc', [1]), ('ctm', [3]), ('none', [2, 4])])
def test_directory_committee_filters_match_memberships(client, directory, committee, expected):
    administrator, _, experts = directory
    client.force_login(administrator)
    response = client.get(url(), {'committee': committee})
    assert response.status_code == 200
    assert {e.pk for e in response.context['cl'].result_list} == {experts[i].pk for i in expected}


def test_directory_empty_controls_do_not_filter_out_everyone(client, directory):
    administrator, _, _ = directory
    client.force_login(administrator)
    response = client.get(url(), {'status__exact': '', 'committee': '', 'appointment_date__gte': '',
                                  'appointment_date__lte': '', 'q': '', 'per_page': '25'})
    assert response.status_code == 200
    assert response.context['cl'].result_count == 5
    assert response.context['active_filters'] == []


def test_directory_pagination_preserves_filters(client, directory):
    administrator, structures, _ = directory
    users = administrator.__class__.objects.bulk_create([
        administrator.__class__(username=f'batch-{i}', email=f'batch-{i}@example.test', first_name=f'Batch {i}')
        for i in range(26)
    ])
    Expert.objects.bulk_create([Expert(user=user, structure=structures[0], status='ACTIVE') for user in users])
    client.force_login(administrator)
    response = client.get(url(), {'q': 'batch', 'status': 'ACTIVE', 'committee': 'none', 'per_page': '25',
                                  'structure__id__in': str(structures[0].pk)})
    assert response.status_code == 200
    assert len(response.context['expert_rows']) == 25
    next_url = response.context['next_url']
    assert 'committee=none' in next_url and 'per_page=25' in next_url
    assert 'structure__id__in=' in next_url and 'status__exact=ACTIVE' in next_url
    page_two = client.get(url() + next_url)
    assert page_two.status_code == 200
    assert len(page_two.context['expert_rows']) == 1
    assert page_two.context['cl'].result_count == 26


def test_directory_read_only_user_cannot_see_mutation_actions(client, directory, user_factory):
    _, _, experts = directory
    reader = user_factory(username='directory-reader', is_staff=False)
    group, _ = Group.objects.get_or_create(name=console_group_name())
    group.permissions.clear()
    reader.groups.add(group)
    reader.user_permissions.add(Permission.objects.get(content_type__app_label='experts', codename='view_expert'))
    client.force_login(reader)
    response = client.get(url())
    assert response.status_code == 200
    assert all(not row['can_change'] and not row['can_delete'] for row in response.context['expert_rows'])
    assert 'Créer un expert' not in response.content.decode()
    assert client.get(reverse('console:model_edit', args=['experts', 'expert', experts[0].pk])).status_code == 403


def test_directory_reports_only_recorded_incomplete_profiles(client, directory):
    from apps.experts.models import ProfileUpdate
    administrator, _, experts = directory
    ProfileUpdate.objects.create(expert=experts[0], status='IN_PROGRESS')
    ProfileUpdate.objects.create(expert=experts[1], status='COMPLETE')
    client.force_login(administrator)
    response = client.get(url())
    assert response.status_code == 200
    assert response.context['show_incomplete_stat'] is True
    assert response.context['expert_stats']['incomplete'] == 1


def test_directory_keeps_legacy_date_filters_visible_and_removable(client, directory):
    administrator, _, _ = directory
    client.force_login(administrator)
    response = client.get(url(), {'appointment_date__isnull': 'True'})
    assert response.status_code == 200
    assert response.context['cl'].result_count == 2
    chip = response.context['active_filters'][0]
    assert 'appointment_date' not in chip['url']
    assert client.get(chip['url']).context['cl'].result_count == 5

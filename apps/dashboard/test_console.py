import pytest
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Group
from django.urls import reverse

from apps.core.models import AuditLog
from apps.dashboard.console_permissions import console_group_name, sync_console_group
from apps.norms.models import Norme


@pytest.fixture
def console_admin(user_factory):
    return user_factory(
        username='console-admin',
        email='console-admin@cnetp.cd',
        is_superuser=True,
        is_staff=True,
    )


@pytest.fixture
def console_member(user_factory):
    sync_console_group()
    user = user_factory(username='console-member', email='console-member@cnetp.cd')
    user.groups.add(Group.objects.get(name=console_group_name()))
    return user


@pytest.mark.django_db
def test_console_requires_authentication(client):
    response = client.get(reverse('console:home'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_console_rejects_non_member(client, user_factory):
    user = user_factory(username='non-member')
    client.force_login(user)
    response = client.get(reverse('console:home'))
    assert response.status_code == 403


@pytest.mark.django_db
def test_console_accepts_group_member(client, console_member):
    client.force_login(console_member)
    response = client.get(reverse('console:home'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_group_sync_permissions():
    group = sync_console_group()
    codenames = set(group.permissions.values_list('codename', flat=True))
    assert 'delete_user' not in codenames
    assert 'view_user' in codenames
    assert 'change_user' in codenames
    assert 'view_auditlog' in codenames
    assert 'change_auditlog' not in codenames
    assert 'view_logentry' in codenames


@pytest.mark.django_db
def test_console_pages_render(client, console_admin, norme_factory, user_factory):
    norme = norme_factory()
    other = user_factory(username='other-user')
    inactive = user_factory(username='inactive-user', is_active=False)
    client.force_login(console_admin)

    pages = [
        reverse('console:home'),
        reverse('console:models'),
        reverse('console:model_list', args=['norms', 'norme']),
        reverse('console:model_detail', args=['norms', 'norme', norme.pk]),
        reverse('console:model_create', args=['norms', 'norme']),
        reverse('console:model_edit', args=['norms', 'norme', norme.pk]),
        reverse('console:model_delete', args=['norms', 'norme', norme.pk]),
        reverse('console:users'),
        reverse('console:user_detail', args=[other.pk]),
        reverse('console:user_create'),
        reverse('console:user_edit', args=[other.pk]),
        reverse('console:user_password', args=[other.pk]),
        reverse('console:user_deactivate', args=[other.pk]),
        reverse('console:user_reactivate', args=[inactive.pk]),
        reverse('console:audit'),
    ]
    for url in pages:
        response = client.get(url)
        assert response.status_code == 200, (url, response.status_code)


@pytest.mark.django_db
def test_user_delete_is_blocked(client, console_admin, user_factory):
    target = user_factory(username='cannot-delete')
    client.force_login(console_admin)
    response = client.post(
        reverse('console:model_delete', args=['core', 'user', target.pk]),
    )
    assert response.status_code == 403
    assert target.__class__.objects.filter(pk=target.pk).exists()


@pytest.mark.django_db
def test_admin_user_delete_permission_is_false(console_admin):
    from django.contrib import admin
    from django.test import RequestFactory

    request = RequestFactory().get('/admin/')
    request.user = console_admin
    user_admin = admin.site._registry[console_admin.__class__]
    assert user_admin.has_delete_permission(request) is False
    assert 'delete_selected' not in user_admin.get_actions(request)


@pytest.mark.django_db
def test_norme_create_and_audit(client, console_admin, ctm_factory, wg_factory):
    ctm = ctm_factory()
    wg = wg_factory(ctm=ctm)
    client.force_login(console_admin)
    response = client.post(
        reverse('console:model_create', args=['norms', 'norme']),
        {
            'title': 'Norme console',
            'reference_number': 'CNETP-CONSOLE-001',
            'description': 'Créée depuis la console',
            'standard_family': 'NCD',
            'norm_type': 'NCD',
            'status': 'DRAFT',
            'target_count': 1,
            'ctm': ctm.pk,
            'wg': wg.pk,
        },
    )
    assert response.status_code == 302, response.context and response.context.get('form').errors
    norme = Norme.objects.get(reference_number='CNETP-CONSOLE-001')
    assert norme.created_by == console_admin
    assert norme.updated_by == console_admin


@pytest.mark.django_db
def test_model_delete_records_audit(client, console_admin, norme_factory):
    norme = norme_factory()
    pk = norme.pk
    client.force_login(console_admin)

    response = client.post(
        reverse('console:model_delete', args=['norms', 'norme', pk]),
    )

    assert response.status_code == 302
    assert not Norme._base_manager.filter(pk=pk).exists()
    log = LogEntry.objects.get(
        content_type__app_label='norms',
        content_type__model='norme',
        object_id=str(pk),
    )
    assert log.object_id == str(pk)
    assert AuditLog.objects.filter(
        content_type='norms.Norme',
        object_id=pk,
        action='DELETE',
    ).exists()


@pytest.mark.django_db
def test_user_deactivation_restores_previous_expert_status(
    client,
    console_admin,
    user_factory,
):
    from apps.experts.models import Expert, Structure

    structure = Structure.objects.create(
        name='Structure console',
        acronym='SC',
        category='ADMIN',
    )
    target = user_factory(username='expert-console', is_expert=True)
    expert = Expert.objects.create(user=target, structure=structure, status='ACTIVE')
    client.force_login(console_admin)

    response = client.post(reverse('console:user_deactivate', args=[target.pk]))

    assert response.status_code == 302
    target.refresh_from_db()
    expert.refresh_from_db()
    assert target.is_active is False
    assert expert.status == 'SUSPENDED'

    response = client.post(
        reverse('console:user_reactivate', args=[target.pk]),
        {'restore_expert_status': 'on'},
    )

    assert response.status_code == 302
    target.refresh_from_db()
    expert.refresh_from_db()
    assert target.is_active is True
    assert expert.status == 'ACTIVE'

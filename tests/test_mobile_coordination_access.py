from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from api.v1.mobile.views import MobileAuthViewSet
from apps.governance.models import (
    CTCMembership, ComitePilotage, MandatOrganisation, PilotageMembreship,
    PosteOrganisation, TechnicalCell,
)
from apps.governance.st_matrix import prepare_matrix
from apps.governance.st_operations_models import STAccessPolicy


def bootstrap(user):
    request = APIRequestFactory().get('/api/v1/mobile/auth/bootstrap/')
    force_authenticate(request, user=user)
    response = MobileAuthViewSet.as_view({'get': 'bootstrap'})(request)
    assert response.status_code == 200
    return response.data


@pytest.mark.django_db
@pytest.mark.parametrize('is_admin', [False, True])
def test_no_profile_does_not_grant_coordination(user_factory, is_admin):
    user = user_factory(is_staff=is_admin, is_superuser=is_admin)
    data = bootstrap(user)
    assert data['space'] == 'public'
    assert data['can_access_coordination'] is False


@pytest.mark.django_db
def test_simple_expert_cannot_access_coordination(expert_factory):
    expert = expert_factory()
    data = bootstrap(expert.user)
    assert data['space'] == 'expert'
    assert data['can_access_coordination'] is False


@pytest.mark.django_db
@pytest.mark.parametrize('active', [False, True])
def test_only_active_ctc_membership_grants_access(expert_factory, active):
    expert = expert_factory()
    CTCMembership.all_objects.create(
        expert=expert, ctc=TechnicalCell.objects.create(), is_active=active,
    )
    data = bootstrap(expert.user)
    assert data['can_access_coordination'] is active
    assert data['space'] == ('ctc' if active else 'expert')


@pytest.mark.django_db
def test_pilotage_membership_preserves_independent_ctc_access(expert_factory):
    expert = expert_factory()
    CTCMembership.objects.create(expert=expert, ctc=TechnicalCell.objects.create())
    PilotageMembreship.objects.create(
        expert=expert, comite=ComitePilotage.objects.create(), role='PRESIDENT',
    )
    data = bootstrap(expert.user)
    assert data['space'] == 'pilotage_directoire'
    assert data['is_ctc'] is True
    assert data['can_access_coordination'] is True


@pytest.mark.django_db
@pytest.mark.parametrize('start_offset,end_offset,allowed', [
    (-2, 2, True), (1, 2, False), (-2, -1, False),
])
def test_st_mandate_must_be_current(expert_factory, start_offset, end_offset, allowed):
    expert = expert_factory()
    version = prepare_matrix()
    version.status = 'VALIDATED'
    version.save()
    STAccessPolicy.objects.update_or_create(pk=1, defaults={'version': version, 'enabled': True})
    post = PosteOrganisation.objects.get(code='ST-V3-06')
    today = timezone.localdate()
    MandatOrganisation.objects.create(
        expert=expert, poste=post, function=post.title, status='ACTIVE',
        start_date=today + timedelta(days=start_offset),
        end_date=today + timedelta(days=end_offset),
        appointment_reference='Test accès mobile',
    )
    data = bootstrap(expert.user)
    assert data['is_ctc'] is False
    assert data['can_access_coordination'] is allowed
    assert data['space'] == ('ctc' if allowed else 'expert')

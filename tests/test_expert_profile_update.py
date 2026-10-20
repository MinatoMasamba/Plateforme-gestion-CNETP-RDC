"""Parcours de mise à jour du profil expert (page /mise-a-jour-profil/)."""
import pytest
from django.urls import reverse

from apps.governance.models import (
    Affectation, CTCMembership, ComitePilotage, PilotageMembreship, TechnicalCell,
)


@pytest.mark.django_db
def test_update_persists_and_redirects_to_expert_workspace(
    client, expert_factory, ctm_factory, wg_factory,
):
    ctm1 = ctm_factory(number=1, name='CTM 1')
    ctm2 = ctm_factory(number=2, name='CTM 2')
    wg1 = wg_factory(ctm=ctm1, number=1, name='WG 1')
    wg2 = wg_factory(ctm=ctm2, number=1, name='WG 2')
    expert = expert_factory(ctm=ctm1)
    Affectation.objects.create(expert=expert, ctm=ctm1, wg=wg1)
    client.force_login(expert.user)

    response = client.post(reverse('web:expert_profile_update'), {
        'first_name': 'Amina',
        'last_name': 'Expert',
        'phone': '+243810000000',
        'province': 'Haut-Katanga',
        'whatsapp_number': '+243820000000',
        'specialties': 'Géotechnique',
        'bio': 'Bio test',
        'ctm': ctm2.pk,
        'wg': wg2.pk,
    })

    assert response.status_code == 302
    assert response.url == reverse('web:app')
    expert.user.refresh_from_db()
    expert.refresh_from_db()
    assert expert.user.first_name == 'Amina'
    assert expert.user.phone == '+243810000000'
    assert expert.specialties == 'Géotechnique'
    assert expert.ctm_id == ctm2.pk
    assert list(
        Affectation.objects.filter(expert=expert, is_primary_ctm=True)
        .values_list('ctm_id', 'wg_id')
    ) == [(ctm2.pk, wg2.pk)]


@pytest.mark.django_db
def test_login_returns_to_form_via_next(client, expert_factory):
    expert = expert_factory()
    form_url = reverse('web:expert_profile_update')

    response = client.get(form_url)
    assert response.status_code == 302
    login_url = response.url
    assert login_url.startswith('/se-connecter/')
    assert 'next=' in login_url

    response = client.post(login_url, {
        'email': expert.user.email,
        'password': 'testpass123',
        'next': form_url,
    })
    assert response.status_code == 302
    assert response.url == form_url


@pytest.mark.django_db
def test_ctc_member_redirected_to_ctc_dashboard(client, expert_factory):
    expert = expert_factory()
    ctc = TechnicalCell.objects.create(name='CTC test')
    CTCMembership.objects.create(ctc=ctc, expert=expert, role='COORDINATOR')
    client.force_login(expert.user)

    response = client.post(reverse('web:expert_profile_update'), {
        'first_name': 'Amina', 'last_name': 'Expert', 'specialties': 'Geo',
    })
    assert response.status_code == 302
    assert response.url == reverse('web:ctc_dashboard')


@pytest.mark.django_db
def test_mon_profil_link_follows_expert_interface(client, expert_factory):
    expert = expert_factory()
    client.force_login(expert.user)
    url = reverse('web:expert_profile_update')

    response = client.get(url)
    assert response.context['mon_profil_url'] == reverse('web:app')

    ctc = TechnicalCell.objects.create(name='CTC test')
    CTCMembership.objects.create(ctc=ctc, expert=expert, role='COORDINATOR')
    response = client.get(url)
    assert response.context['mon_profil_url'] == reverse('web:ctc_dashboard')


@pytest.mark.django_db
def test_changing_ctm_replaces_affectation_instead_of_duplicating(
    client, expert_factory, ctm_factory, wg_factory,
):
    ctm1 = ctm_factory(number=1, name='CTM 1')
    ctm2 = ctm_factory(number=2, name='CTM 2')
    wg1 = wg_factory(ctm=ctm1, number=1, name='WG 1')
    wg2 = wg_factory(ctm=ctm2, number=1, name='WG 2')
    expert = expert_factory(ctm=ctm1)
    Affectation.objects.create(expert=expert, ctm=ctm1, wg=wg1, is_primary_ctm=True, is_primary_wg=True)
    client.force_login(expert.user)

    response = client.post(reverse('web:expert_profile_update'), {
        'first_name': 'Amina', 'last_name': 'Expert', 'specialties': 'Geo',
        'ctm': ctm2.pk, 'wg': wg2.pk,
    })
    assert response.status_code == 302
    expert.refresh_from_db()
    assert expert.ctm_id == ctm2.pk
    assert list(
        Affectation.objects.filter(expert=expert).values_list('ctm_id', 'wg_id')
    ) == [(ctm2.pk, wg2.pk)]


@pytest.mark.django_db
def test_dirigeant_still_limited_to_their_ctm(
    client, expert_factory, ctm_factory, wg_factory,
):
    ctm1 = ctm_factory(number=1, name='CTM 1')
    ctm2 = ctm_factory(number=2, name='CTM 2')
    wg1 = wg_factory(ctm=ctm1, number=1, name='WG 1')
    wg2 = wg_factory(ctm=ctm2, number=1, name='WG 2')
    expert = expert_factory(ctm=ctm1)
    comite = ComitePilotage.objects.create()
    PilotageMembreship.objects.create(comite=comite, expert=expert, role='PRESIDENT')
    client.force_login(expert.user)
    url = reverse('web:expert_profile_update')

    form = client.get(url).context['form']
    assert set(form.fields['wg'].queryset.values_list('pk', flat=True)) == {wg1.pk}
    assert form.fields['wg'].required is True

    response = client.post(url, {
        'first_name': 'Amina', 'last_name': 'Expert', 'specialties': 'Geo',
        'ctm': ctm1.pk, 'wg': wg2.pk,
    })
    assert response.status_code == 400

    response = client.post(url, {
        'first_name': 'Amina', 'last_name': 'Expert', 'specialties': 'Geo',
        'ctm': ctm1.pk, 'wg': wg1.pk,
    })
    assert response.status_code == 302


@pytest.mark.django_db
def test_ctm_without_wg_is_accepted(client, expert_factory, ctm_factory):
    ctm = ctm_factory(number=7, name='CTM sans WG')
    expert = expert_factory()
    client.force_login(expert.user)

    response = client.post(reverse('web:expert_profile_update'), {
        'first_name': 'Amina', 'last_name': 'Expert',
        'specialties': 'Geo', 'ctm': ctm.pk,
    })
    assert response.status_code == 302
    expert.refresh_from_db()
    assert expert.ctm_id == ctm.pk


@pytest.mark.django_db
def test_invalid_ctm_is_rejected_without_crash(client, expert_factory):
    expert = expert_factory()
    client.force_login(expert.user)

    response = client.post(reverse('web:expert_profile_update'), {
        'first_name': 'Amina', 'last_name': 'Expert',
        'specialties': 'Geo', 'ctm': 'abc',
    })
    assert response.status_code == 400


@pytest.mark.django_db
def test_province_uses_predefined_choices(client, expert_factory):
    expert = expert_factory()
    client.force_login(expert.user)
    url = reverse('web:expert_profile_update')

    response = client.get(url)
    choices = dict(response.context['form'].fields['province'].choices)
    assert 'Kinshasa' in choices
    assert 'Haut-Katanga' in choices
    assert 'Pas au pays' in choices

    response = client.post(url, {
        'first_name': 'Amina', 'last_name': 'Expert', 'specialties': 'Geo',
        'province': 'Kinshasa',
    })
    assert response.status_code == 302
    expert.user.refresh_from_db()
    assert expert.user.province == 'Kinshasa'

    response = client.post(url, {
        'first_name': 'Amina', 'last_name': 'Expert', 'specialties': 'Geo',
        'province': 'Province inventée',
    })
    assert response.status_code == 400
    expert.user.refresh_from_db()
    assert expert.user.province == 'Kinshasa'

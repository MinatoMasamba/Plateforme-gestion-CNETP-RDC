import pytest
from django.urls import reverse
from web.views import expert_workspace_url_name

from apps.experts.models import Structure
from apps.governance.models import (
    AvisConseiller, ComitePilotage, PilotageMembreship, PosteNominatif,
)
from apps.norms.models import Norme


def _membership(expert, role, order=None, title=None):
    comite = ComitePilotage.objects.create(name=f'Comité test {role} {order or ""}')
    PilotageMembreship.objects.create(comite=comite, expert=expert, role=role)
    if order is not None:
        PosteNominatif.objects.create(
            comite=comite,
            holder=expert,
            role=role,
            title=title or f'Poste test {order}',
            order=order,
        )
    return comite


@pytest.mark.django_db
def test_nominated_expertise_opens_only_its_interface(client, expert_factory, norme_factory):
    expert = expert_factory()
    _membership(expert, 'CONSEILLER_POLITIQUE', order=6, title='Conseiller Technique — Cabinet du Ministre')
    norme = norme_factory(title='Norme de test expertise')
    client.force_login(expert.user)

    response = client.get(reverse('web:conseiller_spaces'))

    assert response.status_code == 200
    assert response.context['space']['key'] == 'expertise'
    assert response.context['allowed_space_keys'] == ['expertise']
    assert response.context['selected_norm'] == norme
    assert b'Expertise technique' in response.content
    assert b'Aucune validation' in response.content
    assert b'changer le statut' not in response.content.lower()
    assert b'Choisir un espace' not in response.content
    assert b'Assistant IA' in response.content
    assert b'Instructions' in response.content
    assert b'Tableau de bord' in response.content
    for icon in (b'data-lucide="clipboard-list"', b'data-lucide="sparkles"',
                 b'data-lucide="sun"', b'data-lucide="moon"'):
        assert icon in response.content

    for key in ('coordination', 'conformite', 'controle', 'partenaires'):
        page = client.get(reverse('web:conseiller_spaces'), {'espace': key})
        assert page.status_code == 403


@pytest.mark.django_db
def test_login_routes_confirmed_post_to_own_dashboard(client, expert_factory):
    expert = expert_factory()
    _membership(expert, 'CONSEILLER_POLITIQUE', order=6)
    client.force_login(expert.user)

    assert expert_workspace_url_name(expert.user) == 'web:conseiller_spaces'
    response = client.get(reverse('web:pilotage_dashboard'))
    assert response.status_code == 302
    assert response.url == reverse('web:conseiller_spaces')
    legacy = client.get(reverse('web:pilotage_dashboard'), {'vue': 'pilotage'})
    assert legacy.status_code == 200


@pytest.mark.django_db
def test_unconfirmed_post_does_not_assign_an_interface(client, expert_factory):
    expert = expert_factory()
    _membership(expert, 'CONSEILLER_POLITIQUE')
    client.force_login(expert.user)

    assert expert_workspace_url_name(expert.user) == 'web:pilotage_conseillers_app'
    assert client.get(reverse('web:conseiller_spaces')).status_code == 403


@pytest.mark.django_db
def test_generic_administrator_preview_cannot_submit_specialized_avis(client, expert_factory, norme_factory):
    expert = expert_factory()
    expert.user.is_superuser = True
    expert.user.save(update_fields=['is_superuser'])
    _membership(expert, 'CONSEILLER')
    norme = norme_factory()
    client.force_login(expert.user)

    page = client.get(reverse('web:conseiller_spaces'), {'vue': 'avis'})
    response = client.post(reverse('web:conseiller_space_avis'), {
        'espace': 'expertise', 'norme': norme.pk, 'objet': 'Aperçu',
        'analyse': 'Cet avis ne doit pas être créé.', 'recommandation': 'FAVORABLE',
    })
    assert page.status_code == 200
    assert page.context['preview_mode'] is True
    assert b'Enregistrer le brouillon' not in page.content
    assert response.status_code == 403
    assert not AvisConseiller.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize('role,order,visible,hidden', [
    ('CONSEILLER_POLITIQUE', 13, 'Réserves', 'Légistique'),
    ('CONSEILLER_POLITIQUE', 16, 'Légistique', 'Calendrier'),
    ('ADMIN_TECH_FIN', 18, 'Essais et contrôles', 'Études financières'),
    ('ADMIN_TECH_FIN', 22, 'Études financières', 'Essais et contrôles'),
    ('PARTENAIRE_SOC_CIV', 23, 'Contributions', 'Consultations'),
    ('PARTENAIRE_SOC_CIV', 26, 'Consultations', 'Études financières'),
])
def test_sidebar_follows_post_mission(client, expert_factory, role, order, visible, hidden):
    expert = expert_factory()
    _membership(expert, role, order=order)
    client.force_login(expert.user)

    response = client.get(reverse('web:conseiller_spaces'))
    menu_labels = [label for _, label in response.context['space']['menu']]
    assert response.status_code == 200
    assert expert_workspace_url_name(expert.user) == 'web:conseiller_spaces'
    assert menu_labels[0] == 'Tableau de bord'
    assert visible in menu_labels
    assert hidden not in menu_labels


@pytest.mark.django_db
def test_nominated_conseiller_is_limited_to_his_space(client, expert_factory, norme_factory):
    expert = expert_factory()
    _membership(expert, 'CONSEILLER_POLITIQUE', order=13, title='Conseiller conformité')
    norme_factory(title='Norme de conformité')
    client.force_login(expert.user)

    default = client.get(reverse('web:conseiller_spaces'))
    forbidden = client.get(reverse('web:conseiller_spaces'), {'espace': 'expertise'})

    assert default.status_code == 200
    assert default.context['space']['key'] == 'conformite'
    assert default.context['allowed_space_keys'] == ['conformite']
    assert forbidden.status_code == 403


@pytest.mark.django_db
def test_atf_cannot_read_or_post_another_space(client, expert_factory, norme_factory):
    or_structure = Structure.objects.create(name='Office des Routes test', acronym='OR', category='ADMIN')
    expert = expert_factory(structure=or_structure)
    _membership(expert, 'ADMIN_TECH_FIN', order=18, title='Office des Routes')
    norme = norme_factory(title='Norme routes')
    client.force_login(expert.user)

    page = client.get(reverse('web:conseiller_spaces'))
    forbidden = client.get(reverse('web:conseiller_spaces'), {'espace': 'partenaires'})
    post = client.post(reverse('web:conseiller_space_avis'), {
        'espace': 'partenaires',
        'norme': norme.pk,
        'objet': 'Avis indu',
        'analyse': 'Cet avis ne doit pas être créé.',
        'recommandation': 'FAVORABLE',
        'action': 'soumettre',
    })

    assert page.status_code == 200
    assert page.context['space']['key'] == 'controle'
    assert forbidden.status_code == 403
    assert post.status_code == 403
    assert AvisConseiller.objects.count() == 0


@pytest.mark.django_db
def test_avis_is_created_and_submitted_without_changing_norm_status(client, expert_factory, norme_factory):
    expert = expert_factory()
    _membership(expert, 'CONSEILLER_POLITIQUE', order=6, title='Conseiller Technique — Cabinet du Ministre')
    norme = norme_factory(title='Norme à examiner', status='CTM_REVIEW')
    client.force_login(expert.user)

    response = client.post(reverse('web:conseiller_space_avis'), {
        'espace': 'expertise',
        'norme': norme.pk,
        'objet': 'Pertinence des dispositions techniques',
        'analyse': 'Les essais prévus sont adaptés, sous réserve du suivi des résultats.',
        'recommandation': 'RESERVE',
        'action': 'soumettre',
    })

    avis = AvisConseiller.objects.get()
    norme.refresh_from_db()
    assert response.status_code == 302
    assert avis.statut == AvisConseiller.Statut.SOUMIS
    assert avis.profil == AvisConseiller.Profil.EXPERTISE
    assert avis.soumis_le is not None
    assert norme.status == 'CTM_REVIEW'


@pytest.mark.django_db
def test_draft_is_not_presented_as_submitted(client, expert_factory, norme_factory):
    expert = expert_factory()
    _membership(expert, 'CONSEILLER_POLITIQUE', order=6, title='Conseiller Technique — Cabinet du Ministre')
    norme = norme_factory()
    client.force_login(expert.user)

    client.post(reverse('web:conseiller_space_avis'), {
        'espace': 'expertise',
        'norme': norme.pk,
        'objet': 'Brouillon de travail',
        'analyse': 'Analyse encore en cours.',
        'recommandation': 'COMPLEMENT',
        'action': 'brouillon',
    })

    page = client.get(reverse('web:conseiller_spaces'), {'vue': 'avis'})
    avis = AvisConseiller.objects.get()
    assert avis.statut == AvisConseiller.Statut.BROUILLON
    assert avis.soumis_le is None
    assert b'Brouillon de travail' in page.content
    assert b'Transmis au circuit' not in page.content


@pytest.mark.django_db
def test_avis_rejects_norm_outside_mandate(client, expert_factory, norme_factory, ctm_factory):
    or_structure = Structure.objects.create(name='Office des Routes test 2', acronym='OR', category='ADMIN')
    expert = expert_factory(structure=or_structure)
    _membership(expert, 'ADMIN_TECH_FIN', order=18)
    outside = norme_factory(ctm=ctm_factory(number=7), title='Norme hors périmètre')
    client.force_login(expert.user)

    response = client.post(reverse('web:conseiller_space_avis'), {
        'espace': 'controle',
        'norme': outside.pk,
        'objet': 'Avis hors périmètre',
        'analyse': 'Cet avis ne doit pas être créé.',
        'recommandation': 'FAVORABLE',
        'action': 'soumettre',
    })

    assert response.status_code == 404
    assert AvisConseiller.objects.count() == 0
    assert Norme.all_objects.get(pk=outside.pk)

@pytest.mark.django_db
def test_sidebar_tabs_render_one_content_at_a_time(client, expert_factory, norme_factory):
    expert = expert_factory()
    _membership(expert, 'CONSEILLER_POLITIQUE', order=6, title='Conseiller Technique — Cabinet du Ministre')
    norme_factory(title='Norme onglets')
    client.force_login(expert.user)

    avis = client.get(reverse('web:conseiller_spaces'), {'vue': 'avis'})
    documents = client.get(reverse('web:conseiller_spaces'), {'vue': 'documents'})
    fallback = client.get(reverse('web:conseiller_spaces'), {'vue': 'inconnue'})

    assert avis.status_code == 200
    assert avis.context['active_vue'] == 'avis'
    assert b"Objet de l'avis" in avis.content
    assert b'Indicateurs du p' not in avis.content

    assert documents.status_code == 200
    assert documents.context['active_vue'] == 'documents'
    assert b'Documents et versions' in documents.content
    assert b"Objet de l'avis" not in documents.content

    assert fallback.status_code == 200
    assert fallback.context['active_vue'] == 'overview'
    assert b'Indicateurs du p' in fallback.content

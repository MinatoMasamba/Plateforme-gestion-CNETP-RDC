"""Accès et données du tableau de bord des présidents de sous-commission."""

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.governance.models import GroupeCible, Organe, Tache
from apps.governance.phoenix_models import (
    MandatOrganisation, OrganisationVersion, PosteOrganisation, RattachementDocumentaire,
)
from apps.norms.models import NormeVersion


pytestmark = pytest.mark.django_db


def _active_sc(code):
    version = OrganisationVersion.objects.create(
        code=f'active-{code.lower()}', name=f'Organisation {code}', status='ACTIVE',
        source_document='Acte de test', activation_reference='ACT-1',
        gt_catalogue_reference='GT-1', permissions_reference='HAB-1', circuit_reference='CIR-1',
    )
    sc = Organe.objects.create(version=version, type='SC', code=code, name=code,
                               status='ACTIVE', source_reference='Acte de test')
    group = GroupeCible.objects.create(sc=sc, code=f'{code}-GT1', name='Groupe de test', activity='PRODUCTION',
                                       source_reference='Acte de test')
    return version, sc, group


def _mandate(expert, sc):
    post = PosteOrganisation.objects.create(
        organe=sc, code=f'{sc.code}-PRES', category='PRESIDENCY', title='Président de sous-commission',
        status='ACTIVE', source_reference='Acte de nomination',
    )
    return MandatOrganisation.objects.create(
        expert=expert, poste=post, function='Président de sous-commission',
        status='ACTIVE', capacity='ORGANISATION', appointment_reference='NOM-1',
        start_date=timezone.localdate(),
    )


def test_sc_bureau_roles_have_a_clickable_sidebar_link(client, expert_factory, user_factory):
    visitor = expert_factory()
    client.force_login(visitor.user)
    assert client.get(reverse('web:president_sc')).status_code == 403
    assert 'Suivi des normes de ma SC' not in client.get(reverse('web:app')).content.decode()
    _, sc, _ = _active_sc('SC-TEST')
    for number, (title, category) in enumerate((
        ('Président', 'PRESIDENCY'), ('1e Vice-Président', 'PRESIDENCY'),
        ('Rapporteur', 'MEMBER'), ('Secrétaire', 'SECRETARIAT'),
    ), start=1):
        expert = expert_factory(user=user_factory(username=f'sc-bureau-{number}', email=f'sc-{number}@example.test'))
        post = PosteOrganisation.objects.create(
            organe=sc, code=f'SC-TEST-BUREAU-{number}', category=category, title=title,
            status='VALIDATED', source_reference='Acte de nomination',
        )
        MandatOrganisation.objects.create(
            expert=expert, poste=post, function=title, status='ACTIVE',
            capacity='ORGANISATION', appointment_reference=f'NOM-{number}',
            start_date=timezone.localdate(),
        )
        client.force_login(expert.user)
        sidebar = client.get(reverse('web:app')).content.decode()
        assert 'Suivi des normes de ma SC' in sidebar
        assert f'href="{reverse("web:president_sc")}"' in sidebar
        assert client.get(reverse('web:president_sc')).status_code == 200
        assert client.get(reverse('web:president_sc_data')).json()['scope']['code'] == 'SC-TEST'


def test_norms_tasks_versions_and_historical_filters_stay_in_sc(client, expert_factory, norme_factory, ctm_factory, wg_factory):
    president = expert_factory()
    contributor = expert_factory(user=president.user.__class__.objects.create_user(
        username='contributor', email='contributor@example.test', password='testpass123'))
    client.force_login(president.user)
    version, sc, group = _active_sc('SC-OWN')
    _mandate(president, sc)
    ctm = ctm_factory()
    wg = wg_factory(ctm=ctm)
    norm = norme_factory(ctm=ctm, wg=wg, reference_number='NCD-OWN')
    other = norme_factory(reference_number='NCD-OTHER')
    RattachementDocumentaire.objects.create(
        norme=norm, version=version, sc=sc, gt=group, role='OWNER', status='VALIDATED',
        decision_reference='DEC-1', effective_from=timezone.localdate(),
    )
    Tache.objects.create(target_group=group, norme=norm, titre='Rédaction', assigned_to=contributor,
                         status='COMPLETED')
    NormeVersion.all_objects.create(norme=norm, version_number=1, title='Version initiale', content='Texte réel')
    NormeVersion.all_objects.create(norme=norm, version_number=2, title='Version revue', content='Texte conservé')

    data = client.get(reverse('web:president_sc_data'), {'sc': sc.pk, 'ctm': ctm.pk, 'wg': wg.pk}).json()
    assert [item['code'] for item in data['norms']] == ['NCD-OWN']
    assert data['norms'][0]['rows'][0]['done'] == 1
    assert [item['content'] for item in data['norms'][0]['versions']] == ['Texte conservé', 'Texte réel']
    assert client.get(reverse('web:president_sc_data'), {'sc': sc.pk, 'ctm': other.ctm_id}).json()['norms'] == []
    assert client.get(reverse('web:president_sc_data'), {'sc': sc.pk + 999}).status_code == 403


@pytest.mark.django_db(transaction=True)
def test_president_browser_updates_reader_and_experts(live_server, client, expert_factory, norme_factory):
    from urllib.parse import urlparse
    from playwright.sync_api import sync_playwright

    president = expert_factory()
    contributor = expert_factory(user=president.user.__class__.objects.create_user(
        username='browser-contributor', email='browser-contributor@example.test', password='testpass123'))
    version, sc, group = _active_sc('SC-BROWSER')
    _mandate(president, sc)
    first = norme_factory(title='Norme première', reference_number='NCD-BROWSER-1')
    second = norme_factory(title='Norme seconde', reference_number='NCD-BROWSER-2')
    for norm in (first, second):
        RattachementDocumentaire.objects.create(
            norme=norm, version=version, sc=sc, gt=group, role='CONTRIBUTOR',
            status='VALIDATED', decision_reference=f'DEC-{norm.pk}',
            effective_from=timezone.localdate(),
        )
    Tache.objects.create(target_group=group, norme=second, titre='Étude', assigned_to=contributor,
                         status='COMPLETED')
    NormeVersion.all_objects.create(norme=first, version_number=1, title=first.title, content='Texte premier')
    NormeVersion.all_objects.create(norme=second, version_number=1, title=second.title, content='Texte second')
    client.force_login(president.user)
    host = urlparse(live_server.url).hostname
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        for width, height, theme in ((1440, 900, 'dark'), (390, 844, 'light')):
            context = browser.new_context(viewport={'width': width, 'height': height})
            context.add_init_script(f"localStorage.setItem('theme-preference', '{theme}')")
            context.add_cookies([{'name': 'sessionid', 'value': client.cookies['sessionid'].value,
                                  'domain': host, 'path': '/'}])
            page = context.new_page()
            page.route('https://cdn.tailwindcss.com', lambda route: route.fulfill(
                path='/home/minato/project/templates/static/vendor/tailwindcss.js',
                content_type='application/javascript'))
            page.route('https://unpkg.com/lucide@latest', lambda route: route.fulfill(
                path='/home/minato/project/templates/static/vendor/lucide.js',
                content_type='application/javascript'))
            page.goto(f'{live_server.url}{reverse("web:app")}', wait_until='domcontentloaded')
            if width < 768 and 'mobile-sidebar-open' not in page.locator('#sidebar-container').get_attribute('class'):
                page.locator('[data-bottom-tab="editor"]').click()
            page.get_by_role('link', name='Ouvrir le suivi des normes de ma sous-commission').click()
            assert page.url.startswith(f'{live_server.url}{reverse("web:president_sc")}')
            assert page.locator('html').evaluate('(node) => node.classList.contains("dark")') == (theme == 'dark')
            assert page.locator('#reader-title').inner_text() == 'Norme première'
            page.get_by_role('link', name='Norme seconde').first.click()
            assert page.locator('#reader-title').inner_text() == 'Norme seconde'
            assert page.locator('#expert-count').inner_text() == '1'
            page.screenshot(path=f'/tmp/president-sc-{width}.png', full_page=True)
            page.get_by_role('button', name='Changer le thème').click()
            assert page.locator('html').evaluate('(node) => node.classList.contains("dark")') != (theme == 'dark')
            page.get_by_role('button', name='Historique').click()
            assert page.locator('#document-panel').is_hidden()
            page.get_by_role('button', name='Version 1').click()
            assert page.get_by_text('Texte second').is_visible()
            context.close()
        browser.close()

"""Parcours navigateur du circuit de réponse aux dérogations."""

import pytest
from django.conf import settings
from django.test import Client
from playwright.sync_api import sync_playwright

from apps.governance.models import ComitePilotage, PermissionRequest, PilotageMembreship


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_pilotage_reply_desktop_and_requester_mobile(live_server, client, expert_factory, user_factory):
    committee = ComitePilotage.objects.create(name='Pilotage navigateur')
    requester = expert_factory(user=user_factory(
        username='browser_requester', email='browser_requester@cnetp.cd',
        first_name='Amina', last_name='Demandeuse',
    ))
    reviewer = expert_factory(user=user_factory(
        username='browser_reviewer', email='browser_reviewer@cnetp.cd',
        first_name='Jean', last_name='Répondant',
    ))
    PilotageMembreship.objects.create(comite=committee, expert=requester, role='CONSEILLER')
    PilotageMembreship.objects.create(comite=committee, expert=reviewer, role='SECRETARY')
    permission = PermissionRequest.objects.create(
        requester=requester, restricted_resource='Console globale', reason='Consulter le dossier demandé.',
    )
    client.force_login(reviewer.user)
    reviewer_session = client.cookies[settings.SESSION_COOKIE_NAME].value
    requester_client = Client()
    requester_client.force_login(requester.user)
    requester_session = requester_client.cookies[settings.SESSION_COOKIE_NAME].value

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            desktop = browser.new_context(viewport={'width': 1440, 'height': 900})
            desktop.add_cookies([{
                'name': settings.SESSION_COOKIE_NAME,
                'value': reviewer_session,
                'url': live_server.url,
            }])
            reviewer_page = desktop.new_page()
            reviewer_page.goto(live_server.url + '/pilotage/#panel-requests')
            reviewer_page.locator(f'#comment-{permission.pk}').fill('Accès refusé après examen du dossier.')
            reviewer_page.locator(f'#btn-rejected-{permission.pk}').click()
            reviewer_page.get_by_text('Réponse envoyée par mail.').wait_for()
            reviewer_page.get_by_text('Réponses récentes').wait_for()
            assert reviewer_page.get_by_text('Jean Répondant').count() >= 1
            reviewer_page.screenshot(path='/tmp/pilotage-derogation-directoire.png')

            mobile = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True)
            mobile.add_cookies([{
                'name': settings.SESSION_COOKIE_NAME,
                'value': requester_session,
                'url': live_server.url,
            }])
            requester_page = mobile.new_page()
            requester_page.goto(live_server.url + '/pilotage/')
            requester_page.get_by_text('Mes Demandes de Dérogation').wait_for()
            assert requester_page.get_by_text('Réponse de Jean Répondant').is_visible()
            assert requester_page.get_by_text('Accès refusé après examen du dossier.').is_visible()
            requester_page.get_by_text('Réponse de Jean Répondant').scroll_into_view_if_needed()
            requester_page.screenshot(path='/tmp/pilotage-derogation-mobile.png')
        finally:
            browser.close()

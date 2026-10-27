"""Capture the local Django reference and Flutter public pages without submitting data."""
import argparse
import re
import sys
from pathlib import Path
from playwright.sync_api import expect, sync_playwright


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--flutter', default='http://127.0.0.1:8082')
    parser.add_argument('--django', default='http://127.0.0.1:8001')
    parser.add_argument('--exercise', action='store_true')
    args = parser.parse_args()
    output = Path('reports/portal_parity')
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        def enable_semantics():
            placeholder = page.locator('flt-semantics-placeholder')
            if placeholder.count():
                placeholder.evaluate('(el) => el.click()')
                page.wait_for_timeout(500)
        for name, url in [
            ('django_home', args.django + '/'),
            ('django_login', args.django + '/se-connecter/'),
            ('django_registration', args.django + '/inscription-expert/'),
            ('flutter_home', args.flutter + '/#/'),
            ('flutter_login', args.flutter + '/#/login'),
            ('flutter_registration', args.flutter + '/#/candidature'),
            ('flutter_reset', args.flutter + '/#/mot-de-passe-oublie'),
        ]:
            page.goto(url, wait_until='networkidle', timeout=90000)
            page.wait_for_timeout(3500 if name.startswith('django') else 1500)
            if name.startswith('flutter'):
                enable_semantics()
            page.screenshot(path=str(output / f'{name}.png'), full_page=not name.startswith('flutter'))
            print(name, page.url, page.locator('body').inner_text()[:1500], flush=True)
        if args.exercise:
            page.goto(args.flutter + '/#/login', wait_until='networkidle')
            enable_semantics()
            page.get_by_role('button', name='Mot de passe oublié ?').click()
            page.get_by_role('button', name='Envoyer le code').click()
            assert 'Saisissez une adresse email valide.' in page.locator('body').inner_text()
            page.get_by_role('button', name='Retour à la connexion').click()
            page.get_by_role('button', name=re.compile('Déposer une candidature')).click()
            page.get_by_role('button', name='Étape suivante').click()
            assert 'Champ requis' in page.locator('body').inner_text()
            for label, value in [('Prénom', 'Alice'), ('Nom et Post-nom', 'Test'),
                                 ('Email', 'ui-check@example.test'), ('Mot de passe', 'Test-passphrase-2026!'),
                                 ('Confirmer le mot de passe', 'Test-passphrase-2026!')]:
                page.get_by_role('textbox', name=label, exact=True).fill(value)
            page.get_by_role('button', name='Étape suivante').click()
            assert "Organisation d'origine" in page.locator('body').inner_text()
            page.screenshot(path=str(output / 'flutter_registration_step2.png'))
            page.get_by_role('button', name='Précédent').click()
            page.wait_for_timeout(500)
            page.screenshot(path=str(output / 'flutter_registration_back.png'))
            expect(page.get_by_role('textbox', name='Prénom', exact=True)).to_have_value('Alice')
            page.set_viewport_size({'width': 390, 'height': 844})
            for name, route in [('home', '/'), ('login', '/login'), ('registration', '/candidature'), ('reset', '/mot-de-passe-oublie')]:
                page.goto(args.flutter + '/#' + route, wait_until='networkidle')
                page.wait_for_timeout(600)
                page.screenshot(path=str(output / f'flutter_mobile_{name}.png'))
            print('PUBLIC_NAVIGATION_AND_VALIDATION_OK', flush=True)
        print('BROWSER_ERRORS', errors, flush=True)
        browser.close()


if __name__ == '__main__':
    main()

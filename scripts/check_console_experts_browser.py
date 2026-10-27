"""Capture and inspect the two expert changelist variants on the local server."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from playwright.sync_api import sync_playwright


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    user = get_user_model().objects.filter(is_active=True, is_superuser=True).first()
    if not user:
        raise RuntimeError('Aucun compte administrateur local disponible.')
    client = Client()
    client.force_login(user, backend='django.contrib.auth.backends.ModelBackend')
    output = Path('reports/console_experts')
    output.mkdir(parents=True, exist_ok=True)
    verify = '--verify' in sys.argv
    suffix = '_after' if verify else ''
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        context.add_cookies([{'name': settings.SESSION_COOKIE_NAME,
                             'value': client.cookies[settings.SESSION_COOKIE_NAME].value,
                             'url': 'http://127.0.0.1:1111/'}])
        page = context.new_page()
        for name, query in [('all', ''), ('pending', '?status=PENDING')]:
            page.goto('http://127.0.0.1:1111/dashboard/administration/modeles/experts/expert/' + query, wait_until='networkidle')
            page.screenshot(path=str(output / f'{name}{suffix}.png'), full_page=False)
            print(name, page.url, page.locator('body').inner_text()[:1600])
            print(page.evaluate('''() => ({
                viewport: innerWidth, document: document.documentElement.scrollWidth,
                table: document.querySelector('#result_list')?.getBoundingClientRect().toJSON(),
                filters: document.querySelectorAll('.console-filter-choice').length,
                cellPadding: document.querySelector('#result_list td') && getComputedStyle(document.querySelector('#result_list td')).padding,
                filterHeight: document.querySelector('.console-filter-group')?.parentElement.getBoundingClientRect().height,
            })'''))
            if verify:
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                selected = page.locator('[data-console-filter-select]').first.locator('option:checked').inner_text()
                assert selected == ('En attente' if query else 'Tout'), selected
                assert page.locator('[data-console-filter-select]').count() == 3
                if name == 'all' and page.locator('#result_list td').count():
                    assert page.locator('#result_list td').first.evaluate('(el) => getComputedStyle(el).padding') == '13px 14px'
        page.set_viewport_size({'width': 390, 'height': 844})
        page.reload(wait_until='networkidle')
        page.screenshot(path=str(output / f'pending_mobile{suffix}.png'), full_page=True)
        if verify:
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert page.locator('#console-sidebar').evaluate('(el) => getComputedStyle(el).boxShadow') == 'none'
            page.get_by_role('button', name='Afficher ou masquer le menu').click()
            assert page.locator('#console-sidebar').evaluate('(el) => el.classList.contains("is-open")')
            page.keyboard.press('Escape')
            assert not page.locator('#console-sidebar').evaluate('(el) => el.classList.contains("is-open")')
            page.locator('[data-console-filter-select]').first.select_option(label='Actif')
            page.wait_for_url('**/*status__exact=ACTIVE*')
            page.wait_for_load_state('networkidle')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(output / 'active_mobile_after.png'))
            print('RESPONSIVE_LAYOUT_AND_FILTER_NAVIGATION_OK')
        browser.close()
    client.logout()


if __name__ == '__main__':
    main()

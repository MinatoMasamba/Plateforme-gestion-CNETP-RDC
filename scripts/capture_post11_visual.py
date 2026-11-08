"""Captures navigateur du poste 11 : sidebar, dashboard, rapports, mobile."""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:1111'
OUT = Path('reports/poste11_ged/visual')
OUT.mkdir(parents=True, exist_ok=True)


def login(page):
    page.goto(f'{BASE}/se-connecter/', wait_until='domcontentloaded')
    html = page.content()
    token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
    response = page.request.post(f'{BASE}/se-connecter/', form={
        'csrfmiddlewaretoken': token, 'email': 'sourceacademique@gmail.com', 'password': 'Visual2026!'},
        headers={'Referer': f'{BASE}/se-connecter/'})
    assert response.status in (200, 302), f'login {response.status}'
    page.goto(f'{BASE}/ctc/', wait_until='domcontentloaded')
    assert 'se-connecter' not in page.url, page.url


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        page.on('console', lambda m: errors.append(f'console.{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        page.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
        login(page)
        page.wait_for_selector('[data-ged-workspace]', timeout=30000)
        page.wait_for_timeout(4000)
        page.screenshot(path=str(OUT / '01_dashboard_desktop.png'), full_page=True)

        # navigation par la sidebar
        for view, name in [('indexation', '02_indexation'), ('codification', '03_codification'),
                           ('versions', '04_versions'), ('ged_anomalies', '05_anomalies'),
                           ('rapports', '06_rapports')]:
            btn = page.locator(f'[data-sidebar-view="{view}"]')
            if btn.count():
                btn.first.click()
                page.wait_for_timeout(2500)
                page.screenshot(path=str(OUT / f'{name}.png'), full_page=True)
            else:
                errors.append(f'sidebar manquante: {view}')

        # sidebar rétractable
        toggle = page.locator('[data-sidebar-toggle], .cnetp-sidebar-resize, #sidebar-reopen-btn')
        page.screenshot(path=str(OUT / '07_sidebar_open.png'))
        errors.append(f'toggles trouves: {[t for t in ["data-sidebar-toggle", "cnetp-sidebar-resize", "sidebar-reopen-btn"] if page.locator(t).count()]}')

        # mobile
        mob = browser.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True)
        mob.on('pageerror', lambda e: errors.append(f'mobile pageerror: {e}'))
        login(mob)
        mob.wait_for_selector('[data-ged-workspace]', timeout=30000)
        mob.wait_for_timeout(3000)
        mob.screenshot(path=str(OUT / '08_dashboard_mobile.png'), full_page=True)
        browser.close()
    print('\n'.join(errors) if errors else 'AUCUNE ERREUR CONSOLE')
    print(f'captured -> {OUT}')


if __name__ == '__main__':
    sys.exit(main())

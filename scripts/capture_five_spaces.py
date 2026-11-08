"""Recette navigateur des 19 postes ST : captures, navigation et refus serveur.

Utiliser une copie de base préparée par prepare_five_spaces_db.py et le même
SQLITE_NAME pour ce script et le serveur. Les portes de recette visuelle et
métier sont séparées : une page de module à venir ne prouve aucune fonction.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
DESKTOP = {'width': 1440, 'height': 900}
MOBILE = {'width': 390, 'height': 844}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:1114')
    parser.add_argument('--out', default=str(BASE_DIR / 'reports/recette_prompt/apres'))
    parser.add_argument('--manifest', default=str(BASE_DIR / 'reports/recette_prompt/roles.json'))
    parser.add_argument('--only', default='')
    args = parser.parse_args()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_test')
    import django
    django.setup()
    from django.conf import settings
    from django.test import Client
    from apps.experts.models import Expert
    from apps.governance.phoenix_runtime import active_st_mandate
    from apps.governance.st_spaces import allowed_views_for_post, menu_for_post, space_for_post, SPACES
    from playwright.sync_api import sync_playwright

    roles = json.loads(Path(args.manifest).read_text())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    records, failures = [], []
    profiles = []
    for code, info in roles.items():
        if args.only and args.only not in (code, info['pole']):
            continue
        expert = Expert.objects.select_related('user').get(user__email=info['email'])
        mandate = active_st_mandate(expert)
        client = Client()
        client.force_login(expert.user, backend='django.contrib.auth.backends.ModelBackend')
        profiles.append((code, allowed_views_for_post(mandate.poste), menu_for_post(mandate.poste),
                         SPACES[space_for_post(mandate.poste)]['home'],
                         client.cookies[settings.SESSION_COOKIE_NAME].value))
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome', headless=True)
        for code, allowed, menu, home, session in profiles:
            folder = out / code
            folder.mkdir(exist_ok=True)
            for label, viewport in [('pc', DESKTOP), ('mobile', MOBILE)]:
                context = browser.new_context(viewport=viewport, locale='fr-FR',
                    is_mobile=label == 'mobile', has_touch=label == 'mobile', reduced_motion='reduce')
                # Font fallback is deliberate: the UI must work with local assets only.
                context.route('https://fonts.googleapis.com/**', lambda route: route.abort())
                context.route('https://cdn.jsdelivr.net/**', lambda route: route.abort())
                context.add_cookies([{'name': settings.SESSION_COOKIE_NAME,
                    'value': session, 'url': args.base_url + '/'}])
                page = context.new_page()
                errors, network = [], []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.on('response', lambda r: network.append({'status': r.status, 'url': r.url})
                    if r.status >= 500 else None)
                try:
                    response = page.goto(args.base_url + '/ctc/', wait_until='domcontentloaded', timeout=120000)
                    page.wait_for_function("window.CTC_CTX && window.switchView && document.querySelector('#sidebar-nav-principal button')")
                    page.wait_for_timeout(200)
                    home_metrics = page.evaluate('''() => {
                        const visible = document.querySelector('.view-container:not(.hidden)');
                        const main = document.querySelector('#ctc-main');
                        const work = visible?.querySelector('#workday-title')?.getBoundingClientRect();
                        return {
                            hash: location.hash.slice(1), menu: document.querySelectorAll('#sidebar-nav-principal button').length,
                            blocks: ['todo','waiting','deadlines','recent'].map(x => !!visible?.querySelector('#workday-'+x)),
                            rail: !!visible?.querySelector('[aria-label="Alertes et échéances"]'),
                            footer: !!document.querySelector('footer'),
                            workday_visible: !!work && work.bottom < main.getBoundingClientRect().bottom,
                            overflow: document.documentElement.scrollWidth > innerWidth + 2,
                            styled: getComputedStyle(visible.querySelector('.st-space-kpis')).display === 'grid',
                        };
                    }''')
                    record = dict(post=code, viewport=label, http=response.status, home=home_metrics,
                                  forbidden=[], views=[], errors=errors, network=network)
                    page.screenshot(path=str(folder / f'home_{label}.png'), animations='disabled')
                    page.locator('#workday-title').scroll_into_view_if_needed()
                    page.screenshot(path=str(folder / f'workday_{label}.png'), animations='disabled')
                    page.evaluate("document.querySelector('#ctc-main').scrollTop = 1000000")
                    page.screenshot(path=str(folder / f'bottom_{label}.png'), animations='disabled')
                    for item in menu:
                        view = item['view']
                        if view == home:
                            continue
                        if label == 'mobile':
                            page.locator('#mobile-menu-btn').click()
                        page.locator('#sidebar-nav-principal button').filter(has_text=item['label']).click()
                        page.wait_for_timeout(80)
                        metrics = page.evaluate('''() => {
                            const v = document.querySelector('.view-container:not(.hidden)');
                            const m = document.querySelector('#ctc-main');
                            return {hash: location.hash.slice(1), id: v?.id,
                                overflow: m.scrollWidth > m.clientWidth + 2,
                                placeholder: !!v?.querySelector('[data-st-incomplete]')};
                        }''')
                        page.screenshot(path=str(folder / f'{view}_{label}.png'), animations='disabled')
                        record['views'].append(dict(view=view, **metrics))
                    forbidden = next((v for v in ['ptn','accounts','legal','indexation','communication','financial'] if v not in allowed), None)
                    if forbidden:
                        denied = context.request.get(args.base_url + f'/ctc/espace/{forbidden}/')
                        absent = page.locator('#view-' + forbidden).count() == 0
                        page.evaluate('(v) => window.switchView(v)', forbidden)
                        record['forbidden'].append(dict(view=forbidden, http=denied.status,
                            html_absent=absent, hash_redirect=page.evaluate('location.hash.slice(1)') == home))
                    # All roles get a second visual check in dark mode.
                    page.evaluate('(v) => { window.switchView(v); document.documentElement.classList.add("dark"); }', home)
                    page.screenshot(path=str(folder / f'home_{label}_dark.png'), animations='disabled')
                    page.locator('#workday-title').scroll_into_view_if_needed()
                    page.screenshot(path=str(folder / f'workday_{label}_dark.png'), animations='disabled')
                    record['visual_ok'] = (
                        response.status == 200 and home_metrics['hash'] == home
                        and 5 <= home_metrics['menu'] <= 7 and all(home_metrics['blocks'])
                        and home_metrics['rail'] and home_metrics['footer'] and home_metrics['styled']
                        and home_metrics['workday_visible'] and not home_metrics['overflow']
                        and not errors and not network
                        and all(v['hash'] == v['view'] and not v['overflow'] for v in record['views'])
                        and all(v['http'] == 403 and v['html_absent'] and v['hash_redirect'] for v in record['forbidden'])
                    )
                    record['business_incomplete'] = [v['view'] for v in record['views'] if v['placeholder']]
                    records.append(record)
                    if not record['visual_ok']:
                        failures.append(record)
                    print(f"{'PASS' if record['visual_ok'] else 'FAIL'} {code} {label} "
                          f"metier_incomplet={record['business_incomplete']}", flush=True)
                except Exception as exc:
                    failure = dict(post=code, viewport=label, error=str(exc), visual_ok=False)
                    records.append(failure)
                    failures.append(failure)
                    print(f'FAIL {code} {label}: {exc}', flush=True)
                    page.screenshot(path=str(folder / f'error_{label}.png'), timeout=5000)
                finally:
                    # Persist after each profile: interruption never leaves a false summary.
                    (out / 'manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2))
                    context.close()
        browser.close()
    tested = sorted({r['post'] for r in records})
    lines = ['# Recette navigateur ST v3', '',
        f'Postes parcourus : {len(tested)}/19. Formats : 1440×900 et 390×844.',
        f'Contrôles navigateur : {len(records)-len(failures)} PASS, {len(failures)} FAIL.',
        'Les captures sombres sont à examiner visuellement. Un PASS navigateur ne vaut pas recette métier.', '',
        '| Poste | Format | Navigateur | Modules métier incomplets |', '|---|---|---|---|']
    for r in records:
        lines.append(f"| {r['post']} | {r['viewport']} | {'PASS' if r['visual_ok'] else 'FAIL'} | {', '.join(r.get('business_incomplete', [])) or r.get('error', '—')} |")
    (out / 'INDEX.md').write_text('\n'.join(lines)+'\n')
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

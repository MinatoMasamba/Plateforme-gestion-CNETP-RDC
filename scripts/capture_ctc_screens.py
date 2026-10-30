"""Capture every CTC web screen for desktop and mobile training material.

Prerequisites:
    mon_env/bin/python scripts/prepare_ctc_capture_db.py
    SQLITE_NAME=/tmp/ctc_capture.sqlite3 DEBUG=True \
        mon_env/bin/python manage.py runserver 127.0.0.1:1112 --noreload

Usage:
    mon_env/bin/python scripts/capture_ctc_screens.py \
        --db /tmp/ctc_capture.sqlite3 --base-url http://127.0.0.1:1112 \
        --out captures_ctc --roles /tmp/ctc_roles.json
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

ROLE_ORDER = [
    'coordonnateur_principal', 'coordonnateur_adjoint', 'assistant_executif',
    'veille_acgt', 'veille_sg', 'expert_juridique', 'sauvegardes_ci',
    'planification_recons', 'economiste_foner', 'scientifique_inbtp',
    'gaf', 'responsable_enquetes', 'liaison_fec', 'communicateur',
    'sig_beau', 'sig_ovd', 'operateur_saisie', 'it_btc', 'it_sg_itp',
]

# (view id, role, variant label or None)
INTERFACE_CAPTURES = [
    ('dossiers', 'coordonnateur_principal', None),
    ('dossiers', 'assistant_executif', 'assistant'),
    ('dossiers', 'operateur_saisie', 'operateur'),
    ('assignations', 'coordonnateur_principal', None),
    ('assignations', 'veille_sg', 'analyste'),
    ('assignations', 'expert_juridique', 'juridique'),
    ('ctc_requests', 'assistant_executif', None),
    ('assistant_executif', 'assistant_executif', None),
    ('financial', 'gaf', None),
    ('statistiques', 'coordonnateur_principal', None),
    ('experts', 'coordonnateur_principal', None),
    ('tracabilite', 'coordonnateur_principal', None),
    ('homologations', 'coordonnateur_principal', None),
    ('instructions', 'coordonnateur_principal', None),
    ('reunions', 'coordonnateur_principal', None),
    ('drive', 'it_sg_itp', None),
    ('archives', 'coordonnateur_principal', None),
    ('parametres', 'coordonnateur_principal', None),
    ('parametres', 'it_sg_itp', 'admin'),
]

MENU_VARIANTS = [
    ('defaut', 'coordonnateur_principal'),
    ('gaf', 'gaf'),
    ('assistant_executif', 'assistant_executif'),
    ('it', 'it_sg_itp'),
]

DESKTOP = (1440, 900)
MOBILE = (390, 844)
MAX_CONTENT_HEIGHT = 24000


def slug(value: str) -> str:
    return value.replace('/', '-').replace(' ', '-')


class Capture:
    def __init__(self, base_url: str, out: Path):
        self.base_url = base_url.rstrip('/')
        self.out = out
        self.records: list[dict] = []
        self.pages: dict[tuple[str, bool], tuple[object, object, list[str]]] = {}

    def add(self, path: Path, **meta) -> None:
        self.records.append({
            'path': str(path.relative_to(self.out)),
            'width': meta.get('width'),
            'height': meta.get('height'),
            'role': meta.get('role'),
            'view': meta.get('view'),
            'kind': meta.get('kind'),
            'scroll_ok': meta.get('scroll_ok'),
            'errors': meta.get('errors') or [],
        })

    def _page(self, browser, session: str, role: str, size: tuple[int, int]):
        width, height = size
        mobile = width < 768
        key = (role, mobile)
        if key not in self.pages:
            context = browser.new_context(
                viewport={'width': width, 'height': height},
                device_scale_factor=1,
                is_mobile=mobile,
                has_touch=mobile,
                locale='fr-FR',
            )
            context.add_cookies([{
                'name': 'sessionid', 'value': session, 'url': self.base_url + '/',
            }])
            page = context.new_page()
            errors: list[str] = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            try:
                page.goto(f'{self.base_url}/ctc/#dashboard', wait_until='domcontentloaded', timeout=90000)
                page.wait_for_selector('#ctc-ctx-data', state='attached', timeout=30000)
                page.wait_for_timeout(700)
            except Exception:
                context.close()
                raise
            self.pages[key] = (context, page, errors)
        return self.pages[key][1]

    def _errors(self, role: str, mobile: bool) -> list[str]:
        entry = self.pages.get((role, mobile))
        return entry[2] if entry else []

    @staticmethod
    def _reset(page) -> None:
        try:
            page.keyboard.press('Escape')
        except Exception:
            pass
        page.evaluate("""() => {
            if (typeof toggleDock === 'function') toggleDock(false);
            if (typeof closeDirectoryModal === 'function') closeDirectoryModal();
            if (typeof closeInstructionModal === 'function') closeInstructionModal();
            if (typeof closeCTCPermissionModal === 'function') closeCTCPermissionModal();
            document.getElementById('topbar-profile-switcher-panel')?.classList.add('hidden');
            document.querySelector('header')?.style.removeProperty('visibility');
            document.body.classList.remove('overflow-hidden');
            document.body.style.overflow = '';
        }""")

    def _base_view(self, page, view: str) -> None:
        page.evaluate("() => document.getElementById('pwa-install-banner')?.classList.add('hidden')")
        page.evaluate(
            "(view) => { if (window.switchView) window.switchView(view); }",
            view,
        )
        page.wait_for_timeout(450)
        page.evaluate("() => document.fonts?.ready")

    def capture_shell(
        self,
        browser,
        session: str,
        role: str,
        view: str,
        path: Path,
        size: tuple[int, int],
    ) -> None:
        width, height = size
        mobile = width < 768
        page = self._page(browser, session, role, size)
        self._reset(page)
        page.set_viewport_size({'width': width, 'height': height})
        self._base_view(page, view)

        scroll_ok = None
        if mobile:
            page.evaluate("""() => {
                const main = document.querySelector('#ctc-main');
                if (!main) return null;
                main.scrollTop = main.scrollHeight - main.clientHeight;
                return null;
            }""")
            page.wait_for_timeout(250)
            check = page.evaluate("""() => {
                const main = document.querySelector('#ctc-main');
                const view = document.querySelector('.view-container:not(.hidden)');
                if (!main || !view) return {ok: false, reason: 'conteneur absent'};
                const max = main.scrollHeight - main.clientHeight;
                const rect = view.getBoundingClientRect();
                return {
                    ok: Math.abs(main.scrollTop - max) < 2 && rect.bottom <= window.innerHeight + 4,
                    scrollTop: main.scrollTop,
                    max,
                    bottom: rect.bottom,
                    innerHeight: window.innerHeight,
                };
            }""")
            scroll_ok = bool(check.get('ok'))
            page.evaluate("() => { const main = document.querySelector('#ctc-main'); if (main) main.scrollTop = 0; }")
            page.wait_for_timeout(150)

        metrics = page.evaluate("""() => {
            const main = document.querySelector('#ctc-main');
            const header = document.querySelector('header');
            return {
                scroll: main ? main.scrollHeight : document.documentElement.scrollHeight,
                chrome: header ? header.getBoundingClientRect().height : 0,
            };
        }""")
        target = min(MAX_CONTENT_HEIGHT, max(height, int(metrics['scroll'] + metrics['chrome'] + 32)))
        page.set_viewport_size({'width': width, 'height': target})
        page.wait_for_timeout(650)
        page.evaluate("() => { const main = document.querySelector('#ctc-main'); if (main) main.scrollTop = 0; }")
        page.wait_for_timeout(200)
        path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path), full_page=True, timeout=180000)
        page.set_viewport_size({'width': width, 'height': height})
        self.add(path, width=width, height=target, role=role, view=view,
                 kind='shell', scroll_ok=scroll_ok, errors=self._errors(role, mobile))
        print(f'  {path.relative_to(self.out)}  {width}x{target}  scroll={scroll_ok}', flush=True)

    def capture_page(self, browser, session: str, role: str, url: str, path: Path,
                     size: tuple[int, int], kind: str) -> None:
        width, height = size
        mobile = width < 768
        page = self._page(browser, session, role, size)
        self._reset(page)
        page.set_viewport_size({'width': width, 'height': height})
        page.goto(url, wait_until='domcontentloaded', timeout=90000)
        page.wait_for_timeout(1200)
        page.evaluate("() => document.fonts?.ready")
        page.evaluate("() => document.getElementById('pwa-install-banner')?.classList.add('hidden')")
        scroll = page.evaluate("() => document.documentElement.scrollHeight")
        target = min(MAX_CONTENT_HEIGHT, max(height, int(scroll) + 24))
        page.set_viewport_size({'width': width, 'height': target})
        page.wait_for_timeout(600)
        path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path), full_page=True, timeout=180000)
        page.set_viewport_size({'width': width, 'height': height})
        self.add(path, width=width, height=target, role=role, view=url, kind=kind,
                 errors=self._errors(role, mobile))
        print(f'  {path.relative_to(self.out)}  {width}x{target}', flush=True)

    def capture_viewport(self, browser, session: str, role: str, action, path: Path,
                         size: tuple[int, int], kind: str, view: str = 'dashboard',
                         hide_topbar: bool = False, fit_content: bool = False) -> None:
        width, height = size
        mobile = width < 768
        shot_height = height
        page = self._page(browser, session, role, size)
        self._reset(page)
        page.set_viewport_size({'width': width, 'height': height})
        self._base_view(page, view)
        if hide_topbar:
            page.evaluate("() => { const h = document.querySelector('header'); if (h) h.style.visibility = 'hidden'; }")
        action(page)
        page.wait_for_timeout(500)
        if fit_content:
            needed = page.evaluate("() => document.querySelector('.institutional-drawer__panel')?.scrollHeight || 0")
            if needed > shot_height:
                shot_height = min(MAX_CONTENT_HEIGHT, int(needed) + 12)
                page.set_viewport_size({'width': width, 'height': shot_height})
                page.wait_for_timeout(350)
        path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path), timeout=180000)
        self._reset(page)
        page.set_viewport_size({'width': width, 'height': height})
        self.add(path, width=width, height=shot_height, role=role, view=kind, kind=kind,
                 errors=self._errors(role, mobile))
        print(f'  {path.relative_to(self.out)}  {width}x{shot_height}', flush=True)

    def close_role(self, role: str) -> None:
        for key in [key for key in self.pages if key[0] == role]:
            context, _page, _errors = self.pages.pop(key)
            context.close()

    def close(self) -> None:
        for context, _page, _errors in self.pages.values():
            context.close()
        self.pages.clear()

    def write_index(self, roles: dict) -> None:
        lines = [
            '# Captures des interfaces CTC',
            '',
            f'Généré le {datetime.now():%d/%m/%Y %H:%M}.',
            '',
            'Captures Chromium : PC 1440 px de large, mobile 390 px de large. '
            'Les images de modules sont prises sur toute la hauteur du contenu, '
            'pas seulement sur la hauteur visible.',
            '',
            'Les identités des comptes CTC ont été anonymisées dans une copie de la '
            'base ; les données métier existantes sont conservées.',
            '',
            '## Tableau de bord par rôle',
            '',
            '| # | Sous-rôle | Pôle | PC | Mobile |',
            '|---|---|---|---|---|',
        ]
        for index, role in enumerate(ROLE_ORDER, start=1):
            info = roles[role]
            folder = f'par_role/{index:02d}_{role}'
            lines.append(
                f'| {index} | `{role}` | {info["pole"]} | '
                f'[PC]({folder}/{role}_dashboard_pc.png) | '
                f'[Mobile]({folder}/{role}_dashboard_mobile.png) |'
            )
        lines += [
            '',
            '## Interfaces',
            '',
            '| Interface | Variante | PC | Mobile |',
            '|---|---|---|---|',
        ]
        for view, role, variant in INTERFACE_CAPTURES:
            name = f'{view}_{variant}' if variant else view
            lines.append(
                f'| `{view}` | {variant or "—"} | [PC](interfaces/{name}_pc.png) | '
                f'[Mobile](interfaces/{name}_mobile.png) |'
            )
        lines += [
            '',
            '## Navigation et modales',
            '',
            '| Élément | PC | Mobile |',
            '|---|---|---|',
        ]
        for name in ('annuaire', 'instruction', 'permission'):
            lines.append(f'| {name} | [PC](modales/{name}_pc.png) | [Mobile](modales/{name}_mobile.png) |')
        lines.append('| Profil (panneau) | [PC](modales/profil_pc.png) | — |')
        for variant, _role in MENU_VARIANTS:
            lines.append(f'| Menu mobile — {variant} | — | [Mobile](navigation/menu_mobile_{variant}.png) |')
        lines += [
            '',
            '## Pages autonomes',
            '',
            '| Page | PC | Mobile |',
            '|---|---|---|',
        ]
        for name in ('norme_read', 'ctm_detail', 'copil_rapport'):
            lines.append(f'| {name} | [PC](pages/{name}_pc.png) | [Mobile](pages/{name}_mobile.png) |')
        lines += [
            '',
            '## Contrôle du défilement mobile',
            '',
            'Chaque capture mobile vérifie que le conteneur principal atteint sa '
            'position maximale et que le bas de la vue reste dans la fenêtre. '
            'Le détail figure dans `manifest.json`.',
            '',
        ]
        (self.out / 'INDEX.md').write_text('\n'.join(lines), encoding='utf-8')
        manifest_path = self.out / 'manifest.json'
        merged: dict[str, dict] = {}
        if manifest_path.exists():
            try:
                for record in json.loads(manifest_path.read_text(encoding='utf-8')):
                    merged[record['path']] = record
            except (json.JSONDecodeError, KeyError, TypeError):
                merged = {}
        for record in self.records:
            merged[record['path']] = record
        manifest_path.write_text(
            json.dumps(sorted(merged.values(), key=lambda row: row['path']),
                       ensure_ascii=False, indent=2),
            encoding='utf-8',
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='/tmp/ctc_capture.sqlite3')
    parser.add_argument('--base-url', default='http://127.0.0.1:1112')
    parser.add_argument('--out', default=str(BASE_DIR / 'captures_ctc'))
    parser.add_argument('--roles', default='/tmp/ctc_roles.json')
    parser.add_argument('--only', default='', help='Filtrer sur un sous-rôle ou une vue')
    args = parser.parse_args()

    os.environ['SQLITE_NAME'] = args.db
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()

    from django.conf import settings
    from django.test import Client
    from apps.experts.models import Expert
    from apps.governance.models import CTCProcessus, CTM
    from apps.norms.models import Norme
    roles = json.loads(Path(args.roles).read_text(encoding='utf-8'))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    capture = Capture(args.base_url, out)

    sessions: dict[str, str] = {}
    for role, info in roles.items():
        expert = Expert.objects.select_related('user').get(user__email=info['email'])
        client = Client()
        client.force_login(expert.user, backend='django.contrib.auth.backends.ModelBackend')
        sessions[role] = client.cookies[settings.SESSION_COOKIE_NAME].value

    processus = CTCProcessus.objects.select_related('norme').first()
    norme_id = processus.norme_id if processus else Norme.objects.values_list('id', flat=True).first()
    ctm = CTM.objects.order_by('number').first()
    try:
        from apps.governance.models import CopilRapport
        has_copil = CopilRapport.objects.exists()
    except Exception:
        has_copil = False

    selected = args.only.strip()
    coord = sessions['coordonnateur_principal']
    views = {view for view, _role, _variant in INTERFACE_CAPTURES}
    failed: list[tuple[str, str]] = []

    def safe(label: str, func) -> None:
        try:
            func()
        except Exception as exc:  # noqa: BLE001 - on continue les captures suivantes
            print(f'  ERREUR {label} : {exc}', flush=True)
            failed.append((label, str(exc)))

    with __import__('playwright.sync_api', fromlist=['sync_playwright']).sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)

        role_views: dict[str, list[tuple[str, str]]] = {}
        for view, view_role, variant in INTERFACE_CAPTURES:
            name = f'{view}_{variant}' if variant else view
            role_views.setdefault(view_role, []).append((view, name))

        for index, role in enumerate(ROLE_ORDER, start=1):
            with_dashboard = not selected or selected in (role, 'dashboard')
            views_for_role = [
                (view, name) for view, name in role_views.get(role, [])
                if not selected or selected == view
            ]
            if not with_dashboard and not views_for_role:
                continue
            folder = out / 'par_role' / f'{index:02d}_{role}'
            print(f'[{index}/{len(ROLE_ORDER)}] {role}', flush=True)
            if with_dashboard:
                safe(f'{role}/dashboard/pc', lambda: capture.capture_shell(
                    browser, sessions[role], role, 'dashboard',
                    folder / f'{role}_dashboard_pc.png', DESKTOP,
                ))
                safe(f'{role}/dashboard/mobile', lambda: capture.capture_shell(
                    browser, sessions[role], role, 'dashboard',
                    folder / f'{role}_dashboard_mobile.png', MOBILE,
                ))
            for view, name in views_for_role:
                safe(f'{name}/pc', lambda: capture.capture_shell(
                    browser, sessions[role], role, view,
                    out / 'interfaces' / f'{name}_pc.png', DESKTOP,
                ))
                safe(f'{name}/mobile', lambda: capture.capture_shell(
                    browser, sessions[role], role, view,
                    out / 'interfaces' / f'{name}_mobile.png', MOBILE,
                ))
            capture.close_role(role)

        if selected in ('', 'modales'):
            print('Modales', flush=True)
            for size, suffix in ((DESKTOP, 'pc'), (MOBILE, 'mobile')):
                safe(f'annuaire/{suffix}', lambda: capture.capture_viewport(
                    browser, coord, 'coordonnateur_principal',
                    lambda page: page.evaluate("() => window.openDirectoryModal?.()"),
                    out / 'modales' / f'annuaire_{suffix}.png', size, 'annuaire',
                    hide_topbar=True,
                ))
                safe(f'instruction/{suffix}', lambda: capture.capture_viewport(
                    browser, coord, 'coordonnateur_principal',
                    lambda page: (
                        page.evaluate("() => window.openInstructionModal?.(null)"),
                        page.wait_for_timeout(400),
                        page.evaluate("() => {"
                            "const panel = document.querySelector('.institutional-drawer__panel');"
                            "if (panel) panel.scrollTop = 0;"
                        "}"),
                    ),
                    out / 'modales' / f'instruction_{suffix}.png', size, 'instruction',
                    view='instructions', hide_topbar=True, fit_content=True,
                ))
                safe(f'permission/{suffix}', lambda: capture.capture_viewport(
                    browser, coord, 'coordonnateur_principal',
                    lambda page: page.evaluate(
                        "() => window.openCTCPermissionModal?.('Accès temporaire aux dossiers')"
                    ),
                    out / 'modales' / f'permission_{suffix}.png', size, 'permission',
                    hide_topbar=True,
                ))
            safe('profil/pc', lambda: capture.capture_viewport(
                browser, coord, 'coordonnateur_principal',
                lambda page: page.evaluate(
                    "() => document.getElementById('topbar-profile-switcher-panel')?.classList.remove('hidden')"
                ),
                out / 'modales' / 'profil_pc.png', DESKTOP, 'profil',
            ))

        if selected in ('', 'menu'):
            print('Menu mobile', flush=True)
            for variant, role in MENU_VARIANTS:
                safe(f'menu/{variant}', lambda: capture.capture_viewport(
                    browser, sessions[role], role,
                    lambda page: page.click('#mobile-menu-btn'),
                    out / 'navigation' / f'menu_mobile_{variant}.png', MOBILE, f'menu-{variant}',
                ))

        if selected in ('', 'pages'):
            print('Pages autonomes', flush=True)
            if norme_id:
                url = f'{args.base_url}/ctc/norme/{norme_id}/lecture/'
                for size, suffix in ((DESKTOP, 'pc'), (MOBILE, 'mobile')):
                    safe(f'norme_read/{suffix}', lambda: capture.capture_page(
                        browser, coord, 'coordonnateur_principal', url,
                        out / 'pages' / f'norme_read_{suffix}.png', size, 'norme_read',
                    ))
            if ctm:
                url = f'{args.base_url}/ctc/ctm/{ctm.number}/'
                for size, suffix in ((DESKTOP, 'pc'), (MOBILE, 'mobile')):
                    safe(f'ctm_detail/{suffix}', lambda: capture.capture_page(
                        browser, coord, 'coordonnateur_principal', url,
                        out / 'pages' / f'ctm_detail_{suffix}.png', size, 'ctm_detail',
                    ))
            if has_copil:
                url = f'{args.base_url}/ctc/copil/rapport/'
                for size, suffix in ((DESKTOP, 'pc'), (MOBILE, 'mobile')):
                    safe(f'copil_rapport/{suffix}', lambda: capture.capture_page(
                        browser, coord, 'coordonnateur_principal', url,
                        out / 'pages' / f'copil_rapport_{suffix}.png', size, 'copil_rapport',
                    ))

        capture.close()
        browser.close()

    capture.write_index(roles)
    mobile_checks = [r for r in capture.records if r['kind'] == 'shell' and r['width'] < 768]
    failures = [r for r in mobile_checks if r['scroll_ok'] is False]
    print(f'\nCaptures : {len(capture.records)}')
    print(f'Contrôles mobiles en échec : {len(failures)}')
    for row in failures:
        print(f'  {row["role"]} / {row["view"]} / {row["path"]}')
    print(f'Index : {out / "INDEX.md"}')


if __name__ == '__main__':
    main()

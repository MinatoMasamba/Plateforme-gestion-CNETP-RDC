"""Capture desktop/mobile screenshots of the App Store pages."""
from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

DESKTOP = (1440, 900)
MOBILE = (390, 844)


def capture(base_url: str, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    pages = [
        ('catalog', '/app-store/'),
        ('detail', '/app-store/apps/cne-itp-mobile/'),
        ('announcements', '/app-store/annonces/'),
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for label, path in pages:
            for device, size in (('desktop', DESKTOP), ('mobile', MOBILE)):
                context = browser.new_context(
                    viewport={'width': size[0], 'height': size[1]},
                    device_scale_factor=1,
                )
                page = context.new_page()
                page.goto(base_url.rstrip('/') + path, wait_until='networkidle', timeout=60000)
                target = out / f'appstore_{label}_{device}.png'
                page.screenshot(path=str(target), full_page=True)
                context.close()
                print(target)
        browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:1113')
    parser.add_argument('--out', default='reports/appstore')
    args = parser.parse_args()
    capture(args.base_url, Path(args.out))

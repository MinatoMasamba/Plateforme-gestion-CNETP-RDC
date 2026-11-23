"""Vérifier un incident synthétique avec la session admin privée existante."""
import json
import time
from pathlib import Path

from remote_expert_distribution import BASE, get_page, session


def main():
    client = session()
    _, page = get_page(client, '/admin/')
    event_id = f'release_probe_{time.time_ns()}'
    response = client.post(
        BASE + '/api/v1/mobile/diagnostics/',
        json={
            'event_id': event_id, 'category': 'flutter',
            'app_version': '1.0.0-beta.1+4', 'platform': 'windows',
            'message': 'Test synthétique de réception des diagnostics avant distribution.',
        },
        headers={
            'X-CSRFToken': page.fields['csrfmiddlewaretoken']['value'],
            'Referer': BASE + '/admin/',
        }, timeout=30,
    )
    result = {'http_status': response.status_code, 'synthetic_event_id': event_id}
    if response.status_code in (200, 201):
        incident_id = response.json()['id']
        admin_response, _ = get_page(client, f'/admin/mobileapp/clientdiagnostic/{incident_id}/change/')
        result['visible_in_admin'] = admin_response.status_code == 200 and event_id in admin_response.text
        result['incident_id'] = incident_id
    else:
        result['response'] = response.text[:500]
        listing, _ = get_page(client, '/admin/mobileapp/clientdiagnostic/?q=' + event_id)
        result['saved_in_database'] = event_id in listing.text
    destination = Path(__file__).resolve().parents[1] / 'reports/expert_beta'
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'remote_diagnostic_probe.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))
    if response.status_code not in (200, 201) or not result.get('visible_in_admin'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()

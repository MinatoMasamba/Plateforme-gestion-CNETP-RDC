"""Récupérer le dernier APK distant sans modifier sa publication."""
import hashlib
import json
import re
import zipfile
from pathlib import Path

from remote_expert_distribution import BASE, form_defaults, get_page, session


def main():
    root = Path(__file__).resolve().parents[1]
    client = session()
    _, listing = get_page(client, '/admin/appstore/appreleasefile/')
    candidates = []
    for link in set(listing.links):
        match = re.fullmatch(r'/admin/appstore/appreleasefile/(\d+)/change/', link)
        if match:
            _, page = get_page(client, link)
            values = form_defaults(page)
            if values.get('platform') == 'android':
                candidates.append(int(match.group(1)))
    if not candidates:
        raise RuntimeError('Aucun APK distant identifiable.')
    file_id = max(candidates)
    destination = root / '.private_build' / f'distributed-{file_id}.apk'
    digest = hashlib.sha256()
    with client.get(BASE + f'/app-store/telecharger/{file_id}/', stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with destination.open('wb') as output:
            for chunk in response.iter_content(1024 * 1024):
                digest.update(chunk)
                output.write(chunk)
    with zipfile.ZipFile(destination) as package:
        libraries = [name for name in package.namelist() if name.startswith('lib/') and name.endswith('.so')]
        if package.testzip() is not None:
            raise RuntimeError('Archive APK corrompue.')
    result = {'file_id': file_id, 'file': str(destination), 'bytes': destination.stat().st_size,
              'sha256': digest.hexdigest(), 'native_libraries': libraries, 'zip_integrity': True}
    (root / 'reports/expert_beta/distributed_apk_inspection.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()

"""Envoyer un installateur vérifié comme brouillon sans élargir la bêta."""
import hashlib
import json
import re
import sys
from pathlib import Path

from remote_expert_distribution import BASE, ensure_app, form_defaults, get_page, post_form, session


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    package = Path(manifest['file']).resolve()
    if not package.is_relative_to(root / 'external_redaction/releases'):
        raise RuntimeError('Dossier de distribution incorrect.')
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    if digest != manifest['sha256']:
        raise RuntimeError('Empreinte locale incorrecte.')
    client = session()
    app_id = ensure_app(client)
    _, listing = get_page(client, f'/app-store/administration/applications/{app_id}/')
    version_id = None
    pattern = rf'/app-store/administration/applications/{app_id}/versions/(\d+)/'
    for link in set(listing.links):
        match = re.fullmatch(pattern, link)
        if match:
            _, page = get_page(client, link)
            if page.fields.get('version_number', {}).get('value') == manifest['version']:
                if page.fields['status'].get('options') and form_defaults(page)['status'] != 'draft':
                    raise RuntimeError('Version existante non modifiable.')
                version_id = int(match.group(1))
                break
    if version_id is None:
        location = post_form(client, f'/app-store/administration/applications/{app_id}/versions/nouvelle/', {
            'version_number': manifest['version'], 'version_mode': 'manual',
            'channel': 'beta', 'status': 'draft', 'min_os_version': 'Windows 10 x64',
            'compatibility_notes': 'Installateur Windows x64 avec bibliothèques et données. API distante HTTPS.',
            'release_notes': 'Choix entre Expert et Coordination du Secrétariat technique ; conservation locale des diagnostics en attente de transmission.',
            'known_issues': 'Recette sur poste utilisateur requise. Le test distant du journal retourne HTTP 500. Android attend la clé de signature existante.',
        })
        match = re.fullmatch(pattern, location)
        if not match:
            raise RuntimeError('URL de version inattendue.')
        version_id = int(match.group(1))
    version_path = f'/app-store/administration/applications/{app_id}/versions/{version_id}/'
    _, listing = get_page(client, '/admin/appstore/appreleasefile/')
    file_id = None
    for link in set(listing.links):
        match = re.fullmatch(r'/admin/appstore/appreleasefile/(\d+)/change/', link)
        if match:
            response, page = get_page(client, link)
            values = form_defaults(page)
            if str(values.get('version')) == str(version_id) and values.get('platform') == 'windows':
                if digest not in response.text:
                    raise RuntimeError('Un autre fichier Windows existe déjà pour cette version.')
                file_id = int(match.group(1))
    if file_id is None:
        _, upload_page = get_page(client, version_path)
        architectures = {option['value'] for option in upload_page.fields['architecture']['options']}
        if 'x86_64' not in architectures:
            raise RuntimeError('Architecture Windows x86_64 absente du formulaire distant.')
        with package.open('rb') as stream:
            post_form(client, version_path + 'fichiers/', {
                'platform': 'windows', 'architecture': 'x86_64', 'approve_now': 'on',
                'install_notes': 'Exécuter cet installateur puis ouvrir CNE-ITP Expert depuis le menu Démarrer. Installation pour le compte Windows courant.',
            }, files={'package': (package.name, stream, 'application/vnd.microsoft.portable-executable')}, form_path=version_path)
        _, listing = get_page(client, '/admin/appstore/appreleasefile/')
        for link in set(listing.links):
            match = re.fullmatch(r'/admin/appstore/appreleasefile/(\d+)/change/', link)
            if match:
                response, page = get_page(client, link)
                values = form_defaults(page)
                if str(values.get('version')) == str(version_id) and values.get('platform') == 'windows' and digest in response.text:
                    file_id = int(match.group(1))
                    break
    if file_id is None:
        raise RuntimeError('Téléversement non confirmé.')
    with client.get(BASE + f'/app-store/telecharger/{file_id}/', stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        received = hashlib.sha256()
        count = 0
        for chunk in response.iter_content(1024 * 1024):
            received.update(chunk)
            count += len(chunk)
    if received.hexdigest() != digest or count != package.stat().st_size:
        raise RuntimeError('Le téléchargement distant ne correspond pas au fichier local.')
    result = {**manifest, 'version_id': version_id, 'file_id': file_id,
              'status': 'draft', 'remote_download_verified': True,
              'admin_url': BASE + f'/admin/appstore/appreleasefile/{file_id}/change/',
              'download_url': BASE + f'/app-store/telecharger/{file_id}/'}
    destination = root / 'reports/expert_beta'
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'windows_distribution.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()

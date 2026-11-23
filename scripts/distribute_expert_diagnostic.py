"""Déposer l'APK de recette en brouillon, sans remplacer la bêta signée."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

from remote_expert_distribution import (
    BASE, ensure_app, ensure_version, find_release, form_defaults,
    get_page, post_form, session,
)


def main():
    root = Path(__file__).resolve().parents[1]
    package = Path(sys.argv[1]).resolve()
    if not package.is_relative_to(root / 'external_redaction/releases'):
        raise RuntimeError('Dossier de distribution incorrect.')
    with zipfile.ZipFile(package) as archive:
        if 'AndroidManifest.xml' not in archive.namelist():
            raise RuntimeError('APK invalide.')
        if any(name.endswith('/libdartjni.so') for name in archive.namelist()):
            raise RuntimeError('La passerelle JNI en cause est encore présente.')
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    client = session()
    app_id = ensure_app(client)
    version_id = ensure_version(
        client, app_id, sys.argv[2],
        'Recette Android ARM64 : correction du crash JNI, page de norme éditable, proportions mobiles et zone système corrigées.',
        'Application séparée CNE-ITP Diagnostic, package cd.cneitp.expert.diagnostic. Android ARM64 uniquement.',
    )
    path = f'/app-store/administration/applications/{app_id}/versions/{version_id}/'
    _, page = get_page(client, path)
    if form_defaults(page).get('status') != 'draft':
        raise RuntimeError('Une version publiée ne peut pas être remplacée.')
    post_form(client, path, {
        'known_issues': 'APK de diagnostic signé avec une clé de développement. Installation séparée ; ne met pas à jour la bêta officielle. La clé bêta existante reste nécessaire pour la livraison officielle. Correctif du journal serveur à déployer.',
        'status': 'draft',
    })
    file_id = find_release(client, version_id, digest)
    if file_id is None:
        with package.open('rb') as stream:
            post_form(client, path + 'fichiers/', {
                'platform': 'android', 'architecture': 'arm64', 'approve_now': 'on',
                'install_notes': 'Recette uniquement : ouvrir CNE-ITP Diagnostic. Ce fichier ne remplace pas CNE-ITP Expert. Android ARM64.',
            }, files={'package': (package.name, stream, 'application/vnd.android.package-archive')}, form_path=path)
        file_id = find_release(client, version_id, digest)
    if file_id is None:
        raise RuntimeError('Téléversement non confirmé.')
    downloaded = hashlib.sha256()
    size = 0
    with client.get(BASE + f'/app-store/telecharger/{file_id}/', stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        for chunk in response.iter_content(1024 * 1024):
            downloaded.update(chunk)
            size += len(chunk)
    if downloaded.hexdigest() != digest or size != package.stat().st_size:
        raise RuntimeError('Empreinte du téléchargement incorrecte.')
    result = {'version_id': version_id, 'file_id': file_id, 'status': 'draft',
              'package': 'cd.cneitp.expert.diagnostic', 'signing': 'development',
              'architecture': 'arm64', 'bytes': size, 'sha256': digest,
              'remote_download_verified': True,
              'admin_url': BASE + f'/admin/appstore/appreleasefile/{file_id}/change/',
              'download_url': BASE + f'/app-store/telecharger/{file_id}/'}
    (root / 'reports/expert_beta/android_diagnostic_distribution.json').write_text(
        json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()

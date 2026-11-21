"""Inspecter les formulaires de distribution avec une session admin temporaire.

Aucun mot de passe n'est conservé ici. La session provient de la connexion
explicitement autorisée par l'utilisateur et reste dans .private_build.
"""
import json
import re
import hashlib
import io
import os
import secrets
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import parse_qs, urljoin, urlsplit

import requests

BASE = 'https://workalldomain.pythonanywhere.com'


def session():
    state = json.loads((Path(__file__).resolve().parents[1] / '.private_build/remote_admin_session.json').read_text())
    client = requests.Session()
    for cookie in state['cookies']:
        client.cookies.set(**cookie)
    return client


def login():
    username = os.environ['CNE_REMOTE_ADMIN_USER']
    password = os.environ['CNE_REMOTE_ADMIN_PASSWORD']
    client = requests.Session()
    response = client.get(BASE + '/admin/login/', timeout=30)
    response.raise_for_status()
    page = FormPage()
    page.feed(response.text)
    csrf = page.fields['csrfmiddlewaretoken']['value']
    response = client.post(BASE + '/admin/login/', data={
        'username': username, 'password': password, 'csrfmiddlewaretoken': csrf, 'next': '/admin/',
    }, headers={'Referer': BASE + '/admin/login/'}, allow_redirects=False, timeout=30)
    if response.status_code != 302:
        raise RuntimeError('Connexion administrateur non confirmée.')
    response = client.get(BASE + '/admin/', timeout=30)
    if response.status_code != 200 or '/admin/logout/' not in response.text:
        raise RuntimeError('Tableau administrateur inaccessible.')
    root = Path(__file__).resolve().parents[1]
    fd = os.open(root / '.private_build/remote_admin_session.json', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump({'cookies': [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'secure': c.secure} for c in client.cookies]}, stream)
    print(json.dumps({'authenticated': True}))


class FormPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fields = {}
        self.links = []
        self.forms = []
        self.select = None
        self.option = None
        self.textarea = None
        self.title = ''
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'title':
            self.in_title = True
        if tag == 'form':
            self.forms.append({'action': attrs.get('action'), 'method': attrs.get('method')})
        if tag == 'input' and attrs.get('name'):
            self.fields[attrs['name']] = {'type': attrs.get('type', 'text'), 'value': attrs.get('value', ''), 'checked': 'checked' in attrs}
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])
        if tag == 'select':
            self.select = attrs.get('name')
            if self.select:
                self.fields[self.select] = {'type': 'select', 'options': [], 'multiple': 'multiple' in attrs}
        if tag == 'option' and self.select:
            self.option = {'value': attrs.get('value', ''), 'label': '', 'selected': 'selected' in attrs}
            self.fields[self.select]['options'].append(self.option)
        if tag == 'textarea' and attrs.get('name'):
            self.textarea = attrs['name']
            self.fields[self.textarea] = {'type': 'textarea', 'value': ''}

    def handle_data(self, text):
        if self.option is not None:
            self.option['label'] += text
        if self.textarea:
            self.fields[self.textarea]['value'] += text
        if self.in_title:
            self.title += text

    def handle_endtag(self, tag):
        if tag == 'select':
            self.select = None
        if tag == 'option':
            self.option = None
        if tag == 'textarea':
            self.textarea = None
        if tag == 'title':
            self.in_title = False


def get_page(client, path):
    if not path.startswith('/') or path.startswith('//'):
        raise ValueError('Chemin relatif au serveur du projet requis.')
    response = client.get(BASE + path, timeout=60)
    if response.url.split('?')[0].endswith('/login/'):
        raise RuntimeError('Session administrateur expirée.')
    page = FormPage()
    page.feed(response.text)
    page.links = [urljoin(response.url, link).removeprefix(BASE) for link in page.links]
    return response, page


def safe_summary(response, page):
    fields = {}
    for name, field in page.fields.items():
        if '__prefix__' in name:
            continue
        if name in ('csrfmiddlewaretoken', 'password'):
            fields[name] = {'type': field['type'], 'value': '[masqué]'}
        elif name.endswith(('beta_testers', 'created_by', 'updated_by')):
            fields[name] = {'type': field['type'], 'count': len(field.get('options', []))}
        else:
            fields[name] = field
    return {'status': response.status_code, 'path': response.url.removeprefix(BASE),
            'title': page.title, 'forms': page.forms, 'fields': fields,
            'links': [url for url in page.links if 'appstore' in url or 'app-store' in url]}


def form_defaults(page):
    result = {}
    for name, field in page.fields.items():
        kind = field['type']
        if '__prefix__' in name or kind in ('file', 'submit'):
            continue
        if kind == 'checkbox':
            if field['checked']:
                result[name] = field['value'] or 'on'
        elif kind == 'select':
            selected = [option['value'] for option in field['options'] if option['selected']]
            result[name] = selected if field.get('multiple') else (selected[0] if selected else field['options'][0]['value'])
        else:
            result[name] = field.get('value', '')
    return result


class MultipartUpload:
    def __init__(self, data, files):
        self.boundary = 'cne-expert-' + secrets.token_hex(16)
        self.parts = []
        self.length = 0
        self.transferred = 0
        self.last_progress = 0
        for name, value in data.items():
            for item in value if isinstance(value, list) else [value]:
                header = f'--{self.boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
                self._bytes((header + str(item) + '\r\n').encode())
        for name, (filename, stream, mime) in files.items():
            header = f'--{self.boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{filename}"\r\nContent-Type: {mime}\r\n\r\n'
            self._bytes(header.encode())
            self.parts.append(stream)
            self.length += os.fstat(stream.fileno()).st_size - stream.tell()
            self._bytes(b'\r\n')
        self._bytes(f'--{self.boundary}--\r\n'.encode())

    def _bytes(self, value):
        self.parts.append(io.BytesIO(value))
        self.length += len(value)

    def __len__(self):
        return self.length

    def read(self, size=65536):
        if size < 0:
            size = 65536
        output = bytearray()
        while self.parts and len(output) < size:
            chunk = self.parts[0].read(size - len(output))
            if chunk:
                output.extend(chunk)
            else:
                self.parts.pop(0)
        self.transferred += len(output)
        if self.transferred - self.last_progress >= 8 * 1024 * 1024:
            print(json.dumps({'step': 'upload_progress', 'sent_bytes': self.transferred, 'total_bytes': self.length}), flush=True)
            self.last_progress = self.transferred
        return bytes(output)


def post_form(client, path, values, files=None, form_path=None):
    response, page = get_page(client, form_path or path)
    response.raise_for_status()
    data = form_defaults(page)
    data.update(values)
    headers = {'Referer': BASE + path}
    if files:
        body = MultipartUpload(data, files)
        headers['Content-Type'] = f'multipart/form-data; boundary={body.boundary}'
        response = client.post(BASE + path, data=body, headers=headers, timeout=(180, 300), allow_redirects=False)
    else:
        response = client.post(BASE + path, data=data, headers=headers, timeout=(20, 300), allow_redirects=False)
    if response.status_code not in (302, 303):
        errors = re.findall(r'<ul class="errorlist[^>]*>(.*?)</ul>', response.text, flags=re.S)
        clean = [re.sub('<[^>]+>', ' ', value).strip()[:300] for value in errors]
        raise RuntimeError(f'Enregistrement non confirmé : HTTP {response.status_code}, erreurs {clean}')
    return response.headers.get('Location', '')


def ensure_app(client):
    response, listing = get_page(client, '/admin/appstore/softwareapp/')
    response.raise_for_status()
    for link in listing.links:
        link = urlsplit(link).path
        if re.fullmatch(r'/admin/appstore/softwareapp/\d+/change/', link):
            _, app = get_page(client, link)
            if app.fields.get('slug', {}).get('value') == 'cne-itp-expert':
                return int(link.split('/')[-3])
    path = '/app-store/administration/applications/nouvelle/'
    logo = Path(__file__).resolve().parents[1] / 'flutter_app/assets/img/logo-cnetp.png'
    with logo.open('rb') as stream:
        location = post_form(client, path, {
            'name': 'CNE-ITP Expert', 'slug': 'cne-itp-expert',
            'short_description': 'Application Expert CNE-ITP — version bêta Android.',
            'full_description': 'Application destinée aux experts pour la consultation des projets, les réunions et le suivi des contributions.',
            'features': 'Consultation des projets\nRéunions et participation\nNotifications\nProfil expert',
            'publisher': 'CNE-ITP',
        }, files={'icon': ('logo-cnetp.png', stream, 'image/png')})
    match = re.fullmatch(r'/app-store/administration/applications/(\d+)/', location)
    if not match:
        raise RuntimeError(f'Application enregistrée mais URL inattendue : {location}')
    return int(match.group(1))


def ensure_version(client, app_id, release_version='1.0.0-beta.1+2', release_notes=None, compatibility=None):
    response, listing = get_page(client, f'/app-store/administration/applications/{app_id}/')
    response.raise_for_status()
    pattern = rf'/app-store/administration/applications/{app_id}/versions/(\d+)/'
    for link in listing.links:
        match = re.fullmatch(pattern, link)
        if match:
            _, version = get_page(client, link)
            if version.fields.get('version_number', {}).get('value') == release_version:
                return int(match.group(1))
    location = post_form(client, f'/app-store/administration/applications/{app_id}/versions/nouvelle/', {
        'version_number': release_version, 'version_mode': 'manual', 'channel': 'beta',
        'status': 'draft', 'min_os_version': 'Android 7.0 (API 24)',
        'compatibility_notes': compatibility or 'APK universel : ARM 32 bits, ARM 64 bits et x86_64. Windows reporté.',
        'release_notes': release_notes or 'Interface Expert bêta, logo institutionnel de l’en-tête, navigation mobile et enregistrement natif des documents Android.',
        'known_issues': 'Les nouvelles fonctions Réunions et le journal technique nécessitent encore le déploiement des routes serveur correspondantes. Leur absence actuelle a été vérifiée avant publication.',
    })
    match = re.fullmatch(pattern, location)
    if not match:
        raise RuntimeError(f'URL de version inattendue : {location}')
    return int(match.group(1))


def find_release(client, version_id, digest):
    response, listing = get_page(client, '/admin/appstore/appreleasefile/')
    response.raise_for_status()
    for link in listing.links:
        link = urlsplit(link).path
        match = re.fullmatch(r'/admin/appstore/appreleasefile/(\d+)/change/', link)
        if not match:
            continue
        response, release = get_page(client, link)
        values = form_defaults(release)
        if str(values.get('version')) == str(version_id) and values.get('platform') == 'android':
            if digest not in response.text:
                raise RuntimeError('Un APK différent existe déjà pour cette version ; aucun écrasement effectué.')
            if values.get('quarantine_status') != 'approved':
                raise RuntimeError('Le fichier existant n’est pas approuvé.')
            return int(match.group(1))
    return None


def active_expert_users(client):
    url = BASE + '/api/v1/experts/?status=ACTIVE&page_size=100'
    identifiers = set()
    while url:
        if not url.startswith(BASE + '/'):
            raise RuntimeError('Pagination hors du serveur du projet refusée.')
        response = client.get(url, timeout=60)
        response.raise_for_status()
        body = response.json()
        rows = body.get('results', []) if isinstance(body, dict) else body
        for row in rows:
            if row.get('status') != 'ACTIVE':
                continue
            user = row.get('user')
            identifier = user.get('id') if isinstance(user, dict) else (row.get('user_id') or user)
            if identifier is not None:
                identifiers.add(str(int(identifier)))
        url = body.get('next') if isinstance(body, dict) else None
    if not identifiers:
        raise RuntimeError('Aucun compte expert actif identifiable ; accès bêta non modifié.')
    return identifiers


def upload_and_publish(client, manifest_path=None):
    root = Path(__file__).resolve().parents[1]
    manifest_path = Path(manifest_path) if manifest_path else root / 'external_redaction/releases/cne-itp-expert-1.0.0-beta.1+2.json'
    manifest = json.loads(manifest_path.read_text())
    apk = Path(manifest.get('file', str(manifest_path.with_suffix('.apk')))).resolve()
    if not apk.is_relative_to(root / 'external_redaction/releases'):
        raise RuntimeError('Le fichier doit provenir du dossier des versions vérifiées.')
    with apk.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != manifest['sha256']:
        raise RuntimeError('APK local modifié depuis sa vérification de signature.')
    app_id = ensure_app(client)
    version_id = ensure_version(client, app_id, manifest['version'], manifest.get('release_notes'),
                                'APK unique ARM 32 et 64 bits. Android 7.0 minimum. Windows reporté.' if manifest.get('compressed_native_libraries') else None)
    version_path = f'/app-store/administration/applications/{app_id}/versions/{version_id}/'
    file_id = find_release(client, version_id, digest)
    if file_id is None:
        _, page = get_page(client, version_path)
        if page.fields.get('package', {}).get('type') != 'file':
            raise RuntimeError('Formulaire serveur de téléversement non reconnu.')
        print(json.dumps({'step': 'upload_start', 'bytes': apk.stat().st_size}), flush=True)
        with apk.open('rb') as stream:
            post_form(client, version_path + 'fichiers/', {
                'platform': 'android', 'architecture': 'any', 'approve_now': 'on',
                'install_notes': 'APK bêta signé, Android 7.0 minimum. Logo identique à celui de l’en-tête de l’application.',
            }, files={'package': (apk.name, stream, 'application/vnd.android.package-archive')}, form_path=version_path)
        file_id = find_release(client, version_id, digest)
        if file_id is None:
            raise RuntimeError('Téléversement non confirmé dans les fichiers de distribution.')
    print(json.dumps({'step': 'upload_verified', 'file_id': file_id, 'sha256': digest}), flush=True)
    active = active_expert_users(client)
    admin_path = f'/admin/appstore/appversion/{version_id}/change/'
    _, page = get_page(client, admin_path)
    field = page.fields.get('beta_testers')
    if not field or not field.get('multiple'):
        raise RuntimeError('Gestion des testeurs bêta indisponible sur ce serveur.')
    available = {option['value'] for option in field['options']}
    if not active.issubset(available):
        raise RuntimeError('Un compte expert n’est pas présent dans la liste des comptes autorisables.')
    previous = {option['value'] for option in field['options'] if option['selected']}
    audience = active | previous
    if audience != previous:
        post_form(client, admin_path, {'beta_testers': sorted(audience, key=int), '_save': 'Enregistrer'})
    _, verify = get_page(client, admin_path)
    selected = {option['value'] for option in verify.fields['beta_testers']['options'] if option['selected']}
    if not audience.issubset(selected):
        raise RuntimeError('Les destinataires bêta n’ont pas été confirmés.')
    post_form(client, version_path + 'publier/', {'set_recommended': '1'}, form_path=version_path)
    _, published = get_page(client, version_path)
    values = form_defaults(published)
    if values.get('status') != 'published' or values.get('channel') != 'beta':
        raise RuntimeError('Publication bêta non confirmée.')
    download_url = BASE + f'/app-store/telecharger/{file_id}/'
    response = client.get(download_url, stream=True, timeout=(20, 300), allow_redirects=False)
    if response.status_code != 200:
        raise RuntimeError(f'Téléchargement distant impossible : HTTP {response.status_code}.')
    received = hashlib.sha256()
    count = 0
    for chunk in response.iter_content(1024 * 1024):
        received.update(chunk)
        count += len(chunk)
    if received.hexdigest() != digest or count != apk.stat().st_size:
        raise RuntimeError('Le fichier téléchargé ne correspond pas à l’APK signé.')
    report = {'application_id': app_id, 'version_id': version_id, 'file_id': file_id, 'version': manifest['version'],
              'download_url': download_url, 'admin_url': BASE + f'/admin/appstore/appreleasefile/{file_id}/change/',
              'channel': 'beta', 'status': 'published', 'active_expert_accounts': len(active),
              'bytes': count, 'sha256': digest, 'remote_download_verified': True,
              'backend_routes_deployed': False}
    (root / 'reports/expert_beta/remote_release.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


def verify_and_close(client):
    root = Path(__file__).resolve().parents[1]
    report_path = root / 'reports/expert_beta/remote_release.json'
    report = json.loads(report_path.read_text())
    response = requests.get(report['download_url'], timeout=30, allow_redirects=False)
    destination = urlsplit(urljoin(BASE, response.headers.get('Location', '')))
    if (response.status_code != 302 or destination.netloc != urlsplit(BASE).netloc
            or destination.path not in ('/se-connecter/', '/admin/login/')
            or parse_qs(destination.query).get('next') != [urlsplit(report['download_url']).path]):
        raise RuntimeError('La protection du téléchargement anonyme n’a pas été confirmée.')
    report['anonymous_download_requires_login'] = True
    routes = {}
    for path in ('/api/v1/mobile/diagnostics/', '/api/v1/mobile/expert/meetings/capabilities/'):
        routes[path] = client.head(BASE + path, timeout=30, allow_redirects=False).status_code
    report['backend_route_statuses'] = routes
    report['backend_routes_deployed'] = all(code != 404 for code in routes.values())
    _, page = get_page(client, '/admin/')
    csrf = page.fields['csrfmiddlewaretoken']['value']
    response = client.post(BASE + '/admin/logout/', data={'csrfmiddlewaretoken': csrf},
                           headers={'Referer': BASE + '/admin/'}, timeout=30, allow_redirects=False)
    if response.status_code not in (200, 302, 303):
        raise RuntimeError('Fermeture de session distante non confirmée.')
    response = client.get(BASE + '/admin/', timeout=30, allow_redirects=False)
    if response.status_code != 302 or '/admin/login/' not in response.headers.get('Location', ''):
        raise RuntimeError('La session temporaire est encore active.')
    (root / '.private_build/remote_admin_session.json').unlink()
    report['temporary_session_closed'] = True
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if sys.argv[1:] == ['--login']:
        login()
        raise SystemExit(0)
    client = session()
    if sys.argv[1:] == ['--ensure-app']:
        print(json.dumps({'application_id': ensure_app(client)}))
        raise SystemExit(0)
    if sys.argv[1:] == ['--ensure-version']:
        app_id = ensure_app(client)
        print(json.dumps({'application_id': app_id, 'version_id': ensure_version(client, app_id)}))
        raise SystemExit(0)
    if sys.argv[1:] == ['--upload-and-publish']:
        upload_and_publish(client)
        raise SystemExit(0)
    if len(sys.argv) == 3 and sys.argv[1] == '--upload-manifest':
        upload_and_publish(client, sys.argv[2])
        raise SystemExit(0)
    if sys.argv[1:] == ['--verify-and-close']:
        verify_and_close(client)
        raise SystemExit(0)
    for path in sys.argv[1:]:
        response, page = get_page(client, path)
        print(json.dumps(safe_summary(response, page), ensure_ascii=False))

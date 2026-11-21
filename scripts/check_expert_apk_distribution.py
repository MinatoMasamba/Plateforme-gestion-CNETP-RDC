"""Recette du vrai APK dans l'admin et le téléchargement, base /tmp seulement."""
import hashlib
import json
import os
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_test'
os.environ['SQLITE_NAME'] = '/tmp/expert_beta_review.sqlite3'
os.environ['APPSTORE_PACKAGES_ROOT'] = '/tmp/expert_beta_packages'
os.environ['CLIENT_DIAGNOSTICS_DIR'] = '/tmp/expert_beta_diagnostics'
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from apps.appstore.models import AppReleaseFile
from apps.core.models import User

assert str(settings.DATABASES['default']['NAME']) == '/tmp/expert_beta_review.sqlite3'
apk = root / 'external_redaction/releases/cne-itp-expert-1.0.0-beta.1+2.apk'
assert apk.is_file(), 'APK final absent.'
with apk.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
release = AppReleaseFile.objects.filter(version__application__slug='cne-itp-expert',
                                        version__version_number='1.0.0-beta.1+2', platform='android').first()
if release is None:
    call_command('import_expert_builds', release_version='1.0.0-beta.1+2', apk=str(apk), publish=True,
                 tester=['beta_review@example.test'])
    release = AppReleaseFile.objects.get(version__application__slug='cne-itp-expert',
                                         version__version_number='1.0.0-beta.1+2', platform='android')
assert release.sha256 == digest, 'La version publiée de recette ne correspond pas au vrai APK.'
client = Client()
client.force_login(User.objects.get(username='beta_review'))
url = reverse('web:appstore_download', args=[release.pk])
response = client.get(url)
assert response.status_code == 200, response.status_code
received = hashlib.sha256()
for chunk in response.streaming_content:
    received.update(chunk)
assert received.hexdigest() == digest
assert response['Cache-Control'] == 'private, no-store'
admin, _ = User.objects.get_or_create(username='beta_admin_review', defaults={
    'email': 'beta_admin_review@example.test', 'is_staff': True, 'is_superuser': True,
})
client.force_login(admin)
page = client.get(reverse('admin:appstore_appreleasefile_change', args=[release.pk]))
assert page.status_code == 200
assert url in page.content.decode()
assert digest in page.content.decode()
report = {'database': '/tmp/expert_beta_review.sqlite3', 'platform': 'android',
          'file': str(apk), 'bytes': release.size_bytes, 'sha256': digest,
          'download_path': url, 'download_status': 200, 'admin_status': 200,
          'downloaded_bytes_match': True, 'scope': 'Recette locale isolée, aucun envoi au serveur distant.'}
output = root / 'reports/expert_beta/apk_distribution.json'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))

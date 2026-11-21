import hashlib

import pytest
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import modelform_factory

from apps.appstore.admin import ReleaseAdminForm
from apps.appstore.models import AppReleaseFile, AppVersion, SoftwareApp
from apps.appstore.services import bump_patch_version, parse_version_tuple, verify_stored_hash


def test_flutter_version_with_prerelease_and_build_number():
    assert parse_version_tuple('1.0.0-beta.1+2') == ((1, 0, 0), '-beta.1+2')
    assert bump_patch_version('1.0.0-beta.1+2') == '1.0.1'


@pytest.mark.django_db
def test_admin_upload_populates_download_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(AppReleaseFile._meta.get_field('file'), 'storage', FileSystemStorage(location=tmp_path))
    app = SoftwareApp.objects.create(name='Test Expert', slug='test-expert', short_description='Recette')
    version = AppVersion.objects.create(application=app, version_number='test-beta', channel='beta')
    form_class = modelform_factory(AppReleaseFile, form=ReleaseAdminForm, exclude=('size_bytes', 'sha256', 'original_name'))
    content = b'package de test uniquement'
    form = form_class(data={'version': version.pk, 'platform': 'android', 'architecture': 'any', 'quarantine_status': 'pending'},
                      files={'file': SimpleUploadedFile('expert.apk', content)})
    assert form.is_valid(), form.errors
    release = form.save()
    assert release.size_bytes == len(content)
    assert release.sha256 == hashlib.sha256(content).hexdigest()
    assert release.original_name == 'expert.apk'
    assert verify_stored_hash(release) == release.sha256

"""Tests App Store CNE-ITP : versions, téléchargements, permissions."""
import hashlib

import pytest
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings
from django.urls import reverse

from apps.appstore.models import (
    AppAnnouncement,
    AppCategory,
    AppDownloadEvent,
    AppReleaseFile,
    AppVersion,
    SoftwareApp,
)
from apps.appstore.services import attach_package, publish_version
from apps.dashboard.console_permissions import console_group_name, sync_console_group


def _admin(user_factory):
    sync_console_group()
    user = user_factory(
        username='appstore-admin',
        email='appstore-admin@cnetp.cd',
        is_staff=True,
    )
    user.groups.add(Group.objects.get(name=console_group_name()))
    return user


def _user(user_factory, username='appstore-user'):
    return user_factory(username=username, email=f'{username}@cnetp.cd')


def _package(name, content: bytes):
    return SimpleUploadedFile(name, content, content_type='application/octet-stream')


def _published_app_with_two_versions(admin_user):
    category = AppCategory.objects.create(
        name='Applications professionnelles CNE-ITP',
        slug='pro-cne',
        created_by=admin_user,
    )
    app = SoftwareApp.objects.create(
        name='CNE-ITP Mobile',
        slug='cne-itp-mobile',
        short_description='Application mobile officielle',
        full_description='Description complète',
        features='Consultation\nNotifications',
        publisher='CNE-ITP',
        category=category,
        is_published=True,
        is_featured=True,
        created_by=admin_user,
    )
    v120 = AppVersion.objects.create(
        application=app,
        version_number='1.2.0',
        channel=AppVersion.Channel.STABLE,
        release_notes='Version stable actuelle',
        created_by=admin_user,
    )
    v115 = AppVersion.objects.create(
        application=app,
        version_number='1.1.5',
        channel=AppVersion.Channel.STABLE,
        release_notes='Version stable antérieure',
        created_by=admin_user,
    )
    content_120 = b'PACKAGE-CONTENT-1.2.0-ANDROID'
    content_115 = b'PACKAGE-CONTENT-1.1.5-ANDROID'
    f120 = AppReleaseFile(version=v120, platform=AppReleaseFile.Platform.ANDROID)
    f120.save()
    attach_package(f120, _package('cne-1.2.0.apk', content_120), approve=True)
    f115 = AppReleaseFile(version=v115, platform=AppReleaseFile.Platform.ANDROID)
    f115.save()
    attach_package(f115, _package('cne-1.1.5.apk', content_115), approve=True)
    publish_version(v120, set_recommended=True)
    publish_version(v115, set_recommended=False)
    return app, v120, v115, f120, f115, content_120, content_115


@pytest.mark.django_db
def test_admin_two_versions_user_downloads_exact_files(user_factory, tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path / 'media'):
        admin = _admin(user_factory)
        user = _user(user_factory)
        app, v120, v115, f120, f115, c120, c115 = _published_app_with_two_versions(admin)

        client = Client()
        assert client.get(reverse('web:appstore_catalog')).status_code == 200
        detail = client.get(reverse('web:appstore_detail', kwargs={'slug': app.slug}))
        assert detail.status_code == 200
        assert b'1.2.0' in detail.content
        assert b'1.1.5' in detail.content

        # Anonymous cannot download
        anon = client.get(reverse('web:appstore_download', kwargs={'file_id': f120.pk}))
        assert anon.status_code in (302, 403)

        assert AppDownloadEvent.objects.count() == 0

        client.force_login(user)
        older = client.get(reverse('web:appstore_detail', kwargs={'slug': app.slug}) + '?version=1.1.5')
        assert older.status_code == 200
        assert b'1.1.5' in older.content

        r115 = client.get(reverse('web:appstore_download', kwargs={'file_id': f115.pk}))
        assert r115.status_code == 200
        assert b''.join(r115.streaming_content) == c115
        assert r115['X-AppStore-SHA256'] == hashlib.sha256(c115).hexdigest()

        r120 = client.get(reverse('web:appstore_download', kwargs={'file_id': f120.pk}))
        assert r120.status_code == 200
        assert b''.join(r120.streaming_content) == c120
        assert r120['X-AppStore-SHA256'] == hashlib.sha256(c120).hexdigest()

        assert AppDownloadEvent.objects.count() == 2
        assert set(AppDownloadEvent.objects.values_list('version__version_number', flat=True)) == {
            '1.2.0', '1.1.5',
        }


@pytest.mark.django_db
def test_withdrawn_and_missing_file_not_downloadable(user_factory, tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path / 'media'):
        admin = _admin(user_factory)
        user = _user(user_factory)
        app, v120, v115, f120, f115, *_ = _published_app_with_two_versions(admin)
        v115.status = AppVersion.Status.WITHDRAWN
        v115.save(update_fields=['status'])

        client = Client()
        client.force_login(user)
        detail = client.get(reverse('web:appstore_detail', kwargs={'slug': app.slug}) + '?version=1.1.5')
        assert detail.status_code == 200
        assert reverse('web:appstore_download', kwargs={'file_id': f115.pk}).encode() not in detail.content

        response = client.get(reverse('web:appstore_download', kwargs={'file_id': f115.pk}))
        assert response.status_code == 403

        # Missing blob
        if f120.file and f120.file.storage.exists(f120.file.name):
            f120.file.storage.delete(f120.file.name)
        response = client.get(reverse('web:appstore_download', kwargs={'file_id': f120.pk}))
        assert response.status_code == 403


@pytest.mark.django_db
def test_admin_routes_forbidden_for_regular_user(user_factory):
    user = _user(user_factory, 'regular-appstore')
    client = Client()
    client.force_login(user)
    response = client.get(reverse('web:appstore_admin_home'))
    assert response.status_code == 403


@pytest.mark.django_db
def test_beta_requires_authorization(user_factory, tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path / 'media'):
        admin = _admin(user_factory)
        user = _user(user_factory, 'beta-user')
        tester = _user(user_factory, 'beta-tester')
        app, *_rest = _published_app_with_two_versions(admin)
        beta = AppVersion.objects.create(
            application=app,
            version_number='1.3.0-beta',
            channel=AppVersion.Channel.BETA,
            release_notes='Canal test',
            status=AppVersion.Status.PUBLISHED,
            created_by=admin,
        )
        beta.beta_testers.add(tester)
        release = AppReleaseFile(version=beta, platform=AppReleaseFile.Platform.ANDROID)
        release.save()
        attach_package(release, _package('beta.apk', b'BETA-BYTES'), approve=True)

        client = Client()
        client.force_login(user)
        assert client.get(reverse('web:appstore_download', kwargs={'file_id': release.pk})).status_code == 403

        client.force_login(tester)
        ok = client.get(reverse('web:appstore_download', kwargs={'file_id': release.pk}))
        assert ok.status_code == 200
        assert b''.join(ok.streaming_content) == b'BETA-BYTES'


@pytest.mark.django_db
def test_announcement_links_to_specific_version(user_factory, tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path / 'media'):
        admin = _admin(user_factory)
        app, v120, v115, *_ = _published_app_with_two_versions(admin)
        AppAnnouncement.objects.create(
            title='Mise à jour 1.1.5',
            body='Correctifs disponibles',
            kind=AppAnnouncement.Kind.UPDATE,
            application=app,
            version=v115,
            status=AppAnnouncement.Status.PUBLISHED,
            created_by=admin,
        )
        client = Client()
        page = client.get(reverse('web:appstore_announcements'))
        assert page.status_code == 200
        assert b'version=1.1.5' in page.content
        assert app.slug.encode() in page.content


@pytest.mark.django_db
def test_catalog_click_does_not_create_download_event(user_factory, tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path / 'media'):
        admin = _admin(user_factory)
        _published_app_with_two_versions(admin)
        client = Client()
        client.get(reverse('web:appstore_catalog'))
        client.get(reverse('web:appstore_detail', kwargs={'slug': 'cne-itp-mobile'}))
        assert AppDownloadEvent.objects.count() == 0


@pytest.mark.django_db
def test_admin_can_create_app_via_web(user_factory):
    admin = _admin(user_factory)
    client = Client()
    client.force_login(admin)
    AppCategory.objects.create(name='Utilitaires', slug='utilitaires')
    response = client.post(reverse('web:appstore_admin_app_new'), {
        'name': 'Outil ST',
        'slug': 'outil-st',
        'short_description': 'Outil du secrétariat',
        'full_description': 'Description',
        'features': 'Export',
        'publisher': 'CNE-ITP',
        'category': AppCategory.objects.get(slug='utilitaires').pk,
        'is_featured': 'on',
        'is_published': 'on',
    })
    assert response.status_code == 302
    assert SoftwareApp.objects.filter(slug='outil-st', is_published=True).exists()

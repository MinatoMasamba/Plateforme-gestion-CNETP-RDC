"""Seed démo App Store (idempotent) pour captures et vérification manuelle."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.appstore.models import (
    AppAnnouncement,
    AppCategory,
    AppReleaseFile,
    AppVersion,
    SoftwareApp,
)
from apps.appstore.services import attach_package, publish_announcement, publish_version


class Command(BaseCommand):
    help = 'Crée une application démo avec deux versions publiées.'

    def handle(self, *args, **options):
        category, _ = AppCategory.objects.get_or_create(
            slug='pro-cne-itp',
            defaults={
                'name': 'Applications professionnelles CNE-ITP',
                'description': 'Logiciels officiels de la Commission.',
                'sort_order': 1,
            },
        )
        AppCategory.objects.get_or_create(
            slug='experts',
            defaults={'name': 'Applications pour les experts', 'sort_order': 2},
        )
        AppCategory.objects.get_or_create(
            slug='secretariat-technique',
            defaults={'name': 'Outils du Secrétariat technique', 'sort_order': 3},
        )

        app, created = SoftwareApp.objects.get_or_create(
            slug='cne-itp-mobile',
            defaults={
                'name': 'CNE-ITP Mobile',
                'short_description': 'Application mobile officielle pour experts et agents.',
                'full_description': (
                    'CNE-ITP Mobile permet de consulter les dossiers, les notifications '
                    'et les réunions depuis un téléphone Android.'
                ),
                'features': 'Consultation des dossiers\nNotifications push\nRéunions',
                'publisher': 'CNE-ITP',
                'category': category,
                'is_featured': True,
                'is_published': True,
            },
        )
        if not created:
            app.category = category
            app.is_featured = True
            app.is_published = True
            app.withdrawn_at = None
            app.save()

        for number, notes, recommend in (
            ('1.1.5', 'Correctifs de stabilité et performances.', False),
            ('1.2.0', 'Nouvelle interface et synchronisation accélérée.', True),
        ):
            version, _ = AppVersion.objects.get_or_create(
                application=app,
                version_number=number,
                defaults={
                    'channel': AppVersion.Channel.STABLE,
                    'release_notes': notes,
                    'status': AppVersion.Status.DRAFT,
                },
            )
            release, _ = AppReleaseFile.objects.get_or_create(
                version=version,
                platform=AppReleaseFile.Platform.ANDROID,
                architecture=AppReleaseFile.Architecture.ANY,
            )
            if not release.has_downloadable_blob:
                payload = f'CNE-ITP-MOBILE-{number}\n'.encode()
                attach_package(
                    release,
                    SimpleUploadedFile(f'cne-itp-mobile-{number}.apk', payload),
                    approve=True,
                )
            else:
                release.quarantine_status = AppReleaseFile.QuarantineStatus.APPROVED
                release.save(update_fields=['quarantine_status', 'updated_at'])
            publish_version(version, set_recommended=recommend)

        announcement, _ = AppAnnouncement.objects.get_or_create(
            title='Mise à jour CNE-ITP Mobile 1.2.0',
            defaults={
                'body': 'La version 1.2.0 est disponible. Téléchargez-la depuis l’App Store.',
                'kind': AppAnnouncement.Kind.UPDATE,
                'application': app,
                'version': app.versions.get(version_number='1.2.0'),
                'is_pinned': True,
                'status': AppAnnouncement.Status.DRAFT,
            },
        )
        if announcement.status != AppAnnouncement.Status.PUBLISHED:
            announcement.application = app
            announcement.version = app.versions.get(version_number='1.2.0')
            announcement.published_at = timezone.now()
            announcement.save()
            publish_announcement(announcement)

        self.stdout.write(self.style.SUCCESS(
            f'App Store démo prêt : {app.slug} ({app.versions.count()} versions).'
        ))

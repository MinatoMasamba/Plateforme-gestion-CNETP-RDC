from pathlib import Path
import zipfile

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.appstore.models import AppReleaseFile, AppVersion, SoftwareApp
from apps.appstore.services import attach_package, publish_version
from apps.experts.models import Expert


class Command(BaseCommand):
    help = 'Enregistrer les vrais fichiers Expert dans les modèles de l’admin existant.'

    def add_arguments(self, parser):
        parser.add_argument('--release-version', required=True)
        parser.add_argument('--apk')
        parser.add_argument('--windows')
        parser.add_argument('--publish', action='store_true')
        parser.add_argument('--tester', action='append', default=[])
        parser.add_argument('--all-active-experts', action='store_true')

    def handle(self, *args, **options):
        paths = {}
        for platform, key, extension in [('android', 'apk', '.apk'), ('windows', 'windows', '.exe')]:
            if not options[key]:
                continue
            path = Path(options[key]).resolve()
            if not path.is_file() or path.suffix.lower() != extension:
                raise CommandError(f'Fichier {extension} introuvable : {path}')
            if platform == 'android':
                try:
                    with zipfile.ZipFile(path) as package:
                        if 'AndroidManifest.xml' not in package.namelist() or not any(name.endswith('/libflutter.so') for name in package.namelist()):
                            raise CommandError('Ce fichier ne contient pas une application Android Flutter.')
                except zipfile.BadZipFile as exc:
                    raise CommandError('APK invalide.') from exc
            else:
                with path.open('rb') as stream:
                    if stream.read(2) != b'MZ' or path.stat().st_size < 1024:
                        raise CommandError('Exécutable Windows invalide.')
            paths[platform] = path
        if not paths:
            raise CommandError('Fournir --apk et/ou --windows.')
        testers = get_user_model().objects.filter(email__in=options['tester'], is_active=True)
        if testers.count() != len(set(options['tester'])):
            raise CommandError('Un compte de test demandé est absent ou inactif.')
        with transaction.atomic():
            app, _ = SoftwareApp.objects.get_or_create(slug='cne-itp-expert', defaults={
                'name': 'CNE-ITP Expert', 'short_description': 'Application Expert — version bêta.',
                'publisher': 'CNE-ITP',
            })
            version, _ = AppVersion.objects.get_or_create(application=app, version_number=options['release_version'],
                                                       defaults={'channel': AppVersion.Channel.BETA})
            if version.status == AppVersion.Status.PUBLISHED:
                raise CommandError('Version déjà publiée : utiliser un nouveau numéro, sans écraser ses fichiers.')
            for platform, path in paths.items():
                release, _ = AppReleaseFile.objects.get_or_create(version=version, platform=platform,
                                                                architecture=AppReleaseFile.Architecture.ANY)
                with path.open('rb') as source:
                    attach_package(release, File(source, name=path.name), approve=True)
                self.stdout.write(f'{platform} : {release.size_bytes} octets ; SHA-256 {release.sha256}')
                self.stdout.write(f'Lien direct : /app-store/telecharger/{release.pk}/')
            version.beta_testers.add(*testers)
            if options['all_active_experts']:
                ids = Expert.objects.filter(status='ACTIVE', user__is_active=True, user__is_expert=True).values_list('user_id', flat=True)
                version.beta_testers.add(*ids)
            if options['publish']:
                platforms = set(version.files.filter(quarantine_status='approved').exclude(file='').values_list('platform', flat=True))
                if 'android' not in platforms:
                    raise CommandError('Publication Expert refusée : APK Android approuvé requis.')
                publish_version(version, set_recommended=True)
        self.stdout.write('Enregistré dans /admin/appstore/appversion/. Aucun droit institutionnel modifié.')

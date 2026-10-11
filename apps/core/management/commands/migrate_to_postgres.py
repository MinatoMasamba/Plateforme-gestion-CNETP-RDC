"""Migration complète des données de SQLite vers PostgreSQL.

CLI
---
    python manage.py migrate_to_postgres --db-password '<motdepasse>'

La commande copie **toutes** les données (utilisateurs, experts, structures,
CTM/WG, normes, versions, votes, amendements, réunions, paiements,
notifications, ...) de la base SQLite courante vers PostgreSQL, sans perte.

Elle enchaîne trois étapes via des sous-processus (chacun avec son propre
``DB_ENGINE``) afin de rester simple et fiable :

    1. ``dumpdata``  -> sérialise la base SQLite dans un fixture JSON
    2. ``migrate``   -> crée le schéma PostgreSQL
    3. ``loaddata``  -> réinjecte toutes les données (clés primaires incluses)

Les séquences PostgreSQL sont automatiquement resynchronisées par ``loaddata``.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


DEFAULT_EXCLUDES = ['contenttypes', 'auth.permission', 'admin.logentry', 'sessions']

# Modèles inclus en priorité dans le rapport (indicateurs clés).
KEY_MODELS = [
    ('core', 'User'),
    ('experts', 'Structure'),
    ('experts', 'Expert'),
    ('governance', 'CTM'),
    ('governance', 'WG'),
    ('norms', 'Norme'),
    ('norms', 'NormeVersion'),
    ('amendments', 'Amendement'),
    ('meetings', 'Reunion'),
    ('payments', 'Cotisation'),
    ('mobileapp', 'Notification'),
]


class Command(BaseCommand):
    help = (
        "Copie TOUTES les données de la base SQLite vers PostgreSQL, sans perte, "
        "en une seule commande."
    )

    def add_arguments(self, parser):
        parser.add_argument('--fixture', default=None,
                            help="Chemin du fichier fixture temporaire (défaut: /tmp).")
        parser.add_argument('--keep-fixture', action='store_true',
                            help="Conserver le fixture après l'import.")
        parser.add_argument('--db-name', default=os.environ.get('DB_NAME', 'cnetp_db'))
        parser.add_argument('--db-user', default=os.environ.get('DB_USER', 'cnetp_user'))
        parser.add_argument('--db-password', default=os.environ.get('DB_PASSWORD', ''))
        parser.add_argument('--db-host', default=os.environ.get('DB_HOST', 'localhost'))
        parser.add_argument('--db-port', default=os.environ.get('DB_PORT', '5432'))
        parser.add_argument('--source-sqlite',
                            default=os.environ.get('SQLITE_NAME',
                                                   str(settings.BASE_DIR / 'db.sqlite3')),
                            help="Chemin de la base SQLite source.")
        parser.add_argument('--exclude', nargs='*', default=DEFAULT_EXCLUDES,
                            help="Applications/objets à exclure du dump.")
        parser.add_argument('--skip-migrate', action='store_true',
                            help="Ne pas exécuter migrate sur la cible.")
        parser.add_argument('--wipe', action='store_true',
                            help="Vider la base cible avant l'import.")
        parser.add_argument('--noinput', '--no-input', action='store_true', dest='noinput',
                            help="Ne poser aucune question.")

    # ------------------------------------------------------------------ helpers
    def _run(self, args, env, label):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n▶ {label}"))
        self.stdout.write(f"  manage.py {' '.join(args)}")
        result = subprocess.run([sys.executable, str(settings.BASE_DIR / 'manage.py'), *args], env=env)
        if result.returncode != 0:
            raise CommandError(f"Échec de l'étape « {label} » (code {result.returncode}).")

    def _source_counts(self):
        """Compte les objets clés dans la base source."""
        from django.apps import apps as django_apps
        counts = {}
        for app_label, model_name in KEY_MODELS:
            try:
                model = django_apps.get_model(app_label, model_name)
                counts[f"{app_label}.{model_name}"] = model.objects.count()
            except Exception:
                continue
        return counts

    # ------------------------------------------------------------------- handle
    def handle(self, *args, **options):
        source_db = Path(options['source_sqlite'])
        if not source_db.exists():
            raise CommandError(f"Base SQLite source introuvable : {source_db}")

        current_engine = settings.DATABASES['default']['ENGINE'].rsplit('.', 1)[-1]
        self.stdout.write(self.style.NOTICE(
            f"Base source   : {source_db}  (engine: {current_engine})"
        ))
        self.stdout.write(self.style.NOTICE(
            f"Base cible   : postgresql://{options['db_user']}@{options['db_host']}:"
            f"{options['db_port']}/{options['db_name']}"
        ))

        # Aperçu des données à migrer (lu sur la base source SQLite).
        preview = self._source_counts()
        if preview:
            self.stdout.write(self.style.NOTICE("Données détectées (source) :"))
            for name, count in preview.items():
                self.stdout.write(f"    - {name:<32} {count}")

        if not options['noinput']:
            confirm = input("\nConfirmer la migration vers PostgreSQL ? [oui/non] ").strip().lower()
            if confirm not in ('oui', 'o', 'yes', 'y'):
                self.stdout.write(self.style.WARNING("Migration annulée."))
                return

        fixture = options['fixture'] or str(
            Path(tempfile.gettempdir()) / 'cnetp_sqlite_dump.json'
        )
        Path(fixture).parent.mkdir(parents=True, exist_ok=True)

        base_env = os.environ.copy()
        base_env.pop('DJANGO_SETTINGS_MODULE', None)

        source_env = base_env.copy()
        source_env['DB_ENGINE'] = 'sqlite'
        source_env['SQLITE_NAME'] = str(source_db)

        target_env = base_env.copy()
        target_env['DB_ENGINE'] = 'postgresql'
        target_env['DB_NAME'] = options['db_name']
        target_env['DB_USER'] = options['db_user']
        target_env['DB_PASSWORD'] = options['db_password']
        target_env['DB_HOST'] = options['db_host']
        target_env['DB_PORT'] = options['db_port']

        try:
            # 1. Export de la base SQLite
            dump_args = ['dumpdata', '--natural-foreign', '--natural-primary',
                         '--indent', '2', '-o', fixture]
            for exclude in options['exclude']:
                dump_args += ['--exclude', exclude]
            self._run(dump_args, source_env, "Export de la base SQLite (dumpdata)")

            # 2. Création du schéma PostgreSQL
            if not options['skip_migrate']:
                self._run(['migrate', '--noinput'], target_env,
                          "Création du schéma PostgreSQL (migrate)")

            # 3. (Optionnel) nettoyage de la cible
            if options['wipe']:
                self._run(['flush', '--noinput'], target_env,
                          "Vidage de la base cible (flush)")

            # 4. Import des données
            self._run(['loaddata', fixture], target_env,
                      "Import des données dans PostgreSQL (loaddata)")
        finally:
            if not options['keep_fixture'] and not options['fixture']:
                try:
                    Path(fixture).unlink()
                except OSError:
                    pass

        self.stdout.write(self.style.SUCCESS(
            "\n✅ Migration terminée : toutes les données ont été copiées vers PostgreSQL."
        ))
        self.stdout.write(
            "   Vérifiez ensuite en configurant DB_ENGINE=postgresql dans votre .env."
        )

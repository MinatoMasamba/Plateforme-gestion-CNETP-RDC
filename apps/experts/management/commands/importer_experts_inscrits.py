"""
Commande d'import des inscriptions issues du formulaire externe (export JSON,
ex. apps/experts/data/inscrits.json) vers la plateforme CNETP.

Pour chaque inscription du fichier : crée un compte User + une fiche Expert
(statut PENDING) avec la structure d'origine et la sous-commission (CTM)
correspondantes.

Idempotente et sans risque de doublon : tout email déjà utilisé par un User
existant sur la plateforme est ignoré et compté comme "expert déjà existant"
(aucune modification n'est faite sur les comptes déjà présents). Les doublons
internes au fichier (même email plusieurs fois) sont eux aussi dédupliqués :
seule la soumission la plus récente est conservée.

Aucun email n'est envoyé par cette commande : les comptes créés ont un mot de
passe aléatoire inutilisable en l'état. L'invitation/activation se fait
séparément (cf. notifier_experts_inscription).

Usage :
    python manage.py importer_experts_inscrits
    python manage.py importer_experts_inscrits --file chemin/vers/inscrits.json
    python manage.py importer_experts_inscrits --dry-run
"""
import json
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string

from apps.core.models import User
from apps.experts.models import Expert, Structure
from apps.governance.models import CTM


DEFAULT_FILE = Path(settings.BASE_DIR) / 'apps' / 'experts' / 'data' / 'inscrits.json'

# Mapping "Structure Origine" (valeur du formulaire externe) -> nom officiel
# Structure (Tableau 1 du Manuel Organisationnel CNETP 2026), déjà peuplé par
# seed_official_structures.
STRUCTURE_MAPPING = {
    'Secrétariat Général ITP': 'Secrétariat Général aux ITP',
    'Cabinet du Ministre des ITP': 'Cabinet du Ministre des ITP',
    'Secrétariat Général à la Reconstruction': 'Secrétariat Général à la Reconstruction',
    'Office des Routes': 'Office des Routes',
    'Office des Voiries et Drainage - OVD': 'Office des Voiries et Drainage',
    'Agence Congolaise des Grands Travaux - ACGT': 'Agence Congolaise des Grands Travaux',
    "Fonds National d'Entretien Routier - FONER": "Fonds National d'Entretien Routier",
    'Cellule Infrastructure - CI': 'Cellule Infrastructures',
    "Bureau d'Études d'Aménagement Urbain - BEAU": "Bureau d'Études d'Aménagement Urbain",
    'Autre Ministère partenaire': 'Autres Ministères',
    'Institution académique ou recherche': 'Institutions Académiques et de Recherche',
    'Ordre professionnel ou association': 'Ordres Professionnels et Associations Professionnelles',
    'Société civile ou organisme technique': 'Société Civile et Organismes Techniques',
}

# Structures de repli pour les valeurs hors Tableau 1 officiel (créées si absentes)
FALLBACK_STRUCTURES = {
    'Expert indépendant / consultant': ('Expert indépendant / consultant', 'IND', 'PRIVATE'),
    'Autre': ('Autre / Structure non précisée', 'AUTRE', 'PRIVATE'),
    '': ('Autre / Structure non précisée', 'AUTRE', 'PRIVATE'),
}


def parse_inscription_date(value):
    try:
        return timezone.make_aware(datetime.strptime((value or '').strip(), '%d/%m/%Y %H:%M:%S'))
    except ValueError:
        return None


class Command(BaseCommand):
    help = (
        "Importe les inscriptions du formulaire externe (JSON) et crée un compte "
        "User + une fiche Expert (statut PENDING) pour chaque email non déjà "
        "présent sur la plateforme. Les emails déjà utilisés sont ignorés "
        "(considérés comme expert déjà existant)."
    )

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, default=str(DEFAULT_FILE),
                             help="Chemin du fichier JSON à importer.")
        parser.add_argument('--dry-run', action='store_true',
                             help="Simule l'import sans rien écrire en base.")

    def handle(self, *args, **options):
        file_path = Path(options['file'])
        dry_run = options['dry_run']

        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f"Fichier introuvable : {file_path}"))
            return

        with open(file_path, encoding='utf-8') as f:
            records = json.load(f)

        # Un même email peut apparaître plusieurs fois (resoumissions) : on ne
        # garde que la fiche la plus récente selon "Date d'inscription".
        by_email = {}
        for record in records:
            email = (record.get('Email') or '').strip().lower()
            if not email:
                continue
            current = by_email.get(email)
            if current is None:
                by_email[email] = record
                continue
            current_date = parse_inscription_date(current.get("Date d'inscription")) or datetime.min
            new_date = parse_inscription_date(record.get("Date d'inscription")) or datetime.min
            if new_date > current_date:
                by_email[email] = record

        self.stdout.write(
            f"{len(records)} inscription(s) lues, {len(by_email)} email(s) unique(s) à traiter."
            + (" [DRY-RUN]" if dry_run else "") + "\n"
        )

        created, skipped_existing, errors = 0, 0, 0

        for email, record in sorted(by_email.items()):
            try:
                if User.objects.filter(email__iexact=email).exists():
                    skipped_existing += 1
                    self.stdout.write(f"• Ignoré (déjà expert/utilisateur) : {email}")
                    continue

                if dry_run:
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f"[DRY-RUN] Créerait : {email}"))
                    continue

                with transaction.atomic():
                    self._create_expert(email, record)
                created += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Créé : {email}"))

            except Exception as exc:
                errors += 1
                self.stderr.write(self.style.ERROR(f"✗ Échec pour {email} : {exc}"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(
            f"{created} créé(s), {skipped_existing} déjà existant(s) (ignoré(s)), {errors} échec(s)."
        ))
        self.stdout.write("=" * 60)

    def _resolve_structure(self, raw_name):
        raw_name = (raw_name or '').strip()
        official_name = STRUCTURE_MAPPING.get(raw_name, raw_name)

        structure = Structure.objects.filter(name__iexact=official_name).first()
        if structure:
            return structure

        name, acronym, category = FALLBACK_STRUCTURES.get(
            raw_name, (raw_name or 'Structure non précisée', 'AUTRE', 'PRIVATE')
        )
        structure, _ = Structure.objects.get_or_create(
            name=name, defaults={'acronym': acronym, 'category': category}
        )
        return structure

    def _resolve_ctm(self, raw_sc):
        raw_sc = (raw_sc or '').strip().upper()
        if raw_sc.startswith('SC') and raw_sc[2:].isdigit():
            return CTM.objects.filter(number=int(raw_sc[2:])).first()
        return None

    def _unique_username(self, base):
        base = base or 'expert'
        username = base
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base}{suffix}"
        return username

    def _build_bio(self, record):
        full_name_etat_civil = ' '.join(filter(None, [
            (record.get('Nom') or '').strip(),
            (record.get('Postnom') or '').strip(),
            (record.get('Prénom') or '').strip(),
        ]))
        adresse = ', '.join(filter(None, [
            (record.get('Avenue') or '').strip(),
            (record.get('Numéro') or '').strip(),
            (record.get('Quartier') or '').strip(),
            (record.get('Commune') or '').strip(),
            (record.get('Ville') or '').strip(),
            (record.get('Province') or '').strip(),
        ]))
        piece_identite = ' '.join(filter(None, [
            (record.get('Type Pièce') or '').strip(),
            (record.get('Numéro Pièce') or '').strip(),
        ]))
        fields = [
            ('Code Membre', record.get('Code Membre')),
            ('Civilité', record.get('Civilité')),
            ('Nom complet (état civil)', full_name_etat_civil),
            ('Date de naissance', record.get('Date Naissance')),
            ('Lieu de naissance', record.get('Lieu Naissance')),
            ('Nationalité', record.get('Nationalité')),
            ("Pièce d'identité", piece_identite),
            ('Adresse', adresse),
            ('Titre/Fonction', record.get('Titre/Fonction')),
            ('Diplôme', record.get('Diplôme')),
            ('Expérience BTP', record.get('Expérience BTP')),
            ('Disponibilité', record.get('Disponibilité')),
            ('Rôles souhaités', record.get('Rôles')),
            ('Structure Origine (déclarée)', record.get('Structure Origine')),
            ('Structure Autre (précision)', record.get('Structure Autre')),
            ('Acceptation Calendrier', record.get('Acceptation Calendrier')),
            ('Acceptation Publication', record.get('Acceptation Publication')),
            ('Commentaire Admin', record.get('Commentaire Admin')),
        ]
        return '\n'.join(f"{label} : {value}" for label, value in fields if value)

    def _create_expert(self, email, record):
        first_name = (record.get('Prénom') or '').strip()
        last_name = ' '.join(filter(None, [
            (record.get('Nom') or '').strip(),
            (record.get('Postnom') or '').strip(),
        ]))
        username = self._unique_username(email.split('@')[0])

        user = User.objects.create_user(
            username=username,
            email=email,
            password=get_random_string(32),
            first_name=first_name,
            last_name=last_name,
            phone=(record.get('Téléphone') or '').strip(),
            province=(record.get('Province') or '').strip(),
        )
        user.is_expert = True
        user.bio = self._build_bio(record)
        user.save()

        structure = self._resolve_structure(record.get('Structure Origine'))
        ctm = self._resolve_ctm(record.get('Sous-commission'))

        expert = Expert.objects.create(
            user=user,
            structure=structure,
            ctm=ctm,
            status='PENDING',
            specialties=(record.get('Spécialités') or '')[:500],
        )

        inscription_dt = parse_inscription_date(record.get("Date d'inscription"))
        if inscription_dt:
            Expert.objects.filter(pk=expert.pk).update(inscription_date=inscription_dt)

        return expert

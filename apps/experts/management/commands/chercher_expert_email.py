"""
Commande de diagnostic : recherche un ou plusieurs experts par email et
compare leur fiche source (fichier JSON des inscriptions) avec leur état en
base de données.

Sert notamment à comprendre pourquoi certains experts se retrouvent
"Non assigné" (sans CTM) après importer_experts_inscrits : dans la grande
majorité des cas ce n'est pas un bug de la commande d'import, mais une
valeur "Sous-commission" absente dans le JSON source (le formulaire externe
n'a pas capturé cette info), y compris parfois pour des personnes ayant
pourtant coché le rôle "Membre sous-commission".

Usage :
    python manage.py chercher_expert_email un.email@exemple.com
    python manage.py chercher_expert_email email1@x.com email2@y.com
    python manage.py chercher_expert_email --file chemin/inscrits.json email@x.com

    # Vérifier tous les emails du fichier JSON (163 fiches) :
    python manage.py chercher_expert_email --tous

    # Ne vérifier que les experts déjà en base sans CTM assigné :
    python manage.py chercher_expert_email --sans-ctm

    # Version condensée (une ligne par expert, pas le détail complet) :
    python manage.py chercher_expert_email --tous --resume
"""
import json
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import User
from apps.experts.models import Expert
from apps.governance.models import CTM

DEFAULT_FILE = Path(settings.BASE_DIR) / 'apps' / 'experts' / 'data' / 'inscrits.json'


def resolve_ctm(raw_sc):
    raw_sc = (raw_sc or '').strip().upper()
    if raw_sc.startswith('SC') and raw_sc[2:].isdigit():
        return CTM.objects.filter(number=int(raw_sc[2:])).first()
    return None


def parse_inscription_date(value):
    try:
        return timezone.make_aware(datetime.strptime((value or '').strip(), '%d/%m/%Y %H:%M:%S'))
    except ValueError:
        return None


def most_recent(matches):
    """Reproduit la déduplication d'importer_experts_inscrits : en cas de
    resoumissions, seule la fiche la plus récente est réellement importée."""
    return max(matches, key=lambda r: parse_inscription_date(r.get("Date d'inscription")) or datetime.min)


class Command(BaseCommand):
    help = (
        "Recherche un ou plusieurs experts par email dans le fichier JSON "
        "d'inscriptions et compare leur structure (Sous-commission/CTM) avec "
        "l'état en base."
    )

    def add_arguments(self, parser):
        parser.add_argument('emails', nargs='*', help="Adresse(s) email à rechercher.")
        parser.add_argument('--file', type=str, default=str(DEFAULT_FILE),
                             help="Chemin du fichier JSON des inscriptions.")
        parser.add_argument('--tous', action='store_true',
                             help="Vérifie tous les emails présents dans le fichier JSON.")
        parser.add_argument('--sans-ctm', action='store_true',
                             help="Ne vérifie que les experts déjà en base sans CTM assigné.")
        parser.add_argument('--resume', action='store_true',
                             help="Affichage condensé (une ligne par expert) au lieu du détail complet.")

    def handle(self, *args, **options):
        file_path = Path(options['file'])
        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f"Fichier introuvable : {file_path}"))
            return

        with open(file_path, encoding='utf-8') as f:
            records = json.load(f)

        if options['sans_ctm']:
            emails = list(
                Expert.objects.filter(ctm__isnull=True)
                .values_list('user__email', flat=True)
                .order_by('user__email')
            )
        elif options['tous']:
            emails = sorted({
                (r.get('Email') or '').strip().lower()
                for r in records if (r.get('Email') or '').strip()
            })
        elif options['emails']:
            emails = [e.strip().lower() for e in options['emails']]
        else:
            self.stderr.write(self.style.ERROR(
                "Précisez un ou plusieurs emails, ou utilisez --tous / --sans-ctm."
            ))
            return

        resume = options['resume']
        stats = {'ok': 0, 'non_assigne_legitime': 0, 'incoherent': 0, 'echec_format': 0, 'introuvable': 0}

        for email in emails:
            matches = [r for r in records if (r.get('Email') or '').strip().lower() == email]
            if resume:
                self._inspect_resume(email, matches, stats)
            else:
                self._inspect_detail(email, matches, stats)
                self.stdout.write("=" * 70 + "\n")

        self.stdout.write(self.style.MIGRATE_HEADING(f"\n--- Résumé ({len(emails)} email(s) vérifié(s)) ---"))
        self.stdout.write(self.style.SUCCESS(f"  CTM résolu correctement        : {stats['ok']}"))
        self.stdout.write(f"  Non assigné (légitime)         : {stats['non_assigne_legitime']}")
        self.stdout.write(self.style.ERROR(f"  Incohérent (rôle sans SC)      : {stats['incoherent']}"))
        self.stdout.write(self.style.ERROR(f"  Échec de résolution (format)   : {stats['echec_format']}"))
        self.stdout.write(self.style.WARNING(f"  Introuvable dans le JSON       : {stats['introuvable']}"))

    def _classify(self, record, stats):
        """Détermine le statut CTM de la fiche retenue et met à jour stats.
        Retourne (ctm, sous_commission, roles, incoherent)."""
        sous_commission = (record.get('Sous-commission') or '').strip()
        roles = record.get('Rôles') or ''
        ctm = resolve_ctm(sous_commission)
        incoherent = False

        if ctm:
            stats['ok'] += 1
        elif sous_commission:
            stats['echec_format'] += 1
        else:
            if 'sous-commission' in roles.lower():
                incoherent = True
                stats['incoherent'] += 1
            else:
                stats['non_assigne_legitime'] += 1

        return ctm, sous_commission, roles, incoherent

    def _inspect_resume(self, email, matches, stats):
        if not matches:
            stats['introuvable'] += 1
            self.stdout.write(self.style.WARNING(f"  {email:<40} introuvable dans le JSON"))
            return

        record = most_recent(matches)
        ctm, sous_commission, roles, incoherent = self._classify(record, stats)

        if ctm:
            statut = self.style.SUCCESS(f"CTM{ctm.number} - {ctm.name}")
        elif incoherent:
            statut = self.style.ERROR("⚠ INCOHÉRENT — rôle 'Membre sous-commission' sans SC renseignée")
        elif sous_commission:
            statut = self.style.ERROR(f"⚠ ÉCHEC — valeur '{sous_commission}' non reconnue")
        else:
            statut = "Non assigné (légitime, rôle ne nécessite pas de SC)"

        self.stdout.write(f"  {email:<40} {statut}")

    def _inspect_detail(self, email, matches, stats):
        self.stdout.write(self.style.HTTP_INFO(f"\n### {email} ###\n"))

        self.stdout.write(self.style.MIGRATE_HEADING("--- Fiche(s) source (JSON) ---"))
        if not matches:
            self.stdout.write(self.style.WARNING("  Aucune entrée trouvée dans le fichier JSON."))
            stats['introuvable'] += 1
        else:
            retained = most_recent(matches)
            if len(matches) > 1:
                self.stdout.write(self.style.WARNING(
                    f"  {len(matches)} soumissions trouvées pour cet email "
                    "(seule la plus récente est importée, marquée [RETENUE])."
                ))
            for i, record in enumerate(matches, start=1):
                sous_commission = (record.get('Sous-commission') or '').strip()
                roles = record.get('Rôles') or ''
                is_retained = record is retained
                ctm, _, _, incoherent = self._classify(record, stats) if is_retained else (
                    resolve_ctm(sous_commission), sous_commission, roles, False
                )

                date_inscription = record.get("Date d'inscription")
                marque = " [RETENUE]" if is_retained and len(matches) > 1 else ""
                self.stdout.write(f"\n  [{i}] Date d'inscription : {date_inscription}{marque}")
                self.stdout.write(f"      Nom complet          : {record.get('Prénom')} {record.get('Nom')} {record.get('Postnom')}")
                self.stdout.write(f"      Structure Origine    : {record.get('Structure Origine')}")
                self.stdout.write(f"      Rôles                : {roles}")
                self.stdout.write(f"      Sous-commission (brut): {sous_commission!r}")
                if ctm:
                    self.stdout.write(self.style.SUCCESS(f"      CTM résolu           : CTM{ctm.number} - {ctm.name}"))
                elif sous_commission:
                    self.stdout.write(self.style.ERROR(
                        f"      CTM résolu           : ÉCHEC — valeur '{sous_commission}' "
                        "ne correspond à aucun CTM (format inattendu)."
                    ))
                else:
                    self.stdout.write(self.style.WARNING("      CTM résolu           : Non assigné (champ vide dans le JSON)"))
                    if incoherent:
                        self.stdout.write(self.style.ERROR(
                            "      ⚠ Incohérence source : le rôle 'Membre sous-commission' est "
                            "coché mais aucune Sous-commission n'a été renseignée dans le formulaire."
                        ))
                self.stdout.write(f"      Statut inscription   : {record.get('Statut')}")

        self.stdout.write(self.style.MIGRATE_HEADING("\n--- État en base de données ---"))
        user = User.objects.filter(email__iexact=email).select_related('expert_profile').first()
        if not user:
            self.stdout.write(self.style.WARNING("  Aucun compte User avec cet email (pas encore importé)."))
            return

        self.stdout.write(f"  User          : {user.username} (id={user.id}, is_expert={user.is_expert})")
        expert = getattr(user, 'expert_profile', None)

        if not expert:
            self.stdout.write(self.style.WARNING("  Aucune fiche Expert associée à ce User."))
            return

        self.stdout.write(f"  Statut Expert : {expert.status}")
        self.stdout.write(f"  Structure     : {expert.structure}")
        self.stdout.write(
            f"  CTM en base   : "
            + (f"CTM{expert.ctm.number} - {expert.ctm.name}" if expert.ctm else "Non assigné")
        )

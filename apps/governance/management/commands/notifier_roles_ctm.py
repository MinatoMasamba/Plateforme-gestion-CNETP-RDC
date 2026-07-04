"""
Commande de notification : envoie à chaque Expert affecté à un Comité
Technique Miroir (Expert.ctm) un email détaillant les responsabilités
précises de son rôle au sein de ce CTM (Président scientifique, Rapporteur,
Secrétaire, ou Membre).

Distincte de notifier_roles_pilotage (qui s'adresse au Comité de Pilotage
Élargi) : cette commande couvre les 8 CTM / sous-commissions techniques.

Usage :
    python manage.py notifier_roles_ctm --dry-run
    python manage.py notifier_roles_ctm
    python manage.py notifier_roles_ctm --ctm 3
    python manage.py notifier_roles_ctm --statut ACTIVE
    python manage.py notifier_roles_ctm --skip 20 --limit 20
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from apps.experts.models import Expert

logger = logging.getLogger(__name__)

NUMERO_SUPPORT_TECHNIQUE = "0983290982"

SUJET_EMAIL = "🇨🇩 CNETP — Votre rôle au sein de votre Comité Technique Miroir (CTM)"

INSTRUCTIONS_PAR_ROLE = {
    "PRESIDENT": (
        "Président(e) scientifique du CTM",
        """- Présider les sessions du Comité Technique Miroir et en valider l'ordre du jour scientifique ;
- Coordonner les travaux des Groupes de Travail (WG) rattachés à votre CTM ;
- Garantir la cohérence scientifique et technique des projets de normes soumis à validation ;
- Représenter le CTM auprès de la Cellule Technique de Coordination (CTC) et du Comité de Pilotage ;
- Arbitrer les divergences techniques entre membres et Groupes de Travail.""",
    ),
    "RAPPORTEUR": (
        "Rapporteur du CTM",
        """- Consolider et synthétiser les travaux techniques issus des Groupes de Travail (WG) du CTM ;
- Rédiger les rapports d'avancement transmis à la Cellule Technique de Coordination (CTC) ;
- Présenter l'état d'avancement des projets de normes lors des sessions du CTM et du Comité de Pilotage ;
- Assurer le suivi des recommandations et de leur mise en œuvre.""",
    ),
    "SECRETARY": (
        "Secrétaire du CTM",
        """- Rédiger et diffuser les procès-verbaux de chaque session du CTM ;
- Tenir à jour le registre des décisions et des projets de normes examinés ;
- Centraliser et archiver la documentation technique du CTM ;
- Préparer et transmettre les convocations et l'ordre du jour aux membres du CTM.""",
    ),
    "MEMBRE": (
        "Membre du CTM",
        """- Participer activement aux sessions du CTM et aux travaux des Groupes de Travail (WG) qui vous sont confiés ;
- Contribuer, selon votre domaine de spécialité, à l'élaboration et à la révision des projets de normes ;
- Examiner et commenter les documents techniques soumis au CTM ;
- Relayer auprès de votre structure d'origine les orientations et décisions adoptées par le CTM.""",
    ),
}

MESSAGE_TEMPLATE = """🇨🇩 MINISTERE DES INFRASTRUCTURES ET TRAVAUX PUBLICS 🇨🇩
Commission Nationale pour la création des Normes de Construction (CNE-ITP)
CTM {ctm_number} — {ctm_nom}

Cher(ère) {nom},

Suite à votre inscription sur la plateforme CNETP et à votre affectation au sein du Comité Technique Miroir (CTM) « {ctm_nom} », nous vous communiquons ci-dessous le détail de vos responsabilités en tant que :

➤ {titre_poste}

Vos missions principales :

{instructions}

Nous vous remercions de prendre connaissance de ces responsabilités et de vous tenir disponible pour les prochaines sessions de votre CTM.

Pour toute question relative à votre rôle ou à l'utilisation de la plateforme, le Support Technique reste à votre disposition au numéro suivant : {numero_support}.

Veuillez agréer, Honorable Expert, notre haute considération patriotique.

La Cellule Technique de Coordination (CTC)
Secrétariat Général aux ITP / Direction de la Réglementation et des Normes.
📍 Kinshasa, RDC."""


def determiner_role(expert):
    ctm = expert.ctm
    if ctm.scientific_president_id == expert.id:
        return "PRESIDENT"
    if ctm.rapporteur_id == expert.id:
        return "RAPPORTEUR"
    if ctm.secretary_id == expert.id:
        return "SECRETARY"
    return "MEMBRE"


class Command(BaseCommand):
    help = (
        "Envoie à chaque Expert affecté à un Comité Technique Miroir (CTM) un "
        "email détaillant les responsabilités de son rôle (Président scientifique, "
        "Rapporteur, Secrétaire ou Membre)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                             help="Affiche ce qui serait envoyé sans rien envoyer réellement.")
        parser.add_argument("--ctm", type=int, default=None,
                             help="Ne notifie que les membres du CTM portant ce numéro (1 à 8).")
        parser.add_argument("--statut", type=str, default=None,
                             help="Ne notifie que les experts ayant ce statut (ex: ACTIVE, PENDING).")
        parser.add_argument("--skip", type=int, default=0,
                             help="Ignore les N premiers destinataires (utile pour reprendre un envoi interrompu).")
        parser.add_argument("--limit", type=int, default=None,
                             help="Ne traite que les N destinataires suivants (après --skip).")

    def handle(self, *args, **options):
        qs = Expert.objects.filter(ctm__isnull=False).select_related("user", "ctm").order_by("ctm__number", "user__last_name")

        if options["ctm"] is not None:
            qs = qs.filter(ctm__number=options["ctm"])
        if options["statut"]:
            qs = qs.filter(status=options["statut"].upper())

        destinataires = list(qs)

        if not destinataires:
            self.stdout.write(self.style.WARNING(
                "⚠️  Aucun Expert avec un CTM assigné ne correspond aux critères. Rien à envoyer."
            ))
            return

        skip = options["skip"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        a_traiter = destinataires[skip:]
        if limit is not None:
            a_traiter = a_traiter[:limit]

        if skip or limit is not None:
            self.stdout.write(self.style.WARNING(
                f"ℹ️  {len(a_traiter)} destinataire(s) traité(s) "
                f"(skip={skip}, limit={limit}) sur {len(destinataires)} au total."
            ))

        emails_ok, emails_ko, sans_email = 0, 0, 0

        for expert in a_traiter:
            email = (expert.user.email or "").strip()
            nom = expert.full_name

            if not email:
                sans_email += 1
                self.stdout.write(self.style.WARNING(f"⚠️  Pas d'email pour {nom} — ignoré."))
                continue

            role = determiner_role(expert)
            titre_poste, instructions = INSTRUCTIONS_PAR_ROLE[role]

            message = MESSAGE_TEMPLATE.format(
                ctm_number=expert.ctm.number,
                ctm_nom=expert.ctm.name,
                nom=nom,
                titre_poste=titre_poste,
                instructions=instructions,
                numero_support=NUMERO_SUPPORT_TECHNIQUE,
            )

            if dry_run:
                self.stdout.write(f"[DRY-RUN] Email → {nom} <{email}> — CTM{expert.ctm.number} / {titre_poste}")
                continue

            try:
                send_mail(
                    subject=SUJET_EMAIL,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                emails_ok += 1
                self.stdout.write(self.style.SUCCESS(f"✅ Email envoyé à {nom} <{email}> — CTM{expert.ctm.number} / {titre_poste}"))
            except Exception:
                emails_ko += 1
                logger.exception("Échec de l'envoi de l'email à %s <%s>", nom, email)
                self.stdout.write(self.style.ERROR(f"❌ Échec email pour {nom} <{email}>"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(
            f"📧 Emails  : {emails_ok} envoyé(s), {emails_ko} échec(s), {sans_email} sans adresse"
        ))
        self.stdout.write("=" * 60 + "\n")

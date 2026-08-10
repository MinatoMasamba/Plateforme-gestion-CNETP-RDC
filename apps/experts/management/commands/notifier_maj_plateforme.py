"""
Commande de diffusion : informe les Experts réellement inscrits que la
plateforme vient d'être mise à jour et peut désormais être installée comme
application (PC ou mobile, utilisable hors ligne).

Source des destinataires : apps/experts/data/inscrits.json — export des
inscriptions réelles (Nom, Postnom, Prénom, Téléphone, Email, Structure
Origine), plus fiable que la liste codée en dur de
notifier_experts_inscription.py.

Usage :
    python manage.py notifier_maj_plateforme --dry-run
    python manage.py notifier_maj_plateforme
    python manage.py notifier_maj_plateforme --whatsapp-only
    python manage.py notifier_maj_plateforme --skip 20 --limit 10
"""

import json
import logging
from pathlib import Path

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from apps.experts.management.commands.notifier_experts_inscription import (
    normaliser_numero_whatsapp,
    whatsapp_configure,
    whatsapp_from,
)

logger = logging.getLogger(__name__)

INSCRITS_JSON = Path(__file__).resolve().parent.parent.parent / "data" / "inscrits.json"

SUJET_EMAIL = "CNE-ITP — La plateforme est mise à jour"

MESSAGE_TEMPLATE = """Bonjour {prenom},

Nous espérons que vous allez bien.

Nous vous informons que la plateforme CNE-ITP vient d'être mise à jour.

🔗 {lien}

Dès votre prochaine connexion, un message vous proposera d'installer l'application — que vous soyez sur ordinateur ou sur téléphone mobile. Une fois installée, elle reste accessible et utilisable même hors connexion internet.

Nous vous remercions pour votre engagement au sein de {structure}.

Cordialement,
L'équipe technique CNE-ITP"""

LIEN_PLATEFORME = "https://workalldomain.pythonanywhere.com/"


def charger_inscrits():
    with open(INSCRITS_JSON, encoding="utf-8") as f:
        return json.load(f)


class Command(BaseCommand):
    help = (
        "Envoie à chaque expert réellement inscrit (apps/experts/data/inscrits.json) "
        "un message l'informant de la mise à jour de la plateforme et de la "
        "possibilité d'installer l'application, par email et par WhatsApp."
    )

    def add_arguments(self, parser):
        parser.add_argument("--lien", type=str, default=None,
                             help="Lien vers la plateforme à insérer dans le message (sinon valeur par défaut).")
        parser.add_argument("--dry-run", action="store_true",
                             help="Affiche ce qui serait envoyé sans rien envoyer réellement.")
        parser.add_argument("--skip", type=int, default=0,
                             help="Ignore les N premiers inscrits (utile pour reprendre un envoi interrompu).")
        parser.add_argument("--limit", type=int, default=None,
                             help="Ne traite que les N inscrits suivants (après --skip).")
        parser.add_argument("--whatsapp-only", action="store_true",
                             help="N'envoie que le WhatsApp (n'envoie pas l'email).")
        parser.add_argument("--email-only", action="store_true",
                             help="N'envoie que l'email (n'envoie pas le WhatsApp).")

    def handle(self, *args, **options):
        lien = options["lien"] or LIEN_PLATEFORME
        dry_run = options["dry_run"]
        skip = options["skip"]
        limit = options["limit"]
        whatsapp_only = options["whatsapp_only"]
        email_only = options["email_only"]

        inscrits = charger_inscrits()
        if skip:
            inscrits = inscrits[skip:]
        if limit is not None:
            inscrits = inscrits[:limit]

        self.stdout.write(f"ℹ️  {len(inscrits)} inscrit(s) à traiter.")

        client = None
        if not dry_run and whatsapp_configure() and not email_only:
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        elif not dry_run and not email_only:
            self.stdout.write(self.style.WARNING(
                "⚠️  Twilio non configuré (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / "
                "TWILIO_WHATSAPP_FROM) — les messages WhatsApp seront seulement journalisés."
            ))

        emails_ok = emails_ko = wa_ok = wa_ko = sans_numero = 0

        for inscrit in inscrits:
            prenom = (inscrit.get("Prénom") or "").strip()
            nom = (inscrit.get("Nom") or "").strip()
            postnom = (inscrit.get("Postnom") or "").strip()
            nom_complet = " ".join(p for p in [prenom, postnom, nom] if p) or "Cher membre"
            structure = (inscrit.get("Structure Origine") or "").strip() or "votre structure"
            email = (inscrit.get("Email") or "").strip()
            numero = (inscrit.get("Téléphone") or "").strip()

            message = MESSAGE_TEMPLATE.format(prenom=prenom or nom_complet, structure=structure, lien=lien)

            if email and not whatsapp_only:
                if dry_run:
                    self.stdout.write(f"[DRY-RUN] Email → {nom_complet} <{email}> ({structure})")
                else:
                    try:
                        send_mail(
                            subject=SUJET_EMAIL,
                            message=message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[email],
                            fail_silently=False,
                        )
                        emails_ok += 1
                        self.stdout.write(self.style.SUCCESS(f"✅ Email envoyé à {nom_complet} <{email}>"))
                    except Exception:
                        emails_ko += 1
                        logger.exception("Échec de l'envoi de l'email à %s <%s>", nom_complet, email)
                        self.stdout.write(self.style.ERROR(f"❌ Échec email pour {nom_complet} <{email}>"))

            if not email_only:
                if not numero:
                    sans_numero += 1
                    self.stdout.write(self.style.WARNING(f"⚠️  Aucun numéro trouvé pour {nom_complet}"))
                elif dry_run:
                    self.stdout.write(f"[DRY-RUN] WhatsApp → {nom_complet} <{numero}> ({structure})")
                else:
                    try:
                        if client is not None:
                            client.messages.create(
                                from_=whatsapp_from(),
                                to=f"whatsapp:{normaliser_numero_whatsapp(numero)}",
                                body=message,
                            )
                        else:
                            logger.info(
                                "WhatsApp non configuré — message simulé pour %s <%s> : %s",
                                nom_complet, numero, message,
                            )
                        wa_ok += 1
                        self.stdout.write(self.style.SUCCESS(f"✅ WhatsApp envoyé à {nom_complet} <{numero}>"))
                    except Exception:
                        wa_ko += 1
                        logger.exception("Échec de l'envoi WhatsApp à %s <%s>", nom_complet, numero)
                        self.stdout.write(self.style.ERROR(f"❌ Échec WhatsApp pour {nom_complet} <{numero}>"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"📧 Emails   : {emails_ok} envoyé(s), {emails_ko} échec(s)"))
        self.stdout.write(self.style.SUCCESS(f"📱 WhatsApp : {wa_ok} envoyé(s), {wa_ko} échec(s), {sans_numero} sans numéro"))
        self.stdout.write("=" * 60 + "\n")

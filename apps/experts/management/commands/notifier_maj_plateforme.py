"""
Commande de diffusion : informe les Experts réellement inscrits (en base, avec leur
structure enregistrée) que la plateforme CNE-ITP a été mise à jour et qu'une
application installable (PWA, utilisable hors ligne) est désormais disponible.

Les numéros WhatsApp ne sont pas systématiquement renseignés sur les comptes en
base (Expert.whatsapp_number). Ils sont donc recherchés par correspondance de nom
dans apps/experts/data/inscrits.json (export du formulaire d'inscription), qui
n'est pas directement lié aux comptes Expert par une clé étrangère.

Usage :
    python manage.py notifier_maj_plateforme --dry-run
    python manage.py notifier_maj_plateforme --dry-run --structure "Ordre des Architectes"
    python manage.py notifier_maj_plateforme
    python manage.py notifier_maj_plateforme --skip 50 --limit 20
"""

import json
import logging
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from apps.experts.models import Expert

logger = logging.getLogger(__name__)

INSCRITS_JSON = Path(__file__).resolve().parents[2] / "data" / "inscrits.json"

SEUIL_CORRESPONDANCE_DEFAUT = 0.6

LIEN_PLATEFORME_DEFAUT = "https://workalldomain.pythonanywhere.com/"

SUJET_EMAIL = "CNE-ITP — Mise à jour de la plateforme : application désormais disponible"

MESSAGE_TEMPLATE = """Honorable {nom},

Nous avons l'honneur de vous informer, au nom de la Coordination du Secrétariat technique de la CNE-ITP, que la plateforme numérique de la Commission a fait l'objet d'une mise à jour.

🔗 Lien vers la plateforme : {lien}

Dès votre prochaine connexion, un message s'affichera pour vous inviter à installer l'application dédiée. Celle-ci est disponible aussi bien sur ordinateur que sur téléphone mobile, s'installe en quelques instants et demeure accessible même en l'absence de connexion internet.

Nous vous prions de bien vouloir procéder à cette installation dans les meilleurs délais.

Le Service de Support Technique reste à votre entière disposition pour toute assistance.

Veuillez agréer, Honorable {nom}, l'expression de notre haute considération.

La Coordination du Secrétariat technique
CNE-ITP — Secrétariat Général aux ITP
Kinshasa, RDC."""


def normaliser_texte(texte):
    texte = texte or ""
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii")
    texte = texte.lower()
    texte = re.sub(r"[^a-z\s]", " ", texte)
    return re.sub(r"\s+", " ", texte).strip()


def normaliser_numero_whatsapp(numero):
    """Convertit un numéro local congolais (0XXXXXXXXX) au format E.164 (+243XXXXXXXXX)."""
    numero = numero.strip().replace(" ", "")
    if numero.startswith("+"):
        return numero
    if numero.startswith("0"):
        return "+243" + numero[1:]
    return "+" + numero


def whatsapp_configure():
    return bool(
        settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_WHATSAPP_FROM
    )


def whatsapp_from():
    expediteur = settings.TWILIO_WHATSAPP_FROM.strip()
    if expediteur.startswith("whatsapp:"):
        return expediteur
    return f"whatsapp:{expediteur}"


def envoyer_whatsapp(client, numero, message):
    client.messages.create(
        from_=whatsapp_from(),
        to=f"whatsapp:{normaliser_numero_whatsapp(numero)}",
        body=message,
    )


def charger_inscrits():
    """Charge inscrits.json et construit un index (nom normalisé -> téléphone)."""
    if not INSCRITS_JSON.exists():
        return []
    with open(INSCRITS_JSON, encoding="utf-8") as f:
        data = json.load(f)
    entrees = []
    for row in data:
        nom_complet = " ".join(
            filter(None, [row.get("Nom"), row.get("Postnom"), row.get("Prénom")])
        )
        cle = normaliser_texte(nom_complet)
        telephone = (row.get("Téléphone") or "").strip()
        if cle and telephone:
            entrees.append({"cle": cle, "mots": set(cle.split()), "telephone": telephone})
    return entrees


def trouver_telephone(nom_expert, inscrits, seuil):
    """Cherche le meilleur numéro correspondant à nom_expert dans inscrits (liste d'entrées)."""
    cle_expert = normaliser_texte(nom_expert)
    mots_expert = set(cle_expert.split())
    if not mots_expert:
        return None, 0.0

    meilleur, meilleur_score = None, 0.0
    for entree in inscrits:
        if not entree["mots"]:
            continue
        chevauchement = len(mots_expert & entree["mots"]) / max(len(mots_expert), 1)
        ratio = SequenceMatcher(None, cle_expert, entree["cle"]).ratio()
        score = max(chevauchement, ratio)
        if score > meilleur_score:
            meilleur_score, meilleur = score, entree

    if meilleur and meilleur_score >= seuil:
        return meilleur["telephone"], meilleur_score
    return None, meilleur_score


class Command(BaseCommand):
    help = (
        "Informe les Experts réellement inscrits en base (avec leur structure) que "
        "la plateforme CNE-ITP est mise à jour et que l'application (PWA, hors ligne) "
        "est disponible. Le numéro WhatsApp est recherché par nom dans inscrits.json."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche ce qui serait envoyé (et le résultat du matching) sans rien envoyer réellement.",
        )
        parser.add_argument(
            "--structure",
            type=str,
            default=None,
            help="Ne traite que les experts rattachés à cette structure (nom ou sigle, correspondance partielle).",
        )
        parser.add_argument(
            "--statuts",
            type=str,
            default="PENDING,ACTIVE,INACTIVE,SUSPENDED",
            help="Statuts Expert à inclure, séparés par des virgules (défaut : tous sauf REJECTED).",
        )
        parser.add_argument(
            "--seuil",
            type=float,
            default=SEUIL_CORRESPONDANCE_DEFAUT,
            help=f"Seuil de similarité (0-1) pour valider une correspondance de nom (défaut {SEUIL_CORRESPONDANCE_DEFAUT}).",
        )
        parser.add_argument(
            "--lien",
            type=str,
            default=LIEN_PLATEFORME_DEFAUT,
            help="Lien vers la plateforme à insérer dans le message (défaut : URL de production).",
        )
        parser.add_argument("--skip", type=int, default=0, help="Ignore les N premiers experts.")
        parser.add_argument("--limit", type=int, default=None, help="Ne traite que les N experts suivants (après --skip).")
        parser.add_argument("--whatsapp-only", action="store_true", help="N'envoie que le WhatsApp.")
        parser.add_argument("--email-only", action="store_true", help="N'envoie que l'email.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        lien = options["lien"]
        seuil = options["seuil"]
        whatsapp_only = options["whatsapp_only"]
        email_only = options["email_only"]
        statuts = [s.strip() for s in options["statuts"].split(",") if s.strip()]

        qs = Expert.objects.select_related("user", "structure").filter(status__in=statuts)
        if options["structure"]:
            qs = qs.filter(structure__name__icontains=options["structure"])
        qs = qs.order_by("structure__name", "user__last_name", "user__first_name")

        skip, limit = options["skip"], options["limit"]
        experts = list(qs[skip:])
        if limit is not None:
            experts = experts[:limit]

        if not experts:
            self.stdout.write(self.style.WARNING("⚠️  Aucun expert à traiter avec ces filtres."))
            return

        inscrits = charger_inscrits()
        self.stdout.write(f"ℹ️  {len(inscrits)} entrée(s) chargée(s) depuis inscrits.json pour le matching des numéros.")
        self.stdout.write(f"ℹ️  {len(experts)} expert(s) à traiter (sur {qs.count()} au total avec ces filtres).\n")

        client = None
        if not dry_run and whatsapp_configure():
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        elif not dry_run:
            self.stdout.write(self.style.WARNING(
                "⚠️  Twilio non configuré (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / "
                "TWILIO_WHATSAPP_FROM) — les WhatsApp seront seulement journalisés."
            ))

        emails_ok = emails_ko = wa_ok = wa_ko = wa_non_trouve = 0

        for expert in experts:
            nom = expert.user.get_full_name() or expert.user.username
            structure = expert.structure.name if expert.structure else "Structure inconnue"
            email = (expert.user.email or "").strip()
            telephone = (expert.whatsapp_number or "").strip()

            score = None
            if not telephone:
                telephone, score = trouver_telephone(nom, inscrits, seuil)

            message = MESSAGE_TEMPLATE.format(nom=nom, lien=lien)

            if email and not whatsapp_only:
                if dry_run:
                    self.stdout.write(f"[DRY-RUN] Email → {nom} ({structure}) <{email}>")
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
                        self.stdout.write(self.style.SUCCESS(f"✅ Email envoyé à {nom} ({structure}) <{email}>"))
                    except Exception:
                        emails_ko += 1
                        logger.exception("Échec de l'envoi de l'email à %s <%s>", nom, email)
                        self.stdout.write(self.style.ERROR(f"❌ Échec email pour {nom} <{email}>"))
            elif not email and not whatsapp_only:
                self.stdout.write(self.style.WARNING(f"⚠️  Pas d'email pour {nom} ({structure})"))

            if not email_only:
                if telephone:
                    info_score = f" (score={score:.2f})" if score is not None else " (numéro du compte)"
                    if dry_run:
                        self.stdout.write(f"[DRY-RUN] WhatsApp → {nom} ({structure}) <{telephone}>{info_score}")
                    else:
                        try:
                            if client is not None:
                                envoyer_whatsapp(client, telephone, message)
                            else:
                                logger.info("WhatsApp non configuré — message simulé pour %s <%s>", nom, telephone)
                            wa_ok += 1
                            self.stdout.write(self.style.SUCCESS(f"✅ WhatsApp envoyé à {nom} ({structure}) <{telephone}>"))
                        except Exception:
                            wa_ko += 1
                            logger.exception("Échec de l'envoi WhatsApp à %s <%s>", nom, telephone)
                            self.stdout.write(self.style.ERROR(f"❌ Échec WhatsApp pour {nom} <{telephone}>"))
                else:
                    wa_non_trouve += 1
                    self.stdout.write(self.style.WARNING(
                        f"⚠️  Aucun numéro trouvé pour {nom} ({structure}) — meilleur score={score:.2f}" if score else
                        f"⚠️  Aucun numéro trouvé pour {nom} ({structure})"
                    ))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"📧 Emails   : {emails_ok} envoyé(s), {emails_ko} échec(s)"))
        self.stdout.write(self.style.SUCCESS(f"📱 WhatsApp : {wa_ok} envoyé(s), {wa_ko} échec(s), {wa_non_trouve} numéro(s) introuvable(s)"))
        self.stdout.write("=" * 60 + "\n")

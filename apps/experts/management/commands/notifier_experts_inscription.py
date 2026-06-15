"""
Commande de diffusion : invite les 200 Experts mandatés du Collège CNE-ITP
à procéder à leur inscription officielle sur la plateforme, par email et WhatsApp.

Usage :
    python manage.py notifier_experts_inscription
    python manage.py notifier_experts_inscription --lien https://cnetp.cd/inscription
    python manage.py notifier_experts_inscription --dry-run
"""

import json
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Liste des Experts à notifier : un dictionnaire par personne.
# Champs attendus : "nom", "email" ou "mail" (optionnel) et "telephone" ou
# "numero" (optionnel, format local 0XXXXXXXXX ou international +243XXXXXXXXX).
# ---------------------------------------------------------------------------
EXPERTS =  [

  {
    "nom": "eddy masamba  mpaka-yoka ",
    "mail": "edmasamba100@gmail.com",
    "numero": "0983290982"
  },

  {
    "nom": "Blaise MAMONIKA  LUEMBA ",
    "mail": "luembablaiseluemba@gmail.com",
    "numero": "0898011141"
  },
  {
    "nom": "Deborah pongombo Omoyi",
    "mail": "omoyiandrea@gmail.com",
    "numero": "0820182497"
  },
  {
    "nom": "Parfait  Muaba  Mutambay ",
    "mail": "romanickparfait@gmail.com",
    "numero": "0824988937"
  },
  {
    "nom": "Israël-Tshany  MUSANGANI  BENDERA ",
    "mail": "istshany_bend@yahoo.fr",
    "numero": "0998193627"
  },
  {
    "nom": "RODRIGUE  NTIMANSIEMI MAMBUENI ",
    "mail": "rmnsj1@gmail.com",
    "numero": "0815844637"
  },
  {
    "nom": "Emmanuel Kibwe Mwila",
    "mail": "emmanuel.mwila@foner.cd",
    "numero": "0814067413"
  },
  {
    "nom": "Patrick  MAKAMBO  KAKU ",
    "mail": "kakupatrick87@gmail.com",
    "numero": "0896480552"
  },
  {
    "nom": "Michel Soko longe Uyumbu",
    "mail": "micheluyumbu2021@gmail.com",
    "numero": "0817793505"
  },
  {
    "nom": "Ben  NGOY CIEPELA ",
    "mail": "bengoy@outlook.com",
    "numero": "0999997290"
  },
  {
    "nom": "Winner Balinga Mapanda",
    "mail": "winner.mapanda@foner.cd",
    "numero": "0973006030"
  },
  {
    "nom": "Winner Balinga Mapanda",
    "mail": "winner.mapanda@foner.cd",
    "numero": "0973006030"
  },
  {
    "nom": "Jules KABOFI NKOMBWA",
    "mail": "gectopoplus@gmail.com",
    "numero": "0815007746"
  },
  {
    "nom": "CHRISTIAN CUBAKA ACIZA",
    "mail": "christianaciza@gmail.com",
    "numero": "0994577416"
  },
  {
    "nom": "Guelord BOLIPUA MPIA",
    "mail": "guelordboli@gmail.com",
    "numero": "0811485775"
  },
  {
    "nom": "Jean Marie  KUMWAMBA  N'SAPU ",
    "mail": "gtnconstruct@gmail.com",
    "numero": "0991003456"
  },
  {
    "nom": "Christian Makindu Kyalumba ",
    "mail": "chkyamak1@gmail.com",
    "numero": "0999927990"
  },
  {
    "nom": "Joseph Nono NANA NKIERE",
    "mail": "nkierenana@yahoo.com",
    "numero": "0823051460"
  },
  {
    "nom": "Jean de Dieu KOEBONI BOBO",
    "mail": "bobojeandedieu@gmail.com",
    "numero": "0816422014"
  },
  {
    "nom": "Roger Kandu Mayi Vibila",
    "mail": "rgvibila@holops.com",
    "numero": "0816861660"
  },
  {
    "nom": "ERIC  PALA KIBALA ",
    "mail": "kibalaeric01@gmail.com",
    "numero": "0999943140"
  },
  {
    "nom": "Yves Muzola Ngoma",
    "mail": "yvesmuzola@gmail.com",
    "numero": "0991407271"
  },
  {
    "nom": "Gabriel Zaatcha KAZADI MUHOLA LASER",
    "mail": "laser.muhola@anat.gouv.cd",
    "numero": "0891558686"
  },
  {
    "nom": "Alpha Memidra  Mapoko Isongo Egbango",
    "mail": "alpha.egbango@celluleinfra.org",
    "numero": "0819823416"
  },
  {
    "nom": "WIREN KITSHIAKA  MONDU",
    "mail": "wiren.mondu@celluleinfra.org",
    "numero": "0810722822"
  },
  {
    "nom": "CHICO VUZUNGA MWADI",
    "mail": "mwadivuzungachico@gmail.com",
    "numero": "0819090470"
  },
  {
    "nom": "Blaise MAMONIKA  LUEMBA ",
    "mail": "luembablaiseluemba@gmail.com",
    "numero": "0898011141"
  },
  {
    "nom": "Guycele  Mpioko Malabi",
    "mail": "celemalabi@gmail.com",
    "numero": "0810622671"
  },
  {
    "nom": "Jean Bosco  Malele Bifulu ",
    "mail": "bifuluscolie2014@gmail.com",
    "numero": "0814029156"
  },
  {
    "nom": "Olivier  PASHO-LAWATA  ROGHO",
    "mail": "oliverutche@gmail.com",
    "numero": "0824376306"
  },
  {
    "nom": "Ralph Désiré  Bizongo",
    "mail": "desire.bizongo@celluleinfra.org",
    "numero": "0979059000"
  },
  {
    "nom": "Romain Mbule Bussa",
    "mail": "romainlandry.bussa@gmail.com",
    "numero": "0853683861"
  },
  {
    "nom": "Alpha Memidra  Mapoko Isongo Egbango",
    "mail": "alpha.egbango@celluleinfra.org",
    "numero": "0819823416"
  },
  {
    "nom": "Didier Mukendi Kamunga ",
    "mail": "kamungadidier@yahoo.fr",
    "numero": "0994744092"
  },
  {
    "nom": "Willy MANGA VALE",
    "mail": "willy.vale@inbtp.ac.cd",
    "numero": "0971550108"
  },
  {
    "nom": "Pires TOFOFA  LISINGO",
    "mail": "pireslisingo@gmail.com",
    "numero": "0812153345"
  },
  {
    "nom": "Doris  Kilungu  Kayamba ",
    "mail": "kayambakilungudoris@gmail.com",
    "numero": "0897956637"
  },
  {
    "nom": "Pires TOFOFA LISINGO",
    "mail": "pireslisingo@gmail.com",
    "numero": "0812153345"
  },
  {
    "nom": "Chadrack  Mutambayi  Ngoie",
    "mail": "ngoiechadrack2@gmail.com",
    "numero": "0892256018"
  },
  {
    "nom": "Chadrack  Mutambayi  Ngoie",
    "mail": "ngoiechadrack2@gmail.com",
    "numero": "0892256018"
  }


  
]



LIEN_INSCRIPTION_PAR_DEFAUT = "[Insérer le lien ici]"

SUJET_EMAIL = "🇨🇩 CNE-ITP — Invitation à votre inscription de test (Collège des 200 Experts)"

MESSAGE_TEMPLATE = """🇨🇩 MINISTERE DES INFRASTRUCTURES ET TRAVAUX PUBLICS 🇨🇩
Commission Nationale pour la création des Normes de Construction (CNE-ITP)
Pour les Honorables Experts Mandatés (Collège des 200)

Honorables Experts, Chers Collègues,

Au nom de la Haute Coordination Générale et du Secrétariat Général aux ITP, nous vous invitons, suite à votre désignation officielle, à finaliser votre mise en place administrative au sein de la CNE-ITP.

Vous êtes priés de procéder ce jour à votre inscription de test sur la plateforme numérique afin de valider votre affectation fonctionnelle dans vos instances respectives (Comité de Pilotage, Cellule Technique ou Comités Miroirs - CTM).

🔗 Lien pour votre inscription : 👉 {lien}

Note importante : Veillez à renseigner avec exactitude votre structure de provenance et votre profil technique. Votre participation constitue le garant scientifique du futur Référentiel Normatif National du Génie Civil en RDC.

Le Service de Support Technique reste à votre entière disposition.

Veuillez agréer, Honorables Experts, notre haute considération patriotique.

La Cellule Technique de Coordination (CTC)
Secrétariat Général aux ITP / Direction de la Réglementation et des Normes.
📍 Kinshasa, RDC."""


def whatsapp_configure():
    return bool(
        settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_WHATSAPP_FROM
    )


def normaliser_numero_whatsapp(numero):
    """Convertit un numéro local congolais (0XXXXXXXXX) au format E.164 (+243XXXXXXXXX)."""
    numero = numero.strip().replace(" ", "")
    if numero.startswith("+"):
        return numero
    if numero.startswith("0"):
        return "+243" + numero[1:]
    return "+" + numero


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


class Command(BaseCommand):
    help = (
        "Envoie à chaque Expert du Collège des 200 (liste EXPERTS) une invitation "
        "à s'inscrire sur la plateforme CNE-ITP, par email et par WhatsApp."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--lien",
            type=str,
            default=None,
            help="Lien d'inscription à insérer dans le message (sinon valeur par défaut).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche ce qui serait envoyé sans rien envoyer réellement.",
        )
        parser.add_argument(
            "--skip",
            type=int,
            default=0,
            help="Ignore les N premiers experts de la liste (utile pour reprendre un envoi interrompu).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Ne traite que les N experts suivants (après --skip).",
        )
        parser.add_argument(
            "--whatsapp-only",
            action="store_true",
            help="N'envoie que le WhatsApp (n'envoie pas l'email).",
        )
        parser.add_argument(
            "--email-only",
            action="store_true",
            help="N'envoie que l'email (n'envoie pas le WhatsApp).",
        )

    def handle(self, *args, **options):
        if not EXPERTS:
            self.stdout.write(self.style.WARNING(
                "⚠️  La liste EXPERTS est vide — renseignez-la dans "
                "apps/experts/management/commands/notifier_experts_inscription.py avant de relancer."
            ))
            return

        lien = options["lien"] or LIEN_INSCRIPTION_PAR_DEFAUT
        message = MESSAGE_TEMPLATE.format(lien=lien)
        dry_run = options["dry_run"]

        client = None
        if not dry_run and whatsapp_configure():
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        elif not dry_run:
            self.stdout.write(self.style.WARNING(
                "⚠️  Twilio non configuré (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / "
                "TWILIO_WHATSAPP_FROM) — les messages WhatsApp seront seulement journalisés."
            ))

        skip = options["skip"]
        limit = options["limit"]
        whatsapp_only = options["whatsapp_only"]
        email_only = options["email_only"]

        experts_a_traiter = EXPERTS[skip:]
        if limit is not None:
            experts_a_traiter = experts_a_traiter[:limit]

        if skip or limit is not None:
            self.stdout.write(self.style.WARNING(
                f"ℹ️  {len(experts_a_traiter)} expert(s) traité(s) "
                f"(skip={skip}, limit={limit}) sur {len(EXPERTS)} au total."
            ))

        emails_ok, emails_ko = 0, 0
        wa_ok, wa_ko = 0, 0

        for expert in experts_a_traiter:
            nom = expert.get("nom", "Honorable Expert")
            email = (expert.get("email") or expert.get("mail") or "").strip()
            telephone = (expert.get("telephone") or expert.get("numero") or "").strip()

            if email and not whatsapp_only:
                if dry_run:
                    self.stdout.write(f"[DRY-RUN] Email → {nom} <{email}>")
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
                        self.stdout.write(self.style.SUCCESS(f"✅ Email envoyé à {nom} <{email}>"))
                    except Exception:
                        emails_ko += 1
                        logger.exception("Échec de l'envoi de l'email à %s <%s>", nom, email)
                        self.stdout.write(self.style.ERROR(f"❌ Échec email pour {nom} <{email}>"))

            if telephone and not email_only:
                if dry_run:
                    self.stdout.write(f"[DRY-RUN] WhatsApp → {nom} <{telephone}>")
                else:
                    try:
                        if client is not None:
                            envoyer_whatsapp(client, telephone, message)
                        else:
                            logger.info(
                                "WhatsApp non configuré — message simulé pour %s <%s> : %s",
                                nom, telephone, message,
                            )
                        wa_ok += 1
                        self.stdout.write(self.style.SUCCESS(f"✅ WhatsApp envoyé à {nom} <{telephone}>"))
                    except Exception:
                        wa_ko += 1
                        logger.exception("Échec de l'envoi WhatsApp à %s <%s>", nom, telephone)
                        self.stdout.write(self.style.ERROR(f"❌ Échec WhatsApp pour {nom} <{telephone}>"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(
            f"📧 Emails  : {emails_ok} envoyé(s), {emails_ko} échec(s)"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"📱 WhatsApp: {wa_ok} envoyé(s), {wa_ko} échec(s)"
        ))
        self.stdout.write("=" * 60 + "\n")

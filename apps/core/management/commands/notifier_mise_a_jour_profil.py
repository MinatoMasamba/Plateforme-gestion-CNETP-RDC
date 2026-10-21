"""Commande d'envoi du communiqué de mise à jour des profils experts.

Envoie à tous les experts enregistrés (disposant d'une adresse e-mail) un
message les invitant à mettre à jour leur profil et leur affectation, avec le
lien vers la page communiqué / formulaire.

Usage :
    python manage.py notifier_mise_a_jour_profil --dry-run
    python manage.py notifier_mise_a_jour_profil
    python manage.py notifier_mise_a_jour_profil --statut ACTIVE
    python manage.py notifier_mise_a_jour_profil --skip 20 --limit 20
    python manage.py notifier_mise_a_jour_profil --base-url https://plateforme.cne-itp.cd
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.urls import reverse

from apps.experts.models import Expert

logger = logging.getLogger(__name__)


def email_expert(user):
    """Adresse email de l'expert depuis la base (User.email), avec repli sur le
    username s'il s'agit d'une adresse email (comptes historiques)."""
    email = (user.email or "").strip()
    if not email:
        username = (user.username or "").strip()
        if "@" in username:
            email = username
    return email


SUJET_EMAIL = "🇨🇩 CNE-ITP — Mise à jour obligatoire de votre profil expert"

MESSAGE_TEMPLATE = """🇨🇩 COMMISSION NATIONALE D'ÉLABORATION DES NORMES ITP (CNE-ITP)

Mise à jour obligatoire des profils et des affectations

Cher(ère) {nom},

Dans le cadre de la réorganisation de la CNE-ITP et de l'adoption de sa nouvelle
structure organisationnelle, tous les experts enregistrés sur la plateforme sont
invités à mettre à jour leur profil et à confirmer leur affectation.

Cette démarche est obligatoire, même si vous souhaitez conserver votre groupe de
travail ou votre affectation actuelle, afin de préparer la reprise des activités
prévue pour le lundi 19 octobre 2026.

Comment procéder ?

1. Connectez-vous à la plateforme avec votre compte habituel.
2. Mot de passe oublié ? Utilisez l'option « Mot de passe oublié ».
3. Actualisez vos informations personnelles et professionnelles.
4. Joignez votre CV actualisé au format PDF.
5. Précisez vos domaines de compétence.
6. Confirmez ou modifiez votre sous-commission et votre groupe de travail.
7. Validez le formulaire.

Accéder au communiqué et au formulaire :
{url}

Date limite : jeudi 22 octobre 2026 à 20h30.

Les anciens groupes de travail et les travaux déjà réalisés sont conservés. Tout
expert n'ayant pas effectué cette mise à jour dans le délai imparti pourra voir son
accès à la plateforme suspendu, jusqu'à régularisation de sa situation.

Nous comptons sur votre collaboration et votre diligence.

Ecosys RDC
Équipe technique chargée de la plateforme numérique CNE-ITP
"""


class Command(BaseCommand):
    help = (
        "Envoie à tous les experts un e-mail les invitant à mettre à jour leur "
        "profil, avec le lien vers le communiqué et le formulaire dédiés."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Affiche ce qui serait envoyé sans rien envoyer réellement.")
        parser.add_argument("--statut", type=str, default=None,
                            help="Ne notifie que les experts ayant ce statut (ex: ACTIVE, PENDING).")
        parser.add_argument("--skip", type=int, default=0,
                            help="Ignore les N premiers destinataires (reprise d'un envoi interrompu).")
        parser.add_argument("--limit", type=int, default=None,
                            help="Ne traite que les N destinataires suivants (après --skip).")
        parser.add_argument("--base-url", type=str, default=None,
                            help="URL de base de la plateforme (défaut : settings.SITE_URL).")

    def handle(self, *args, **options):
        base_url = (options["base_url"] or getattr(settings, "SITE_URL", "") or "").rstrip("/")
        if not base_url:
            self.stdout.write(self.style.ERROR(
                "❌ URL de base introuvable. Renseignez --base-url ou settings.SITE_URL."
            ))
            return

        url = base_url + reverse("web:expert_profile_update_notice")

        qs = (
            Expert.objects.select_related("user")
            .order_by("user__last_name", "user__first_name")
        )
        if options["statut"]:
            qs = qs.filter(status=options["statut"].upper())

        destinataires = list(qs)
        if not destinataires:
            self.stdout.write(self.style.WARNING(
                "⚠️  Aucun expert avec une adresse e-mail ne correspond aux critères."
            ))
            return

        skip = options["skip"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        a_traiter = destinataires[skip:]
        if limit is not None:
            a_traiter = a_traiter[:limit]

        self.stdout.write(self.style.WARNING(f"🔗 Lien envoyé : {url}"))
        if skip or limit is not None:
            self.stdout.write(self.style.WARNING(
                f"ℹ️  {len(a_traiter)} destinataire(s) traité(s) "
                f"(skip={skip}, limit={limit}) sur {len(destinataires)} au total."
            ))

        emails_ok, emails_ko = 0, 0

        for expert in a_traiter:
            email = email_expert(expert.user)
            nom = expert.full_name or expert.user.get_full_name() or expert.user.username

            if not email:
                self.stdout.write(self.style.WARNING(f"⚠️  Pas d'email pour {nom} — ignoré."))
                continue

            if dry_run:
                self.stdout.write(f"[DRY-RUN] Email → {nom} <{email}>")
                continue

            message = MESSAGE_TEMPLATE.format(nom=nom, url=url)
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
                logger.exception("Échec de l'envoi à %s <%s>", nom, email)
                self.stdout.write(self.style.ERROR(f"❌ Échec email pour {nom} <{email}>"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(
            f"📧 Emails : {emails_ok} envoyé(s), {emails_ko} échec(s), {len(a_traiter)} traité(s)"
        ))
        self.stdout.write("=" * 60 + "\n")

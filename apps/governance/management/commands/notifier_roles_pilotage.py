"""
Commande de notification : envoie à chaque Expert occupant un poste au
Comité de Pilotage Élargi (PosteNominatif.holder ou PilotageMembreship) un
email détaillant les responsabilités précises de son rôle (Président,
Vice-Président, Secrétaire, Rapporteur, Conseiller institutionnel,
Administrateur technique et financier, Partenaire sectoriel, etc.).

Distincte des emails d'admission (acceptation/rejet) et de confirmation de
compte : cette commande s'adresse uniquement aux Experts déjà inscrits qui
occupent effectivement un poste au sein du Comité de Pilotage.

Usage :
    python manage.py notifier_roles_pilotage --dry-run
    python manage.py notifier_roles_pilotage
    python manage.py notifier_roles_pilotage --skip 5 --limit 10
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from apps.governance.models import PilotageMembreship, PosteNominatif

logger = logging.getLogger(__name__)

NUMERO_SUPPORT_TECHNIQUE = "0983290982"

SUJET_EMAIL = "🇨🇩 CNETP — Votre rôle au sein du Comité de Pilotage Élargi"

INSTRUCTIONS_PAR_ROLE = {
    "PRESIDENT": (
        "Président(e) du Comité de Pilotage Élargi",
        """- Présider l'ensemble des sessions du Comité de Pilotage Élargi et en valider l'ordre du jour ;
- Représenter le Comité auprès du Ministre des ITP, de la Haute Coordination et des partenaires institutionnels ;
- Arbitrer les décisions stratégiques et trancher en cas de blocage entre collèges ;
- Garantir le respect du calendrier de validation du Référentiel Normatif National du Génie Civil.""",
    ),
    "VICE_PRESIDENT": (
        "Vice-Président(e) du Comité de Pilotage Élargi",
        """- Assister le Président et assurer la présidence des sessions en cas d'empêchement de celui-ci ;
- Superviser la coordination entre le Comité de Pilotage et la structure d'origine que vous représentez ;
- Veiller à la bonne articulation entre le Comité de Pilotage et les Comités Techniques Miroirs (CTM) ;
- Contribuer à l'arbitrage des dossiers stratégiques soumis au Comité.""",
    ),
    "SECRETARY": (
        "Secrétaire du Comité de Pilotage Élargi",
        """- Rédiger et diffuser les procès-verbaux de chaque session du Comité ;
- Tenir à jour le registre officiel des décisions et résolutions adoptées ;
- Centraliser, archiver et sécuriser la documentation officielle du Comité de Pilotage ;
- Préparer et transmettre les convocations et l'ordre du jour aux membres.""",
    ),
    "RAPPORTEUR": (
        "Rapporteur Général du Comité de Pilotage Élargi",
        """- Synthétiser les travaux techniques issus des Comités Techniques Miroirs (CTM) et des Groupes de Travail (WG) ;
- Présenter les rapports d'avancement du Référentiel Normatif National lors des sessions du Comité ;
- Consolider les recommandations techniques à transmettre à la Haute Coordination Générale ;
- Assurer le suivi de la mise en œuvre des décisions à caractère technique.""",
    ),
    "CONSEILLER_POLITIQUE": (
        "Conseiller(ère) Institutionnel(le) et Politique",
        """- Conseiller le Comité sur les aspects institutionnels et la cohérence avec les politiques publiques en vigueur ;
- Assurer le lien entre le Comité de Pilotage et l'institution que vous représentez (Cabinet du Ministre, Secrétariat Général, etc.) ;
- Participer activement à chaque session et apporter un éclairage politique et institutionnel sur les dossiers soumis ;
- Relayer auprès de votre structure d'origine les décisions et orientations validées par le Comité.""",
    ),
    "ADMIN_TECH_FIN": (
        "Administrateur(trice) Technique et Financier(ère)",
        """- Superviser les aspects techniques et financiers des dossiers soumis au Comité de Pilotage ;
- Veiller à la bonne gestion et au suivi des ressources allouées au processus de normalisation ;
- Contrôler la conformité administrative et financière des décisions prises par le Comité ;
- Alerter le Bureau Directoire en cas d'écart budgétaire ou administratif constaté.""",
    ),
    "PARTENAIRE_SOC_CIV": (
        "Partenaire Sectoriel et Société Civile",
        """- Représenter au sein du Comité les intérêts de votre secteur et/ou de la société civile ;
- Veiller à ce que les normes élaborées tiennent compte des réalités de terrain et des usagers ;
- Faire remonter au Comité les préoccupations et observations de votre secteur ou structure d'origine ;
- Participer aux consultations techniques relatives aux projets de normes en cours d'examen.""",
    ),
    "CONSEILLER": (
        "Conseiller(ère) du Comité de Pilotage",
        """- Participer aux sessions du Comité de Pilotage et contribuer activement aux délibérations ;
- Apporter votre expertise sur les dossiers techniques et institutionnels soumis au Comité ;
- Relayer auprès de votre structure d'origine les décisions adoptées par le Comité.""",
    ),
}

MESSAGE_TEMPLATE = """🇨🇩 MINISTERE DES INFRASTRUCTURES ET TRAVAUX PUBLICS 🇨🇩
Commission Nationale pour la création des Normes de Construction (CNE-ITP)
{comite_nom}

Cher(ère) {nom},

Suite à votre inscription sur la plateforme CNETP et à votre affectation au sein du Comité de Pilotage Élargi, nous vous communiquons ci-dessous le détail de vos responsabilités en tant que :

➤ {titre_poste}

Vos missions principales :

{instructions}

Nous vous remercions de prendre connaissance de ces responsabilités et de vous tenir disponible pour les prochaines sessions du Comité.

Pour toute question relative à votre poste ou à l'utilisation de la plateforme, le Support Technique reste à votre disposition au numéro suivant : {numero_support}.

Veuillez agréer, Honorable Expert, notre haute considération patriotique.

La Cellule Technique de Coordination (CTC)
Secrétariat Général aux ITP / Direction de la Réglementation et des Normes.
📍 Kinshasa, RDC."""


def collecter_destinataires():
    """
    Construit, sans doublon, la liste des Experts occupant effectivement un
    poste au Comité de Pilotage — en croisant la grille nominative
    (PosteNominatif.holder, plus précise : intitulé exact du poste) et les
    adhésions réelles (PilotageMembreship, utilisées pour les permissions).
    Un Expert présent dans les deux n'est notifié qu'une seule fois.
    """
    destinataires = {}

    postes_pourvus = (
        PosteNominatif.objects
        .filter(holder__isnull=False)
        .select_related("holder__user", "comite")
    )
    for poste in postes_pourvus:
        destinataires[poste.holder_id] = {
            "expert": poste.holder,
            "role": poste.role,
            "titre_poste": poste.title,
            "comite_nom": poste.comite.name,
        }

    memberships = PilotageMembreship.objects.select_related("expert__user", "comite")
    role_choices = dict(PilotageMembreship._meta.get_field("role").choices)
    for membership in memberships:
        destinataires.setdefault(membership.expert_id, {
            "expert": membership.expert,
            "role": membership.role,
            "titre_poste": role_choices.get(membership.role, membership.role),
            "comite_nom": membership.comite.name,
        })

    return list(destinataires.values())


class Command(BaseCommand):
    help = (
        "Envoie à chaque Expert occupant un poste au Comité de Pilotage Élargi "
        "un email détaillant les responsabilités de son rôle (Président, "
        "Conseiller, Administrateur technique et financier, etc.)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche ce qui serait envoyé sans rien envoyer réellement.",
        )
        parser.add_argument(
            "--skip",
            type=int,
            default=0,
            help="Ignore les N premiers destinataires (utile pour reprendre un envoi interrompu).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Ne traite que les N destinataires suivants (après --skip).",
        )

    def handle(self, *args, **options):
        destinataires = collecter_destinataires()

        if not destinataires:
            self.stdout.write(self.style.WARNING(
                "⚠️  Aucun Expert n'occupe actuellement un poste au Comité de Pilotage "
                "(PosteNominatif.holder et PilotageMembreship sont vides). Rien à envoyer."
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

        for item in a_traiter:
            expert = item["expert"]
            email = (expert.user.email or "").strip()
            nom = expert.full_name

            if not email:
                sans_email += 1
                self.stdout.write(self.style.WARNING(f"⚠️  Pas d'email pour {nom} — ignoré."))
                continue

            titre_poste, instructions = INSTRUCTIONS_PAR_ROLE.get(
                item["role"],
                (item["titre_poste"], "- Contribuer aux travaux du Comité de Pilotage selon les orientations reçues."),
            )

            message = MESSAGE_TEMPLATE.format(
                comite_nom=item["comite_nom"],
                nom=nom,
                titre_poste=item["titre_poste"] or titre_poste,
                instructions=instructions,
                numero_support=NUMERO_SUPPORT_TECHNIQUE,
            )

            if dry_run:
                self.stdout.write(f"[DRY-RUN] Email → {nom} <{email}> — {item['titre_poste']}")
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
                self.stdout.write(self.style.SUCCESS(f"✅ Email envoyé à {nom} <{email}>"))
            except Exception:
                emails_ko += 1
                logger.exception("Échec de l'envoi de l'email à %s <%s>", nom, email)
                self.stdout.write(self.style.ERROR(f"❌ Échec email pour {nom} <{email}>"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(
            f"📧 Emails  : {emails_ok} envoyé(s), {emails_ko} échec(s), {sans_email} sans adresse"
        ))
        self.stdout.write("=" * 60 + "\n")

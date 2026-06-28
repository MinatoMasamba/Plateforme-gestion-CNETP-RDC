"""
Management command : envoie à chaque expert enregistré sur la plateforme un
message détaillant ce qu'il doit faire en fonction du/des poste(s) qu'il occupe
(Comité de Pilotage, Cellule Technique de Coordination, Niveau Exécutif,
Présidence/Secrétariat/Rapporteur de CTM ou de WG, ou simple membre).

Ce message est distinct des notifications d'admission / confirmation déjà
envoyées ailleurs dans la plateforme : il sert à rappeler à chaque expert ses
responsabilités concrètes selon le rôle qu'il a choisi ou qui lui a été
attribué.
"""

from django.core.management.base import BaseCommand, CommandError

from apps.experts.models import Expert
from apps.governance.models import Affectation, CTCMembership, PilotageMembreship
from apps.mobileapp.models import Notification
from apps.mobileapp.tasks import dispatch_notification

DEV_CONTACT = "0983290982"

PILOTAGE_DUTIES = {
    'PRESIDENT': [
        "Convoquer et présider les réunions du Comité de Pilotage.",
        "Valider l'ordre du jour stratégique et arbitrer les orientations majeures du CNETP.",
        "Représenter le Comité auprès du Ministère des ITP et des autres autorités de tutelle.",
        "Signer les décisions stratégiques issues du Comité.",
    ],
    'VICE_PRESIDENT': [
        "Assister le Président et le remplacer en cas d'absence.",
        "Suivre l'exécution des décisions du Bureau.",
        "Coordonner les collèges du Comité de Pilotage.",
    ],
    'SECRETARY': [
        "Rédiger les convocations et procès-verbaux des réunions du Comité.",
        "Assurer le suivi administratif des décisions prises.",
        "Tenir à jour le registre des membres et des résolutions.",
    ],
    'RAPPORTEUR': [
        "Synthétiser les travaux et décisions du Comité de Pilotage.",
        "Produire les rapports d'activité périodiques.",
        "Présenter le bilan stratégique aux instances de tutelle.",
    ],
    'CONSEILLER_POLITIQUE': [
        "Assurer la liaison entre le CNETP et les institutions publiques/ministérielles.",
        "Alerter le Bureau sur les enjeux politiques et réglementaires.",
        "Faciliter l'adoption des normes auprès des autorités.",
    ],
    'ADMIN_TECH_FIN': [
        "Superviser la gestion technique et financière des projets normatifs.",
        "Valider les budgets et indemnités liés aux travaux des CTM/WG.",
        "Produire des rapports de suivi budgétaire.",
    ],
    'PARTENAIRE_SOC_CIV': [
        "Recueillir les avis des parties prenantes sectorielles et de la société civile.",
        "Relayer les préoccupations du secteur lors des enquêtes publiques.",
        "Contribuer à la légitimité sociale des normes adoptées.",
    ],
    'CONSEILLER': [
        "Participer aux réunions stratégiques du Comité de Pilotage.",
        "Apporter votre expertise sur les dossiers soumis.",
        "Contribuer aux décisions collégiales du Comité.",
    ],
}

CTC_DUTIES = {
    'COORDINATOR': [
        "Organiser et superviser le toilettage légistique des normes transmises par les CTM.",
        "Répartir les dossiers entre les membres de la Cellule.",
        "Valider officiellement les normes avant l'enquête publique.",
    ],
    'VICE_COORDINATOR': [
        "Suppléer le Coordonnateur en son absence.",
        "Superviser le suivi des dossiers en cours de toilettage.",
    ],
    'ISO_EXPERT': [
        "Vérifier la cohérence des normes avec les référentiels ISO/ARSO.",
        "Signaler les écarts normatifs internationaux et proposer les harmonisations nécessaires.",
    ],
    'LEGAL': [
        "Assurer le toilettage légistique (forme et structure juridique) des normes.",
        "Vérifier la conformité réglementaire avant transmission au Comité de Pilotage.",
        "Rédiger les avis juridiques nécessaires.",
    ],
    'ENVIRONMENTAL': [
        "Évaluer l'impact environnemental des normes proposées.",
        "Émettre des recommandations sur les aspects environnementaux.",
    ],
    'PLANNER': [
        "Établir le calendrier des travaux de toilettage et d'enquête publique.",
        "Suivre les délais réglementaires.",
    ],
    'ECONOMIST': [
        "Analyser l'impact économique des normes.",
        "Évaluer les coûts de mise en conformité pour les opérateurs.",
    ],
    'SCIENTIFIC': [
        "Apporter un avis scientifique et technique sur les dossiers de normes.",
        "Valider la rigueur méthodologique des travaux des CTM.",
    ],
    'ACCOUNTANT': [
        "Assurer le suivi comptable des indemnités et cotisations liées aux travaux normatifs.",
        "Produire les états financiers de la Cellule.",
    ],
    'ENQUIRY_MANAGER': [
        "Organiser et superviser les enquêtes publiques sur les projets de normes.",
        "Consolider les avis du public et des parties prenantes.",
    ],
    'INDUSTRIAL': [
        "Recueillir les avis des opérateurs industriels concernés par les normes.",
        "Faciliter le dialogue entre la CTC et le secteur privé.",
    ],
    'COMMUNICATOR': [
        "Diffuser les informations relatives aux normes en cours d'examen.",
        "Assurer la communication institutionnelle du CNETP.",
    ],
    'EXECUTIVE': [
        "Assurer le secrétariat administratif de la Cellule.",
        "Organiser les réunions et assurer le suivi du courrier.",
    ],
    'CARTOGRAPHER': [
        "Produire les supports cartographiques nécessaires aux normes techniques concernées.",
        "Assurer la mise à jour des données géospatiales.",
    ],
    'DATA_ENTRY': [
        "Assurer la saisie et la mise à jour des données dans la plateforme.",
        "Vérifier l'exactitude des informations enregistrées.",
    ],
    'IT_ADMIN': [
        "Assurer le bon fonctionnement technique de la plateforme CNETP.",
        "Gérer les accès et la sécurité informatique de la plateforme.",
    ],
}

EXECUTIVE_DUTIES = {
    'MINISTER': [
        "Valider les orientations stratégiques transmises par le Comité de Pilotage.",
        "Homologuer les normes adoptées au Journal Officiel.",
    ],
    'SG_ITP': [
        "Assurer le suivi administratif des dossiers transmis par le Comité de Pilotage.",
        "Faire le lien entre le CNETP et le Cabinet du Ministre.",
    ],
    'CABINET': [
        "Préparer les dossiers soumis à la signature du Ministre.",
        "Assurer la coordination entre le Cabinet et le CNETP.",
    ],
}

CTM_ROLE_DUTIES = {
    'Président scientifique CTM': [
        "Superviser la cohérence technique des normes élaborées par les WG de votre CTM.",
        "Valider les votes de majorité avant transmission au Comité de Pilotage.",
        "Représenter le CTM lors des réunions inter-comités.",
    ],
    'Rapporteur CTM': [
        "Rédiger les comptes-rendus des réunions du CTM.",
        "Synthétiser les résultats des votes et les transmettre à la coordination.",
    ],
    'Secrétaire CTM': [
        "Organiser les convocations et la logistique des réunions du CTM.",
        "Tenir à jour les dossiers administratifs du Comité.",
    ],
    'Membre CTM': [
        "Participer aux réunions de votre Comité Technique Miroir (CTM).",
        "Examiner et voter les normes soumises par les groupes de travail (WG).",
        "Veiller à la cohérence inter-WG des normes.",
    ],
}

WG_ROLE_DUTIES = {
    'Président WG': [
        "Organiser et diriger les séances de rédaction de la norme.",
        "Soumettre la norme au vote des membres du WG dès qu'elle est prête.",
        "Transmettre les résultats du vote au CTM.",
    ],
    'Rapporteur WG': [
        "Documenter l'avancement des travaux de rédaction.",
        "Rédiger les versions successives de la norme.",
    ],
    'Secrétaire WG': [
        "Assurer le suivi administratif et logistique du groupe de travail.",
    ],
    'Membre WG': [
        "Contribuer activement à la rédaction de la norme assignée à votre WG.",
        "Voter sur le contenu (Pour / Contre / Abstention) pour faire progresser le dossier vers le CTM.",
    ],
}

GENERIC_DUTIES = [
    "Compléter votre profil expert sur la plateforme.",
    "Consulter régulièrement vos affectations (CTM/WG) sur le portail.",
]


class Command(BaseCommand):
    help = (
        "Envoie à chaque expert enregistré sur la plateforme un message (notification + email) "
        "détaillant ce qu'il doit faire selon le ou les postes qu'il occupe."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="N'envoie rien, affiche uniquement le contenu qui serait envoyé à chaque expert.",
        )
        parser.add_argument(
            '--expert-id',
            type=int,
            default=None,
            help="Limiter l'envoi à un seul expert (utile pour tester avant un envoi massif).",
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        expert_id = options['expert_id']

        experts = Expert.objects.select_related('user').exclude(user__email='')
        if expert_id:
            experts = experts.filter(id=expert_id)
            if not experts.exists():
                raise CommandError(f"Aucun expert trouvé avec l'id {expert_id}.")

        sent, skipped = 0, 0
        mode = "[DRY-RUN] " if dry_run else ""

        for expert in experts:
            if not expert.user.email:
                skipped += 1
                continue

            role_blocks = self._gather_role_blocks(expert)
            title, body = self._compose_message(expert, role_blocks)

            self.stdout.write(f"{mode}→ {expert.full_name} <{expert.user.email}> : {title}")

            if dry_run:
                self.stdout.write(body + "\n" + ("-" * 60))
                continue

            notification = Notification.objects.create(
                user=expert.user,
                title=title,
                body=body,
                notification_type='SYSTEM',
                priority='HIGH',
                data={
                    'role_blocks': [
                        {'label': label, 'duties': duties} for label, duties in role_blocks
                    ],
                    'dev_contact': DEV_CONTACT,
                },
            )
            dispatch_notification(notification.id)
            sent += 1

        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"\n[DRY-RUN] {experts.count()} expert(s) examiné(s), aucun message envoyé."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\n✅ {sent} message(s) envoyé(s), {skipped} expert(s) ignoré(s) (pas d'email)."
            ))

    def _gather_role_blocks(self, expert):
        """Construit la liste (label, taches) de tous les postes occupes par l'expert."""
        blocks = []

        executive_position = getattr(expert, 'executive_position', None)
        if executive_position:
            blocks.append((
                executive_position.get_position_display(),
                EXECUTIVE_DUTIES.get(executive_position.position, GENERIC_DUTIES),
            ))

        for membership in PilotageMembreship.objects.filter(expert=expert).select_related('comite'):
            blocks.append((
                f"{membership.get_role_display()} — {membership.comite.name}",
                PILOTAGE_DUTIES.get(membership.role, GENERIC_DUTIES),
            ))

        for membership in CTCMembership.objects.filter(expert=expert).select_related('ctc'):
            blocks.append((
                f"{membership.get_role_display()} — {membership.ctc.name}",
                CTC_DUTIES.get(membership.role, GENERIC_DUTIES),
            ))

        for affectation in Affectation.objects.filter(expert=expert).select_related('ctm', 'wg'):
            if affectation.ctm_role:
                blocks.append((
                    f"{affectation.ctm_role} — CTM {affectation.ctm.number} ({affectation.ctm.name})",
                    CTM_ROLE_DUTIES.get(affectation.ctm_role, GENERIC_DUTIES),
                ))
            if affectation.wg_role:
                blocks.append((
                    f"{affectation.wg_role} — {affectation.wg.name}",
                    WG_ROLE_DUTIES.get(affectation.wg_role, GENERIC_DUTIES),
                ))

        if not blocks:
            blocks.append(("Expert enregistré", GENERIC_DUTIES))

        return blocks

    def _compose_message(self, expert, role_blocks):
        title = "Vos responsabilités sur la Plateforme CNETP"

        lines = [
            f"Bonjour {expert.full_name},",
            "",
            "Dans le cadre de votre engagement au sein du CNETP, voici le récapitulatif de ce que vous "
            "devez faire selon le(s) poste(s) qui vous ont été confiés :",
            "",
        ]
        for label, duties in role_blocks:
            lines.append(f"▸ {label}")
            for duty in duties:
                lines.append(f"   • {duty}")
            lines.append("")

        lines += [
            "Merci de vous connecter régulièrement à la plateforme pour suivre vos dossiers, voter sur "
            "les normes en cours et participer aux réunions de votre comité.",
            "",
            f"Pour toute question technique sur la plateforme, contactez le développeur au {DEV_CONTACT}.",
            "",
            "Cordialement,",
            "L'équipe CNETP",
        ]

        return title, "\n".join(lines)

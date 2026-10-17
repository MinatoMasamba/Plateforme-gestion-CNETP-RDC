"""Envoie aux experts le communiqué HTML + texte + PDF de transition."""

from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.experts.models import Expert
from apps.messaging.communiques import build_context, expert_email, send_to_expert
from apps.messaging.models import CommuniqueOfficiel, CommuniqueSequence

OBJET = "Transition vers la nouvelle organisation de la CNE-ITP"


def default_pdf_path(numero_label):
    return (
        Path(__file__).resolve().parents[2]
        / 'data' / 'communiques' / f'communique_{numero_label}.pdf'
    )


class Command(BaseCommand):
    help = (
        "Envoie le communiqué de transition organisationnelle aux experts : "
        "HTML, version texte et PDF officiel joint. Le numéro est auto-incrémenté "
        "et la date du communiqué est saisissable."
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help="Affiche les destinataires sans envoyer.")
        parser.add_argument('--statut', default='ACTIVE', help="Statut des experts (défaut : ACTIVE).")
        parser.add_argument('--email', action='append', default=[], help="Limiter à une ou plusieurs adresses email.")
        parser.add_argument('--limit', type=int, default=0, help="Limiter le nombre d'envois.")
        parser.add_argument('--skip', type=int, default=0, help="Ignorer les N premiers destinataires.")
        parser.add_argument('--force', action='store_true', help="Renvoyer même si un envoi réussi existe.")
        parser.add_argument('--key', default='', help="Clé de suivi (défaut : communique:<numéro>).")
        parser.add_argument(
            '--date', default='',
            help="Date officielle du communiqué AAAA-MM-JJ (défaut : aujourd'hui).",
        )
        parser.add_argument(
            '--new', action='store_true',
            help="Créer un nouveau communiqué même si un communiqué existe déjà à cette date.",
        )
        parser.add_argument(
            '--communique-id', type=int, default=0,
            help="Réutiliser un communiqué existant par son identifiant.",
        )
        parser.add_argument(
            '--pdf', default='',
            help="PDF original à joindre (défaut : apps/messaging/data/communiques/communique_<numéro>.pdf).",
        )
        parser.add_argument(
            '--base-url', default='',
            help="URL publique à utiliser dans l'email (défaut : settings.SITE_URL).",
        )

    def _select_communique(self, options, dry_run=False):
        if options['communique_id']:
            communique = CommuniqueOfficiel.objects.filter(pk=options['communique_id']).first()
            if not communique:
                raise CommandError("Communiqué introuvable.")
            return communique

        date_value = parse_date(options['date']) if options['date'] else timezone.localdate()
        if not date_value:
            raise CommandError("Date invalide : utilisez le format AAAA-MM-JJ.")
        if not options['new']:
            communique = (
                CommuniqueOfficiel.objects.filter(date_communique=date_value)
                .order_by('-numero').first()
            )
            if communique:
                return communique
        if dry_run:
            preview = CommuniqueOfficiel(date_communique=date_value, objet=OBJET)
            preview.numero = CommuniqueSequence.peek_next_number()
            return preview
        return CommuniqueOfficiel.objects.create(
            date_communique=date_value,
            objet=OBJET,
        )

    def handle(self, *args, **options):
        communique = self._select_communique(options, dry_run=options['dry_run'])
        context = build_context(
            numero=communique.numero_label,
            date_communique=communique.date_communique,
            base_url=options.get('base_url') or None,
        )
        key = options['key'] or f"communique:{communique.numero_label}:{context['version_code']}"

        experts = (
            Expert.objects.select_related('user', 'structure')
            .filter(status=options['statut'])
            .order_by('user__last_name', 'user__first_name')
        )
        if options['email']:
            experts = experts.filter(user__email__in=options['email'])
        experts = list(experts)
        if options['skip']:
            experts = experts[options['skip']:]
        if options['limit']:
            experts = experts[:options['limit']]

        if not experts:
            raise CommandError("Aucun destinataire ne correspond aux critères.")

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Communiqué N° {communique.numero_label} du "
            f"{communique.date_communique:%d/%m/%Y} — version {context['version_code']} "
            f"({context['sc_count']} SC, {context['gt_count']} GT)"
        ))
        self.stdout.write(f"Sujet : {context['subject']}")
        self.stdout.write(f"Lien plateforme : {context['platform_url']}")
        self.stdout.write(f"Clé de suivi : {key}")
        self.stdout.write(f"Destinataires : {len(experts)}")

        pdf_bytes = None
        pdf_filename = None
        if options['dry_run']:
            if communique.fichier_pdf:
                self.stdout.write(f"PDF original : {communique.fichier_pdf.name}")
            else:
                candidate = Path(options['pdf']) if options['pdf'] else default_pdf_path(communique.numero_label)
                if not candidate.is_file():
                    raise CommandError(
                        f"PDF original introuvable : {candidate}. "
                        "Fournissez --pdf ou déposez le fichier dans apps/messaging/data/communiques/."
                    )
                self.stdout.write(f"PDF original : {candidate}")

        if options['dry_run']:
            for expert in experts:
                self.stdout.write(
                    f"  - {expert.full_name or expert.user.username} <{expert_email(expert) or 'sans email'}>"
                )
            self.stdout.write(self.style.WARNING("Dry-run : aucun email envoyé."))
            return

        if options['pdf']:
            source = Path(options['pdf'])
            if not source.is_file():
                raise CommandError(f"PDF original introuvable : {source}")
            with source.open('rb') as handle:
                communique.fichier_pdf.save(f'communique_{communique.numero_label}.pdf', File(handle), save=True)
        elif not communique.fichier_pdf:
            source = default_pdf_path(communique.numero_label)
            if not source.is_file():
                raise CommandError(
                    f"PDF original introuvable : {source}. "
                    "Fournissez --pdf ou déposez le fichier dans apps/messaging/data/communiques/."
                )
            with source.open('rb') as handle:
                communique.fichier_pdf.save(source.name, File(handle), save=True)

        with communique.fichier_pdf.open('rb') as handle:
            pdf_bytes = handle.read()
        pdf_filename = Path(communique.fichier_pdf.name).name
        self.stdout.write(f"PDF joint : {pdf_filename} ({len(pdf_bytes)} octets)")

        sent = skipped = failed = 0
        for expert in experts:
            try:
                result = send_to_expert(
                    expert, key, context, force=options['force'],
                    pdf_bytes=pdf_bytes, pdf_filename=pdf_filename,
                )
            except Exception as exc:
                failed += 1
                self.stderr.write(self.style.ERROR(
                    f"  ✗ {expert.full_name or expert.user.username} : {exc}"
                ))
                continue
            if result['status'] == 'sent':
                sent += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ {expert.full_name or expert.user.username}"))
            else:
                skipped += 1
                self.stdout.write(
                    f"  = {expert.full_name or expert.user.username} : {result.get('reason', 'ignoré')}"
                )

        if sent and not failed:
            communique.statut = CommuniqueOfficiel.STATUS_SENT
            communique.save(update_fields=['statut', 'updated_at'])
        elif sent:
            communique.statut = CommuniqueOfficiel.STATUS_SENT
            communique.save(update_fields=['statut', 'updated_at'])

        self.stdout.write(self.style.SUCCESS(
            f"Terminé : {sent} envoyé(s), {skipped} ignoré(s), {failed} échec(s)."
        ))

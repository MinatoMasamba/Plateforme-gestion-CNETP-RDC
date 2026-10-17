"""Envoie aux experts le communiqué HTML + texte + PDF de transition."""

from django.core.management.base import BaseCommand, CommandError

from apps.experts.models import Expert
from apps.messaging.communiques import (
    SUBJECT,
    build_context,
    expert_email,
    send_to_expert,
)


class Command(BaseCommand):
    help = (
        "Envoie le communiqué de transition organisationnelle aux experts : "
        "HTML, version texte et PDF officiel joint."
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help="Affiche les destinataires sans envoyer.")
        parser.add_argument('--statut', default='ACTIVE', help="Statut des experts (défaut : ACTIVE).")
        parser.add_argument('--email', action='append', default=[], help="Limiter à une ou plusieurs adresses email.")
        parser.add_argument('--limit', type=int, default=0, help="Limiter le nombre d'envois.")
        parser.add_argument('--skip', type=int, default=0, help="Ignorer les N premiers destinataires.")
        parser.add_argument('--force', action='store_true', help="Renvoyer même si un envoi réussi existe.")
        parser.add_argument('--key', default='', help="Clé de suivi (défaut : organisation:<code version>).")

    def handle(self, *args, **options):
        context = build_context()
        key = options['key'] or f"organisation:{context['version_code']}"

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
            f"Communiqué organisation — version {context['version_code']} "
            f"({context['sc_count']} SC, {context['gt_count']} GT)"
        ))
        self.stdout.write(f"Sujet : {SUBJECT}")
        self.stdout.write(f"Clé de suivi : {key}")
        self.stdout.write(f"Destinataires : {len(experts)}")

        if options['dry_run']:
            for expert in experts:
                self.stdout.write(
                    f"  - {expert.full_name or expert.user.username} <{expert_email(expert) or 'sans email'}>"
                )
            self.stdout.write(self.style.WARNING("Dry-run : aucun email envoyé."))
            return

        sent = skipped = failed = 0
        for expert in experts:
            try:
                result = send_to_expert(expert, key, context, force=options['force'])
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

        self.stdout.write(self.style.SUCCESS(
            f"Terminé : {sent} envoyé(s), {skipped} ignoré(s), {failed} échec(s)."
        ))

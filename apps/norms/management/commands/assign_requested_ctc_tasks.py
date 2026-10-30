"""Répartit le travail préparatoire CTC entre les membres existants de la base."""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import AuditLog
from apps.governance.models import CTCMembership, PosteNominatifCTC, RattachementDocumentaire, Tache
from apps.norms.models import Norme


ROLE_PLAN = {
    'COORDINATOR': ('003', '004', '104', '401'),
    'EXECUTIVE': ('003', '104', '302', '603'),
    'ISO_EXPERT': ('003', '004', '104', '105', '204', '302', '603'),
    'LEGAL': ('004', '105', '204', '302', '401'),
    'ENVIRONMENTAL': ('104', '105', '204', '302', '401'),
    'PLANNER': ('104', '105', '302', '603'),
    'ECONOMIST': ('104', '105', '204', '302'),
    'SCIENTIFIC': ('003', '004', '104', '204', '302'),
    'INDUSTRIAL': ('104', '105', '302', '401'),
    'COMMUNICATOR': ('003', '603'),
    'CARTOGRAPHER': ('104', '105', '204', '401'),
    'DATA_ENTRY': ('003', '104', '302'),
    'IT_ADMIN': ('004',),
}
ROLE_ACTION = {
    'COORDINATOR': 'Vérifier le cadrage et déterminer la prochaine étape',
    'EXECUTIVE': 'Contrôler le bordereau et les pièces reçues',
    'ISO_EXPERT': 'Vérifier les références normatives et leurs éditions',
    'LEGAL': 'Identifier les dispositions nécessitant un examen juridique',
    'ENVIRONMENTAL': 'Identifier les impacts et justificatifs à examiner',
    'PLANNER': 'Établir les jalons et dépendances du traitement',
    'ECONOMIST': 'Documenter les hypothèses de coût et leur source',
    'SCIENTIFIC': 'Vérifier les méthodes, hypothèses et résultats',
    'INDUSTRIAL': 'Préparer la liste des acteurs à consulter',
    'COMMUNICATOR': 'Préparer la note d’information interne',
    'CARTOGRAPHER': 'Contrôler la présence et la provenance des plans',
    'DATA_ENTRY': 'Indexer les pièces et relever les documents manquants',
    'IT_ADMIN': 'Vérifier les accès techniques au dossier',
}


class Command(BaseCommand):
    help = 'Crée 52 tâches CTC préparatoires pour les membres existants, sans créer de compte.'

    def handle(self, *args, **options):
        db = Path(str(settings.DATABASES['default']['NAME'])).resolve()
        if db != (Path(settings.BASE_DIR) / 'db.sqlite3').resolve():
            raise CommandError('La commande doit utiliser db.sqlite3 à la racine.')
        if sum(map(len, ROLE_PLAN.values())) != 52:
            raise CommandError('Le plan doit contenir exactement 52 tâches.')
        created = []
        with transaction.atomic():
            for role, codes in ROLE_PLAN.items():
                members = list(CTCMembership.objects.filter(
                    role=role, expert__status='ACTIVE', expert__user__is_active=True
                ).select_related('expert__user').order_by('pk'))
                if not members:
                    raise CommandError(f'Aucun membre CTC actif pour {role}.')
                nominated = set(PosteNominatifCTC.objects.filter(
                    role=role, holder__isnull=False
                ).values_list('holder_id', flat=True))
                pool = [member for member in members if member.expert_id in nominated] or members
                for index, code in enumerate(codes):
                    ref = f'NCD {code}'
                    norm = Norme.all_objects.get(reference_number=ref, circuit_version='LEGACY')
                    binding = RattachementDocumentaire.objects.get(norme=norm, role='OWNER', status='PROPOSED')
                    actor = pool[index % len(pool)].expert
                    title = f'{ROLE_ACTION[role]} — {ref}'
                    task, was_created = Tache.objects.get_or_create(
                        norme=norm, target_sc=binding.sc, titre=title,
                        defaults={
                            'description': f'Rôle CTC : {role}. Travail préparatoire sur « {norm.title} ». '
                                           'Consigner les sources, les pièces manquantes et la suite à proposer après examen par la sous-commission. '
                                           'Aucune validation ni transmission n’est présumée.',
                            'assigned_to': actor,
                            'status': 'ON_HOLD' if binding.sc.status == 'PROPOSED' else 'PLANNED',
                            'priority': 'NORMAL', 'progress': 0,
                        },
                    )
                    if was_created:
                        AuditLog.objects.create(user=None, action='CREATE', content_type='Tache',
                            object_id=task.pk, object_repr=title,
                            changes={'role_ctc': role, 'assigned_to': actor.user.username,
                                     'norme': ref, 'status': task.status,
                                     'source': 'Répartition demandée le 28/10/2026'})
                        created.append((role, ref, actor.user.username))
        self.stdout.write(f'{len(created)} tâches CTC créées et affectées aux comptes existants.')

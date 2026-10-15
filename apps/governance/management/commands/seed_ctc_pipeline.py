"""Peuple le pipeline CTC (dossiers normatifs) et disperse les statuts.

La vue « Dossiers Normatifs » du CTC (`templates/ctc/app/components/dossiers_view.html`)
itère sur les `CTCProcessus`. Sans eux, le CTC affiche « Aucun dossier normatif ».

Cette commande (idempotente) :
  * crée un `CTCProcessus` pour chaque norme avec une étape répartie
    (RECEPTION → GEOSPATIAL → MULTI_REVIEW → INDUSTRIAL → SIGNED_OUT) ;
  * aligne le statut de la norme sur l'étape (INTERNAL_REVIEW, CTM_REVIEW,
    PILOTAGE_REVIEW, …) ;
  * marque 2 normes comme PUBLISHED (pour le « fini / publié ») ;
  * crée des examens analytiques (toilettage, ISO, écologie, économique,
    chronogramme, FEC) en attente, afin que les rôles analystes voient des tâches.

Usage :
    python manage.py seed_ctc_pipeline
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.governance.models import CTCProcessus
from apps.norms.models import Norme
from apps.validation.models import (
    EconomicReview,
    EcologicalReview,
    ISOReview,
    IndustrialConsultation,
    LegisticReview,
    ScheduleReview,
)

STAGES = ['RECEPTION', 'GEOSPATIAL', 'MULTI_REVIEW', 'INDUSTRIAL', 'SIGNED_OUT']

STAGE_TO_STATUS = {
    'RECEPTION': 'INTERNAL_REVIEW',
    'GEOSPATIAL': 'INTERNAL_REVIEW',
    'MULTI_REVIEW': 'INTERNAL_REVIEW',
    'INDUSTRIAL': 'CTM_REVIEW',
    'SIGNED_OUT': 'PILOTAGE_REVIEW',
}


class Command(BaseCommand):
    help = "Crée le pipeline CTC (CTCProcessus) et disperse les statuts des normes."

    def handle(self, *args, **options):
        normes = list(Norme.objects.select_related('ctm', 'wg').order_by('id'))
        if not normes:
            self.stdout.write(self.style.WARNING(
                "Aucune norme en base. Lancez d'abord `python manage.py seed_e2e`."))
            return

        created = 0
        for index, norme in enumerate(normes):
            stage = STAGES[index % len(STAGES)]
            processus, was_created = CTCProcessus.objects.get_or_create(
                norme=norme, defaults={'current_stage': stage})
            if was_created:
                created += 1
            # Aligner le statut macro de la norme sur l'étape (si encore brouillon)
            if norme.status in ('DRAFT', 'INTERNAL_REVIEW', 'CTM_REVIEW', 'PILOTAGE_REVIEW'):
                new_status = STAGE_TO_STATUS.get(stage)
                if new_status and norme.status != new_status:
                    norme.status = new_status
                    norme.save(update_fields=['status', 'updated_at'])

        # 2 normes terminées / publiées (statut « fini »)
        for norme in normes[:2]:
            norme.status = 'PUBLISHED'
            norme.publication_date = date.today() - timedelta(days=10)
            norme.jo_reference = f'JO-{norme.reference_number}'
            norme.is_public = True
            norme.save(update_fields=['status', 'publication_date', 'jo_reference',
                                      'is_public', 'updated_at'])

        # Examens analytiques en attente (visibles par les rôles analystes CTC)
        review_created = 0
        review_models = [ISOReview, LegisticReview, EcologicalReview,
                         EconomicReview, ScheduleReview, IndustrialConsultation]
        for index, norme in enumerate(normes):
            model = review_models[index % len(review_models)]
            defaults = {'status': 'PENDING'}
            if model is ScheduleReview:
                defaults = {'planner_status': 'PENDING', 'scientist_status': 'PENDING'}
            _, was_created = model.objects.get_or_create(norme=norme, defaults=defaults)
            review_created += int(was_created)

        self.stdout.write(self.style.SUCCESS(
            f"Pipeline CTC : {created} nouveau(x) dossier(s) pour {len(normes)} norme(s). "
            f"{review_created} examen(s) analytique(s) en attente. 2 normes publiées."
        ))

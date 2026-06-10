from django.contrib import admin
from .models import (
    LegisticReview, ISOReview, EcologicalReview,
    EconomicReview, ScheduleReview, IndustrialConsultation,
)


@admin.register(LegisticReview)
class LegisticReviewAdmin(admin.ModelAdmin):
    list_display = ('norme', 'legist', 'status', 'review_start_date', 'review_end_date')
    list_filter = ('status',)
    search_fields = ('norme__reference_number', 'norme__title')
    raw_id_fields = ('legist',)


@admin.register(ISOReview)
class ISOReviewAdmin(admin.ModelAdmin):
    list_display = ('norme', 'expert', 'status', 'iso_references', 'review_start_date')
    list_filter = ('status',)
    search_fields = ('norme__reference_number',)
    raw_id_fields = ('expert',)


@admin.register(EcologicalReview)
class EcologicalReviewAdmin(admin.ModelAdmin):
    list_display = ('norme', 'expert', 'status', 'review_start_date')
    list_filter = ('status',)
    search_fields = ('norme__reference_number',)
    raw_id_fields = ('expert',)


@admin.register(EconomicReview)
class EconomicReviewAdmin(admin.ModelAdmin):
    list_display = ('norme', 'expert', 'status', 'lifecycle_cost_usd', 'review_start_date')
    list_filter = ('status',)
    search_fields = ('norme__reference_number',)
    raw_id_fields = ('expert',)


@admin.register(ScheduleReview)
class ScheduleReviewAdmin(admin.ModelAdmin):
    list_display = ('norme', 'planner', 'scientist', 'planner_status', 'scientist_status', 'completed')
    list_filter = ('planner_status', 'scientist_status')
    search_fields = ('norme__reference_number',)
    raw_id_fields = ('planner', 'scientist')

    def completed(self, obj):
        return obj.is_completed
    completed.boolean = True
    completed.short_description = "Terminé"


@admin.register(IndustrialConsultation)
class IndustrialConsultationAdmin(admin.ModelAdmin):
    list_display = ('norme', 'expert', 'status', 'market_feasible', 'review_start_date')
    list_filter = ('status', 'market_feasible')
    search_fields = ('norme__reference_number',)
    raw_id_fields = ('expert',)

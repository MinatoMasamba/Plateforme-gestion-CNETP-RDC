from datetime import date

from django.db import migrations, models


BATCH_REFERENCE = 'RAPPORT-ADOPTE-2026-10-15'
EFFECTIVE_DATE = date(2026, 10, 15)


def confirm_report_assignments(apps, schema_editor):
    AffectationSousCommission = apps.get_model('governance', 'AffectationSousCommission')
    assignments = AffectationSousCommission.objects.filter(
        source_kind='REPORT_PROPOSAL',
        status='REVIEW',
        sc__isnull=False,
    ).order_by('expert_id', 'sc__code', 'pk')
    primary_experts = set()
    for assignment in assignments:
        already_primary = AffectationSousCommission.objects.filter(
            version_id=assignment.version_id,
            expert_id=assignment.expert_id,
            status='MIGRATED',
            is_primary=True,
        ).exclude(pk=assignment.pk).exists()
        assignment.status = 'MIGRATED'
        assignment.effective_from = assignment.effective_from or EFFECTIVE_DATE
        assignment.is_primary = not already_primary and assignment.expert_id not in primary_experts
        if assignment.is_primary:
            primary_experts.add(assignment.expert_id)
        fields = ['status', 'effective_from', 'is_primary']
        rationale = assignment.rationale or ''
        if 'examiner' in rationale.lower():
            assignment.rationale = rationale.replace(
                'Proposition nominative', 'Affectation directe',
            ).replace(
                'à examiner sans effet sur les droits', 'sans mandat ni habilitation',
            )
            fields.append('rationale')
        assignment.save(update_fields=fields)


def unconfirm_report_assignments(apps, schema_editor):
    AffectationSousCommission = apps.get_model('governance', 'AffectationSousCommission')
    AffectationSousCommission.objects.filter(
        source_kind='REPORT_PROPOSAL',
        batch_reference=BATCH_REFERENCE,
        status='MIGRATED',
    ).update(status='REVIEW', effective_from=None, is_primary=False)


class Migration(migrations.Migration):

    dependencies = [
        ('governance', '0030_consultationconseiller'),
    ]

    operations = [
        migrations.AlterField(
            model_name='affectationsouscommission',
            name='status',
            field=models.CharField(
                choices=[
                    ('MIGRATED', 'Affecté'),
                    ('REVIEW', 'À examiner'),
                    ('ENDED', 'Terminé'),
                    ('CANCELLED', 'Annulé'),
                ],
                default='REVIEW',
                max_length=20,
            ),
        ),
        migrations.RunPython(confirm_report_assignments, unconfirm_report_assignments),
    ]

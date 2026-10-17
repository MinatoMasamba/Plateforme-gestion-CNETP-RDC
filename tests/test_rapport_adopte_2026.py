import pytest
from django.core.management import call_command

from apps.governance.models import (
    GroupeCible, HabilitationAction, JournalMigration, MandatOrganisation,
    Organe, PosteOrganisation,
)
from apps.governance.rapport_adopte_2026 import prepare_adopted_organisation


@pytest.mark.django_db
def test_adopted_report_catalogue_is_complete_idempotent_and_grants_no_rights():
    version, counts = prepare_adopted_organisation()
    assert version.status == 'PROPOSED'
    assert counts == {
        'copil_posts': 22, 'st_posts': 24, 'sc': 7,
        'gt': 35, 'sc_bureau_posts': 30,
    }
    assert list(Organe.objects.filter(version=version, type='SC').values_list('composition__tome', flat=True).order_by('composition__tome')) == list(range(7))
    assert all(GroupeCible.objects.filter(sc=sc).count() == 5 for sc in Organe.objects.filter(version=version, type='SC'))
    assert not GroupeCible.objects.filter(sc__version=version, mission='').exists()
    assert MandatOrganisation.objects.count() == 0
    assert HabilitationAction.objects.count() == 0
    journal_count = JournalMigration.objects.filter(version=version).count()
    _, repeated_counts = prepare_adopted_organisation()
    assert repeated_counts == counts
    assert PosteOrganisation.objects.filter(organe__version=version).count() == 76
    assert JournalMigration.objects.filter(version=version).count() == journal_count


@pytest.mark.django_db
def test_confirmed_report_holder_is_placed_on_post_without_habilitation(user_factory, expert_factory):
    version, _ = prepare_adopted_organisation()
    expert = expert_factory(user=user_factory(
        username='joseph.bamenikio', email='joseph@example.cd',
        first_name='Joseph', last_name='BAMENIKIO',
    ))
    options = {'decision_reference': 'Confirmation test', 'effective_date': '2026-10-17'}
    call_command('affecter_bureaux_sc_rapport', **options)
    mandate = MandatOrganisation.objects.get(poste__code='SC-BAT-BUREAU-01')
    assert mandate.expert == expert
    assert mandate.status == 'ACTIVE'
    assert mandate.function == 'Président'
    assert mandate.appointment_reference == options['decision_reference']
    assert not HabilitationAction.objects.exists()
    assert version.status == 'PROPOSED'
    call_command('affecter_bureaux_sc_rapport', **options)
    assert MandatOrganisation.objects.count() == 1
    assert JournalMigration.objects.filter(version=version, operation='AFFECT_SC_BUREAUX').count() == 1

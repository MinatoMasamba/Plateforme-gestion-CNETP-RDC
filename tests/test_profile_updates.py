from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.models import User
from apps.experts.models import Expert, ProfileUpdate, ProfileUpdateEvent, Structure
from apps.experts.profile_updates import transition
from apps.governance.models import OrganisationVersion, Organe, GroupeCible, ChoixOrganisationExpert


class ProfileUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='profil-test', email='profil@example.org', password='secret', first_name='Ada', last_name='Test', phone='123')
        self.staff = User.objects.create_user(username='staff-test', password='secret', is_staff=True)
        self.structure = Structure.objects.create(name='Structure test', acronym='ST', category='ADMIN')
        self.expert = Expert.objects.create(user=self.user, structure=self.structure, status='ACTIVE', specialties='Géotechnique')
        self.version = OrganisationVersion.objects.create(code='profil-test', name='Organisation test', source_document='test')

    def test_legacy_active_expert_is_not_complete(self):
        self.assertFalse(ProfileUpdate.objects.filter(expert=self.expert).exists())
        self.assertEqual(transition(self.expert, 'IN_PROGRESS', self.user, version=self.version).status, 'IN_PROGRESS')
        with self.assertRaises(ValidationError):
            transition(self.expert, 'SUBMITTED', self.user)
        self.assertEqual(ProfileUpdateEvent.objects.filter(profile_update__expert=self.expert).count(), 1)

    def test_admin_cannot_certify_missing_profile(self):
        transition(self.expert, 'IN_PROGRESS', self.user, version=self.version)
        with self.assertRaises(ValidationError):
            transition(self.expert, 'COMPLETE', self.staff)
        self.assertEqual(self.expert.status, 'ACTIVE')

    def test_owner_cannot_open_administrative_review(self):
        transition(self.expert, 'IN_PROGRESS', self.user, version=self.version)
        with self.assertRaises(ValidationError):
            transition(self.expert, 'UNDER_REVIEW', self.user)

    def test_submission_and_verification_do_not_change_nomination_status(self):
        self.expert.cv = 'experts/cv/test.pdf'
        self.expert.save()
        sc = Organe.objects.create(version=self.version, code='SC-TEST', name='Test', type='SC', source_reference='test')
        gt = GroupeCible.objects.create(sc=sc, code='GT-TEST', name='Groupe', activity='PRODUCTION', source_reference='test')
        ChoixOrganisationExpert.objects.create(expert=self.expert, version=self.version, sc=sc, groupe=gt)
        transition(self.expert, 'IN_PROGRESS', self.user, version=self.version)
        transition(self.expert, 'SUBMITTED', self.user)
        transition(self.expert, 'UNDER_REVIEW', self.staff)
        state = transition(self.expert, 'COMPLETE', self.staff)
        self.assertEqual(state.validated_by, self.staff)
        self.assertIsNotNone(state.completed_at)
        self.assertEqual(self.expert.status, 'ACTIVE')
        self.assertEqual(state.events.count(), 4)

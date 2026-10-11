"""Smoke tests pour le module sidebar (précédemment non fonctionnel)."""
import pytest
from rest_framework.test import APIClient

from apps.experts.models import Expert, Structure
from apps.governance.models import CTM, WG, Affectation


@pytest.mark.django_db
class TestSidebarEndpoints:
    @pytest.fixture(autouse=True)
    def _setup(self, user_factory):
        self.user = user_factory(username='sidebar', email='sidebar@cnetp.cd')
        self.ctm = CTM.objects.create(number=1, name='CTM Sidebar', description='Test')
        self.wg = WG.objects.create(ctm=self.ctm, number=1, name='WG Sidebar')
        self.structure = Structure.objects.create(name='Structure Sidebar', acronym='SB', category='ADMIN')
        self.expert = Expert.objects.create(
            user=self.user, structure=self.structure, ctm=self.ctm, status='ACTIVE'
        )
        Affectation.objects.create(expert=self.expert, ctm=self.ctm, wg=self.wg)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_profile_me(self):
        resp = self.client.get('/api/v1/profile/me/')
        assert resp.status_code == 200
        assert resp.data['ctm'] == 'CTM Sidebar'
        assert resp.data['wg'] == 'WG Sidebar'
        assert resp.data['wgCode'] == 'WG 1.1'

    def test_profile_preferences_persists_theme(self):
        resp = self.client.patch('/api/v1/profile/preferences/', {'theme': 'dark'}, format='json')
        assert resp.status_code == 200
        self.expert.refresh_from_db()
        assert self.expert.theme_preference == 'dark'

    def test_working_groups_list(self):
        resp = self.client.get('/api/v1/working-groups/')
        assert resp.status_code == 200
        assert len(resp.data) == 1

    def test_sidebar_experts_list(self):
        resp = self.client.get('/api/v1/sidebar/experts/')
        assert resp.status_code == 200

    def test_sidebar_documents_list(self):
        resp = self.client.get('/api/v1/sidebar/documents/')
        assert resp.status_code == 200

    def test_sidebar_meetings_list(self):
        resp = self.client.get('/api/v1/sidebar/meetings/')
        assert resp.status_code == 200

    def test_sidebar_budgets_list(self):
        resp = self.client.get('/api/v1/sidebar/budgets/')
        assert resp.status_code == 200

    def test_dashboard_kpis(self):
        resp = self.client.get('/api/v1/dashboard/kpis/kpis/')
        assert resp.status_code == 200
        assert resp.data['total_ctm'] == 1

    def test_wg_tasks(self):
        resp = self.client.get(f'/api/v1/tasks/working-groups/{self.wg.id}/tasks/')
        assert resp.status_code == 200

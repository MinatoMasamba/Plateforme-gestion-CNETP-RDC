from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.governance.models import CTM, WG
from apps.ia_agent.models import AgentArtifact, AgentSession
from apps.ia_agent.tools.governance_tools import detect_inter_ctm_overlap, flag_inter_ctm_overlap
from apps.norms.models import Norme


class DetectInterCTMOverlapTests(TestCase):

    def setUp(self):
        self.ctm_geotech = CTM.objects.create(name="Géotechnique", number=1)
        self.ctm_ouvrages = CTM.objects.create(name="Ouvrages d'art", number=2)

        self.wg_a = WG.objects.create(ctm=self.ctm_geotech, number=1, name="Fondations profondes")
        self.wg_b = WG.objects.create(ctm=self.ctm_ouvrages, number=1, name="Dimensionnement des ponts")
        self.wg_c = WG.objects.create(ctm=self.ctm_ouvrages, number=2, name="Assainissement pluvial urbain")

        Norme.objects.create(
            title="Calcul de portance des fondations profondes en sol latéritique",
            reference_number="CNETP-TEST-001",
            description="Méthode de calcul de portance et tassement des fondations profondes",
            ctm=self.ctm_geotech, wg=self.wg_a,
        )
        Norme.objects.create(
            title="Dimensionnement des fondations profondes de ponts routiers",
            reference_number="CNETP-TEST-002",
            description="Critères de dimensionnement des fondations profondes pour ouvrages d'art",
            ctm=self.ctm_ouvrages, wg=self.wg_b,
        )
        Norme.objects.create(
            title="Réseaux d'assainissement pluvial en zone urbaine",
            reference_number="CNETP-TEST-003",
            description="Dimensionnement des collecteurs pluviaux urbains",
            ctm=self.ctm_ouvrages, wg=self.wg_c,
        )

    def test_detects_overlap_between_different_ctm(self):
        candidates = detect_inter_ctm_overlap(session=None)

        pairs = {(c["wg_a"]["id"], c["wg_b"]["id"]) for c in candidates}
        self.assertIn((self.wg_a.id, self.wg_b.id), pairs)

    def test_does_not_flag_unrelated_wg_across_ctm(self):
        candidates = detect_inter_ctm_overlap(session=None)

        pairs = {(c["wg_a"]["id"], c["wg_b"]["id"]) for c in candidates}
        self.assertNotIn((self.wg_a.id, self.wg_c.id), pairs)

    def test_never_compares_wg_within_the_same_ctm(self):
        candidates = detect_inter_ctm_overlap(session=None)

        for c in candidates:
            self.assertNotEqual(c["wg_a"]["ctm_id"], c["wg_b"]["ctm_id"])

    def test_flag_inter_ctm_overlap_creates_artifact_with_scope(self):
        user = get_user_model().objects.create_user(username="test-ctc", password="x")
        session = AgentSession.objects.create(user=user, scope='ctc', provider='gemini')

        result = flag_inter_ctm_overlap(
            session=session,
            wg_a_id=self.wg_a.id,
            wg_b_id=self.wg_b.id,
            analysis_text="Chevauchement détecté sur les fondations profondes.",
            recommendation="Aligner les deux CTM sur une méthode de calcul commune.",
        )

        artifact = AgentArtifact.objects.get(id=result["artifact_id"])
        self.assertEqual(artifact.artifact_type, 'NORM_OVERLAP')
        self.assertEqual(artifact.status, 'DRAFT')
        self.assertEqual(artifact.payload["scope"], "inter_ctm")
        self.assertEqual(artifact.payload["wg_a"]["ctm_number"], 1)
        self.assertEqual(artifact.payload["wg_b"]["ctm_number"], 2)

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.governance.models import CTM, WG
from apps.ia_agent.models import AgentArtifact, AgentSession
from apps.ia_agent.tools.public_inquiry_tools import synthesize_public_inquiry
from apps.norms.models import Norme
from apps.public.models import PublicAmendement


class SynthesizePublicInquiryTests(TestCase):

    def setUp(self):
        ctm = CTM.objects.create(name="Assainissement", number=7)
        wg = WG.objects.create(ctm=ctm, number=1, name="Réseaux pluviaux")
        self.norme = Norme.objects.create(
            title="Norme sur le drainage pluvial urbain",
            reference_number="CNETP-TEST-PI-001",
            description="Norme régissant le drainage et l'assainissement pluvial",
            ctm=ctm, wg=wg,
        )
        user = get_user_model().objects.create_user(username="test-pilotage", password="x")
        self.session = AgentSession.objects.create(user=user, scope='pilotage', provider='gemini')

        PublicAmendement.objects.create(
            norme=self.norme, proposed_by_name="Citoyen A", proposed_by_email="a@example.com",
            title="Ajouter un collecteur", description="Il faut renforcer le drainage pluvial du quartier.",
            status='PENDING',
        )
        PublicAmendement.objects.create(
            norme=self.norme, proposed_by_name="Citoyen B", proposed_by_email="b@example.com",
            title="Matériaux locaux", description="Utiliser des matériaux locaux comme la latérite pour les fondations.",
            status='ACCEPTED',
        )

    def test_persists_artifact_by_default(self):
        result = synthesize_public_inquiry(self.session, self.norme.id)

        self.assertIn("artifact_id", result)
        artifact = AgentArtifact.objects.get(id=result["artifact_id"])
        self.assertEqual(artifact.artifact_type, 'PUBLIC_INQUIRY_SYNTHESIS')
        self.assertEqual(artifact.status, 'DRAFT')
        self.assertEqual(artifact.object_id, self.norme.id)

    def test_persist_false_does_not_create_artifact(self):
        count_before = AgentArtifact.objects.count()
        result = synthesize_public_inquiry(self.session, self.norme.id, persist=False)

        self.assertNotIn("artifact_id", result)
        self.assertEqual(AgentArtifact.objects.count(), count_before)

    def test_groups_by_status_and_theme(self):
        result = synthesize_public_inquiry(self.session, self.norme.id, persist=False)

        self.assertEqual(result["total"], 2)
        self.assertIn("En attente de révision", result["by_status"])
        self.assertIn("Accepté", result["by_status"])
        self.assertIn("drainage_assainissement", result["by_theme"])
        self.assertIn("materiaux", result["by_theme"])

    def test_limit_caps_number_of_items(self):
        result = synthesize_public_inquiry(self.session, self.norme.id, limit=1, persist=False)
        self.assertEqual(result["total"], 1)

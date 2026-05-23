from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from datetime import date

from apps.validation.models import LegisticReview
from apps.norms.models import Norme
from apps.documents.models import DocumentFile
from apps.experts.models import Expert, Structure

User = get_user_model()


class Phase5Sprint1IntegrationTest(APITestCase):
    """Tests d'intégration complets pour Sprint 1 Phase 5"""
    
    def setUp(self):
        """Créer l'environnement de test complet"""
        self.client = APIClient()
        
        # Créer utilisateurs avec différents rôles
        self.minister_user = User.objects.create_user(
            username='minister',
            email='minister@example.com',
            password='testpass123',
            is_minister=True
        )
        
        self.ctc_user = User.objects.create_user(
            username='ctc',
            email='ctc@example.com',
            password='testpass123',
            is_ctc_staff=True
        )
        
        self.legist_user = User.objects.create_user(
            username='legist',
            email='legist@example.com',
            password='testpass123',
            is_expert=True
        )
        
        self.expert_user = User.objects.create_user(
            username='expert',
            email='expert@example.com',
            password='testpass123',
            is_expert=True
        )
        
        # Créer structure et experts
        self.structure = Structure.objects.create(
            name='Test Structure',
            category='administrative'
        )
        
        self.legist = Expert.objects.create(
            user=self.legist_user,
            structure=self.structure,
            status='ACTIVE'
        )
        
        self.expert = Expert.objects.create(
            user=self.expert_user,
            structure=self.structure,
            status='ACTIVE'
        )
        
        # Créer une norme au statut INTERNAL_REVIEW
        self.norme = Norme.objects.create(
            title='Test Norme Integration',
            reference_number='TNI-001',
            status='INTERNAL_REVIEW'
        )
    
    def test_complete_legistic_workflow(self):
        """Tester le workflow complet du toilettage légistique"""
        # 1. CTC crée un toilettage légistique
        self.client.force_authenticate(user=self.ctc_user)
        
        review = LegisticReview.objects.create(
            norme=self.norme,
            status='PENDING'
        )
        
        # 2. CTC assigne un légiste
        response = self.client.post(
            f'/api/v1/legistic-reviews/{review.id}/start_review/',
            {
                'legist': self.legist.id,
                'comments': 'Starting legal review'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.status, 'ASSIGNED')
        
        # 3. Légiste récupère ses reviews
        self.client.force_authenticate(user=self.legist_user)
        response = self.client.get('/api/v1/legistic-reviews/my_reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # 4. Légiste complète le toilettage
        response = self.client.post(
            f'/api/v1/legistic-reviews/{review.id}/complete_review/',
            {
                'comments': 'Review completed successfully',
                'approval_date': date.today().isoformat()
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.status, 'REVIEW_COMPLETED')
        
        # 5. Vérifier que le statut de la norme a été mis à jour
        self.norme.refresh_from_db()
        self.assertEqual(self.norme.status, 'LEGISTIC_REVIEW')
    
    def test_complete_publication_workflow(self):
        """Tester le workflow complet de publication au JO"""
        # 1. Mettre la norme au statut ADOPTED
        self.norme.status = 'ADOPTED'
        self.norme.save()
        
        # 2. Ministre publie au JO
        self.client.force_authenticate(user=self.minister_user)
        
        response = self.client.post(
            f'/api/v1/norms/{self.norme.id}/publish_to_jo/',
            {
                'jo_reference': 'JO-2024-INTEGRATION-001',
                'publication_date': date.today().isoformat()
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.norme.refresh_from_db()
        self.assertEqual(self.norme.status, 'PUBLISHED')
        self.assertEqual(self.norme.jo_reference, 'JO-2024-INTEGRATION-001')
        
        # 3. Vérifier le statut de publication
        response = self.client.get(f'/api/v1/norms/{self.norme.id}/publication_status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['is_published'], True)
    
    def test_complete_document_upload_workflow(self):
        """Tester le workflow complet d'upload de documents"""
        self.client.force_authenticate(user=self.expert_user)
        
        # 1. Expert upload un document pour la norme
        file_obj1 = SimpleUploadedFile(
            "test_norm_doc.pdf",
            b"document_content",
            content_type="application/pdf"
        )
        
        response = self.client.post(
            '/api/v1/documents/',
            {
                'file': file_obj1,
                'title': 'Norme Justification',
                'file_type': 'PDF',
                'category': 'Justificatif',
                'norme': self.norme.id
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        doc1 = DocumentFile.objects.get(title='Norme Justification')
        self.assertEqual(doc1.norme, self.norme)
        self.assertEqual(doc1.uploaded_by, self.expert_user)
        
        # 2. Expert récupère ses documents
        response = self.client.get('/api/v1/documents/my_documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # 3. Rendre public un document
        response = self.client.patch(
            f'/api/v1/documents/{doc1.id}/',
            {'is_public': True},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 4. Vérifier que le document public est visible
        response = self.client.get('/api/v1/documents/public_documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_permission_isolation(self):
        """Tester que les permissions sont bien isolées"""
        # Expert ne peut pas assigner un légiste
        self.client.force_authenticate(user=self.expert_user)
        
        review = LegisticReview.objects.create(
            norme=self.norme,
            status='PENDING'
        )
        
        response = self.client.post(
            f'/api/v1/legistic-reviews/{review.id}/start_review/',
            {'legist': self.legist.id}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Expert ne peut pas publier au JO
        self.norme.status = 'ADOPTED'
        self.norme.save()
        
        response = self.client.post(
            f'/api/v1/norms/{self.norme.id}/publish_to_jo/',
            {'jo_reference': 'JO-TEST'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_database_consistency_after_workflows(self):
        """Tester la cohérence de la base de données après les workflows"""
        # 1. Créer un workflow complet
        review = LegisticReview.objects.create(
            norme=self.norme,
            status='PENDING'
        )
        
        self.client.force_authenticate(user=self.ctc_user)
        self.client.post(
            f'/api/v1/legistic-reviews/{review.id}/start_review/',
            {'legist': self.legist.id}
        )
        
        # 2. Vérifier que tout est cohérent
        review.refresh_from_db()
        self.assertEqual(review.legist, self.legist)
        self.assertIsNotNone(review.review_start_date)
        
        # 3. Ajouter des documents
        self.client.force_authenticate(user=self.expert_user)
        
        file_obj = SimpleUploadedFile("test.pdf", b"content")
        doc = DocumentFile.objects.create(
            uploaded_by=self.expert_user,
            file=file_obj,
            title='Test',
            norme=self.norme
        )
        
        # 4. Vérifier que la norme a bien le document lié
        docs = self.norme.documents.all()
        self.assertEqual(docs.count(), 1)
        self.assertEqual(docs.first(), doc)
    
    def test_api_response_formats(self):
        """Tester que les réponses API ont le bon format"""
        self.client.force_authenticate(user=self.ctc_user)
        
        # Vérifier list endpoint
        response = self.client.get('/api/v1/legistic-reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        
        # Vérifier detail endpoint
        review = LegisticReview.objects.create(
            norme=self.norme,
            status='PENDING'
        )
        
        response = self.client.get(f'/api/v1/legistic-reviews/{review.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', response.data)
        self.assertIn('norme', response.data)
        self.assertIn('status', response.data)
    
    def test_sprint1_complete_workflow(self):
        """Tester un workflow complet combinant tous les éléments de Sprint 1"""
        # Workflow: Expertis → Légiste → Publication → Documents
        
        # 1. Créer toilettage légistique
        self.client.force_authenticate(user=self.ctc_user)
        review = LegisticReview.objects.create(
            norme=self.norme,
            status='PENDING'
        )
        
        self.client.post(
            f'/api/v1/legistic-reviews/{review.id}/start_review/',
            {'legist': self.legist.id}
        )
        
        # 2. Légiste complete
        self.client.force_authenticate(user=self.legist_user)
        self.client.post(
            f'/api/v1/legistic-reviews/{review.id}/complete_review/',
            {
                'comments': 'Review done',
                'approval_date': date.today().isoformat()
            }
        )
        
        # 3. Transitionner norme au statut ADOPTED
        self.norme.status = 'ADOPTED'
        self.norme.save()
        
        # 4. Publier au JO
        self.client.force_authenticate(user=self.minister_user)
        self.client.post(
            f'/api/v1/norms/{self.norme.id}/publish_to_jo/',
            {'jo_reference': 'JO-FINAL'}
        )
        
        # 5. Upload doc final
        self.client.force_authenticate(user=self.expert_user)
        file_obj = SimpleUploadedFile("final.pdf", b"final_content")
        self.client.post(
            '/api/v1/documents/',
            {
                'file': file_obj,
                'title': 'Final Document',
                'file_type': 'PDF',
                'norme': self.norme.id
            },
            format='multipart'
        )
        
        # 6. Vérifier l'état final
        self.norme.refresh_from_db()
        self.assertEqual(self.norme.status, 'PUBLISHED')
        self.assertEqual(self.norme.jo_reference, 'JO-FINAL')
        self.assertEqual(self.norme.documents.count(), 1)
        
        review.refresh_from_db()
        self.assertEqual(review.status, 'REVIEW_COMPLETED')

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from datetime import date

from apps.validation.models import LegisticReview
from apps.norms.models import Norme
from apps.experts.models import Expert, Structure
from apps.governance.models import CTM

User = get_user_model()


class LegisticReviewModelTest(TestCase):
    """Tests pour le modèle LegisticReview"""
    
    def setUp(self):
        """Créer les données de test"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.legist_user = User.objects.create_user(
            username='legist',
            email='legist@example.com',
            password='testpass123',
            is_expert=True
        )
        
        # Créer structure et expert
        self.structure = Structure.objects.create(
            name='Test Structure',
            category='administrative'
        )
        
        self.legist = Expert.objects.create(
            user=self.legist_user,
            structure=self.structure,
            status='ACTIVE'
        )
        
        # Créer une norme
        self.norme = Norme.objects.create(
            title='Test Norme',
            reference_number='TN-001',
            status='INTERNAL_REVIEW'
        )
    
    def test_create_legistic_review(self):
        """Tester la création d'un toilettage légistique"""
        review = LegisticReview.objects.create(
            norme=self.norme,
            legist=self.legist,
            status='PENDING'
        )
        self.assertEqual(review.norme, self.norme)
        self.assertEqual(review.legist, self.legist)
        self.assertEqual(review.status, 'PENDING')
    
    def test_review_status_choices(self):
        """Tester que les statuts sont valides"""
        review = LegisticReview.objects.create(
            norme=self.norme,
            status='PENDING'
        )
        valid_statuses = ['PENDING', 'ASSIGNED', 'IN_REVIEW', 'REVIEW_COMPLETED', 'APPROVED', 'REJECTED']
        for status_choice in valid_statuses:
            review.status = status_choice
            review.full_clean()  # Ne doit pas lever d'erreur
    
    def test_review_str(self):
        """Tester la représentation string"""
        review = LegisticReview.objects.create(
            norme=self.norme,
            status='PENDING'
        )
        expected = f"Toilettage {self.norme.reference_number} - PENDING"
        self.assertEqual(str(review), expected)


class LegisticReviewAPITest(APITestCase):
    """Tests API pour LegisticReview"""
    
    def setUp(self):
        """Créer les données de test"""
        self.client = APIClient()
        
        # Créer utilisateurs
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
        
        # Créer une norme
        self.norme = Norme.objects.create(
            title='Test Norme',
            reference_number='TN-001',
            status='INTERNAL_REVIEW'
        )
    
    def test_list_legistic_reviews_authenticated(self):
        """Tester la récupération de la liste des toilettages"""
        self.client.force_authenticate(user=self.ctc_user)
        
        LegisticReview.objects.create(
            norme=self.norme,
            status='PENDING'
        )
        
        response = self.client.get('/api/v1/legistic-reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_start_review_by_ctc(self):
        """Tester le démarrage d'un toilettage par CTC"""
        self.client.force_authenticate(user=self.ctc_user)
        
        review = LegisticReview.objects.create(
            norme=self.norme,
            status='PENDING'
        )
        
        response = self.client.post(
            f'/api/v1/legistic-reviews/{review.id}/start_review/',
            {
                'legist': self.legist.id,
                'comments': 'Starting review'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.status, 'ASSIGNED')
        self.assertEqual(review.legist, self.legist)
    
    def test_complete_review_by_legist(self):
        """Tester la complétion d'un toilettage par le légiste"""
        self.client.force_authenticate(user=self.legist_user)
        
        review = LegisticReview.objects.create(
            norme=self.norme,
            legist=self.legist,
            status='IN_REVIEW',
            review_start_date=date.today()
        )
        
        response = self.client.post(
            f'/api/v1/legistic-reviews/{review.id}/complete_review/',
            {
                'comments': 'Review completed',
                'approval_date': date.today().isoformat()
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.status, 'REVIEW_COMPLETED')
    
    def test_reject_review_by_legist(self):
        """Tester le rejet d'un toilettage"""
        self.client.force_authenticate(user=self.legist_user)
        
        review = LegisticReview.objects.create(
            norme=self.norme,
            legist=self.legist,
            status='IN_REVIEW'
        )
        
        response = self.client.post(
            f'/api/v1/legistic-reviews/{review.id}/reject_review/',
            {
                'comments': 'Needs more work'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.status, 'REJECTED')
    
    def test_my_reviews_endpoint(self):
        """Tester l'endpoint pour voir ses propres revues"""
        self.client.force_authenticate(user=self.legist_user)
        
        review1 = LegisticReview.objects.create(
            norme=self.norme,
            legist=self.legist,
            status='ASSIGNED'
        )
        
        # Créer une autre norme et review
        norme2 = Norme.objects.create(
            title='Test Norme 2',
            reference_number='TN-002'
        )
        review2 = LegisticReview.objects.create(
            norme=norme2,
            legist=self.legist,
            status='IN_REVIEW'
        )
        
        response = self.client.get('/api/v1/legistic-reviews/my_reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_permission_denied_for_unauthenticated(self):
        """Tester que les utilisateurs non authentifiés ne peuvent pas accéder"""
        response = self.client.get('/api/v1/legistic-reviews/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_pending_endpoint(self):
        """Tester l'endpoint pour voir les reviews en attente"""
        self.client.force_authenticate(user=self.ctc_user)
        
        review1 = LegisticReview.objects.create(
            norme=self.norme,
            status='PENDING'
        )
        
        norme2 = Norme.objects.create(
            title='Test Norme 2',
            reference_number='TN-002'
        )
        review2 = LegisticReview.objects.create(
            norme=norme2,
            legist=self.legist,
            status='ASSIGNED'
        )
        
        response = self.client.get('/api/v1/legistic-reviews/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

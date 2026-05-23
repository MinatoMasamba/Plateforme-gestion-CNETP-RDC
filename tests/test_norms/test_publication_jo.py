from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from datetime import date

from apps.norms.models import Norme
from apps.experts.models import Expert, Structure
from apps.governance.models import CTM

User = get_user_model()


class NormePublicationJOAPITest(APITestCase):
    """Tests API pour la publication au Journal Officiel"""
    
    def setUp(self):
        """Créer les données de test"""
        self.client = APIClient()
        
        # Créer utilisateurs
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
        
        self.expert_user = User.objects.create_user(
            username='expert',
            email='expert@example.com',
            password='testpass123',
            is_expert=True
        )
        
        # Créer structure et expert
        self.structure = Structure.objects.create(
            name='Test Structure',
            category='administrative'
        )
        
        self.expert = Expert.objects.create(
            user=self.expert_user,
            structure=self.structure,
            status='ACTIVE'
        )
        
        # Créer une norme au statut ADOPTED
        self.norme = Norme.objects.create(
            title='Test Norme',
            reference_number='TN-001',
            status='ADOPTED'
        )
    
    def test_publish_to_jo_by_minister(self):
        """Tester la publication au JO par un ministre"""
        self.client.force_authenticate(user=self.minister_user)
        
        response = self.client.post(
            f'/api/v1/norms/{self.norme.id}/publish_to_jo/',
            {
                'jo_reference': 'JO-2024-001',
                'publication_date': date.today().isoformat()
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.norme.refresh_from_db()
        self.assertEqual(self.norme.status, 'PUBLISHED')
        self.assertEqual(self.norme.jo_reference, 'JO-2024-001')
    
    def test_publish_to_jo_by_ctc(self):
        """Tester la publication au JO par un coordinateur CTC"""
        self.client.force_authenticate(user=self.ctc_user)
        
        response = self.client.post(
            f'/api/v1/norms/{self.norme.id}/publish_to_jo/',
            {
                'jo_reference': 'JO-2024-002',
                'publication_date': date.today().isoformat()
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.norme.refresh_from_db()
        self.assertEqual(self.norme.status, 'PUBLISHED')
    
    def test_publish_to_jo_permission_denied_expert(self):
        """Tester que seul ministre/CTC peuvent publier"""
        self.client.force_authenticate(user=self.expert_user)
        
        response = self.client.post(
            f'/api/v1/norms/{self.norme.id}/publish_to_jo/',
            {
                'jo_reference': 'JO-2024-003'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_publish_to_jo_wrong_status(self):
        """Tester la publication avec un mauvais statut"""
        self.client.force_authenticate(user=self.minister_user)
        
        self.norme.status = 'DRAFT'
        self.norme.save()
        
        response = self.client.post(
            f'/api/v1/norms/{self.norme.id}/publish_to_jo/',
            {
                'jo_reference': 'JO-2024-004'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ADOPTED', response.data['error'])
    
    def test_publish_to_jo_missing_reference(self):
        """Tester la publication sans référence JO"""
        self.client.force_authenticate(user=self.minister_user)
        
        response = self.client.post(
            f'/api/v1/norms/{self.norme.id}/publish_to_jo/',
            {},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('jo_reference', response.data['error'])
    
    def test_publication_status_endpoint(self):
        """Tester l'endpoint de statut de publication"""
        self.client.force_authenticate(user=self.expert_user)
        
        # Publier la norme d'abord
        self.norme.status = 'PUBLISHED'
        self.norme.jo_reference = 'JO-2024-005'
        self.norme.publication_date = date.today()
        self.norme.save()
        
        response = self.client.get(
            f'/api/v1/norms/{self.norme.id}/publication_status/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['is_published'], True)
        self.assertEqual(response.data['jo_reference'], 'JO-2024-005')
        self.assertIsNotNone(response.data['publication_date'])
    
    def test_publication_status_unpublished_norme(self):
        """Tester le statut de publication pour une norme non publiée"""
        self.client.force_authenticate(user=self.expert_user)
        
        response = self.client.get(
            f'/api/v1/norms/{self.norme.id}/publication_status/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['is_published'], False)
        self.assertIsNone(response.data['jo_reference'])

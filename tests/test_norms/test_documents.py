from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from apps.documents.models import DocumentFile
from apps.experts.models import Expert, Structure
from apps.norms.models import Norme

User = get_user_model()


class DocumentFileModelTest(TestCase):
    """Tests pour le modèle DocumentFile"""
    
    def setUp(self):
        """Créer les données de test"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.structure = Structure.objects.create(
            name='Test Structure',
            category='administrative'
        )
        
        self.expert = Expert.objects.create(
            user=self.user,
            structure=self.structure,
            status='ACTIVE'
        )
    
    def test_create_document(self):
        """Tester la création d'un document"""
        file_obj = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        
        doc = DocumentFile.objects.create(
            uploaded_by=self.user,
            expert=self.expert,
            file=file_obj,
            title='Test Document',
            file_type='PDF'
        )
        
        self.assertEqual(doc.title, 'Test Document')
        self.assertEqual(doc.file_type, 'PDF')
        self.assertEqual(doc.uploaded_by, self.user)
    
    def test_document_str(self):
        """Tester la représentation string du document"""
        file_obj = SimpleUploadedFile("test.pdf", b"file_content")
        
        doc = DocumentFile.objects.create(
            uploaded_by=self.user,
            file=file_obj,
            title='Test Document',
            file_type='PDF'
        )
        
        self.assertIn('Test Document', str(doc))


class DocumentFileAPITest(APITestCase):
    """Tests API pour DocumentFile"""
    
    def setUp(self):
        """Créer les données de test"""
        self.client = APIClient()
        
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        self.structure = Structure.objects.create(
            name='Test Structure',
            category='administrative'
        )
        
        self.expert1 = Expert.objects.create(
            user=self.user1,
            structure=self.structure,
            status='ACTIVE'
        )
        
        self.norme = Norme.objects.create(
            title='Test Norme',
            reference_number='TN-001'
        )
    
    def test_list_documents_authenticated(self):
        """Tester la récupération de la liste des documents"""
        self.client.force_authenticate(user=self.user1)
        
        file_obj = SimpleUploadedFile("test.pdf", b"file_content")
        DocumentFile.objects.create(
            uploaded_by=self.user1,
            file=file_obj,
            title='Test Doc',
            file_type='PDF'
        )
        
        response = self.client.get('/api/v1/documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_upload_document(self):
        """Tester l'upload d'un document"""
        self.client.force_authenticate(user=self.user1)
        
        file_obj = SimpleUploadedFile(
            "test.pdf",
            b"file_content" * 100,
            content_type="application/pdf"
        )
        
        response = self.client.post(
            '/api/v1/documents/',
            {
                'file': file_obj,
                'title': 'Test Document',
                'description': 'Test description',
                'file_type': 'PDF',
                'category': 'Test'
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DocumentFile.objects.count(), 1)
    
    def test_upload_document_with_norme(self):
        """Tester l'upload d'un document lié à une norme"""
        self.client.force_authenticate(user=self.user1)
        
        file_obj = SimpleUploadedFile("test.pdf", b"file_content")
        
        response = self.client.post(
            '/api/v1/documents/',
            {
                'file': file_obj,
                'title': 'Norme Document',
                'file_type': 'PDF',
                'norme': self.norme.id
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        doc = DocumentFile.objects.get(title='Norme Document')
        self.assertEqual(doc.norme, self.norme)
    
    def test_unauthenticated_cannot_upload(self):
        """Tester que les non-authentifiés ne peuvent pas uploader"""
        file_obj = SimpleUploadedFile("test.pdf", b"file_content")
        
        response = self.client.post(
            '/api/v1/documents/',
            {
                'file': file_obj,
                'title': 'Test',
                'file_type': 'PDF'
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_delete_own_document(self):
        """Tester la suppression de son propre document"""
        self.client.force_authenticate(user=self.user1)
        
        file_obj = SimpleUploadedFile("test.pdf", b"file_content")
        doc = DocumentFile.objects.create(
            uploaded_by=self.user1,
            file=file_obj,
            title='Test Doc',
            file_type='PDF'
        )
        
        response = self.client.delete(f'/api/v1/documents/{doc.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(DocumentFile.objects.count(), 0)
    
    def test_cannot_delete_others_document(self):
        """Tester qu'on ne peut pas supprimer le document d'un autre"""
        self.client.force_authenticate(user=self.user2)
        
        file_obj = SimpleUploadedFile("test.pdf", b"file_content")
        doc = DocumentFile.objects.create(
            uploaded_by=self.user1,
            file=file_obj,
            title='Test Doc',
            file_type='PDF'
        )
        
        response = self.client.delete(f'/api/v1/documents/{doc.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(DocumentFile.objects.count(), 1)
    
    def test_my_documents_endpoint(self):
        """Tester l'endpoint pour voir ses propres documents"""
        self.client.force_authenticate(user=self.user1)
        
        # Créer des documents pour user1
        file_obj1 = SimpleUploadedFile("test1.pdf", b"content1")
        DocumentFile.objects.create(
            uploaded_by=self.user1,
            file=file_obj1,
            title='Doc1'
        )
        
        file_obj2 = SimpleUploadedFile("test2.pdf", b"content2")
        DocumentFile.objects.create(
            uploaded_by=self.user1,
            file=file_obj2,
            title='Doc2'
        )
        
        # Créer un document pour user2
        file_obj3 = SimpleUploadedFile("test3.pdf", b"content3")
        DocumentFile.objects.create(
            uploaded_by=self.user2,
            file=file_obj3,
            title='Doc3'
        )
        
        response = self.client.get('/api/v1/documents/my_documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_public_documents_endpoint(self):
        """Tester l'endpoint des documents publics"""
        self.client.force_authenticate(user=self.user1)
        
        # Créer des documents publics et privés
        file_obj1 = SimpleUploadedFile("public.pdf", b"public_content")
        DocumentFile.objects.create(
            uploaded_by=self.user1,
            file=file_obj1,
            title='Public Doc',
            is_public=True
        )
        
        file_obj2 = SimpleUploadedFile("private.pdf", b"private_content")
        DocumentFile.objects.create(
            uploaded_by=self.user1,
            file=file_obj2,
            title='Private Doc',
            is_public=False
        )
        
        response = self.client.get('/api/v1/documents/public_documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Public Doc')
    
    def test_file_size_display(self):
        """Tester l'affichage de la taille du fichier"""
        file_obj = SimpleUploadedFile("test.pdf", b"file_content")
        doc = DocumentFile.objects.create(
            uploaded_by=self.user1,
            file=file_obj,
            title='Test Doc',
            file_size=1024 * 1024 * 5  # 5 MB
        )
        
        self.assertEqual(doc.get_file_size_display(), '5.0 MB')

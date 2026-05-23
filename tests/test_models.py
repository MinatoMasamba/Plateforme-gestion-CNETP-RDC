import pytest
from django.test import TestCase
from apps.core.models import User
from apps.experts.models import Expert, Structure
from apps.governance.models import CTM, WG


@pytest.mark.django_db
def test_user_creation():
    """Test création d'un utilisateur"""
    user = User.objects.create_user(username='john_doe', email='john@cnetp.cd', password='testpass123')
    assert user.username == 'john_doe'
    assert user.email == 'john@cnetp.cd'


@pytest.mark.django_db
def test_structure_and_expert():
    """Test création d'une structure et d'un expert"""
    user = User.objects.create_user(username='expert1', email='expert@cnetp.cd', password='test')
    structure = Structure.objects.create(
        name='Test Structure',
        acronym='TST',
        category='ADMIN'
    )
    expert = Expert.objects.create(
        user=user,
        structure=structure,
        status='ACTIVE'
    )
    assert expert.structure.name == 'Test Structure'
    assert expert.status == 'ACTIVE'


@pytest.mark.django_db
def test_ctm_and_wg():
    """Test création d'un CTM et WG"""
    ctm = CTM.objects.create(number=1, name='CTM 1', description='Test CTM')
    wg = WG.objects.create(ctm=ctm, number=1, name='WG 1.1')
    assert wg.ctm == ctm
    assert wg.number == 1


@pytest.mark.django_db
def test_norme_creation():
    """Test création d'une norme"""
    from apps.norms.models import Norme
    
    ctm = CTM.objects.create(number=2, name='CTM 2', description='Test')
    wg = WG.objects.create(ctm=ctm, number=1, name='WG 2.1')
    norme = Norme.objects.create(
        title='Test Norme',
        reference_number='CNETP-001-2024',
        description='Test description',
        ctm=ctm,
        wg=wg
    )
    assert norme.status == 'DRAFT'
    assert norme.ctm.number == 2

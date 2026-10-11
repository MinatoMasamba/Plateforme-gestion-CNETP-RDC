import pytest


@pytest.fixture
def user_factory():
    """Factory pour créer des utilisateurs test"""
    from apps.core.models import User

    def _create_user(username='testuser', email='test@cnetp.cd', password='testpass123', **kwargs):
        if 'username' in kwargs:
            username = kwargs.pop('username')
        if 'email' in kwargs:
            email = kwargs.pop('email')
        if 'password' in kwargs:
            password = kwargs.pop('password')
        return User.objects.create_user(username=username, email=email, password=password, **kwargs)

    return _create_user


@pytest.fixture
def expert_factory(user_factory):
    """Factory pour créer des experts test"""
    from apps.experts.models import Expert, Structure

    def _create_expert(user=None, structure=None, **kwargs):
        if user is None:
            user = user_factory()
        if structure is None:
            structure, _ = Structure.objects.get_or_create(
                name='Test Structure',
                defaults={'acronym': 'TST', 'category': 'ADMIN'}
            )
        return Expert.objects.create(user=user, structure=structure, status='ACTIVE', **kwargs)

    return _create_expert


@pytest.fixture
def ctm_factory():
    """Factory pour créer des CTM test"""
    from apps.governance.models import CTM
    counter = {'count': 0}

    def _create_ctm(number=None, name=None, **kwargs):
        if number is None:
            counter['count'] += 1
            number = counter['count']
        if name is None:
            name = f'Test CTM {number}'
        return CTM.objects.create(number=number, name=name, description='Test', **kwargs)

    return _create_ctm


@pytest.fixture
def wg_factory(ctm_factory):
    """Factory pour créer des WG test"""
    from apps.governance.models import WG
    counter = {'count': 0}

    def _create_wg(ctm=None, number=None, name=None, **kwargs):
        if ctm is None:
            ctm = ctm_factory()
        if number is None:
            counter['count'] += 1
            number = counter['count']
        if name is None:
            name = f'Test WG {number}'
        return WG.objects.create(ctm=ctm, number=number, name=name, **kwargs)

    return _create_wg


@pytest.fixture
def norme_factory(ctm_factory, wg_factory):
    """Factory pour créer des normes test"""
    from apps.norms.models import Norme

    def _create_norme(title='Test Norme', ctm=None, wg=None, **kwargs):
        if ctm is None:
            ctm = ctm_factory()
        if wg is None:
            wg = wg_factory(ctm=ctm)

        defaults = {
            'title': title,
            'reference_number': f'CNETP-TEST-{Norme.objects.count() + 1}',
            'description': 'Test',
            'ctm': ctm,
            'wg': wg,
        }
        defaults.update(kwargs)
        return Norme.objects.create(**defaults)

    return _create_norme

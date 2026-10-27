import pytest


@pytest.fixture
def user_factory(db):
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
def ctm_factory(db):
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

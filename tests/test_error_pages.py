"""Les handlers Django affichent les pages institutionnelles sans détails internes."""
import pytest
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import Http404, HttpResponse
from django.test import Client, override_settings
from django.urls import include, path


def error_view(request, code):
    exceptions = {
        400: SuspiciousOperation,
        403: PermissionDenied,
        404: Http404,
        500: RuntimeError,
    }
    raise exceptions[code]('INTERNAL_ERROR_DETAIL_NOT_FOR_DISPLAY')


def form_view(request):
    return HttpResponse('Formulaire accepté')


urlpatterns = [
    path('_test/erreur/<int:code>/', error_view),
    path('_test/formulaire/', form_view),
    path('', include('config.urls')),
]


@pytest.mark.parametrize(('code', 'heading'), [
    (400, 'Requête invalide'),
    (403, 'Accès refusé'),
    (404, 'Page introuvable'),
    (500, 'Une erreur est survenue'),
])
def test_error_handlers_render_custom_pages(code, heading):
    with override_settings(DEBUG=False, ROOT_URLCONF=__name__):
        response = Client(raise_request_exception=False).get(f'/_test/erreur/{code}/')

    assert response.status_code == code
    html = response.content.decode()
    assert heading in html
    assert 'Retour à l’accueil' in html
    assert 'INTERNAL_ERROR_DETAIL_NOT_FOR_DISPLAY' not in html
    assert 'Traceback' not in html


def test_csrf_rejection_uses_custom_page():
    with override_settings(DEBUG=False, ROOT_URLCONF=__name__):
        response = Client(enforce_csrf_checks=True).post('/_test/formulaire/')

    assert response.status_code == 403
    assert 'Vérification de sécurité échouée' in response.content.decode()
    assert 'CSRF cookie not set' not in response.content.decode()


@pytest.mark.django_db
def test_console_access_denied_uses_custom_403(user_factory):
    client = Client()
    client.force_login(user_factory())
    with override_settings(DEBUG=False):
        response = client.get('/dashboard/administration/modeles/experts/expert/')

    assert response.status_code == 403
    assert 'Accès refusé' in response.content.decode()

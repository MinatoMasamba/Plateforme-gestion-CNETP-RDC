"""Module rapports et navigation du shell documentaire poste 11."""
import pytest

from tests.test_st_ged import ged  # noqa: F401


@pytest.mark.django_db
def test_reports_payload_carries_owner_and_mine_flag(ged, client):
    g = ged
    client.force_login(g.writer)
    created = client.post('/api/v1/st/reports/',
        {'title': 'Rapport de recette', 'sections': [{'title': 'Objet', 'content': 'Suivi documentaire'}]},
        content_type='application/json')
    assert created.status_code == 201
    payload = created.json()
    assert payload['mine'] is True
    assert payload['owner_name'] == (g.writer.get_full_name() or g.writer.username)
    assert payload['dispatch_count'] == 0
    assert payload['updated_at']
    client.force_login(g.head)
    visible = client.get('/api/v1/st/reports/').json()['results']
    matching = [row for row in visible if row['id'] == payload['id']]
    assert matching, 'Le chef du Pôle 2 doit voir les rapports de son pôle.'
    assert matching[0]['mine'] is False
    assert matching[0]['owner_name'] == payload['owner_name']


@pytest.mark.django_db
def test_post11_shell_renders_document_space_and_reports_navigation(ged, client):
    client.force_login(ged.writer)
    response = client.get('/ctc/')
    assert response.status_code == 200
    content = response.content.decode()
    assert 'data-ged-workspace' in content
    assert 'Espace documentaire' in content
    assert 'Suivi et supervision documentaire' in content
    assert 'data-ged-sc-chart' in content
    assert 'data-sidebar-view="rapports"' in content
    assert 'st-report-gallery' in content
    assert 'stReportsInit' in content
    assert 'Importer un rapport' in content
    assert 'st-report-preview' in content
    assert 'data-ged-my-reports' in content
    assert 'Mes rapports' in content
    for view in ('indexation', 'ged', 'codification', 'versions', 'ged_anomalies', 'ged_activity'):
        assert f'data-sidebar-view="{view}"' in content

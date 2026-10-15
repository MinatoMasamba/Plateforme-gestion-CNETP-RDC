"""Tests E2E fonctionnels (via l'API du serveur live, sessions par rôle).

Couvre : saisie de norme, 20 éditions + historique/diff/rollback, PDF,
upload de documents, messagerie (10 conversations), paiements, assistant IA
ciblé, workflow jusqu'à la publication au JO, et verrouillage concurrent.

Lancer avec : ``pytest tests/e2e -m e2e``
"""
import time

import pytest

from tests.e2e.conftest import ROLES, E2E_PASSWORD, api


pytestmark = pytest.mark.e2e


def _as_list(data):
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    return data if isinstance(data, list) else []


def _ctm_wg(session):
    ctms = _as_list(api(session, 'get', '/api/v1/ctm/').json())
    assert ctms, 'Aucun CTM seedé'
    ctm_id = ctms[0]['id']
    wgs = _as_list(api(session, 'get', '/api/v1/wg/').json())
    wg = next((w for w in wgs if w.get('ctm') == ctm_id), None) or (wgs[0] if wgs else None)
    assert wg, 'Aucun WG seedé'
    return ctm_id, wg['id']


def _create_norme(session, ref):
    ctm_id, wg_id = _ctm_wg(session)
    resp = api(session, 'post', '/api/v1/norms/', json={
        'reference_number': ref,
        'title': f'Norme E2E {ref}',
        'description': 'Norme créée par la campagne E2E.',
        'ctm': ctm_id, 'wg': wg_id, 'standard_family': 'NCD',
    })
    assert resp.status_code in (201, 200), resp.text
    return resp.json()['id']


def test_expert_creates_norme_and_20_versions(api_login):
    s = api_login(ROLES['expert'][0])
    ref = f'E2E-V-TS{int(time.time())}'
    norme_id = _create_norme(s, ref)

    for i in range(1, 21):
        resp = api(s, 'post', f'/api/v1/norms/{norme_id}/create_version/', json={
            'title': f'Norme E2E {ref}',
            'content': f'Section 1 Objet\nLigne éditée #{i}.\n\nSection 2 Application\nContenu stable.',
            'comment': f'Édition {i}',
        })
        assert resp.status_code in (201, 200), resp.text

    versions = _as_list(api(s, 'get', f'/api/v1/norms/{norme_id}/versions/?per_page=100').json())
    assert len(versions) >= 20, f'{len(versions)} versions trouvées'

    history = api(s, 'get', f'/api/v1/norms/{norme_id}/history/')
    assert history.status_code == 200


def test_norme_diff_and_rollback(api_login):
    s = api_login(ROLES['expert'][0])
    ref = f'E2E-D-TS{int(time.time())}'
    norme_id = _create_norme(s, ref)

    api(s, 'post', f'/api/v1/norms/{norme_id}/create_version/',
        json={'title': ref, 'content': 'Section 1\nTexte A.', 'comment': 'v1'})
    api(s, 'post', f'/api/v1/norms/{norme_id}/create_version/',
        json={'title': ref, 'content': 'Section 1\nTexte B corrigé.', 'comment': 'v2'})

    diff = api(s, 'get', f'/api/v1/norms/{norme_id}/diff/?v1=1&v2=2')
    assert diff.status_code == 200, diff.text

    rollback = api(s, 'post', f'/api/v1/norms/{norme_id}/rollback-version/',
                   json={'version_number': 1})
    assert rollback.status_code in (201, 200), rollback.text
    versions = _as_list(api(s, 'get', f'/api/v1/norms/{norme_id}/versions/').json())
    assert len(versions) >= 3


def test_norme_pdf_generation(api_login):
    s = api_login(ROLES['expert'][0])
    ref = f'E2E-PDF-TS{int(time.time())}'
    norme_id = _create_norme(s, ref)
    api(s, 'post', f'/api/v1/norms/{norme_id}/create_version/',
        json={'title': ref, 'content': 'Section 1\nContenu PDF.', 'comment': 'pdf'})

    resp = api(s, 'get', f'/api/v1/norms/{norme_id}/pdf/')
    assert resp.status_code == 200, resp.text[:300]
    assert resp.headers.get('Content-Type', '').startswith('application/pdf')
    assert len(resp.content) > 500


def test_document_upload_and_listing(api_login):
    s = api_login(ROLES['expert'][0])
    files = {'file': ('e2e_upload.txt', b'Contenu du document E2E.', 'text/plain')}
    data = {'title': 'Document E2E', 'file_type': 'OTHER', 'category': 'Evidence', 'is_public': 'true'}
    resp = api(s, 'post', '/api/v1/documents/', data=data, files=files)
    assert resp.status_code in (201, 200), resp.text

    mine = api(s, 'get', '/api/v1/documents/my_documents/')
    assert mine.status_code == 200
    assert len(_as_list(mine.json())) >= 1

    pub = api(s, 'get', '/api/v1/documents/public_documents/')
    assert pub.status_code == 200


def test_messaging_10_conversations(api_login):
    s = api_login(ROLES['expert'][0])
    contacts = _as_list(api(s, 'get', '/api/v1/messages/contacts/').json())
    assert contacts, 'Aucun contact partageant le CTM'
    receivers = [c['user_id'] for c in contacts][:10]

    created = 0
    for rid in receivers:
        resp = api(s, 'post', '/api/v1/messages/', json={
            'receiver_id': rid, 'content': 'Message de test E2E — vérification conversation.',
        })
        if resp.status_code in (201, 200):
            created += 1

    assert created >= min(10, len(receivers)), f'{created} conversations créées'
    unread = api(s, 'get', '/api/v1/messages/unread_count/')
    assert unread.status_code == 200


def test_payments_flow(api_login):
    ctc = api_login(ROLES['ctc'][0])
    expert = api_login(ROLES['expert'][0])

    structures = _as_list(api(ctc, 'get', '/api/v1/structures/').json())
    assert structures
    structure_id = structures[-1]['id']

    cot = api(ctc, 'post', '/api/v1/cotisations/', json={
        'structure': structure_id, 'annee': 2099, 'montant': 7500,
        'due_date': '2099-12-31',
    })
    if cot.status_code in (201, 200) and 'id' in cot.json():
        cot_id = cot.json()['id']
    else:
        existing = _as_list(api(ctc, 'get', '/api/v1/cotisations/?per_page=100').json())
        assert existing, cot.text
        cot_id = existing[-1]['id']

    paiement = api(expert, 'post', '/api/v1/paiements/', json={
        'cotisation': cot_id, 'montant': 1000, 'methode_paiement': 'VIREMENT',
        'payment_date': '2026-10-11',
    })
    assert paiement.status_code in (201, 200), paiement.text

    # Le serializer de création ne renvoie pas l'id : on le récupère via la liste.
    paiements = _as_list(api(ctc, 'get', '/api/v1/paiements/?per_page=100').json())
    assert paiements, 'Aucun paiement listé'
    paiement_id = max(p['id'] for p in paiements)

    confirm = api(ctc, 'post', f'/api/v1/paiements/{paiement_id}/confirm/')
    assert confirm.status_code in (200, 201), confirm.text


def test_ia_targeted_advice(api_login):
    s = api_login(ROLES['expert'][0])
    texte = (
        "Section 1 Objet\n"
        "Le présente norme définit les exigeance minimales.\n"
        "Section 2 Domaine\n"
        "Elle s'applique au batiment et aux travaus publics."
    )
    resp = api(s, 'post', '/api/v1/ia-agent/sessions/regulatory-advice/', json={'text': texte})
    assert resp.status_code == 200, resp.text[:300]
    data = resp.json()
    assert 'edits' in data and 'applied_text' in data
    for edit in data['edits']:
        assert set(['find', 'replace', 'reason', 'applied']).issubset(edit.keys())


def test_workflow_to_publication(api_login):
    ctc = api_login(ROLES['ctc'][0])
    ref = f'E2E-JO-TS{int(time.time())}'
    norme_id = _create_norme(ctc, ref)

    chain = ['INTERNAL_REVIEW', 'CTM_REVIEW', 'LEGISTIC_REVIEW', 'PUBLIC_INQUIRY',
             'PILOTAGE_REVIEW', 'FINAL_REVIEW', 'ADOPTED']
    for statut in chain:
        resp = api(ctc, 'post', f'/api/v1/norms/{norme_id}/update_status/', json={'status': statut})
        assert resp.status_code in (200, 201), f'{statut}: {resp.text[:200]}'

    publish = api(ctc, 'post', f'/api/v1/norms/{norme_id}/publish_to_jo/',
                  json={'jo_reference': f'JO-E2E-{int(time.time())}'})
    assert publish.status_code in (200, 201), publish.text[:300]

    status = api(ctc, 'get', f'/api/v1/norms/{norme_id}/publication_status/')
    assert status.status_code == 200
    assert status.json().get('is_published') is True


def test_concurrent_edit_lock(api_login):
    owner = api_login(ROLES['expert'][0])
    other = api_login('expert2@cnetp.cd')

    ref = f'E2E-LOCK-TS{int(time.time())}'
    norme_id = _create_norme(owner, ref)

    lock = api(owner, 'post', f'/api/v1/norms/{norme_id}/lock/')
    assert lock.status_code in (200, 201), lock.text

    blocked = api(other, 'post', f'/api/v1/norms/{norme_id}/create_version/',
                  json={'title': ref, 'content': 'Tentative concurrente.', 'comment': 'x'})
    assert blocked.status_code in (423, 409), blocked.text[:200]

    api(owner, 'post', f'/api/v1/norms/{norme_id}/unlock/')

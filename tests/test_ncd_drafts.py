"""Tests du circuit de création de brouillons NCD par un client externe (API)."""

import pytest
from rest_framework.test import APIClient

from apps.norms.models import Norme, NormeVersion

pytestmark = pytest.mark.django_db


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def ctc_user(user_factory):
    return user_factory(username="ctc", email="ctc@cnetp.cd", is_ctc_staff=True)


def _norm_payload(ctm, wg, reference_number="NCD 001"):
    return {
        "reference_number": reference_number,
        "title": "Vocabulaire technique unifié et symboles graphiques pour le BTP en RDC",
        "description": "Base de travail pour la terminologie du BTP.",
        "source_reference": "Rapport adopté de la CNE-ITP du 15 octobre 2026",
        "standard_family": "NCD",
        "norm_type": "NCD",
        "category": "Matériaux & Essais / Socle commun",
        "iso_reference": "ISO 80000 (série)",
        "tags": "vocabulaire, symboles",
        "ctm": ctm.id,
        "wg": wg.id,
    }


def test_create_draft_as_ctc_staff(api, ctc_user, ctm_factory, wg_factory):
    ctm = ctm_factory(number=6, name="Matériaux & Essais / Socle Commun (SC-SOCLE)")
    wg = wg_factory(ctm=ctm, number=1, name="Normalisation Appliquée")

    api.force_authenticate(ctc_user)
    response = api.post("/api/v1/norms/", _norm_payload(ctm, wg), format="json")

    assert response.status_code == 201, response.data
    assert response.data["source_reference"] == "Rapport adopté de la CNE-ITP du 15 octobre 2026"

    norme = Norme.all_objects.get(reference_number="NCD 001")
    assert norme.status == "DRAFT"
    assert norme.standard_family == "NCD"


def test_duplicate_reference_number_rejected(api, ctc_user, ctm_factory, wg_factory):
    ctm = ctm_factory(number=6, name="Matériaux & Essais / Socle Commun (SC-SOCLE)")
    wg = wg_factory(ctm=ctm, number=1, name="Normalisation Appliquée")

    api.force_authenticate(ctc_user)
    first = api.post("/api/v1/norms/", _norm_payload(ctm, wg), format="json")
    assert first.status_code == 201, first.data

    second = api.post("/api/v1/norms/", _norm_payload(ctm, wg), format="json")
    assert second.status_code == 400, second.data


def test_create_version_deposits_first_version(api, ctc_user, ctm_factory, wg_factory):
    ctm = ctm_factory(number=6, name="Matériaux & Essais / Socle Commun (SC-SOCLE)")
    wg = wg_factory(ctm=ctm, number=1, name="Normalisation Appliquée")

    api.force_authenticate(ctc_user)
    created = api.post("/api/v1/norms/", _norm_payload(ctm, wg), format="json")
    assert created.status_code == 201, created.data

    norm_id = created.data["id"]
    response = api.post(
        f"/api/v1/norms/{norm_id}/create_version/",
        {"title": created.data["title"], "content": "AVANT-PROPOS\nBase de travail.", "comment": "v0.1"},
        format="json",
    )
    assert response.status_code == 201, response.data
    assert response.data["version_number"] == 1

    version = NormeVersion.all_objects.get(norme_id=norm_id, version_number=1)
    assert version.is_draft is True
    assert "AVANT-PROPOS" in version.content


def test_expert_outside_sc_cannot_create(api, user_factory, expert_factory, ctm_factory, wg_factory):
    ctm_other = ctm_factory(number=6, name="Matériaux & Essais / Socle Commun (SC-SOCLE)")
    ctm_own = ctm_factory(number=3, name="Géotechnique & Fondations (SC-GF)")
    wg = wg_factory(ctm=ctm_other, number=1, name="Normalisation Appliquée")

    user = user_factory(username="expert", email="expert@cnetp.cd", is_expert=True)
    expert = expert_factory(user=user, ctm=ctm_own)

    api.force_authenticate(user)
    response = api.post("/api/v1/norms/", _norm_payload(ctm_other, wg), format="json")

    assert response.status_code == 403, response.data
    assert not Norme.all_objects.filter(reference_number="NCD 001").exists()

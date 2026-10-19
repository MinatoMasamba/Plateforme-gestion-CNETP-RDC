"""Client externe de synchronisation des 20 brouillons NCD vers l'API Django.

Principe : l'environnement de rédaction est isolé du serveur. Ce script
s'authentifie à l'API (JWT), résout les identifiants de sous-commission (CTM)
et de groupe de travail (WG), puis transmet chaque brouillon (création de la
norme + dépôt de la première version). Il est idempotent : un brouillon déjà
enregistré (même ``reference_number``) est ignoré, jamais dupliqué.

Aucune écriture directe en base : tout passe par les endpoints REST.

Configuration (variables d'environnement) :
  NCD_API_BASE           base de l'API (défaut http://127.0.0.1:8000/api/v1)
  NCD_SERVICE_EMAIL      identifiant du compte de service (défaut service.ncd@cnetp.cd)
  NCD_SERVICE_PASSWORD   mot de passe du compte de service (requis, jamais en dur)
"""

import os
import sys

import requests

from catalogue import CATALOGUE, SOURCE

API_BASE = os.environ.get("NCD_API_BASE", "http://127.0.0.1:8000/api/v1")
EMAIL = os.environ.get("NCD_SERVICE_EMAIL", "service.ncd@cnetp.cd")
PASSWORD = os.environ.get("NCD_SERVICE_PASSWORD", "")

LOGIN_URL = f"{API_BASE}/mobile/auth/login/"
CTM_URL = f"{API_BASE}/ctm/"
WG_URL = f"{API_BASE}/wg/"
NORMS_URL = f"{API_BASE}/norms/"


def fetch_all(session, url, params=None):
    """Parcourt la pagination DRF et retourne la liste complète des résultats."""
    results = []
    page_params = dict(params or {})
    while url:
        response = session.get(url, params=page_params, timeout=30)
        response.raise_for_status()
        data = response.json()
        results.extend(data.get("results", []))
        url = data.get("next")
        page_params = {}
    return results


def authenticate():
    if not PASSWORD:
        raise SystemExit("NCD_SERVICE_PASSWORD doit être défini (compte de service API).")
    session = requests.Session()
    response = session.post(
        LOGIN_URL,
        json={
            "email": EMAIL,
            "password": PASSWORD,
            "device_id": "ncd-external-client",
            "device_type": "web",
        },
        timeout=30,
    )
    response.raise_for_status()
    access = response.json().get("access")
    if not access:
        raise SystemExit("Authentification impossible : aucun jeton d'accès reçu.")
    session.headers.update({"Authorization": f"Bearer {access}"})
    return session


def build_reference_index(session):
    """Retourne (ctm_by_number, wg_by_key) où wg_by_key = {(numéro SC, nom WG): id}."""
    ctms = fetch_all(session, CTM_URL)
    wgs = fetch_all(session, WG_URL)

    ctm_by_number = {int(ctm["number"]): ctm["id"] for ctm in ctms}

    wg_by_key = {}
    for wg in wgs:
        ctm = wg.get("ctm") or {}
        number = ctm.get("number")
        if number is not None:
            wg_by_key[(int(number), wg["name"])] = wg["id"]
    return ctm_by_number, wg_by_key


def norm_exists(session, code):
    data = fetch_all(session, NORMS_URL, {"search": code})
    for row in data:
        if row.get("reference_number") == code:
            return row["id"]
    return None


def create_norm(session, entry, ctm_id, wg_id):
    payload = {
        "reference_number": entry["code"],
        "title": entry["title"],
        "description": entry["description"],
        "source_reference": SOURCE,
        "standard_family": "NCD",
        "norm_type": "NCD",
        "category": entry["category"],
        "iso_reference": entry.get("iso_reference", ""),
        "arso_reference": "",
        "tags": entry.get("tags", ""),
        "ctm": ctm_id,
        "wg": wg_id,
    }
    response = session.post(NORMS_URL, json=payload, timeout=30)
    if response.status_code in (400, 422):
        return None, response.json()
    response.raise_for_status()
    return response.json(), None


def create_version(session, norm_id, entry):
    payload = {
        "title": entry["title"],
        "content": entry["content"],
        "comment": "Première version du brouillon (base de travail pour les experts).",
    }
    response = session.post(
        f"{NORMS_URL}{norm_id}/create_version/",
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def main():
    session = authenticate()
    ctm_by_number, wg_by_key = build_reference_index(session)

    report = {"created": [], "skipped": [], "errors": []}
    for entry in CATALOGUE:
        code = entry["code"]
        sc_number = entry["sc_number"]
        wg_name = entry["wg_name"]

        ctm_id = ctm_by_number.get(sc_number)
        wg_id = wg_by_key.get((sc_number, wg_name))
        if ctm_id is None or wg_id is None:
            report["errors"].append((code, f"SC {sc_number} ou WG « {wg_name} » introuvable."))
            continue

        existing = norm_exists(session, code)
        if existing:
            report["skipped"].append((code, existing))
            continue

        norm, error = create_norm(session, entry, ctm_id, wg_id)
        if error is not None:
            report["errors"].append((code, error))
            continue

        norm_id = norm["id"]
        version = create_version(session, norm_id, entry)
        report["created"].append((code, norm_id, version.get("version_number")))

    print("\n=== Résultat de la synchronisation ===")
    print(f"Créés   : {len(report['created'])}")
    for code, norm_id, v in report["created"]:
        print(f"  + {code} -> norme {norm_id}, version v{v}")
    print(f"Ignorés : {len(report['skipped'])} (déjà enregistrés)")
    for code, norm_id in report["skipped"]:
        print(f"  = {code} -> norme {norm_id}")
    print(f"Erreurs : {len(report['errors'])}")
    for code, err in report["errors"]:
        print(f"  ! {code} : {err}")

    if report["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

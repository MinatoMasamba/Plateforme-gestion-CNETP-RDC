"""Client externe de rédaction / synchronisation des brouillons NCD.

Principes :
  * l'environnement de rédaction est isolé du serveur ; tout passe par l'API REST ;
  * aucune écriture directe en base ;
  * opérations idempotentes (clé = ``reference_number``).

Authentification (au choix) :
  * JWT (compte de service avec email) — ``NCD_SERVICE_EMAIL`` + ``NCD_SERVICE_PASSWORD`` ;
  * session (super-utilisateur) — ``NCD_USERNAME`` + ``NCD_PASSWORD``.

Configuration (variables d'environnement) :
  NCD_API_BASE           base de l'API (défaut https://workalldomain.pythonanywhere.com/api/v1)
  NCD_USERNAME           identifiant du super-utilisateur (défaut superuser)
  NCD_PASSWORD           mot de passe du super-utilisateur (défaut superuser)
  NCD_SERVICE_EMAIL      identifiant JWT du compte de service (optionnel)
  NCD_SERVICE_PASSWORD   mot de passe JWT du compte de service (optionnel)

Commandes :
  python client.py                  # sync : créer les 20 brouillons du catalogue
  python client.py list             # lister les normes
  python client.py get <ref>        # détail + versions d'une norme
  python client.py update <ref> --title "..." --description "..." --iso-reference "..."
  python client.py add-version <ref> --content @fichier.txt --comment "motif"
"""

import argparse
import os
import sys

import requests

from catalogue import CATALOGUE, SOURCE

API_BASE = os.environ.get("NCD_API_BASE", "https://workalldomain.pythonanywhere.com/api/v1")
USERNAME = os.environ.get("NCD_USERNAME", "superuser")
PASSWORD = os.environ.get("NCD_PASSWORD", "superuser")
SERVICE_EMAIL = os.environ.get("NCD_SERVICE_EMAIL", "")
SERVICE_PASSWORD = os.environ.get("NCD_SERVICE_PASSWORD", "")

SITE_URL = API_BASE.rsplit("/api", 1)[0]

LOGIN_URL = f"{API_BASE}/auth/login/"
MOBILE_LOGIN_URL = f"{API_BASE}/mobile/auth/login/"
CTM_URL = f"{API_BASE}/ctm/"
WG_URL = f"{API_BASE}/wg/"
NORMS_URL = f"{API_BASE}/norms/"


# ── Authentification ─────────────────────────────────────────────────────────
def _jwt_session():
    if not SERVICE_EMAIL or not SERVICE_PASSWORD:
        return None
    session = requests.Session()
    response = session.post(
        MOBILE_LOGIN_URL,
        json={"email": SERVICE_EMAIL, "password": SERVICE_PASSWORD,
              "device_id": "ncd-external-client", "device_type": "web"},
        timeout=30,
    )
    response.raise_for_status()
    access = response.json().get("access")
    if not access:
        raise SystemExit("Authentification JWT impossible : aucun jeton reçu.")
    session.headers.update({"Authorization": f"Bearer {access}"})
    return session


def _session_auth():
    session = requests.Session()
    # Récupère le cookie CSRF posé par le site, requis pour les écritures.
    session.get(SITE_URL, timeout=30)
    csrf = session.cookies.get("csrftoken", "")
    response = session.post(
        LOGIN_URL,
        json={"username": USERNAME, "password": PASSWORD},
        timeout=30,
    )
    if response.status_code != 200:
        raise SystemExit(f"Connexion impossible ({response.status_code}): {response.text[:200]}")
    if csrf:
        session.headers.update({"X-CSRFToken": csrf, "Referer": SITE_URL})
    return session


def authenticate():
    session = _jwt_session() or _session_auth()
    return session


# ── Helpers API ──────────────────────────────────────────────────────────────
def fetch_all(session, url, params=None):
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


def build_reference_index(session):
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


def find_norm(session, reference):
    data = fetch_all(session, NORMS_URL, {"search": reference})
    for row in data:
        if row.get("reference_number") == reference:
            return row
    return None


def norm_id(session, reference):
    row = find_norm(session, reference)
    if not row:
        raise SystemExit(f"Norme « {reference} » introuvable.")
    return row["id"]


# ── Commandes ────────────────────────────────────────────────────────────────
def cmd_list(session, args):
    rows = fetch_all(session, NORMS_URL)
    print(f"{len(rows)} norme(s)")
    for row in rows:
        print(f"  {row.get('reference_number'):28} {row.get('status'):16} "
              f"{(row.get('title') or '')[:55]}")


def cmd_get(session, args):
    nid = norm_id(session, args.reference)
    detail = session.get(f"{NORMS_URL}{nid}/", timeout=30).json()
    print(f"Référence    : {detail.get('reference_number')}")
    print(f"Titre        : {detail.get('title')}")
    print(f"Statut       : {detail.get('status')}")
    print(f"Famille      : {detail.get('standard_family')} | type : {detail.get('norm_type')}")
    print(f"SC (CTM)     : {detail.get('ctm_name')}")
    print(f"WG           : {detail.get('wg_name')}")
    print(f"ISO          : {detail.get('iso_reference')}")
    print(f"Source       : {detail.get('source_reference')}")
    print(f"Description  : {(detail.get('description') or '')[:200]}")
    print(f"Versions     : {detail.get('version_count')}")
    latest = detail.get("latest_version")
    if latest:
        print(f"\nDernière version v{latest.get('version_number')} (brouillon: {latest.get('is_draft')}) :")
        print((latest.get('content') or '')[:1500])


def cmd_sync(session, args):
    ctm_by_number, wg_by_key = build_reference_index(session)
    report = {"created": [], "skipped": [], "errors": []}
    for entry in CATALOGUE:
        code = entry["code"]
        ctm_id = ctm_by_number.get(entry["sc_number"])
        wg_id = wg_by_key.get((entry["sc_number"], entry["wg_name"]))
        if ctm_id is None or wg_id is None:
            report["errors"].append((code, f"SC {entry['sc_number']} ou WG « {entry['wg_name']} » introuvable."))
            continue
        if find_norm(session, code):
            report["skipped"].append((code, "existe"))
            continue
        payload = {
            "reference_number": code, "title": entry["title"],
            "description": entry["description"], "source_reference": SOURCE,
            "standard_family": "NCD", "norm_type": "NCD",
            "category": entry["category"], "iso_reference": entry.get("iso_reference", ""),
            "arso_reference": "", "tags": entry.get("tags", ""),
            "ctm": ctm_id, "wg": wg_id,
        }
        response = session.post(NORMS_URL, json=payload, timeout=30)
        if response.status_code not in (200, 201):
            report["errors"].append((code, response.text[:200]))
            continue
        norm = response.json()
        vresp = session.post(f"{NORMS_URL}{norm['id']}/create_version/", json={
            "title": entry["title"], "content": entry["content"],
            "comment": "Première version du brouillon (base de travail pour les experts).",
        }, timeout=60)
        if vresp.status_code not in (200, 201):
            report["errors"].append((code, vresp.text[:200]))
            continue
        report["created"].append((code, norm["id"], vresp.json().get("version_number")))

    print(f"Créés : {len(report['created'])}")
    for code, nid, v in report["created"]:
        print(f"  + {code} -> norme {nid} v{v}")
    print(f"Ignorés : {len(report['skipped'])}")
    for code, why in report["skipped"]:
        print(f"  = {code} ({why})")
    print(f"Erreurs : {len(report['errors'])}")
    for code, err in report["errors"]:
        print(f"  ! {code} : {err}")
    if report["errors"]:
        sys.exit(1)


def cmd_update(session, args):
    nid = norm_id(session, args.reference)
    fields = {}
    if args.title:
        fields["title"] = args.title
    if args.description:
        fields["description"] = args.description
    if args.iso_reference:
        fields["iso_reference"] = args.iso_reference
    if args.tags:
        fields["tags"] = args.tags
    if not fields:
        raise SystemExit("Aucun champ à modifier (--title, --description, --iso-reference, --tags).")
    response = session.patch(f"{NORMS_URL}{nid}/", json=fields, timeout=30)
    if response.status_code not in (200, 201):
        raise SystemExit(f"Échec de la mise à jour ({response.status_code}): {response.text[:300]}")
    data = response.json()
    print(f"Mise à jour OK : {data.get('reference_number')} — {data.get('title')}")


def cmd_add_version(session, args):
    nid = norm_id(session, args.reference)
    content = args.content
    if content.startswith("@"):
        content = open(content[1:], encoding="utf-8").read()
    response = session.post(f"{NORMS_URL}{nid}/create_version/", json={
        "title": args.title or args.reference,
        "content": content,
        "comment": args.comment or "Nouvelle version.",
    }, timeout=60)
    if response.status_code not in (200, 201):
        raise SystemExit(f"Échec du dépôt de version ({response.status_code}): {response.text[:300]}")
    data = response.json()
    print(f"Version déposée : {args.reference} v{data.get('version_number')}")


# ── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Client CNE-ITP de rédaction externe.")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="lister les normes")

    p_get = sub.add_parser("get", help="détail d'une norme")
    p_get.add_argument("reference")

    p_upd = sub.add_parser("update", help="modifier une norme existante")
    p_upd.add_argument("reference")
    p_upd.add_argument("--title")
    p_upd.add_argument("--description")
    p_upd.add_argument("--iso-reference")
    p_upd.add_argument("--tags")

    p_ver = sub.add_parser("add-version", help="déposer une nouvelle version")
    p_ver.add_argument("reference")
    p_ver.add_argument("--content", required=True, help="texte brut ou @fichier.txt")
    p_ver.add_argument("--title")
    p_ver.add_argument("--comment")

    args = parser.parse_args()

    session = authenticate()
    if args.command == "list":
        cmd_list(session, args)
    elif args.command == "get":
        cmd_get(session, args)
    elif args.command == "update":
        cmd_update(session, args)
    elif args.command == "add-version":
        cmd_add_version(session, args)
    else:
        cmd_sync(session, args)


if __name__ == "__main__":
    main()

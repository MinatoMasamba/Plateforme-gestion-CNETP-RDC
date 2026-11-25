"""Client externe de création de réunion CNE-ITP.

Même principes que ``client.py`` :
  * l'environnement de rédaction est isolé du serveur ; tout passe par l'API REST ;
  * aucune écriture directe en base ;
  * authentification JWT (compte de service) ou session (super-utilisateur).

Configuration (variables d'environnement) :
  NCD_API_BASE           base de l'API (défaut https://workalldomain.pythonanywhere.com/api/v1)
  NCD_SERVICE_EMAIL      identifiant JWT du compte de service (optionnel)
  NCD_SERVICE_PASSWORD   mot de passe JWT du compte de service (optionnel)
  NCD_USERNAME           identifiant du super-utilisateur (défaut superuser)
  NCD_PASSWORD           mot de passe du super-utilisateur (défaut superuser)

Commandes :
  python create_reunion.py capabilities
  python create_reunion.py create --type CTM --titre "..." --date 2026-12-01T10:00:00+01:00 \
      --mode SALLE --ctm 1 --ordre-jour "..."

Le compte doit pouvoir planifier une réunion (staff CTC, secrétaire/rapporteur
d'un CTM/WG, ou mandat ST-V3-07 pour les types CTC/CTM/WG).
"""

import argparse
import os
import sys

import requests

API_BASE = os.environ.get("NCD_API_BASE", "https://workalldomain.pythonanywhere.com/api/v1")
USERNAME = os.environ.get("NCD_USERNAME", "superuser")
PASSWORD = os.environ.get("NCD_PASSWORD", "superuser")
SERVICE_EMAIL = os.environ.get("NCD_SERVICE_EMAIL", "")
SERVICE_PASSWORD = os.environ.get("NCD_SERVICE_PASSWORD", "")

SITE_URL = API_BASE.rsplit("/api", 1)[0]
LOGIN_URL = f"{API_BASE}/auth/login/"
MOBILE_LOGIN_URL = f"{API_BASE}/mobile/auth/login/"
REUNIONS_URL = f"{API_BASE}/reunions/"
CTM_URL = f"{API_BASE}/ctm/"
WG_URL = f"{API_BASE}/wg/"

TYPES = ("CTM", "WG", "PILOTAGE", "ASSEMBLEE", "CTC")
MODES = ("PRESENTIEL", "EXTERNE", "SALLE")


def _jwt_session():
    if not SERVICE_EMAIL or not SERVICE_PASSWORD:
        return None
    session = requests.Session()
    response = session.post(
        MOBILE_LOGIN_URL,
        json={"email": SERVICE_EMAIL, "password": SERVICE_PASSWORD,
              "device_id": "ncd-reunion-client", "device_type": "web"},
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
    session.get(SITE_URL, timeout=30)
    response = session.post(LOGIN_URL, json={"username": USERNAME, "password": PASSWORD}, timeout=30)
    if response.status_code != 200:
        raise SystemExit(f"Connexion impossible ({response.status_code}): {response.text[:200]}")
    csrf = session.cookies.get("csrftoken", "")
    if csrf:
        session.headers.update({"X-CSRFToken": csrf, "Referer": SITE_URL})
    return session


def authenticate():
    return _jwt_session() or _session_auth()


def fetch_all(session, url):
    results = []
    while url:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        results.extend(data.get("results", []))
        url = data.get("next")
    return results


def cmd_capabilities(session, args):
    response = session.get(f"{REUNIONS_URL}capabilities/", timeout=30)
    response.raise_for_status()
    data = response.json()
    print(f"Peut planifier : {data.get('can_plan')}")
    print(f"CTM autorisés  : {data.get('can_plan_ctm_ids')}")
    for ctm in data.get("ctms", []):
        print(f"  CTM {ctm['id']:>3}  {ctm['name']}")
    for wg in data.get("workgroups", []):
        print(f"  WG  {wg['id']:>3}  {wg['name']} (CTM {wg['ctm_id']})")


def cmd_create(session, args):
    if args.type not in TYPES:
        raise SystemExit(f"Type invalide « {args.type} ». Choix : {', '.join(TYPES)}.")
    if args.mode not in MODES:
        raise SystemExit(f"Mode invalide « {args.mode} ». Choix : {', '.join(MODES)}.")
    if args.type != "ASSEMBLEE" and not args.ctm and not args.wg:
        raise SystemExit("Indiquer au moins --ctm ou --wg (sauf pour ASSEMBLEE).")

    payload = {
        "type": args.type,
        "titre": args.titre,
        "date": args.date,
        "mode": args.mode,
        "description": args.description or "",
        "ordre_jour": args.ordre_jour or "",
        "lieu": args.lieu or "",
        "lien_reunion_virtuelle": args.lien or "",
        "document_reglementaire": args.document or "",
        "enregistrement_actif": not args.no_record,
        "consentement_enregistrement": args.consent,
    }
    if args.ctm:
        payload["ctm"] = args.ctm
    if args.wg:
        payload["wg"] = args.wg

    response = session.post(REUNIONS_URL, json=payload, timeout=180)
    if response.status_code not in (200, 201):
        raise SystemExit(f"Échec de la création ({response.status_code}): {response.text[:500]}")
    data = response.json()
    print("Réunion créée :")
    print(f"  id       : {data.get('id')}")
    print(f"  titre    : {data.get('titre')}")
    print(f"  type     : {data.get('type')}")
    print(f"  date     : {data.get('date')}")
    print(f"  mode     : {data.get('mode')}")
    print(f"  statut   : {data.get('status')}")
    print(f"  salle    : {data.get('room_name')}")


def main():
    parser = argparse.ArgumentParser(description="Client CNE-ITP de création de réunion.")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("capabilities", help="vérifier les droits de planification")

    p_create = sub.add_parser("create", help="créer une réunion")
    p_create.add_argument("--type", required=True, choices=TYPES)
    p_create.add_argument("--titre", required=True)
    p_create.add_argument("--date", required=True, help="ISO 8601, ex. 2026-12-01T10:00:00+01:00")
    p_create.add_argument("--mode", default="PRESENTIEL", choices=MODES)
    p_create.add_argument("--ctm", type=int)
    p_create.add_argument("--wg", type=int)
    p_create.add_argument("--lieu")
    p_create.add_argument("--lien", help="lien visio (mode EXTERNE)")
    p_create.add_argument("--description")
    p_create.add_argument("--ordre-jour")
    p_create.add_argument("--document", help="document réglementaire de référence")
    p_create.add_argument("--no-record", action="store_true", help="désactiver l'enregistrement")
    p_create.add_argument("--consent", action="store_true", help="consentement à l'enregistrement")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(2)

    session = authenticate()
    if args.command == "capabilities":
        cmd_capabilities(session, args)
    else:
        cmd_create(session, args)


if __name__ == "__main__":
    main()

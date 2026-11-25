"""Vérifier la configuration LiveKit (locale et distante).

Usage :
  python scripts/livekit_status.py
  python scripts/livekit_status.py --site https://workalldomain.pythonanywhere.com

Lecture :
  * local  : présence des variables LIVEKIT_* dans l'environnement / .env ;
  * distant: POST vide sur le webhook LiveKit. 503 = non configuré,
             401 = configuré (signature refusée), 200 = configuré.
"""

import argparse
import os
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
KEYS = ("LIVEKIT_URL", "LIVEKIT_API_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET")


def load_env(path):
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def mask(value):
    return f"{value[:4]}…{value[-2:]}" if len(value) > 6 else ("<set>" if value else "<vide>")


def main():
    parser = argparse.ArgumentParser(description="État de la configuration LiveKit.")
    parser.add_argument("--site", default="https://workalldomain.pythonanywhere.com")
    args = parser.parse_args()

    env = {**load_env(ROOT / ".env"), **os.environ}
    configured = all(env.get(key) for key in KEYS)
    print("== Local ==")
    for key in KEYS:
        print(f"  {key:18} {mask(env.get(key, ''))}")
    print(f"  is_configured      {configured}")

    url = args.site.rstrip("/") + "/api/v1/meetings/livekit/webhook/"
    print(f"\n== Distant ({args.site}) ==")
    try:
        response = requests.post(url, json={}, timeout=25)
        status = response.status_code
        detail = ""
        try:
            detail = response.json().get("detail", "")
        except ValueError:
            pass
        if status == 503:
            verdict = "NON configuré (503)"
        elif status in (200, 400, 401, 403):
            verdict = f"configuré (HTTP {status})"
        else:
            verdict = f"réponse inattendue (HTTP {status})"
        print(f"  {verdict}")
        if detail:
            print(f"  detail: {detail}")
    except requests.RequestException as exc:
        print(f"  erreur réseau : {exc}")


if __name__ == "__main__":
    main()

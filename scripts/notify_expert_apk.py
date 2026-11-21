"""Campagne autorisée : lien APK par email, puis WhatsApp en repli.

Coordonnées et journal détaillé restent privés ; seul le bilan est public.
Les envois Gmail sont effectués par le connecteur et leurs résultats consignés.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import requests
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from remote_expert_distribution import BASE, form_defaults, get_page, session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RELEASE = json.loads((ROOT / 'reports/expert_beta/remote_release.json').read_text())
RELEASE_VERSION = RELEASE.get('version', '1.0.0-beta.1+2')
CAMPAIGN = f'expert-apk-{RELEASE_VERSION}'
STATE = ROOT / f'.private_build/apk_notifications_{RELEASE_VERSION}.json'
SUBJECT = 'CNE-ITP — application Expert Android : version bêta allégée'
URL = RELEASE['download_url']
SIZE = f"{RELEASE['bytes'] / 1000000:.1f}".replace('.', ',')
HTML = f'''<p>Bonjour,</p>
<p>La version bêta Android de l’application <strong>CNE-ITP Expert</strong> est disponible pour test.</p>
<p><a href="{URL}">Télécharger l’APK Android</a><br>{URL}</p>
<p>Connectez-vous avec votre compte CNE-ITP habituel pour télécharger le fichier ({SIZE} Mo, Android 7.0 minimum). Un seul APK convient aux téléphones ARM 32 et 64 bits.</p>
<p>Les nouvelles fonctions Réunions ne sont pas encore activées.</p>
<p>Plateforme CNE-ITP</p>'''
TEXT = (f'Bonjour,\nLa version bêta Android CNE-ITP Expert est disponible pour test.\n'
        f'Télécharger : {URL}\nConnectez-vous avec votre compte CNE-ITP habituel. '
        f'APK unique ARM 32/64 bits : {SIZE} Mo, Android 7.0 minimum.\nLes nouvelles fonctions Réunions ne sont pas encore activées.\nPlateforme CNE-ITP')


def load():
    return json.loads(STATE.read_text())


def save(data):
    data['updated_at'] = datetime.now(timezone.utc).isoformat()
    fd = os.open(STATE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
    counts = Counter(row['status'] for row in data['recipients'])
    summary = {'campaign': CAMPAIGN, 'total_accounts': len(data['recipients']),
               'statuses': dict(counts), 'updated_at': data['updated_at'],
               'unique_emails_accepted': len({row['email'].casefold() for row in data['recipients'] if row['status'] == 'EMAIL_ACCEPTED'}),
               'gmail_messages_accepted': len({row['gmail_id'] for row in data['recipients'] if row.get('gmail_id') and row['status'] == 'EMAIL_ACCEPTED'}),
               'download_url': URL, 'apk_megabytes': SIZE}
    (ROOT / 'reports/expert_beta/apk_notification_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def valid_email(value):
    value = (value or '').strip()
    try:
        validate_email(value)
        return value
    except ValidationError:
        return None


def normalize_phone(value):
    value = (value or '').strip().removeprefix('whatsapp:')
    if not value or re.search(r'[^0-9+() .-]', value):
        return None
    value = re.sub(r'[() .-]', '', value)
    if value.startswith('00'):
        value = '+' + value[2:]
    elif re.fullmatch(r'0[89]\d{8}', value):
        value = '+243' + value[1:]
    elif re.fullmatch(r'[89]\d{8}', value):
        value = '+243' + value
    elif re.fullmatch(r'243\d{9}', value):
        value = '+' + value
    return value if re.fullmatch(r'\+[1-9]\d{7,14}', value) else None


def rows(client, path):
    url = BASE + path
    output = []
    while url:
        if not url.startswith(BASE + '/'):
            raise RuntimeError('Pagination inattendue.')
        response = client.get(url, timeout=60)
        response.raise_for_status()
        body = response.json()
        output.extend(body.get('results', []) if isinstance(body, dict) else body)
        url = body.get('next') if isinstance(body, dict) else None
    return output


def prepare():
    client = session()
    experts = [item for item in rows(client, '/api/v1/experts/?status=ACTIVE&page_size=100') if item.get('status') == 'ACTIVE']
    users = {str(item['id']): item for item in rows(client, '/api/v1/users/?page_size=100')}
    release = json.loads((ROOT / 'reports/expert_beta/remote_release.json').read_text())
    _, page = get_page(client, f"/admin/appstore/appversion/{release['version_id']}/change/")
    allowed = set(form_defaults(page)['beta_testers'])
    previous = load() if STATE.exists() else {'campaign': CAMPAIGN, 'subject': SUBJECT, 'url': URL, 'recipients': []}
    existing = {str(row['user_id']): row for row in previous['recipients']}
    planned = []
    for expert in experts:
        user = expert.get('user')
        identifier = str(user.get('id') if isinstance(user, dict) else (expert.get('user_id') or user))
        user = users.get(identifier, user if isinstance(user, dict) else {})
        if identifier in existing:
            planned.append(existing[identifier])
            continue
        email = valid_email(user.get('email'))
        phone = normalize_phone(expert.get('whatsapp_number') or user.get('phone'))
        row = {'user_id': int(identifier), 'expert_id': expert['id'],
               'email': (user.get('email') or '').strip(), 'phone': phone,
               'status': 'EMAIL_READY' if email else ('WHATSAPP_READY' if phone else 'NO_VALID_CONTACT')}
        if identifier not in allowed:
            row['status'] = 'NO_BETA_ACCESS'
        planned.append(row)
    previous['recipients'] = planned
    summary = save(previous)
    summary['unique_valid_email_addresses'] = len({row['email'].casefold() for row in planned if row['status'] == 'EMAIL_READY'})
    summary['unique_whatsapp_fallback_numbers'] = len({row['phone'] for row in planned if row['status'] == 'WHATSAPP_READY'})
    print(json.dumps(summary, ensure_ascii=False))


def email_batch(limit):
    data = load()
    groups = {}
    accepted = {row['email'].casefold(): row for row in data['recipients'] if row['status'] == 'EMAIL_ACCEPTED'}
    for row in data['recipients']:
        if row['status'] != 'EMAIL_READY':
            continue
        address = row['email'].casefold()
        if address in accepted:
            row.update(status='EMAIL_ACCEPTED', gmail_id=accepted[address]['gmail_id'], deduplicated=True)
            continue
        groups.setdefault(address, []).append(row)
    result = []
    for address, group in list(groups.items())[:limit]:
        for row in group:
            row['status'] = 'EMAIL_SENDING'
        result.append({'key': address, 'to': group[0]['email'], 'subject': SUBJECT, 'html': HTML,
                       'user_ids': [row['user_id'] for row in group]})
    save(data)
    print(json.dumps(result, ensure_ascii=False))


def record_results(results):
    data = load()
    for result in results:
        ids = set(result['user_ids'])
        for row in data['recipients']:
            if row['user_id'] not in ids:
                continue
            row['status'] = result['status']
            for field in ('gmail_id', 'error'):
                if field in result:
                    row[field] = result[field]
    print(json.dumps(save(data), ensure_ascii=False))


def whatsapp_fallback():
    """Envoi réel, sans simulation ; ne jamais renvoyer un statut ambigu."""
    from config import settings
    import time

    if not all((settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_WHATSAPP_FROM)):
        raise RuntimeError('Configuration WhatsApp manquante.')
    data = load()
    endpoint = f'https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json'
    auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    sender = 'whatsapp:' + settings.TWILIO_WHATSAPP_FROM.removeprefix('whatsapp:')
    groups = {}
    for row in data['recipients']:
        if row['status'] == 'WHATSAPP_READY' and row.get('phone'):
            groups.setdefault(row['phone'], []).append(row)
    for phone, group in groups.items():
        for row in group:
            row['status'] = 'WHATSAPP_SENDING'
        save(data)
        try:
            response = requests.post(endpoint, auth=auth, data={'From': sender, 'To': 'whatsapp:' + phone, 'Body': TEXT}, timeout=45)
            result = response.json()
        except (requests.RequestException, ValueError):
            for row in group:
                row.update(status='WHATSAPP_UNCONFIRMED', error='Résultat réseau ambigu : vérifier le fournisseur avant toute relance.')
            save(data)
            break
        for row in group:
            row['whatsapp_code'] = result.get('error_code') or result.get('code')
            if response.status_code == 201 and result.get('sid'):
                row.update(status='WHATSAPP_ACCEPTED', whatsapp_sid=result['sid'], whatsapp_provider_status=result.get('status'))
            else:
                row.update(status='WHATSAPP_REJECTED', error=f"Fournisseur HTTP {response.status_code}, code {result.get('code')}")
        save(data)
        if response.status_code != 201:
            if response.status_code in (401, 403, 429):
                break
            continue
        for _ in range(3):
            time.sleep(3)
            try:
                check = requests.get(endpoint.removesuffix('.json') + '/' + result['sid'] + '.json', auth=auth, timeout=20)
                check.raise_for_status()
                outcome = check.json()
            except (requests.RequestException, ValueError):
                break
            for row in group:
                row['whatsapp_provider_status'] = outcome.get('status')
                row['whatsapp_code'] = outcome.get('error_code')
                if outcome.get('status') in ('failed', 'undelivered'):
                    row['status'] = 'WHATSAPP_FAILED'
                elif outcome.get('status') in ('delivered', 'read'):
                    row['status'] = 'WHATSAPP_DELIVERED'
            save(data)
            if outcome.get('status') in ('failed', 'undelivered', 'delivered', 'read'):
                break
    summary = save(data)
    summary['whatsapp_provider_codes'] = dict(Counter(str(row['whatsapp_code']) for row in data['recipients'] if row.get('whatsapp_code')))
    print(json.dumps(summary, ensure_ascii=False))


def domain_audit():
    data = load()
    domains = {row['email'].rsplit('@', 1)[1].casefold() for row in data['recipients'] if row['status'] == 'EMAIL_READY'}

    def check(domain):
        try:
            result = requests.get('https://dns.google/resolve', params={'name': domain, 'type': 'MX'}, timeout=15).json()
            if result.get('Status') == 3:
                return domain, 'INVALID_DOMAIN'
            if result.get('Status') != 0:
                return domain, 'UNCONFIRMED'
            entries = [item['data'] for item in result.get('Answer', []) if item.get('type') == 15]
            if entries:
                return domain, 'INVALID_DOMAIN' if all(re.fullmatch(r'\d+\s+\.', item) for item in entries) else 'MX_PRESENT'
            # SMTP autorise un domaine sans MX si une adresse IP est publiée.
            for kind, record_type in [('A', 1), ('AAAA', 28)]:
                address = requests.get('https://dns.google/resolve', params={'name': domain, 'type': kind}, timeout=15).json()
                if any(item.get('type') == record_type for item in address.get('Answer', [])):
                    return domain, 'IMPLICIT_MX'
            return domain, 'UNCONFIRMED'
        except (requests.RequestException, ValueError):
            return domain, 'UNCONFIRMED'

    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = dict(pool.map(check, domains))
    for row in data['recipients']:
        if row['status'] != 'EMAIL_READY':
            continue
        row['email_domain_status'] = outcomes[row['email'].rsplit('@', 1)[1].casefold()]
        if row['email_domain_status'] == 'INVALID_DOMAIN':
            row['status'] = 'WHATSAPP_READY' if row['phone'] else 'NO_VALID_CONTACT'
            row['error'] = 'Domaine email inexistant ou déclarant ne pas recevoir de courrier.'
    summary = save(data)
    summary['domain_checks'] = dict(Counter(outcomes.values()))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'prepare-and-audit', 'email-batch', 'record', 'summary', 'audit-domains', 'whatsapp-fallback'])
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--results-json')
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
    elif args.command == 'prepare-and-audit':
        prepare()
        domain_audit()
    elif args.command == 'email-batch':
        email_batch(args.limit)
    elif args.command == 'record':
        record_results(json.loads(args.results_json))
    elif args.command == 'audit-domains':
        domain_audit()
    elif args.command == 'whatsapp-fallback':
        whatsapp_fallback()
    else:
        print(json.dumps(save(load()), ensure_ascii=False))

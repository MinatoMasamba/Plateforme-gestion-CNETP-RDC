import json
import os
import re
import requests
from django.conf import settings
from django.utils import timezone
from .models import Draft


def _load_local_env_vars():
    env_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    if not os.path.exists(env_path):
        return {}

    values = {}
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key in {'GEMINI_API_URL', 'GEMINI_API_KEY'} and value:
                    values[key] = value
    except OSError:
        return {}
    return values


def _get_gemini_config():
    env_vars = _load_local_env_vars()
    
    # Récupération propre de la clé (on cherche d'abord la clé principale)
    api_key = (
        getattr(settings, 'GEMINI_API_KEY', None) or 
        os.environ.get('GEMINI_API_KEY') or 
        env_vars.get('GEMINI_API_KEY') or
        getattr(settings, 'GEMINI_API_KEY2', None) or # Fallback sur la clé 2
        env_vars.get('GEMINI_API_KEY2')
    )
    
    # On force la récupération du modèle Gemma s'il est mal configuré ailleurs
    model = getattr(settings, 'GEMINI_MODEL', None) or os.environ.get('GEMINI_MODEL') or env_vars.get('GEMINI_MODEL')
    
    # Sécurité : si l'environnement renvoie un modèle Gemini par erreur, on le force sur Gemma
    if not model or 'gemini' in model.lower():
        model = 'gemma-4-31b-it'

    return {
        'api_url': getattr(settings, 'GEMINI_API_URL', None) or os.environ.get('GEMINI_API_URL') or env_vars.get('GEMINI_API_URL'),
        'api_key': api_key,
        'model': model,
    }


def _build_gemini_request_url(api_url: str | None, api_key: str | None = None, model: str | None = None) -> str:
    """Construit l'URL de génération Gemini à partir d'une URL de base ou d'un endpoint complet."""
    base_url = (api_url or '').strip()
    if not base_url:
        return ''

    model_name = (model or '').strip() or 'gemma-4-31b-it'
    normalized_base = base_url.rstrip('/')

    if re.search(r'/models/[^/]+(?::generateContent)?$', normalized_base, re.IGNORECASE):
        request_url = normalized_base
        if not request_url.endswith(':generateContent'):
            request_url = f'{request_url}:generateContent'
    else:
        request_url = f'{normalized_base}/models/{model_name}:generateContent'

    if api_key and '?key=' not in request_url and '&key=' not in request_url:
        separator = '&' if '?' in request_url else '?'
        request_url = f'{request_url}{separator}key={api_key}'

    return request_url


def get_governance_structure() -> list[dict]:
    """Récupère la structure complète CTM/WG depuis la base."""
    from apps.governance.models import CTM, WG
    
    ctm_list = []
    for ctm in CTM.objects.all().order_by('number'):
        wg_list = []
        for wg in WG.objects.filter(ctm=ctm).order_by('number'):
            wg_list.append({
                'name': wg.name,
                'number': wg.number,
                'description': (wg.description or '').strip(),
                'label': f"WG {ctm.number}.{wg.number} - {wg.name}",
            })
        ctm_list.append({
            'name': ctm.name,
            'number': ctm.number,
            'description': (ctm.description or '').strip(),
            'wgs': wg_list,
        })
    return ctm_list


def get_governance_structure_text() -> str:
    """Retourne une représentation texte lisible de la structure CTM/WG."""
    structure = get_governance_structure()
    lines = []
    for ctm in structure:
        lines.append(f"CTM {ctm['number']}: {ctm['name']}")
        lines.append(f"  Description: {ctm['description']}")
        for wg in ctm['wgs']:
            lines.append(f"  - {wg['label']}")
            lines.append(f"    Description: {wg['description']}")
        lines.append("")
    return "\n".join(lines)


def build_classification_prompt(domain: str, draft_type: str, content: str, data: dict | None) -> str:
    """Construit le prompt complet avec la structure CTM/WG pour classification automatique."""
    structure_text = get_governance_structure_text()
    
    # Instructions spécifiques selon le type de document
    type_instructions = {
        'guide': """Rédige un GUIDE PRATIQUE ET NORMATIF à destination du WG sélectionné.
        Structure à respecter:
        1. Introduction et objectifs du guide
        2. Champ d'application
        3. Principes généraux et définitions
        4. Procédures et méthodes recommandées
        5. Obligations réglementaires et conformité
        6. Exemples concrets et cas d'usage
        7. Références utiles""",
        
        'norme': """Rédige une NORME NORMATIVE FORMELLE (style document officiel).
        Structure à respecter:
        1. Titre et numéro de référence
        2. Préambule et objectifs
        3. Champ d'application
        4. Références normatives
        5. Termes et définitions
        6. Exigences normatives détaillées
        7. Méthodes d'essai et de contrôle
        8. Annexes (si nécessaires)""",
        
        'norme_fictive': """Rédige une NORME FICTIVE (brouillon de travail) pour tests et discussion.
        Structure à respecter:
        1. Titre provisoire
        2. Objectifs du document de travail
        3. Propositions techniques
        4. Points de discussion
        5. Questions ouvertes pour le groupe
        Marque clairement toutes les sections comme DRAFT ou PROVISOIRE.""",
        
        'directive': """Rédige une DIRECTIVE TECHNIQUE opérationnelle.
        Structure:
        1. Objet et champ d'application
        2. Définitions et abréviations
        3. Responsabilités
        4. Procédures détaillées
        5. Documents associés
        6. Dispositions transitoires""",
        
        'recommandation': """Rédige des RECOMMANDATIONS TECHNIQUES.
        Structure:
        1. Contexte et justification
        2. Recommandations principales
        3. Mise en œuvre
        4. Suivi et évaluation"""
    }
    
    instructions = type_instructions.get(draft_type, type_instructions['guide'])
    
    prompt = f"""Tu es l'assistant IA de la Commission Nationale d'Élaboration des Normes Techniques de Construction (CNETP).

## OBJECTIF PRINCIPAL
Analyse le contenu textuel fourni par l'utilisateur et DÉTERMINE AUTOMATIQUEMENT quel CTM (Comité Technique Miroir) et quel WG (Groupe de Travail) est le plus approprié pour recevoir ce document.

## STRUCTURE COMPLÈTE DES CTM ET WG DE LA CNETP
Voici la liste exhaustive de tous les CTM et WG existants avec leurs descriptions :

{structure_text}

## RÈGLES DE CLASSIFICATION IMPÉRATIVES
1. Tu DOIS choisir UN SEUL CTM et UN SEUL WG parmi ceux listés ci-dessus.
2. Le choix doit être basé UNIQUEMENT sur le contenu textuel fourni.
3. Analyse les mots-clés, le domaine technique, et le contexte général.
4. Si le contenu concerne plusieurs WG, choisis le PLUS PERTINENT.
5. Justifie TOUJOURS ton choix dans la raison de classification.

## INFORMATIONS FOURNIES PAR L'UTILISATEUR
- Domaine d'application: {domain or 'non précisé'}
- Type de document demandé: {draft_type}
- Contenu textuel à analyser:
---
{content or 'Aucun contenu textuel fourni'}
---

- Données JSON complémentaires:
{json.dumps(data or {}, ensure_ascii=False, indent=2)}

## TYPE DE DOCUMENT À GÉNÉRER
{draft_type.upper()} - {instructions}

## FORMAT DE RÉPONSE OBLIGATOIRE
Tu DOIS retourner UNIQUEMENT un objet JSON valide avec la structure suivante:
{{
    "ctm": "Nom exact du CTM choisi (ex: CTM 8 - Sciences des Matériaux)",
    "wg": "Nom exact du WG choisi (ex: WG 8.4 - Normalisation Appliquée)",
    "classification_reason": "Explication détaillée du choix (50-100 mots)",
    "document_type": "{draft_type}",
    "draft_text": "Le texte complet du document généré selon les instructions ci-dessus"
}}

## CONSIGNES DE RÉDACTION
- Rédige en français professionnel
- Utilise un style normatif et technique
- Structure claire avec des titres et sections
- Sois précis et concret
- Adapte le contenu au WG choisi

Maintenant, analyse le contenu, choisis le WG approprié et génère le document."""
    
    return prompt


def _extract_text(body):
    """Extrait le texte d'une réponse Gemini."""
    if isinstance(body, str):
        return body
    if isinstance(body, dict):
        if 'text' in body:
            return body['text']
        if 'candidates' in body and body['candidates']:
            candidate = body['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                parts = candidate['content']['parts']
                return ''.join(p.get('text', '') for p in parts if 'text' in p)
    return json.dumps(body, ensure_ascii=False)


def call_gemini(prompt: str) -> dict:
    """Appelle l'API Gemini avec le prompt."""
    cfg = _get_gemini_config()
    api_url = cfg['api_url']
    api_key = cfg.get('api_key')
    model_name = cfg.get('model')

    if not api_url:
        return {
            'ctm': '',
            'wg': '',
            'classification_reason': 'Configuration Gemini absente',
            'document_type': 'guide',
            'draft_text': 'Configuration Gemini absente. Veuillez définir GEMINI_API_URL et GEMINI_API_KEY dans les settings Django.',
        }

    # Si la requête renvoie 403, on peut retenter avec des clés de secours GEMINI_API_KEY1..6
    from django.conf import settings
    import os
    fallback_keys = []
    for i in range(1, 7):
        name = f'GEMINI_API_KEY{i}'
        val = getattr(settings, name, None) or os.environ.get(name)
        if val:
            fallback_keys.append(val)
    # Dédupliquer et garantir que la clé principale est d'abord
    ordered_keys = [k for k in ([api_key] if api_key else []) + fallback_keys if k]

    # Format pour Gemini
    payload = {
        'contents': [{
            'parts': [{'text': prompt}]
        }],
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 8192,
        }
    }

    last_exc = None
    for key in ordered_keys or [None]:
        headers = {'Content-Type': 'application/json'}
        if key:
            headers['x-goog-api-key'] = key
            headers['Authorization'] = f'Bearer {key}'
        request_url = _build_gemini_request_url(api_url, key, model_name)
        try:
            resp = requests.post(request_url, json=payload, headers=headers, timeout=90)
            resp.raise_for_status()
            body = resp.json()
        except requests.exceptions.RequestException as e:
            last_exc = e
            # Si erreur 403, on tente la clé suivante
            status = None
            if hasattr(e, 'response') and e.response is not None:
                try:
                    status = e.response.status_code
                except Exception:
                    status = None
            if status == 403:
                # try next key
                continue
            # pour d'autres erreurs, on ne retente pas
            return {
                'ctm': '',
                'wg': '',
                'classification_reason': f'Erreur API Gemini: {str(e)}',
                'document_type': 'guide',
                'draft_text': f'Erreur lors de l\'appel à l\'API Gemini: {str(e)}',
            }

        text = _extract_text(body)

        # Essayer de parser le JSON
        try:
            # Nettoyer le texte (enlever les backticks et le markdown)
            clean_text = re.sub(r'```json\s*', '', text)
            clean_text = re.sub(r'```\s*', '', clean_text)
            parsed = json.loads(clean_text.strip())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as e:
            # Si le parsing échoue, on essaie de trouver du JSON dans le texte
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    if isinstance(parsed, dict):
                        return parsed
                except:
                    pass
            # Fallback: créer un objet avec le texte brut
            return {
                'ctm': '',
                'wg': '',
                'classification_reason': 'Réponse non structurée',
                'document_type': 'guide',
                'draft_text': text,
            }
        except requests.exceptions.RequestException as e:
            last_exc = e
            # Si erreur 403, on tente la clé suivante
            status = None
            if hasattr(e, 'response') and e.response is not None:
                try:
                    status = e.response.status_code
                except Exception:
                    status = None
            if status == 403:
                # try next key
                continue
            # pour d'autres erreurs, on ne retente pas
            return {
                'ctm': '',
                'wg': '',
                'classification_reason': f'Erreur API Gemini: {str(e)}',
                'document_type': 'guide',
                'draft_text': f'Erreur lors de l\'appel à l\'API Gemini: {str(e)}',
            }
    # Si toutes les clés ont échoué, retourner l'erreur finale
    if last_exc is not None:
        return {
            'ctm': '',
            'wg': '',
            'classification_reason': f'Erreur API Gemini: {str(last_exc)}',
            'document_type': 'guide',
            'draft_text': f'Erreur lors de l\'appel à l\'API Gemini: {str(last_exc)}',
        }


def generate_and_save(domain: str, draft_type: str, content: str = '', data: dict | None = None) -> Draft:
    """Génère un brouillon et l'enregistre dans la base de données."""
    # Construire le prompt complet
    prompt = build_classification_prompt(domain, draft_type, content, data)
    
    # Appeler Gemini
    result = call_gemini(prompt)
    
    # Extraire les valeurs
    selected_ctm = result.get('ctm', '')
    selected_wg = result.get('wg', '')
    selected_type = result.get('document_type') or draft_type
    draft_text = result.get('draft_text', '')
    classification_reason = result.get('classification_reason', '')
    
    # Fallback si le CTM/WG n'ont pas été trouvés
    if not selected_ctm or not selected_wg:
        # Essayer de déduire depuis la structure
        structure = get_governance_structure()
        if structure and structure[0].get('wgs'):
            selected_ctm = structure[0].get('name', '')
            first_wg = structure[0].get('wgs', [{}])[0].get('label', '')
            selected_wg = first_wg
            if not classification_reason:
                classification_reason = 'Fallback automatique (aucun WG détecté par l\'IA)'
    
    # Créer l'enregistrement
    record = Draft.objects.create(
        ctm=selected_ctm,
        wg=selected_wg,
        type=selected_type,
        domain=domain or 'non précisé',
        input_json={
            'content': content,
            'data': data or {},
            'prompt': prompt[:1000],  # Garder un extrait du prompt pour audit
            'full_prompt': prompt,    # Prompt complet pour débogage
        },
        draft_text=draft_text,
        classification_reason=classification_reason,
    )
    
    return record
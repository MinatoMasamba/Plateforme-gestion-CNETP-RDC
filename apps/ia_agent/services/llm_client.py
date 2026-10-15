"""
Couche d'abstraction LLM : DeepSeek (API compatible OpenAI).

Expose une interface unifiée pour AgentRunner, indépendante du format
de stockage des messages. DeepSeek supporte le function calling (tools)
au format OpenAI : nous convertissons donc les spécifications d'outils
(name / description / input_schema) vers ce format.
"""
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, List

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

DEEPSEEK_DEFAULT_BASE_URL = 'https://api.deepseek.com'
DEEPSEEK_DEFAULT_MODEL = 'deepseek-chat'

_client = None
_client_cache_key = None


class DeepSeekError(Exception):
    """Erreur remontée par l'API DeepSeek (status HTTP + corps de réponse)."""


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class LLMResponse:
    stop_reason: str  # 'tool_use' | 'end_turn'
    text: str = ''
    tool_calls: List[ToolCall] = field(default_factory=list)
    raw_assistant_content: Any = None  # format natif OpenAI, pour l'historique en-cours de tour


class DeepSeekLLMClient:
    """Wrappeur DeepSeek via l'API REST compatible OpenAI (chat/completions)."""

    def __init__(self, api_key, model=DEEPSEEK_DEFAULT_MODEL,
                 base_url=DEEPSEEK_DEFAULT_BASE_URL, timeout=120):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip('/')
        self._timeout = timeout

    # ── Conversion des specs d'outils vers le format OpenAI ──────────────────

    @staticmethod
    def _to_openai_tools(tools_spec):
        if not tools_spec:
            return []
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema") or {"type": "object", "properties": {}},
                },
            }
            for t in tools_spec
        ]

    # ── Appel HTTP ────────────────────────────────────────────────────────────

    def _post(self, payload):
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self._timeout)
        except requests.exceptions.Timeout:
            raise DeepSeekError("timeout — la requête DeepSeek a expiré")
        except requests.exceptions.RequestException as exc:
            raise DeepSeekError(f"connection — {exc}")

        if response.status_code != 200:
            body = response.text[:500]
            raise DeepSeekError(f"DeepSeek API {response.status_code} : {body}")

        return response.json()

    # ── Parsing de la réponse ─────────────────────────────────────────────────

    @staticmethod
    def _parse_response(data):
        choices = data.get("choices") or []
        choice = choices[0] if choices else {}
        message = choice.get("message") or {}

        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            parsed = []
            raw = []
            for tc in tool_calls:
                fn = tc.get("function") or {}
                name = fn.get("name", "")
                args_str = fn.get("arguments") or "{}"
                if isinstance(args_str, str):
                    try:
                        args = json.loads(args_str)
                    except json.JSONDecodeError:
                        args = {}
                else:
                    args = args_str or {}
                parsed.append(ToolCall(id=tc.get("id") or "", name=name, input=args))
                raw.append({
                    "id": tc.get("id") or "",
                    "type": "function",
                    "function": {"name": name, "arguments": args_str},
                })
            return LLMResponse(
                stop_reason='tool_use',
                tool_calls=parsed,
                raw_assistant_content=raw,
            )

        content = message.get("content") or ""
        return LLMResponse(stop_reason='end_turn', text=content)

    # ── Interface unifiée ─────────────────────────────────────────────────────

    def complete(self, system, messages, tools_spec, force_tool=False, max_tokens=None):
        full_messages = [{"role": "system", "content": system or ""}] + list(messages)

        if max_tokens is None:
            max_tokens = getattr(settings, 'DEEPSEEK_MAX_TOKENS', 8192)

        payload = {
            "model": self._model,
            "messages": full_messages,
            "max_tokens": max_tokens,
            "temperature": getattr(settings, 'DEEPSEEK_TEMPERATURE', 0.7),
            "stream": False,
        }

        openai_tools = self._to_openai_tools(tools_spec)
        if openai_tools:
            payload["tools"] = openai_tools
            # DeepSeek ne force pas un appel d'outil ("required" non supporté) :
            # on laisse "auto" et le prompt guide l'usage des outils.
            payload["tool_choice"] = "auto"

        data = self._post(payload)
        return self._parse_response(data)

    def build_assistant_message(self, raw_content):
        """Reconstruit le message assistant (avec tool_calls) pour l'historique OpenAI."""
        return {"role": "assistant", "content": None, "tool_calls": raw_content}

    def build_tool_result_message(self, tool_results):
        """Retourne la liste des messages 'tool' à ajouter à l'historique."""
        return [
            {"role": "tool", "tool_call_id": tr["id"], "content": tr["content"]}
            for tr in tool_results
        ]


def get_llm_client(provider=None):
    """Retourne l'instance DeepSeek partagée (unique provider de la plateforme)."""
    global _client, _client_cache_key

    api_key = getattr(settings, 'DEEPSEEK_API_KEY', '') or os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key:
        return None

    model = getattr(settings, 'DEEPSEEK_MODEL', DEEPSEEK_DEFAULT_MODEL)
    base_url = getattr(settings, 'DEEPSEEK_BASE_URL', DEEPSEEK_DEFAULT_BASE_URL)
    timeout = getattr(settings, 'DEEPSEEK_TIMEOUT', 120)

    cache_key = (api_key, model, base_url, timeout)
    if _client is None or _client_cache_key != cache_key:
        _client = DeepSeekLLMClient(
            api_key=api_key,
            model=model,
            base_url=base_url,
            timeout=timeout,
        )
        _client_cache_key = cache_key

    return _client


def unavailable_message(provider=None):
    return (
        "Neronne de Source Académique AI n'est pas configuré (clé de service manquante). "
        "Merci de contacter l'administrateur."
    )


def api_error_message(exc):
    msg = str(exc)
    low = msg.lower()
    if "402" in msg or "insufficient balance" in low or "insufficient_balance" in low:
        return "Le service de Neronne de Source Académique AI a atteint sa limite de crédit. Contacte l'administrateur."
    if "429" in msg or "rate limit" in low or "quota" in low or "resource_exhausted" in low:
        return "Quota API dépassé. Attends quelques instants puis réessaie."
    if "401" in msg or "authentication" in low or "invalid api key" in low or "invalid_api_key" in low or "unauthenticated" in low:
        return "Le service de Neronne de Source Académique AI est momentanément mal configuré. Contacte l'administrateur."
    if "peer closed" in low or "overloaded" in low or "529" in msg or "503" in msg or "500" in msg:
        return "Neronne de Source Académique AI est momentanément indisponible ou saturé. Réessaie dans quelques instants."
    if "timeout" in low or "timed out" in low:
        return "La requête a expiré. Réessaie dans un instant."
    return f"Erreur lors de la communication avec Neronne de Source Académique AI : {msg[:250]}"

"""
Couche d'abstraction LLM : Anthropic (Claude) et Google (Gemini).
Expose une interface unifiée pour AgentRunner, indépendante du provider.
"""
import logging
from dataclasses import dataclass, field
from typing import Any, List

logger = logging.getLogger(__name__)

_anthropic_client = None
_gemini_client = None
_gemini_client_cache_key = None


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
    raw_assistant_content: Any = None  # format natif du provider, pour l'historique en-cours de tour


class AnthropicLLMClient:
    """Wrappeur Claude via le SDK Anthropic."""

    def __init__(self, client, model):
        self._client = client
        self._model = model

    def complete(self, system, messages, tools_spec, force_tool=False):
        kwargs = {}
        if force_tool and tools_spec:
            kwargs['tool_choice'] = {"type": "any"}

        response = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=system,
            messages=messages,
            tools=tools_spec,
            **kwargs,
        )

        if response.stop_reason != "tool_use":
            text = "".join(b.text for b in response.content if b.type == "text")
            return LLMResponse(stop_reason='end_turn', text=text)

        tool_calls = [
            ToolCall(id=b.id, name=b.name, input=b.input)
            for b in response.content
            if b.type == "tool_use"
        ]
        return LLMResponse(
            stop_reason='tool_use',
            tool_calls=tool_calls,
            raw_assistant_content=[b.model_dump() for b in response.content],
        )

    def build_assistant_message(self, raw_content):
        return {"role": "assistant", "content": raw_content}

    def build_tool_result_message(self, tool_results):
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tr["id"],
                    "content": tr["content"],
                }
                for tr in tool_results
            ],
        }


# Modèles Gemini à essayer en séquence en cas d'échec du modèle principal
GEMINI_FALLBACK_MODELS = [
    'gemini-3.1-pro-preview',
    'gemini-3-flash-preview',
    'gemini-2.5-pro',
    'gemini-3.1-flash-lite',
    'gemini-3.5-flash',
    'gemma-4-31b-it',
    'gemma-4-26b-a4b-it',
]


# Ancienne constante de clés de secours (vide par défaut).
# Préférence : définir GEMINI_API_KEY1..6 dans l'environnement ou GEMINI_FALLBACK_API_KEYS en settings.
GEMINI_FALLBACK_API_KEYS = []




class GeminiLLMClient:
    """Wrappeur Gemini via google-genai SDK, avec fallback automatique sur les modèles et les clés API."""

    def __init__(self, client, model, fallback_models=None, api_keys=None, client_factory=None):
        self._client = client
        self._model = model
        self._fallback_models = fallback_models or GEMINI_FALLBACK_MODELS
        self._api_keys = api_keys or []
        self._client_factory = client_factory

    def _to_gemini_tools(self, tools_spec):
        if not tools_spec:
            return []
        return [{
            "function_declarations": [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                }
                for t in tools_spec
            ]
        }]

    def _to_gemini_contents(self, messages):
        """Convertit les messages mixtes (Anthropic-style texte + Gemini-style tool) en contents Gemini."""
        result = []
        for msg in messages:
            if "parts" in msg:
                result.append(msg)
            else:
                role = "model" if msg["role"] == "assistant" else "user"
                text = msg.get("content") or " "
                result.append({"role": role, "parts": [{"text": text}]})
        return result

    def _get_client_for_key(self, api_key):
        if self._client_factory is not None:
            return self._client_factory(api_key)
        return self._client

    def _call_model(self, model, contents, config, client=None):
        active_client = client or self._client
        return active_client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

    def _parse_response(self, response):
        candidate = response.candidates[0]
        parts = candidate.content.parts if candidate.content else []

        # Exclure les parts de raisonnement interne (thought=True) — Gemini thinking models
        visible_parts = [p for p in parts if not getattr(p, 'thought', False)]

        fc_parts = [
            p for p in visible_parts
            if getattr(p, 'function_call', None) and getattr(p.function_call, 'name', None)
        ]

        if fc_parts:
            tool_calls = [
                ToolCall(
                    id=f"gemini_{i}_{p.function_call.name}",
                    name=p.function_call.name,
                    input={k: v for k, v in (p.function_call.args or {}).items()},
                )
                for i, p in enumerate(fc_parts)
            ]
            raw = [
                {"function_call": {"name": p.function_call.name, "args": dict(p.function_call.args or {})}}
                for p in fc_parts
            ]
            return LLMResponse(stop_reason='tool_use', tool_calls=tool_calls, raw_assistant_content=raw)

        text = "".join(p.text for p in visible_parts if getattr(p, 'text', None))
        return LLMResponse(stop_reason='end_turn', text=text)

    def complete(self, system, messages, tools_spec, force_tool=False):
        contents = self._to_gemini_contents(messages)
        gemini_tools = self._to_gemini_tools(tools_spec)

        config = {"system_instruction": system}
        if gemini_tools:
            config["tools"] = gemini_tools
            if force_tool:
                config["tool_config"] = {"function_calling_config": {"mode": "ANY"}}

        models_to_try = [self._model] + [
            m for m in self._fallback_models if m != self._model
        ]
        api_keys_to_try = [key for key in self._api_keys if key] or [None]
        last_exc = None
        for model in models_to_try:
            for api_key in api_keys_to_try:
                try:
                    client = self._get_client_for_key(api_key) if api_key is not None else self._client
                    response = self._call_model(model, contents, config, client=client)
                    return self._parse_response(response)
                except Exception as exc:
                    logger.warning(
                        "Gemini — modèle %s indisponible avec la clé %s : %s — essai du suivant",
                        model,
                        api_key or '<default>',
                        exc,
                    )
                    last_exc = exc

        raise last_exc

    def build_assistant_message(self, raw_content):
        return {"role": "model", "parts": raw_content}

    def build_tool_result_message(self, tool_results):
        return {
            "role": "user",
            "parts": [
                {
                    "function_response": {
                        "name": tr["name"],
                        "response": {"result": tr["content"]},
                    }
                }
                for tr in tool_results
            ],
        }


def get_llm_client(provider):
    """Retourne l'instance Gemini, quel que soit le provider demandé."""
    global _anthropic_client, _gemini_client, _gemini_client_cache_key
    from django.conf import settings

    # Forcer le fournisseur Gemini pour toute l'IA de la plateforme.
    provider_name = str(provider or 'gemini').strip().lower()
    if 'claude' in provider_name or provider_name in {'anthropic', 'claude_code', 'claude-code'}:
        provider_name = 'gemini'

    if provider_name == 'gemini':
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            return None

        # Support either a single list `GEMINI_FALLBACK_API_KEYS` in settings
        # or a set of individual env/settings variables GEMINI_API_KEY1..GEMINI_API_KEY6.
        fallback_api_keys = getattr(settings, 'GEMINI_FALLBACK_API_KEYS', None)
        if fallback_api_keys is None:
            # Collect GEMINI_API_KEY1..6 from settings first, then from environment
            import os
            keys = []
            for i in range(1, 7):
                name = f'GEMINI_API_KEY{i}'
                val = getattr(settings, name, None)
                if not val:
                    val = os.environ.get(name)
                if val:
                    keys.append(val)
            # Fallback to the older constant if nothing else provided
            fallback_api_keys = keys or [k for k in GEMINI_FALLBACK_API_KEYS if k]
        else:
            if isinstance(fallback_api_keys, str):
                fallback_api_keys = [item.strip() for item in fallback_api_keys.split(',') if item.strip()]

        ordered_api_keys = [api_key] + [key for key in (fallback_api_keys or []) if key and key != api_key]
        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash')
        cache_key = (api_key, model_name, tuple(ordered_api_keys))

        if _gemini_client is None or _gemini_client_cache_key != cache_key:
            from google import genai

            def build_client(key):
                return genai.Client(api_key=key)

            _gemini_client = GeminiLLMClient(
                client=build_client(api_key),
                model=model_name,
                api_keys=ordered_api_keys,
                client_factory=build_client,
            )
            _gemini_client_cache_key = cache_key
        return _gemini_client

    # Toute autre valeur est ignorée au profit de Gemini.
    return None


def unavailable_message(provider):
    if provider == 'gemini':
        return (
            "L'agent Gemini n'est pas configuré (clé GEMINI_API_KEY manquante). "
            "Merci de contacter l'administrateur."
        )
    return (
        "L'agent Claude n'est pas configuré (clé ANTHROPIC_API_KEY manquante). "
        "Merci de contacter l'administrateur."
    )


def api_error_message(exc):
    msg = str(exc)
    low = msg.lower()
    if "credit balance is too low" in msg or ("billing" in low and "anthropic" in low):
        return "Solde de crédits Anthropic insuffisant — recharge sur console.anthropic.com → Plans & Billing."
    if "quota" in low or "resource_exhausted" in low or "429" in msg:
        return "Quota API dépassé. Attends quelques instants puis réessaie."
    if "401" in msg or "authentication" in low or "api_key_invalid" in low or "unauthenticated" in low:
        return "Clé API invalide ou expirée. Vérifie la configuration ANTHROPIC_API_KEY / GEMINI_API_KEY."
    if "peer closed" in low or "complete message body" in low or "overloaded" in low or "529" in msg or "503" in msg:
        return "Le service IA est momentanément indisponible ou saturé. Réessaie dans quelques instants."
    if "timeout" in low:
        return "La requête a expiré. Réessaie dans un instant."
    return f"Erreur lors de la communication avec l'IA : {msg[:250]}"

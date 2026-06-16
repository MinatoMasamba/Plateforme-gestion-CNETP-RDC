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


class GeminiLLMClient:
    """Wrappeur Gemini via google-genai SDK, avec fallback automatique sur la liste de modèles."""

    def __init__(self, client, model, fallback_models=None):
        self._client = client
        self._model = model
        self._fallback_models = fallback_models or GEMINI_FALLBACK_MODELS

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

    def _call_model(self, model, contents, config):
        return self._client.models.generate_content(
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
        last_exc = None
        for model in models_to_try:
            try:
                response = self._call_model(model, contents, config)
                return self._parse_response(response)
            except Exception as exc:
                logger.warning("Gemini — modèle %s indisponible : %s — essai du suivant", model, exc)
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
    """Retourne l'instance LLM pour le provider demandé, ou None si non configuré."""
    global _anthropic_client, _gemini_client
    from django.conf import settings

    if provider == 'gemini':
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            return None
        if _gemini_client is None:
            from google import genai
            _gemini_client = GeminiLLMClient(
                client=genai.Client(api_key=api_key),
                model=getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash'),
            )
        return _gemini_client

    else:  # 'anthropic' (défaut)
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
        if not api_key:
            return None
        if _anthropic_client is None:
            import anthropic
            _anthropic_client = AnthropicLLMClient(
                client=anthropic.Anthropic(api_key=api_key),
                model=getattr(settings, 'ANTHROPIC_MODEL', 'claude-sonnet-4-5'),
            )
        return _anthropic_client


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
    if "overloaded" in low or "529" in msg or "503" in msg:
        return "Les serveurs IA sont temporairement surchargés. Réessaie dans quelques instants."
    if "timeout" in low:
        return "La requête a expiré. Réessaie dans un instant."
    return f"Erreur lors de la communication avec l'IA : {msg[:250]}"

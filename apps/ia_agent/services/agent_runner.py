import json
import logging

from django.conf import settings

from ..models import AgentMessage
from ..tools import anthropic_tool_specs, get_tool
from .anthropic_client import get_client
from .prompts import build_system_prompt

logger = logging.getLogger(__name__)

UNAVAILABLE_MESSAGE = (
    "L'agent IA n'est pas configuré sur cette plateforme (clé ANTHROPIC_API_KEY "
    "manquante). Merci de contacter l'administrateur."
)

ITERATION_LIMIT_MESSAGE = (
    "Désolé, je n'ai pas réussi à terminer cette tâche dans le nombre d'étapes "
    "autorisées. Peux-tu reformuler ou préciser ta demande ?"
)


class AgentRunner:
    """Exécute un tour de conversation avec l'agent IA pour une session donnée."""

    def __init__(self, session):
        self.session = session

    def run_turn(self, user_text):
        AgentMessage.objects.create(session=self.session, role='user', content=user_text)

        client = get_client()
        if client is None:
            return AgentMessage.objects.create(
                session=self.session, role='assistant', content=UNAVAILABLE_MESSAGE,
            )

        system_prompt = build_system_prompt(self.session)
        tools = anthropic_tool_specs(self.session.scope)
        messages = self._build_message_history()

        for _ in range(settings.IA_AGENT_MAX_TOOL_ITERATIONS):
            response = client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=2048,
                system=system_prompt,
                messages=messages,
                tools=tools,
            )

            if response.stop_reason != "tool_use":
                text = "".join(
                    block.text for block in response.content if block.type == "text"
                )
                return AgentMessage.objects.create(
                    session=self.session, role='assistant', content=text,
                )

            messages.append({
                "role": "assistant",
                "content": [block.model_dump() for block in response.content],
            })

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                output = self._execute_tool(block.name, block.input)

                AgentMessage.objects.create(
                    session=self.session,
                    role='tool',
                    tool_name=block.name,
                    tool_input=block.input,
                    tool_output=output,
                )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(output, default=str, ensure_ascii=False),
                })

            messages.append({"role": "user", "content": tool_results})

        return AgentMessage.objects.create(
            session=self.session, role='assistant', content=ITERATION_LIMIT_MESSAGE,
        )

    def _execute_tool(self, name, tool_input):
        tool_spec = get_tool(name)
        if tool_spec is None or self.session.scope not in tool_spec["scopes"]:
            return {"error": f"Outil '{name}' non disponible pour ce contexte."}

        try:
            return tool_spec["handler"](session=self.session, **tool_input)
        except Exception as exc:
            logger.exception("Erreur lors de l'exécution du tool %s", name)
            return {"error": str(exc)}

    def _build_message_history(self):
        """Reconstruit l'historique Anthropic à partir des tours précédents (texte uniquement)."""
        messages = []
        for msg in self.session.messages.filter(role__in=['user', 'assistant']).order_by('created_at'):
            messages.append({"role": msg.role, "content": msg.content})
        return messages

import json
import logging

from django.conf import settings
from django.utils.timezone import localtime, now

from ..models import AgentMessage
from ..tools import anthropic_tool_specs, get_tool
from .llm_client import api_error_message, get_llm_client, unavailable_message

logger = logging.getLogger(__name__)

ITERATION_LIMIT_MESSAGE = (
    "Désolé, je n'ai pas réussi à terminer cette tâche dans le nombre d'étapes "
    "autorisées. Peux-tu reformuler ou préciser ta demande ?"
)

# ─── Logging coloré terminal ─────────────────────────────────────────────────

_C = {
    'R': '\033[0m',   'B': '\033[1m',   'D': '\033[2m',
    'red': '\033[31m', 'green': '\033[32m', 'yellow': '\033[33m',
    'blue': '\033[34m', 'magenta': '\033[35m', 'cyan': '\033[36m',
    'white': '\033[37m',
}


def _cl(color: str, symbol: str, label: str, detail: str = '') -> None:
    """Log coloré dans le terminal (uniquement si DEBUG=True)."""
    if not getattr(settings, 'DEBUG', False):
        return
    c = _C.get(color, '')
    r, b, d = _C['R'], _C['B'], _C['D']
    det = f"\n        {d}{detail[:300]}{r}" if detail else ''
    print(f"{c}{b}[IA]{r} {c}{symbol}  {label}{r}{det}", flush=True)


# ─── Titres et instructions de greeting ──────────────────────────────────────

_GREETING_TITLES = {
    'expert':   'Analyse dossier expert',
    'ctc':      'Analyse chevauchements CTC',
    'pilotage': 'Tableau de bord Pilotage',
}


def _build_greeting_instruction(scope: str, expert=None) -> str:
    if scope == 'expert':
        if expert:
            return (
                "Effectue une analyse préliminaire de fond AVANT de saluer l'utilisateur. "
                f"1. Appelle get_expert_dossier avec expert_id={expert.id} pour charger son dossier complet. "
                "2. Appelle list_wg_options pour lister les groupes de travail disponibles. "
                "Ensuite, présente-toi brièvement, résume les points clés du dossier "
                "(affectations CTM/WG, spécialités, statut de validation), signale tout "
                "groupe de travail pertinent non encore attribué, et propose des actions "
                "concrètes. Termine en demandant quelle action entreprendre. "
                "Réponds en Markdown structuré, 4-6 phrases max."
            )
        return (
            "Présente-toi brièvement en tant qu'assistant IA CNETP. Indique que tu peux "
            "consulter les dossiers experts et groupes de travail. "
            "Demande quel travail effectuer. 3-4 phrases max."
        )
    if scope == 'ctc':
        return (
            "Effectue une analyse préliminaire de fond AVANT de saluer l'utilisateur. "
            "1. Appelle detect_wg_overlap sans filtre CTM pour détecter les chevauchements "
            "potentiels entre groupes de travail sur l'ensemble des CTM. "
            "Ensuite, présente-toi brièvement en une phrase, résume les chevauchements les "
            "plus significatifs (CTM concernés, paires WG, mots-clés partagés), signale les "
            "cas les plus critiques, et demande quel aspect approfondir. "
            "Réponds en Markdown, 4-6 phrases max."
        )
    if scope == 'pilotage':
        return (
            "Effectue une analyse préliminaire de fond AVANT de saluer l'utilisateur. "
            "Appelle successivement ces outils : "
            "1. get_chart_data(metric='normes_by_status') — état d'avancement des normes. "
            "2. get_chart_data(metric='normes_by_ctm') — répartition par CTM. "
            "3. get_chart_data(metric='votes_participation') — participation aux votes. "
            "4. get_chart_data(metric='experts_by_structure') — experts par structure. "
            "5. detect_wg_overlap() — chevauchements inter-WG. "
            "Ensuite, présente-toi brièvement en une phrase au Comité de Pilotage, fournis "
            "un résumé analytique des métriques clés (chiffres importants, tendances, points "
            "d'attention), signale les chevauchements les plus critiques avec leurs CTM/WG "
            "concernés, et propose 3 axes d'approfondissement prioritaires. "
            "Réponds en Markdown structuré avec titres (##) et listes."
        )
    return "Présente-toi et demande quel travail d'analyse tu dois effectuer."


# ─── Runner ──────────────────────────────────────────────────────────────────

class AgentRunner:
    """Exécute un tour de conversation avec l'agent IA pour une session donnée."""

    def __init__(self, session):
        self.session = session

    # ── Tour normal (déclenché par un message utilisateur) ────────────────────

    def run_turn(self, user_text: str):
        s = self.session
        _cl('magenta', '▶', f"Nouveau tour  scope={s.scope}  user={s.user}  provider={s.provider}")
        _cl('cyan', '💬', "Message utilisateur", user_text[:300])

        # Nommer la session avec le premier message utilisateur
        self._set_title_from_message(user_text)

        AgentMessage.objects.create(session=s, role='user', content=user_text)

        llm = get_llm_client(s.provider)
        if llm is None:
            _cl('red', '✗', f"LLM indisponible — {s.provider}")
            return AgentMessage.objects.create(
                session=s, role='assistant',
                content=unavailable_message(s.provider),
            )

        system_prompt = self._build_system_prompt()
        tools_spec   = self._get_tools_spec()
        messages     = self._build_message_history()

        _cl('blue', '⚙', (
            f"Prompt : {len(system_prompt)} car. | "
            f"Outils : {len(tools_spec)} | "
            f"Historique : {len(messages)} msgs"
        ))

        return self._run_loop(llm, system_prompt, messages, tools_spec)

    # ── Analyse de fond au démarrage de session ───────────────────────────────

    def run_greeting(self):
        """Analyse préliminaire + accueil automatique — aucun message utilisateur persisté."""
        s = self.session
        _cl('magenta', '★', f"Analyse de fond  scope={s.scope}  provider={s.provider}")

        llm = get_llm_client(s.provider)
        if llm is None:
            _cl('red', '✗', f"LLM indisponible pour greeting — {s.provider}")
            return None

        from .permissions import get_expert_for_user
        expert = get_expert_for_user(s.user)

        system_prompt = self._build_system_prompt()
        tools_spec    = self._get_tools_spec()
        instruction   = _build_greeting_instruction(s.scope, expert)

        _cl('blue', '⚙', f"Outils disponibles : {[t['name'] for t in tools_spec]}")

        # Nommer la session avec le type d'analyse
        self._set_greeting_title()

        messages = [{"role": "user", "content": instruction}]
        return self._run_loop(llm, system_prompt, messages, tools_spec, force_first_tool=bool(tools_spec))

    # ── Boucle tool-use commune ───────────────────────────────────────────────

    def _build_fallback_error_message(self, exc):
        msg = str(exc).lower()
        if any(token in msg for token in [
            'quota', 'resource_exhausted', '429', 'rate_limit', 'unavailable',
            '503', 'peer closed', 'timeout', 'timed out', 'connection',
        ]):
            return (
                "Le service IA est momentanément indisponible ou saturé. "
                "Merci de réessayer dans quelques instants."
            )
        return api_error_message(exc)

    def _run_loop(self, llm, system_prompt, messages, tools_spec, force_first_tool=False):
        max_iter = settings.IA_AGENT_MAX_TOOL_ITERATIONS

        for iteration in range(max_iter):
            force = force_first_tool and iteration == 0
            _cl('blue', f'[{iteration + 1}/{max_iter}]', f"Appel LLM ({self.session.provider}){' [force_tool]' if force else ''}…")

            try:
                response = llm.complete(system_prompt, messages, tools_spec, force_tool=force)
            except Exception as exc:
                _cl('red', '✗', f"Erreur API ({self.session.provider})", str(exc))
                logger.error("Erreur API LLM (%s) : %s", self.session.provider, exc)
                return AgentMessage.objects.create(
                    session=self.session, role='assistant',
                    content=self._build_fallback_error_message(exc),
                )

            _cl('blue', '←', (
                f"stop_reason={response.stop_reason}  "
                f"texte={len(response.text or '')} car.  "
                f"tool_calls={len(response.tool_calls)}"
            ))

            if response.stop_reason != 'tool_use':
                _cl('green', '✓', "Réponse finale", (response.text or '')[:200])
                return AgentMessage.objects.create(
                    session=self.session, role='assistant', content=response.text,
                )

            messages.append(llm.build_assistant_message(response.raw_assistant_content))

            tool_results = []
            for tc in response.tool_calls:
                _cl('yellow', '⚡', f"Outil  →  {tc.name}", json.dumps(tc.input, ensure_ascii=False)[:200])

                output     = self._execute_tool(tc.name, tc.input)
                output_str = json.dumps(output, default=str, ensure_ascii=False)

                if 'error' in output:
                    _cl('red', '✗', f"{tc.name}  →  ERREUR", output_str[:200])
                else:
                    _cl('green', '✓', f"{tc.name}  →  OK", output_str[:200])

                AgentMessage.objects.create(
                    session=self.session, role='tool',
                    tool_name=tc.name, tool_input=tc.input, tool_output=output,
                )
                tool_results.append({
                    "id": tc.id,
                    "name": tc.name,
                    "content": output_str,
                })

            messages.append(llm.build_tool_result_message(tool_results))

        _cl('red', '!', f"Limite d'itérations atteinte ({max_iter})")
        return AgentMessage.objects.create(
            session=self.session, role='assistant', content=ITERATION_LIMIT_MESSAGE,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_system_prompt(self):
        from .prompts import build_system_prompt
        return build_system_prompt(self.session)

    def _get_tools_spec(self):
        from .prompts import get_scope_config
        all_tools = anthropic_tool_specs(self.session.scope)
        config = get_scope_config(self.session)
        if config and config.allowed_tools is not None:
            allowed = set(config.allowed_tools)
            return [t for t in all_tools if t['name'] in allowed]
        return all_tools

    def _execute_tool(self, name: str, tool_input: dict):
        tool_spec = get_tool(name)
        if tool_spec is None or self.session.scope not in tool_spec["scopes"]:
            return {"error": f"Outil '{name}' non disponible pour ce contexte."}
        try:
            return tool_spec["handler"](session=self.session, **tool_input)
        except Exception as exc:
            logger.exception("Erreur lors de l'exécution du tool %s", name)
            return {"error": str(exc)}

    def _build_message_history(self):
        """Historique user/assistant uniquement (sans traces tool) — format Anthropic-style."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.session.messages.filter(
                role__in=['user', 'assistant']
            ).order_by('created_at')
        ]

    def _set_title_from_message(self, user_text: str) -> None:
        """Nomme la session avec le premier message utilisateur si pas encore de titre."""
        if self.session.title:
            return
        raw = user_text.strip().replace('\n', ' ')
        title = raw[:55] + ('…' if len(raw) > 55 else '')
        self.session.title = title
        self.session.save(update_fields=['title', 'updated_at'])
        _cl('cyan', '🏷', f"Session nommée : {title}")

    def _set_greeting_title(self) -> None:
        """Nomme la session avec le type d'analyse préliminaire et la date/heure."""
        if self.session.title:
            return
        label = _GREETING_TITLES.get(self.session.scope, 'Analyse IA')
        date_str = localtime(now()).strftime('%d/%m %H:%M')
        title = f"{label} — {date_str}"
        self.session.title = title
        self.session.save(update_fields=['title', 'updated_at'])
        _cl('cyan', '🏷', f"Session nommée : {title}")

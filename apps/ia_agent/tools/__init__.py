"""Registre des outils (tools) exposés à l'agent IA, scopés par contexte d'usage."""

TOOL_REGISTRY = {}


def register(name, description, input_schema, scopes):
    """Décorateur enregistrant une fonction Python comme tool Claude."""

    def decorator(func):
        TOOL_REGISTRY[name] = {
            "description": description,
            "input_schema": input_schema,
            "scopes": set(scopes),
            "handler": func,
        }
        return func

    return decorator


def tools_for_scope(scope):
    return {name: spec for name, spec in TOOL_REGISTRY.items() if scope in spec["scopes"]}


def anthropic_tool_specs(scope):
    return [
        {
            "name": name,
            "description": spec["description"],
            "input_schema": spec["input_schema"],
        }
        for name, spec in tools_for_scope(scope).items()
    ]


def get_tool(name):
    return TOOL_REGISTRY.get(name)


def load_tools():
    """Importe tous les modules de tools pour déclencher les @register au démarrage."""
    from . import chart_tools  # noqa: F401
    from . import email_tools  # noqa: F401
    from . import expert_tools  # noqa: F401
    from . import governance_tools  # noqa: F401
    from . import public_inquiry_tools  # noqa: F401
    from . import referential_tools  # noqa: F401

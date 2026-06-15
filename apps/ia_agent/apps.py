from django.apps import AppConfig


class IaAgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ia_agent'
    verbose_name = "Agent IA"

    def ready(self):
        from .tools import load_tools
        load_tools()

from django.apps import AppConfig


class GovernanceConfig(AppConfig):
    name = 'apps.governance'

    def ready(self):
        from . import nomination_notifications  # noqa: F401

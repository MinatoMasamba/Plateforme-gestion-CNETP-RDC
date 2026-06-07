from django.apps import AppConfig


class NormsConfig(AppConfig):
    name = 'apps.norms'

    def ready(self):
        import apps.norms.signals  # noqa: F401

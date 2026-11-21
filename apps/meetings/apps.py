from django.apps import AppConfig


class MeetingsConfig(AppConfig):
    name = 'apps.meetings'

    def ready(self):
        from . import signals  # noqa: F401

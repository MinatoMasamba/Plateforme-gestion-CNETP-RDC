from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    verbose_name = 'Tableau de bord'

    def ready(self):
        from django.db.models.signals import post_migrate

        from .console_permissions import sync_console_group

        post_migrate.connect(
            sync_console_group,
            dispatch_uid='dashboard.sync_console_group',
        )

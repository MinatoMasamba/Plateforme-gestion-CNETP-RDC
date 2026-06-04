from django.apps import AppConfig


class MobileappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mobileapp'
    
    def ready(self):
        """Enregistrer les signaux au démarrage de l'app"""
        import apps.mobileapp.signals


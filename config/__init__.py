"""Point d'entrée du package config.

Importe l'application Celery au démarrage de Django afin que les tâches
partagées soient toujours enregistrées (convention Django/Celery).
"""
from .celery import app as celery_app

__all__ = ('celery_app',)

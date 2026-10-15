from django.db import models


class LegacyNormeManager(models.Manager):
    """Les contrats historiques CTM/WG ne reçoivent pas les dossiers Phoenix."""
    def get_queryset(self):
        return super().get_queryset().filter(circuit_version='LEGACY')


class LegacyVersionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(norme__circuit_version='LEGACY')

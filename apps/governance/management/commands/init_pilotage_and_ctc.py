"""
Management command to initialize Comité de Pilotage and Cellule Technique
Creates the structure entries (without assigning experts yet)
"""

from django.core.management.base import BaseCommand
from apps.governance.models import ComitePilotage, TechnicalCell


class Command(BaseCommand):
    help = 'Initialize Comité de Pilotage and Cellule Technique de Coordination structures'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("""
╔════════════════════════════════════════════════════════════════════════════╗
║  INITIALISATION DES ORGANES DE DIRECTION CNETP                            ║
║  Comité de Pilotage & Cellule Technique de Coordination                   ║
╚════════════════════════════════════════════════════════════════════════════╝
        """))
        
        self._create_pilotage()
        self._create_technical_cell()
        
        self.stdout.write(self.style.SUCCESS("\n✅ Initialisation terminée!\n"))

    def _create_pilotage(self):
        """Create Comité de Pilotage Élargi"""
        self.stdout.write(self.style.SUCCESS("\n=== COMITÉ DE PILOTAGE ÉLARGI ===\n"))
        
        pilotage, created = ComitePilotage.objects.get_or_create(
            name="Comité de Pilotage Élargi CNETP",
            defaults={
                'name': "Comité de Pilotage Élargi CNETP"
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS("""
✅ Comité de Pilotage créé

Structure (27 postes):
  
  ▸ Bureau Directoire (5 postes)
    • Président
    • Vice-Président
    • Secrétaire Général
    • Trésorier
    • Rapporteur Général
  
  ▸ Collège des Conseillers Institutionnels et Politiques (12 postes)
    • Représentants gouvernementaux (4)
    • Représentants ministériels (4)
    • Représentants institutionnels (4)
  
  ▸ Collège des Administrateurs Techniques et Financiers (5 postes)
    • Experts administratifs
    • Administrateurs financiers
    • Coordinateurs techniques
  
  ▸ Collège des Partenaires Sectoriels et de la Société Civile (5 postes)
    • Représentants sectoriels
    • Organisations de la société civile
    • Partenaires techniques

📝 Note: Les membres seront assignés ultérieurement basé sur les experts disponibles.
            """))
        else:
            self.stdout.write(f"⚠️  Comité de Pilotage existant: {pilotage.name}")
        
        return pilotage

    def _create_technical_cell(self):
        """Create Cellule Technique de Coordination"""
        self.stdout.write(self.style.SUCCESS("\n=== CELLULE TECHNIQUE DE COORDINATION (CTC) ===\n"))
        
        ctc, created = TechnicalCell.objects.get_or_create(
            name="Cellule Technique de Coordination CNETP",
            defaults={
                'name': "Cellule Technique de Coordination CNETP"
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS("""
✅ Cellule Technique créée

Structure (20 postes):
  
  ▸ Direction des Opérations (3 postes)
    • Directeur des Opérations
    • Coordinateur Général
    • Chef de Projet
  
  ▸ Pôle d'Analyse et d'Ingénierie Documentaire (7 postes)
    • Analyste Normatif Principal
    • Spécialistes Documentaires (3)
    • Ingénieurs en Ingénierie Documentaire (3)
  
  ▸ Pôle Logistique, Communication et Relations Extérieures (4 postes)
    • Responsable Logistique
    • Responsable Communication
    • Chargé de Relations Extérieures
    • Assistant Logistique
  
  ▸ Bureau d'Appui Technique et Numérique (6 postes)
    • Responsable IT
    • Développeurs (2)
    • Administrateur Système
    • Responsable Sécurité Informatique
    • Webmaster

📝 Note: Les membres seront assignés ultérieurement basé sur les experts disponibles.
            """))
        else:
            self.stdout.write(f"⚠️  Cellule Technique existante: {ctc.name}")
        
        return ctc

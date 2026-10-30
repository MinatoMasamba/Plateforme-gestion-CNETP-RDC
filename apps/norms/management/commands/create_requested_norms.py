"""Complète les références demandées qui manquent dans la base racine."""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.governance.models import OrganisationVersion, Organe, RattachementDocumentaire, WG
from apps.norms.models import Norme, NormeVersion
from .convert_requested_norms_to_legacy import PROJECT_GROUPS


PROJECTS = (
    ('NCD 003', 'Échantillonnage et identification des matériaux de construction', 'SC-SOCLE',
     'Prélèvement, étiquetage, transport et conservation des échantillons de matériaux.',
     'Chaque prélèvement doit être relié à un lot, un lieu, une date, un opérateur et une méthode de prélèvement.',
     'Contrôler la continuité de la chaîne de garde et la concordance entre étiquette, fiche et rapport d’essai.'),
    ('NCD 004', 'Exigences de traçabilité des essais en laboratoire', 'SC-SOCLE',
     'Enregistrements des essais réalisés pour les infrastructures et travaux publics.',
     'Le dossier d’essai doit relier l’échantillon, l’instrument, son étalonnage, l’opérateur, la méthode et le résultat.',
     'Reconstituer un résultat depuis le rapport final jusqu’aux données brutes et aux contrôles de l’instrument.'),
    ('NCD 104', 'Exigences techniques des plateformes ferroviaires', 'SC-IT',
     'Conception et contrôle des plateformes recevant une infrastructure ferroviaire.',
     'Les hypothèses de charge, de sol, de drainage et d’entretien doivent être explicites et cohérentes entre les pièces.',
     'Comparer les profils, coupes, données géotechniques et notes de calcul du même tronçon.'),
    ('NCD 105', 'Drainage des routes et ouvrages de franchissement', 'SC-IT',
     'Collecte, transfert et évacuation des eaux affectant les routes et ouvrages de franchissement.',
     'Chaque bassin contributif, dispositif et exutoire doit être identifié avec ses hypothèses hydrologiques.',
     'Vérifier la continuité hydraulique entre les plans, calculs, ouvrages prévus et points de rejet.'),
    ('NCD 204', 'Conception et contrôle des fondations superficielles', 'SC-GF',
     'Choix, dimensionnement et réception des fondations superficielles.',
     'Les charges, caractéristiques du sol, niveau d’assise et vérifications de tassement doivent être documentés.',
     'Rapprocher la reconnaissance de sol, la note de calcul et les contrôles réalisés pendant l’exécution.'),
    ('NCD 302', 'Gestion technique des réseaux d’assainissement', 'SC-OH',
     'Inventaire, exploitation, inspection et maintenance des réseaux d’assainissement.',
     'Chaque tronçon doit avoir une référence stable, un état constaté, une intervention et une responsabilité de suivi.',
     'Confronter plans, fiches d’inspection, incidents et registre des interventions.'),
    ('NCD 401', 'Réseaux de voirie et espaces publics urbains', 'SC-VRD',
     'Coordination des réseaux, cheminements et équipements implantés dans les emprises urbaines.',
     'Les plans doivent identifier les conflits d’emprise, accès de maintenance et interfaces entre gestionnaires.',
     'Superposer les plans des réseaux et documenter chaque conflit avant approbation du tracé.'),
    ('NCD 603', 'Entretien préventif des bâtiments administratifs', 'SC-BAT',
     'Inventaire, inspection périodique et entretien des bâtiments administratifs.',
     'Chaque équipement doit avoir un identifiant, un état, une fréquence de contrôle à approuver et un historique d’intervention.',
     'Comparer le programme d’entretien aux fiches de visite et aux preuves de travaux exécutés.'),
)


def initial_content(ref, title, scope, requirement, control):
    return f'''# {ref} — {title}
Version 1 · Projet de travail à examiner par la sous-commission compétente

## 1. Objet
Le présent projet définit les informations et les contrôles nécessaires pour {scope[0].lower() + scope[1:]}

## 2. Domaine d’application
La sous-commission doit préciser les catégories d’ouvrages, de matériaux ou de prestations couvertes, ainsi que les cas exclus. Une exigence ne devient applicable qu’après identification de son objet, de son responsable et de sa méthode de vérification. Les cas particuliers seront traités dans une annexe ou une décision documentée.

## 3. Références
Le groupe de travail établira la liste datée des textes et documents applicables. Leur édition, leur disponibilité et leur portée juridique doivent être vérifiées avant citation dans une version soumise. Aucune référence externe n’est présumée adoptée dans ce projet.

## 4. Termes et définitions
Les termes techniques utilisés dans les prescriptions devront être définis une seule fois. Chaque définition doit être cohérente avec les plans, formulaires et rapports associés. Les abréviations seront explicitées lors de leur première occurrence.

## 5. Exigences générales
{requirement} La traçabilité doit permettre de retrouver la pièce source, la personne qui a effectué le contrôle, la date du constat et la suite donnée à un écart. Toute dérogation devra être motivée et soumise à l’autorité compétente dans le circuit applicable.

## 6. Dossier technique attendu
Le dossier comprendra l’identification du projet, les hypothèses, les plans ou fiches nécessaires, les méthodes retenues, les résultats et les réserves. Les annexes doivent porter une référence et une version. Une pièce absente sera signalée comme telle ; elle ne sera pas remplacée par une conclusion supposée.

## 7. Méthode de vérification
{control} Le contrôleur consigne l’échantillon ou le périmètre examiné, les pièces consultées, la méthode employée, les résultats et les écarts. La vérification est reproductible à partir des données conservées. Si les données ne permettent pas de conclure, le dossier est retourné pour complément.

## 8. Critères de conformité
La sous-commission doit définir les critères mesurables et leur justification technique. Les seuils chiffrés, tolérances et fréquences de contrôle restent à établir sur une base documentaire vérifiée. Le rapport de contrôle distingue conforme, non conforme et indéterminé, avec la preuve associée à chaque conclusion.

## 9. Responsabilités
Le rédacteur fournit les hypothèses et pièces sources. Le vérificateur décrit les contrôles réalisés. Le responsable de la sous-commission consolide les observations et soumet les points non résolus selon le circuit habilité. Le suivi des corrections conserve la version examinée et la réponse apportée.

## 10. Enregistrements
Les fiches, plans, résultats, observations, réponses et décisions sont conservés avec leur auteur réel, leur date et leur version. Le classement doit permettre de relier un résultat à la prescription qui l’a motivé et à la décision qui a suivi.

## 11. Annexes à préparer
Le groupe de travail préparera les formulaires de contrôle, tableaux de résultats et exemples de pièces nécessaires au domaine couvert. Leur contenu sera validé avant utilisation opérationnelle.

## 12. Historique
V1 : ouverture du projet et définition du contenu à instruire. Les révisions suivantes seront créées seulement après contributions, contrôles et décisions effectivement enregistrés.
'''


class Command(BaseCommand):
    help = 'Crée les huit projets NCD absents, sans inventer de validation ni auteur.'

    def handle(self, *args, **options):
        db = Path(str(settings.DATABASES['default']['NAME'])).resolve()
        if db != (Path(settings.BASE_DIR) / 'db.sqlite3').resolve():
            raise CommandError('La commande doit utiliser db.sqlite3 à la racine.')
        created = []
        with transaction.atomic():
            for ref, title, sc_code, scope, requirement, control in PROJECTS:
                if Norme.all_objects.filter(reference_number=ref).exists():
                    continue
                ctm_number, wg_number = PROJECT_GROUPS[ref]
                wg = WG.objects.get(ctm__number=ctm_number, number=wg_number)
                norme = Norme.all_objects.create(reference_number=ref, title=title,
                    description=f'{scope} {requirement}', status='DRAFT', circuit_version='LEGACY',
                    ctm=wg.ctm, wg=wg,
                    source_reference='Demande de préparation du 28 octobre 2026')
                NormeVersion.all_objects.create(norme=norme, version_number=1,
                    title=f'{ref} — avant-projet',
                    content=initial_content(ref, title, scope, requirement, control),
                    summary='Première version de travail ; examen de la sous-commission requis.',
                    is_draft=True)
                version_code = 'reorganisation-2026-10-15' if sc_code == 'SC-VRD' else 'phoenix-2026-10'
                version = OrganisationVersion.objects.get(code=version_code)
                sc = Organe.objects.get(version=version, type='SC', code=sc_code)
                RattachementDocumentaire.objects.create(norme=norme, version=version, sc=sc,
                    role='OWNER', status='PROPOSED')
                created.append(ref)
        self.stdout.write(f'{len(created)} projets créés en brouillon : {", ".join(created) if created else "aucun"}.')

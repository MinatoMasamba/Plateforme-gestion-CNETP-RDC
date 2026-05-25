#!/usr/bin/env python
"""
Script de création des 8 Comités Techniques Miroirs (CTM)
Basé sur le Manuel Organisationnel CNETP 2026

Structure:
- 8 CTM au total (153 experts)
- 7 CTM à 19 experts
- 1 CTM à 20 experts (SC8)
- Chaque CTM a 3-4 Groupes de Travail (WG)
"""

import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.governance.models import CTM, WG
from django.utils import timezone

# Données des 8 CTM selon le manuel organisationnel CNETP
CTM_DATA = [
    {
        'number': 1,
        'name': 'Géotechnique et Risques Naturels',
        'description': 'Reconnaissance des sols, géomécanique, fondations, stabilité des talus, prévention des risques sismiques et d\'inondation',
        'iso_reference': 'ISO/TC 58',
        'arso_reference': 'ARSO/TC 3',
        'effectif': 19,
        'missions': [
            'Établir les normes de reconnaissance géotechnique',
            'Définir les critères de stabilité des talus',
            'Évaluer les risques sismiques et naturels',
            'Harmoniser les pratiques de fondation'
        ],
        'wg': [
            {'number': 1, 'name': 'Sols & Géomécanique', 'description': 'Caractérisation des sols tropicaux et ferrallitiques'},
            {'number': 2, 'name': 'Risques Naturels', 'description': 'Prévention et adaptation aux aléas naturels'},
            {'number': 3, 'name': 'Fondations', 'description': 'Conception et exécution des systèmes de fondation'},
        ]
    },
    {
        'number': 2,
        'name': 'Ouvrages d\'Art',
        'description': 'Ponts, viaducs, barrages, calcul mécanique des structures, dimensionnement des éléments',
        'iso_reference': 'ISO/TC 167',
        'arso_reference': 'ARSO/TC 4',
        'effectif': 19,
        'missions': [
            'Standardiser la conception des ponts et viaducs',
            'Établir les normes de dimensionnement structural',
            'Définir les règles de calcul mécanique',
            'Harmoniser les pratiques de conception d\'ouvrages d\'art'
        ],
        'wg': [
            {'number': 1, 'name': 'Ponts et Viaducs', 'description': 'Conception, dimensionnement et exécution des ponts'},
            {'number': 2, 'name': 'Barrages & Structures Hydrauliques', 'description': 'Conception et stabilité des grands ouvrages hydrauliques'},
            {'number': 3, 'name': 'Calcul Mécanique', 'description': 'Méthodes et outils de calcul des structures'},
        ]
    },
    {
        'number': 3,
        'name': 'Bâtiment, Urbanisme et Transition Numérique',
        'description': 'Conception structurelle, sécurité incendie, performance énergétique, BIM et numérisation',
        'iso_reference': 'ISO/TC 163',
        'arso_reference': 'ARSO/TC 5',
        'effectif': 19,
        'missions': [
            'Établir les normes de conception structurelle des bâtiments',
            'Définir les standards de sécurité incendie',
            'Optimiser la performance énergétique',
            'Développer les standards BIM et de numérisation'
        ],
        'wg': [
            {'number': 1, 'name': 'Structures Bâtiment', 'description': 'Conception et dimensionnement des structures'},
            {'number': 2, 'name': 'Sécurité Incendie & Performance Énergétique', 'description': 'Prévention incendie et efficacité énergétique'},
            {'number': 3, 'name': 'BIM & Numérisation', 'description': 'Maquette numérique, interopérabilité et standards numériques (ISO 19650)'},
        ]
    },
    {
        'number': 4,
        'name': 'Aéroports et Transport Aérien',
        'description': 'Pistes, tarmacs, terminaux, conformité OACI (Organisation de l\'Aviation Civile Internationale)',
        'iso_reference': 'ISO/TC 190',
        'arso_reference': 'ARSO/TC 8',
        'effectif': 19,
        'missions': [
            'Adapter les normes OACI au contexte RDC',
            'Établir les standards de conception aéroportuaire',
            'Définir les critères de sécurité aéronautique',
            'Harmoniser les équipements et infrastructures'
        ],
        'wg': [
            {'number': 1, 'name': 'Infrastructure Aéroportuaire', 'description': 'Conception des pistes, tarmacs et surfaces d\'atterrissage'},
            {'number': 2, 'name': 'Terminaux et Équipements', 'description': 'Structures terminales et équipements de soutien'},
            {'number': 3, 'name': 'Conformité OACI', 'description': 'Adaptation des normes OACI et certification'},
        ]
    },
    {
        'number': 5,
        'name': 'Infrastructures de Transport Linéaire et Maritimes',
        'description': 'Routes, chemins de fer, ports; corridors de transport, chaussées, infrastructures portuaires',
        'iso_reference': 'ISO/TC 194',
        'arso_reference': 'ARSO/TC 6',
        'effectif': 19,
        'missions': [
            'Établir les normes de conception routière adaptées aux contextes tropicaux',
            'Standardiser les infrastructures ferroviaires',
            'Définir les critères de conception portuaire',
            'Harmoniser les corridors de transport régionaux'
        ],
        'wg': [
            {'number': 1, 'name': 'Ingénierie Routière', 'description': 'Conception, matériaux et dimensionnement des chaussées'},
            {'number': 2, 'name': 'Voies Ferrées', 'description': 'Infrastructure ferroviaire et standards de voie'},
            {'number': 3, 'name': 'Infrastructures Portuaires', 'description': 'Quais, bassins, équipements portuaires'},
        ]
    },
    {
        'number': 6,
        'name': 'Ressources en Eau et Hydraulique',
        'description': 'Adduction d\'eau, irrigation, forages, gestion des ressources hydriques',
        'iso_reference': 'ISO/TC 224',
        'arso_reference': 'ARSO/TC 7',
        'effectif': 19,
        'missions': [
            'Établir les normes d\'exploitation des ressources hydriques',
            'Standardiser les systèmes d\'adduction d\'eau',
            'Définir les critères d\'irrigation durable',
            'Harmoniser les pratiques de forage et prélèvement'
        ],
        'wg': [
            {'number': 1, 'name': 'Adduction d\'Eau', 'description': 'Systèmes de captage, traitement et distribution'},
            {'number': 2, 'name': 'Irrigation et Drainage', 'description': 'Aménagements d\'irrigation et systèmes de drainage'},
            {'number': 3, 'name': 'Forages et Captage', 'description': 'Techniques de forage et exploitation des nappes phréatiques'},
        ]
    },
    {
        'number': 7,
        'name': 'Assainissement et Gestion des Déchets',
        'description': 'Gestion des eaux usées et pluviales, traitement et évacuation, lutte contre l\'insalubrité',
        'iso_reference': 'ISO/TC 275',
        'arso_reference': 'ARSO/TC 9',
        'effectif': 19,
        'missions': [
            'Standardiser les systèmes d\'assainissement urbain et rural',
            'Définir les normes de traitement des eaux usées',
            'Établir les critères d\'gestion des eaux pluviales',
            'Promouvoir l\'hygiène et la lutte contre l\'insalubrité'
        ],
        'wg': [
            {'number': 1, 'name': 'Réseaux d\'Assainissement', 'description': 'Collecte et transport des eaux usées'},
            {'number': 2, 'name': 'Traitement et Épuration', 'description': 'Stations de traitement et dépuration des eaux'},
            {'number': 3, 'name': 'Gestion des Eaux Pluviales', 'description': 'Drainage urbain et gestion des écoulements'},
        ]
    },
    {
        'number': 8,
        'name': 'Sciences des Matériaux, Métrologie et Valorisation Locale',
        'description': 'Caractérisation des matériaux locaux, essais physiques, métrologie, simulation et recherche',
        'iso_reference': 'ISO/TC 262',
        'arso_reference': 'ARSO/TC 10',
        'effectif': 20,
        'missions': [
            'Caractériser et valoriser les matériaux locaux',
            'Établir les protocoles de métrologie et d\'essais',
            'Développer la simulation numérique et les modèles',
            'Promouvoir la recherche appliquée en génie civil'
        ],
        'wg': [
            {'number': 1, 'name': 'Matériaux de Construction Locaux', 'description': 'Identification et valorisation des matériaux RDC'},
            {'number': 2, 'name': 'Essais et Métrologie', 'description': 'Laboratoires, équipements d\'essais et protocoles'},
            {'number': 3, 'name': 'Simulation et Recherche', 'description': 'Modélisation numérique, simulation et R&D'},
            {'number': 4, 'name': 'Normalisation Appliquée', 'description': 'Application des normes ISO/ARSO au contexte local'},
        ]
    },
]

def create_ctm():
    """Crée les 8 CTM avec leurs métadonnées"""
    print("\n=== CRÉATION DES 8 COMITÉS TECHNIQUES MIROIRS ===\n")
    
    created_ctms = []
    
    for ctm_data in CTM_DATA:
        try:
            ctm, created = CTM.objects.get_or_create(
                number=ctm_data['number'],
                defaults={
                    'name': ctm_data['name'],
                    'description': ctm_data['description'],
                    'iso_reference': ctm_data['iso_reference'],
                    'arso_reference': ctm_data['arso_reference'],
                }
            )
            
            status = "✅ CRÉÉ" if created else "⚠️  EXISTE"
            print(f"{status} - CTM {ctm.number}: {ctm.name} ({ctm_data['effectif']} experts)")
            print(f"    - ISO: {ctm_data['iso_reference']} | ARSO: {ctm_data['arso_reference']}")
            print(f"    - Missions: {', '.join(ctm_data['missions'][:2])}...")
            
            created_ctms.append((ctm, ctm_data))
            
        except Exception as e:
            print(f"❌ ERREUR CTM {ctm_data['number']}: {e}")
    
    print(f"\n✅ Total CTM: {CTM.objects.count()}/8\n")
    return created_ctms

def create_working_groups(created_ctms):
    """Crée les Groupes de Travail pour chaque CTM"""
    print("\n=== CRÉATION DES GROUPES DE TRAVAIL ===\n")
    
    total_wg = 0
    
    for ctm, ctm_data in created_ctms:
        print(f"\n📋 CTM {ctm.number}: {ctm.name}")
        
        for wg_data in ctm_data['wg']:
            try:
                wg, created = WG.objects.get_or_create(
                    ctm=ctm,
                    number=wg_data['number'],
                    defaults={
                        'name': wg_data['name'],
                        'description': wg_data['description'],
                    }
                )
                
                status = "✅" if created else "⚠️"
                print(f"  {status} WG {ctm.number}.{wg.number}: {wg.name}")
                total_wg += 1
                
            except Exception as e:
                print(f"  ❌ Erreur WG {ctm_data['number']}.{wg_data['number']}: {e}")
    
    print(f"\n✅ Total Groupes de Travail: {WG.objects.count()}\n")

def print_summary():
    """Affiche un résumé de la structure créée"""
    print("\n" + "="*80)
    print("📊 RÉSUMÉ ORGANISATIONNEL CNETP")
    print("="*80 + "\n")
    
    # CTM Summary
    print("🏛️  COMITÉS TECHNIQUES MIROIRS (CTM):")
    print("-" * 80)
    
    for ctm in CTM.objects.all().order_by('number'):
        wg_count = ctm.working_groups.count()
        print(f"\n  CTM {ctm.number}: {ctm.name}")
        print(f"  ├─ Groupes de Travail: {wg_count}")
        print(f"  ├─ ISO Reference: {ctm.iso_reference}")
        print(f"  ├─ ARSO Reference: {ctm.arso_reference}")
        print(f"  └─ Description: {ctm.description[:60]}...")
        
        for wg in ctm.working_groups.all().order_by('number'):
            print(f"     └─ WG {ctm.number}.{wg.number}: {wg.name}")
    
    print("\n" + "="*80)
    print("✅ STRUCTURE ORGANISATIONNELLE COMPLÈTE")
    print(f"   - Total CTM: {CTM.objects.count()}")
    print(f"   - Total WG: {WG.objects.count()}")
    print(f"   - Experts théoriques: 8 CTM × 19-20 = ~152")
    print("="*80 + "\n")

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║  CRÉATION DES STRUCTURES DE GOUVERNANCE CNETP                             ║
║  Basé sur le Manuel Organisationnel 2026                                  ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Créer les CTM
    created_ctms = create_ctm()
    
    # Créer les WG
    create_working_groups(created_ctms)
    
    # Afficher le résumé
    print_summary()
    
    print("✅ Script de création terminé avec succès !\n")

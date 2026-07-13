"""
Management command to create the 8 CTM with their metadata
Based on CNETP 2026 Organizational Manual
"""

from django.core.management.base import BaseCommand
from apps.governance.models import CTM, WG


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
            {'number': 3, 'name': 'Stabilité & Érosions', 'description': 'Critères de stabilité des talus, compactage et géo-matériaux de remblai'},
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
            {'number': 1, 'name': 'Calcul Structural & Eurocodes', 'description': 'Obligations légales de dimensionnement des structures lourdes et ponts'},
            {'number': 2, 'name': 'Génie Parasismique', 'description': 'Conception et stabilité des ouvrages face aux aléas sismiques'},
            {'number': 3, 'name': 'Ouvrages Hydrauliques Lourds', 'description': 'Ponts-cadres, viaducs en béton précontraint et ouvrages hydrauliques lourds'},
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
            {'number': 1, 'name': 'Habitabilité & Sécurité', 'description': 'Éclairage naturel, étanchéité des façades, isolation thermique passive'},
            {'number': 2, 'name': 'BIM & Transition Numérique', 'description': 'Maquette numérique, interopérabilité et standards numériques (ISO 19650)'},
            {'number': 3, 'name': 'Performance Énergétique & Coûts', 'description': 'Éco-matériaux, efficacité énergétique et valorisation de la norme africaine ARS 1333'},
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
            {'number': 1, 'name': 'Macro-drainage & Eaux Pluviales', 'description': 'Drainage urbain et gestion des écoulements pluviaux'},
            {'number': 2, 'name': 'Eaux Usées & Réseaux d\'Égouts', 'description': 'Collecte, transport et dépuration des eaux usées'},
            {'number': 3, 'name': 'Déchets Solides & CET', 'description': 'Gestion des déchets solides et centres d\'enfouissement technique'},
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
            {'number': 1, 'name': 'Matériaux Géo-sourcés & Locaux', 'description': 'Identification et valorisation des matériaux locaux RDC'},
            {'number': 2, 'name': 'Essais & Métrologie Légale', 'description': 'Laboratoires, équipements d\'essais et protocoles de métrologie'},
            {'number': 3, 'name': 'Simulation, Recherche & Certification', 'description': 'Modélisation numérique, simulation, R&D et certification'},
        ]
    },
]


class Command(BaseCommand):
    help = 'Create the 8 Technical Mirror Committees (CTM) with their Working Groups based on CNETP 2026 manual'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("""
╔════════════════════════════════════════════════════════════════════════════╗
║  CRÉATION DES STRUCTURES DE GOUVERNANCE CNETP                             ║
║  Basé sur le Manuel Organisationnel 2026                                  ║
╚════════════════════════════════════════════════════════════════════════════╝
        """))
        
        # Create CTM
        self._create_ctm()
        
        # Create WG
        self._create_working_groups()
        
        # Print summary
        self._print_summary()
        
        self.stdout.write(self.style.SUCCESS("✅ Script de création terminé avec succès !\n"))

    def _create_ctm(self):
        """Create the 8 CTM with their metadata"""
        self.stdout.write(self.style.SUCCESS("\n=== CRÉATION DES 8 COMITÉS TECHNIQUES MIROIRS ===\n"))
        
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
                self.stdout.write(f"{status} - CTM {ctm.number}: {ctm.name} ({ctm_data['effectif']} experts)")
                self.stdout.write(f"    - ISO: {ctm_data['iso_reference']} | ARSO: {ctm_data['arso_reference']}")
                self.stdout.write(f"    - Missions: {', '.join(ctm_data['missions'][:2])}...")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ ERREUR CTM {ctm_data['number']}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"✅ Total CTM: {CTM.objects.count()}/8\n"))

    def _create_working_groups(self):
        """Create Working Groups for each CTM"""
        self.stdout.write(self.style.SUCCESS("\n=== CRÉATION DES GROUPES DE TRAVAIL ===\n"))
        
        total_wg = 0
        
        for ctm_data in CTM_DATA:
            try:
                ctm = CTM.objects.get(number=ctm_data['number'])
                self.stdout.write(f"\n📋 CTM {ctm.number}: {ctm.name}")
                
                for wg_data in ctm_data['wg']:
                    try:
                        wg, created = WG.objects.update_or_create(
                            ctm=ctm,
                            number=wg_data['number'],
                            defaults={
                                'name': wg_data['name'],
                                'description': wg_data['description'],
                            }
                        )

                        status = "✅ créé" if created else "• mis à jour"
                        self.stdout.write(f"  {status} WG {ctm.number}.{wg.number}: {wg.name}")
                        total_wg += 1
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  ❌ Erreur WG {ctm_data['number']}.{wg_data['number']}: {e}"))
            
            except CTM.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ CTM {ctm_data['number']} non trouvé"))
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Total Groupes de Travail: {WG.objects.count()}\n"))

    def _print_summary(self):
        """Print a summary of the created structure"""
        self.stdout.write("\n" + "="*80)
        self.stdout.write("📊 RÉSUMÉ ORGANISATIONNEL CNETP")
        self.stdout.write("="*80 + "\n")
        
        # CTM Summary
        self.stdout.write("🏛️  COMITÉS TECHNIQUES MIROIRS (CTM):")
        self.stdout.write("-" * 80)
        
        for ctm in CTM.objects.all().order_by('number'):
            wg_count = ctm.working_groups.count()
            self.stdout.write(f"\n  CTM {ctm.number}: {ctm.name}")
            self.stdout.write(f"  ├─ Groupes de Travail: {wg_count}")
            self.stdout.write(f"  ├─ ISO Reference: {ctm.iso_reference}")
            self.stdout.write(f"  ├─ ARSO Reference: {ctm.arso_reference}")
            self.stdout.write(f"  └─ Description: {ctm.description[:60]}...")
            
            for wg in ctm.working_groups.all().order_by('number'):
                self.stdout.write(f"     └─ WG {ctm.number}.{wg.number}: {wg.name}")
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("✅ STRUCTURE ORGANISATIONNELLE COMPLÈTE"))
        self.stdout.write(f"   - Total CTM: {CTM.objects.count()}")
        self.stdout.write(f"   - Total WG: {WG.objects.count()}")
        self.stdout.write(f"   - Experts théoriques: 8 CTM × 19-20 = ~152")
        self.stdout.write("="*80 + "\n")

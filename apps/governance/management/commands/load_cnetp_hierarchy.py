"""
Management command to load CNETP hierarchy (200 experts across 6 levels, 8 CTM, 24 WG, 16 structures)
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.experts.models import Expert
from apps.governance.models import (
    CTM, WG, Affectation,
    ComitePilotage, PilotageMembreship,
    TechnicalCell, CTCMembership,
    OriginStructure, ExecutiveLevel
)

User = get_user_model()


class Command(BaseCommand):
    help = "Load CNETP hierarchy: 200 experts, 6 levels, 8 CTM, 24 WG, 16 structures"

    def handle(self, *args, **options):
        """Execute the command"""
        self.stdout.write("Starting CNETP hierarchy load...")
        
        # Step 1: Create Origin Structures (16 girons)
        self.stdout.write("Creating 16 origin structures...")
        self.create_structures()
        
        # Step 2: Create 200 experts
        self.stdout.write("Creating 200 experts...")
        experts = self.create_experts()
        
        # Step 3: Create Executive Level (3 positions)
        self.stdout.write("Creating Executive Level...")
        self.create_executive_level(experts[:3])
        
        # Step 4: Create Steering Committee (24 members)
        self.stdout.write("Creating Steering Committee...")
        self.create_steering_committee(experts[3:27])
        
        # Step 5: Create Technical Cell (20 members)
        self.stdout.write("Creating Technical Cell...")
        self.create_technical_cell(experts[27:47])
        
        # Step 6: Create CTM (8 committees)
        self.stdout.write("Creating 8 CTM...")
        self.create_ctm_and_wg(experts[47:])
        
        self.stdout.write(self.style.SUCCESS("✓ CNETP hierarchy loaded successfully!"))
        self.stdout.write(f"Total experts: {Expert.objects.count()}")

    def create_structures(self):
        """Create 16 origin structures"""
        structures_data = [
            # Administration publique (61)
            ('ADM-01', 'Cabinet du Ministre', 'ADMIN', 'Cabinet du Ministre des ITP', 15),
            ('ADM-02', 'Secrétariat Général', 'ADMIN', 'SG-ITP', 20),
            ('ADM-03', 'SG Reconstruction', 'ADMIN', 'Secrétariat Général Reconstruction', 12),
            ('ADM-04', 'Ministères partenaires', 'ADMIN', 'Urbanisme, Aménagement, Environnement', 10),
            ('ADM-05', 'Experts juridiques', 'ADMIN', 'Cellule juridique', 4),
            
            # Établissements publics (64)
            ('OFF-01', 'Office de Réhabilitation', 'OFFICES', 'OR', 12),
            ('OFF-02', 'Office de Vérification Développement', 'OFFICES', 'OVD', 12),
            ('OFF-03', 'ACGT', 'OFFICES', 'Agence Congolaise de la Géomatique', 8),
            ('OFF-04', 'BTC', 'OFFICES', 'Bureau Technique Congolais', 15),
            ('OFF-05', 'FONER', 'OFFICES', 'Fonds National d\'Électrification Rurale', 10),
            ('OFF-06', 'Cellule Infrastructure', 'OFFICES', 'CI', 4),
            ('OFF-07', 'BEAU', 'OFFICES', 'Bureau d\'Étude Architecture Urbaine', 3),
            
            # Ordres professionnels (30)
            ('ORD-01', 'ONIC', 'ORDERS', 'Ordre National des Ingénieurs Civils', 16),
            ('ORD-02', 'ONA', 'ORDERS', 'Ordre National des Architectes', 14),
            
            # Institutions Académiques et de Recherche (20)
            ('ACAD-01', 'Institutions Académiques et de Recherche', 'ACADEMIA', '20 sièges dédiés à la caution scientifique et validation théorique.', 20),
        ]
        
        for code, name, giron, description, count in structures_data:
            OriginStructure.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'giron': giron,
                    'description': description,
                    'expected_expert_count': count,
                }
            )
        
        # Add remaining girons
        remaining = [
            ('MET-01', 'OCC', 'METROLOGY', 'Office de Contrôle et Certification', 10),
            ('MET-02', 'Société civile', 'METROLOGY', 'Organisations de la société civile', 5),
            ('PRIV-01', 'FEC', 'PRIVATE', 'Fédération des Entreprises du Congo', 8),
        ]
        
        for code, name, giron, description, count in remaining:
            OriginStructure.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'giron': giron,
                    'description': description,
                    'expected_expert_count': count,
                }
            )

    def create_experts(self):
        """Create 200 experts"""
        experts = []
        structures = list(OriginStructure.objects.all())
        
        for i in range(1, 201):
            username = f"expert{i:03d}"
            first_name = f"Expert"
            last_name = f"Expert{i:03d}"
            
            # Create user if not exists
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"expert{i:03d}@cnetp.rdc",
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': True,
                }
            )
            
            # Find or create corresponding structure in experts app
            from apps.experts.models import Structure as ExpertsStructure
            structure_name = structures[i % len(structures)].name
            expert_structure, _ = ExpertsStructure.objects.get_or_create(
                name=structure_name,
                defaults={
                    'acronym': f"STR{i % len(structures)}",
                    'category': 'ADMIN',  # Default
                }
            )
            
            # Create expert
            expert, _ = Expert.objects.get_or_create(
                user=user,
                defaults={
                    'structure': expert_structure,
                    'status': 'ACTIVE',
                    'specialties': f"Specialty {i}",
                }
            )
            experts.append(expert)
        
        return experts

    def create_executive_level(self, executives):
        """Create 3 Executive positions"""
        positions = ['MINISTER', 'SG_ITP', 'CABINET']
        for position, expert in zip(positions, executives):
            ExecutiveLevel.objects.get_or_create(
                position=position,
                defaults={'expert': expert}
            )

    def create_steering_committee(self, members):
        """Create Steering Committee (24 members)"""
        comite, _ = ComitePilotage.objects.get_or_create(
            name="Comité de Pilotage Stratégique CNETP",
            defaults={
                'president': members[0],
                'vice_president': members[1],
                'secretary': members[2],
                'rapporteur': members[3],
            }
        )
        
        roles = ['PRESIDENT', 'VICE_PRESIDENT', 'SECRETARY', 'RAPPORTEUR']
        for i, member in enumerate(members):
            role = roles[i] if i < len(roles) else 'CONSEILLER'
            PilotageMembreship.objects.get_or_create(
                comite=comite,
                expert=member,
                defaults={'role': role}
            )

    def create_technical_cell(self, members):
        """Create Technical Cell (20 members)"""
        ctc, _ = TechnicalCell.objects.get_or_create(
            name="Cellule Technique de Coordination",
            defaults={
                'coordinator': members[0],
                'vice_coordinator': members[1],
            }
        )
        
        roles = [
            'COORDINATOR', 'VICE_COORDINATOR', 'ISO_EXPERT', 'LEGAL',
            'ENVIRONMENTAL', 'PLANNER', 'ECONOMIST', 'SCIENTIFIC',
            'ACCOUNTANT', 'ENQUIRY_MANAGER', 'INDUSTRIAL', 'COMMUNICATOR',
            'EXECUTIVE', 'CARTOGRAPHER', 'DATA_ENTRY', 'IT_ADMIN'
        ]
        
        for i, member in enumerate(members):
            role = roles[i] if i < len(roles) else 'COORDINATOR'
            CTCMembership.objects.get_or_create(
                ctc=ctc,
                expert=member,
                defaults={'role': role}
            )

    def create_ctm_and_wg(self, experts):
        """Create 8 CTM with WG names aligned to the official manual"""
        ctm_names = [
            "Géotechnique et Risques Naturels",
            "Ouvrages d'Art",
            "Bâtiment, Urbanisme et Transition Numérique",
            "Aéroports et Transport Aérien",
            "Infrastructures de Transport Linéaire et Maritimes",
            "Ressources en Eau et Hydraulique",
            "Assainissement et Gestion des Déchets",
            "Sciences des Matériaux, Métrologie et Valorisation Locale",
        ]

        CTM_WGS = {
            1: ["Sols & Géomécanique", "Risques Naturels", "Stabilité & Érosions"],
            2: ["Calcul Structural & Eurocodes", "Génie Parasismique", "Ouvrages Hydrauliques Lourds / Ponts-Cadres"],
            3: ["Habitabilité & Sécurité", "BIM & Transition Numérique", "Performance Énergétique & Coûts"],
            4: ["Infrastructure Aéroportuaire", "Terminaux et Équipements", "Conformité OACI"],
            5: ["Ingénierie Routière", "Voies Ferrées", "Infrastructures Portuaires"],
            6: ["Adduction d'Eau", "Irrigation et Drainage", "Forages et Captage"],
            7: ["Macro-drainage & Eaux Pluviales", "Eaux Usées & Réseaux d'Égouts", "Déchets Solides & CET"],
            8: ["Matériaux Géo-sourcés & Locaux", "Essais & Métrologie Légale", "Simulation, Recherche & Certification"],
        }
        
        expert_idx = 0
        experts_list = list(experts)
        
        for ctm_num, ctm_name in enumerate(ctm_names, 1):
            # Create CTM
            ctm, _ = CTM.objects.get_or_create(
                number=ctm_num,
                defaults={
                    'name': ctm_name,
                    'description': f"CTM {ctm_num}: {ctm_name}",
                    'iso_reference': f"ISO/TC {100 + ctm_num}",
                    'scientific_president': experts_list[expert_idx] if expert_idx < len(experts_list) else None,
                }
            )
            expert_idx += 1
            
            # Use authoritative WG names when available
            wg_names = CTM_WGS.get(ctm_num, [f"WG {ctm_num}.{i}" for i in range(1, 4)])
            for wg_num, wg_name in enumerate(wg_names, 1):
                wg, _ = WG.objects.get_or_create(
                    ctm=ctm,
                    number=wg_num,
                    defaults={
                        'name': wg_name,
                        'description': f"Working Group {ctm_num}.{wg_num} - {wg_name}",
                        'president': experts_list[expert_idx] if expert_idx < len(experts_list) else None,
                    }
                )
                expert_idx += 1
                
                # Create 4-5 affectations per WG
                for _ in range(5):
                    if expert_idx < len(experts_list):
                        expert = experts_list[expert_idx]
                        Affectation.objects.get_or_create(
                            expert=expert,
                            ctm=ctm,
                            wg=wg,
                            defaults={
                                'is_primary_ctm': True,
                                'is_primary_wg': True,
                            }
                        )
                        expert_idx += 1

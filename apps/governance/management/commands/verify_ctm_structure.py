"""
Management command to verify CTM structure against manual requirements
Checks that all required roles and functions are implemented
"""

from django.core.management.base import BaseCommand
from django.db.models import Sum
from apps.governance.models import CTM, WG, ComitePilotage, TechnicalCell, PosteNominatif, PosteNominatifCTC
from apps.experts.models import Structure
from apps.norms.models import Norme
import sys


REQUIRED_ROLES = [
    'president',
    'vice_president',
    'secretary',
    'rapporteur',
]

REQUIRED_CTM_COUNT = 8
REQUIRED_WG_COUNT = 25


class Command(BaseCommand):
    help = 'Verify CTM structure against CNETP 2026 organizational manual requirements'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("""
╔════════════════════════════════════════════════════════════════════════════╗
║  VÉRIFICATION DE LA STRUCTURE ORGANISATIONNELLE CNETP                     ║
║  Validation contre le Manuel Organisationnel 2026                         ║
╚════════════════════════════════════════════════════════════════════════════╝
        """))
        
        checks = [
            ('CTM Count', self._check_ctm_count),
            ('WG Count', self._check_wg_count),
            ('CTM Names & References', self._check_ctm_details),
            ('WG Structure', self._check_wg_structure),
            ('Role Fields', self._check_role_fields),
            ('Pilotage Committee', self._check_pilotage),
            ('Technical Cell', self._check_technical_cell),
            ('Official Structures (Lignes 1-17)', self._check_official_structures),
            ('Pilotage Postes Nominatifs (27)', self._check_pilotage_postes),
            ('CTC Postes Nominatifs (20)', self._check_ctc_postes),
            ('Plan de Production Semestriel (PPT-2026)', self._check_production_plan_normes),
        ]
        
        results = {}
        for check_name, check_func in checks:
            try:
                result = check_func()
                results[check_name] = result
                status = "✅" if result['status'] == 'pass' else "⚠️"
                self.stdout.write(f"{status} {check_name}: {result['message']}")
            except Exception as e:
                results[check_name] = {'status': 'error', 'message': str(e)}
                self.stdout.write(self.style.ERROR(f"❌ {check_name}: {e}"))
        
        self._print_summary(results)
        
        # Determine exit status
        failed = sum(1 for r in results.values() if r['status'] != 'pass')
        if failed > 0:
            self.stdout.write(self.style.WARNING(f"\n⚠️  {failed} check(s) failed or incomplete"))
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ All checks passed!"))

    def _check_ctm_count(self):
        """Verify that 8 CTM have been created"""
        count = CTM.objects.count()
        if count == REQUIRED_CTM_COUNT:
            return {'status': 'pass', 'message': f'{count} CTM found (expected {REQUIRED_CTM_COUNT})'}
        else:
            return {'status': 'warn', 'message': f'{count} CTM found (expected {REQUIRED_CTM_COUNT})'}

    def _check_wg_count(self):
        """Verify that at least 24 WG have been created"""
        count = WG.objects.count()
        if count >= REQUIRED_WG_COUNT:
            return {'status': 'pass', 'message': f'{count} WG found (required {REQUIRED_WG_COUNT})'}
        else:
            return {'status': 'warn', 'message': f'{count} WG found (required {REQUIRED_WG_COUNT})'}

    def _check_ctm_details(self):
        """Verify CTM details against manual"""
        self.stdout.write("\n  📋 CTM Details Verification:")
        
        expected_ctm = {
            1: {'name_contains': 'Géotechnique', 'iso': 'ISO/TC 58'},
            2: {'name_contains': 'Ouvrages', 'iso': 'ISO/TC 167'},
            3: {'name_contains': 'Bâtiment', 'iso': 'ISO/TC 163'},
            4: {'name_contains': 'Aéroports', 'iso': 'ISO/TC 190'},
            5: {'name_contains': 'Transport', 'iso': 'ISO/TC 194'},
            6: {'name_contains': 'Eau', 'iso': 'ISO/TC 224'},
            7: {'name_contains': 'Assainissement', 'iso': 'ISO/TC 275'},
            8: {'name_contains': 'Matériaux', 'iso': 'ISO/TC 262'},
        }
        
        passed = 0
        for num, expected in expected_ctm.items():
            try:
                ctm = CTM.objects.get(number=num)
                has_name = expected['name_contains'].lower() in ctm.name.lower()
                has_iso = expected['iso'] in (ctm.iso_reference or '')
                
                if has_name and has_iso:
                    self.stdout.write(f"    ✅ CTM {num}: {ctm.name}")
                    passed += 1
                elif has_name:
                    self.stdout.write(f"    ⚠️  CTM {num}: Name OK, ISO ref missing")
                else:
                    self.stdout.write(f"    ❌ CTM {num}: Name mismatch")
                    
            except CTM.DoesNotExist:
                self.stdout.write(f"    ❌ CTM {num}: Not found")
        
        status = 'pass' if passed == 8 else 'warn'
        return {'status': status, 'message': f'{passed}/8 CTM details verified'}

    def _check_wg_structure(self):
        """Verify WG structure"""
        self.stdout.write("\n  📋 Working Groups Structure:")
        
        expected_wg_counts = {
            1: 3, 2: 3, 3: 3, 4: 3, 5: 4,
            6: 3, 7: 3, 8: 3,
        }
        
        passed = 0
        for ctm_num, expected_count in expected_wg_counts.items():
            try:
                ctm = CTM.objects.get(number=ctm_num)
                actual_count = ctm.working_groups.count()
                
                if actual_count >= expected_count:
                    self.stdout.write(f"    ✅ CTM {ctm_num}: {actual_count} WG (≥ {expected_count})")
                    passed += 1
                else:
                    self.stdout.write(f"    ❌ CTM {ctm_num}: {actual_count} WG (< {expected_count})")
                    
            except CTM.DoesNotExist:
                self.stdout.write(f"    ❌ CTM {ctm_num}: Not found")
        
        status = 'pass' if passed == 8 else 'warn'
        return {'status': status, 'message': f'{passed}/8 CTM have correct WG count'}

    def _check_role_fields(self):
        """Check if CTM model has role fields"""
        self.stdout.write("\n  👤 Role Fields Verification:")
        
        ctm = CTM.objects.first()
        if not ctm:
            return {'status': 'warn', 'message': 'No CTM found to check'}
        
        # Check CTM role fields
        ctm_fields = [f.name for f in CTM._meta.get_fields()]
        ctm_role_fields = {
            'scientific_president': 'scientific_president',
            'secretary': 'secretary',
            'rapporteur': 'rapporteur',
        }
        
        self.stdout.write("\n    CTM Role Fields:")
        ctm_found = 0
        for role_name, field_name in ctm_role_fields.items():
            if field_name in ctm_fields:
                self.stdout.write(f"      ✅ {field_name}")
                ctm_found += 1
            else:
                self.stdout.write(f"      ⚠️  {field_name} (not found)")
        
        # Check WG role fields
        wg_fields = [f.name for f in WG._meta.get_fields()]
        wg_role_fields = {
            'president': 'president',
            'secretary': 'secretary',
            'rapporteur': 'rapporteur',
        }
        
        self.stdout.write("\n    WG Role Fields:")
        wg_found = 0
        for role_name, field_name in wg_role_fields.items():
            if field_name in wg_fields:
                self.stdout.write(f"      ✅ {field_name}")
                wg_found += 1
            else:
                self.stdout.write(f"      ⚠️  {field_name} (not found)")
        
        status = 'pass' if ctm_found == 3 and wg_found == 3 else 'warn'
        total = ctm_found + wg_found
        return {'status': status, 'message': f'{total}/6 role fields found (CTM: {ctm_found}/3, WG: {wg_found}/3)'}

    def _check_pilotage(self):
        """Verify Comité de Pilotage structure"""
        try:
            pilotage = ComitePilotage.objects.first()
            if pilotage:
                return {'status': 'pass', 'message': 'Comité de Pilotage found'}
            else:
                return {'status': 'warn', 'message': 'Comité de Pilotage not yet populated'}
        except Exception as e:
            return {'status': 'warn', 'message': f'Cannot check Pilotage: {e}'}

    def _check_technical_cell(self):
        """Verify Cellule Technique de Coordination structure"""
        try:
            cell = TechnicalCell.objects.first()
            if cell:
                return {'status': 'pass', 'message': 'Cellule Technique found'}
            else:
                return {'status': 'warn', 'message': 'Cellule Technique not yet populated'}
        except Exception as e:
            return {'status': 'warn', 'message': f'Cannot check Technical Cell: {e}'}

    def _check_official_structures(self):
        """Verify the 17 official origin structures (Tableau 1, Lignes 1-17) are seeded"""
        self.stdout.write("\n  🏛️  Structures d'origine officielles (Tableau 1, Lignes 1-17) :")

        key_lines = [
            'Secrétariat Général aux ITP',
            'Cabinet du Ministre des ITP',
            'Office des Routes',
            'Office des Voiries et Drainage',
            'Agence Congolaise des Grands Travaux',
            'Bureau Technique de Contrôle',
            "Fonds National d'Entretien Routier",
        ]

        count = Structure.objects.count()
        missing = [name for name in key_lines if not Structure.objects.filter(name=name).exists()]

        for name in key_lines:
            if name in missing:
                self.stdout.write(f"    ❌ {name} : introuvable")
            else:
                self.stdout.write(f"    ✅ {name}")

        if count >= 19 and not missing:
            return {'status': 'pass', 'message': f"{count} structures en base (≥ 19 attendues), Lignes-clés présentes"}
        elif not missing:
            return {'status': 'warn', 'message': f"{count} structures en base (< 19 attendues), mais Lignes-clés présentes"}
        else:
            return {'status': 'warn', 'message': f"{count} structures en base — manquantes : {', '.join(missing)}"}

    def _check_pilotage_postes(self):
        """Verify the 27 nominative posts of the Comité de Pilotage Élargi (manuel, section 3.1)"""
        try:
            comite = ComitePilotage.objects.get(name="Comité de Pilotage Élargi CNETP")
        except ComitePilotage.DoesNotExist:
            return {'status': 'warn', 'message': "Comité de Pilotage Élargi CNETP introuvable — exécutez init_pilotage_and_ctc"}

        postes = PosteNominatif.objects.filter(comite=comite)
        count = postes.count()
        sans_structure = postes.filter(required_structure__isnull=True).count()

        self.stdout.write(
            f"\n  🪑 Postes nominatifs — Comité de Pilotage Élargi : {count}/27, "
            f"{sans_structure} sans structure d'origine rattachée"
        )

        if count == 27 and sans_structure == 0:
            return {'status': 'pass', 'message': "27/27 postes créés, tous rattachés à une structure d'origine"}
        elif count == 0:
            return {'status': 'warn', 'message': "Aucun poste — exécutez : python manage.py seed_pilotage_postes"}
        else:
            return {'status': 'warn', 'message': f"{count}/27 postes, {sans_structure} sans structure d'origine (attendu : 27 et 0)"}

    def _check_ctc_postes(self):
        """Verify the 20 nominative posts of the Cellule Technique de Coordination (manuel, section 3.2)"""
        try:
            ctc = TechnicalCell.objects.get(name="Cellule Technique de Coordination CNETP")
        except TechnicalCell.DoesNotExist:
            return {'status': 'warn', 'message': "Cellule Technique de Coordination CNETP introuvable — exécutez init_pilotage_and_ctc"}

        postes = PosteNominatifCTC.objects.filter(ctc=ctc)
        count = postes.count()
        sans_structure = postes.filter(required_structure__isnull=True).count()

        self.stdout.write(
            f"\n  🪑 Postes nominatifs — Cellule Technique de Coordination : {count}/20, "
            f"{sans_structure} sans structure d'origine rattachée"
        )

        if count == 20 and sans_structure == 0:
            return {'status': 'pass', 'message': "20/20 postes créés, tous rattachés à une structure d'origine"}
        elif count == 0:
            return {'status': 'warn', 'message': "Aucun poste — exécutez : python manage.py seed_ctc_postes"}
        else:
            return {'status': 'warn', 'message': f"{count}/20 postes, {sans_structure} sans structure d'origine (attendu : 20 et 0)"}

    def _check_production_plan_normes(self):
        """Verify the production plan (NOTE TECHNIQUE N°1 COMPLÉMENT DIRCAB, CNE-ITP/CTC/PPT-2026):
        185 NCD + 7 CA + 9 DIR + 8 REC réparties sur 24 GT (WG 4.3 volontairement exclu)."""
        self.stdout.write("\n  📑 Plan de Production Semestriel (CNE-ITP/CTC/PPT-2026) :")

        EXPECTED = {'NCD': 185, 'CA': 7, 'DIR': 9, 'REC': 8}

        plan_normes = Norme.objects.filter(reference_number__startswith='CNETP-PPT2026-')

        actual = {}
        for norm_type in EXPECTED:
            qs = plan_normes.filter(norm_type=norm_type)
            if norm_type == 'NCD':
                actual[norm_type] = qs.aggregate(total=Sum('target_count'))['total'] or 0
            else:
                actual[norm_type] = qs.count()

        passed = 0
        for norm_type, expected_count in EXPECTED.items():
            if actual[norm_type] == expected_count:
                self.stdout.write(f"    ✅ {norm_type}: {actual[norm_type]} (attendu {expected_count})")
                passed += 1
            else:
                self.stdout.write(f"    ❌ {norm_type}: {actual[norm_type]} (attendu {expected_count})")

        # 24 des 25 WG doivent avoir au moins une entrée (WG4.3 "Conformité OACI" exclu)
        wgs_with_entries = set(
            plan_normes.values_list('wg__ctm__number', 'wg__number').distinct()
        )
        excluded = {(4, 3)}
        all_wgs = set(WG.objects.values_list('ctm__number', 'number'))
        expected_wgs = all_wgs - excluded
        missing_wgs = expected_wgs - wgs_with_entries

        if missing_wgs:
            self.stdout.write(
                f"    ❌ GT manquants dans le plan de production : "
                f"{', '.join(f'{c}.{w}' for c, w in sorted(missing_wgs))}"
            )

        status = 'pass' if passed == len(EXPECTED) and not missing_wgs else 'warn'
        return {
            'status': status,
            'message': (
                f"NCD={actual['NCD']}/185, CA={actual['CA']}/7, DIR={actual['DIR']}/9, "
                f"REC={actual['REC']}/8, GT couverts={len(wgs_with_entries)}/24 (WG4.3 exclu)"
            )
        }

    def _print_summary(self, results):
        """Print verification summary"""
        self.stdout.write("\n" + "="*80)
        self.stdout.write("📊 RÉSUMÉ DE VÉRIFICATION")
        self.stdout.write("="*80)
        
        passed = sum(1 for r in results.values() if r['status'] == 'pass')
        warned = sum(1 for r in results.values() if r['status'] == 'warn')
        errored = sum(1 for r in results.values() if r['status'] == 'error')
        
        self.stdout.write(f"\n✅ Passed: {passed}")
        self.stdout.write(f"⚠️  Warnings: {warned}")
        self.stdout.write(f"❌ Errors: {errored}")
        
        self.stdout.write("\n" + "="*80 + "\n")

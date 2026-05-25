"""
Management command to verify CTM structure against manual requirements
Checks that all required roles and functions are implemented
"""

from django.core.management.base import BaseCommand
from apps.governance.models import CTM, WG, ComitePilotage, TechnicalCell
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
            1: 3, 2: 3, 3: 3, 4: 3, 5: 3,
            6: 3, 7: 3, 8: 4,
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

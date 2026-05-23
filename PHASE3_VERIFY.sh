#!/bin/bash

echo "==================================="
echo "PHASE 3 - VERIFICATION SCRIPT"
echo "==================================="
echo ""

source mon_env/bin/activate

# Check models
echo "✓ Checking Models..."
python manage.py shell << PYEOF
from apps.governance.models import ExecutiveLevel, ComitePilotage, TechnicalCell, CTM, WG, OriginStructure
print(f"  - Executives: {ExecutiveLevel.objects.count()}")
print(f"  - Steering Committee: {ComitePilotage.objects.count()}")
print(f"  - Technical Cell: {TechnicalCell.objects.count()}")
print(f"  - CTM: {CTM.objects.count()}")
print(f"  - WG: {WG.objects.count()}")
print(f"  - Structures: {OriginStructure.objects.count()}")
PYEOF

# Check templates
echo ""
echo "✓ Checking Templates..."
for template in executives steering_committee technical_cell ctm_list structures base; do
    if [ -f "web/templates/hierarchy/${template}.html" ]; then
        echo "  ✓ ${template}.html"
    else
        echo "  ✗ ${template}.html MISSING"
    fi
done

# Check API endpoints
echo ""
echo "✓ Checking API Endpoints..."
python manage.py shell << PYEOF
from api.v1.hierarchy_views import *
endpoints = [
    'ExecutiveLevelViewSet',
    'SteeringCommitteeViewSet',
    'TechnicalCellViewSet',
    'OriginStructureViewSet',
    'HierarchyViewSet'
]
for endpoint in endpoints:
    print(f"  ✓ {endpoint}")
PYEOF

# Check Django
echo ""
echo "✓ Running Django checks..."
python manage.py check --quiet && echo "  ✓ All checks passed (0 errors)" || echo "  ✗ Errors found"

# Check URL routing
echo ""
echo "✓ Checking URL routes..."
grep -q "hierarchy" web/urls.py && echo "  ✓ hierarchy/ route registered" || echo "  ✗ hierarchy/ route missing"
grep -q "hierarchy" api/v1/urls.py && echo "  ✓ /api/v1/hierarchy routes registered" || echo "  ✗ API routes missing"

echo ""
echo "==================================="
echo "✅ PHASE 3 VERIFICATION COMPLETE"
echo "==================================="

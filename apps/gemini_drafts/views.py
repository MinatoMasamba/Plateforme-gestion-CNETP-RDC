import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .services import generate_and_save, get_governance_structure
from .models import Draft


@csrf_exempt
def generate_draft(request):
    """Endpoint pour générer un brouillon avec classification automatique."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode POST requise'}, status=405)
    
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    
    # Validation des champs requis
    draft_type = payload.get('type')
    content = payload.get('content') or payload.get('text') or ''
    
    if not draft_type:
        return JsonResponse({'error': 'Champ "type" requis (guide, norme, norme_fictive)'}, status=400)
    
    if not content:
        return JsonResponse({'error': 'Champ "content" requis'}, status=400)
    
    try:
        record = generate_and_save(
            domain=payload.get('domain', 'non précisé'),
            draft_type=draft_type,
            content=content,
            data=payload.get('data'),
        )
    except Exception as exc:
        return JsonResponse({'error': f'Erreur de génération: {str(exc)}'}, status=500)
    
    return JsonResponse({
        'success': True,
        'draft': record.as_dict(),
        'classification': {
            'ctm': record.ctm,
            'wg': record.wg,
            'reason': record.classification_reason,
        }
    }, status=201)


def list_drafts(request):
    """Liste les brouillons."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode GET requise'}, status=405)
    
    # Filtrer par CTM et WG si fournis
    ctm = request.GET.get('ctm')
    wg = request.GET.get('wg')
    
    qs = Draft.objects.all()
    if ctm:
        qs = qs.filter(ctm__icontains=ctm)
    if wg:
        qs = qs.filter(wg__icontains=wg)
    
    data = [d.as_dict() for d in qs[:50]]
    return JsonResponse({'drafts': data, 'total': len(data)}, safe=False)


def dashboard(request):
    """Page de dashboard du générateur."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode GET requise'}, status=405)
    
    # Récupérer la structure pour affichage
    structure = get_governance_structure()
    
    context = {
        'structure': structure,
    }
    return render(request, 'gemini_drafts/dashboard.html', context)


def get_structure(request):
    """Endpoint pour récupérer la structure CTM/WG."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode GET requise'}, status=405)
    
    structure = get_governance_structure()
    return JsonResponse({'structure': structure})
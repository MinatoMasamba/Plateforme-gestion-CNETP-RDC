from django.shortcuts import render
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
import json

from apps.experts.models import Expert, Structure

CATEGORY_LABELS = {
    'ADMIN':   'Administration publique',
    'PUBLIC':  'Établissements publics',
    'PROF':    'Ordres professionnels',
    'ACAD':    'Académiques & Recherche',
    'METRO':   'Métrologie & Société civile',
    'PRIVATE': 'Secteur privé',
}


def dashboard(request):
    # ── KPIs ──────────────────────────────────────────────
    total   = Expert.objects.count()
    active  = Expert.objects.filter(status='ACTIVE').count()
    pending = Expert.objects.filter(status='PENDING').count()
    rejected= Expert.objects.filter(status='REJECTED').count()
    recent  = Expert.objects.filter(
        inscription_date__gte=timezone.now() - timedelta(days=30)
    ).count()

    # ── Par structure ──────────────────────────────────────
    structures = Structure.objects.annotate(
        total    = Count('experts'),
        n_active = Count('experts', filter=Q(experts__status='ACTIVE')),
        n_pending= Count('experts', filter=Q(experts__status='PENDING')),
        n_rejected=Count('experts', filter=Q(experts__status='REJECTED')),
    ).filter(total__gt=0).order_by('-total')

    # ── Courbe mensuelle 12 mois ───────────────────────────
    monthly = (
        Expert.objects
        .filter(inscription_date__gte=timezone.now() - timedelta(days=365))
        .annotate(month=TruncMonth('inscription_date'))
        .values('month').annotate(n=Count('id')).order_by('month')
    )

    # ── Annuaire experts (10 derniers) ─────────────────────
    latest_experts = (
        Expert.objects
        .select_related('user', 'structure', 'ctm')
        .order_by('-inscription_date')[:10]
    )

    # ── Données JSON pour les graphiques ──────────────────
    chart_monthly = {
        'labels': [m['month'].strftime('%b %Y') for m in monthly],
        'values': [m['n'] for m in monthly],
    }

    chart_status = {
        'labels': ['Actifs', 'En attente', 'Rejetés', 'Autres'],
        'data':   [active, pending, rejected, total - active - pending - rejected],
        'colors': ['#10b981', '#f59e0b', '#ef4444', '#94a3b8'],
    }

    chart_structures = {
        'labels':  [s.acronym for s in structures],
        'active':  [s.n_active  for s in structures],
        'pending': [s.n_pending for s in structures],
        'rejected':[s.n_rejected for s in structures],
    }

    context = {
        'total': total, 'active': active,
        'pending': pending, 'recent': recent,
        'structures': structures,
        'latest_experts': latest_experts,
        'chart_monthly':    json.dumps(chart_monthly),
        'chart_status':     json.dumps(chart_status),
        'chart_structures': json.dumps(chart_structures),
    }
    return render(request, 'dashboard/dashboard.html', context)


def ajax_structure(request, pk):
    """Retourne les experts d'une structure en JSON (pour le modal)."""
    experts = (
        Expert.objects
        .filter(structure_id=pk)
        .select_related('user', 'ctm')
        .order_by('-inscription_date')
    )
    data = [{
        'nom':     e.user.get_full_name(),
        'email':   e.user.email,
        'ctm':     e.ctm.name if e.ctm else '—',
        'statut':  e.get_status_display(),
        'statut_code': e.status,
        'date':    e.inscription_date.strftime('%d/%m/%Y'),
    } for e in experts]
    return JsonResponse({'experts': data, 'total': len(data)})

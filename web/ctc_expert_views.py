"""Fiche expert et CV consultables depuis l'annuaire CTC."""
from pathlib import PurePath

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache

from apps.experts.models import Expert
from apps.governance.activity_supervision import activity_access_for, log_sensitive_access
from apps.governance.models import ActivitySession, CTCMembership, Tache
from apps.norms.models import NormeVersion


def _target(request, pk):
    if not CTCMembership.objects.filter(expert__user=request.user).exists():
        raise PermissionDenied('Accès réservé aux membres de la CTC.')
    return get_object_or_404(Expert.objects.select_related('user', 'structure', 'ctm'),
                             pk=pk, user__is_active=True)


@login_required(login_url='/se-connecter/')
@never_cache
def expert_detail(request, pk):
    target = _target(request, pk)
    can_view = activity_access_for(request.user)['can_view_contributions']
    try:
        cv_available = bool(target.cv) and target.cv.storage.exists(target.cv.name)
    except OSError:
        cv_available = False
    context = {'target': target, 'can_view_contributions': can_view, 'cv_available': cv_available}
    if can_view:
        sessions = ActivitySession.objects.filter(user=target.user).aggregate(
            seconds=Sum('active_seconds'), count=Count('pk'))
        seconds = sessions['seconds'] or 0
        context.update({
            'time_display': f'{seconds // 3600} h {(seconds % 3600) // 60:02d} min {seconds % 60:02d} s',
            'session_count': sessions['count'],
            'editions': NormeVersion.all_objects.filter(version_author=target.user)
                .select_related('norme').order_by('-created_at', '-pk'),
            'tasks': Tache.objects.filter(assigned_to=target).select_related('norme').order_by('due_date', 'pk'),
        })
    log_sensitive_access(request, target, purpose='Consultation de la fiche expert depuis la CTC')
    return render(request, 'ctc/app/components/expert_detail.html', context)


@login_required(login_url='/se-connecter/')
@never_cache
def expert_cv(request, pk):
    target = _target(request, pk)
    if not target.cv:
        raise Http404('Aucun CV enregistré.')
    try:
        stream = target.cv.open('rb')
    except (FileNotFoundError, OSError):
        raise Http404('Le fichier CV est introuvable.')
    log_sensitive_access(request, target, purpose='Consultation du CV depuis la CTC')
    filename = PurePath(target.cv.name).name
    pdf = filename.lower().endswith('.pdf')
    response = FileResponse(stream, as_attachment=not pdf, filename=filename,
                            content_type='application/pdf' if pdf else 'application/octet-stream')
    response['X-Content-Type-Options'] = 'nosniff'
    return response

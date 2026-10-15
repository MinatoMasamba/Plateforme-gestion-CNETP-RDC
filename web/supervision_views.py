from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from apps.core.models import AuditLog
from apps.experts.models import Expert
from apps.norms.models import Norme, NormeVersion
from apps.norms.diff_utils import build_inline_diff_segments
from apps.governance.ctc_supervision import FIELD_LABELS, _change_details
from .pilotage_views import get_pilotage_context


def supervisor_context(request):
    expert = Expert.objects.filter(user=request.user).select_related('structure').first()
    privileges = get_pilotage_context(expert) if expert else None
    if not privileges or not privileges['can_view_global_console']:
        raise PermissionDenied('Cette consultation est réservée aux membres habilités du Pilotage.')
    return {'expert': expert, **privileges}


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageNormeHistoryView(View):
    def get(self, request, pk):
        context = supervisor_context(request)
        norme = get_object_or_404(Norme.objects.select_related('ctm', 'wg'), pk=pk)
        versions = list(norme.versions.select_related('version_author').order_by('-version_number'))
        for version in versions:
            version.history_author = (version.version_author.get_full_name() or version.version_author.username) if version.version_author else 'Auteur non enregistré'
        selected = versions[0] if versions else None
        if request.GET.get('version_id'):
            try:
                selected = get_object_or_404(NormeVersion, norme=norme, pk=int(request.GET['version_id']))
            except ValueError:
                return HttpResponseBadRequest('Identifiant de version invalide.')
        if request.GET.get('v2'):
            try:
                selected = get_object_or_404(NormeVersion, norme=norme, version_number=int(request.GET['v2']))
            except ValueError:
                return HttpResponseBadRequest('Numéro de version invalide.')
        previous = next((version for version in versions if selected and version.version_number < selected.version_number), None)
        if request.GET.get('v1'):
            try:
                number = int(request.GET['v1'])
                previous = get_object_or_404(NormeVersion, norme=norme, version_number=number) if number else None
            except ValueError:
                return HttpResponseBadRequest('Numéro de version invalide.')
        old = previous.content if previous else ''
        new = selected.content if selected else ''
        context.update({
            'norme': norme, 'versions': versions, 'selected': selected, 'previous': previous,
            'history_title': 'Historique des versions', 'old_text': old, 'new_text': new,
            'diff_sections': [{'title': 'Texte du document', 'segments': build_inline_diff_segments(old, new)}] if selected else [],
            'back_url': reverse('web:pilotage_ctm_detail', args=[norme.ctm.number]) + '#ctm-activity',
        })
        return render(request, 'pilotage/history.html', context)


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageActivityHistoryView(View):
    def get(self, request, pk):
        context = supervisor_context(request)
        log = get_object_or_404(AuditLog.objects.select_related('user'), pk=pk, changes__scope__in=['ctc', 'ctm'])
        norme = Norme.objects.filter(pk=log.changes.get('norme_id')).select_related('ctm').first()
        if log.content_type == 'norms.NormeVersion' and log.action == 'CREATE' and norme:
            version = NormeVersion.objects.filter(pk=log.object_id, norme=norme).first()
            if version:
                return redirect(reverse('web:pilotage_norme_history', args=[norme.pk]) + f'?version_id={version.pk}')
        sections = [{
            'title': FIELD_LABELS.get(change.field_name, change.field_name),
            'segments': build_inline_diff_segments(change.old_text, change.new_text),
        } for change in log.text_changes.all()]
        context.update({
            'norme': norme, 'log': log, 'history_title': 'Historique de la modification',
            'diff_sections': sections, 'details': _change_details(log.changes.get('fields', {})),
            'back_url': (reverse('web:pilotage_ctm_detail', args=[norme.ctm.number]) + '#ctm-journal') if norme and log.changes.get('scope') == 'ctm' else reverse('web:pilotage_dashboard') + '#panel-ctc',
            'actor_name': (log.user.get_full_name() or log.user.username) if log.user else 'Auteur non enregistré',
            'snapshot_fields': [{'label': FIELD_LABELS.get(name, change.get('label', name)),
                                 'before': change.get('before'), 'after': change.get('after')}
                                for name, change in log.changes.get('fields', {}).items()
                                if not isinstance(change.get('before'), dict) and not isinstance(change.get('after'), dict)],
        })
        return render(request, 'pilotage/history.html', context)

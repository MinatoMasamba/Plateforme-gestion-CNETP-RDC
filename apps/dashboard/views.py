from django.shortcuts import render
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from collections import Counter, defaultdict
import json
import unicodedata
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.documents.models import DocumentFile
from apps.governance.activity_models import ActivityAggregate, ActivitySession
from apps.governance.models import CTCMembership, PilotageMembreship
from apps.governance.phoenix_models import (
    AffectationSousCommission, ChoixOrganisationExpert, DossierPhoenix,
    GroupeCible, MandatOrganisation, Organe, OrganisationVersion,
    PosteOrganisation, RattachementDocumentaire,
)
from apps.norms.models import Norme, NormeComment, NormeVersion
from apps.experts.models import ProfileUpdate
from .report_export import build_report_docx

logger = logging.getLogger(__name__)

from apps.experts.models import Expert, Structure

CATEGORY_LABELS = {
    'ADMIN':   'Administration publique',
    'PUBLIC':  'Établissements publics',
    'PROF':    'Ordres professionnels',
    'ACAD':    'Académiques & Recherche',
    'METRO':   'Métrologie & Société civile',
    'PRIVATE': 'Secteur privé',
}


@login_required(login_url='web:expert_login')
def dashboard(request):
    _require_intelligence(request)
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

    # ── Répartition par CTM ────────────────────────────────
    ctm_data = (
        Expert.objects
        .values('ctm__name')
        .annotate(n=Count('id'))
        .order_by('-n')
    )
    CTM_COLORS = ['#2563eb','#3b82f6','#60a5fa','#93c5fd','#bfdbfe','#1d4ed8','#1e40af','#1e3a8a','#94a3b8']
    chart_ctm = {
        'labels': [d['ctm__name'] or 'Non assigné' for d in ctm_data],
        'data':   [d['n'] for d in ctm_data],
        'colors': CTM_COLORS[:len(list(ctm_data))],
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
        'chart_ctm':        json.dumps(chart_ctm),
        'chart_structures': json.dumps(chart_structures),
        'intelligence_access': can_use_intelligence(request.user),
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required(login_url='web:expert_login')
def ajax_structure(request, pk):
    """Retourne les experts d'une structure en JSON (pour le modal)."""
    _require_intelligence(request)
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


def can_use_intelligence(user):
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_staff or user.is_superuser or user.is_minister:
        return True
    return (PilotageMembreship.objects.filter(expert__user=user, expert__status='ACTIVE').exists()
            or CTCMembership.objects.filter(expert__user=user, expert__status='ACTIVE').exists())


def _require_intelligence(request):
    if not can_use_intelligence(request.user):
        raise PermissionDenied


def _reference_version():
    # The adopted-report proposal has seven SC and 35 GT; never merge its
    # rows with the earlier validated catalogue.
    return (OrganisationVersion.objects.filter(code='reorganisation-2026-10-15').first()
            or OrganisationVersion.objects.filter(status='ACTIVE').first()
            or OrganisationVersion.objects.order_by('-created_at').first())


def _document_queryset(user):
    qs = DocumentFile.objects.select_related('norme', 'uploaded_by')
    if user.has_perm('documents.view_documentfile') or user.is_superuser:
        return qs
    return qs.filter(Q(is_public=True) | Q(uploaded_by=user)).distinct()


def _snapshot(version):
    scs = list(Organe.objects.filter(version=version, type='SC').order_by('code')) if version else []
    gt_rows = list(GroupeCible.objects.filter(sc__in=scs).select_related('sc').order_by('sc__code', 'code'))
    groups_by_sc = {sc.pk: [] for sc in scs}
    for gt in gt_rows:
        groups_by_sc[gt.sc_id].append(gt)
    active_assignments = AffectationSousCommission.objects.filter(
        version=version, status='MIGRATED', sc__in=scs, effective_to__isnull=True,
    ) if version else AffectationSousCommission.objects.none()
    review_assignments = AffectationSousCommission.objects.filter(
        version=version, status='REVIEW', sc__in=scs,
    ) if version else AffectationSousCommission.objects.none()
    choices = ChoixOrganisationExpert.objects.filter(version=version, sc__in=scs) if version else ChoixOrganisationExpert.objects.none()
    mandates = MandatOrganisation.objects.filter(
        Q(poste__organe__in=scs) | Q(groupe__sc__in=scs)
    ).distinct()
    measures = (ActivityAggregate.objects.filter(period_type='DAY', target_group__sc__in=scs)
                .values('target_group__sc_id').annotate(seconds=Sum('active_seconds'), people=Count('user_id', distinct=True)))
    measure_map = {row['target_group__sc_id']: row for row in measures}
    dossiers = DossierPhoenix.objects.filter(gt__sc__in=scs).select_related('norme', 'gt', 'gt__sc')
    dossier_counts = dict(dossiers.values('gt__sc_id').annotate(n=Count('id')).values_list('gt__sc_id', 'n'))
    assignment_counts = dict(active_assignments.values('sc_id').annotate(n=Count('expert_id', distinct=True)).values_list('sc_id', 'n'))
    review_counts = dict(review_assignments.values('sc_id').annotate(n=Count('expert_id', distinct=True)).values_list('sc_id', 'n'))
    choice_counts = dict(choices.values('sc_id').annotate(n=Count('expert_id', distinct=True)).values_list('sc_id', 'n'))
    mandate_counts = dict(mandates.filter(status='ACTIVE', poste__organe__in=scs).values('poste__organe_id').annotate(n=Count('id')).values_list('poste__organe_id', 'n'))
    posts_by_sc = defaultdict(list)
    for post in PosteOrganisation.objects.filter(organe__in=scs).prefetch_related('mandates__expert__user').order_by('organe__code', 'code'):
        confirmed = next((m for m in post.mandates.all() if m.status == 'ACTIVE'), None)
        proposed = next((m for m in post.mandates.all() if m.status == 'PROPOSED'), None)
        posts_by_sc[post.organe_id].append({'post': post, 'confirmed': confirmed, 'proposed': proposed})
    rows = []
    for sc in scs:
        measure = measure_map.get(sc.pk, {})
        rows.append({
            'sc': sc, 'groups': groups_by_sc[sc.pk], 'gt_count': len(groups_by_sc[sc.pk]),
            'assigned': assignment_counts.get(sc.pk, 0), 'review': review_counts.get(sc.pk, 0),
            'choices': choice_counts.get(sc.pk, 0), 'mandates': mandate_counts.get(sc.pk, 0),
            'minutes': round((measure.get('seconds') or 0) / 60),
            'measured_people': measure.get('people') or 0,
            'dossiers': dossier_counts.get(sc.pk, 0),
            'posts': posts_by_sc[sc.pk],
        })
    return rows, gt_rows, dossiers


@login_required(login_url='web:expert_login')
def intelligence(request):
    _require_intelligence(request)
    version = _reference_version()
    rows, groups, dossiers = _snapshot(version)
    section = request.GET.get('section', 'vue')
    allowed = {'vue', 'organisation', 'experts', 'production', 'documents', 'observations', 'rapports'}
    if section not in allowed:
        raise Http404
    selected_sc = request.GET.get('sc', '')
    if selected_sc and not any(str(row['sc'].pk) == selected_sc for row in rows):
        raise Http404
    selected_norm = request.GET.get('norme', '')
    if selected_norm and not selected_norm.isdecimal():
        raise Http404
    norms = (Norme.all_objects.select_related('ctm', 'wg')
             .exclude(status='ARCHIVED')
             .order_by('reference_number'))
    if selected_norm:
        norm = get_object_or_404(norms, pk=selected_norm)
    else:
        norm = None
    q = request.GET.get('q', '').strip()[:100]
    docs = _document_queryset(request.user)
    if q:
        docs = docs.filter(Q(title__icontains=q) | Q(category__icontains=q))
    comments = NormeComment.objects.select_related('norme', 'author__user').order_by('-created_at')
    if norm:
        comments = comments.filter(norme=norm)
    report = request.GET.get('rapport', 'cabinet')
    if report not in {'cabinet', 'general', 'experts', 'sc', 'production', 'decisions'}:
        raise Http404
    report_focus = {
        'cabinet': "Pour le Cabinet, la priorité est de confirmer les responsabilités, les affectations et les échéances. Les indicateurs ci-dessous décrivent l'enregistrement dans la base, sans présumer de décisions officielles.",
        'general': "L'avancement porte sur l'organisation, la mobilisation des experts et les projets de normes enregistrés. Les points en attente sont distingués des décisions acquises.",
        'experts': "La participation combine ici la dernière connexion connue et les minutes mesurées sur les GT cibles. Les activités hors plateforme ne sont pas comptées.",
        'sc': "Chaque sous-commission est comparée selon ses GT, affectations à examiner, personnes mesurées et dossiers reliés explicitement.",
        'production': "La production est appréciée à partir des projets et versions enregistrés. Seul le statut du projet atteste une étape d'adoption ou de publication.",
        'decisions': "Les affectations à examiner et les responsabilités sans mandat actif constituent des sujets à instruire. Aucune nomination n'est déduite d'un choix d'expert.",
    }[report]
    context = {
        'section': section, 'version': version, 'rows': rows, 'groups': groups,
        'dossiers': dossiers[:30], 'selected_sc': selected_sc, 'norms': norms[:100],
        'norm': norm, 'versions': NormeVersion.all_objects.filter(norme=norm).order_by('-version_number') if norm else [],
        'comments': comments[:50], 'documents': docs[:80], 'q': q, 'report': report,
        'document_versions': NormeVersion.all_objects.select_related('norme').order_by('-created_at')[:80],
        'report_focus': report_focus,
        'extracted_at': timezone.localtime(),
        'expert_count': Expert.objects.filter(user__is_staff=False, user__is_superuser=False).count(),
        'connected_count': Expert.objects.filter(user__is_staff=False, user__is_superuser=False, user__last_login__isnull=False).count(),
        'profile_submitted': ProfileUpdate.objects.filter(expert__user__is_staff=False, expert__user__is_superuser=False, status__in=['SUBMITTED', 'UNDER_REVIEW']).count(),
        'profile_validated': ProfileUpdate.objects.filter(expert__user__is_staff=False, expert__user__is_superuser=False, status='COMPLETE').count(),
        'project_count': norms.count(), 'version_count': NormeVersion.all_objects.count(),
        'draft_count': norms.filter(status='DRAFT').count(),
        'adopted_count': norms.filter(status__in=['ADOPTED', 'HOMOLOGATED', 'PUBLISHED']).count(),
        'review_count': sum(row['review'] for row in rows),
        'unassigned_review_count': AffectationSousCommission.objects.filter(version=version, status='REVIEW', sc__isnull=True).count() if version else 0,
        'decision_count': sum(1 for row in rows if row['mandates'] == 0),
        'doc_count': _document_queryset(request.user).count(),
        'comment_count': NormeComment.objects.count(),
        'statuses': norms.values('status').annotate(n=Count('id')).order_by('status'),
        'bindings': RattachementDocumentaire.objects.filter(version=version, sc__in=[r['sc'] for r in rows]).select_related('norme', 'sc')[:30] if version else [],
        'pilotage_members': PilotageMembreship.objects.select_related('expert__user').order_by('role')[:40],
        'ctc_members': CTCMembership.objects.select_related('expert__user').order_by('role')[:40],
    }
    return render(request, 'dashboard/intelligence.html', context)


@login_required(login_url='web:expert_login')
def expert_activity_report(request):
    """Live counterpart of the Ecosys expert-activity report, with explicit definitions."""
    _require_intelligence(request)
    version = _reference_version()
    rows, _, _ = _snapshot(version)
    base = Expert.objects.filter(user__is_staff=False, user__is_superuser=False).select_related('user', 'structure', 'profile_update')
    q = request.GET.get('q', '').strip()[:80]
    sc_id = request.GET.get('sc', '')
    if sc_id and not any(str(row['sc'].pk) == sc_id for row in rows):
        raise Http404
    all_experts = list(base.order_by('user__last_name', 'user__first_name'))
    expert_ids = [e.pk for e in all_experts]
    user_ids = [e.user_id for e in all_experts]
    sessions = (ActivitySession.objects.filter(user_id__in=user_ids)
                .values('user_id').annotate(seconds=Sum('active_seconds'), n=Count('id')))
    session_map = {item['user_id']: item for item in sessions}
    edition_map = dict(NormeVersion.all_objects.filter(version_author_id__in=user_ids)
                       .values('version_author_id').annotate(n=Count('id')).values_list('version_author_id', 'n'))
    assignment_map = defaultdict(list)
    if version:
        assignments = AffectationSousCommission.objects.filter(version=version, expert_id__in=expert_ids, status='REVIEW').select_related('sc')
        for item in assignments:
            assignment_map[item.expert_id].append(item.sc)
    selected = []
    profile_counts = Counter()
    for expert in all_experts:
        profile = getattr(expert, 'profile_update', None)
        filled = bool(expert.cv or expert.whatsapp_number or expert.user.profile_picture or expert.bank_account or expert.mobile_money_number)
        connected = expert.user.last_login is not None
        if connected and filled:
            profile_group = 'Connecté et informations personnelles renseignées'
        elif connected:
            profile_group = 'Connecté, informations à compléter'
        elif filled:
            profile_group = 'Fiche renseignée, sans connexion connue'
        else:
            profile_group = 'Ni connexion ni élément personnel identifié'
        profile_counts[profile_group] += 1
        if q and q.casefold() not in (expert.user.get_full_name() + ' ' + expert.structure.name).casefold():
            continue
        targets = [sc for sc in assignment_map[expert.pk] if sc]
        if sc_id and not any(str(sc.pk) == sc_id for sc in targets):
            continue
        activity = session_map.get(expert.user_id, {})
        selected.append({
            'expert': expert, 'profile_group': profile_group,
            'workflow': profile.get_status_display() if profile else 'Aucun dossier de mise à jour',
            'profile_date': profile.submitted_at if profile and profile.submitted_at else None,
            'scs': targets, 'minutes': round((activity.get('seconds') or 0) / 60),
            'sessions': activity.get('n') or 0, 'editions': edition_map.get(expert.user_id, 0),
        })
    paginator = Paginator(selected, 30)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'dashboard/expert_activity_report.html', {
        'version': version, 'rows': rows, 'records': page, 'q': q, 'sc_id': sc_id,
        'total': Expert.objects.filter(user__is_staff=False, user__is_superuser=False).count(),
        'connected': Expert.objects.filter(user__is_staff=False, user__is_superuser=False, user__last_login__isnull=False).count(),
        'email_confirmed': Expert.objects.filter(user__is_staff=False, user__is_superuser=False, user__email_confirmed=True).count(),
        'profile_submitted': ProfileUpdate.objects.filter(expert__user__is_staff=False, expert__user__is_superuser=False, status__in=['SUBMITTED', 'UNDER_REVIEW']).count(),
        'profile_validated': ProfileUpdate.objects.filter(expert__user__is_staff=False, expert__user__is_superuser=False, status='COMPLETE').count(),
        'profile_counts': dict(profile_counts), 'sessions_count': ActivitySession.objects.filter(user__in=Expert.objects.filter(user__is_staff=False, user__is_superuser=False).values('user_id')).values('user_id').distinct().count(),
        'minutes_total': round((ActivitySession.objects.filter(user__in=Expert.objects.filter(user__is_staff=False, user__is_superuser=False).values('user_id')).aggregate(n=Sum('active_seconds'))['n'] or 0) / 60),
        'editions_total': NormeVersion.all_objects.filter(version_author__in=Expert.objects.filter(user__is_staff=False, user__is_superuser=False).values('user_id')).count(),
        'extracted_at': timezone.localtime(),
    })


@login_required(login_url='web:expert_login')
def intelligence_report_word(request):
    _require_intelligence(request)
    kind = request.GET.get('rapport', 'cabinet')
    if kind not in {'cabinet', 'general', 'experts', 'sc', 'production', 'decisions'}:
        raise Http404
    version = _reference_version()
    rows, groups, _ = _snapshot(version)
    payload = {
        'kind': kind, 'version': version, 'rows': rows,
        'group_count': len(groups),
        'expert_count': Expert.objects.filter(user__is_staff=False, user__is_superuser=False).count(),
        'connected_count': Expert.objects.filter(user__is_staff=False, user__is_superuser=False, user__last_login__isnull=False).count(),
        'project_count': Norme.all_objects.count(), 'version_count': NormeVersion.all_objects.count(),
        'adopted_count': Norme.all_objects.filter(status__in=['ADOPTED', 'HOMOLOGATED', 'PUBLISHED']).count(),
        'review_count': AffectationSousCommission.objects.filter(version=version, status='REVIEW').count() if version else 0,
        'extracted_at': timezone.localtime(),
    }
    content = build_report_docx(payload)
    response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="CNE-ITP-rapport-{kind}.docx"'
    return response


def _fold(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c))


@login_required(login_url='web:expert_login')
@require_POST
def intelligence_assistant(request):
    _require_intelligence(request)
    question = request.POST.get('question', '').strip()[:500]
    if not question:
        return JsonResponse({'answer': 'Saisissez une question.', 'sources': []}, status=400)
    version = _reference_version()
    rows, groups, dossiers = _snapshot(version)
    query = _fold(question)
    source = reverse('dashboard:intelligence')
    chart = None
    if 'compare' in query or 'participation' in query or 'sous-commission' in query:
        answer = 'Comparaison des sept sous-commissions selon les mesures journalières liées à leurs GT. Une valeur nulle peut signifier que le suivi n’a pas encore produit de mesure.'
        table = [{'sc': r['sc'].code, 'affectations_a_examiner': r['review'], 'experts_mesures': r['measured_people'], 'minutes_mesurees': r['minutes'], 'dossiers': r['dossiers']} for r in rows]
        chart = {'type': 'bar', 'title': 'Minutes mesurées par sous-commission', 'labels': [r['sc'].code for r in rows], 'values': [r['minutes'] for r in rows]}
        source += '?section=organisation'
    elif 'president' in query or 'poste' in query:
        vacant = [g.code for g in groups if not MandatOrganisation.objects.filter(groupe=g, status='ACTIVE', function__icontains='président').exists()]
        answer = f'{len(vacant)} GT sans mandat actif de président enregistré dans le référentiel {version.get_status_display() if version else "absent"}.'
        table = [{'gt': code} for code in vacant]
        source += '?section=organisation'
    elif 'expert' in query or 'connexion' in query:
        total = Expert.objects.filter(user__is_staff=False, user__is_superuser=False).count()
        connected = Expert.objects.filter(user__is_staff=False, user__is_superuser=False, user__last_login__isnull=False).count()
        answer = f'{total} experts hors comptes administrateurs ; {connected} ont une dernière connexion enregistrée.'
        table = []
        source += '?section=experts'
    elif 'copil' in query or 'decision' in query:
        pending = Norme.all_objects.filter(status='PILOTAGE_REVIEW')
        answer = f'{pending.count()} projet(s) portent le statut « validation Comité Pilotage ». Ce statut ne prouve pas qu’une décision formelle soit déjà inscrite.'
        table = [{'reference': n.reference_number, 'titre': n.title[:90]} for n in pending[:20]]
        source += '?section=production'
    elif 'norme' in query or 'projet' in query:
        statuses = list(Norme.all_objects.values('status').annotate(n=Count('id')).order_by('status'))
        answer = f'{Norme.all_objects.count()} projets de normes et {NormeVersion.all_objects.count()} versions enregistrés. Un projet enregistré ne signifie pas une norme adoptée.'
        table = [{'statut': dict(Norme.STATUS_CHOICES).get(r['status'], r['status']), 'projets': r['n']} for r in statuses]
        chart = {'type': 'bar', 'title': 'Projets par statut', 'labels': [row['statut'] for row in table], 'values': [row['projets'] for row in table]}
        source += '?section=production'
    elif 'observation' in query or 'commentaire' in query:
        answer = f'{NormeComment.objects.count()} commentaire(s) de norme enregistré(s). Le modèle ne suit pas un état de résolution ; impossible de compter les points non résolus.'
        table = []
        source += '?section=observations'
    elif 'cabinet' in query or 'rapport' in query or 'synthese' in query:
        answer = f'Note disponible en prévisualisation : {len(rows)} sous-commissions, {len(groups)} GT, {Norme.all_objects.count()} projets. Référentiel : {version.get_status_display() if version else "absent"}.'
        table = []
        source += '?section=rapports&rapport=cabinet'
    else:
        answer = 'Je peux répondre brièvement sur les experts, les sept sous-commissions, les présidences de GT, les projets de normes, les observations et la note Cabinet. Précisez votre question.'
        table = []
    logger.info('intelligence_query user_id=%s source=%s', request.user.pk, source)
    return JsonResponse({'answer': answer, 'table': table, 'chart': chart, 'sources': [{'label': 'Données CNE-ITP · extraction du ' + timezone.localtime().strftime('%d/%m/%Y %H:%M'), 'url': source}]})


@login_required(login_url='web:expert_login')
def intelligence_document(request, pk):
    _require_intelligence(request)
    document = get_object_or_404(_document_queryset(request.user), pk=pk)
    if not document.file:
        raise Http404
    try:
        suffix = document.file.name.rsplit('.', 1)[-1].lower()
        preview = request.GET.get('preview') == '1' and (
            (document.file_type == 'PDF' and suffix == 'pdf')
            or (document.file_type == 'IMAGE' and suffix in {'png', 'jpg', 'jpeg', 'webp'})
        )
        response = FileResponse(document.file.open('rb'), as_attachment=not preview, filename=document.file.name.rsplit('/', 1)[-1])
        if preview:
            response['X-Frame-Options'] = 'SAMEORIGIN'
        return response
    except FileNotFoundError:
        raise Http404


def intelligence_document_media(request, path):
    """Guard legacy /media/documents/... URLs that otherwise bypass view permissions."""
    if '..' in path.split('/'):
        raise Http404
    document = get_object_or_404(DocumentFile.objects.all(), file='documents/' + path)
    if not document.is_public:
        if not request.user.is_authenticated:
            raise PermissionDenied
        if not _document_queryset(request.user).filter(pk=document.pk).exists():
            raise PermissionDenied
    try:
        return FileResponse(document.file.open('rb'), as_attachment=False)
    except FileNotFoundError:
        raise Http404

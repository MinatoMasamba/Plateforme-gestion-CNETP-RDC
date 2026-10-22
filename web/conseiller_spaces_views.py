"""Cinq espaces de travail fonctionnels pour les conseillers du COPIL.

Les espaces sont des compositions de présentation. Ils ne créent aucun
mandat, ne remplacent pas les postes officiels et ne donnent jamais le
pouvoir de valider une norme. Les droits restent vérifiés par le serveur à
chaque lecture et à chaque écriture.
"""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.experts.models import Expert
from apps.governance.models import CTM, AvisConseiller, DemandeAnalyse, PosteNominatif, Tache
from apps.norms.models import Norme, NormeComment, NormeVersion
from apps.validation.models import (
    EcologicalReview, EconomicReview, IndustrialConsultation, ISOReview,
    LegisticReview,
)
from web.pilotage_views import get_pilotage_context


_PARTENAIRE_POSTES = {
    23: ("ONA", "Ordre National des Architectes"),
    24: ("Syndicats", "Syndicats et organismes de régulation"),
    25: ("BEAU", "Bureau d'Études d'Aménagement Urbain"),
    26: ("FEC", "Fédération des Entreprises du Congo"),
    27: ("OCC", "Office Congolais de Contrôle"),
}

_ATF_POSTES = {
    18: ("OR", "Office des Routes"),
    19: ("OVD", "Office des Voiries et Drainage"),
    20: ("ACGT", "Agence Congolaise des Grands Travaux"),
    21: ("BTC", "Bureau Technique de Contrôle"),
    22: ("FONER", "Fonds National d'Entretien Routier"),
}
_ATF_SCOPE_CTM = {18: [1], 19: [7], 20: [1, 2, 3], 21: list(range(1, 9))}

_SPACE_DEFINITIONS = [
    {
        'key': 'expertise',
        'list_tab': 'dossiers',
        'profil': AvisConseiller.Profil.EXPERTISE,
        'persona': 'Conseiller technique · Expertise technique',
        'title': 'Expertise technique',
        'short': 'Expertise',
        'lead': 'Examiner la pertinence technique des projets de normes et préparer des avis pour le COPIL.',
        'accent': 'azure',
        'glyph': '◆',
        'scope': 'Dossiers techniques',
        'menu': [
            ('overview', 'Tableau de bord'),
            ('dossiers', 'Dossiers normatifs'),
            ('analyse', 'Analyse technique'),
            ('avis', 'Avis et recommandations'),
            ('documents', 'Documents de référence'),
        ],
        'functions': [
            'Consulter les projets de normes et leurs versions',
            'Comparer les observations des experts',
            'Rédiger un avis technique motivé',
            'Transmettre une recommandation au circuit de décision',
        ],
    },
    {
        'key': 'coordination',
        'list_tab': 'contributions',
        'profil': AvisConseiller.Profil.COORDINATION,
        'persona': 'Conseiller technique · Coordination institutionnelle',
        'title': 'Coordination institutionnelle',
        'short': 'Coordination',
        'lead': 'Suivre les contributions, les échéances et les rapports institutionnels sans programmer les actes du Directoire.',
        'accent': 'teal',
        'glyph': '◎',
        'scope': 'Contributions et échéances',
        'menu': [
            ('overview', 'Tableau de bord'),
            ('contributions', 'Contributions attendues'),
            ('calendrier', 'Calendrier'),
            ('rapports', 'Rapports'),
            ('avis', 'Avis et recommandations'),
        ],
        'functions': [
            'Consulter les dossiers de son périmètre',
            'Suivre les contributions et les échéances',
            'Déposer une observation datée',
            'Préparer un avis institutionnel distinct des décisions du Directoire',
        ],
    },
    {
        'key': 'conformite',
        'list_tab': 'conformite',
        'profil': AvisConseiller.Profil.CONFORMITE,
        'persona': 'Conseiller technique · Conformité et réglementation',
        'title': 'Conformité et réglementation',
        'short': 'Conformité',
        'lead': 'Examiner les obligations, les réserves et les pièces de conformité du périmètre confié.',
        'accent': 'amber',
        'glyph': '⚖',
        'scope': 'Points de conformité',
        'menu': [
            ('overview', 'Tableau de bord'),
            ('conformite', 'Dossiers de conformité'),
            ('reserves', 'Réserves'),
            ('legistique', 'Légistique'),
            ('avis', 'Avis et recommandations'),
        ],
        'functions': [
            'Lire les examens environnementaux, fonciers, territoriaux ou juridiques',
            'Consigner une réserve motivée',
            'Préparer un avis de conformité',
            'Accéder au module légistique uniquement lorsque le mandat le prévoit',
        ],
    },
    {
        'key': 'controle',
        'list_tab': 'specialite',
        'profil': AvisConseiller.Profil.CONTROLE,
        'persona': 'Conseiller technique · Contrôle technique et financier',
        'title': 'Contrôle technique et financier',
        'short': 'Contrôle',
        'lead': "Suivre les dossiers de spécialité, les contrôles techniques et les évaluations financières autorisées.",
        'accent': 'violet',
        'glyph': '▣',
        'scope': 'Dossiers de spécialité',
        'menu': [
            ('overview', 'Tableau de bord'),
            ('specialite', 'Dossiers de spécialité'),
            ('essais', 'Essais et contrôles'),
            ('finance', 'Études financières'),
            ('avis', 'Avis et recommandations'),
        ],
        'functions': [
            'Consulter les dossiers relevant du domaine du poste',
            'Examiner les contrôles techniques enregistrés',
            'Lire les évaluations financières autorisées',
            'Préparer un avis technique ou financier',
        ],
    },
    {
        'key': 'partenaires',
        'list_tab': 'contributions',
        'profil': AvisConseiller.Profil.PARTENAIRES,
        'persona': 'Conseiller technique · Partenaires et expertise',
        'title': 'Partenaires et expertise',
        'short': 'Partenaires',
        'lead': 'Consulter les dossiers partagés et suivre les contributions sectorielles expressément autorisées.',
        'accent': 'emerald',
        'glyph': '◈',
        'scope': 'Contributions sectorielles',
        'menu': [
            ('overview', 'Tableau de bord'),
            ('consultations', 'Consultations'),
            ('contributions', 'Contributions'),
            ('documents', 'Documents partagés'),
            ('avis', 'Avis et recommandations'),
        ],
        'functions': [
            'Consulter les dossiers et documents partagés',
            'Suivre les consultations auxquelles le poste est associé',
            'Apporter une contribution sectorielle',
            "Préparer un avis consultatif, sans vote ni validation",
        ],
    },
]


_TAB_LEADS = {
    ('expertise', 'overview'): "Vue synthétique de l'activité du profil et des dossiers à examiner.",
    ('expertise', 'dossiers'): 'Projets de normes du périmètre, filtrables par statut et par CTM.',
    ('expertise', 'analyse'): "Lecture du dossier sélectionné, de sa dernière version et de l'état des examens.",
    ('expertise', 'avis'): 'Rédaction et suivi des avis techniques destinés au circuit de décision.',
    ('expertise', 'documents'): 'Versions et pièces de référence du dossier sélectionné.',
    ('coordination', 'overview'): 'Vue synthétique des contributions, échéances et rapports du périmètre.',
    ('coordination', 'contributions'): 'Contributions attendues et dossiers suivis par le profil.',
    ('coordination', 'calendrier'): 'Échéances enregistrées, sans déduction automatique des dates absentes.',
    ('coordination', 'rapports'): "Rapports d'analyse liés au compte et au circuit consultatif.",
    ('coordination', 'avis'): 'Avis institutionnels distincts des décisions du Directoire.',
    ('conformite', 'overview'): 'Vue synthétique des points de conformité et des réserves du périmètre.',
    ('conformite', 'conformite'): 'Dossiers soumis à un examen de conformité ou de réglementation.',
    ('conformite', 'reserves'): 'Réserves et observations consignées sur le dossier sélectionné.',
    ('conformite', 'legistique'): 'Toilettage légistique et obligations applicables au dossier sélectionné.',
    ('conformite', 'avis'): 'Avis de conformité préparatoires, sans pouvoir de validation.',
    ('controle', 'overview'): "Vue synthétique des dossiers de spécialité et des contrôles enregistrés.",
    ('controle', 'specialite'): 'Dossiers relevant des CTM et du domaine du poste.',
    ('controle', 'essais'): 'Examens techniques enregistrés sur le dossier sélectionné.',
    ('controle', 'finance'): 'Évaluations financières et domaines autorisés du profil.',
    ('controle', 'avis'): 'Avis techniques et financiers préparatoires au circuit de décision.',
    ('partenaires', 'overview'): 'Vue synthétique des consultations et contributions sectorielles.',
    ('partenaires', 'consultations'): 'Consultations industrielles et sectorielles enregistrées.',
    ('partenaires', 'contributions'): 'Dossiers du périmètre et contribution sectorielle associée.',
    ('partenaires', 'documents'): 'Documents partagés pour le dossier sélectionné.',
    ('partenaires', 'avis'): 'Avis consultatifs, sans vote ni validation.',
}

SPACES = {space['key']: space for space in _SPACE_DEFINITIONS}
SPACE_ORDER = [space['key'] for space in _SPACE_DEFINITIONS]
_DIRECTOIRE_ROLES = {'PRESIDENT', 'VICE_PRESIDENT', 'SECRETARY', 'RAPPORTEUR'}
_GOLD_STATUSES = {'PUBLISHED', 'HOMOLOGATED', 'ADOPTED'}
_CLOSED_STATUSES = {'ARCHIVED'}
_REVIEW_LABELS = [
    ('legistic_review', 'Toilettage légistique'),
    ('iso_review', 'Veille ISO / SADC'),
    ('ecological_review', 'Sauvegardes écologiques'),
    ('economic_review', 'Évaluation financière'),
]


def _expert(request):
    expert = (
        Expert.objects.filter(user=request.user, status='ACTIVE', user__is_active=True)
        .select_related('user', 'structure')
        .first()
    )
    if not expert:
        raise PermissionDenied("Compte expert actif requis.")
    return expert


def _pilotage_context(expert):
    context = get_pilotage_context(expert)
    if not context:
        raise PermissionDenied("Accès réservé aux membres du Comité de Pilotage.")
    return context


def _space_keys(expert, context):
    """Return the sole interface supported by the confirmed Pilotage mandate."""
    role = context['membership'].role
    poste = context.get('poste')
    order = poste.order if poste else None
    if role == 'CONSEILLER' and expert.user.is_superuser:
        # Design preview for administrators; the generic counsellor keeps
        # the transversal dashboard at /pilotage/.
        return ['expertise']
    if (not poste or PosteNominatif.objects.filter(
        holder=expert, comite=context['membership'].comite, role=role,
    ).count() != 1):
        return []
    if role == 'CONSEILLER_POLITIQUE':
        if order in (6, 7):
            return ['expertise']
        if order is not None and 8 <= order <= 12:
            return ['coordination']
        if order is not None and 13 <= order <= 17:
            return ['conformite']
        # A title alone is not a confirmed nomination to a numbered post.
        return []
    if role == 'ADMIN_TECH_FIN':
        return ['controle']
    if role == 'PARTENAIRE_SOC_CIV':
        return ['partenaires']
    return []


def _default_space(keys):
    return keys[0] if keys else ''


def _selected_space(request, keys):
    requested = request.GET.get('espace')
    if requested and requested != keys[0]:
        raise PermissionDenied("Cet espace ne relève pas du mandat connecté.")
    return SPACES[keys[0]]


def _space_for_post(space, context):
    """Keep navigation limited to modules relevant to the numbered post."""
    poste = context.get('poste')
    if not poste:
        return space
    order = poste.order
    hidden = set()
    if space['key'] == 'coordination':
        hidden.add('rapports' if order == 8 else 'calendrier')
    elif space['key'] == 'conformite' and order not in (16, 17):
        hidden.add('legistique')
    elif space['key'] == 'controle':
        hidden.add('essais' if order == 22 else 'finance')
    elif space['key'] == 'partenaires' and order != 26:
        hidden.add('consultations')
    return {**space, 'persona': poste.title,
            'menu': [item for item in space['menu'] if item[0] not in hidden]}


def _poste_scope_labels(expert, context, space_key):
    role = context['membership'].role
    poste = context.get('poste')
    order = poste.order if poste else None
    if space_key == 'controle':
        if order in _ATF_POSTES:
            return _ATF_POSTES[order]
        acronym = (expert.structure.acronym or '').upper() if expert.structure else ''
        for number, (code, label) in _ATF_POSTES.items():
            if code == acronym:
                return code, label
        return 'Spécialité', 'Contrôle technique et financier'
    if space_key == 'partenaires':
        if order in _PARTENAIRE_POSTES:
            return _PARTENAIRE_POSTES[order]
        acronym = (expert.structure.acronym or '').upper() if expert.structure else ''
        for number, (code, label) in _PARTENAIRE_POSTES.items():
            if code == acronym:
                return code, label
        return 'Partenaire', 'Contribution sectorielle'
    if space_key == 'conformite' and context.get('user_sub_role') == 'juridique':
        return 'Légistique', 'Conformité juridique et réglementaire'
    if order:
        return f'Poste {order}', role.replace('_', ' ').title()
    return 'Profil fonctionnel', role.replace('_', ' ').title()


def _scoped_norms(expert, context, space_key):
    norms = Norme.all_objects.select_related('ctm', 'wg').exclude(status__in=_CLOSED_STATUSES)
    order = context['poste'].order if context.get('poste') else None
    if space_key == 'controle':
        if order == 22:
            norms = norms.filter(economic_review__isnull=False)
        elif order in _ATF_SCOPE_CTM:
            norms = norms.filter(ctm__number__in=_ATF_SCOPE_CTM[order])
        else:
            norms = norms.none()
    elif space_key == 'partenaires':
        if order == 26:
            norms = norms.filter(industrial_consultation__isnull=False)
    return norms.distinct()


def _status_tone(status):
    if status in _GOLD_STATUSES:
        return 'positive'
    if status in {'PUBLIC_INQUIRY', 'PILOTAGE_REVIEW', 'FINAL_REVIEW'}:
        return 'attention'
    if status in {'DRAFT', 'INTERNAL_REVIEW'}:
        return 'neutral'
    return 'info'


def _review_rows(norme):
    rows = []
    for attribute, label in _REVIEW_LABELS:
        review = getattr(norme, attribute, None)
        rows.append({
            'label': label,
            'review': review,
            'status': review.get_status_display() if review else 'Non configuré',
            'tone': _status_tone(review.status) if review else 'empty',
        })
    return rows


def _kpi(label, value, hint, tone=''):
    return {'label': label, 'value': value, 'hint': hint, 'tone': tone}


def _scoped_task_queryset(expert, context, norms):
    tasks = Tache.objects.filter(norme__in=norms).select_related('norme', 'target_group__sc')
    if context['membership'].role == 'CONSEILLER':
        tasks = tasks.filter(Q(assigned_to=expert) | Q(backup_assignee=expert))
    return tasks


def _workspace_data(request, expert, context, space):
    key = space['key']
    scoped = _scoped_norms(expert, context, key)
    query = (request.GET.get('q') or '').strip()
    status = (request.GET.get('statut') or '').strip()
    ctm_number = (request.GET.get('ctm') or '').strip()
    norms = scoped.order_by('-updated_at', '-pk')
    if query:
        norms = norms.filter(
            Q(reference_number__icontains=query)
            | Q(title__icontains=query)
            | Q(description__icontains=query)
        )
    if status:
        norms = norms.filter(status=status)
    if ctm_number.isdigit():
        norms = norms.filter(ctm__number=int(ctm_number))
    norms = list(norms[:80])

    selected = None
    selected_raw = (request.GET.get('norme') or '').strip()
    if selected_raw.isdecimal():
        selected = next((item for item in norms if item.pk == int(selected_raw)), None)
        if selected is None:
            selected = scoped.filter(pk=int(selected_raw)).first()
    if selected is None and norms:
        selected = norms[0]

    versions = []
    comments = []
    tasks = []
    reviews = []
    documents = []
    if selected:
        versions = list(
            NormeVersion.all_objects.filter(norme=selected)
            .select_related('version_author')
            .order_by('-version_number')[:12]
        )
        comments = list(
            NormeComment.objects.filter(norme=selected)
            .select_related('author__user')
            .order_by('-created_at')[:8]
        )
        tasks = list(
            Tache.objects.filter(norme=selected)
            .select_related('assigned_to__user', 'target_group__sc')
            .order_by('status', 'due_date')[:8]
        )
        reviews = _review_rows(selected)
        documents = [version for version in versions if version.document]

    my_avis = list(
        AvisConseiller.objects.filter(auteur=expert, profil=space['profil'])
        .select_related('norme')
        .order_by('-created_at')[:20]
    )
    norme_avis = []
    if selected:
        norme_avis = list(
            AvisConseiller.objects.filter(norme=selected, statut=AvisConseiller.Statut.SOUMIS)
            .select_related('auteur__user')
            .order_by('-soumis_le', '-created_at')[:12]
        )
    analyses = list(
        DemandeAnalyse.objects.filter(Q(emetteur=expert) | Q(destinataire=expert))
        .select_related('emetteur__user', 'destinataire__user', 'norme')
        .order_by('-created_at')[:12]
    )
    consultations = list(
        IndustrialConsultation.objects.select_related('norme', 'expert__user')
        .order_by('-updated_at')[:12]
    )
    if context.get('poste') and context['poste'].order == 26:
        consultations = [item for item in consultations if item.expert_id == expert.pk]
    elif key == 'partenaires':
        consultations = []

    open_tasks = _scoped_task_queryset(expert, context, scoped)
    today = timezone.localdate()
    upcoming = open_tasks.exclude(status='COMPLETED').filter(
        due_date__gte=today, due_date__lte=today + timedelta(days=14),
    )
    comment_count = NormeComment.objects.filter(norme__in=scoped).count()
    pending_reviews = 0
    for model in (LegisticReview, ISOReview, EcologicalReview, EconomicReview):
        pending_reviews += model.objects.filter(
            norme__in=scoped, status__in=['PENDING', 'ASSIGNED', 'IN_REVIEW'],
        ).count()

    avis_drafts = sum(1 for item in my_avis if item.statut == AvisConseiller.Statut.BROUILLON)
    avis_sent = sum(1 for item in my_avis if item.statut == AvisConseiller.Statut.SOUMIS)
    if key == 'expertise':
        kpis = [
            _kpi('Dossiers techniques', scoped.count(), 'Normes non archivées du périmètre.'),
            _kpi('Avis à préparer', avis_drafts, 'Brouillons personnels de ce profil.'),
            _kpi('Observations ouvertes', comment_count, 'Commentaires internes enregistrés.'),
        ]
    elif key == 'coordination':
        kpis = [
            _kpi('Contributions attendues', upcoming.count(), 'Tâches échues dans les 14 jours.'),
            _kpi('Échéances proches', open_tasks.exclude(status='COMPLETED').filter(due_date__lt=today).count(),
                 'Tâches non terminées dont l’échéance est dépassée.'),
            _kpi('Avis transmis', avis_sent, 'Avis de ce profil transmis au circuit.'),
        ]
    elif key == 'conformite':
        kpis = [
            _kpi('Points à examiner', pending_reviews, 'Examens de conformité non terminés.'),
            _kpi('Réserves consignées', comment_count, 'Commentaires et réserves enregistrés.'),
            _kpi('Avis de conformité', avis_sent, 'Avis de ce profil transmis au circuit.'),
        ]
    elif key == 'controle':
        economic_count = EconomicReview.objects.filter(norme__in=scoped).count()
        kpis = [
            _kpi('Dossiers de spécialité', scoped.count(), 'Normes du périmètre technique autorisé.'),
            _kpi('Contrôles en attente', pending_reviews, 'Examens techniques non terminés.'),
            _kpi('Évaluations financières', economic_count, 'Évaluations économiques enregistrées.'),
        ]
    else:
        is_fec = context.get('poste') and context['poste'].order == 26
        kpis = [
            _kpi('Consultations suivies' if is_fec else 'Dossiers partagés',
                 len(consultations) if is_fec else scoped.count(),
                 'Consultations industrielles enregistrées.' if is_fec else 'Normes non archivées du périmètre.'),
            _kpi('Avis transmis', avis_sent, 'Avis de ce profil transmis au circuit.'),
            _kpi('Demandes d’analyse', len(analyses), 'Demandes liées au compte connecté.'),
        ]

    ctm_options = (
        CTM.objects.filter(normes__in=scoped).distinct().order_by('number')
        if scoped.exists() else CTM.objects.none()
    )
    return {
        'space': space,
        'kpis': kpis,
        'norms': norms,
        'selected_norm': selected,
        'versions': versions,
        'comments': comments,
        'tasks': tasks,
        'reviews': reviews,
        'documents': documents,
        'my_avis': my_avis,
        'norme_avis': norme_avis,
        'analyses': analyses,
        'consultations': consultations,
        'ctm_options': ctm_options,
        'filters': {'q': query, 'statut': status, 'ctm': ctm_number},
        'has_data': scoped.exists(),
        'total_scoped': scoped.count(),
    }


@login_required(login_url='/se-connecter/')
@require_GET
def conseiller_spaces(request):
    expert = _expert(request)
    context = _pilotage_context(expert)
    keys = _space_keys(expert, context)
    if not keys:
        raise PermissionDenied("Aucun espace conseiller n'est associé à ce mandat.")
    space = _space_for_post(_selected_space(request, keys), context)
    menu = dict(space['menu'])
    active_vue = (request.GET.get('vue') or 'overview').strip()
    if active_vue not in menu:
        active_vue = 'overview'
    data = _workspace_data(request, expert, context, space)
    poste_code, poste_label = _poste_scope_labels(expert, context, space['key'])
    return render(request, 'pilotage/espaces/workspace.html', {
        **data,
        'expert': expert,
        'membership': context['membership'],
        'preview_mode': context['membership'].role == 'CONSEILLER',
        'allowed_space_keys': keys,
        'poste_code': poste_code,
        'poste_label': poste_label,
        'profile_unconfirmed': not context.get('poste'),
        'status_choices': Norme.STATUS_CHOICES,
        'recommandations': AvisConseiller.Recommandation.choices,
        'avis_status': AvisConseiller.Statut,
        'active_vue': active_vue,
        'active_label': menu[active_vue],
        'active_lead': _TAB_LEADS.get((space['key'], active_vue), space['lead']),
    })


@login_required(login_url='/se-connecter/')
@require_POST
@transaction.atomic
def conseiller_space_avis(request):
    expert = _expert(request)
    context = _pilotage_context(expert)
    if context['membership'].role == 'CONSEILLER':
        raise PermissionDenied("L'aperçu administrateur ne permet pas de rédiger un avis spécialisé.")
    keys = _space_keys(expert, context)
    space_key = (request.POST.get('espace') or '').strip()
    if space_key not in keys:
        raise PermissionDenied("Cet espace ne relève pas du mandat connecté.")
    space = SPACES[space_key]
    scoped = _scoped_norms(expert, context, space_key)
    norme = get_object_or_404(scoped, pk=request.POST.get('norme'))
    objet = (request.POST.get('objet') or '').strip()
    analyse = (request.POST.get('analyse') or '').strip()
    recommandation = (request.POST.get('recommandation') or '').strip()
    action = (request.POST.get('action') or 'brouillon').strip()
    if not objet or not analyse:
        messages.error(request, "Renseignez l'objet et l'analyse motivée.")
        return redirect(f"{reverse('web:conseiller_spaces')}?espace={space_key}&vue=avis&norme={norme.pk}#avis")
    if len(objet) > 250:
        messages.error(request, "L'objet ne peut pas dépasser 250 caractères.")
        return redirect(f"{reverse('web:conseiller_spaces')}?espace={space_key}&vue=avis&norme={norme.pk}#avis")
    if recommandation not in dict(AvisConseiller.Recommandation.choices):
        raise PermissionDenied("Recommandation invalide.")
    if action not in {'brouillon', 'soumettre'}:
        raise PermissionDenied("Action invalide.")
    statut = AvisConseiller.Statut.SOUMIS if action == 'soumettre' else AvisConseiller.Statut.BROUILLON
    avis = AvisConseiller.objects.create(
        norme=norme,
        auteur=expert,
        profil=space['profil'],
        objet=objet,
        analyse=analyse,
        recommandation=recommandation,
        statut=statut,
        soumis_le=timezone.now() if statut == AvisConseiller.Statut.SOUMIS else None,
        created_by=request.user,
        updated_by=request.user,
    )
    if statut == AvisConseiller.Statut.SOUMIS:
        messages.success(request, "L'avis a été transmis au circuit de décision. Il ne vaut pas validation.")
    else:
        messages.success(request, "Le brouillon d'avis a été enregistré.")
    return redirect(f"{reverse('web:conseiller_spaces')}?espace={space_key}&vue=avis&norme={norme.pk}#avis-{avis.pk}")


__all__ = ['SPACES', 'SPACE_ORDER', 'conseiller_spaces', 'conseiller_space_avis']

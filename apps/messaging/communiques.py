"""Construction et envoi du communiqué de transition organisationnelle."""

import io
from datetime import date
from xml.sax.saxutils import escape as xml_escape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from api.v1.pdf_utils import (
    GOLD_CNETP,
    _base_styles,
    _header_block,
    _page_footer,
)
from apps.governance.models import GroupeCible, Organe, PosteOrganisation
from apps.governance.phoenix_models import OrganisationVersion
from apps.governance.phoenix_runtime import current_organisation_version

from .models import CommuniqueEnvoi

MOIS_FR = (
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
)


def _french_date(value):
    return f"{value.day} {MOIS_FR[value.month - 1]} {value.year}"


def expert_email(expert):
    user = getattr(expert, 'user', None)
    if not user:
        return ''
    email = (user.email or '').strip()
    if not email:
        candidate = (user.username or '').strip()
        if '@' in candidate:
            email = candidate
    return email


def build_context(version=None, numero=None, date_communique=None):
    version = version or current_organisation_version()
    if not version:
        raise ValueError("Aucune version d'organisation n'est disponible.")
    scs = list(
        Organe.objects.filter(version=version, type=Organe.Type.SC)
        .exclude(status=OrganisationVersion.Status.ARCHIVED)
        .prefetch_related('groupes')
        .order_by('code')
    )
    gt_count = GroupeCible.objects.filter(sc__version=version).count()
    post_count = PosteOrganisation.objects.filter(
        organe__version=version,
        organe__type__in=[Organe.Type.COPIL, Organe.Type.ST, Organe.Type.ST_POLE],
    ).count()
    site_url = (getattr(settings, 'SITE_URL', '') or '').rstrip('/')
    numero = str(numero or getattr(settings, 'COMMUNIQUE_OFFICIEL_NUMERO', '002')).strip()
    raw_date = date_communique or getattr(settings, 'COMMUNIQUE_OFFICIEL_DATE', '2026-10-16')
    if isinstance(raw_date, str):
        parsed_date = parse_date(raw_date)
    elif isinstance(raw_date, date):
        parsed_date = raw_date
    else:
        parsed_date = None
    parsed_date = parsed_date or timezone.localdate()
    date_label = _french_date(parsed_date)
    subject = f"CNE-ITP | Communiqué officiel N° {numero} du {date_label}."
    context = {
        'version': version,
        'version_code': version.code,
        'version_name': version.name,
        'version_status': version.get_status_display(),
        'sc_count': len(scs),
        'gt_count': gt_count,
        'post_count': post_count,
        'sous_commissions': [
            {
                'code': sc.code,
                'name': sc.official_name or sc.name,
                'groupes': [
                    {'code': groupe.code, 'name': groupe.name}
                    for groupe in sc.groupes.all().order_by('code')
                ],
            }
            for sc in scs
        ],
        'site_url': site_url,
        'platform_url': f'{site_url}/app/' if site_url else '/app/',
        'profile_url': f'{site_url}/profil/' if site_url else '/profil/',
        'logo_url': f'{site_url}/static/img/logo-cnetp.png' if site_url else '/static/img/logo-cnetp.png',
        'annee': timezone.localdate().year,
        'date_communique': parsed_date,
        'communique_numero': numero,
        'communique_date_label': date_label,
        'subject': subject,
    }
    return context


def build_pdf(context):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2.5 * cm,
    )
    styles = _base_styles()
    elements = _header_block(
        styles,
        f"COMMUNIQUÉ OFFICIEL N° {context['communique_numero']}",
        f"Transition vers la nouvelle organisation de la CNE-ITP — {context['communique_date_label']}",
    )
    elements.append(Paragraph(
        f"<b>Version organisationnelle :</b> {xml_escape(context['version_name'])} "
        f"({xml_escape(context['version_code'])}) — {xml_escape(context['version_status'])}",
        styles['BodySmall'],
    ))
    elements.append(Spacer(1, 0.35 * cm))
    elements.append(Paragraph(
        "À l'attention des experts et des membres de la plateforme CNE-ITP,",
        styles['BodySmall'],
    ))
    elements.append(Spacer(1, 0.25 * cm))
    elements.append(Paragraph(
        "La nouvelle organisation de la Commission nationale d'élaboration des normes "
        "des infrastructures de travaux publics est désormais structurée en "
        f"<b>{context['sc_count']} sous-commissions techniques</b> et "
        f"<b>{context['gt_count']} groupes de travail</b>. Les anciennes versions sont archivées "
        "et ne sont plus utilisées par les interfaces de la plateforme.",
        styles['BodySmall'],
    ))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("Ce qui change", styles['SectionHeader']))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=GOLD_CNETP, spaceAfter=6))
    for line in (
        "Les sous-commissions techniques et leurs groupes de travail deviennent le cadre unique de travail.",
        "Les affectations et les postes de coordination sont lus depuis la version organisationnelle courante.",
        "Les données historiques sont conservées dans les archives de la plateforme.",
    ):
        elements.append(Paragraph(f"• {xml_escape(line)}", styles['BodySmall']))
        elements.append(Spacer(1, 0.15 * cm))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph("Vos étapes sur la plateforme", styles['SectionHeader']))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=GOLD_CNETP, spaceAfter=6))
    for index, line in enumerate((
        "Connectez-vous à la plateforme avec votre compte habituel.",
        "Vérifiez et actualisez vos informations professionnelles et votre CV.",
        "Consultez votre sous-commission et votre groupe de travail.",
        "Suivez l'état de vos dossiers et de vos contributions.",
        "Contactez la coordination du Secrétariat technique en cas de difficulté.",
    ), start=1):
        elements.append(Paragraph(f"{index}. {xml_escape(line)}", styles['BodySmall']))
        elements.append(Spacer(1, 0.15 * cm))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph(
        f"Plateforme CNE-ITP : {xml_escape(context['platform_url'])}",
        styles['BodySmall'],
    ))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph(
        "Le présent communiqué est également disponible en version HTML et en texte dans "
        "le courrier électronique auquel il est joint.",
        styles['BodySmall'],
    ))
    doc.build(elements, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return buffer.getvalue()


def render_email(expert, context):
    per_expert = dict(context)
    per_expert['expert'] = expert
    per_expert['greeting_name'] = expert.full_name or expert.user.get_full_name() or expert.user.username
    html = render_to_string('emails/communique_nouvelle_organisation.html', per_expert)
    text = render_to_string('emails/communique_nouvelle_organisation.txt', per_expert)
    return html, text


def send_to_expert(expert, communique_key, context, force=False):
    email = expert_email(expert)
    record = CommuniqueEnvoi.objects.filter(
        communique_key=communique_key, email=email,
    ).first() if email else None

    if not email:
        if record is None:
            CommuniqueEnvoi.objects.create(
                communique_key=communique_key, subject=context['subject'],
                recipient=expert.user, email='', status=CommuniqueEnvoi.STATUS_SKIPPED,
                error="Aucune adresse email disponible.",
            )
        return {'status': 'skipped', 'reason': 'email absent'}

    if record and record.status == CommuniqueEnvoi.STATUS_SENT and not force:
        return {'status': 'skipped', 'reason': 'déjà envoyé'}

    html, text = render_email(expert, context)
    pdf_bytes = build_pdf(context)
    filename = f"communique_organisation_{context['version_code']}.pdf"

    record = record or CommuniqueEnvoi(
        communique_key=communique_key, subject=context['subject'],
        recipient=expert.user, email=email,
    )
    record.subject = context['subject']
    record.status = CommuniqueEnvoi.STATUS_PENDING
    record.error = ''
    record.save()

    try:
        message = EmailMultiAlternatives(
            subject=context['subject'],
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        message.attach_alternative(html, 'text/html')
        message.attach(filename, pdf_bytes, 'application/pdf')
        message.send(fail_silently=False)
    except Exception as exc:
        record.status = CommuniqueEnvoi.STATUS_FAILED
        record.error = str(exc)
        record.save(update_fields=['status', 'error', 'updated_at'])
        raise

    record.status = CommuniqueEnvoi.STATUS_SENT
    record.sent_at = timezone.now()
    record.save(update_fields=['status', 'sent_at', 'updated_at'])
    return {'status': 'sent', 'email': email}

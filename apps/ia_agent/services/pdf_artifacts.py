import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from api.v1.pdf_utils import GOLD_CNETP, _base_styles, _header_block, _info_table, _page_footer
from apps.experts.models import Expert
from apps.governance.models import WG


def generate_wg_request_pdf(expert, wg, justification_text):
    """Génère le PDF de demande d'attribution d'un expert à un groupe de travail."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2.5 * cm,
    )
    styles = _base_styles()
    elements = []

    elements += _header_block(
        styles,
        title="DEMANDE D'ATTRIBUTION À UN GROUPE DE TRAVAIL",
        subtitle=f"WG {wg.ctm.number}.{wg.number} — {wg.name}",
    )

    elements.append(Paragraph("Informations sur le demandeur", styles["SectionHeader"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD_CNETP, spaceAfter=6))
    elements.append(_info_table([
        ("Expert", expert.full_name),
        ("Structure", expert.structure.name if expert.structure else "—"),
        ("Spécialités", expert.specialties or "—"),
        ("CTM ciblé", f"CTM {wg.ctm.number} — {wg.ctm.name}"),
        ("Groupe de travail ciblé", f"WG {wg.ctm.number}.{wg.number} — {wg.name}"),
        ("Référence ISO du CTM", wg.ctm.iso_reference or "—"),
        ("Référence ARSO du CTM", wg.ctm.arso_reference or "—"),
    ], styles))
    elements.append(Spacer(1, 0.5 * cm))

    elements.append(Paragraph("Justification de la demande", styles["SectionHeader"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD_CNETP, spaceAfter=6))
    for para in (justification_text or "").split("\n\n"):
        para = para.strip()
        if para:
            elements.append(Paragraph(para.replace("\n", "<br/>"), styles["BodySmall"]))
            elements.append(Spacer(1, 0.2 * cm))

    doc.build(elements, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return buffer.getvalue()


def generate_wg_request_pdf_from_artifact(artifact):
    payload = artifact.payload
    expert = Expert.objects.select_related('user', 'structure').get(id=payload['expert_id'])
    wg = WG.objects.select_related('ctm').get(id=payload['wg_id'])
    return generate_wg_request_pdf(expert, wg, payload.get('justification', ''))

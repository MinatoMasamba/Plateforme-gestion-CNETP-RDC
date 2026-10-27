"""Reçus PDF des paiements de cotisation."""
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..pdf_utils import _base_styles, _header_block, _info_table, _page_footer


def generate_payment_receipt(paiement):
    """Génère le reçu PDF d'un paiement de cotisation et retourne ses octets."""
    cotisation = paiement.cotisation
    structure = cotisation.structure
    styles = _base_styles()
    styles.add(ParagraphStyle(
        name="Amount",
        fontSize=18,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a3a5c"),
        alignment=1,
        spaceBefore=4,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="Notice",
        fontSize=9,
        fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#b45309"),
        leading=13,
        spaceBefore=8,
    ))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
        title=f"Reçu {paiement.numero_recu}",
    )

    elements = _header_block(
        styles,
        "REÇU DE PAIEMENT",
        f"N° {paiement.numero_recu or '—'}",
    )
    elements.append(Paragraph(
        f"{paiement.montant} USD",
        styles["Amount"],
    ))
    elements.append(_info_table([
        ("Structure", structure.name),
        ("Exercice", cotisation.annee),
        ("Statut du paiement", paiement.get_status_display()),
        ("Mode de paiement", paiement.get_methode_paiement_display()),
        ("Date du paiement", paiement.payment_date.strftime("%d/%m/%Y")),
        ("Référence de transaction", paiement.numero_transaction or "—"),
        ("Confirmé le", paiement.confirmed_at.strftime("%d/%m/%Y %H:%M") if paiement.confirmed_at else "—"),
        ("Cotisation annuelle", f"{cotisation.montant} USD"),
        ("Total confirmé", f"{cotisation.montant_paye} USD"),
        ("Reste à payer", f"{cotisation.reste_payer} USD"),
    ], styles))
    elements.append(Spacer(1, 0.5 * cm))

    if paiement.status != 'CONFIRMED':
        elements.append(Paragraph(
            "Ce reçu constate une déclaration de paiement. Il ne vaut quittance "
            "définitive qu’après confirmation par la Cellule Technique de Coordination.",
            styles["Notice"],
        ))
        elements.append(Spacer(1, 0.3 * cm))

    totals = Table(
        [[
            Paragraph("<b>Montant du reçu</b>", styles["BodySmall"]),
            Paragraph(f"<b>{paiement.montant} USD</b>", styles["BodySmall"]),
        ]],
        colWidths=[10 * cm, 7 * cm],
    )
    totals.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f2f4f7")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(totals)

    doc.build(elements, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return buffer.getvalue()


def generate_jeton_receipt(jeton):
    """Génère le reçu PDF d'une indemnité de présence."""
    expert = jeton.expert
    styles = _base_styles()
    styles.add(ParagraphStyle(
        name="Amount",
        fontSize=18,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a3a5c"),
        alignment=1,
        spaceBefore=4,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="Notice",
        fontSize=9,
        fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#b45309"),
        leading=13,
        spaceBefore=8,
    ))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
        title=f"Reçu indemnité {jeton.pk}",
    )

    elements = _header_block(
        styles,
        "REÇU D’INDEMNITÉ",
        f"Jeton n° {jeton.pk}",
    )
    elements.append(Paragraph(f"{jeton.montant} USD", styles["Amount"]))
    elements.append(_info_table([
        ("Expert", expert.user.get_full_name() or expert.user.username),
        ("Structure", expert.structure.name),
        ("Réunion", jeton.reunion.titre),
        ("Date de la réunion", jeton.reunion.date.strftime("%d/%m/%Y")),
        ("Statut", jeton.get_status_display()),
        ("Payé le", jeton.payment_date.strftime("%d/%m/%Y") if jeton.payment_date else "—"),
        ("Contestation", jeton.get_contestation_status_display()),
        ("Motif", jeton.contestation_motif or "—"),
        ("Décision", jeton.contestation_resolution or "—"),
    ], styles))
    elements.append(Spacer(1, 0.4 * cm))

    if jeton.contestation_status == 'PENDING':
        elements.append(Paragraph(
            "Une contestation est en cours d’instruction. Ce reçu ne vaut pas "
            "validation définitive du montant contesté.",
            styles["Notice"],
        ))
    elif jeton.status != 'PAID':
        elements.append(Paragraph(
            "Cette indemnité est en attente de liquidation. Ce document atteste "
            "du droit constaté, pas du virement effectif.",
            styles["Notice"],
        ))

    doc.build(elements, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return buffer.getvalue()

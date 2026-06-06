import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)


# ─── Palette de couleurs CNETP ──────────────────────────────────────────────

BLUE_CNETP = colors.HexColor("#1a3a5c")
GOLD_CNETP = colors.HexColor("#c8a84b")
LIGHT_GREY = colors.HexColor("#f2f4f7")
MID_GREY = colors.HexColor("#6b7280")


def _base_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CNETPTitle",
        fontSize=16, fontName="Helvetica-Bold",
        textColor=BLUE_CNETP, spaceAfter=4, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="CNETPSubtitle",
        fontSize=11, fontName="Helvetica",
        textColor=MID_GREY, spaceAfter=2, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontSize=11, fontName="Helvetica-Bold",
        textColor=BLUE_CNETP, spaceBefore=10, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="BodySmall",
        fontSize=9, fontName="Helvetica",
        textColor=colors.black, leading=13,
    ))
    styles.add(ParagraphStyle(
        name="Footer",
        fontSize=8, fontName="Helvetica",
        textColor=MID_GREY, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="Label",
        fontSize=9, fontName="Helvetica-Bold",
        textColor=BLUE_CNETP,
    ))
    return styles


def _header_block(styles, title, subtitle=""):
    """Bloc d'en-tête commun à tous les PDF CNETP."""
    elements = []
    elements.append(Paragraph("REPUBLIQUE DEMOCRATIQUE DU CONGO", styles["CNETPSubtitle"]))
    elements.append(Paragraph("Ministère des Infrastructures et Travaux Publics", styles["CNETPSubtitle"]))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(HRFlowable(width="100%", thickness=2, color=GOLD_CNETP))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph(
        "COMMISSION NATIONALE D'ELABORATION DES NORMES TECHNIQUES<br/>DE CONSTRUCTION (CNETP)",
        styles["CNETPTitle"],
    ))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=BLUE_CNETP))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph(title, styles["CNETPTitle"]))
    if subtitle:
        elements.append(Paragraph(subtitle, styles["CNETPSubtitle"]))
    elements.append(Spacer(1, 0.4 * cm))
    return elements


def _info_table(rows, styles):
    """Petit tableau deux colonnes pour les informations générales."""
    data = [[Paragraph(k, styles["Label"]), Paragraph(str(v), styles["BodySmall"])] for k, v in rows]
    table = Table(data, colWidths=[4.5 * cm, 12.5 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT_GREY]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d1d5db")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _page_footer(canvas, doc):
    """Pied de page avec numéro de page et date de génération."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MID_GREY)
    footer_text = (
        f"CNETP — Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} "
        f"— Page {doc.page}"
    )
    canvas.drawCentredString(A4[0] / 2, 1.5 * cm, footer_text)
    canvas.setStrokeColor(GOLD_CNETP)
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, 1.8 * cm, A4[0] - 2 * cm, 1.8 * cm)
    canvas.restoreState()


# ─── Génération PDF d'une norme ─────────────────────────────────────────────

def generate_norm_pdf(norme, version=None):
    """
    Génère un PDF pour une norme CNETP.
    version : instance NormeVersion optionnelle ; si None, prend la dernière.
    Retourne bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2.5 * cm,
    )
    styles = _base_styles()
    elements = []

    # En-tête
    elements += _header_block(
        styles,
        title=f"PROJET DE NORME — {norme.reference_number}",
        subtitle=norme.title,
    )

    # Informations générales
    elements.append(Paragraph("Informations générales", styles["SectionHeader"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD_CNETP, spaceAfter=6))

    ctm_name = norme.ctm.name if norme.ctm else "—"
    wg_name = norme.wg.name if norme.wg else "—"
    status_display = dict(norme._meta.get_field("status").choices).get(norme.status, norme.status)
    created_str = norme.created_at.strftime("%d/%m/%Y") if norme.created_at else "—"
    pub_str = norme.publication_date.strftime("%d/%m/%Y") if norme.publication_date else "—"
    iso_ref = norme.iso_reference or "—"
    arso_ref = getattr(norme, "arso_reference", None) or "—"

    info_rows = [
        ("Référence", norme.reference_number),
        ("Titre", norme.title),
        ("Statut", status_display),
        ("Comité Technique Miroir", ctm_name),
        ("Groupe de Travail", wg_name),
        ("Date de création", created_str),
        ("Date de publication", pub_str),
        ("Référence ISO", iso_ref),
        ("Référence ARSO", arso_ref),
    ]
    if norme.jo_reference:
        info_rows.append(("Référence Journal Officiel", norme.jo_reference))

    elements.append(_info_table(info_rows, styles))
    elements.append(Spacer(1, 0.5 * cm))

    # Description
    if norme.description:
        elements.append(Paragraph("Description", styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD_CNETP, spaceAfter=6))
        elements.append(Paragraph(norme.description, styles["BodySmall"]))
        elements.append(Spacer(1, 0.5 * cm))

    # Contenu de la version
    if version is None:
        version = norme.versions.order_by("-version_number").first()

    if version:
        ver_label = f"Version {version.version_number}"
        if version.title:
            ver_label += f" — {version.title}"
        elements.append(Paragraph(ver_label, styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD_CNETP, spaceAfter=6))

        author_name = "—"
        if version.version_author:
            author_name = version.version_author.get_full_name() or version.version_author.username
        created_v = version.created_at.strftime("%d/%m/%Y") if version.created_at else "—"

        elements.append(_info_table([
            ("Auteur", author_name),
            ("Date", created_v),
            ("Résumé", version.summary or "—"),
            ("Brouillon", "Oui" if version.is_draft else "Non"),
        ], styles))
        elements.append(Spacer(1, 0.3 * cm))

        if version.content:
            elements.append(Paragraph("Contenu", styles["SectionHeader"]))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD_CNETP, spaceAfter=6))
            for para in version.content.split("\n\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(para.replace("\n", "<br/>"), styles["BodySmall"]))
                    elements.append(Spacer(1, 0.2 * cm))

        # Tableau des changements
        changes = list(version.changes.all())
        if changes:
            elements.append(Spacer(1, 0.3 * cm))
            elements.append(Paragraph("Historique des modifications", styles["SectionHeader"]))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD_CNETP, spaceAfter=6))

            header = [
                Paragraph("Section", styles["Label"]),
                Paragraph("Type", styles["Label"]),
                Paragraph("Justification", styles["Label"]),
            ]
            rows = [header]
            for ch in changes:
                type_display = {"ADD": "Ajout", "REMOVE": "Suppression", "MODIFY": "Modification"}.get(
                    ch.change_type, ch.change_type
                )
                rows.append([
                    Paragraph(ch.section or "—", styles["BodySmall"]),
                    Paragraph(type_display, styles["BodySmall"]),
                    Paragraph(ch.change_reason or "—", styles["BodySmall"]),
                ])

            tbl = Table(rows, colWidths=[2.5 * cm, 3 * cm, 11.5 * cm])
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BLUE_CNETP),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d1d5db")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(tbl)
    else:
        elements.append(Paragraph("Aucune version disponible.", styles["BodySmall"]))

    doc.build(elements, onLaterPages=_page_footer, onFirstPage=_page_footer)
    return buffer.getvalue()


# ─── Génération PDF d'un Procès-Verbal ──────────────────────────────────────

def generate_pv_pdf(pv):
    """
    Génère un PDF pour un procès-verbal de réunion CNETP.
    pv : instance ProcessusVerbaux.
    Retourne bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2.5 * cm,
    )
    styles = _base_styles()
    elements = []

    reunion = pv.reunion
    type_display = {
        "CTM": "Comité Technique Miroir",
        "WG": "Groupe de Travail",
        "PILOTAGE": "Comité de Pilotage",
        "ASSEMBLEE": "Assemblée Plénière",
        "CTC": "Cellule Technique CTC",
    }.get(reunion.type, reunion.type)
    date_str = reunion.date.strftime("%d/%m/%Y à %H:%M") if reunion.date else "—"

    elements += _header_block(
        styles,
        title="PROCES-VERBAL DE REUNION",
        subtitle=f"{type_display} — {date_str}",
    )

    # Informations réunion
    elements.append(Paragraph("Informations de la réunion", styles["SectionHeader"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD_CNETP, spaceAfter=6))

    ctm_name = reunion.ctm.name if reunion.ctm else "—"
    wg_name = reunion.wg.name if reunion.wg else "—"
    organisateur_name = "—"
    if reunion.organisateur:
        organisateur_name = (
            reunion.organisateur.user.get_full_name()
            or reunion.organisateur.user.username
        )

    elements.append(_info_table([
        ("Type de réunion", type_display),
        ("Titre", reunion.titre),
        ("Date et heure", date_str),
        ("Lieu", reunion.lieu or "—"),
        ("CTM", ctm_name),
        ("Groupe de Travail", wg_name),
        ("Organisateur", organisateur_name),
        ("Lien virtuel", reunion.lien_reunion_virtuelle or "—"),
    ], styles))
    elements.append(Spacer(1, 0.5 * cm))

    # Ordre du jour
    if reunion.ordre_jour:
        elements.append(Paragraph("Ordre du jour", styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD_CNETP, spaceAfter=6))
        for line in reunion.ordre_jour.split("\n"):
            line = line.strip()
            if line:
                elements.append(Paragraph(f"• {line}", styles["BodySmall"]))
        elements.append(Spacer(1, 0.5 * cm))

    # Statistiques quorum
    elements.append(Paragraph("Participation", styles["SectionHeader"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD_CNETP, spaceAfter=6))
    total = (pv.nombre_presents or 0) + (pv.nombre_absents or 0)
    taux = f"{round(pv.nombre_presents * 100 / total)}%" if total else "—"
    elements.append(_info_table([
        ("Présents", str(pv.nombre_presents or 0)),
        ("Absents", str(pv.nombre_absents or 0)),
        ("Taux de présence", taux),
        ("Quorum atteint", "Oui" if pv.quorum_atteint else "Non"),
    ], styles))
    elements.append(Spacer(1, 0.5 * cm))

    # Liste des présences
    presences = list(reunion.presences.select_related("expert__user", "expert__structure").all())
    if presences:
        elements.append(Paragraph("Liste d'émargement", styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD_CNETP, spaceAfter=6))

        status_labels = {"PRESENT": "Présent", "ABSENT": "Absent", "EXCUSED": "Excusé"}
        status_colors = {
            "PRESENT": colors.HexColor("#d1fae5"),
            "ABSENT": colors.HexColor("#fee2e2"),
            "EXCUSED": colors.HexColor("#fef3c7"),
        }

        header = [
            Paragraph("Nom & Prénom", styles["Label"]),
            Paragraph("Structure", styles["Label"]),
            Paragraph("Statut", styles["Label"]),
        ]
        rows = [header]
        row_colors = [BLUE_CNETP]
        for p in presences:
            full_name = p.expert.user.get_full_name() or p.expert.user.username
            structure = p.expert.structure.name if p.expert.structure else "—"
            rows.append([
                Paragraph(full_name, styles["BodySmall"]),
                Paragraph(structure, styles["BodySmall"]),
                Paragraph(status_labels.get(p.status, p.status), styles["BodySmall"]),
            ])
            row_colors.append(status_colors.get(p.status, colors.white))

        tbl = Table(rows, colWidths=[6 * cm, 7 * cm, 4 * cm])
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), BLUE_CNETP),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d1d5db")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
        for i, color in enumerate(row_colors[1:], start=1):
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), color))
        tbl.setStyle(TableStyle(style_cmds))
        elements.append(tbl)
        elements.append(Spacer(1, 0.5 * cm))

    # Votes de la réunion
    votes = list(reunion.votes.select_related("expert__user").all())
    if votes:
        elements.append(Paragraph("Résultats des votes", styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD_CNETP, spaceAfter=6))

        vote_labels = {"POUR": "Pour", "CONTRE": "Contre", "ABSTENTION": "Abstention"}
        header = [
            Paragraph("Nom & Prénom", styles["Label"]),
            Paragraph("Vote", styles["Label"]),
            Paragraph("Justification", styles["Label"]),
        ]
        rows = [header]
        for v in votes:
            full_name = v.expert.user.get_full_name() or v.expert.user.username
            rows.append([
                Paragraph(full_name, styles["BodySmall"]),
                Paragraph(vote_labels.get(v.choix, v.choix), styles["BodySmall"]),
                Paragraph(v.justification or "—", styles["BodySmall"]),
            ])

        tbl = Table(rows, colWidths=[6 * cm, 3 * cm, 8 * cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLUE_CNETP),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d1d5db")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(tbl)
        elements.append(Spacer(1, 0.5 * cm))

    # Contenu du PV
    if pv.contenu:
        elements.append(Paragraph("Contenu du procès-verbal", styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD_CNETP, spaceAfter=6))
        for para in pv.contenu.split("\n\n"):
            para = para.strip()
            if para:
                elements.append(Paragraph(para.replace("\n", "<br/>"), styles["BodySmall"]))
                elements.append(Spacer(1, 0.2 * cm))

    elements.append(Spacer(1, 0.5 * cm))

    # Bloc signature
    elements.append(HRFlowable(width="100%", thickness=1, color=GOLD_CNETP, spaceAfter=10))
    elements.append(Paragraph("Signature", styles["SectionHeader"]))

    sig_name = "—"
    sig_date = "—"
    if pv.signed_by:
        sig_name = pv.signed_by.user.get_full_name() or pv.signed_by.user.username
    if pv.signature_date:
        sig_date = pv.signature_date.strftime("%d/%m/%Y")

    sig_table = Table(
        [[
            Paragraph(f"Signé par : {sig_name}", styles["BodySmall"]),
            Paragraph(f"Date de signature : {sig_date}", styles["BodySmall"]),
        ]],
        colWidths=[9 * cm, 8 * cm],
    )
    sig_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(sig_table)

    doc.build(elements, onLaterPages=_page_footer, onFirstPage=_page_footer)
    return buffer.getvalue()

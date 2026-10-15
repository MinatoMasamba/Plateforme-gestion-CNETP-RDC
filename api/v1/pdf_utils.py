import io
import os
from datetime import datetime
from xml.sax.saxutils import escape as _xml_escape

from django.conf import settings

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)


# ─── Palette officielle — Charte graphique du Gouvernement RDC ──────────────
RDC_BLUE = colors.HexColor("#0095c9")    # Pantone 801C
RDC_YELLOW = colors.HexColor("#fff24b")  # Pantone 803C
RDC_RED = colors.HexColor("#db3832")     # Pantone 485C

BLUE_CNETP = colors.HexColor("#1a3a5c")
GOLD_CNETP = colors.HexColor("#c8a84b")
LIGHT_GREY = colors.HexColor("#f2f4f7")
MID_GREY = colors.HexColor("#6b7280")
DARK = colors.HexColor("#0f172a")
BORDER = colors.HexColor("#d1d5db")

LOGO_PATH = settings.BASE_DIR / "templates" / "static" / "img" / "logo-cnetp.png"
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = settings.BASE_DIR / "web" / "static" / "dist" / "img" / "logo-cnetp.png"


def _esc(value):
    """Échappe le texte pour le mini-langage de balisage ReportLab."""
    return _xml_escape(str(value if value is not None else ""))


def _qr_png_bytes(data):
    """Génère un QR code PNG (bytes) ou None si la librairie est absente."""
    try:
        import qrcode

        img = qrcode.make(data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None



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


# ─── Éléments de marque (Charte graphique du Gouvernement RDC) ──────────────

def _norm_styles():
    styles = _base_styles()
    styles.add(ParagraphStyle(name="BrandTitle", fontSize=9.5, fontName="Helvetica-Bold",
                              textColor=DARK, leading=11))
    styles.add(ParagraphStyle(name="BrandSub", fontSize=8, fontName="Helvetica",
                              textColor=MID_GREY, leading=10))
    styles.add(ParagraphStyle(name="DocH1", fontSize=15, fontName="Helvetica-Bold",
                              textColor=DARK, alignment=TA_CENTER, spaceBefore=4, spaceAfter=2))
    styles.add(ParagraphStyle(name="DocH2", fontSize=12, fontName="Helvetica-Bold",
                              textColor=DARK, spaceBefore=10, spaceAfter=3))
    styles.add(ParagraphStyle(name="DocBody", fontSize=10, fontName="Helvetica",
                              textColor=DARK, leading=15))
    styles.add(ParagraphStyle(name="MetaLabel", fontSize=6.5, fontName="Helvetica-Bold",
                              textColor=MID_GREY, alignment=TA_CENTER, leading=8))
    styles.add(ParagraphStyle(name="MetaValue", fontSize=9.5, fontName="Helvetica-Bold",
                              textColor=DARK, alignment=TA_CENTER, leading=12))
    styles.add(ParagraphStyle(name="CenterSmall", fontSize=8, fontName="Helvetica",
                              textColor=MID_GREY, alignment=TA_CENTER))
    return styles


def _tricolor_vertical(width=0.32 * cm, height=1.6 * cm):
    """Ligne d'État verticale : Bleu / Jaune / Rouge à parts égales."""
    seg = height / 3.0
    table = Table([[""], [""], [""]], colWidths=[width], rowHeights=[seg, seg, seg])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), RDC_BLUE),
        ("BACKGROUND", (0, 1), (0, 1), RDC_YELLOW),
        ("BACKGROUND", (0, 2), (0, 2), RDC_RED),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def _tricolor_horizontal(width, height=0.14 * cm):
    """Ligne d'État horizontale : Bleu / Jaune / Rouge à parts égales."""
    table = Table([["", "", ""]], colWidths=[width / 3.0] * 3, rowHeights=[height])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), RDC_BLUE),
        ("BACKGROUND", (1, 0), (1, 0), RDC_YELLOW),
        ("BACKGROUND", (2, 0), (2, 0), RDC_RED),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def _brand_block(styles):
    """Bloc-armoirie + Ligne d'État (parts égales) + intitulé officiel."""
    text = [
        Paragraph("RÉPUBLIQUE DÉMOCRATIQUE DU CONGO", styles["BrandTitle"]),
        Paragraph("Cellule Technique de Coordination - CNE-ITP", styles["BrandSub"]),
        Paragraph("<i>Lecteur normatif – Secrétariat technique</i>", styles["BrandSub"]),
    ]
    if os.path.exists(LOGO_PATH):
        logo = Image(str(LOGO_PATH), width=1.55 * cm, height=1.55 * cm)
    else:
        logo = Paragraph("", styles["BrandSub"])
    table = Table([[logo, _tricolor_vertical(), text]],
                  colWidths=[1.75 * cm, 0.5 * cm, 14.0 * cm])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def _meta_cartouche(norme, version, styles):
    ctm_no = norme.ctm.number if norme.ctm else "—"
    wg_no = f"{ctm_no}.{norme.wg.number}" if norme.wg else "—"
    status_display = dict(norme._meta.get_field("status").choices).get(norme.status, norme.status)
    ver = f"v{version.version_number}" if version else "—"
    labels = ["Référence", "CTM / WG", "Statut", "Version"]
    values = [norme.reference_number, f"{ctm_no} / {wg_no}", status_display, ver]
    head = [Paragraph(_esc(label).upper(), styles["MetaLabel"]) for label in labels]
    body = [Paragraph(_esc(value), styles["MetaValue"]) for value in values]
    table = Table([head, body], colWidths=[4.25 * cm] * 4)
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GREY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _make_norm_footer(norme, qr_bytes):
    """Pied de page réglementaire (référence, mentions, copyright, QR) collé en bas."""
    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(2 * cm, 2.3 * cm, A4[0] - 2 * cm, 2.3 * cm)

        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(DARK)
        canvas.drawString(2 * cm, 1.65 * cm, norme.reference_number)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MID_GREY)
        canvas.drawString(2 * cm, 1.25 * cm,
                          "Document généré via la plateforme CNE-ITP — Usage interne")
        canvas.drawCentredString(
            A4[0] / 2, 0.85 * cm,
            "© 2026 Gouvernement de la République Démocratique du Congo. Tous droits réservés.")
        canvas.drawRightString(A4[0] - 2 * cm, 1.65 * cm, f"Page {doc.page}")

        if qr_bytes:
            try:
                canvas.drawImage(ImageReader(io.BytesIO(qr_bytes)),
                                 A4[0] - 4.0 * cm, 0.72 * cm, 1.4 * cm, 1.4 * cm, mask="auto")
            except Exception:
                pass
        canvas.restoreState()
    return _footer


# ─── Génération PDF d'une norme (fidèle à la page de lecture CTC) ────────────

def generate_norm_pdf(norme, version=None):
    """
    Génère un PDF A4 pour une norme, calqué sur la page de lecture CTC
    (bandeau d'État RDC, cartouche de métadonnées, sections, pied + QR).
    version : instance NormeVersion optionnelle ; sinon la dernière version.
    Retourne bytes.
    """
    if version is None:
        version = norme.get_latest_version()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.8 * cm, bottomMargin=3.2 * cm,
        title=f"{norme.reference_number} — {norme.title}",
    )
    styles = _norm_styles()
    elements = []

    # Bandeau institutionnel (armoiries + Ligne d'État + intitulé)
    elements.append(_brand_block(styles))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(_tricolor_horizontal(17 * cm))
    elements.append(Spacer(1, 0.55 * cm))

    # En-tête documentaire centré
    elements.append(Paragraph("RÉPUBLIQUE DÉMOCRATIQUE DU CONGO", styles["CenterSmall"]))
    elements.append(Paragraph("<b>Cellule Technique de Coordination — CNE-ITP</b>", styles["DocH1"]))
    elements.append(Paragraph(_esc(norme.title.upper()), styles["DocH1"]))
    elements.append(Spacer(1, 0.35 * cm))

    # Cartouche de métadonnées
    elements.append(_meta_cartouche(norme, version, styles))
    elements.append(Spacer(1, 0.6 * cm))

    # Préambule
    if norme.description:
        elements.append(Paragraph("Préambule", styles["DocH2"]))
        elements.append(_tricolor_horizontal(3 * cm))
        elements.append(Spacer(1, 0.15 * cm))
        for para in norme.description.split("\n"):
            if para.strip():
                elements.append(Paragraph(_esc(para.strip()), styles["DocBody"]))
        elements.append(Spacer(1, 0.25 * cm))

    # Corps : sections issues du contenu structuré de la version
    if version and version.content:
        for block in version.get_structured_content():
            title = (block.get("title") or "").strip()
            content = (block.get("content") or "").strip()
            if title:
                elements.append(Paragraph(_esc(title), styles["DocH2"]))
                elements.append(_tricolor_horizontal(3 * cm))
                elements.append(Spacer(1, 0.1 * cm))
            for line in content.split("\n"):
                if line.strip():
                    elements.append(Paragraph(_esc(line.strip()), styles["DocBody"]))
            elements.append(Spacer(1, 0.2 * cm))
    else:
        elements.append(Paragraph("Aucune version disponible.", styles["DocBody"]))

    qr_bytes = _qr_png_bytes(
        f"{(settings.SITE_URL or '').rstrip('/')}/ctc/norme/{norme.id}/lecture/ | {norme.reference_number}"
    )
    footer = _make_norm_footer(norme, qr_bytes)
    doc.build(elements, onFirstPage=footer, onLaterPages=footer)
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

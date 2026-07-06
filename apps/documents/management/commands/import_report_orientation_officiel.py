from __future__ import annotations

import re
import subprocess
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from apps.documents.models import DocumentFile
from apps.governance.models import CTM, WG
from apps.norms.models import Norme


DEFAULT_PDF = Path("Rapport_Orientation_Officiel_CNE_ITP - Copie_Phoenix.pdf")


def _normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _title_from_filename(pdf_path: Path) -> str:
    stem = pdf_path.stem
    stem = stem.replace("_", " ")
    stem = stem.replace("Copie Phoenix", "")
    stem = stem.replace("Copie", "")
    stem = _normalize_spaces(stem)
    return stem or "Rapport officiel"


def _try_pdftotext(pdf_path: Path) -> str:
    try:
        result = subprocess.run(
            ["pdftotext", str(pdf_path), "-"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return ""
    return _normalize_spaces(result.stdout or "")


def _pick_user():
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).order_by("id").first()
    if user:
        return user
    user = User.objects.filter(is_staff=True).order_by("id").first()
    if user:
        return user
    raise CommandError("Aucun utilisateur admin/staff trouvé pour uploader le document.")


class Command(BaseCommand):
    help = (
        "Importe le rapport officiel PDF comme document de plateforme et crée/actualise "
        "une norme brouillon rattachée à un CTM/WG."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "pdf_path",
            nargs="?",
            default=str(DEFAULT_PDF),
            help="Chemin du PDF à importer.",
        )
        parser.add_argument(
            "--reference-number",
            default="CNE-ITP-ORIENTATION-2026",
            help="Référence unique de la norme à créer ou mettre à jour.",
        )
        parser.add_argument(
            "--ctm",
            type=int,
            default=1,
            help="Numéro du CTM de rattachement.",
        )
        parser.add_argument(
            "--wg",
            type=int,
            default=1,
            help="Numéro du WG de rattachement.",
        )
        parser.add_argument(
            "--public",
            action="store_true",
            help="Rendre le document et la norme publics.",
        )

    def handle(self, *args, **options):
        pdf_path = Path(options["pdf_path"]).expanduser().resolve()
        if not pdf_path.exists():
            raise CommandError(f"PDF introuvable: {pdf_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise CommandError("Le fichier fourni n'est pas un PDF.")

        try:
            ctm = CTM.objects.get(number=options["ctm"])
            wg = WG.objects.get(ctm=ctm, number=options["wg"])
        except (CTM.DoesNotExist, WG.DoesNotExist) as exc:
            raise CommandError(
                f"CTM/WG introuvable pour CTM {options['ctm']} / WG {options['ctm']}.{options['wg']}"
            ) from exc

        uploaded_by = _pick_user()
        raw_text = _try_pdftotext(pdf_path)
        base_title = _title_from_filename(pdf_path)

        if raw_text:
            first_line = raw_text.split(".")[0][:180]
            if first_line and len(first_line) > 10:
                base_title = _normalize_spaces(first_line)

        title = base_title
        description = (
            f"Rapport officiel importé depuis {pdf_path.name}. "
            f"{'Texte extrait automatiquement.' if raw_text else 'PDF scanné ou texte non extractible automatiquement.'}"
        )

        norme, norme_created = Norme.objects.update_or_create(
            reference_number=options["reference_number"],
            defaults={
                "title": title,
                "description": description,
                "ctm": ctm,
                "wg": wg,
                "standard_family": "OTHER",
                "category": "Rapport officiel",
                "norm_type": "REC",
                "target_count": 1,
                "status": "DRAFT",
                "is_public": bool(options["public"]),
                "tags": "rapport,orientation,officiel,pdf",
            },
        )

        document_title = f"{title} - PDF officiel"
        document, document_created = DocumentFile.objects.update_or_create(
            norme=norme,
            title=document_title,
            defaults={
                "uploaded_by": uploaded_by,
                "expert": None,
                "description": description,
                "file_type": "PDF",
                "category": "Rapport",
                "is_public": bool(options["public"]),
                "mime_type": "application/pdf",
                "file_size": pdf_path.stat().st_size,
            },
        )

        with pdf_path.open("rb") as fh:
            if document.file and document.file.name:
                document.file.delete(save=False)
            document.file.save(pdf_path.name, File(fh), save=True)

        self.stdout.write(self.style.SUCCESS("Import terminé."))
        self.stdout.write(f"Norme: {norme.reference_number} — {norme.title}")
        self.stdout.write(f"CTM/WG: CTM {ctm.number} / WG {wg.ctm.number}.{wg.number}")
        self.stdout.write(f"Norme {'créée' if norme_created else 'mise à jour'}.")
        self.stdout.write(f"Document {'créé' if document_created else 'mis à jour'}.")
        self.stdout.write(
            "Note: le PDF semble image-only si pdftotext ne renvoie rien; "
            "le titre est alors déduit du nom du fichier."
        )

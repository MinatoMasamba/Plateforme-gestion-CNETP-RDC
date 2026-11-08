"""Validation réelle commune des pièces GED et des réceptions."""
import hashlib
import io
from pathlib import Path
from django.core.exceptions import ValidationError

MAX_SIZE = 10 * 1024 * 1024


def inspect_document(upload):
    if not upload or getattr(upload, 'size', MAX_SIZE + 1) > MAX_SIZE:
        raise ValidationError('Fichier PDF, PNG ou JPG de 10 Mo maximum requis.')
    content = upload.read(MAX_SIZE + 1)
    upload.seek(0)
    if not content or len(content) > MAX_SIZE:
        raise ValidationError('Fichier vide ou supérieur à 10 Mo.')
    suffix = Path(upload.name).suffix.lower()
    valid = (suffix == '.pdf' and content.startswith(b'%PDF-')) or (suffix == '.png' and content.startswith(b'\x89PNG\r\n\x1a\n')) or (suffix in ('.jpg', '.jpeg') and content.startswith(b'\xff\xd8\xff'))
    if not valid:
        raise ValidationError('Le contenu doit correspondre au format PDF, PNG ou JPG annoncé.')
    text = ''
    try:
        if suffix == '.pdf':
            import fitz
            with fitz.open(stream=content, filetype='pdf') as reader:
                if reader.needs_pass or not reader.page_count:
                    raise ValueError('PDF chiffré ou vide')
                # Texte natif d’abord ; OCR uniquement si le PDF est un scan et que Tesseract est présent.
                parts = []
                length = 0
                for page in reader:
                    part = page.get_text()
                    length += len(part)
                    if length > 2_000_000:
                        raise ValueError('Texte extrait trop volumineux')
                    parts.append(part)
                text = '\n'.join(parts).strip()
                if not text:
                    text = _ocr_pdf(reader)
        else:
            from PIL import Image
            with Image.open(io.BytesIO(content)) as image:
                image.verify()
            text = _ocr_image(content)
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError('Fichier illisible, chiffré ou endommagé.') from exc
    return {'size': len(content), 'sha256': hashlib.sha256(content).hexdigest(), 'text': text}


def _tesseract_available():
    from shutil import which
    return bool(which('tesseract'))


def _ocr_pdf(reader):
    """OCR réel via PyMuPDF+Tesseract ; chaîne vide si indisponible (jamais de texte inventé)."""
    if not _tesseract_available():
        return ''
    try:
        parts, length = [], 0
        for page in reader:
            try:
                tp = page.get_textpage_ocr(flags=0, language='fra', dpi=200)
                part = page.get_text(textpage=tp) or ''
            except Exception:
                part = ''
            length += len(part)
            if length > 2_000_000:
                break
            parts.append(part)
        return '\n'.join(parts).strip()
    except Exception:
        return ''


def _ocr_image(content):
    if not _tesseract_available():
        return ''
    try:
        import pytesseract
        from PIL import Image
        with Image.open(io.BytesIO(content)) as image:
            return (pytesseract.image_to_string(image, lang='fra') or '').strip()[:2_000_000]
    except Exception:
        return ''

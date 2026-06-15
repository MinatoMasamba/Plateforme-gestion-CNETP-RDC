import functools
import re

from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from apps.norms.models import Norme

from ..models import AgentArtifact
from . import register

CATALOGUE_PATH = settings.BASE_DIR / "catalogue_full.txt"
CACHE_DIR = settings.BASE_DIR / ".cache" / "ia_agent"

REFERENTIAL_PDFS = [
    "Catalogue-of-African-Regional-Standards-ARSAdoptions-by-Sector-and-TC-Dec-2025-1.pdf",
    "Normes ISO Miroiterie (CTM) Bâtiment.pdf",
]


@functools.lru_cache(maxsize=1)
def _load_catalogue_chunks():
    if not CATALOGUE_PATH.exists():
        return []

    with open(CATALOGUE_PATH, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    chunk_size = 12
    chunks = []
    for i in range(0, len(lines), chunk_size):
        block = "".join(lines[i:i + chunk_size]).strip()
        if block:
            chunks.append({"location": f"catalogue_full.txt#L{i + 1}", "text": block})
    return chunks


def _extract_pdf_text(pdf_path):
    import fitz

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / (pdf_path.stem + ".txt")
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8", errors="replace")

    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    cache_file.write_text(text, encoding="utf-8")
    return text


@functools.lru_cache(maxsize=1)
def _load_pdf_chunks():
    chunks = []
    for name in REFERENTIAL_PDFS:
        path = settings.BASE_DIR / name
        if not path.exists():
            continue
        text = _extract_pdf_text(path)
        for idx, para in enumerate(text.split("\n\n")):
            para = para.strip()
            if len(para) > 40:
                chunks.append({"location": f"{name}#para{idx}", "text": para})
    return chunks


def _score(text_lower, terms):
    return sum(text_lower.count(t) for t in terms)


SEARCH_EXTERNAL_REFERENTIALS_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Termes de recherche (mots-clés techniques)"},
        "max_results": {"type": "integer", "description": "Nombre de résultats max (défaut 5)"},
    },
    "required": ["query"],
}


@register(
    "search_external_referentials",
    "Recherche dans les référentiels locaux (catalogue ARSO texte, catalogue PDF des "
    "normes régionales africaines ARSO, catalogue PDF des normes ISO Miroiterie/Bâtiment) "
    "des extraits pertinents pour une requête de mots-clés techniques.",
    SEARCH_EXTERNAL_REFERENTIALS_SCHEMA,
    scopes=["ctc", "pilotage"],
)
def search_external_referentials(session, query, max_results=5):
    terms = re.findall(r"[a-zàâäéèêëïîôöùûüçœ0-9]{3,}", (query or "").lower())
    if not terms:
        return []

    results = []
    for chunk in _load_catalogue_chunks():
        score = _score(chunk["text"].lower(), terms)
        if score > 0:
            results.append({
                "source": "catalogue_full.txt",
                "location": chunk["location"],
                "excerpt": chunk["text"][:500],
                "score": score,
            })

    for chunk in _load_pdf_chunks():
        score = _score(chunk["text"].lower(), terms)
        if score > 0:
            results.append({
                "source": "pdf",
                "location": chunk["location"],
                "excerpt": chunk["text"][:500],
                "score": score,
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results]


PROPOSE_EXTERNAL_REFERENCE_SCHEMA = {
    "type": "object",
    "properties": {
        "ctm_id": {"type": "integer"},
        "norme_id": {
            "type": "integer",
            "description": "ID de la norme existante visée (requis si proposal_type=COMMENT_ON_EXISTING)",
        },
        "title": {"type": "string"},
        "description": {"type": "string"},
        "referential_excerpt": {
            "type": "string",
            "description": "Extrait du référentiel ISO/ARSO justifiant la proposition",
        },
        "proposal_type": {"type": "string", "enum": ["NEW_NORM", "COMMENT_ON_EXISTING"]},
    },
    "required": ["ctm_id", "title", "description", "referential_excerpt", "proposal_type"],
}


@register(
    "propose_external_reference",
    "Crée une proposition (brouillon) — nouvelle norme ou commentaire sur une norme "
    "existante — basée sur un extrait de référentiel ISO/ARSO local, pour révision "
    "humaine par la CTC.",
    PROPOSE_EXTERNAL_REFERENCE_SCHEMA,
    scopes=["ctc", "pilotage"],
)
def propose_external_reference(session, ctm_id, title, description, referential_excerpt, proposal_type, norme_id=None):
    payload = {
        "ctm_id": ctm_id,
        "title": title,
        "description": description,
        "referential_excerpt": referential_excerpt,
        "proposal_type": proposal_type,
    }

    content_type = None
    object_id = None
    if proposal_type == 'COMMENT_ON_EXISTING' and norme_id:
        norme = Norme.objects.get(id=norme_id)
        content_type = ContentType.objects.get_for_model(Norme)
        object_id = norme.id
        payload["norme_id"] = norme.id
        payload["norme_reference"] = norme.reference_number

    artifact = AgentArtifact.objects.create(
        session=session,
        artifact_type='EXTERNAL_PROPOSAL',
        title=title,
        payload=payload,
        status='DRAFT',
        content_type=content_type,
        object_id=object_id,
    )

    return {"artifact_id": artifact.id, "status": artifact.status, "title": artifact.title}

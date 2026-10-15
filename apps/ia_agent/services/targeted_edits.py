"""Corrections ciblées « ligne / colonne » pour l'assistant IA.

Objectif : ne jamais réécrire tout le document. On produit une liste d'éditions
minimales ``{find, replace, reason}`` (façon agent CLI : patch chirurgical) puis
on les applique au texte d'origine.

Deux stratégies :
  * le LLM renvoie directement un JSON ``{"summary", "edits": [...]}`` ;
  * à défaut (réponse en texte libre), on dérive un diff ligne à ligne via
    ``difflib`` afin que seules les lignes réellement modifiées soient ciblées.
"""
import difflib
import json
import re

MAX_EDITS = 80


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def parse_targeted_json(raw: str):
    """Extrait ``(summary, edits)`` d'une réponse LLM au format JSON.

    Renvoie ``(None, None)`` si aucune structure exploitable n'est trouvée.
    """
    if not raw:
        return None, None

    text = raw.strip()
    # Retirer d'éventuelles clôtures de code ```json ... ```
    text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()

    candidate = text
    if not candidate.startswith("{"):
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None, None
        candidate = candidate[start:end + 1]

    try:
        data = json.loads(candidate)
    except (json.JSONDecodeError, ValueError):
        return None, None

    if not isinstance(data, dict):
        return None, None

    summary = data.get("summary") or data.get("explanation") or ""
    raw_edits = data.get("edits")
    if raw_edits is None:
        return None, None
    if not isinstance(raw_edits, list):
        return None, None

    edits = []
    for item in raw_edits:
        if not isinstance(item, dict):
            continue
        find = item.get("find") or item.get("old") or ""
        replace = item.get("replace") or item.get("new") or ""
        reason = item.get("reason") or "Correction"
        if not find and not replace:
            continue
        edits.append({"find": find, "replace": replace, "reason": reason})
    return summary, edits[:MAX_EDITS]


def build_edits_from_proposal(original: str, proposal: str):
    """Diff ligne à ligne : ne cible que les lignes/cellules modifiées."""
    if not proposal or proposal.strip() == (original or "").strip():
        return []

    a = (original or "").splitlines()
    b = proposal.splitlines()
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    labels = {
        "replace": "Ligne reformulée",
        "delete": "Ligne supprimée",
        "insert": "Ligne ajoutée",
    }

    edits = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        edits.append({
            "find": "\n".join(a[i1:i2]),
            "replace": "\n".join(b[j1:j2]),
            "reason": labels.get(tag, "Modification"),
        })
        if len(edits) >= MAX_EDITS:
            break
    return edits


def _apply_single(text: str, find: str, replace: str):
    """Applique une édition, avec repli tolérant (ligne, espaces)."""
    if find and find in text:
        return text.replace(find, replace, 1), True

    find_norm = _normalize_whitespace(find)
    if not find_norm:
        return text, False

    lines = text.split("\n")
    # Correspondance exacte de ligne (espaces normalisés)
    for index, line in enumerate(lines):
        if _normalize_whitespace(line) == find_norm:
            lines[index] = replace
            return "\n".join(lines), True
    # Correspondance partielle sur une ligne
    for index, line in enumerate(lines):
        if find_norm in _normalize_whitespace(line):
            lines[index] = replace
            return "\n".join(lines), True
    return text, False


def apply_edits(text: str, edits):
    """Applique les éditions et renvoie ``(texte_final, editions_annotées)``.

    Chaque édition reçoit un booléen ``applied`` indiquant si la cible a été
    trouvée dans le texte (pour l'affichage front « Appliqué / Non appliqué »).
    """
    applied_text = text or ""
    annotated = []
    for edit in edits or []:
        find = edit.get("find") or ""
        replace = edit.get("replace") if edit.get("replace") is not None else ""
        reason = edit.get("reason") or "Correction"
        if not find:
            annotated.append({"find": find, "replace": replace, "reason": reason, "applied": False})
            continue
        new_text, ok = _apply_single(applied_text, find, replace)
        annotated.append({"find": find, "replace": replace, "reason": reason, "applied": ok})
        if ok:
            applied_text = new_text
    return applied_text, annotated

import re
from difflib import SequenceMatcher


TOKEN_PATTERN = re.compile(r"\w+(?:['’.-]\w+)*|[^\w\s]|\s+")


def build_inline_diff_segments(old_text, new_text):
    """Retourne un diff inline par token, en conservant les espaces et la ponctuation.

    Chaque segment contient un type : equal, delete, insert.
    Le rendu côté template peut ensuite afficher les suppressions en rouge et
    les ajouts en bleu, tout en gardant le texte inchangé en gris.
    """
    if old_text is None:
        old_text = ""
    if new_text is None:
        new_text = ""

    old_tokens = TOKEN_PATTERN.findall(old_text)
    new_tokens = TOKEN_PATTERN.findall(new_text)

    matcher = SequenceMatcher(None, old_tokens, new_tokens, autojunk=False)
    segments = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old_chunk = old_tokens[i1:i2]
        new_chunk = new_tokens[j1:j2]

        if tag == 'equal':
            for token in old_chunk:
                if token:
                    segments.append({'type': 'equal', 'text': token})
        elif tag == 'delete':
            for token in old_chunk:
                if token:
                    segments.append({'type': 'delete', 'text': token})
        elif tag == 'insert':
            for token in new_chunk:
                if token:
                    segments.append({'type': 'insert', 'text': token})
        elif tag == 'replace':
            max_len = max(len(old_chunk), len(new_chunk))
            for idx in range(max_len):
                old_token = old_chunk[idx] if idx < len(old_chunk) else None
                new_token = new_chunk[idx] if idx < len(new_chunk) else None
                if old_token and new_token and old_token != new_token:
                    if old_token:
                        segments.append({'type': 'delete', 'text': old_token})
                    if new_token:
                        segments.append({'type': 'insert', 'text': new_token})
                elif old_token:
                    segments.append({'type': 'delete', 'text': old_token})
                elif new_token:
                    segments.append({'type': 'insert', 'text': new_token})

    return segments

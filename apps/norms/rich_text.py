import html
import re
from dataclasses import dataclass
from urllib.parse import urlsplit


FORMAT_PLAIN = 'plain'
FORMAT_MARKDOWN = 'md'
CONTENT_FORMAT_CHOICES = (
    (FORMAT_PLAIN, 'Texte brut'),
    (FORMAT_MARKDOWN, 'Markdown CNE-ITP'),
)

_COLORS = {
    'bleu': '#0095C9',
    'rouge': '#DB3832',
    'nuit': '#0A2540',
}
_SIZES = {
    'petit': 9,
    'grand': 14,
    'tres-grand': 18,
}
_STYLE_KEYS = {'taille', 'couleur', 'surlignage'}
# « \< » est un chevron littéral échappé par les éditeurs riches.
_RAW_HTML = re.compile(r'(?<!\\)<\s*/?\s*[a-zA-Z!]')
_STYLED = re.compile(r'\[((?:\\.|[^\[\]\\\n])+)\]\{([^{}\n]+)\}')


class RichTextValidationError(ValueError):
    pass


@dataclass(frozen=True)
class RichBlock:
    kind: str
    html: str
    plain: str
    level: int | None = None

    def pdf_html(self):
        return self.html


def _error(message, text=None, position=None):
    if text is not None and position is not None:
        line = text.count('\n', 0, position) + 1
        column = position - text.rfind('\n', 0, position)
        return RichTextValidationError(f'{message} (ligne {line}, colonne {column})')
    return RichTextValidationError(message)


def _safe_url(value):
    decoded = html.unescape(value.strip())
    if any(character.isspace() or ord(character) < 32 for character in decoded):
        raise _error('Lien contenant des espaces ou caractères interdits')
    try:
        parsed = urlsplit(decoded)
    except ValueError as exc:
        raise _error('Lien mal formé') from exc
    if parsed.scheme.lower() not in {'http', 'https', 'mailto'}:
        raise _error("Lien interdit : seuls http, https et mailto sont acceptés")
    if parsed.scheme.lower() in {'http', 'https'} and not parsed.netloc:
        raise _error('Lien absolu incomplet')
    if parsed.scheme.lower() == 'mailto' and not parsed.path:
        raise _error('Adresse mailto vide')
    return decoded


def _style_to_html(attributes):
    colors = {}
    for item in attributes.split('|'):
        if '=' not in item:
            raise _error('Attribut de style invalide')
        key, value = (part.strip() for part in item.split('=', 1))
        if key not in _STYLE_KEYS:
            raise _error(f'Attribut non autorisé : {key}')
        if key == 'taille':
            if value not in _SIZES:
                raise _error(f'Taille de texte inconnue : {value}')
            colors['size'] = str(_SIZES[value])
        elif key == 'couleur':
            if value not in _COLORS:
                raise _error(f'Couleur de texte inconnue : {value}')
            colors['color'] = _COLORS[value]
        elif key == 'surlignage':
            if value != 'jaune':
                raise _error(f'Surlignage inconnu : {value}')
            colors['backColor'] = '#FFF24B'
    if colors:
        attrs = ' '.join(f'{key}="{value}"' for key, value in colors.items())
        return f'<font {attrs}>', '</font>'
    return '', ''


def _find_closing(text, marker, position):
    escaped = False
    for index in range(position, len(text)):
        char = text[index]
        if escaped:
            escaped = False
        elif char == '\\':
            escaped = True
        elif text.startswith(marker, index):
            return index
    return -1


def _find_link_end(text, position):
    depth = 0
    for index in range(position, len(text)):
        char = text[index]
        if char == '\n':
            break
        if char == '(':
            depth += 1
        elif char == ')':
            if depth == 0:
                return index
            depth -= 1
    return -1


def _inline(text, start=0, closing=None, depth=0):
    if depth > 30:
        raise _error('Mise en forme trop profondément imbriquée', text, start)
    rendered = []
    plain = []
    index = start

    def wrap(marker, open_tag, close_tag, marker_position):
        end = _find_closing(text, marker, marker_position + len(marker))
        if end < 0:
            raise _error(f'Marqueur « {marker} » non fermé', text, marker_position)
        inner_html, inner_plain, consumed = _inline(
            text, marker_position + len(marker), marker, depth + 1
        )
        return f'{open_tag}{inner_html}{close_tag}', inner_plain, consumed

    while index < len(text):
        if closing and text.startswith(closing, index):
            return ''.join(rendered), ''.join(plain), index + len(closing)

        char = text[index]
        if char == '\\':
            if index + 1 >= len(text):
                raise _error("Caractère d'échappement sans valeur", text, index)
            rendered.append(html.escape(text[index + 1]))
            plain.append(text[index + 1])
            index += 2
            continue

        if char == '[':
            styled = _STYLED.match(text, index)
            if styled:
                label = styled.group(1)
                label_html, label_plain, consumed = _inline(label)
                if consumed < len(label):
                    raise _error('Libellé de style invalide', text, index)
                open_tag, close_tag = _style_to_html(styled.group(2))
                rendered.append(f'{open_tag}{label_html}{close_tag}')
                plain.append(label_plain)
                index = styled.end()
                continue
            label_end = text.find('](', index + 1)
            if label_end > -1:
                label = text[index + 1:label_end]
                url_start = label_end + 2
                url_end = _find_link_end(text, url_start)
                if url_end == -1:
                    raise _error('Lien non fermé', text, index)
                label_html, label_plain, consumed = _inline(label)
                if consumed < len(label):
                    raise _error('Libellé de lien invalide', text, index)
                url = _safe_url(text[url_start:url_end])
                rendered.append(
                    f'<a href="{html.escape(url, quote=True)}">'
                    f'{label_html}</a>'
                )
                plain.append(label_plain)
                index = url_end + 1
                continue

        for marker, open_tag, close_tag in (
            ('**', '<b>', '</b>'),
            ('++', '<u>', '</u>'),
            ('*', '<i>', '</i>'),
        ):
            if text.startswith(marker, index):
                value, value_plain, consumed = wrap(marker, open_tag, close_tag, index)
                rendered.append(value)
                plain.append(value_plain)
                index = consumed
                break
        else:
            rendered.append(html.escape(char))
            plain.append(char)
            index += 1

    if closing:
        raise _error(f'Marqueur « {closing} » non fermé', text, start)
    return ''.join(rendered), ''.join(plain), index


def _blocks(markdown):
    blocks = []
    lines = markdown.splitlines()
    index = 0

    def inline(line, line_number):
        try:
            value, plain, consumed = _inline(line)
            if consumed != len(line):
                raise _error('Contenu riche incomplet')
            return value, plain
        except RichTextValidationError as exc:
            raise RichTextValidationError(
                f'{exc} (ligne {line_number})'
            ) from exc

    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if not stripped:
            index += 1
            continue

        if _RAW_HTML.search(stripped):
            raise _error('Le HTML brut n’est pas autorisé', markdown)

        heading = re.match(r'^(#{1,3})\s+(.+)$', stripped)
        list_item = re.match(r'^(?:(-)|(\d+)\.)\s+(.+)$', stripped)
        quote = re.match(r'^>\s?(.*)$', stripped)

        if heading:
            value, plain = inline(heading.group(2), index + 1)
            blocks.append(
                RichBlock(
                    'heading',
                    value,
                    plain,
                    level=len(heading.group(1)),
                )
            )
            index += 1
            continue

        if list_item:
            ordered = list_item.group(2) is not None
            kind = 'ordered_list' if ordered else 'unordered_list'
            items = []
            while index < len(lines):
                current = re.match(r'^(?:(-)|(\d+)\.)\s+(.+)$', lines[index].strip())
                if not current or (current.group(2) is not None) != ordered:
                    break
                value, plain = inline(current.group(3), index + 1)
                marker = f'{current.group(2)}.' if ordered else '-'
                items.append((value, plain, marker))
                index += 1
            html_tag = 'ol' if ordered else 'ul'
            plain_items = '\n'.join(f'{marker} {text}' for _, text, marker in items)
            blocks.append(
                RichBlock(
                    kind,
                    f'<{html_tag}>{"".join(f"<li>{item[0]}</li>" for item in items)}</{html_tag}>',
                    plain_items,
                )
            )
            continue

        if quote:
            quote_html = []
            quote_plain = []
            while index < len(lines):
                current = re.match(r'^>\s?(.*)$', lines[index].strip())
                if not current:
                    break
                value, plain = inline(current.group(1), index + 1)
                quote_html.append(value)
                quote_plain.append(plain)
                index += 1
            blocks.append(
                RichBlock(
                    'quote',
                    f'<blockquote>{"<br/>".join(quote_html)}</blockquote>',
                    '\n'.join(quote_plain),
                )
            )
            continue

        paragraph = []
        while index < len(lines):
            current = lines[index].strip()
            if not current:
                break
            if re.match(r'^(#{1,3})\s+|^>\s?|^(?:-|\d+\.)\s+', current):
                break
            paragraph.append((current, index + 1))
            index += 1
        rendered = [inline(value, line) for value, line in paragraph]
        blocks.append(
            RichBlock(
                'paragraph',
                '<br/>'.join(item[0] for item in rendered),
                '\n'.join(item[1] for item in rendered),
            )
        )

    return blocks


def validate(content, content_format=FORMAT_MARKDOWN):
    value = content or ''
    if content_format == FORMAT_PLAIN:
        return value
    if content_format != FORMAT_MARKDOWN:
        raise _error(f'Format de contenu inconnu : {content_format}')
    if _RAW_HTML.search(value):
        raise _error('Le HTML brut n’est pas autorisé')
    _blocks(value)
    return value


def parse_blocks(content, content_format=FORMAT_MARKDOWN):
    value = content or ''
    if content_format == FORMAT_PLAIN:
        return [
            RichBlock('paragraph', html.escape(line), line)
            for line in value.splitlines()
            if line
        ]
    validate(value, content_format)
    return _blocks(value)


def to_plain(content, content_format=FORMAT_MARKDOWN):
    if content_format == FORMAT_PLAIN:
        return content or ''
    return '\n\n'.join(block.plain for block in parse_blocks(content, content_format))


def to_html(content, content_format=FORMAT_MARKDOWN):
    if content_format == FORMAT_PLAIN:
        return '<br/>'.join(html.escape(line) for line in (content or '').splitlines())
    output = []
    for block in parse_blocks(content, content_format):
        if block.kind == 'heading':
            output.append(
                f'<h{block.level}>{block.html}</h{block.level}>'
            )
        elif block.kind in {'ordered_list', 'unordered_list', 'quote'}:
            output.append(block.html)
        else:
            output.append(f'<p>{block.html}</p>')
    return ''.join(output)


def pdf_blocks(content, content_format=FORMAT_MARKDOWN):
    return parse_blocks(content, content_format)


def content_metrics(content, content_format=FORMAT_MARKDOWN, excerpt_length=280):
    plain = to_plain(content, content_format)
    words = re.findall(r"\b\w+(?:['’]\w+)*\b", plain, flags=re.UNICODE)
    excerpt = ' '.join(plain.split())
    if len(excerpt) > excerpt_length:
        excerpt = f'{excerpt[:excerpt_length].rstrip()}…'
    return {
        'characters': len(plain),
        'words': len(words),
        'excerpt': excerpt,
    }

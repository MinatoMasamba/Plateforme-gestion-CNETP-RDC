/// Conversion entre le « Markdown CNE-ITP » stocké côté serveur et le Delta
/// Quill affiché dans l’éditeur. Miroir de `apps/norms/rich_text.py` : toute
/// évolution du dialecte doit être répercutée dans les deux implémentations
/// (et dans `templates/static/js/components/cnetp-rich-text.js`).
library;

const cnetpFormatPlain = 'plain';
const cnetpFormatMarkdown = 'md';

const cnetpColors = {'bleu': '#0095c9', 'rouge': '#db3832', 'nuit': '#0a2540'};
const cnetpSizes = {'petit': 'small', 'grand': 'large', 'tres-grand': 'huge'};
const cnetpHighlight = '#fff24b';

class CnetpRichTextException implements Exception {
  CnetpRichTextException(this.message);
  final String message;

  @override
  String toString() => message;
}

class CnetpHeading {
  const CnetpHeading(this.level, this.text, this.offset);
  final int level;
  final String text;

  /// Position du titre dans le texte du document Quill.
  final int offset;
}

class _Run {
  _Run(this.text, [Map<String, dynamic>? attrs]) : attrs = attrs ?? {};
  final String text;
  final Map<String, dynamic> attrs;
}

class _Inline {
  _Inline(this.runs, this.end);
  final List<_Run> runs;
  final int end;
}

class _Line {
  _Line(this.kind, this.runs, {this.level, this.marker = ''});
  final String kind; // empty, heading, bullet, ordered, quote, paragraph
  final List<_Run> runs;
  final int? level;
  final String marker;

  String get plain => runs.map((run) => run.text).join();
}

final _rawHtml = RegExp(r'(?<!\\)<\s*/?\s*[a-zA-Z!]');
final _styled = RegExp(r'\[((?:\\.|[^\[\]\\\n])+)\]\{([^{}\n]+)\}');
final _headingLine = RegExp(r'^(#{1,3})\s+(.+)$');
final _listLine = RegExp(r'^(?:(-)|(\d+)\.)\s+(.+)$');
final _quoteLine = RegExp(r'^>\s?(.*)$');

List<String> _splitLines(String value) {
  if (value.isEmpty) return [];
  final lines = value.split(RegExp(r'\r\n|\r|\n'));
  if (lines.isNotEmpty && lines.last.isEmpty) lines.removeLast();
  return lines;
}

String _safeUrl(String value) {
  final url = value.trim();
  if (url.runes.any((c) => c < 33 || c == 0x7f)) {
    throw CnetpRichTextException(
      'Lien contenant des espaces ou caractères interdits',
    );
  }
  final uri = Uri.tryParse(url);
  if (uri == null) throw CnetpRichTextException('Lien mal formé');
  final scheme = uri.scheme.toLowerCase();
  if (!{'http', 'https', 'mailto'}.contains(scheme)) {
    throw CnetpRichTextException(
      'Lien interdit : seuls http, https et mailto sont acceptés',
    );
  }
  if (scheme != 'mailto' && uri.host.isEmpty) {
    throw CnetpRichTextException('Lien absolu incomplet');
  }
  if (scheme == 'mailto' && uri.path.isEmpty) {
    throw CnetpRichTextException('Adresse mailto vide');
  }
  return url;
}

/// Indique si [url] peut être enregistrée comme lien (http, https, mailto).
bool cnetpIsSafeUrl(String url) {
  try {
    _safeUrl(url);
    return true;
  } on CnetpRichTextException {
    return false;
  }
}

Map<String, dynamic> _styleAttrs(String attributes) {
  final result = <String, dynamic>{};
  for (final item in attributes.split('|')) {
    final separator = item.indexOf('=');
    if (separator < 0) {
      throw CnetpRichTextException('Attribut de style invalide');
    }
    final key = item.substring(0, separator).trim();
    final value = item.substring(separator + 1).trim();
    switch (key) {
      case 'taille':
        final size = cnetpSizes[value];
        if (size == null) {
          throw CnetpRichTextException('Taille de texte inconnue : $value');
        }
        result['size'] = size;
      case 'couleur':
        final color = cnetpColors[value];
        if (color == null) {
          throw CnetpRichTextException('Couleur de texte inconnue : $value');
        }
        result['color'] = color;
      case 'surlignage':
        if (value != 'jaune') {
          throw CnetpRichTextException('Surlignage inconnu : $value');
        }
        result['background'] = cnetpHighlight;
      default:
        throw CnetpRichTextException('Attribut non autorisé : $key');
    }
  }
  return result;
}

int _findClosing(String text, String marker, int position) {
  var escaped = false;
  for (var index = position; index < text.length; index++) {
    final char = text[index];
    if (escaped) {
      escaped = false;
    } else if (char == r'\') {
      escaped = true;
    } else if (text.startsWith(marker, index)) {
      return index;
    }
  }
  return -1;
}

int _findLinkEnd(String text, int position) {
  var depth = 0;
  for (var index = position; index < text.length; index++) {
    final char = text[index];
    if (char == '\n') break;
    if (char == '(') {
      depth++;
    } else if (char == ')') {
      if (depth == 0) return index;
      depth--;
    }
  }
  return -1;
}

List<_Run> _apply(List<_Run> runs, Map<String, dynamic> attrs) => [
  for (final run in runs) _Run(run.text, {...attrs, ...run.attrs}),
];

_Inline _inline(String text, [int start = 0, String? closing, int depth = 0]) {
  if (depth > 30) {
    throw CnetpRichTextException('Mise en forme trop profondément imbriquée');
  }
  final runs = <_Run>[];
  var index = start;
  while (index < text.length) {
    if (closing != null && text.startsWith(closing, index)) {
      return _Inline(runs, index + closing.length);
    }
    final char = text[index];
    if (char == r'\') {
      if (index + 1 >= text.length) {
        throw CnetpRichTextException("Caractère d'échappement sans valeur");
      }
      runs.add(_Run(text[index + 1]));
      index += 2;
      continue;
    }
    if (char == '[') {
      final styled = _styled.matchAsPrefix(text, index);
      if (styled != null) {
        final label = styled.group(1)!;
        final inner = _inline(label);
        if (inner.end < label.length) {
          throw CnetpRichTextException('Libellé de style invalide');
        }
        runs.addAll(_apply(inner.runs, _styleAttrs(styled.group(2)!)));
        index = styled.end;
        continue;
      }
      final labelEnd = text.indexOf('](', index + 1);
      if (labelEnd > -1) {
        final label = text.substring(index + 1, labelEnd);
        final urlStart = labelEnd + 2;
        final urlEnd = _findLinkEnd(text, urlStart);
        if (urlEnd == -1) throw CnetpRichTextException('Lien non fermé');
        final inner = _inline(label);
        if (inner.end < label.length) {
          throw CnetpRichTextException('Libellé de lien invalide');
        }
        final url = _safeUrl(text.substring(urlStart, urlEnd));
        runs.addAll(_apply(inner.runs, {'link': url}));
        index = urlEnd + 1;
        continue;
      }
    }
    var matched = false;
    for (final (marker, attr) in const [
      ('**', 'bold'),
      ('++', 'underline'),
      ('*', 'italic'),
    ]) {
      if (text.startsWith(marker, index)) {
        if (_findClosing(text, marker, index + marker.length) < 0) {
          throw CnetpRichTextException('Marqueur « $marker » non fermé');
        }
        final inner = _inline(text, index + marker.length, marker, depth + 1);
        runs.addAll(_apply(inner.runs, {attr: true}));
        index = inner.end;
        matched = true;
        break;
      }
    }
    if (!matched) {
      runs.add(_Run(char));
      index++;
    }
  }
  if (closing != null) {
    throw CnetpRichTextException('Marqueur « $closing » non fermé');
  }
  return _Inline(runs, index);
}

List<_Run> _inlineLine(String line, int lineNumber) {
  try {
    final result = _inline(line);
    if (result.end != line.length) {
      throw CnetpRichTextException('Contenu riche incomplet');
    }
    return result.runs;
  } on CnetpRichTextException catch (error) {
    throw CnetpRichTextException('${error.message} (ligne $lineNumber)');
  }
}

List<_Line> _parseLines(String source, String format) {
  final lines = _splitLines(source);
  if (format == cnetpFormatPlain) {
    return [
      for (final line in lines)
        line.isEmpty ? _Line('empty', []) : _Line('paragraph', [_Run(line)]),
    ];
  }
  if (format != cnetpFormatMarkdown) {
    throw CnetpRichTextException('Format de contenu inconnu : $format');
  }
  if (_rawHtml.hasMatch(source)) {
    throw CnetpRichTextException('Le HTML brut n’est pas autorisé');
  }
  final result = <_Line>[];
  for (var index = 0; index < lines.length; index++) {
    final stripped = lines[index].trim();
    final number = index + 1;
    if (stripped.isEmpty) {
      result.add(_Line('empty', []));
      continue;
    }
    final heading = _headingLine.firstMatch(stripped);
    if (heading != null) {
      result.add(
        _Line(
          'heading',
          _inlineLine(heading.group(2)!, number),
          level: heading.group(1)!.length,
        ),
      );
      continue;
    }
    final item = _listLine.firstMatch(stripped);
    if (item != null) {
      final ordered = item.group(2) != null;
      result.add(
        _Line(
          ordered ? 'ordered' : 'bullet',
          _inlineLine(item.group(3)!, number),
          marker: ordered ? '${item.group(2)}.' : '-',
        ),
      );
      continue;
    }
    final quote = _quoteLine.firstMatch(stripped);
    if (quote != null) {
      result.add(_Line('quote', _inlineLine(quote.group(1)!, number)));
      continue;
    }
    result.add(_Line('paragraph', _inlineLine(stripped, number)));
  }
  return result;
}

/// Lève [CnetpRichTextException] si [source] n’est pas un contenu valide.
void cnetpValidate(String source, [String format = cnetpFormatMarkdown]) {
  _parseLines(source, format);
}

/// Texte brut, regroupé en blocs comme `rich_text.to_plain` côté serveur.
String cnetpToPlain(String source, [String format = cnetpFormatMarkdown]) {
  if (format == cnetpFormatPlain) return source;
  final lines = _parseLines(source, format);
  final blocks = <String>[];
  var index = 0;
  while (index < lines.length) {
    final line = lines[index];
    if (line.kind == 'empty') {
      index++;
      continue;
    }
    if (line.kind == 'heading') {
      blocks.add(line.plain);
      index++;
      continue;
    }
    final group = <String>[];
    final kind = line.kind;
    while (index < lines.length && lines[index].kind == kind) {
      final current = lines[index];
      group.add(
        kind == 'bullet' || kind == 'ordered'
            ? '${current.marker} ${current.plain}'
            : current.plain,
      );
      index++;
    }
    blocks.add(group.join('\n'));
  }
  return blocks.join('\n\n');
}

/// Delta Quill (liste d’opérations JSON) correspondant à [source].
/// Un contenu Markdown invalide est affiché tel quel plutôt que perdu.
List<Map<String, dynamic>> cnetpToDelta(
  String source, [
  String format = cnetpFormatMarkdown,
]) {
  List<_Line> lines;
  try {
    lines = _parseLines(source, format);
  } on CnetpRichTextException {
    lines = _parseLines(source, cnetpFormatPlain);
  }
  final ops = <Map<String, dynamic>>[];
  for (final line in lines) {
    for (final run in line.runs) {
      if (run.text.isEmpty) continue;
      ops.add({
        'insert': run.text,
        if (run.attrs.isNotEmpty) 'attributes': Map.of(run.attrs),
      });
    }
    final block = switch (line.kind) {
      'heading' => {'header': line.level},
      'bullet' => {'list': 'bullet'},
      'ordered' => {'list': 'ordered'},
      'quote' => {'blockquote': true},
      _ => <String, dynamic>{},
    };
    ops.add({'insert': '\n', if (block.isNotEmpty) 'attributes': block});
  }
  if (ops.isEmpty) ops.add({'insert': '\n'});
  return _mergeOps(ops);
}

List<Map<String, dynamic>> _mergeOps(List<Map<String, dynamic>> ops) {
  final merged = <Map<String, dynamic>>[];
  for (final op in ops) {
    final previous = merged.isEmpty ? null : merged.last;
    final insert = op['insert'];
    if (previous != null &&
        insert is String &&
        insert != '\n' &&
        previous['insert'] is String &&
        !(previous['insert'] as String).endsWith('\n') &&
        _sameAttrs(previous['attributes'], op['attributes'])) {
      previous['insert'] = '${previous['insert']}$insert';
    } else {
      merged.add(Map.of(op));
    }
  }
  return merged;
}

bool _sameAttrs(dynamic a, dynamic b) {
  final left = (a as Map?) ?? const {};
  final right = (b as Map?) ?? const {};
  if (left.length != right.length) return false;
  for (final entry in left.entries) {
    if (right[entry.key] != entry.value) return false;
  }
  return true;
}

String _escape(String text) =>
    text.replaceAllMapped(RegExp(r'[\\*+\[\]<]'), (m) => '\\${m[0]}');

String? _key(Map<String, String> map, dynamic value) {
  if (value is! String) return null;
  final normalized = value.toLowerCase();
  for (final entry in map.entries) {
    if (entry.value == normalized) return entry.key;
  }
  return null;
}

String _serializeRun(String text, Map attrs) {
  var value = _escape(text);
  if (attrs['underline'] == true) value = '++$value++';
  if (attrs['italic'] == true) value = '*$value*';
  if (attrs['bold'] == true) value = '**$value**';
  final styles = [
    if (_key(cnetpSizes, attrs['size']) case final size?) 'taille=$size',
    if (_key(cnetpColors, attrs['color']) case final color?) 'couleur=$color',
    if ('${attrs['background']}'.toLowerCase() == cnetpHighlight)
      'surlignage=jaune',
  ];
  if (styles.isNotEmpty) value = '[$value]{${styles.join('|')}}';
  final link = attrs['link'];
  if (link is String && cnetpIsSafeUrl(link)) {
    var url = link.trim();
    var depth = 0;
    for (final char in url.split('')) {
      if (char == '(') depth++;
      if (char == ')' && --depth < 0) break;
    }
    if (depth != 0) {
      url = url.replaceAll('(', '%28').replaceAll(')', '%29');
    }
    value = '[$value]($url)';
  }
  return value;
}

final _blockLike = RegExp(r'^(?:#|>|-\s|\d+\.\s)');

/// Markdown CNE-ITP correspondant au Delta Quill [ops].
String cnetpFromDelta(List<dynamic> ops) {
  final output = <String>[];
  var runs = <_Run>[];
  var ordered = 0;

  void closeLine(Map attrs) {
    final merged = <_Run>[];
    for (final run in runs) {
      if (run.text.isEmpty) continue;
      if (merged.isNotEmpty && _sameAttrs(merged.last.attrs, run.attrs)) {
        merged[merged.length - 1] = _Run(
          '${merged.last.text}${run.text}',
          merged.last.attrs,
        );
      } else {
        merged.add(run);
      }
    }
    final plain = merged.map((run) => run.text).join();
    var inline = merged.map((run) => _serializeRun(run.text, run.attrs)).join();
    final header = attrs['header'];
    final list = attrs['list'];
    ordered = list == 'ordered' ? ordered + 1 : 0;
    if (plain.trim().isEmpty) {
      output.add('');
    } else if (header is int && header > 0) {
      output.add('${'#' * header.clamp(1, 3)} $inline');
    } else if (list == 'bullet' || list == 'unchecked' || list == 'checked') {
      output.add('- $inline');
    } else if (list == 'ordered') {
      output.add('$ordered. $inline');
    } else if (attrs['blockquote'] == true) {
      output.add('> $inline');
    } else {
      inline = inline.trim();
      final match = _blockLike.firstMatch(inline);
      if (match != null) {
        final dot = match[0]!.indexOf('.');
        inline = dot > 0
            ? '${inline.substring(0, dot)}\\${inline.substring(dot)}'
            : '\\$inline';
      }
      output.add(inline);
    }
    runs = [];
  }

  for (final raw in ops) {
    if (raw is! Map) continue;
    final insert = raw['insert'];
    final attrs = (raw['attributes'] as Map?) ?? const {};
    if (insert is! String) continue;
    final parts = insert.split('\n');
    for (var i = 0; i < parts.length; i++) {
      if (parts[i].isNotEmpty) {
        runs.add(_Run(parts[i], Map<String, dynamic>.from(attrs)));
      }
      if (i < parts.length - 1) closeLine(attrs);
    }
  }
  if (runs.isNotEmpty) closeLine(const {});
  while (output.isNotEmpty && output.last.isEmpty) {
    output.removeLast();
  }
  return output.join('\n');
}

/// Titres (niveaux 1 à 3) d’un Delta, pour construire un sommaire.
List<CnetpHeading> cnetpOutline(List<dynamic> ops) {
  final headings = <CnetpHeading>[];
  final line = StringBuffer();
  var offset = 0, lineStart = 0;
  for (final raw in ops) {
    if (raw is! Map) continue;
    final insert = raw['insert'];
    if (insert is! String) {
      offset++;
      continue;
    }
    final parts = insert.split('\n');
    for (var i = 0; i < parts.length; i++) {
      line.write(parts[i]);
      offset += parts[i].length;
      if (i < parts.length - 1) {
        final header = (raw['attributes'] as Map?)?['header'];
        final text = line.toString().trim();
        if (header is int && text.isNotEmpty) {
          headings.add(CnetpHeading(header, text, lineStart));
        }
        line.clear();
        offset++;
        lineStart = offset;
      }
    }
  }
  return headings;
}

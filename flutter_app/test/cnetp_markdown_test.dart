import 'dart:convert';
import 'dart:io';

import 'package:cnetp_app/core/rich_text/cnetp_markdown.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final cases =
      jsonDecode(
            File('../tests/fixtures/rich_text_cases.json').readAsStringSync(),
          )
          as List;

  group('Parité Markdown CNE-ITP (fixtures partagées)', () {
    for (final raw in cases) {
      final item = raw as Map<String, dynamic>;
      final source = item['source'] as String;
      final format = item['content_format'] as String;
      test(item['name'], () {
        if (item['error'] == true) {
          expect(
            () => cnetpValidate(source, format),
            throwsA(isA<CnetpRichTextException>()),
          );
          return;
        }
        expect(cnetpToPlain(source, format), item['plain']);
        // Delta → Markdown → Delta est stable et conserve le texte brut.
        final delta = cnetpToDelta(source, format);
        final markdown = cnetpFromDelta(delta);
        expect(cnetpToDelta(markdown), delta);
        expect(cnetpToPlain(markdown), item['plain']);
      });
    }
  });

  test('les styles hors palette et les liens dangereux sont ignorés', () {
    final markdown = cnetpFromDelta([
      {
        'insert': 'Rose',
        'attributes': {'color': '#ff00ff', 'bold': true},
      },
      {
        'insert': ' lien',
        'attributes': {'link': 'javascript:alert(1)'},
      },
      {'insert': '\n'},
    ]);
    expect(markdown, '**Rose** lien');
  });

  test('le sommaire liste les titres avec leur position', () {
    final outline = cnetpOutline(
      cnetpToDelta('# Domaine\n\nTexte\n## Exigences'),
    );
    expect(outline.map((h) => (h.level, h.text, h.offset)), [
      (1, 'Domaine', 0),
      (2, 'Exigences', 15),
    ]);
  });
}

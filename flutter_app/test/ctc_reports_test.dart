import 'dart:convert';
import 'dart:typed_data';

import 'package:cnetp_app/features/ctc/widgets/ctc_reports.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_quill/flutter_quill.dart' as quill;
import 'package:cnetp_app/features/ctc/widgets/report_fixed_editor.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> report() => {
  'id': 5,
  'reference': 'RAP-ST-TEST',
  'revision': 2,
  'mine': true,
  'owner_name': 'Gestionnaire',
  'template_id': null,
  'dispatch_count': 0,
  'dispatches': [],
  'versions': [
    for (final n in [2, 1])
      {
        'number': n,
        'title': 'Rapport de suivi v$n',
        'author_name': 'Gestionnaire',
        'period_start': '2026-11-01',
        'period_end': '2026-11-08',
        'sections': [
          {'title': 'Activité', 'content': 'Contenu de la version $n'},
        ],
      },
  ],
};

class _Adapter implements HttpClientAdapter {
  final reads = <RequestOptions>[];
  final posts = <RequestOptions>[];
  bool conflict = false;
  Map<String, dynamic> current = report();
  ResponseBody json(dynamic data, [int status = 200]) =>
      ResponseBody.fromString(
        jsonEncode(data),
        status,
        headers: {
          Headers.contentTypeHeader: [Headers.jsonContentType],
        },
      );

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? stream,
    Future<void>? cancelFuture,
  ) async {
    final path = options.uri.path;
    if (options.method == 'POST') {
      posts.add(options);
      if (conflict) {
        return json({
          'detail': 'Révision obsolète ; recharger le rapport.',
        }, 409);
      }
      final body = options.data is String
          ? jsonDecode(options.data)
          : options.data;
      if (path.endsWith('/cover-preview/')) {
        return ResponseBody.fromBytes(
          base64Decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aL1kAAAAASUVORK5CYII=',
          ),
          200,
          headers: {
            Headers.contentTypeHeader: ['image/png'],
          },
        );
      }
      if (path.endsWith('/templates/')) {
        return json({
          'id': 8,
          'name': body['name'],
          'sections': body['sections'],
        }, 201);
      }
      if (path.endsWith('/send/')) return json({'recipient_count': 2}, 201);
      current = {
        ...current,
        'revision': (current['revision'] as int) + 1,
        'versions': [
          {'number': (current['revision'] as int) + 1, ...body},
          ...(current['versions'] as List),
        ],
      };
      return json(current, 201);
    }
    reads.add(options);
    if (path.endsWith('/export/')) {
      return ResponseBody.fromBytes(
        options.queryParameters['file_format'] == 'pdf'
            ? utf8.encode('%PDF-test')
            : [80, 75, 3, 4],
        200,
        headers: {
          Headers.contentTypeHeader: ['application/octet-stream'],
        },
      );
    }
    if (path.endsWith('/communications/targets/')) {
      return json({
        'results': [
          {
            'id': 1,
            'type': 'SC',
            'code': 'SC-IT',
            'label': 'Transport',
            'recipient_count': 2,
            'sendable': true,
          },
        ],
      });
    }
    if (path.endsWith('/sources/99/')) {
      if (options.queryParameters['original'] == 1) {
        return ResponseBody.fromBytes(
          [80, 75, 3, 4],
          200,
          headers: {
            Headers.contentTypeHeader: ['application/octet-stream'],
          },
        );
      }
      if (options.queryParameters.containsKey('page')) {
        return ResponseBody.fromBytes(
          base64Decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aL1kAAAAASUVORK5CYII=',
          ),
          200,
          headers: {
            Headers.contentTypeHeader: ['image/png'],
          },
        );
      }
      return json({
        'id': 99,
        'name': 'modele.pdf',
        'pages': [
          {'width': 595, 'height': 842},
          {'width': 595, 'height': 842},
        ],
        'sections': [
          {'title': 'Synthèse', 'content': 'Texte du modèle'},
        ],
        'note': '',
      });
    }
    if (path.endsWith('/templates/')) {
      return json({
        'results': [
          {
            'id': 1,
            'name': 'Rapport mensuel',
            'source_id': 99,
            'collection': 'page_bleue',
            'document': {
              'source_start_page': 1,
              'cover': {'recipient': 'COPIL'},
            },
            'sections': [
              {'title': 'Synthèse', 'content': 'Structure réutilisable'},
            ],
          },
          {
            'id': 2,
            'name': 'Référence documentaire',
            'source_id': 98,
            'collection': 'reference',
            'sections': [
              {'title': 'Objet', 'content': ''},
            ],
          },
        ],
      });
    }
    if (path.endsWith('/reports/5/')) return json(current);
    return json({
      'results': [current],
    });
  }

  @override
  void close({bool force = false}) {}
}

Finder field(String label) => find.byWidgetPredicate(
  (w) => w is TextField && w.decoration?.labelText == label,
);
Future<void> tap(WidgetTester tester, String label) async {
  await tester.pumpAndSettle();
  await tester.ensureVisible(find.text(label));
  await tester.pumpAndSettle();
  await tester.tap(find.text(label));
  await tester.pumpAndSettle();
}

void main() {
  late _Adapter adapter;
  late List<String> files;
  Future<void> pump(WidgetTester tester, {double width = 1280}) async {
    adapter = _Adapter();
    files = [];
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = Size(width, 1800);
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: CtcReportsView(
            client: Dio()..httpClientAdapter = adapter,
            saveFile: (bytes, name, mime) async {
              expect(bytes, isNotEmpty);
              files.add(name);
            },
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('Saved report exports PDF and Word with the selected revision', (
    tester,
  ) async {
    await pump(tester);
    await tap(tester, 'Ouvrir le rapport');
    await tap(tester, 'Exporter en PDF');
    await tap(tester, 'Exporter en Word');
    expect(files, ['RAP-ST-TEST-v2.pdf', 'RAP-ST-TEST-v2.docx']);
    expect(
      adapter.reads
          .where((r) => r.uri.path.endsWith('/export/'))
          .every((r) => r.queryParameters['revision'] == 2),
      true,
    );
    expect(adapter.posts, isEmpty);
  });

  testWidgets('Revision conflict keeps the edited draft intact', (
    tester,
  ) async {
    await pump(tester);
    await tap(tester, 'Ouvrir le rapport');
    await tester.enterText(field('Titre du rapport'), 'Mon titre corrigé');
    adapter.conflict = true;
    await tap(tester, 'Sauvegarder une version');
    expect(
      find.text('Révision obsolète ; recharger le rapport.'),
      findsOneWidget,
    );
    expect(
      (tester.widget<TextField>(field('Titre du rapport'))).controller!.text,
      'Mon titre corrigé',
    );
    expect(adapter.posts.single.data['revision'], 2);
  });

  testWidgets(
    'Historical report is read-only and exports the historical revision',
    (tester) async {
      await pump(tester);
      await tap(tester, 'Ouvrir le rapport');
      await tester.ensureVisible(find.text('Version 2 — Gestionnaire'));
      await tester.tap(find.text('Version 2 — Gestionnaire'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Version 1 — Gestionnaire').last);
      await tester.pumpAndSettle();
      expect(
        tester.widget<TextField>(field('Titre du rapport')).readOnly,
        true,
      );
      expect(find.text('Sauvegarder une version'), findsNothing);
      await tap(tester, 'Exporter en PDF');
      expect(files.single, 'RAP-ST-TEST-v1.pdf');
    },
  );

  testWidgets('New report validates title and sections before saving', (
    tester,
  ) async {
    await pump(tester);
    await tap(tester, 'Page blanche');
    await tap(tester, 'Sauvegarder une version');
    expect(find.text('Le titre du rapport est requis.'), findsOneWidget);
    expect(adapter.posts, isEmpty);
    await tester.enterText(field('Titre du rapport'), 'Rapport nouveau');
    await tester.enterText(field('Contenu de section 1'), 'Travail effectué');
    await tap(tester, 'Sauvegarder une version');
    expect(adapter.posts.single.uri.path, '/api/v1/st/reports/');
    expect(
      adapter.posts.single.data['sections'][0]['content'],
      'Travail effectué',
    );
    expect(find.textContaining('Aucun envoi effectué'), findsOneWidget);
  });

  testWidgets('Report editor and preview fit a mobile screen', (tester) async {
    await pump(tester, width: 390);
    await tap(tester, 'Ouvrir le rapport');
    await tap(tester, 'Prévisualiser');
    expect(
      find.text('Document de travail non approuvé', skipOffstage: false),
      findsNothing,
    );
    expect(
      find.textContaining('Document de travail non approuvé'),
      findsOneWidget,
    );
    expect(find.text('Contenu de la version 2'), findsWidgets);
    await tap(tester, 'Fermer l’aperçu');
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'Transmission requires explicit confirmation and carries a request key',
    (tester) async {
      await pump(tester);
      await tap(tester, 'Ouvrir le rapport');
      final target = find.text('SC ou GT destinataire');
      await tester.ensureVisible(target);
      await tester.tap(target);
      await tester.pumpAndSettle();
      await tester.tap(find.text('SC · SC-IT — Transport').last);
      await tester.pumpAndSettle();
      await tap(tester, 'Transmettre le rapport');
      expect(adapter.posts, isEmpty);
      await tap(tester, 'Confirmer la transmission');
      final sent = adapter.posts.single;
      expect(sent.data['revision'], 2);
      expect(sent.data['sc_id'], 1);
      expect(
        sent.data['request_key'],
        matches(
          RegExp(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
          ),
        ),
      );
    },
  );
  testWidgets('Rich formatting is retained in a saved version', (tester) async {
    await pump(tester);
    await tap(tester, 'Ouvrir le rapport');
    await tap(tester, 'Activer la mise en forme');
    final editor = tester.widget<quill.QuillEditor>(
      find.byType(quill.QuillEditor),
    );
    editor.controller.document.insert(0, 'Nouveau ');
    editor.controller.formatText(0, 7, quill.Attribute.bold);
    await tester.pumpAndSettle();
    await tap(tester, 'Sauvegarder une version');
    final section = adapter.posts.last.data['sections'][0] as Map;
    expect(section['content'], startsWith('Nouveau '));
    expect(
      (section['delta'] as List).any((op) => op['attributes']?['bold'] == true),
      true,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('Template offers both modes and preserves the source on save', (
    tester,
  ) async {
    await pump(tester, width: 390);
    await tap(tester, 'Page blanche');
    final models = find.byType(DropdownButtonFormField<int>).first;
    await tester.ensureVisible(models);
    await tester.pumpAndSettle();
    await tester.tap(models);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Rapport mensuel').last);
    await tester.pumpAndSettle();
    expect(find.text('Conserver la présentation'), findsOneWidget);
    expect(find.text('Rédaction libre'), findsOneWidget);
    await tester.tap(find.text('Conserver la présentation'));
    await tester.pumpAndSettle();
    expect(find.byType(ReportFixedEditor), findsOneWidget);
    await tester.enterText(field('Titre du rapport'), 'Modèle rempli');
    await tap(tester, 'Sauvegarder une version');
    expect(adapter.posts.last.data['source_id'], 99);
    expect(adapter.posts.last.data['document']['mode'], 'fixed');
    expect(adapter.posts.last.data['document']['source_start_page'], 1);
    expect(
      adapter.reads.any(
        (r) =>
            r.uri.path.endsWith('/sources/99/') &&
            r.queryParameters['page'] == 1,
      ),
      true,
    );
    expect(tester.takeException(), isNull);
  });
  testWidgets('Catalogue shows pack models and downloads the source original', (
    tester,
  ) async {
    await pump(tester);
    expect(find.text('Rapport mensuel'), findsOneWidget);
    expect(find.text('Référence documentaire'), findsNothing);
    final button = find.byTooltip('Télécharger le modèle original');
    await tester.ensureVisible(button);
    await tester.pumpAndSettle();
    await tester.tap(button);
    await tester.pumpAndSettle();
    expect(files.single, 'modele.pdf');
    expect(adapter.posts, isEmpty);
    expect(
      adapter.reads.any((r) => r.uri.path.endsWith('/sources/98/')),
      false,
    );
  });

  testWidgets(
    'Cover fields are previewed and saved with the selected version',
    (tester) async {
      await pump(tester);
      await tap(tester, 'Ouvrir le rapport');
      await tap(tester, 'Page zéro · couverture bleue');
      await tester.enterText(
        field('À l’attention de'),
        'Destinataire personnalisé',
      );
      await tap(tester, 'Voir la page de couverture');
      expect(
        adapter.posts.single.uri.path,
        '/api/v1/st/reports/cover-preview/',
      );
      expect(
        adapter.posts.single.data['recipient'],
        'Destinataire personnalisé',
      );
      await tap(tester, 'Fermer');
      await tap(tester, 'Sauvegarder une version');
      expect(
        adapter.posts.last.data['document']['cover']['recipient'],
        'Destinataire personnalisé',
      );
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets('Model table cells remain editable and versioned', (
    tester,
  ) async {
    await pump(tester, width: 390);
    await tap(tester, 'Ouvrir le rapport');
    await tap(tester, 'Activer la mise en forme');
    final editor = tester.widget<quill.QuillEditor>(
      find.byType(quill.QuillEditor),
    );
    editor.controller.replaceText(
      0,
      0,
      'Indicateur | Valeur\nDossiers | À remplir\n',
      const TextSelection.collapsed(offset: 0),
    );
    await tester.pumpAndSettle();
    await tap(tester, 'Modifier les tableaux');
    await tester.enterText(field('Ligne 1 · colonne 2'), '12');
    await tap(tester, 'Ajouter une ligne');
    await tester.enterText(field('Ligne 2 · colonne 1'), 'Versions');
    await tester.enterText(field('Ligne 2 · colonne 2'), '5');
    await tap(tester, 'Appliquer les tableaux');
    await tap(tester, 'Sauvegarder une version');
    final content = adapter.posts.last.data['sections'][0]['content'] as String;
    expect(content, contains('Dossiers | 12'));
    expect(content, contains('Versions | 5'));
    expect(content, contains('Contenu de la version 2'));
    expect(tester.takeException(), isNull);
  });
}

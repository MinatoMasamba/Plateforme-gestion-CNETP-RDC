import 'dart:convert';
import 'dart:typed_data';

import 'package:cnetp_app/features/ctc/widgets/ctc_reports.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
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
    if (path.endsWith('/templates/')) {
      return json({
        'results': [
          {
            'id': 1,
            'name': 'Rapport mensuel',
            'sections': [
              {'title': 'Synthèse', 'content': 'Structure réutilisable'},
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
  await tester.ensureVisible(find.text(label));
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
}

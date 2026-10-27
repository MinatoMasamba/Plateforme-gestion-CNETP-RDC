import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:cnetp_app/core/api/api_client.dart';
import 'package:cnetp_app/features/expert/widgets/expert_history_tab.dart';
import 'package:cnetp_app/features/expert/widgets/expert_profile_tab.dart';
import 'package:cnetp_app/features/expert/widgets/expert_theme.dart';

Widget _wrap(Widget child) => MaterialApp(
  home: ExpertTheme(
    palette: ExpertPalette.dark,
    child: Scaffold(body: child),
  ),
);

Future<void> _pumpUntil(WidgetTester tester, bool Function() condition) async {
  for (var attempt = 0; attempt < 120; attempt++) {
    if (condition()) return;
    await Future<void>.delayed(const Duration(milliseconds: 25));
    await tester.pump();
  }
}

class _FakeAdapter implements HttpClientAdapter {
  _FakeAdapter(this.versions, this.profile);

  final List<Map<String, dynamic>> versions;
  final Map<String, dynamic> profile;
  final List<RequestOptions> requests = [];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    final path = options.uri.path;
    dynamic data;
    if (path.endsWith('/versions/')) {
      data = versions;
    } else if (path.endsWith('/diff/')) {
      data = {
        'diff_segments': [
          {
            'type': 'equal',
            'text': 'Article 1 — Objet et champ d’application. ',
          },
          {'type': 'delete', 'text': 'Ancienne clause retirée. '},
          {'type': 'insert', 'text': 'Nouvelle clause de conformité ISO. '},
          {'type': 'equal', 'text': 'Article 2 — Références normatives.'},
        ],
      };
    } else if (path.endsWith('/experts/me/')) {
      data = profile;
    } else if (path.endsWith('/my-affiliation/')) {
      data = {
        'ctm': 1,
        'wgs': [11],
        'bureau_ctm_ids': [],
        'ctms': [
          {'id': 1, 'number': 1, 'name': 'Sous-commission initiale'},
          {'id': 2, 'number': 2, 'name': 'Sous-commission cible'},
        ],
        'workgroups': [
          {'id': 11, 'ctm_id': 1, 'name': 'Groupe initial'},
          {'id': 22, 'ctm_id': 2, 'name': 'Groupe cible'},
        ],
      };
    } else if (options.method == 'PATCH') {
      data = <String, dynamic>{'ok': true};
    } else {
      data = <String, dynamic>{};
    }
    return ResponseBody.fromString(
      jsonEncode(data),
      200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late HttpClientAdapter previous;
  late _FakeAdapter adapter;

  setUp(() {
    previous = ApiClient.dio.httpClientAdapter;
    adapter = _FakeAdapter(
      [
        {
          'version_number': 3,
          'summary': 'Mise à jour des clauses de conformité et des références.',
          'author_name': 'Ir. Jean-Pierre Kabange',
          'created_at': '2026-10-24T10:48:00Z',
        },
        {
          'version_number': 2,
          'summary': 'Ajout de la section sur la gouvernance.',
          'author_name': 'Eddy Masamba',
          'created_at': '2026-10-23T09:12:00Z',
        },
        {
          'version_number': 1,
          'summary': 'Version initiale.',
          'author_name': 'Eddy Masamba',
          'created_at': '2026-10-20T08:00:00Z',
        },
      ],
      {
        'id': 7,
        'user': {
          'first_name': 'Jean-Pierre',
          'last_name': 'Kabange',
          'email': 'jp.kabange@cne-itp.cd',
          'phone': '+243 970 000 000',
        },
        'structure': {'name': 'CNE-ITP'},
        'specialties': 'Électricité, ICT, Normalisation',
        'bank_name': 'Equity BCDC',
        'bank_account': '00019-992381',
        'ctm_name': 'CTM 1 — Normes électriques',
        'role_id': 'EXPERT',
        'affectations': [
          {'wg_name': 'WG 1 — Installations'},
          {'wg_name': 'WG 2 — Réseaux'},
        ],
      },
    );
    ApiClient.dio.httpClientAdapter = adapter;
  });

  tearDown(() {
    ApiClient.dio.httpClientAdapter = previous;
  });

  for (final size in const [Size(1440, 900), Size(1024, 768), Size(704, 828)]) {
    testWidgets('History with data renders at $size', (tester) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);

      await tester.runAsync(() async {
        await tester.pumpWidget(
          _wrap(
            const ExpertHistoryTab(docId: '1', docTitle: 'Norme technique'),
          ),
        );
        await _pumpUntil(
          tester,
          () =>
              find.text('v3').evaluate().isNotEmpty &&
              find.byType(SelectableText).evaluate().isNotEmpty,
        );
      });

      expect(tester.takeException(), isNull);
      expect(find.text('v3'), findsWidgets);
      expect(find.text('v3 (Ir.)'), findsOneWidget);
      expect(find.text('v2 (Eddy)'), findsOneWidget);
      expect(find.byType(SelectableText), findsOneWidget);
    });

    testWidgets('Profile with data renders at $size', (tester) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);

      await tester.runAsync(() async {
        await tester.pumpWidget(
          _wrap(
            ExpertProfileTab(
              dark: true,
              fallbackName: 'Expert',
              fallbackEmail: '',
              onThemeChanged: (_) {},
            ),
          ),
        );
        await _pumpUntil(
          tester,
          () => find
              .byWidgetPredicate(
                (widget) =>
                    widget is DropdownButton<String> && widget.value == '1',
              )
              .evaluate()
              .isNotEmpty,
        );
      });

      expect(tester.takeException(), isNull);
      // Le sélecteur affiche le catalogue de my-affiliation, pas l’ancien
      // libellé ctm_name du profil. Vérifier également l’identifiant sélectionné.
      final ctm = tester.widget<DropdownButton<String>>(
        find.byWidgetPredicate(
          (widget) => widget is DropdownButton<String> && widget.value == '1',
        ),
      );
      expect(ctm.value, '1');
      expect(
        (ctm.items!.singleWhere((item) => item.value == '1').child as Text)
            .data,
        'Sous-commission initiale',
      );
    });
  }

  testWidgets('History compare loads the selected versions', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.runAsync(() async {
      await tester.pumpWidget(
        _wrap(const ExpertHistoryTab(docId: '1', docTitle: 'Norme technique')),
      );
      await _pumpUntil(
        tester,
        () =>
            find.text('Comparer').evaluate().length == 3 &&
            find.byType(SelectableText).evaluate().isNotEmpty,
      );
    });

    await tester.runAsync(() async {
      await tester.tap(find.text('Comparer').last);
      await tester.pump();
      await _pumpUntil(
        tester,
        () =>
            adapter.requests
                .where((request) => request.uri.path.endsWith('/diff/'))
                .length >=
            2,
      );
    });

    expect(tester.takeException(), isNull);
    final diffs = adapter.requests
        .where((request) => request.uri.path.endsWith('/diff/'))
        .toList();
    expect(diffs, hasLength(2));
    expect(diffs.last.uri.queryParameters['v1'], '1');
    expect(diffs.last.uri.queryParameters['v2'], '3');
  });

  testWidgets('Profile selects and saves affiliation inside Flutter', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 1200);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    var refreshed = false;
    await tester.runAsync(() async {
      await tester.pumpWidget(
        _wrap(
          ExpertProfileTab(
            dark: true,
            fallbackName: 'Expert',
            fallbackEmail: '',
            onThemeChanged: (_) {},
            onAffiliationSaved: () => refreshed = true,
          ),
        ),
      );
      await _pumpUntil(
        tester,
        () => find.byType(DropdownButton<String>).evaluate().isNotEmpty,
      );
    });
    await tester.ensureVisible(find.byType(DropdownButton<String>).first);
    await tester.tap(find.byType(DropdownButton<String>).first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Sous-commission cible').last);
    await tester.pumpAndSettle();
    expect(find.text('Groupe initial'), findsNothing);
    await tester.tap(find.byType(DropdownButton<String>).at(1));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Groupe cible').last);
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('SAUVEGARDER'));
    await tester.runAsync(() async {
      await tester.tap(find.text('SAUVEGARDER'));
      await _pumpUntil(
        tester,
        () => refreshed && find.text('SAUVEGARDER').evaluate().isEmpty,
      );
    });
    final request = adapter.requests.singleWhere(
      (r) => r.method == 'PATCH' && r.path.endsWith('/my-affiliation/'),
    );
    expect(request.data, {
      'ctm': 2,
      'wgs': [22],
    });
    expect(refreshed, isTrue);
    expect(find.text('Profil enregistré.'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Profile save persists identity and expert fields', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.runAsync(() async {
      await tester.pumpWidget(
        _wrap(
          ExpertProfileTab(
            dark: true,
            fallbackName: 'Expert',
            fallbackEmail: '',
            onThemeChanged: (_) {},
          ),
        ),
      );
      await tester.pump();
      await Future<void>.delayed(const Duration(milliseconds: 100));
      await tester.pump();
    });

    await tester.enterText(find.byType(TextField).first, 'Jean Pierre Kabange');
    await tester.pump();
    expect(find.text('SAUVEGARDER'), findsOneWidget);

    await tester.ensureVisible(find.text('SAUVEGARDER'));
    await tester.pump();

    await tester.runAsync(() async {
      await tester.tap(find.text('SAUVEGARDER'));
      await tester.pump();
      await Future<void>.delayed(const Duration(milliseconds: 100));
      await tester.pump();
    });

    expect(tester.takeException(), isNull);
    expect(find.text('SAUVEGARDER'), findsNothing);

    final patches = adapter.requests
        .where((request) => request.method == 'PATCH')
        .toList();
    expect(
      patches.map((request) => request.uri.path),
      containsAll(['/api/v1/auth/profile/', '/api/v1/experts/7/']),
    );

    final identity =
        patches
                .firstWhere(
                  (request) => request.uri.path == '/api/v1/auth/profile/',
                )
                .data
            as Map;
    expect(identity['first_name'], 'Jean Pierre');
    expect(identity['last_name'], 'Kabange');
    expect(identity['email'], 'jp.kabange@cne-itp.cd');
    expect(identity['phone'], '+243 970 000 000');

    final expert =
        patches
                .firstWhere(
                  (request) => request.uri.path == '/api/v1/experts/7/',
                )
                .data
            as Map;
    expect(expert['specialties'], 'Électricité, ICT, Normalisation');
    expect(expert['bank_name'], 'Equity BCDC');
    expect(expert['bank_account'], '00019-992381');
    expect(expert.containsKey('user_phone'), isFalse);
  });
}

import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cnetp_app/core/api/api_client.dart';
import 'package:cnetp_app/features/ctc/ctc_screen.dart';
import 'package:cnetp_app/features/ctc/widgets/ctc_dashboard.dart';
import 'package:cnetp_app/features/ctc/widgets/ctc_topbar.dart';
import 'package:cnetp_app/features/ctc/widgets/ctc_sidebar.dart';
import 'package:cnetp_app/features/ctc/widgets/ctc_requests_view.dart';
import 'package:cnetp_app/features/ctc/widgets/ctc_modules.dart';
import 'package:cnetp_app/features/ctc/widgets/ctc_read_only_view.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _CtcAdapter implements HttpClientAdapter {
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    final path = options.uri.path;
    final data = path.endsWith('/dashboard/')
        ? {
            'counts': {
              'dossiers': 1,
              'assignations': 0,
              'normes_suivies': 25,
              'taches_en_retard': 0,
            },
            'pole_label': "Bureau d'Appui Technique et Numérique",
            'ctc_sub_role': 'it_sg_itp',
            'sidebar_nav_config': {
              'principal': [
                {'view': 'dashboard', 'label': 'Tableau de bord'},
                {'view': 'dossiers', 'label': 'Dossiers normatifs'},
              ],
              'supervision': [],
              'outils': [],
              'system': [],
            },
          }
        : path.endsWith('/dossiers/')
        ? {
            'results': [
              {
                'reference': 'ARS 1:1986',
                'title': 'Recommandations pour les unités',
                'stage_label': 'Étape 1 — Réception, Numérisation & Cadrage',
              },
            ],
          }
        : path.endsWith('/experts/')
        ? {
            'count': 1,
            'results': [
              {
                'name': 'Expert A',
                'structure': 'CNE-ITP',
                'sc_code': 'SC 1',
                'sc_name': 'Sols',
                'affectation_label': 'Affectation proposée',
              },
            ],
          }
        : path.endsWith('/instructions/')
        ? {
            'general': null,
            'ctms': [
              {'number': 8, 'name': 'CTM réel', 'last_instruction': null},
            ],
          }
        : path.endsWith('/archives/')
        ? {
            'results': [
              {
                'reference': 'A-1',
                'title': 'Norme archivée',
                'status': 'Archivée',
              },
            ],
          }
        : {'results': []};
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
  testWidgets('CTC archive list shows persisted norm status', (tester) async {
    final previous = ApiClient.dio.httpClientAdapter;
    ApiClient.dio.httpClientAdapter = _CtcAdapter();
    addTearDown(() => ApiClient.dio.httpClientAdapter = previous);
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: CtcNormsView(view: 'archives')),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('A-1'), findsOneWidget);
    expect(find.text('Archivée'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('CTC instructions render only the CTMs returned by the server', (
    tester,
  ) async {
    final previous = ApiClient.dio.httpClientAdapter;
    ApiClient.dio.httpClientAdapter = _CtcAdapter();
    addTearDown(() => ApiClient.dio.httpClientAdapter = previous);
    await tester.pumpWidget(
      const MaterialApp(home: Scaffold(body: CtcInstructionsView())),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('Sous-commissions (CTM) · 1'), findsOneWidget);
    expect(find.text('CTM 8'), findsOneWidget);
    expect(find.text('CTM 1'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('CTC expert directory keeps proposed status visible', (
    tester,
  ) async {
    final previous = ApiClient.dio.httpClientAdapter;
    ApiClient.dio.httpClientAdapter = _CtcAdapter();
    addTearDown(() => ApiClient.dio.httpClientAdapter = previous);
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: CtcReadOnlyView(view: 'experts')),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('Expert A'), findsOneWidget);
    expect(find.text('Affectation proposée'), findsOneWidget);
    expect(find.text('Experts enregistrés'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('CTC statistics use server counts and status rows', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: CtcModuleView(
            view: 'statistiques',
            counts: {
              'normes_suivies': 25,
              'sous_commissions': 8,
              'groupes': 38,
              'taches_en_retard': 0,
            },
            dossiers: [],
            stageRows: [
              {'label': 'Brouillon', 'count': 24, 'width': 100},
            ],
            groupNormRows: [
              {'label': 'Sols', 'parent': 'CTM 1', 'count': 2, 'width': 100},
            ],
          ),
        ),
      ),
    );
    expect(find.text('8'), findsOneWidget);
    expect(find.text('38'), findsOneWidget);
    expect(find.text('Brouillon'), findsOneWidget);
    await tester.ensureVisible(find.text('CTM 1 · Sols'));
    expect(find.text('CTM 1 · Sols'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('CTC request review sends the selected decision and comment', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    int? reviewedId;
    String? decision;
    String? comment;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: CtcRequestsView(
            requests: const [
              {
                'id': 7,
                'restricted_resource': 'Accès au dossier CTC',
                'requester': 'Expert A',
                'status_label': 'En attente',
                'reason': 'Pièce urgente.',
              },
            ],
            canReview: true,
            onDecision: (id, value, note) async {
              reviewedId = id;
              decision = value;
              comment = note;
            },
          ),
        ),
      ),
    );
    await tester.tap(find.text('Accès au dossier CTC'));
    await tester.pumpAndSettle();
    expect(find.text('Pièce urgente.'), findsOneWidget);
    await tester.enterText(find.byType(TextField).last, 'Pièce contrôlée.');
    await tester.tap(find.text('Approuver'));
    await tester.pumpAndSettle();
    expect(
      (reviewedId, decision, comment),
      (7, 'APPROVED', 'Pièce contrôlée.'),
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('CTC mobile dossier keeps its title beside a long stage', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final previous = ApiClient.dio.httpClientAdapter;
    ApiClient.dio.httpClientAdapter = _CtcAdapter();
    addTearDown(() => ApiClient.dio.httpClientAdapter = previous);
    await tester.pumpWidget(
      const ProviderScope(child: MaterialApp(home: CtcScreen())),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    await tester.tap(find.byTooltip('Ouvrir le menu'));
    await tester.pumpAndSettle();
    await tester.tap(
      find.descendant(
        of: find.byType(CtcSidebar),
        matching: find.text('Dossiers normatifs'),
      ),
    );
    await tester.pump();
    expect(find.text('ARS 1:1986'), findsOneWidget);
    expect(tester.getSize(find.text('ARS 1:1986')).width, greaterThan(100));
    expect(find.text('Recommandations pour les unités'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  test('CTC navigation follows the server role configuration', () {
    final sections = ctcSectionsFromConfig({
      'principal': [
        {'view': 'dashboard', 'label': 'Tableau de bord'},
        {'view': 'assistant_executif', 'label': 'Assistant Exécutif'},
      ],
      'supervision': [],
      'outils': [],
      'system': [],
    });
    expect(sections.first.items.map((item) => item.view), [
      'dashboard',
      'assistant_executif',
    ]);
    expect(
      sections
          .expand((section) => section.items)
          .any((item) => item.view == 'financial'),
      isFalse,
    );
  });

  testWidgets('CTC top bar accepts an account without display name', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: CtcTopbar(
            poleLabel: 'Coordination',
            userName: '',
            onToggleSidebar: () {},
          ),
        ),
      ),
    );
    expect(tester.takeException(), isNull);
    expect(find.text('?'), findsOneWidget);
  });

  for (final width in [390.0, 1024.0, 1440.0]) {
    testWidgets('CTC dashboard stays usable at ${width.toInt()} pixels', (
      tester,
    ) async {
      tester.view.physicalSize = Size(width, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      var opened = false;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CtcDashboardView(
              poleLabel: "Bureau d'Appui Technique et Numérique",
              subRole: 'it_sg_itp',
              canAdminSystem: true,
              blockedPolitical: true,
              counts: const {
                'dossiers': 1,
                'assignations': 0,
                'normes_suivies': 25,
              },
              dossiers: const [],
              assignations: const [],
              onOpenDossiers: () => opened = true,
            ),
          ),
        ),
      );
      expect(tester.takeException(), isNull);
      expect(find.text('Mon rôle et mes droits'), findsOneWidget);
      expect(find.text('Administration système'), findsOneWidget);
      expect(find.text('Validations politiques bloquées'), findsOneWidget);
      expect(find.text('25'), findsOneWidget);
      await tester.ensureVisible(find.text('Dossiers normatifs'));
      await tester.tap(find.text('Tout voir').last);
      expect(opened, isTrue);
      expect(tester.takeException(), isNull);
    });
  }
}

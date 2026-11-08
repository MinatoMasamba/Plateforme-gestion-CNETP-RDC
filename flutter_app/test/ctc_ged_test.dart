import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cnetp_app/core/api/api_client.dart';
import 'package:cnetp_app/features/ctc/ctc_screen.dart';
import 'package:cnetp_app/features/ctc/widgets/ctc_ged_view.dart';
import 'package:cnetp_app/features/ctc/widgets/ctc_sidebar.dart';
import 'package:cnetp_app/features/ctc/widgets/ctc_topbar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Adapters factice pour l'espace GED du poste 11 (`/api/v1/st/ged/…`).
class _GedAdapter implements HttpClientAdapter {
  bool failSummary = false;
  final List<String> posts = [];
  final List<RequestOptions> reads = [];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    final path = options.uri.path;
    reads.add(options);
    final indexMatches = RegExp(r'/ged/(\d+)/index/$').firstMatch(path);
    final anomalyMatches = RegExp(r'/ged/(\d+)/anomalies/$').firstMatch(path);
    if (indexMatches != null && options.method == 'POST') {
      posts.add('${options.method} $path|${_encoded(options.data)}');
      return _json({'code': 'ARS 1', 'number': 2});
    }
    if (anomalyMatches != null && options.method == 'POST') {
      posts.add('${options.method} $path|${_encoded(options.data)}');
      return _json({});
    }
    if (path.endsWith(codeLookupPath) && options.method == 'GET') {
      return _json({'available': true, 'reference': null, 'author': null});
    }
    if (path.endsWith(gedPath)) {
      if (failSummary) {
        return ResponseBody.fromString(
          '{"detail":"Indisponible"}',
          503,
          headers: {
            Headers.contentTypeHeader: [Headers.jsonContentType],
          },
        );
      }
      final summary = _gedSummary();
      final activity = summary['sc_activity'] as Map;
      if (options.queryParameters['days'] == 7) {
        activity['period_start'] = '2026-10-26';
      }
      if (options.queryParameters['days'] == 90) {
        activity['period_start'] = '2026-08-04';
      }
      return _json(summary);
    }
    if (RegExp(r'/st/ged/11/$').hasMatch(path)) return _json(_queueRow());
    if (path.endsWith(queuePath)) {
      return _json({
        'results': [_queueRow()],
        'total': 1,
      });
    }
    return _json({'results': []});
  }

  @override
  void close({bool force = false}) {}
}

class _MobileCtcAdapter extends _GedAdapter {
  _MobileCtcAdapter();

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    final path = options.uri.path;
    if (path.endsWith('/mobile/ctc/dashboard/')) {
      return _json({
        'counts': {'dossiers': 0, 'assignations': 0},
        'pole_label': 'Pôle 2 — Documentation, codification et PTN',
        'ctc_sub_role': 'st_pole2',
        'st_post_code': 'ST-V3-11',
        'sidebar_nav_config': {
          'principal': [
            {'view': 'dashboard', 'label': 'Tableau de bord'},
            {'view': 'ged', 'label': 'Espace documentaire'},
            {'view': 'ptn', 'label': 'PTN'},
          ],
          'supervision': [],
          'outils': [],
          'system': [
            {'view': 'parametres', 'label': 'Paramètres'},
          ],
        },
      });
    }
    return super.fetch(options, requestStream, cancelFuture);
  }
}

const gedPath = '/st/ged/';
const queuePath = '/st/ged/queue/';
const codeLookupPath = '/st/ged/code-lookup/';

ResponseBody _json(Map<String, dynamic> data) => ResponseBody.fromString(
  jsonEncode(data),
  200,
  headers: {
    Headers.contentTypeHeader: [Headers.jsonContentType],
  },
);

String _encoded(Object? data) {
  if (data is String) return data;
  return jsonEncode(data);
}

Map<String, dynamic> _gedSummary() => {
  'kpis': {
    'ready': 2,
    'blocked': 1,
    'indexed': 3,
    'pending': 1,
    'versions_todo': 1,
    'anomalies': 1,
    'waiting_report': 1,
    'overdue_14': 0,
    'confirmed_period': 1,
    'median_delay_days': 5,
  },
  'statistics': {
    'objective_days': 14,
    'scope': 'calendar_months:6',
    'conformity': {'total': 4, 'reference_unique': 4, 'classified': 4},
  },
  'sc_activity': {
    'period_start': '2026-05-01',
    'period_end': '2026-11-01',
    'buckets': [
      {'label': '01/10'},
      {'label': '08/10'},
      {'label': '15/10'},
    ],
    'results': [
      {
        'code': 'SC 1',
        'tome': 'Tome 1',
        'dossiers': 2,
        'votes': 1,
        'transmitted': 1,
        'reports': 0,
        'overdue': 0,
        'status': 'partielle',
        'name': 'Infrastructures de transport',
        'idle': false,
        'series': [0, 2, 1],
      },
    ],
  },
  'pipeline_upstream': {
    'registered_after_vote': 1,
    'recently_transmitted': 1,
    'awaiting_sc_report': 1,
    'eligible_for_indexation': 2,
    'latest': [
      {
        'reference': 'ARS 5',
        'sc': 'SC 1',
        'title': 'Dossier amont',
        'has_report': true,
      },
    ],
  },
  'pipeline_downstream': {
    'awaiting_post_10': 1,
    'left_p2': 1,
    'returned_after_exam': 1,
    'latest': [
      {
        'reference': 'ARS 1',
        'code': 'ARS 1',
        'version': 2,
        'author': 'CTC',
        'state': 'PENDING',
      },
    ],
  },
  'codes': [
    {
      'id': 5,
      'code': 'ARS 1',
      'norme_id': 2,
      'author': 'CTC',
      'source_reference': 'Rec 001',
    },
  ],
  'recipients': [
    {'id': 3, 'name': 'SC 1', 'title': 'Secrétariat de commission'},
  ],
  'anomalies': [],
  'activity': [],
  'versions_todo': [],
  'results': [],
  'codification_analysis': {
    'rows': [],
    'verified': 1,
    'conflicts': 0,
    'duplicates': 0,
    'missing': 0,
    'inconsistent': 0,
    'format_errors': 0,
  },
  'updated_at': '2026-11-06T10:00:00Z',
  'head': false,
};

Map<String, dynamic> _queueRow() => {
  'id': 11,
  'reference': 'ARS 1:2014',
  'title': "Recommandations d'implantation",
  'norme_id': 2,
  'sc': 'SC 1',
  'tome': 'Tome 1',
  'group': 'GT 3',
  'sender': 'ACGT',
  'vote_date': '2026-10-20',
  'received_at': '2026-10-22',
  'age_days': 3,
  'eligible': true,
  'queue_state': 'READY',
  'blockers': [],
  'files': [
    {'id': 9, 'name': 'dossier_prep.pdf', 'author': 'CTC'},
  ],
  'report': {'name': 'revue_sc.pdf', 'size': 12345, 'url': '/m/revue_sc.pdf'},
  'pv_present': true,
  'latest': {'metadata': {}},
  'base_version_id': 0,
  'next_version': 2,
  'anomalies': [],
};

Future<void> _pumpWorkspace(
  WidgetTester tester, {
  String initialPanel = 'dashboard',
}) async {
  tester.view.physicalSize = const Size(1280, 1400);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(body: CtcGedWorkspace(initialPanel: initialPanel)),
    ),
  );
  await tester.pumpAndSettle(const Duration(milliseconds: 300));
}

void main() {
  testWidgets('Collapsed documentary sidebar fits its 68 pixel rail', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1000, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Align(
            alignment: Alignment.centerLeft,
            child: CtcSidebar(
              activeView: 'espace_p2',
              onSelect: (_) {},
              poleLabel: 'Documentation, codification et PTN',
              userName: 'Gestionnaire GED',
              stPostCode: 'ST-V3-11',
              railEnabled: true,
              isRail: true,
              onRailToggle: () {},
            ),
          ),
        ),
      ),
    );
    expect(tester.getSize(find.byType(CtcSidebar)).width, 68);
    expect(find.byTooltip('Ouvrir le menu'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets('Header menu follows the HTML mobile breakpoint', (tester) async {
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(989, 580);
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: CtcTopbar(
            poleLabel: 'Documentation',
            userName: 'Secrétariat Technique',
            onToggleSidebar: () {},
          ),
        ),
      ),
    );
    expect(find.byTooltip('Ouvrir le menu'), findsNothing);
    tester.view.physicalSize = const Size(390, 844);
    await tester.pumpAndSettle();
    expect(find.byTooltip('Ouvrir le menu'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  late _GedAdapter adapter;
  setUp(() {
    final previous = ApiClient.dio.httpClientAdapter;
    adapter = _GedAdapter();
    ApiClient.dio.httpClientAdapter = adapter;
    addTearDown(() => ApiClient.dio.httpClientAdapter = previous);
  });

  testWidgets('GED dashboard shows the poste 11 KPIs and follow-up cards', (
    tester,
  ) async {
    await _pumpWorkspace(tester);
    expect(find.text('CNE-ITP · Pôle 2 · Poste 11'), findsOneWidget);
    expect(find.text('Admissibles à indexer'), findsOneWidget);
    expect(find.text('Poste 6 · Réceptions du secrétariat'), findsOneWidget);
    expect(find.text('Après indexation · suite du traitement'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Activity legend hides and restores a curve', (tester) async {
    await _pumpWorkspace(tester);
    final legend = find.textContaining('● SC 1');
    expect(legend, findsOneWidget);
    await tester.ensureVisible(legend);
    await tester.tap(legend);
    await tester.pumpAndSettle();
    expect(find.textContaining('○ SC 1'), findsOneWidget);
    await tester.tap(find.textContaining('○ SC 1'));
    await tester.pumpAndSettle();
    expect(find.textContaining('● SC 1'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Touching an activity point shows its recorded count', (
    tester,
  ) async {
    await _pumpWorkspace(tester);
    final chart = find.byWidgetPredicate(
      (widget) =>
          widget is CustomPaint &&
          widget.painter.runtimeType.toString() == '_ActivityPainter',
    );
    expect(chart, findsOneWidget);
    await tester.ensureVisible(chart);
    final rect = tester.getRect(chart);
    await tester.tapAt(Offset(rect.right - 15, rect.top + 105));
    await tester.pump();
    expect(find.textContaining('1 action(s)'), findsOneWidget);
    expect(find.textContaining('SC 1 · Infrastructures'), findsWidgets);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Dashboard fits mobile and changing period requests real data', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      const MaterialApp(home: Scaffold(body: CtcGedWorkspace())),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await tester.tap(find.text('30 jours'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('7 jours').last);
    await tester.pumpAndSettle();
    expect(
      adapter.reads.any(
        (request) =>
            request.uri.path.endsWith(gedPath) &&
            request.queryParameters['days'] == 7,
      ),
      isTrue,
    );
    await tester.scrollUntilVisible(
      find.text('Voir le suivi'),
      500,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Voir le suivi'));
    await tester.pumpAndSettle();
    expect(
      find.text('Aucune version en attente de contrôle documentaire.'),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'Period updates graph dates and retains loaded period on failure',
    (tester) async {
      await _pumpWorkspace(tester);
      await tester.tap(find.text('30 jours'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('90 jours').last);
      await tester.pumpAndSettle();
      expect(find.textContaining('04/08/2026 → 01/11/2026'), findsOneWidget);
      adapter.failSummary = true;
      await tester.tap(find.text('90 jours'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('7 jours').last);
      await tester.pumpAndSettle();
      expect(find.text('90 jours'), findsOneWidget);
      expect(find.textContaining('04/08/2026 → 01/11/2026'), findsOneWidget);
      expect(
        find.textContaining('période précédente conservée'),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('GED work panel lists the queue and opens the fiche', (
    tester,
  ) async {
    await _pumpWorkspace(tester, initialPanel: 'work');
    expect(find.text('ARS 1:2014'), findsOneWidget);
    expect(find.text('À vérifier'), findsWidgets);
    await tester.tap(find.text('ARS 1:2014'));
    await tester.pumpAndSettle();
    expect(find.text("Recommandations d'implantation"), findsWidgets);
    expect(find.text('PV consulté'), findsOneWidget);
    expect(find.text('Indexation documentaire'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'Notification opens its specific dossier through the detail API',
    (tester) async {
      tester.view.physicalSize = const Size(1280, 1400);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CtcGedWorkspace(initialPanel: 'work', initialProcessId: 11),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(
        adapter.reads.any(
          (request) => request.uri.path.endsWith('/st/ged/11/'),
        ),
        true,
      );
      expect(find.text('PV consulté'), findsOneWidget);
      expect(find.text("Recommandations d'implantation"), findsWidgets);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('Confirmed indexation posts code, source and verification', (
    tester,
  ) async {
    await _pumpWorkspace(tester, initialPanel: 'work');
    await tester.tap(find.text('ARS 1:2014'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Pièces vérifiées et lisibles'));
    await tester.tap(find.text('Pièces vérifiées et lisibles'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Confirmer l\u2019indexation'));
    await tester.pumpAndSettle();
    expect(
      adapter.posts.any((entry) => entry.contains('st/ged/11/index/')),
      isTrue,
    );
    expect(adapter.posts.join(' '), contains('"code_id":5'));
    expect(adapter.posts.join(' '), contains('"source_id":9'));
    expect(adapter.posts.join(' '), contains('"verified":true'));
    expect(find.byType(SnackBar), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Ged code lookup explains a free code', (tester) async {
    await _pumpWorkspace(tester, initialPanel: 'codes');
    expect(find.text('Contrôle des codifications'), findsOneWidget);
    await tester.enterText(find.byType(TextField), 'ARS 1');
    await tester.tap(find.text('Vérifier'));
    await tester.pumpAndSettle();
    expect(find.text('Code ARS 1 disponible (non utilisé).'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Anomalies tab lists the panel and its empty state', (
    tester,
  ) async {
    await _pumpWorkspace(tester, initialPanel: 'anomalies');
    expect(find.text('Anomalies documentaires'), findsOneWidget);
    expect(find.text('Aucune anomalie enregistrée.'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('CTC screen routes the ST v3 sidebar to the GED workspace', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1280, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    ApiClient.dio.httpClientAdapter = _MobileCtcAdapter();
    await tester.pumpWidget(
      const ProviderScope(child: MaterialApp(home: CtcScreen())),
    );
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    // Poste ST-V3-11 : la barre latérale espace affiche la nav GED dédiée.
    expect(find.text('Mon rôle et mes droits'), findsNothing);
    expect(find.text('Admissibles à indexer'), findsOneWidget);
    await tester.tap(find.text('Documents GED').first);
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    expect(find.text('CNE-ITP · Pôle 2 · Poste 11'), findsOneWidget);
    expect(
      find.descendant(
        of: find.byType(CtcGedWorkspace),
        matching: find.text('Documents GED'),
      ),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('Report draft survives switching sidebar sections', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1280, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    ApiClient.dio.httpClientAdapter = _MobileCtcAdapter();
    await tester.pumpWidget(
      const ProviderScope(child: MaterialApp(home: CtcScreen())),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Rapports et exports'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Page blanche'));
    await tester.pumpAndSettle();
    final title = find.byWidgetPredicate(
      (w) => w is TextField && w.decoration?.labelText == 'Titre du rapport',
    );
    await tester.enterText(title, 'Mon brouillon conservé');
    await tester.tap(find.text('Tableau de bord'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Rapports et exports').first);
    await tester.pumpAndSettle();
    expect(
      tester.widget<TextField>(title).controller?.text,
      'Mon brouillon conservé',
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('CTC space sidebar collapses to the rail and reopens', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1280, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    ApiClient.dio.httpClientAdapter = _MobileCtcAdapter();
    await tester.pumpWidget(
      const ProviderScope(child: MaterialApp(home: CtcScreen())),
    );
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    expect(find.text('Historique des versions'), findsOneWidget);
    await tester.tap(find.byTooltip('Réduire le menu'));
    await tester.pumpAndSettle();
    expect(find.byTooltip('Ouvrir le menu'), findsWidgets);
    expect(find.text('Historique des versions'), findsNothing);
    await tester.tap(
      find.descendant(
        of: find.byType(CtcSidebar),
        matching: find.byTooltip('Ouvrir le menu'),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Historique des versions'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

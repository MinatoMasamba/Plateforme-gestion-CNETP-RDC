import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:cnetp_app/core/api/api_client.dart';
import 'package:cnetp_app/features/pilotage/console/copil_console_screen.dart';
import 'package:cnetp_app/features/pilotage/organisation/organisation_screen.dart';
import 'package:cnetp_app/features/pilotage/console/widgets/copil_topbar.dart';
import 'package:cnetp_app/features/pilotage/theme/copil_theme.dart';
import 'package:cnetp_app/features/pilotage/directoire/directoire_board_screen.dart';
import 'package:cnetp_app/features/pilotage/organisation/organisation_form_screen.dart';

Widget _wrap(Widget child) => ProviderScope(
  child: MaterialApp(
    theme: ThemeData(fontFamily: 'Inter'),
    home: child,
  ),
);

Future<void> _pumpUntil(WidgetTester tester, bool Function() condition) async {
  for (var attempt = 0; attempt < 120; attempt++) {
    if (condition()) return;
    await Future<void>.delayed(const Duration(milliseconds: 25));
    await tester.pump();
  }
}

Map<String, dynamic> _post(int id, String code, String title, String origin) {
  return {
    'id': id,
    'code': code,
    'title': title,
    'origin': origin,
    'status': 'Proposée',
    'holders': <dynamic>[],
    'proposed_holders': <dynamic>[],
  };
}

class _FakeAdapter implements HttpClientAdapter {
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
    if (path.endsWith('/pilotage/dashboard/')) {
      data = {
        'college': 'directoire',
        'college_label': 'Bureau Directoire',
        'sub_role': 'president',
        'sub_role_label': 'Président',
        'member_count': 0,
        'profile': {
          'full_name': 'Eddy Masamba mpaka-yoka',
          'role': 'Bureau Directoire · Président',
          'structure': 'Université de Kinshasa (UNIKIN)',
          'status': 'Actif',
        },
        'counts': {
          'sous_commissions': 7,
          'experts': 97,
          'a_examiner': 0,
          'normes_travaillees': 25,
        },
        'scs': [
          {
            'code': 'SC-BAT',
            'name': 'Bâtiments Courants & Spéciaux (SC-BAT)',
            'member_count': 26,
            'experts': ['Gradi BANINGIME KEBWIJINA'],
          },
          {
            'code': 'SC-ENV',
            'name': 'Environnement, Santé & Sécurité (SC-ENV)',
            'member_count': 5,
            'experts': ['Guycele Malabi Mpioko'],
          },
        ],
        'pending': {
          'cadrages': 0,
          'reception': 0,
          'adhesions': 0,
          'derogations': 0,
        },
      };
    } else if (path.endsWith('/pilotage/configuration/poste/')) {
      data = options.method == 'POST'
          ? {'id': 1, 'message': 'Informations enregistrées.'}
          : {
              'title': 'Fonction et origine du poste',
              'fields': [
                {
                  'name': 'title',
                  'label': 'Fonction',
                  'type': 'text',
                  'value': 'Président',
                  'required': true,
                  'disabled': false,
                  'help': '',
                },
                {
                  'name': 'status',
                  'label': 'Statut',
                  'type': 'choice',
                  'value': 'PROPOSED',
                  'required': true,
                  'disabled': false,
                  'help': '',
                  'options': [
                    {'value': 'PROPOSED', 'label': 'Proposé'},
                  ],
                },
              ],
            };
    } else if (path.endsWith('/pilotage/directoire/')) {
      data = {
        'profile': {'name': 'Eddy Masamba', 'initials': 'EM'},
        'posts': [
          {
            'n': 1,
            'is_mine': true,
            'title': 'Président du Comité de Pilotage',
            'phase1_title': 'Cadrage stratégique',
            'phase2_title': 'Validation finale & signature',
            'phase3_title': 'Réception du dossier nettoyé par la CTC',
            'reception': [],
            'phases': [
              {'phase': 1, 'items': []},
              {'phase': 2, 'items': []},
            ],
          },
          {
            'n': 2,
            'is_mine': false,
            'title': '1er Vice-Président',
            'phases': [],
          },
        ],
      };
    } else if (path.endsWith('/pilotage/organisation/')) {
      data = {
        'can_manage': true,
        'version': {
          'code': 'reorganisation-2026-10-15',
          'status': 'PROPOSED',
          'status_label': 'Proposée',
          'source_document': 'RAPPORT DE RÉORGANISATION 15-10-2026',
        },
        'counts': {
          'copil_posts': 22,
          'st_posts': 24,
          'subcommissions': 7,
          'experts': 98,
          'pending': 0,
        },
        'copil_groups': [
          {
            'code': 'PRESIDENCY',
            'label': 'Présidence',
            'posts': [
              _post(
                1,
                'COPIL-PRES-01',
                'Président — Ministre des Infrastructures et Travaux Publics',
                'Ministère des ITP',
              ),
              _post(
                2,
                'COPIL-PRES-02',
                '1er Vice-président — Secrétaire général aux ITP',
                'Secrétariat général aux ITP',
              ),
            ],
          },
          {
            'code': 'SECRETARIAT',
            'label': 'Secrétariat',
            'posts': [
              _post(
                3,
                'COPIL-SEC-01',
                'Secrétaire — Directeur DRN',
                'DRN / Secrétariat général aux ITP',
              ),
            ],
          },
        ],
        'st_groups': [
          {
            'code': 'ST',
            'label': 'Coordination',
            'posts': [
              _post(
                10,
                'ST-COORD-01',
                'Coordonnateur — Directeur DRN',
                'DRN / Secrétariat général aux ITP',
              ),
              _post(
                11,
                'ST-COORD-02',
                'Coordonnateur adjoint',
                'Cabinet du Ministre des ITP',
              ),
              _post(12, 'ST-COORD-03', 'Assistant exécutif', 'DRN'),
              _post(13, 'ST-COORD-04', 'Appui administratif', 'DRN'),
            ],
          },
        ],
        'subcommissions': [
          {
            'id': 1,
            'code': 'SC-BAT',
            'official_name': 'Bâtiments Courants & Spéciaux (SC-BAT)',
            'status': 'Validée',
            'domain': 'Bâtiments courants et spéciaux',
            'proposed_bureau_count': 0,
            'migrated_experts': [
              {'name': 'Gradi BANINGIME KEBWIJINA', 'structure': 'UNIKIN'},
            ],
            'posts': [
              _post(
                20,
                'SC-BAT-PRES-01',
                'Président de sous-commission',
                'UNIKIN',
              ),
            ],
            'groups': [
              {
                'code': 'GT-BAT-01',
                'name': 'Béton armé',
                'mission': 'Formulation et contrôle',
                'activity': 'Actif',
                'status': 'Validé',
              },
            ],
          },
        ],
        'pending_experts': <dynamic>[],
        'journal': [
          {
            'created_at': '2026-10-15T10:00:00Z',
            'actor': 'Eddy Masamba',
            'operation': 'Préparation du référentiel',
            'reason': 'Version adoptée',
          },
        ],
      };
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
  setUpAll(() async {
    final loader = FontLoader('Inter')
      ..addFont(rootBundle.load('assets/fonts/Inter.ttf'));
    await loader.load();
  });
  late HttpClientAdapter previous;
  late _FakeAdapter adapter;

  setUp(() {
    previous = ApiClient.dio.httpClientAdapter;
    adapter = _FakeAdapter();
    ApiClient.dio.httpClientAdapter = adapter;
  });

  tearDown(() {
    ApiClient.dio.httpClientAdapter = previous;
  });

  for (final size in const [Size(1440, 900), Size(1024, 768), Size(390, 844)]) {
    testWidgets('COPIL header stays on one line at $size', (tester) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData(fontFamily: 'Inter'),
          home: Scaffold(
            body: CopilTheme(
              palette: CopilPalette.dark,
              child: CopilTopbar(
                memberCount: 7,
                onToggleSidebar: () {},
                onBack: () {},
                onDirectoire: () {},
                onInstructions: () {},
                onAi: () {},
                onThemeToggle: () {},
              ),
            ),
          ),
        ),
      );
      expect(tester.takeException(), isNull);
      final title = tester.getCenter(find.text('PILOTAGE CNE-ITP'));
      final ai = tester.getCenter(find.byTooltip('Assistant IA Pilotage'));
      expect((title.dy - ai.dy).abs(), lessThan(1));
      expect(ai.dx, greaterThan(size.width - 100));
      expect(
        tester.getSize(find.byType(CopilTopbar)).height,
        size.width >= 640 ? 64 : 60,
      );
    });
  }

  testWidgets('Instruction opens the web reference drawer and closes', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.runAsync(() async {
      await tester.pumpWidget(_wrap(const CopilConsoleScreen()));
      await _pumpUntil(
        tester,
        () => find.text('Donner une instruction').evaluate().isNotEmpty,
      );
    });
    await tester.tap(find.text('Donner une instruction'));
    await tester.pumpAndSettle();
    expect(find.text('Non disponible'), findsOneWidget);
    await tester.tap(find.text('Fermer'));
    await tester.pumpAndSettle();
    expect(find.text('Non disponible'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'Directoire matches own functions and exposes organisation navigation',
    (tester) async {
      tester.view.physicalSize = const Size(1440, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.runAsync(() async {
        await tester.pumpWidget(_wrap(const DirectoireBoardScreen()));
        await _pumpUntil(
          tester,
          () =>
              find.text('MES FONCTIONS').evaluate().isNotEmpty &&
              find.text('Eddy Masamba').evaluate().isNotEmpty,
        );
      });
      expect(tester.takeException(), isNull);
      expect(find.text('1er Vice-Président'), findsNothing);
      expect(find.text('Organisation CNE-ITP'), findsOneWidget);
      expect(find.text('Cadrage stratégique'), findsNWidgets(2));
      await tester.tap(find.text('Validation finale & signature'));
      await tester.pump();
      expect(find.text('Validation finale & signature'), findsNWidgets(2));
      expect(find.text('Cadrage stratégique'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  for (final size in const [Size(1440, 900), Size(1024, 768)]) {
    testWidgets('Copil organisation renders at $size', (tester) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);

      await tester.runAsync(() async {
        await tester.pumpWidget(_wrap(const CopilOrganisationScreen()));
        await _pumpUntil(
          tester,
          () =>
              find.text('Comité de Pilotage · 22 postes').evaluate().isNotEmpty,
        );
      });

      expect(tester.takeException(), isNull);
      expect(find.text('Organisation CNE-ITP'), findsOneWidget);
      expect(find.text('Comité de Pilotage · 22 postes'), findsOneWidget);
      expect(find.text('Présidence · 2'), findsOneWidget);
      expect(find.text('Modifier le COPIL'), findsOneWidget);

      expect(find.byIcon(Icons.light_mode_outlined), findsOneWidget);
      await tester.tap(find.byIcon(Icons.light_mode_outlined));
      await tester.pump();
      expect(find.byIcon(Icons.dark_mode_outlined), findsOneWidget);

      await tester.runAsync(() async {
        await tester.tap(find.text('Secrétariat technique').first);
        await tester.pump();
      });

      expect(find.text('Coordination · 4'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('Organisation edits submit the shared form values', (
    tester,
  ) async {
    await tester.runAsync(() async {
      await tester.pumpWidget(
        _wrap(const OrganisationFormScreen(kind: 'poste', id: 1)),
      );
      await _pumpUntil(
        tester,
        () => find.text('Enregistrer').evaluate().isNotEmpty,
      );
    });
    expect(find.text('Président'), findsOneWidget);
    await tester.enterText(find.byType(TextField).first, 'Fonction corrigée');
    await tester.runAsync(() async {
      await tester.tap(find.text('Enregistrer'));
      await _pumpUntil(
        tester,
        () => adapter.requests.any((r) => r.method == 'POST'),
      );
    });
    final request = adapter.requests.lastWhere((r) => r.method == 'POST');
    expect(request.data['title'], 'Fonction corrigée');
    expect(request.data['status'], 'PROPOSED');
    expect(request.queryParameters['id'], 1);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Copil dashboard uses API profile and counts', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.runAsync(() async {
      await tester.pumpWidget(_wrap(const CopilConsoleScreen()));
      await _pumpUntil(
        tester,
        () => find.text('Eddy Masamba mpaka-yoka').evaluate().isNotEmpty,
      );
    });

    expect(tester.takeException(), isNull);
    expect(find.text('Bureau Directoire · Président'), findsOneWidget);
    expect(find.text('Université de Kinshasa (UNIKIN)'), findsOneWidget);
    expect(find.text('97'), findsOneWidget);
    expect(find.text('25'), findsOneWidget);
  });
}

import 'dart:convert';
import 'dart:typed_data';

import 'package:cnetp_app/core/api/api_client.dart';
import 'package:cnetp_app/features/expert/widgets/expert_other_tabs.dart';
import 'package:cnetp_app/features/expert/widgets/expert_theme.dart';
import 'package:cnetp_app/features/expert/expert_screen.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class _Adapter implements HttpClientAdapter {
  final requests = <RequestOptions>[];
  bool leader = true,
      staff = false,
      admitted = false,
      failAdmission = false,
      read = false,
      present = false,
      contested = false;
  String? choice, jetonDecision;
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? stream,
    Future<void>? cancel,
  ) async {
    requests.add(options);
    final path = options.uri.path;
    var code = 200;
    dynamic data = <String, dynamic>{};
    if (path.endsWith('/pending-count-for-my-ctm/')) {
      data = {'is_ctm_leader': leader, 'count': admitted ? 0 : 1};
    } else if (path.endsWith('/pending-for-my-ctm/')) {
      data = admitted
          ? []
          : [
              {
                'id': 8,
                'ctm': 1,
                'ctm_name': 'SC Qualité',
                'user': {
                  'first_name': 'Amina',
                  'last_name': 'Candidate',
                  'email': 'amina@example.test',
                },
                'structure': {'name': 'Structure test'},
              },
            ];
    } else if (path.endsWith('/admit-to-ctm/') || path.endsWith('/reject/')) {
      if (failAdmission) {
        code = 400;
        data = {'detail': 'Demande refusée par le serveur'};
      } else {
        admitted = true;
      }
    } else if (path.endsWith('/wg/')) {
      data = [
        {
          'id': 11,
          'ctm': 1,
          'name': 'WG Qualité',
          'expert_count': 1,
          'expert_list': [
            {'id': 6, 'expert': 7},
          ],
          'latest_norms': [],
          'leadership': {},
        },
      ];
    } else if (path.endsWith('/experts/me/')) {
      data = {'id': 7, 'role_id': staff ? 'COORD_CTC' : 'EXPERT'};
    } else if (path.endsWith('/my-affiliation/')) {
      data = {
        'bureau_ctm_ids': leader ? [1] : [],
        'ctms': [
          {'id': 1, 'name': 'SC Qualité'},
        ],
        'workgroups': [
          {'id': 11, 'ctm_id': 1, 'name': 'WG Qualité'},
        ],
      };
    } else if (path.endsWith('/experts/')) {
      data = [
        {
          'id': 7,
          'user_name': 'Amina Expert',
          'status': 'ACTIVE',
          'structure_name': 'Structure test',
          'specialties': 'Qualité',
        },
      ];
    } else if (path.endsWith('/messages/contacts/')) {
      data = [];
    } else if (path.endsWith('/reunions/')) {
      data = [
        {
          'id': 3,
          'titre': 'Session qualité',
          'date': '2027-01-01T10:00:00Z',
          'ctm': 1,
          'status': 'PLANNED',
        },
      ];
    } else if (path.endsWith('/details/')) {
      data = {
        'id': 3,
        'titre': 'Session qualité',
        'status': 'PLANNED',
        'presences': present
            ? [
                {
                  'id': 6,
                  'expert': 7,
                  'expert_name': 'Amina Expert',
                  'status': 'PRESENT',
                },
              ]
            : [],
        'votes': choice == null
            ? []
            : [
                {'expert': 7, 'expert_name': 'Amina Expert', 'choix': choice},
              ],
        'pv': null,
      };
    } else if (path.endsWith('/checkin_presence/')) {
      present = true;
    } else if (path.endsWith('/vote/')) {
      choice = options.data['choix'];
    } else if (path.endsWith('/notifications/')) {
      data = [
        {
          'id': 4,
          'title': 'Nouvelle norme',
          'body': 'Un texte est disponible',
          'is_read': read,
        },
      ];
    } else if (path.endsWith('/mark_as_read/') ||
        path.endsWith('/mark_all_as_read/')) {
      read = true;
    } else if (path.endsWith('/cotisations/dashboard/')) {
      data = {
        'total_paye': '150.00',
        'total_en_attente': '50.00',
        'percentage_paye': '75',
      };
    } else if (path.endsWith('/cotisations/')) {
      data = [
        {
          'id': 2,
          'structure_name': 'Structure test',
          'annee': 2026,
          'montant': '200',
          'montant_paye': '150',
          'reste_payer': '50',
          'status': 'PARTIAL',
        },
      ];
    } else if (path.endsWith('/paiements/')) {
      data = [
        {
          'id': 12,
          'numero_recu': 'REC-20260101-00012',
          'montant': '75.00',
          'status': 'CONFIRMED',
          'payment_date': '2026-01-01',
        },
      ];
    } else if (path.endsWith('/jetons/')) {
      data = [
        {
          'id': 5,
          'expert': 7,
          'expert_name': 'Amina Expert',
          'montant': '100.00',
          'status': 'PENDING',
          'contestation_status': contested ? 'PENDING' : 'NONE',
          'contestation_motif': contested
              ? 'Montant incorrect pour cette session'
              : '',
          'contestation_resolution': jetonDecision == null
              ? ''
              : 'Décision enregistrée',
        },
      ];
    } else if (path.endsWith('/contest/')) {
      contested = true;
      data = {
        'id': 5,
        'expert': 7,
        'contestation_status': 'PENDING',
        'contestation_motif': options.data['motif'],
      };
    } else if (path.endsWith('/resolve_contestation/')) {
      jetonDecision = options.data['decision'];
      data = {
        'id': 5,
        'expert': 7,
        'contestation_status': jetonDecision,
        'contestation_resolution': options.data['resolution'],
      };
    } else if (path.endsWith('/legistique-workspace/')) {
      data = {
        'can_access': staff,
        'reviews': staff
            ? [
                {
                  'id': 1,
                  'review_id': 9,
                  'code': 'NCD-1',
                  'title': 'Norme qualité',
                  'review_status': 'PENDING',
                  'content': 'Texte à relire',
                },
              ]
            : [],
      };
    } else if (path.endsWith('/workspace/')) {
      data = {
        'steps': [
          {'id': 1, 'title': 'Rédaction'},
          {'id': 2, 'title': 'Validation CTM'},
        ],
        'normes': [
          {
            'id': 1,
            'code': 'NCD-1',
            'title': 'Norme qualité',
            'status_label': 'Rédaction',
            'step': 1,
            'is_public': false,
            'votes': {'percent_for': 80, 'total': 5},
          },
        ],
      };
    }
    return ResponseBody.fromString(
      jsonEncode(data),
      code,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

Widget _wrap(Widget child) => MaterialApp(
  home: ExpertTheme(
    palette: ExpertPalette.dark,
    child: Scaffold(body: child),
  ),
);
Future<void> _flush(WidgetTester tester) async {
  for (var i = 0; i < 8; i++) {
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
    await tester.pump(const Duration(milliseconds: 100));
  }
}

Future<void> _tap(WidgetTester tester, Finder finder) async {
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await _flush(tester);
}

Finder _field(String label) => find.widgetWithText(TextFormField, label);

void main() {
  late HttpClientAdapter previous;
  late _Adapter adapter;
  setUp(() {
    previous = ApiClient.dio.httpClientAdapter;
    adapter = _Adapter();
    ApiClient.dio.httpClientAdapter = adapter;
  });
  tearDown(() => ApiClient.dio.httpClientAdapter = previous);

  testWidgets(
    'bouton adhésions accessible sur mobile sans défilement des onglets',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        const ProviderScope(child: MaterialApp(home: ExpertScreen())),
      );
      await _flush(tester);
      await tester.tap(find.byTooltip('Adhésions des membres'));
      await _flush(tester);
      expect(find.text('Amina Candidate'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'adhésion : choix WG obligatoire, échec conservé, acceptation et rafraîchissement',
    (tester) async {
      var updates = 0;
      await tester.pumpWidget(
        _wrap(ExpertAdhesionsTab(onChanged: () => updates++)),
      );
      await _flush(tester);
      expect(find.text('Amina Candidate'), findsOneWidget);
      await _tap(tester, find.text('Accepter et affecter'));
      await _tap(tester, find.text('Enregistrer'));
      expect(
        adapter.requests.any((r) => r.path.endsWith('/admit-to-ctm/')),
        isFalse,
      );
      await _tap(tester, find.byType(DropdownButtonFormField<String>));
      await _tap(tester, find.text('WG Qualité').last);
      adapter.failAdmission = true;
      await _tap(tester, find.text('Enregistrer'));
      expect(find.byType(AlertDialog), findsOneWidget);
      adapter.failAdmission = false;
      await _tap(tester, find.text('Enregistrer'));
      expect(
        adapter.requests
            .lastWhere((r) => r.path.endsWith('/admit-to-ctm/'))
            .data,
        {'ctm_id': 1, 'wg_id': 11},
      );
      expect(updates, 1);
      expect(
        find.text('Aucune demande d’adhésion en attente.'),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('adhésion : refus motivé envoyé au serveur', (tester) async {
    await tester.pumpWidget(_wrap(const ExpertAdhesionsTab()));
    await _flush(tester);
    await _tap(tester, find.text('Refuser'));
    await tester.enterText(_field('Motif'), 'Dossier incomplet');
    await _tap(tester, find.text('Enregistrer'));
    expect(
      adapter.requests.lastWhere((r) => r.path.endsWith('/reject/')).data,
      {'reason': 'Dossier incomplet'},
    );
  });

  testWidgets('adhésion : actions absentes pour un membre ordinaire', (
    tester,
  ) async {
    adapter.leader = false;
    await tester.pumpWidget(_wrap(const ExpertAdhesionsTab()));
    await _flush(tester);
    expect(find.text('Accepter et affecter'), findsNothing);
    expect(find.textContaining('réservée au bureau'), findsOneWidget);
  });

  testWidgets('annuaire et groupes chargés avec données réelles', (
    tester,
  ) async {
    await tester.pumpWidget(_wrap(const ExpertExpertsTab()));
    await _flush(tester);
    expect(find.text('Amina Expert'), findsOneWidget);
    expect(find.text('Qualité'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('réunion : détail, émargement puis vote connecté', (
    tester,
  ) async {
    await tester.pumpWidget(_wrap(const ExpertMeetingsTab()));
    await _flush(tester);
    await _tap(tester, find.text('Ouvrir : présences, votes et PV'));
    await _flush(tester);
    expect(find.text('Voter POUR'), findsNothing);
    await _tap(tester, find.text('Émarger ma présence'));
    await _tap(tester, find.text('Voter POUR'));
    expect(adapter.requests.lastWhere((r) => r.path.endsWith('/vote/')).data, {
      'choix': 'POUR',
    });
    expect(find.text('Votre vote : POUR'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('finances : chiffres réels et déclaration de paiement', (
    tester,
  ) async {
    await tester.pumpWidget(_wrap(const ExpertFinancialTab()));
    await _flush(tester);
    expect(find.text('Montant perçu : 150.00 USD'), findsOneWidget);
    await _tap(tester, find.text('Déclarer un paiement'));
    await tester.enterText(_field('Montant (USD)'), '50');
    await _tap(tester, find.text('Enregistrer'));
    final request = adapter.requests.lastWhere(
      (r) => r.path == '/api/v1/paiements/' && r.method == 'POST',
    );
    expect(request.data['cotisation'], 2);
    expect(request.data['montant'], '50');
  });

  testWidgets('indemnité : contestation du bénéficiaire', (tester) async {
    await tester.pumpWidget(_wrap(const ExpertFinancialTab()));
    await _flush(tester);
    expect(find.text('Télécharger le reçu PDF'), findsNWidgets(2));
    expect(find.text('Générer le fichier pain.001'), findsNothing);
    await _tap(tester, find.text('Contester l’indemnité'));
    await tester.enterText(
      _field('Motif de la contestation'),
      'Montant incorrect pour cette session',
    );
    await _tap(tester, find.text('Enregistrer'));
    expect(
      adapter.requests.lastWhere((r) => r.path.endsWith('/contest/')).data,
      {'motif': 'Montant incorrect pour cette session'},
    );
    expect(adapter.contested, isTrue);
    expect(
      find.text('Contestation : En attente d’instruction'),
      findsOneWidget,
    );
  });

  testWidgets('indemnité : instruction CTC et mandatement pain.001', (
    tester,
  ) async {
    adapter
      ..staff = true
      ..contested = true;
    await tester.pumpWidget(_wrap(const ExpertFinancialTab()));
    await _flush(tester);
    expect(find.text('Générer le fichier pain.001'), findsOneWidget);
    await _tap(tester, find.text('Instruire la contestation'));
    await _tap(tester, find.byType(DropdownButtonFormField<String>));
    await _tap(tester, find.text('Rejeter la contestation').last);
    await tester.enterText(
      _field('Note d’instruction'),
      'Barème confirmé par le secrétariat',
    );
    await _tap(tester, find.text('Enregistrer'));
    final request = adapter.requests.lastWhere(
      (r) => r.path.endsWith('/resolve_contestation/'),
    );
    expect(request.data, {
      'decision': 'REJECTED',
      'resolution': 'Barème confirmé par le secrétariat',
    });
  });

  testWidgets('notifications : marquage lu et rechargement', (tester) async {
    await tester.pumpWidget(_wrap(const ExpertNotificationsTab()));
    await _flush(tester);
    expect(find.text('● Nouvelle norme'), findsOneWidget);
    await _tap(tester, find.text('Marquer comme lu'));
    expect(find.text('Nouvelle norme'), findsOneWidget);
    expect(find.text('Marquer comme lu'), findsNothing);
  });

  testWidgets('ISO : statut réel et mutation réservée CTC', (tester) async {
    await tester.pumpWidget(_wrap(const ExpertValidationTab()));
    await _flush(tester);
    expect(find.textContaining('80 %'), findsOneWidget);
    expect(find.text('Changer la phase'), findsNothing);
    adapter.staff = true;
    await tester.pumpWidget(const SizedBox());
    await tester.pumpWidget(_wrap(const ExpertValidationTab()));
    await _flush(tester);
    await _tap(tester, find.text('Changer la phase'));
    await _tap(tester, find.byType(DropdownButtonFormField<String>));
    await _tap(tester, find.text('Validation CTM').last);
    await _tap(tester, find.text('Enregistrer'));
    expect(
      adapter.requests.lastWhere((r) => r.path.endsWith('/set-step/')).data,
      {'norme_id': 1, 'step': 2},
    );
  });

  testWidgets('bureau légistique : autorisation serveur et prise en charge', (
    tester,
  ) async {
    await tester.pumpWidget(_wrap(const ExpertLegistiqueTab()));
    await _flush(tester);
    expect(find.text('M’assigner'), findsNothing);
    adapter.staff = true;
    await tester.pumpWidget(const SizedBox());
    await tester.pumpWidget(_wrap(const ExpertLegistiqueTab()));
    await _flush(tester);
    await _tap(tester, find.text('M’assigner'));
    expect(
      adapter.requests.any(
        (r) => r.path.endsWith('/9/assign-self/') && r.method == 'POST',
      ),
      isTrue,
    );
  });
}

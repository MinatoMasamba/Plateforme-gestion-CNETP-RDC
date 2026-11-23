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
import 'package:shared_preferences/shared_preferences.dart';

class _Adapter implements HttpClientAdapter {
  final requests = <RequestOptions>[];
  bool leader = true,
      staff = false,
      admitted = false,
      failAdmission = false,
      read = false,
      present = false,
      meetingClosed = false,
      meetingNotification = false,
      contested = false;
  int messageUnread = 0;
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
    } else if (path.endsWith('/experts/7/')) {
      data = {
        'id': 7,
        'status': 'ACTIVE',
        'user': {
          'id': 12,
          'first_name': 'Amina',
          'last_name': 'Expert',
          'email': 'amina.expert@example.test',
          'phone': '+243 900 000 000',
          'province': 'Kinshasa',
        },
        'structure': {
          'id': 4,
          'name': 'Structure nationale de normalisation',
          'acronym': 'SNN',
          'category': 'Établissement public',
          'contact_person': 'Direction scientifique',
          'email': 'contact@snn.test',
          'phone': '+243 810 000 000',
        },
        'specialties': 'Qualité, normalisation et maquette BIM',
        'inscription_date': '2026-10-12T08:15:00Z',
        'affectations': [
          {
            'ctm_name': 'CTM Qualité',
            'wg_name': 'WG Structures',
            'role': 'Membre CTM / Rapporteur WG',
          },
        ],
        'ctm_name': 'CTM Qualité',
        'appointment_decree_number': 'Arrêté 004/2026',
        'appointment_date': '2026-10-20',
        'profile_update_status': 'COMPLETE',
        'profile_update_submitted_at': '2026-11-01T12:00:00Z',
        'cv': '/media/cv/amina.pdf',
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
    } else if (path.endsWith('/messages/unread_count/')) {
      data = {'unread_count': messageUnread};
    } else if (path.endsWith('/messages/contacts/')) {
      data = [];
    } else if (path.endsWith('/meetings/capabilities/')) {
      data = {
        'can_plan': leader || staff,
        'can_plan_ctm_ids': leader || staff ? [1] : [],
        'ctms': [
          {'id': 1, 'name': 'SC Qualité'},
        ],
        'workgroups': [
          {'id': 11, 'ctm_id': 1, 'name': 'WG Qualité'},
        ],
      };
    } else if (path.endsWith('/reunions/') || path.endsWith('/meetings/')) {
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
        'status': meetingClosed ? 'COMPLETED' : 'PLANNED',
        'question_vote': 'Approuver les conclusions de la séance ?',
        'capabilities': {
          'can_manage': leader || staff,
          'can_validate_pv': staff,
          'can_participate': true,
          'can_checkin': !present,
          'can_vote': present,
        },
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
        'pv': meetingClosed
            ? {
                'id': 4,
                'contenu': 'Compte rendu de la séance',
                'points_discutes': 'Projet examiné',
                'decisions': 'Projet approuvé',
                'redaction': 'BROUILLON',
                'revision': 1,
              }
            : null,
      };
    } else if (path.endsWith('/checkin_presence/')) {
      present = true;
    } else if (path.endsWith('/vote/')) {
      choice = options.data['choix'];
    } else if (path.endsWith('/notifications/')) {
      data = [
        if (meetingNotification)
          {
            'id': 9,
            'title': 'Invitation à une réunion : Session qualité',
            'body': 'Votre séance est planifiée demain.',
            'notification_type': 'REUNION_INVITE',
            'data': {'reunion_id': '3'},
            'is_read': read,
          },
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
    SharedPreferences.setMockInitialValues({});
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
    'navigation PC se replie en rail icônes sans changer les actions',
    (tester) async {
      tester.view.physicalSize = const Size(1440, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(
        const ProviderScope(child: MaterialApp(home: ExpertScreen())),
      );
      await _flush(tester);
      expect(tester.takeException(), isNull, reason: 'Avant réduction');

      expect(
        find.byKey(const ValueKey('expert-desktop-sidebar')),
        findsOneWidget,
      );
      expect(
        tester
            .getSize(find.byKey(const ValueKey('expert-desktop-sidebar')))
            .width,
        280,
      );
      expect(find.text('Historique'), findsOneWidget);
      await tester.tap(find.byTooltip('Réduire le menu'));
      await tester.pumpAndSettle();
      expect(
        tester
            .getSize(find.byKey(const ValueKey('expert-desktop-sidebar')))
            .width,
        68,
      );
      expect(find.text('Historique'), findsNothing);
      expect(find.byTooltip('Historique'), findsOneWidget);
      expect(find.byTooltip('Ouvrir le menu'), findsOneWidget);
      expect(find.byTooltip('Thème'), findsWidgets);
      expect(find.byTooltip('Notifications'), findsWidgets);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets('messagerie flottante affiche le badge non lu sur mobile', (
    tester,
  ) async {
    adapter.messageUnread = 123;
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      const ProviderScope(child: MaterialApp(home: ExpertScreen())),
    );
    await _flush(tester);

    expect(find.text('MESSAGERIE CNE-ITP'), findsNothing);
    expect(find.byTooltip('Messagerie CNE-ITP, 123 non lus'), findsOneWidget);
    expect(find.text('99+'), findsOneWidget);
    expect(
      find.byWidgetPredicate(
        (widget) =>
            widget is Semantics &&
            widget.properties.label == 'Messagerie CNE-ITP, 123 non lus' &&
            widget.properties.button == true &&
            widget.excludeSemantics,
      ),
      findsOneWidget,
    );

    await tester.tap(find.byTooltip('Messagerie CNE-ITP, 123 non lus'));
    await _flush(tester);
    expect(find.text('Centre de communication'), findsOneWidget);
    expect(find.byTooltip('Retour'), findsOneWidget);
    await tester.tap(find.byTooltip('Retour'));
    await _flush(tester);
    expect(find.byTooltip('Messagerie CNE-ITP, 123 non lus'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('création de norme masquée dans le menu mobile', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      const ProviderScope(child: MaterialApp(home: ExpertScreen())),
    );
    await _flush(tester);
    await tester.tap(find.byTooltip('Documents'));
    await _flush(tester);

    expect(find.text('+ Nouveau'), findsNothing);
    expect(find.text('Normes'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

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
    expect(find.text('Actif'), findsOneWidget);
    expect(find.text('Désactiver'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('annuaire : fiche experte complète et navigation retour', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(_wrap(const ExpertExpertsTab()));
    await _flush(tester);
    await _tap(tester, find.text('Voir la fiche'));
    await _flush(tester);

    expect(find.text('Fiche expert'), findsOneWidget);
    expect(find.text('Amina Expert'), findsOneWidget);
    expect(find.text('amina.expert@example.test'), findsOneWidget);
    expect(find.text('Structure nationale de normalisation'), findsWidgets);
    expect(find.text('Qualité, normalisation et maquette BIM'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('WG Structures'),
      300,
      scrollable: find.byType(Scrollable).last,
    );
    expect(find.text('WG Structures'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Arrêté 004/2026'),
      300,
      scrollable: find.byType(Scrollable).last,
    );
    expect(find.text('Arrêté 004/2026'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Curriculum vitæ'),
      300,
      scrollable: find.byType(Scrollable).last,
    );
    expect(find.text('Conforme et vérifié'), findsOneWidget);
    expect(find.text('Curriculum vitæ'), findsOneWidget);
    expect(find.byKey(const ValueKey('expert-profile-back')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('expert-profile-back')));
    await _flush(tester);
    expect(find.text('Experts & Groupes'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('annuaire : désactivation confirmée avant envoi', (tester) async {
    adapter.staff = true;
    await tester.pumpWidget(_wrap(const ExpertExpertsTab()));
    await _flush(tester);
    await _tap(tester, find.text('Désactiver'));
    expect(find.text('Désactiver Amina Expert ?'), findsOneWidget);
    await _tap(tester, find.text('Annuler'));
    expect(
      adapter.requests.any((r) => r.path.endsWith('/deactivate/')),
      isFalse,
    );
    await _tap(tester, find.text('Désactiver'));
    await _tap(tester, find.widgetWithText(FilledButton, 'Désactiver'));
    expect(
      adapter.requests.any((r) => r.path.endsWith('/deactivate/')),
      isTrue,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('réunion : détail, émargement puis vote connecté', (
    tester,
  ) async {
    await tester.pumpWidget(_wrap(const ExpertMeetingsTab()));
    await _flush(tester);
    await _tap(tester, find.text('Toutes'));
    await _tap(tester, find.text('Détails et participation'));
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

  testWidgets('réunions : actions de gestion masquées pour un invité', (
    tester,
  ) async {
    adapter.leader = false;
    await tester.pumpWidget(_wrap(const ExpertMeetingsTab()));
    await _flush(tester);
    expect(find.text('Planifier une session'), findsNothing);
    await _tap(tester, find.text('Toutes'));
    await _tap(tester, find.text('Détails et participation'));
    await _flush(tester);
    for (final label in [
      'Préparer la séance',
      'Clore le scrutin et générer le PV',
      'Rédiger le PV',
      'Valider le PV',
    ]) {
      expect(find.text(label), findsNothing);
    }
    expect(find.byTooltip('Modifier la présence'), findsNothing);
    expect(find.text('Émarger ma présence'), findsOneWidget);
    expect(find.text('Signaler mon absence'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('réunions : PV en lecture seule pour un invité', (tester) async {
    adapter.leader = false;
    adapter.meetingClosed = true;
    await tester.pumpWidget(_wrap(const ExpertMeetingsTab()));
    await _flush(tester);
    await _tap(tester, find.text('Toutes'));
    await _tap(tester, find.text('Détails et participation'));
    await _flush(tester);
    expect(find.text('Compte rendu de la séance'), findsOneWidget);
    expect(find.text('Rédiger le PV'), findsNothing);
    expect(find.text('Valider le PV'), findsNothing);
    expect(find.text('Émarger ma présence'), findsNothing);
    expect(find.text('Voter POUR'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('réunions : semaine vide puis accès à toutes les sessions', (
    tester,
  ) async {
    await tester.pumpWidget(_wrap(const ExpertMeetingsTab()));
    await _flush(tester);
    expect(find.text('Cette semaine'), findsOneWidget);
    expect(find.text('Aujourd’hui'), findsOneWidget);
    expect(find.text('Aucune séance'), findsOneWidget);
    expect(find.text('Aucune réunion prévue cette semaine.'), findsOneWidget);
    await _tap(tester, find.text('Toutes'));
    expect(find.text('1 séance'), findsOneWidget);
    expect(find.text('Session qualité'), findsOneWidget);
    expect(find.byTooltip('Ajouter à mon agenda'), findsOneWidget);
    expect(find.text('2027'), findsOneWidget);
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

  testWidgets('notifications : filtre réunions et ouverture marquée lue', (
    tester,
  ) async {
    adapter.meetingNotification = true;
    String? opened;
    await tester.pumpWidget(
      _wrap(ExpertNotificationsTab(onOpenMeeting: (id) => opened = id)),
    );
    await _flush(tester);
    await _tap(tester, find.text('Réunions'));
    expect(find.text('● Nouvelle norme'), findsNothing);
    expect(
      find.text('● Invitation à une réunion : Session qualité'),
      findsOneWidget,
    );
    await _tap(tester, find.text('Ouvrir la réunion'));
    expect(opened, '3');
    expect(adapter.read, isTrue);
    expect(
      adapter.requests.any(
        (r) => r.path.endsWith('/notifications/9/mark_as_read/'),
      ),
      isTrue,
    );
    expect(tester.takeException(), isNull);
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

import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:cnetp_app/core/api/api_client.dart';
import 'package:cnetp_app/features/expert/widgets/expert_editor_tab.dart';
import 'package:cnetp_app/features/expert/widgets/expert_messaging.dart';
import 'package:cnetp_app/features/expert/widgets/expert_resources.dart';
import 'package:cnetp_app/features/expert/widgets/expert_theme.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _Adapter implements HttpClientAdapter {
  final requests = <RequestOptions>[];
  final messages = <Map<String, dynamic>>[];
  List<Map<String, dynamic>> votes = [];
  bool failSave = false;
  Completer<void>? aiGate;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    dynamic result = <String, dynamic>{};
    final path = options.uri.path;
    var status = 200;
    if (path.endsWith('/experts/me/')) {
      result = {'id': 7};
    } else if (path.endsWith('/contacts/')) {
      result = [
        {'id': 18, 'user_id': 99, 'user_name': 'Alice Expert'},
      ];
    } else if (path.endsWith('/votes/')) {
      result = votes;
    } else if (path.endsWith('/vote/')) {
      votes = [
        {
          'voter': 7,
          'voter_name': 'Expert connecté',
          'vote': options.data['vote'],
        },
      ];
      result = {'promoted_to_ctm': false};
    } else if (path.endsWith('/create_version/')) {
      status = failSave ? 400 : 201;
      result = failSave
          ? {'detail': 'Sauvegarde refusée'}
          : {'content': options.data['content'], 'version_number': 2};
    } else if (path.endsWith('/regulatory-advice/')) {
      if (aiGate != null) await aiGate!.future;
      result = {
        'summary': 'Une correction',
        'applied_text': 'Texte corrigé',
        'edits': [
          {
            'find': 'Texte initial',
            'replace': 'Texte corrigé',
            'reason': 'Précision',
            'applied': true,
          },
        ],
      };
    } else if (path.endsWith('/unread_count/')) {
      result = {'unread_count': 1};
    } else if (path.endsWith('/mark_conversation_as_read/')) {
      result = {'marked_read': 1};
    } else if (path.endsWith('/messages/')) {
      if (options.method == 'POST') {
        result = {
          'id': messages.length + 1,
          'sender': 1,
          'sender_name': 'Moi',
          'content': options.data['content'],
          'timestamp': '2026-10-26T10:00:00Z',
        };
        messages.add(Map<String, dynamic>.from(result as Map));
      } else {
        result = {'results': messages, 'next': null};
      }
    } else if (path.endsWith('/wg/')) {
      result = [
        {
          'id': 3,
          'ctm': 1,
          'name': 'WG Qualité',
          'description': 'Groupe qualité',
        },
      ];
    }
    return ResponseBody.fromString(
      jsonEncode(result),
      status,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

Map<String, dynamic> _doc(int id) => {
  'id': id,
  'title': 'Norme $id',
  'ctm': 1,
  'ctm_name': 'CTM Qualité',
  'reference_number': 'NCD-$id',
  'latest_version': {'content': 'Texte initial'},
};

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

void main() {
  late HttpClientAdapter previous;
  late _Adapter adapter;
  final text = find.byKey(const ValueKey('norm-editor-text'));
  final comment = find.byKey(const ValueKey('norm-editor-comment'));

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    previous = ApiClient.dio.httpClientAdapter;
    adapter = _Adapter();
    ApiClient.dio.httpClientAdapter = adapter;
  });
  tearDown(() => ApiClient.dio.httpClientAdapter = previous);

  Future<void> start(
    WidgetTester tester, {
    Size size = const Size(1400, 1000),
    Map<String, ExpertDraft>? drafts,
    int id = 1,
    VoidCallback? saved,
  }) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      _wrap(
        ExpertEditorTab(
          doc: _doc(id),
          loading: false,
          drafts: drafts,
          onSave: saved ?? () {},
          onOpenProfile: () {},
        ),
      ),
    );
    await _flush(tester);
  }

  for (final width in [390.0, 704.0, 1400.0]) {
    testWidgets(
      'focus élargit le texte et permet de rouvrir les panneaux à $width',
      (tester) async {
        await start(tester, size: Size(width, 1000));
        expect(tester.takeException(), isNull);
        await tester.tap(text);
        await tester.pumpAndSettle();
        expect(find.text('CONSEIL RÉGLEMENTAIRE IA'), findsNothing);
        expect(find.text('SCRUTIN & ÉVALUATION THÉMATIQUE'), findsNothing);
        await _tap(tester, find.text('Afficher IA / partage'));
        expect(find.text('CONSEIL RÉGLEMENTAIRE IA'), findsOneWidget);
        await _tap(tester, find.text('Afficher le scrutin'));
        expect(find.text('SCRUTIN & ÉVALUATION THÉMATIQUE'), findsOneWidget);
        expect(tester.takeException(), isNull);
      },
    );
  }

  testWidgets(
    'sauvegarde réelle avec commentaire et conservation après erreur',
    (tester) async {
      var saved = 0;
      final drafts = <String, ExpertDraft>{};
      await start(tester, drafts: drafts, saved: () => saved++);
      await tester.enterText(text, 'Nouvelle clause');
      await tester.pumpAndSettle();
      await tester.enterText(comment, 'Précision de la clause');
      adapter.failSave = true;
      await _tap(tester, find.text('Sauvegarder la version'));
      expect(saved, 0);
      expect(
        tester.widget<TextField>(text).controller!.text,
        'Nouvelle clause',
      );
      expect(drafts['1']!.comment, 'Précision de la clause');
      adapter.failSave = false;
      await _tap(tester, find.text('Sauvegarder la version'));
      final request = adapter.requests.lastWhere(
        (r) => r.path.endsWith('/create_version/'),
      );
      expect(request.data, {
        'title': 'Norme 1',
        'content': 'Nouvelle clause',
        'comment': 'Précision de la clause',
      });
      expect(saved, 1);
      expect(tester.widget<TextField>(comment).controller!.text, isEmpty);
      expect(drafts['1']!.base, 'Nouvelle clause');
    },
  );

  testWidgets('brouillons indépendants et persistants après démontage', (
    tester,
  ) async {
    final drafts = <String, ExpertDraft>{};
    await start(tester, drafts: drafts);
    await tester.enterText(text, 'Brouillon A');
    await tester.pumpAndSettle();
    await tester.enterText(comment, 'Commentaire A');
    await tester.pumpWidget(
      _wrap(
        ExpertEditorTab(
          doc: _doc(2),
          loading: false,
          drafts: drafts,
          onSave: () {},
          onOpenProfile: () {},
        ),
      ),
    );
    await _flush(tester);
    expect(tester.widget<TextField>(text).controller!.text, 'Texte initial');
    await tester.enterText(text, 'Brouillon B');
    await tester.pumpWidget(const SizedBox());
    await start(tester, drafts: drafts);
    expect(tester.widget<TextField>(text).controller!.text, 'Brouillon A');
    expect(tester.widget<TextField>(comment).controller!.text, 'Commentaire A');
    expect(drafts['2']!.text, 'Brouillon B');
  });

  testWidgets('vote réel et résultats actualisés', (tester) async {
    await start(tester);
    await _tap(tester, find.text('POUR (0)'));
    expect(adapter.requests.lastWhere((r) => r.path.endsWith('/vote/')).data, {
      'vote': 'FOR',
    });
    expect(find.text('POUR (1)'), findsOneWidget);
    expect(find.textContaining('Votre vote : FOR'), findsOneWidget);
  });

  testWidgets('IA applique les corrections puis renseigne le commentaire', (
    tester,
  ) async {
    await start(tester);
    await _tap(tester, find.text('Analyser & optimiser le texte'));
    await _tap(tester, find.text('Appliquer'));
    expect(tester.widget<TextField>(text).controller!.text, 'Texte corrigé');
    expect(
      tester.widget<TextField>(comment).controller!.text,
      contains('Assistant IA'),
    );
  });

  testWidgets('IA obsolète ne remplace pas une nouvelle saisie', (
    tester,
  ) async {
    adapter.aiGate = Completer<void>();
    await start(tester);
    await tester.tap(find.text('Analyser & optimiser le texte'));
    await _flush(tester);
    await tester.enterText(text, 'Saisie plus récente');
    adapter.aiGate!.complete();
    await _flush(tester);
    await _tap(tester, find.text('Afficher IA / partage'));
    final apply = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Appliquer'),
    );
    expect(apply.onPressed, isNull);
    expect(
      tester.widget<TextField>(text).controller!.text,
      'Saisie plus récente',
    );
  });

  testWidgets('réponse IA ignorée après changement de document', (
    tester,
  ) async {
    adapter.aiGate = Completer<void>();
    await start(tester);
    await tester.tap(find.text('Analyser & optimiser le texte'));
    await _flush(tester);
    await tester.pumpWidget(
      _wrap(
        ExpertEditorTab(
          doc: _doc(2),
          loading: false,
          onSave: () {},
          onOpenProfile: () {},
        ),
      ),
    );
    adapter.aiGate!.complete();
    await _flush(tester);
    expect(find.text('Une correction'), findsNothing);
    expect(tester.widget<TextField>(text).controller!.text, 'Texte initial');
  });

  testWidgets('groupes CTM chargés depuis le serveur', (tester) async {
    await start(tester);
    await _tap(tester, find.text('CTM Qualité — Voir groupes'));
    expect(find.text('WG Qualité'), findsOneWidget);
    expect(
      adapter.requests
          .lastWhere((r) => r.path.endsWith('/wg/'))
          .queryParameters['ctm'],
      1,
    );
    await tester.tap(find.text('Fermer'));
    await _flush(tester);
  });

  testWidgets('ressources locales persistantes et isolées par compte', (
    tester,
  ) async {
    await tester.pumpWidget(
      _wrap(
        const SingleChildScrollView(
          child: ExpertResources(documentId: '1', userScope: 'alice'),
        ),
      ),
    );
    await _flush(tester);
    await _tap(tester, find.text('Ressources connexes & espace collaboratif'));
    Finder field(String label) => find.byWidgetPredicate(
      (w) => w is TextField && w.decoration?.labelText == label,
    );
    await tester.enterText(
      field('Google Drive'),
      'https://drive.google.com/drive/folders/test',
    );
    await _tap(tester, find.text('Enregistrer les liens localement'));
    await tester.pumpWidget(const SizedBox());
    await tester.pumpWidget(
      _wrap(
        const SingleChildScrollView(
          child: ExpertResources(documentId: '1', userScope: 'alice'),
        ),
      ),
    );
    await _flush(tester);
    await _tap(tester, find.text('Ressources connexes & espace collaboratif'));
    expect(
      tester.widget<TextField>(field('Google Drive')).controller!.text,
      contains('/folders/test'),
    );
    await tester.pumpWidget(const SizedBox());
    await tester.pumpWidget(
      _wrap(
        const SingleChildScrollView(
          child: ExpertResources(documentId: '1', userScope: 'bob'),
        ),
      ),
    );
    await _flush(tester);
    await _tap(tester, find.text('Ressources connexes & espace collaboratif'));
    expect(
      tester.widget<TextField>(field('Google Drive')).controller!.text,
      isEmpty,
    );
  });

  testWidgets(
    'sélection partagée avec user_id puis ouverture et réponse dans le chat',
    (tester) async {
      await start(tester);
      tester.widget<TextField>(text).controller!.selection =
          const TextSelection(baseOffset: 0, extentOffset: 5);
      await tester.pump();
      final excerpt = find.byKey(const ValueKey('norm-share-excerpt'));
      expect(tester.widget<TextField>(excerpt).controller!.text, 'Texte');
      await _tap(tester, find.byType(DropdownButtonFormField<String>));
      await _tap(tester, find.text('Alice Expert').last);
      await _tap(tester, find.text('Partager à l’expert & Ouvrir le Chat'));
      final share = adapter.requests.firstWhere(
        (r) => r.path == '/api/v1/messages/' && r.method == 'POST',
      );
      expect(share.data['receiver_id'], 99);
      expect(share.data['clause_excerpt'], 'Texte');
      expect(share.data['clause_code'], 'NCD-1');
      expect(find.byType(ExpertMessaging), findsOneWidget);
      expect(
        adapter.requests.any(
          (r) =>
              r.path.endsWith('/mark_conversation_as_read/') &&
              r.data['participant_id'] == 99,
        ),
        isTrue,
      );
      final input = find.descendant(
        of: find.byType(ExpertMessaging),
        matching: find.byType(TextField),
      );
      await tester.enterText(input, 'Merci pour cette clause');
      await tester.tap(find.byTooltip('Envoyer'));
      await _flush(tester);
      expect(adapter.messages.last['content'], 'Merci pour cette clause');
      await tester.tap(find.byTooltip('Fermer'));
      await _flush(tester);
      expect(tester.takeException(), isNull);
    },
  );
}

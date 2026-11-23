import 'dart:convert';
import 'dart:typed_data';

import 'package:cnetp_app/core/api/api_client.dart';
import 'package:cnetp_app/features/expert/widgets/expert_assistant.dart';
import 'package:cnetp_app/features/expert/widgets/expert_messaging.dart';
import 'package:cnetp_app/features/expert/widgets/expert_theme.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _CommunicationAdapter implements HttpClientAdapter {
  final requests = <RequestOptions>[];
  final contact = <String, dynamic>{
    'id': 21,
    'user_id': 21,
    'user_name': 'Jean Kaba',
    'structure_name': 'Université de Kinshasa',
    'ctm_name': 'CTM Bâtiment',
    'specialties': 'Structures',
    'unread_count': 2,
    'last_message': {
      'id': 2,
      'content': 'Merci, je regarde.',
      'sender': 21,
      'timestamp': '2026-11-22T14:35:00Z',
      'is_read': false,
      'is_clause_share': true,
      'clause_code': 'NCD-42',
      'clause_excerpt': 'Le béton doit être contrôlé avant coulage.',
    },
  };

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? stream,
    Future<void>? cancel,
  ) async {
    requests.add(options);
    final path = options.uri.path;
    dynamic data = <String, dynamic>{};
    if (path.endsWith('/messages/conversations/')) {
      data = [contact];
    } else if (path.endsWith('/messages/') &&
        options.method.toUpperCase() == 'GET') {
      data = {
        'results': [
          {
            'id': 1,
            'sender': 21,
            'sender_name': 'Jean Kaba',
            'content': 'Clause de référence',
            'timestamp': '2026-11-22T14:30:00Z',
            'is_read': true,
            'is_clause_share': true,
            'clause_code': 'NCD-42',
            'clause_excerpt': 'Le béton doit être contrôlé avant coulage.',
          },
          {
            'id': 2,
            'sender': 7,
            'sender_name': 'Amina Expert',
            'content': 'Merci, je regarde.',
            'timestamp': '2026-11-22T14:35:00Z',
            'is_read': true,
            'status': 'read',
          },
        ],
        'next': null,
      };
    } else if (path.endsWith('/mark_conversation_as_read/')) {
      data = {'marked_read': 1};
    } else if (path.endsWith('/ia-agent/sessions/') &&
        options.method.toUpperCase() == 'GET') {
      data = [];
    } else if (path.endsWith('/ia-agent/sessions/') &&
        options.method.toUpperCase() == 'POST') {
      data = {
        'id': 42,
        'scope': 'expert',
        'title': options.data['title'],
        'provider': 'deepseek',
      };
    } else if (path.endsWith('/ia-agent/sessions/42/init/')) {
      data = {
        'assistant_message': {
          'id': 1,
          'role': 'assistant',
          'content': 'Bonjour.',
        },
        'artifacts': [],
      };
    } else if (path.endsWith('/ia-agent/sessions/42/send/')) {
      data = {
        'assistant_message': {
          'id': 2,
          'role': 'assistant',
          'content':
              '**Analyse terminée.** Vérifiez la conformité avant usage.',
        },
        'artifacts': [
          {
            'id': 8,
            'session': 42,
            'artifact_type': 'WG_REQUEST',
            'title': 'Demande au WG Structures',
            'status': 'DRAFT',
            'payload': {
              'description': 'Une demande de revue technique a été préparée.',
            },
          },
        ],
      };
    } else if (path.endsWith('/ia-agent/artifacts/')) {
      data = [];
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

Widget _wrap(Widget child) => MaterialApp(
  home: ExpertPageTheme(palette: ExpertPalette.dark, child: child),
);

Future<void> _flush(WidgetTester tester) async {
  for (var index = 0; index < 10; index++) {
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
    await tester.pump(const Duration(milliseconds: 100));
  }
}

void main() {
  late HttpClientAdapter previous;
  late _CommunicationAdapter adapter;

  setUp(() {
    previous = ApiClient.dio.httpClientAdapter;
    adapter = _CommunicationAdapter();
    ApiClient.dio.httpClientAdapter = adapter;
  });

  tearDown(() => ApiClient.dio.httpClientAdapter = previous);

  testWidgets('centre mobile affiche inbox, clause et assistant', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      _wrap(const Scaffold(body: ExpertCommunicationCenter())),
    );
    await _flush(tester);

    expect(find.text('Centre de communication'), findsOneWidget);
    expect(find.text('Boîte de réception'), findsOneWidget);
    expect(
      find.byKey(const ValueKey('communication-content-frame')),
      findsNothing,
    );
    expect(find.text('Jean Kaba'), findsOneWidget);
    expect(find.text('Échanges internes CNE-ITP'), findsOneWidget);

    await tester.tap(find.text('Jean Kaba'));
    await _flush(tester);
    expect(find.text('Clause NCD-42'), findsOneWidget);
    expect(find.text('Lu'), findsOneWidget);
    expect(find.byTooltip('Boîte de réception'), findsOneWidget);

    await tester.tap(find.text('Assistant IA'));
    await _flush(tester);
    expect(find.text('Bonjour, comment puis-je vous aider ?'), findsOneWidget);
    expect(find.text('Résumer la norme ouverte'), findsOneWidget);
    expect(
      find.text('Réponses générées par IA — à vérifier avant usage officiel'),
      findsOneWidget,
    );

    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
  });

  for (final dimensions in [
    (width: 1024.0, frame: 1024.0, inbox: 300.0, history: 260.0),
    (width: 1440.0, frame: 1280.0, inbox: 360.0, history: 300.0),
  ]) {
    testWidgets('proportions PC équilibrées à ${dimensions.width.toInt()} px', (
      tester,
    ) async {
      tester.view.physicalSize = Size(dimensions.width, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(
        _wrap(const Scaffold(body: ExpertCommunicationCenter())),
      );
      await _flush(tester);

      expect(
        tester
            .getSize(find.byKey(const ValueKey('communication-tabs-desktop')))
            .width,
        440,
      );
      expect(
        tester
            .getSize(find.byKey(const ValueKey('communication-content-frame')))
            .width,
        dimensions.frame,
      );
      expect(
        tester.getSize(find.byKey(const ValueKey('communication-inbox'))).width,
        dimensions.inbox,
      );

      await tester.tap(find.text('Assistant IA'));
      await _flush(tester);
      expect(
        tester
            .getSize(find.byKey(const ValueKey('assistant-desktop-frame')))
            .width,
        dimensions.frame,
      );
      expect(
        tester.getSize(find.byKey(const ValueKey('assistant-history'))).width,
        dimensions.history,
      );
      expect(tester.takeException(), isNull);

      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump();
    });
  }

  testWidgets('assistant joint le contexte de norme et affiche un artefact', (
    tester,
  ) async {
    await tester.pumpWidget(
      _wrap(
        const Scaffold(
          body: ExpertAssistant(
            norm: {
              'reference_number': 'NCD-42',
              'title': 'Béton de structures',
            },
          ),
        ),
      ),
    );
    await _flush(tester);

    expect(find.text('NCD-42'), findsOneWidget);
    await tester.ensureVisible(find.text('Résumer la norme ouverte'));
    await tester.tap(find.text('Résumer la norme ouverte'));
    await _flush(tester);

    final sent = adapter.requests.lastWhere(
      (request) => request.uri.path.endsWith('/sessions/42/send/'),
    );
    expect(
      sent.data['content'],
      startsWith('Contexte de la norme ouverte : NCD-42 — Béton de structures'),
    );
    expect(find.textContaining('Analyse terminée.'), findsOneWidget);
    expect(find.text('Demande au WG Structures'), findsOneWidget);
    expect(find.text('Télécharger PDF'), findsOneWidget);

    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
  });
}

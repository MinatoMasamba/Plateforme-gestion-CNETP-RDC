import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:cnetp_app/features/ctc/widgets/ctc_notifications.dart';
import 'package:cnetp_app/features/ctc/widgets/ctc_topbar.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _NotificationsAdapter implements HttpClientAdapter {
  final read = <String>{};
  bool rejectRead = false;
  Completer<void>? gate;
  int posts = 0;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? stream,
    Future<void>? cancelFuture,
  ) async {
    if (options.method == 'POST') {
      posts++;
      if (gate != null) await gate!.future;
      if (rejectRead) return ResponseBody.fromString('{}', 403);
      read.add((options.data as Map)['key'] as String);
    }
    return ResponseBody.fromString(
      jsonEncode({
        'unread_count': 2 - read.length,
        'results': [
          for (final code in ['A', 'B'])
            {
              'key': code,
              'title': 'Dossier $code à compléter',
              'body': 'Rapport SC attendu pour le dossier $code.',
              'category': 'Documentation',
              'date': '2026-11-08T10:00:00Z',
              'is_read': read.contains(code),
              'target': 'indexation',
              'process_id': 42,
            },
        ],
      }),
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
  late _NotificationsAdapter adapter;
  late CtcNotifications controller;
  setUp(() {
    adapter = _NotificationsAdapter();
    controller = CtcNotifications(client: Dio()..httpClientAdapter = adapter);
  });
  tearDown(() => controller.dispose());

  test(
    'Read count changes only after server acknowledgment and survives reload',
    () async {
      await controller.load();
      expect(controller.unread, 2);
      adapter.gate = Completer<void>();
      final opening = controller.open(controller.rows.first);
      await Future<void>.delayed(Duration.zero);
      expect(controller.unread, 2);
      adapter.gate!.complete();
      await opening;
      expect(controller.unread, 1);
      expect(controller.selected?['is_read'], true);
      await controller.load();
      expect(controller.unread, 1);
      await controller.open(controller.rows.first);
      expect(adapter.posts, 1);
    },
  );

  test('Failed read keeps notification unread', () async {
    await controller.load();
    adapter.rejectRead = true;
    await controller.open(controller.rows.first);
    expect(controller.unread, 2);
    expect(controller.selected, isNull);
    expect(controller.error, isNotNull);
  });

  for (final width in [390.0, 1280.0]) {
    testWidgets('Notification details and dossier link work at $width pixels', (
      tester,
    ) async {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = Size(width, 1000);
      addTearDown(tester.view.reset);
      await tester.runAsync(controller.load);
      Map<String, dynamic>? opened;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CtcNotificationsView(
              controller: controller,
              onOpenDossier: (row) => opened = row,
            ),
          ),
        ),
      );
      await tester.tap(find.text('Dossier A à compléter'));
      await tester.pumpAndSettle();
      expect(controller.unread, 1);
      expect(find.text('Lue'), findsOneWidget);
      expect(
        find.text('Rapport SC attendu pour le dossier A.'),
        findsOneWidget,
      );
      await tester.tap(find.text('Ouvrir le dossier concerné'));
      expect(opened?['process_id'], 42);
      await tester.tap(find.text('Toutes les notifications'));
      await tester.pumpAndSettle();
      expect(find.text('0'), findsOneWidget);
      await tester.tap(find.text('Non lues'));
      await tester.pumpAndSettle();
      expect(find.text('Dossier A à compléter'), findsNothing);
      expect(find.text('Dossier B à compléter'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('Bell remains available on mobile and displays unread count', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(390, 844);
    addTearDown(tester.view.reset);
    var opened = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: CtcTopbar(
            poleLabel: 'Documentation',
            userName: 'Secrétariat Technique',
            onToggleSidebar: () {},
            unreadNotifications: 2,
            onNotifications: () => opened = true,
          ),
        ),
      ),
    );
    expect(find.text('2'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('ctc-notifications-button')));
    expect(opened, true);
    expect(tester.takeException(), isNull);
  });
}

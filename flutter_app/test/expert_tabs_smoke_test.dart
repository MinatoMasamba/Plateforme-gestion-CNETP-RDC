import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:cnetp_app/features/expert/expert_screen.dart';

Widget _wrap(Widget child) => ProviderScope(child: MaterialApp(home: child));

void main() {
  for (final size in const [Size(1440, 900), Size(1024, 768)]) {
    for (var tab = 0; tab < 9; tab++) {
      testWidgets('Expert tab $tab renders at $size', (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1.0;
        addTearDown(tester.view.reset);

        await tester.runAsync(() async {
          await tester.pumpWidget(
            _wrap(
              ExpertScreen(key: ValueKey('expert-$tab-$size'), initialTab: tab),
            ),
          );
          await tester.pump();
          await tester.pump(const Duration(milliseconds: 100));
        });

        expect(tester.takeException(), isNull);
      });
    }
  }
}

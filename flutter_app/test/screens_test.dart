import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:cnetp_app/features/auth/login_screen.dart';
import 'package:cnetp_app/features/home/home_screen.dart';
import 'package:cnetp_app/features/pilotage/console/copil_console_screen.dart';
import 'package:cnetp_app/features/pilotage/directoire/directoire_screen.dart';
import 'package:cnetp_app/features/ctc/ctc_screen.dart';
import 'package:cnetp_app/features/expert/expert_screen.dart';

Widget _wrap(Widget child) => ProviderScope(child: MaterialApp(home: child));

Future<void> _setSize(WidgetTester tester) async {
  tester.view.physicalSize = const Size(1440, 900);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);
}

void main() {
  testWidgets('Home renders', (tester) async {
    await _setSize(tester);
    await tester.pumpWidget(_wrap(const HomeScreen()));
    await tester.pump();
    expect(find.text('Le portail national des normes techniques'), findsOneWidget);
  });

  testWidgets('Login renders', (tester) async {
    await _setSize(tester);
    await tester.pumpWidget(_wrap(const LoginScreen()));
    await tester.pump();
    expect(find.text('Espace Expert'), findsOneWidget);
    expect(find.text('Se connecter'), findsWidgets);
  });

  testWidgets('Copil console renders', (tester) async {
    await _setSize(tester);
    await tester.runAsync(() async {
      await tester.pumpWidget(_wrap(const CopilConsoleScreen()));
      await tester.pump();
    });
    expect(find.text('PILOTAGE CNE-ITP'), findsWidgets);
    expect(find.text('Tableau de bord'), findsOneWidget);
  });

  testWidgets('Directoire renders', (tester) async {
    await _setSize(tester);
    await tester.pumpWidget(_wrap(const DirectoireScreen()));
    await tester.pump();
    expect(find.text('Bureau Directoire'), findsWidgets);
  });

  testWidgets('Conseillers renders', (tester) async {
    await _setSize(tester);
    await tester.pumpWidget(_wrap(const DirectoireScreen(conseillers: true)));
    await tester.pump();
    expect(find.text('Conseillers Institutionnels'), findsWidgets);
  });

  testWidgets('CTC renders', (tester) async {
    await _setSize(tester);
    await tester.runAsync(() async {
      await tester.pumpWidget(_wrap(const CtcScreen()));
      await tester.pump();
    });
    expect(find.text('Coordination du Secrétariat technique'), findsOneWidget);
    expect(find.text('Tableau de bord'), findsWidgets);
  });

  testWidgets('Expert renders', (tester) async {
    await _setSize(tester);
    await tester.runAsync(() async {
      await tester.pumpWidget(_wrap(const ExpertScreen()));
      await tester.pump();
    });
    expect(find.text('ESPACE DE TRAVAIL'), findsOneWidget);
  });
}

import 'package:cnetp_app/core/routing/app_router.dart';
import 'package:cnetp_app/features/auth/login_screen.dart';
import 'package:cnetp_app/main.dart';
import 'package:cnetp_app/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

void main() {
  testWidgets('la bande tricolore commence sous la barre système Android', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 900);
    tester.view.devicePixelRatio = 1;
    tester.view.padding = const FakeViewPadding(top: 28);
    tester.view.viewPadding = const FakeViewPadding(top: 28);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.view.resetPadding);
    addTearDown(tester.view.resetViewPadding);
    final router = GoRouter(
      routes: [GoRoute(path: '/', builder: (_, _) => const LoginScreen())],
    );
    addTearDown(router.dispose);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [routerProvider.overrideWithValue(router)],
        child: const CnetpApp(),
      ),
    );
    await tester.pumpAndSettle();
    final blue = find.byWidgetPredicate(
      (widget) => widget is ColoredBox && widget.color == AppColors.brand500,
    );
    expect(blue, findsOneWidget);
    expect(tester.getTopLeft(blue).dy, 28);
    expect(tester.takeException(), isNull);
  });
}

import 'package:cnetp_app/core/auth/auth_controller.dart';
import 'package:cnetp_app/core/auth/session.dart';
import 'package:cnetp_app/core/routing/workspace_access.dart';
import 'package:cnetp_app/features/auth/application_choice_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

const ctcSession = Session(
  access: 'test',
  refresh: 'test-refresh',
  userId: 1,
  email: 'ctc@example.test',
  fullName: 'Coordination',
  userType: 'expert',
  space: 'ctc',
  isCtc: true,
);

class _AuthForTest extends AuthController {
  _AuthForTest(Session? session)
    : super(initialState: const AuthState(status: AuthStatus.unauthenticated)) {
    if (session != null) {
      state = AuthState(status: AuthStatus.authenticated, session: session);
    }
  }
}

void main() {
  test('les autres espaces ouvrent le choix sans revenir à l’accueil', () {
    expect(spacePath('expert'), '/expert');
    for (final space in ['ctc', 'pilotage', 'pilotage_directoire', 'public']) {
      expect(spacePath(space), '/choisir-application');
    }
  });

  for (final width in [390.0, 1280.0]) {
    for (final coordination in [false, true]) {
      testWidgets(
        'choix ${coordination ? 'Coordination' : 'Expert'} à $width',
        (tester) async {
          tester.view.physicalSize = Size(width, 1000);
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetDevicePixelRatio);
          final router = GoRouter(
            initialLocation: '/choix',
            routes: [
              GoRoute(
                path: '/choix',
                builder: (_, _) => const ApplicationChoiceScreen(),
              ),
              GoRoute(
                path: '/expert',
                builder: (_, _) => const Scaffold(body: Text('Expert ouvert')),
              ),
              GoRoute(
                path: '/ctc',
                builder: (_, _) =>
                    const Scaffold(body: Text('Coordination ouverte')),
              ),
            ],
          );
          addTearDown(router.dispose);
          await tester.pumpWidget(
            ProviderScope(
              overrides: [
                authControllerProvider.overrideWith(
                  (ref) => _AuthForTest(ctcSession),
                ),
              ],
              child: MaterialApp.router(routerConfig: router),
            ),
          );
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          final label = coordination
              ? 'Passer à la Coordination'
              : 'Passer à l’application Expert';
          await tester.ensureVisible(find.text(label));
          await tester.tap(find.text(label));
          await tester.pumpAndSettle();
          expect(
            find.text(coordination ? 'Coordination ouverte' : 'Expert ouvert'),
            findsOneWidget,
          );
        },
      );
    }
  }

  for (final role in ['expert', 'admin', 'pilotage']) {
    testWidgets('$role sans habilitation ne voit pas le bouton CTC', (
      tester,
    ) async {
      final session = Session(
        access: 'test',
        refresh: 'test-refresh',
        userId: 1,
        email: 'account@example.test',
        fullName: 'Compte',
        userType: role,
        space: role == 'admin' ? 'public' : role,
      );
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authControllerProvider.overrideWith((ref) => _AuthForTest(session)),
          ],
          child: const MaterialApp(home: ApplicationChoiceScreen()),
        ),
      );
      expect(find.text('Passer à la Coordination'), findsNothing);
      expect(find.text('Passer à l’application Expert'), findsOneWidget);
    });
  }

  for (final allowed in [false, true]) {
    testWidgets('lien direct CTC : habilitation serveur $allowed', (
      tester,
    ) async {
      final session = Session(
        access: 'test',
        refresh: 'test-refresh',
        userId: 1,
        email: 'expert@example.test',
        fullName: 'Expert',
        userType: 'expert',
        space: allowed ? 'ctc' : 'expert',
        // Un mandat ST peut autoriser l'accès sans adhésion CTC historique.
        isCtc: false,
        canAccessCoordination: allowed,
      );
      var coordinationOpened = 0;
      final router = GoRouter(
        initialLocation: '/expert',
        // Même politique que le routeur principal, sans dépendre des modules UI.
        redirect: (_, state) =>
            coordinationAccessRedirect(session, state.matchedLocation),
        routes: [
          GoRoute(
            path: '/expert',
            builder: (_, _) => const Scaffold(body: Text('Expert')),
          ),
          GoRoute(
            path: '/choisir-application',
            builder: (_, _) => const Scaffold(body: Text('Choix')),
          ),
          GoRoute(
            path: '/ctc',
            builder: (_, _) {
              coordinationOpened++;
              return const Scaffold(body: Text('Coordination'));
            },
          ),
        ],
      );
      addTearDown(router.dispose);
      await tester.pumpWidget(MaterialApp.router(routerConfig: router));
      router.go('/ctc');
      await tester.pumpAndSettle();
      expect(
        router.routeInformationProvider.value.uri.path,
        allowed ? '/ctc' : '/expert',
      );
      expect(coordinationOpened > 0, allowed);
      if (!allowed) {
        router.go('/choisir-application');
        await tester.pumpAndSettle();
        expect(router.routeInformationProvider.value.uri.path, '/expert');
      }
      await tester.pumpWidget(const SizedBox.shrink());
    });
  }

  test('capacité explicite conservée et refus prioritaire sur le rôle', () {
    final data = ctcSession.toJson();
    expect(Session.fromJson(data).canAccessCoordination, isTrue);
    expect(
      Session.fromJson({
        ...data,
        'canAccessCoordination': false,
      }).canAccessCoordination,
      isFalse,
    );
    data.remove('canAccessCoordination');
    expect(Session.fromJson(data).canAccessCoordination, isTrue);
  });
}

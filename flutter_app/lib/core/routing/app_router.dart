import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../auth/auth_controller.dart';
import '../../features/home/home_screen.dart';
import '../../features/auth/login_screen.dart';
import '../../features/auth/password_reset_screen.dart';
import '../../features/auth/registration_screen.dart';
import '../../features/splash/splash_screen.dart';
import '../../features/pilotage/console/copil_console_screen.dart';
import '../../features/pilotage/directoire/directoire_screen.dart';
import '../../features/pilotage/directoire/directoire_board_screen.dart';
import '../../features/pilotage/organisation/organisation_screen.dart';
import '../../features/ctc/ctc_screen.dart';
import '../../features/expert/expert_screen.dart';

String spacePath(String space) {
  switch (space) {
    case 'pilotage_directoire':
      return '/pilotage/directoire';
    case 'pilotage_conseillers':
      return '/pilotage/conseillers';
    case 'pilotage_atf':
      return '/pilotage/atf';
    case 'pilotage':
      return '/pilotage';
    case 'ctc':
      return '/ctc';
    case 'expert':
      return '/expert';
    default:
      return '/';
  }
}

const _protected = <String>{
  '/pilotage',
  '/pilotage/directoire',
  '/pilotage/conseillers',
  '/pilotage/atf',
  '/pilotage/organisation',
  '/ctc',
  '/expert',
};

class _AuthRefresh extends ChangeNotifier {
  _AuthRefresh(Ref ref) {
    ref.listen(authControllerProvider, (_, _) => notifyListeners());
  }
}

final routerProvider = Provider<GoRouter>((ref) {
  final refresh = _AuthRefresh(ref);
  ref.onDispose(refresh.dispose);

  return GoRouter(
    initialLocation: '/',
    refreshListenable: refresh,
    redirect: (context, state) {
      final auth = ref.read(authControllerProvider);
      final loc = state.matchedLocation;
      final loggedIn = auth.status == AuthStatus.authenticated;

      // 1) Session en cours de restauration : on attend avant d'appliquer
      //    les règles d'accès (évite la redirection parasite vers /login).
      if (auth.status == AuthStatus.unknown) {
        if (_protected.contains(loc)) {
          final to = Uri.encodeComponent(state.uri.toString());
          return '/splash?to=$to';
        }
        return null; // routes publiques (/, /login)
      }

      // 2) Authentifié : /splash et /login redirigent vers l'espace.
      if (loggedIn) {
        if (loc == '/splash') {
          final to = state.uri.queryParameters['to'];
          if (to != null && to.isNotEmpty) return to;
          return spacePath(auth.session?.space ?? 'public');
        }
        if (loc == '/login') {
          return spacePath(auth.session?.space ?? 'public');
        }
        return null;
      }

      // 3) Non authentifié.
      if (loc == '/splash' || _protected.contains(loc)) return '/login';
      return null;
    },
    routes: [
      GoRoute(path: '/', builder: (_, _) => const HomeScreen()),
      GoRoute(path: '/login', builder: (_, _) => const LoginScreen()),
      GoRoute(
        path: '/candidature',
        builder: (_, _) => const RegistrationScreen(),
      ),
      GoRoute(
        path: '/mot-de-passe-oublie',
        builder: (_, _) => const PasswordResetScreen(),
      ),
      GoRoute(path: '/splash', builder: (_, _) => const SplashScreen()),
      GoRoute(path: '/pilotage', builder: (_, _) => const CopilConsoleScreen()),
      GoRoute(
        path: '/pilotage/organisation',
        builder: (_, _) => const CopilOrganisationScreen(),
      ),
      GoRoute(
        path: '/pilotage/directoire',
        builder: (_, _) => const DirectoireBoardScreen(),
      ),
      GoRoute(
        path: '/pilotage/conseillers',
        builder: (_, _) => const DirectoireScreen(conseillers: true),
      ),
      GoRoute(
        path: '/pilotage/atf',
        builder: (_, _) => const CopilConsoleScreen(),
      ),
      GoRoute(path: '/ctc', builder: (_, _) => const CtcScreen()),
      GoRoute(
        path: '/expert',
        builder: (context, state) {
          final tab = int.tryParse(state.uri.queryParameters['tab'] ?? '') ?? 0;
          return ExpertScreen(initialTab: tab);
        },
      ),
    ],
  );
});

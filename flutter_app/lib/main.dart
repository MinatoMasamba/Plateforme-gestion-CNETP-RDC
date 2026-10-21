import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/auth/auth_controller.dart';
import 'core/routing/app_router.dart';
import 'theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Résout la session avant le premier rendu → pas de course /splash → /login.
  final initial = await AuthController.loadInitialState();
  runApp(
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith(
          (ref) => AuthController(initialState: initial),
        ),
      ],
      child: const CnetpApp(),
    ),
  );
}

class CnetpApp extends ConsumerWidget {
  const CnetpApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'CNE-ITP',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      routerConfig: router,
    );
  }
}

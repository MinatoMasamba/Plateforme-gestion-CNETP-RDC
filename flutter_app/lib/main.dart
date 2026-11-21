import 'dart:async';
import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/api/api_client.dart';
import 'core/diagnostics/client_diagnostics.dart';
import 'core/auth/auth_controller.dart';
import 'core/routing/app_router.dart';
import 'theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  ClientDiagnostics.authenticated = () =>
      ApiClient.accessToken?.isNotEmpty == true;
  ClientDiagnostics.sender = (report) async {
    await ApiClient.dio.post('/api/v1/mobile/diagnostics/', data: report);
  };
  final previousErrorHandler = FlutterError.onError;
  FlutterError.onError = (details) {
    previousErrorHandler?.call(details);
    ClientDiagnostics.report(
      'flutter',
      details.exceptionAsString(),
      stack: details.stack,
    );
  };
  final previousPlatformHandler = PlatformDispatcher.instance.onError;
  PlatformDispatcher.instance.onError = (error, stack) {
    ClientDiagnostics.report('flutter', '$error', stack: stack);
    previousPlatformHandler?.call(error, stack);
    return true;
  };
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

class CnetpApp extends ConsumerStatefulWidget {
  const CnetpApp({super.key});

  @override
  ConsumerState<CnetpApp> createState() => _CnetpAppState();
}

class _CnetpAppState extends ConsumerState<CnetpApp> {
  late final AppLifecycleListener _lifecycle;

  @override
  void initState() {
    super.initState();
    _lifecycle = AppLifecycleListener(
      onDetach: () => unawaited(ApiClient.dispose()),
    );
  }

  @override
  void dispose() {
    _lifecycle.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'CNE-ITP',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      routerConfig: router,
    );
  }
}

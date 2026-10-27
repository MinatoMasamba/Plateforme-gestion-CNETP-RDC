import 'package:dio/dio.dart';

import '../network/network_failover_manager.dart';

/// Client HTTP unique vers l'API Django CNE-ITP.
///
/// Surcharges utiles :
/// --dart-define=API_BASE_URL=https://USERNAME.pythonanywhere.com
/// --dart-define=API_RELAY_BASE_URL=https://relais.example.org
/// --dart-define=LOCAL_PROXY_PORT=8080
/// --dart-define=DIRECT_RETRY_MINUTES=10
///
/// Le relais doit accepter les mêmes chemins, méthodes et en-têtes que l'API
/// (dont `Authorization`), sans mettre en cache les réponses authentifiées.
class ApiClient {
  ApiClient._();

  static const String directBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:1111',
  );

  static const String _relayBaseUrl = String.fromEnvironment(
    'API_RELAY_BASE_URL',
    defaultValue: '',
  );

  static const int _localProxyPort = int.fromEnvironment(
    'LOCAL_PROXY_PORT',
    defaultValue: 8080,
  );

  static const int _directRetryMinutes = int.fromEnvironment(
    'DIRECT_RETRY_MINUTES',
    defaultValue: 10,
  );

  /// Access token courant, posé par le AuthController après login/refresh.
  static String? accessToken;

  static final NetworkFailoverManager networkFailover =
      NetworkFailoverManager(
        directBaseUrl: directBaseUrl,
        relayBaseUrl: _relayBaseUrl.isEmpty ? null : _relayBaseUrl,
        proxyPort: _localProxyPort,
        directRetryInterval: Duration(minutes: _directRetryMinutes),
      );

  static final Dio dio = _buildDio();

  static String get baseUrl => networkFailover.activeBaseUrl;

  static Dio _buildDio() {
    final d = Dio(
      BaseOptions(
        baseUrl: directBaseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 30),
        headers: {'Content-Type': 'application/json'},
      ),
    );
    d.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          final token = accessToken;
          final publicRequest =
              options.path.startsWith('/api/v1/expert-registration/') ||
              options.path.startsWith('/api/v1/mobile/auth/password-reset/') ||
              options.path == '/api/v1/mobile/auth/login/';
          if (!publicRequest && token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
      ),
    );
    d.interceptors.add(NetworkFailoverInterceptor(networkFailover));
    return d;
  }

  static Uri api(String path) => Uri.parse(
    path.startsWith('http://') || path.startsWith('https://')
        ? path
        : '$baseUrl$path',
  );

  static Future<void> dispose() async {
    await networkFailover.dispose();
    dio.close(force: true);
  }
}

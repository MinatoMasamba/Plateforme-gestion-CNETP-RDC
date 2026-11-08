import 'dart:convert';
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
  static Future<bool> Function()? refreshAccessToken;
  static Future<bool>? _refreshInFlight;

  static Future<bool> _refreshOnce() async {
    if (_refreshInFlight != null) return _refreshInFlight!;
    final refresh = refreshAccessToken;
    if (refresh == null) return false;
    final future = refresh();
    _refreshInFlight = future;
    try {
      return await future;
    } finally {
      _refreshInFlight = null;
    }
  }

  static final NetworkFailoverManager networkFailover = NetworkFailoverManager(
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
              options.path == '/api/v1/mobile/auth/login/' ||
              options.path == '/api/v1/mobile/auth/refresh/';
          if (publicRequest) options.headers.remove('Authorization');
          if (!publicRequest && token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          final options = error.requestOptions;
          dynamic body = error.response?.data;
          // Protected downloads also return JSON errors, even when the caller
          // requested a binary response.
          if (body is List<int> && body.length < 65536) {
            try {
              body = jsonDecode(utf8.decode(body));
            } catch (_) {
              /* Non-JSON response. */
            }
          }
          final expiredToken = body is Map && body['code'] == 'token_not_valid';
          final eligible =
              (error.response?.statusCode == 401 ||
                  error.response?.statusCode == 403) &&
              expiredToken &&
              !options.path.startsWith('/api/v1/mobile/auth/') &&
              options.extra['auth_retried'] != true;
          if (eligible) {
            try {
              // Another concurrent request may already have renewed this token.
              final tokenChanged =
                  options.headers['Authorization'] != 'Bearer $accessToken';
              if ((accessToken != null && tokenChanged) ||
                  await _refreshOnce()) {
                options.extra['auth_retried'] = true;
                handler.resolve(await dio.fetch<dynamic>(options));
                return;
              }
            } on DioException catch (retryError) {
              handler.next(retryError);
              return;
            } catch (_) {
              // Keep the original authentication failure visible to the caller.
            }
          }
          handler.next(error);
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

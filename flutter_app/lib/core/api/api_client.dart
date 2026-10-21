import 'package:dio/dio.dart';

/// Client HTTP unique vers l'API Django CNE-ITP.
///
/// L'URL de base est configurable via `--dart-define=API_BASE=...`.
/// En dev web (127.0.0.1:8080/8081) on pointe vers le serveur Django local
/// (127.0.0.1:8001) dont CORS est ouvert en DEBUG.
class ApiClient {
  ApiClient._();

  static const String baseUrl = String.fromEnvironment(
    'API_BASE',
    defaultValue: 'http://127.0.0.1:8001',
  );

  /// Access token courant, posé par le AuthController après login/refresh.
  static String? accessToken;

  static final Dio dio = _buildDio();

  static Dio _buildDio() {
    final d = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ));
    d.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        final token = accessToken;
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
    ));
    return d;
  }

  static Uri api(String path) => Uri.parse('$baseUrl$path');
}

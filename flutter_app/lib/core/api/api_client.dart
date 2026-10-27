import 'package:dio/dio.dart';

/// Client HTTP unique vers l'API Django CNE-ITP.
///
/// Surcharge pour un appareil ou un serveur distant : --dart-define=API_BASE_URL=...
class ApiClient {
  ApiClient._();

  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:1111',
  );

  /// Access token courant, posé par le AuthController après login/refresh.
  static String? accessToken;

  static final Dio dio = _buildDio();

  static Dio _buildDio() {
    final d = Dio(
      BaseOptions(
        baseUrl: baseUrl,
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
    return d;
  }

  static Uri api(String path) => Uri.parse('$baseUrl$path');
}

import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import 'local_proxy_service.dart';

typedef InternetProbe = Future<bool> Function();
typedef LocalProxyFactory = LocalProxyService Function(LocalProxyConfig config);
typedef NowProvider = DateTime Function();

enum NetworkRoute { direct, relay, localProxy }

enum NetworkFailoverFailure {
  connectivityUnconfirmed,
  noAlternateRoute,
  requestNotReplayed,
  proxyUnavailable,
}

class NetworkFailoverException implements Exception {
  const NetworkFailoverException(this.failure, this.message);

  final NetworkFailoverFailure failure;
  final String message;

  @override
  String toString() => message;
}

/// Détecte une panne d'accès à l'API, confirme la connectivité Internet via
/// `generate_204`, puis bascule vers un relais HTTPS ou le proxy local Dart.
///
/// Le proxy local ne contourne pas à lui seul un blocage : son upstream doit
/// être un relais accessible par un autre chemin réseau.
class NetworkFailoverManager {
  NetworkFailoverManager({
    required String directBaseUrl,
    String? relayBaseUrl,
    bool? useLocalProxy,
    bool? webMode,
    int proxyPort = 8080,
    Duration directRetryInterval = const Duration(minutes: 10),
    Duration internetProbeTimeout = const Duration(seconds: 5),
    Duration internetProbeCache = const Duration(seconds: 5),
    String internetProbeUrl = 'https://www.google.com/generate_204',
    Duration relayRequestTimeout = const Duration(seconds: 30),
    InternetProbe? internetProbe,
    LocalProxyFactory? localProxyFactory,
    Dio? transport,
    Dio? probeClient,
    NowProvider? now,
  }) :        _directBaseUrl = _normalizeDirectBase(directBaseUrl),
       _relayBaseUrl = _normalizeRelayBase(relayBaseUrl),
       _useLocalProxy = useLocalProxy ?? !(webMode ?? kIsWeb),
       _webMode = webMode ?? kIsWeb,
       _proxyPort = proxyPort,
       _directRetryInterval = directRetryInterval,
       _internetProbeTimeout = internetProbeTimeout,
       _internetProbeCache = internetProbeCache,
       _internetProbeUrl = internetProbeUrl,
       _internetProbe = internetProbe,
       _now = now ?? DateTime.now {
    _ownsTransport = transport == null;
    _transport =
        transport ??
        Dio(
          BaseOptions(
            connectTimeout: relayRequestTimeout,
            receiveTimeout: relayRequestTimeout,
            sendTimeout: relayRequestTimeout,
          ),
        );
    _ownsProbeClient = probeClient == null;
    _probeClient =
        probeClient ??
        Dio(
          BaseOptions(
            connectTimeout: internetProbeTimeout,
            receiveTimeout: internetProbeTimeout,
            sendTimeout: internetProbeTimeout,
          ),
        );

    if (_useLocalProxy) {
      final factory = localProxyFactory ?? createLocalProxy;
      _proxy = factory(
        LocalProxyConfig(
          upstreamBaseUrl: _relayBaseUrl ?? '',
          port: _proxyPort,
          upstreamTimeout: relayRequestTimeout,
        ),
      );
    } else {
      _proxy = null;
    }
  }

  static const String _retryMarker = 'cnetp.networkFailover.retry';

  final String _directBaseUrl;
  final String? _relayBaseUrl;
  final bool _useLocalProxy;
  final bool _webMode;
  final int _proxyPort;
  final Duration _directRetryInterval;
  final Duration _internetProbeTimeout;
  final Duration _internetProbeCache;
  final String _internetProbeUrl;
  final InternetProbe? _internetProbe;
  final NowProvider _now;

  late final Dio _transport;
  late final Dio _probeClient;
  late final bool _ownsTransport;
  late final bool _ownsProbeClient;
  late final LocalProxyService? _proxy;

  NetworkRoute _route = NetworkRoute.direct;
  DateTime? _activatedAt;
  Future<bool>? _activationInFlight;
  Future<bool>? _probeInFlight;
  DateTime? _lastProbeAt;
  bool _lastProbeResult = false;
  bool _disposed = false;

  String get directBaseUrl => _directBaseUrl;
  String? get relayBaseUrl => _relayBaseUrl;
  NetworkRoute get activeRoute => _route;
  bool get hasAlternateRoute => _relayBaseUrl != null;
  bool get isUsingAlternateRoute => _route != NetworkRoute.direct;

  String get activeBaseUrl {
    switch (_route) {
      case NetworkRoute.direct:
        return _directBaseUrl;
      case NetworkRoute.relay:
        return _relayBaseUrl!;
      case NetworkRoute.localProxy:
        return _proxy?.baseUrl ?? _directBaseUrl;
    }
  }

  /// À appeler dans l'intercepteur de requête avant l'envoi.
  void prepareRequest(RequestOptions options) {
    _maybeRestoreDirect();

    if (_isAbsolute(options.path)) {
      final relative = _pathForFailover(options);
      if (relative != null && _route != NetworkRoute.direct) {
        options.path = relative;
        options.baseUrl = activeBaseUrl;
      }
    } else {
      options.baseUrl = activeBaseUrl;
    }

    final key = _route == NetworkRoute.localProxy ? _proxy?.accessKey : null;
    if (key != null && key.isNotEmpty) {
      options.headers[LocalProxyConfig.accessKeyHeader] = key;
    } else {
      options.headers.remove(LocalProxyConfig.accessKeyHeader);
    }
  }

  /// Vérifie la connectivité du chemin alternatif.
  ///
  /// Natif : `https://www.google.com/generate_204` doit répondre 204. Web : le
  /// relais est sondé, car Google n'autorise pas CORS sur `generate_204`.
  ///
  /// Un échec ne prouve pas l'absence totale d'Internet : il signifie
  /// seulement que la connectivité n'est pas confirmée.
  Future<bool> checkInternet() => _webMode
      ? _alternateRouteReachable(RequestOptions(path: '/'))
      : _internetAvailable();

  Future<void> handleError(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    final options = error.requestOptions;

    if (options.extra[_retryMarker] == true ||
        !isNetworkFailure(error) ||
        (options.cancelToken?.isCancelled ?? false)) {
      handler.next(error);
      return;
    }

    if (_pathForFailover(options) == null) {
      handler.next(error);
      return;
    }

    if (_route == NetworkRoute.localProxy) {
      await _fallbackFromProxy(error, handler);
      return;
    }

    if (_route != NetworkRoute.direct) {
      handler.next(error);
      return;
    }

    if (_relayBaseUrl == null) {
      if (_webMode) {
        handler.next(
          _withFailure(
            error,
            NetworkFailoverFailure.noAlternateRoute,
            "Aucun relais alternatif n'est configuré "
            "(API_RELAY_BASE_URL). Le navigateur ne peut pas utiliser de "
            'proxy local.',
          ),
        );
        return;
      }

      final internetAvailable = await _internetAvailable();
      if (!internetAvailable) {
        handler.next(
          _withFailure(
            error,
            NetworkFailoverFailure.connectivityUnconfirmed,
            'Connectivité Internet non confirmée : le test '
            'https://www.google.com/generate_204 a échoué. '
            "Le serveur CNE-ITP n'a pas pu être joint.",
          ),
        );
        return;
      }

      handler.next(
        _withFailure(
          error,
          NetworkFailoverFailure.noAlternateRoute,
          'Connectivité Internet confirmée, mais aucun relais alternatif '
          "n'est configuré (API_RELAY_BASE_URL).",
        ),
      );
      return;
    }

    if (_webMode) {
      final reachable = await _alternateRouteReachable(options);
      if (!reachable) {
        handler.next(
          _withFailure(
            error,
            NetworkFailoverFailure.connectivityUnconfirmed,
            'Le relais alternatif n’a pas pu être joint depuis le navigateur '
            '(réseau, CORS ou service indisponible). Le serveur CNE-ITP n’a '
            'pas pu être joint.',
          ),
        );
        return;
      }
    } else {
      final internetAvailable = await _internetAvailable();
      if (!internetAvailable) {
        handler.next(
          _withFailure(
            error,
            NetworkFailoverFailure.connectivityUnconfirmed,
            'Connectivité Internet non confirmée : le test '
            'https://www.google.com/generate_204 a échoué. '
            "Le serveur CNE-ITP n'a pas pu être joint.",
          ),
        );
        return;
      }
    }

    final activated = await _activateAlternateRoute();
    if (!activated) {
      handler.next(
        _withFailure(
          error,
          NetworkFailoverFailure.noAlternateRoute,
          'Aucun chemin alternatif disponible pour joindre le serveur '
          'CNE-ITP.',
        ),
      );
      return;
    }

    if (!_canReplay(options)) {
      handler.next(
        _withFailure(
          error,
          NetworkFailoverFailure.requestNotReplayed,
          'Le chemin alternatif est actif. La requête '
          '${options.method.toUpperCase()} n’a pas été rejouée '
          'automatiquement afin d’éviter un doublon. Réessayez l’action.',
        ),
      );
      return;
    }

    await _retryWithActiveRoute(error, handler);
  }

  Future<void> _fallbackFromProxy(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    final relay = _relayBaseUrl;
    if (relay == null) {
      handler.next(
        _withFailure(
          error,
          NetworkFailoverFailure.proxyUnavailable,
          'Le proxy local ne peut pas joindre le relais alternatif.',
        ),
      );
      return;
    }

    _route = NetworkRoute.relay;
    _activatedAt = _now();
    if (!_canReplay(error.requestOptions)) {
      handler.next(
        _withFailure(
          error,
          NetworkFailoverFailure.requestNotReplayed,
          'Le relais alternatif est actif. La requête '
          '${error.requestOptions.method.toUpperCase()} n’a pas été rejouée '
          'automatiquement afin d’éviter un doublon. Réessayez l’action.',
        ),
      );
      return;
    }
    await _retryWithActiveRoute(error, handler);
  }

  Future<void> _retryWithActiveRoute(
    DioException original,
    ErrorInterceptorHandler handler,
  ) async {
    final options = original.requestOptions;
    final path = _pathForFailover(options);
    if (path == null) {
      handler.next(original);
      return;
    }

    final headers = Map<String, dynamic>.from(options.headers)
      ..remove(LocalProxyConfig.accessKeyHeader);
    if (_route == NetworkRoute.localProxy) {
      final key = _proxy?.accessKey;
      if (key != null && key.isNotEmpty) {
        headers[LocalProxyConfig.accessKeyHeader] = key;
      }
    }

    final retryOptions = options.copyWith(
      path: path,
      baseUrl: activeBaseUrl,
      headers: headers,
      extra: {...options.extra, _retryMarker: true},
    );

    try {
      final response = await _transport.fetch<dynamic>(retryOptions);
      handler.resolve(response);
    } on DioException catch (retryError) {
      handler.next(retryError);
    } catch (error, stackTrace) {
      handler.next(
        DioException(
          requestOptions: retryOptions,
          type: DioExceptionType.unknown,
          error: error,
          stackTrace: stackTrace,
        ),
      );
    }
  }

  Future<bool> _activateAlternateRoute() {
    final existing = _activationInFlight;
    if (existing != null) return existing;

    late Future<bool> future;
    future = _activateAlternateRouteInternal().whenComplete(() {
      if (identical(_activationInFlight, future)) _activationInFlight = null;
    });
    _activationInFlight = future;
    return future;
  }

  Future<bool> _activateAlternateRouteInternal() async {
    if (_route != NetworkRoute.direct) return true;
    final relay = _relayBaseUrl;
    if (relay == null) return false;

    if (_useLocalProxy && _proxy != null) {
      try {
        final uri = await _proxy.start();
        if (uri.host == '127.0.0.1' && uri.port > 0) {
          _route = NetworkRoute.localProxy;
          _activatedAt = _now();
          return true;
        }
      } catch (_) {
        // Le relais direct reste préférable à une absence de bascule.
      }
    }

    _route = NetworkRoute.relay;
    _activatedAt = _now();
    return true;
  }

  void _maybeRestoreDirect() {
    if (_route == NetworkRoute.direct) return;
    final activatedAt = _activatedAt;
    if (activatedAt == null) return;
    if (_now().difference(activatedAt) >= _directRetryInterval) {
      _route = NetworkRoute.direct;
      _activatedAt = null;
    }
  }

  /// Sur le Web, `generate_204` est inaccessible à cause de CORS. On teste donc
  /// le relais lui-même : une réponse HTTP, même 401 ou 405, prouve que le
  /// navigateur peut le joindre. Sans relais, aucun chemin alternatif.
  Future<bool> _alternateRouteReachable(RequestOptions options) {
    final existing = _probeInFlight;
    if (existing != null) return existing;

    final now = _now();
    final checkedAt = _lastProbeAt;
    if (checkedAt != null && now.difference(checkedAt) < _internetProbeCache) {
      return Future<bool>.value(_lastProbeResult);
    }

    late Future<bool> future;
    future = _probeRelay(options).whenComplete(() {
      if (identical(_probeInFlight, future)) _probeInFlight = null;
    });
    _probeInFlight = future;
    return future;
  }

  Future<bool> _probeRelay(RequestOptions options) async {
    var result = false;
    try {
      final relay = _relayBaseUrl;
      if (relay == null) return false;
      final path = _pathForFailover(options) ?? '/';
      final normalizedPath = path.startsWith('/') ? path : '/$path';

      // Requête CORS simple : pas d'Authorization, donc pas de préflight.
      // Une réponse 401/405 suffit à prouver que le relais est joignable.
      await _transport.head<dynamic>(
        '$relay$normalizedPath',
        options: Options(
          followRedirects: false,
          receiveTimeout: _internetProbeTimeout,
          sendTimeout: _internetProbeTimeout,
          validateStatus: (_) => true,
        ),
      );
      result = true;
    } catch (_) {
      result = false;
    }

    _lastProbeAt = _now();
    _lastProbeResult = result;
    return result;
  }

  Future<bool> _internetAvailable() {
    final existing = _probeInFlight;
    if (existing != null) return existing;

    final now = _now();
    final checkedAt = _lastProbeAt;
    if (checkedAt != null && now.difference(checkedAt) < _internetProbeCache) {
      return Future<bool>.value(_lastProbeResult);
    }

    late Future<bool> future;
    future = _probeInternet().whenComplete(() {
      if (identical(_probeInFlight, future)) _probeInFlight = null;
    });
    _probeInFlight = future;
    return future;
  }

  Future<bool> _probeInternet() async {
    var result = false;
    try {
      final injected = _internetProbe;
      if (injected != null) {
        result = await injected();
      } else {
        final response = await _probeClient.get<dynamic>(
          _internetProbeUrl,
          options: Options(
            responseType: ResponseType.plain,
            followRedirects: false,
            receiveTimeout: _internetProbeTimeout,
            sendTimeout: _internetProbeTimeout,
            validateStatus: (status) => status == 204,
            headers: const {'Cache-Control': 'no-cache'},
          ),
        );
        result = response.statusCode == 204;
      }
    } catch (_) {
      result = false;
    }

    _lastProbeAt = _now();
    _lastProbeResult = result;
    return result;
  }

  static bool isNetworkFailure(DioException error) {
    if (error.response != null) return false;
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.connectionError:
      case DioExceptionType.unknown:
        return true;
      case DioExceptionType.badCertificate:
      case DioExceptionType.badResponse:
      case DioExceptionType.cancel:
      case DioExceptionType.transformTimeout:
        return false;
    }
  }

  static bool _canReplay(RequestOptions options) {
    final method = options.method.toUpperCase();
    final safeMethod =
        method == 'GET' || method == 'HEAD' || method == 'OPTIONS';
    return safeMethod && options.data == null;
  }

  String? _pathForFailover(RequestOptions options) {
    if (!_isAbsolute(options.path)) return options.path;

    final uri = Uri.tryParse(options.path);
    if (uri == null) return null;
    final direct = Uri.tryParse(_directBaseUrl);
    final relay = _relayBaseUrl == null ? null : Uri.tryParse(_relayBaseUrl);
    final fromKnownHost =
        (direct != null && _sameOrigin(uri, direct)) ||
        (relay != null && _sameOrigin(uri, relay));
    if (!fromKnownHost) return null;
    return uri.hasQuery ? '${uri.path}?${uri.query}' : uri.path;
  }

  static bool _isAbsolute(String path) =>
      path.startsWith('http://') || path.startsWith('https://');

  static bool _sameOrigin(Uri a, Uri b) =>
      a.scheme == b.scheme &&
      a.host.toLowerCase() == b.host.toLowerCase() &&
      a.port == b.port;

  static DioException _withFailure(
    DioException original,
    NetworkFailoverFailure failure,
    String message,
  ) {
    return DioException(
      requestOptions: original.requestOptions,
      response: original.response,
      type: original.type,
      error: NetworkFailoverException(failure, message),
      message: message,
      stackTrace: original.stackTrace,
    );
  }

  static String _normalizeDirectBase(String value) {
    final normalized = _normalizeHttpBase(value, 'directBaseUrl');
    return normalized;
  }

  static String? _normalizeRelayBase(String? value) {
    if (value == null || value.trim().isEmpty) return null;
    final normalized = _normalizeHttpBase(value, 'relayBaseUrl');
    final uri = Uri.parse(normalized);
    if (uri.scheme != 'https' && !_isLoopbackHost(uri.host)) {
      throw ArgumentError.value(
        value,
        'relayBaseUrl',
        'Le relais distant doit utiliser HTTPS',
      );
    }
    return normalized;
  }

  static String _normalizeHttpBase(String value, String name) {
    final trimmed = value.trim();
    final uri = Uri.tryParse(trimmed);
    if (uri == null ||
        uri.host.isEmpty ||
        (uri.scheme != 'http' && uri.scheme != 'https')) {
      throw ArgumentError.value(value, name, 'URL HTTP(S) invalide');
    }
    if (uri.hasQuery || uri.hasFragment) {
      throw ArgumentError.value(
        value,
        name,
        'La base ne doit contenir ni query ni fragment',
      );
    }
    return trimmed.endsWith('/')
        ? trimmed.substring(0, trimmed.length - 1)
        : trimmed;
  }

  static bool _isLoopbackHost(String host) {
    final normalized = host.toLowerCase();
    return normalized == '127.0.0.1' ||
        normalized == 'localhost' ||
        normalized == '::1';
  }

  Future<void> dispose() async {
    if (_disposed) return;
    _disposed = true;
    await _proxy?.stop();
    if (_ownsTransport) _transport.close(force: true);
    if (_ownsProbeClient) _probeClient.close(force: true);
  }
}

class NetworkFailoverInterceptor extends Interceptor {
  NetworkFailoverInterceptor(this.manager);

  final NetworkFailoverManager manager;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    manager.prepareRequest(options);
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) => manager.handleError(err, handler);
}

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'local_proxy_contract.dart';

/// Implémentation native (Android, iOS, Windows, macOS, Linux).
LocalProxyService createLocalProxy(LocalProxyConfig config) =>
    IoLocalProxyService(config);

class IoLocalProxyService implements LocalProxyService {
  IoLocalProxyService(this._config);

  static const Set<String> _hopByHopHeaders = {
    'connection',
    'keep-alive',
    'proxy-authenticate',
    'proxy-authorization',
    'proxy-connection',
    'te',
    'trailer',
    'transfer-encoding',
    'upgrade',
  };

  static const Set<String> _allowedMethods = {
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'HEAD',
    'OPTIONS',
  };

  final LocalProxyConfig _config;
  final String _accessKey = _generateAccessKey();

  HttpServer? _server;
  HttpClient? _client;
  String? _baseUrl;
  Future<Uri>? _starting;

  @override
  bool get isRunning => _server != null;

  @override
  String? get baseUrl => _baseUrl;

  @override
  String get accessKey => _accessKey;

  @override
  Future<Uri> start() {
    final server = _server;
    if (server != null) {
      return Future<Uri>.value(Uri.parse(_baseUrl!));
    }
    final starting = _starting;
    if (starting != null) return starting;

    late Future<Uri> future;
    future = _startInternal().whenComplete(() {
      if (identical(_starting, future)) _starting = null;
    });
    _starting = future;
    return future;
  }

  Future<Uri> _startInternal() async {
    if (_config.port < 0 || _config.port > 65535) {
      throw ArgumentError.value(_config.port, 'port', 'Port invalide');
    }

    final upstream = _validateUpstream();
    final server = await HttpServer.bind(
      InternetAddress.loopbackIPv4,
      _config.port,
    ).timeout(_config.startupTimeout);
    server.autoCompress = false;

    if (_isLoopback(upstream.host) && upstream.port == server.port) {
      await server.close(force: true);
      throw StateError(
        'Le relais ne peut pas pointer vers le proxy local lui-même.',
      );
    }

    final client = HttpClient();
    client.connectionTimeout = _config.upstreamTimeout;
    client.idleTimeout = const Duration(seconds: 15);
    client.autoUncompress = false;
    client.findProxy = (_) => 'DIRECT';

    _client = client;
    _server = server;
    _baseUrl = 'http://127.0.0.1:${server.port}';

    server.listen((request) {
      unawaited(_handleSafely(request));
    });

    return Uri.parse(_baseUrl!);
  }

  Uri _validateUpstream() {
    final uri = Uri.tryParse(_config.upstreamBaseUrl.trim());
    if (uri == null || uri.host.isEmpty || !uri.hasScheme) {
      throw ArgumentError.value(
        _config.upstreamBaseUrl,
        'upstreamBaseUrl',
        'URL de relais invalide',
      );
    }
    if (uri.hasQuery || uri.hasFragment) {
      throw ArgumentError.value(
        _config.upstreamBaseUrl,
        'upstreamBaseUrl',
        'Le relais ne doit contenir ni query ni fragment',
      );
    }
    if (uri.scheme == 'http' && !_isLoopback(uri.host)) {
      throw ArgumentError.value(
        _config.upstreamBaseUrl,
        'upstreamBaseUrl',
        'Le relais distant doit utiliser HTTPS',
      );
    }
    if (uri.scheme != 'http' && uri.scheme != 'https') {
      throw ArgumentError.value(
        _config.upstreamBaseUrl,
        'upstreamBaseUrl',
        'Le relais doit utiliser HTTP(S)',
      );
    }
    return uri;
  }

  @override
  Future<void> stop() async {
    final server = _server;
    _server = null;
    _baseUrl = null;
    _client?.close(force: true);
    _client = null;
    await server?.close(force: true);
  }

  Future<void> _handleSafely(HttpRequest request) async {
    try {
      await _handle(request);
    } catch (_) {
      await _writeJson(request, HttpStatus.badGateway, 'proxy_error');
    }
  }

  Future<void> _handle(HttpRequest request) async {
    if (request.headers.value(LocalProxyConfig.accessKeyHeader) != _accessKey) {
      await _writeJson(request, HttpStatus.forbidden, 'proxy_access_denied');
      return;
    }
    if (!_allowedMethods.contains(request.method)) {
      await _writeJson(
        request,
        HttpStatus.methodNotAllowed,
        'proxy_method_not_allowed',
      );
      return;
    }
    if (request.uri.hasScheme ||
        request.uri.host.isNotEmpty ||
        request.uri.path.startsWith('//')) {
      await _writeJson(request, HttpStatus.badRequest, 'proxy_invalid_target');
      return;
    }

    final body = await request.fold<List<int>>(
      <int>[],
      (buffer, chunk) => buffer..addAll(chunk),
    );
    final target = _buildUpstreamUri(request.uri);

    try {
      final client = _client;
      if (client == null) {
        throw StateError('Proxy non démarré');
      }

      final upstreamRequest = await client
          .openUrl(request.method, target)
          .timeout(_config.upstreamTimeout);
      upstreamRequest.followRedirects = false;
      upstreamRequest.maxRedirects = 0;
      if (body.isNotEmpty) upstreamRequest.contentLength = body.length;

      request.headers.forEach((name, values) {
        final lower = name.toLowerCase();
        if (lower == HttpHeaders.hostHeader ||
            lower == HttpHeaders.contentLengthHeader ||
            lower == LocalProxyConfig.accessKeyHeader.toLowerCase() ||
            lower == HttpHeaders.expectHeader ||
            _hopByHopHeaders.contains(lower)) {
          return;
        }
        for (final value in values) {
          upstreamRequest.headers.add(name, value);
        }
      });

      if (body.isNotEmpty) upstreamRequest.add(body);

      final upstreamResponse = await upstreamRequest
          .close()
          .timeout(_config.upstreamTimeout);
      request.response.statusCode = upstreamResponse.statusCode;

      upstreamResponse.headers.forEach((name, values) {
        final lower = name.toLowerCase();
        if (lower == HttpHeaders.connectionHeader ||
            lower == HttpHeaders.transferEncodingHeader ||
            lower == 'keep-alive' ||
            lower == 'proxy-connection' ||
            lower == 'trailer' ||
            lower == 'upgrade') {
          return;
        }
        for (final value in values) {
          request.response.headers.add(name, value);
        }
      });

      if (request.method == 'HEAD') {
        await upstreamResponse.drain<void>();
      } else {
        await request.response
            .addStream(upstreamResponse)
            .timeout(_config.upstreamTimeout);
      }
      await request.response.close();
    } on TimeoutException {
      await _writeJson(request, HttpStatus.gatewayTimeout, 'upstream_timeout');
    } on HandshakeException {
      await _writeJson(request, HttpStatus.badGateway, 'upstream_tls_error');
    } on SocketException {
      await _writeJson(request, HttpStatus.badGateway, 'upstream_unreachable');
    } on HttpException {
      await _writeJson(request, HttpStatus.badGateway, 'upstream_http_error');
    } catch (_) {
      await _writeJson(request, HttpStatus.badGateway, 'upstream_error');
    }
  }

  Uri _buildUpstreamUri(Uri incoming) {
    final base = _config.upstreamBaseUrl.trim().replaceFirst(RegExp(r'/$'), '');
    final path = incoming.path.isEmpty
        ? '/'
        : (incoming.path.startsWith('/') ? incoming.path : '/${incoming.path}');
    final query = incoming.hasQuery ? '?${incoming.query}' : '';
    return Uri.parse('$base$path$query');
  }

  Future<void> _writeJson(HttpRequest request, int status, String code) async {
    try {
      request.response.statusCode = status;
      request.response.headers.contentType = ContentType.json;
      request.response.write(jsonEncode({'error_code': code}));
      await request.response.close();
    } catch (_) {
      // La réponse peut déjà être engagée ; on ne journalise rien.
    }
  }

  static bool _isLoopback(String host) {
    final normalized = host.toLowerCase();
    return normalized == '127.0.0.1' ||
        normalized == 'localhost' ||
        normalized == '::1';
  }

  static String _generateAccessKey() {
    final random = Random.secure();
    final bytes = List<int>.generate(32, (_) => random.nextInt(256));
    return base64UrlEncode(bytes);
  }
}

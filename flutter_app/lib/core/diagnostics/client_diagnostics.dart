import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ClientDiagnostics {
  ClientDiagnostics._();
  static const appVersion = String.fromEnvironment(
    'APP_VERSION',
    defaultValue: '1.0.0-beta.1+3',
  );
  static Future<void> Function(Map<String, dynamic>)? sender;
  static bool Function()? authenticated;
  static final _queue = <Map<String, dynamic>>[];
  static final _recent = <String, DateTime>{};
  static bool _sending = false;
  static DateTime? _retryAfter;
  static SharedPreferences? _preferences;
  static const _storageKey = 'cnetp_pending_diagnostics';
  static Future<void> _storageWrite = Future.value();

  static Future<void> initialize() async {
    try {
      _preferences = await SharedPreferences.getInstance();
      final saved = _preferences!.getString(_storageKey);
      if (saved == null) return;
      final items = jsonDecode(saved) as List<dynamic>;
      for (final item in items.take(20)) {
        final incident = Map<String, dynamic>.from(item as Map);
        if (!_queue.any((entry) => entry['event_id'] == incident['event_id'])) {
          _queue.add(incident);
        }
      }
      while (_queue.length > 20) {
        _queue.removeAt(0);
      }
    } catch (_) {
      // Le stockage du diagnostic ne doit pas bloquer le démarrage.
    }
  }

  static Future<void> persist() {
    final preferences = _preferences;
    if (preferences == null) return Future.value();
    final snapshot = jsonEncode(_queue);
    _storageWrite = _storageWrite.then((_) async {
      try {
        await preferences.setString(_storageKey, snapshot);
      } catch (_) {
        // Ne pas générer un diagnostic sur sa propre panne de stockage.
      }
    });
    return _storageWrite;
  }

  static void clear() {
    _queue.clear();
    _recent.clear();
    _retryAfter = null;
    unawaited(persist());
  }

  static String sanitize(String value, int limit) {
    var text = value.replaceAll(RegExp(r'https?://[^\s<>]+'), '[URL masquée]');
    text = text.replaceAll(
      RegExp(r'bearer\s+\S+', caseSensitive: false),
      'Bearer [masqué]',
    );
    text = text.replaceAll(
      RegExp(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'),
      '[jeton masqué]',
    );
    text = text.replaceAll(
      RegExp(
        r'(password|passwd|token|secret|api[_-]?key)\s*[:=]\s*\S+',
        caseSensitive: false,
      ),
      '[secret masqué]',
    );
    text = text.replaceAll(
      RegExp(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}'),
      '[courriel masqué]',
    );
    return text.length > limit ? text.substring(0, limit) : text;
  }

  static void report(
    String category,
    String message, {
    StackTrace? stack,
    Map<String, dynamic> details = const {},
  }) {
    final now = DateTime.now();
    final safeMessage = sanitize(message, 2000);
    final fingerprint = '$category|$safeMessage|${details['path']}';
    _recent.removeWhere(
      (_, time) => now.difference(time) > const Duration(minutes: 1),
    );
    if (_recent.containsKey(fingerprint)) return;
    if (_recent.length >= 100) _recent.remove(_recent.keys.first);
    _recent[fingerprint] = now;
    if (_queue.length >= 20) _queue.removeAt(0);
    _queue.add({
      'event_id': '${now.microsecondsSinceEpoch}_${Random().nextInt(1 << 30)}',
      'category': category,
      'app_version': appVersion,
      'platform': kIsWeb ? 'web' : defaultTargetPlatform.name,
      'message': safeMessage,
      if (stack != null) 'stack': sanitize('$stack', 12000),
      ...details,
    });
    unawaited(persist());
    unawaited(flush());
  }

  static Future<void> flush() async {
    if (_sending ||
        sender == null ||
        authenticated?.call() != true ||
        (_retryAfter != null && DateTime.now().isBefore(_retryAfter!))) {
      return;
    }
    _sending = true;
    try {
      while (_queue.isNotEmpty) {
        final incident = _queue.first;
        await sender!(Map.of(incident));
        _queue.remove(incident);
        await persist();
      }
      _retryAfter = null;
    } catch (_) {
      // Une panne de diagnostic ne doit ni masquer l'erreur ni créer une boucle.
      _retryAfter = DateTime.now().add(const Duration(seconds: 30));
    } finally {
      _sending = false;
    }
  }
}

class DiagnosticInterceptor extends Interceptor {
  DiagnosticInterceptor(this.route);
  final String Function() route;
  static const _timer = 'client_diagnostic_timer';

  bool _skip(RequestOptions options) =>
      options.path.contains('/mobile/diagnostics/');

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (!_skip(options)) options.extra[_timer] = Stopwatch()..start();
    handler.next(options);
  }

  void _record(RequestOptions options, int? status, {DioException? error}) {
    if (_skip(options)) return;
    final timer = options.extra[_timer];
    final elapsed = timer is Stopwatch ? timer.elapsedMilliseconds : 0;
    final failure =
        error != null &&
        error.type != DioExceptionType.cancel &&
        (status == null || status >= 500);
    if (failure || elapsed >= 2000) {
      ClientDiagnostics.report(
        failure ? 'network' : 'slow_request',
        failure
            ? 'Requête API échouée (${error.type.name})'
            : 'Requête API lente',
        details: {
          'path': (Uri.tryParse(options.path)?.path ?? '').split('?').first,
          'method': options.method.toUpperCase(),
          'route': route(),
          'duration_ms': elapsed.clamp(0, 3600000),
          'status_code': ?status,
        },
      );
    } else {
      unawaited(ClientDiagnostics.flush());
    }
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    _record(response.requestOptions, response.statusCode);
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    _record(err.requestOptions, err.response?.statusCode, error: err);
    handler.next(err);
  }
}

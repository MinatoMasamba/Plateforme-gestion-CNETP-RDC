import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:cnetp_app/core/network/network_failover_manager.dart';

import 'support/http_test_server.dart';

NetworkFailoverManager _manager({
  required String direct,
  String? relay,
  bool useLocalProxy = false,
  int proxyPort = 0,
  InternetProbe? probe,
  NowProvider? now,
  Duration directRetryInterval = const Duration(minutes: 10),
  Duration relayRequestTimeout = const Duration(seconds: 30),
}) {
  return NetworkFailoverManager(
    directBaseUrl: direct,
    relayBaseUrl: relay,
    useLocalProxy: useLocalProxy,
    proxyPort: proxyPort,
    internetProbe: probe ?? () async => true,
    now: now,
    directRetryInterval: directRetryInterval,
    relayRequestTimeout: relayRequestTimeout,
  );
}

Dio _client(
  NetworkFailoverManager manager, {
  Duration receiveTimeout = const Duration(seconds: 2),
}) {
  final dio = Dio(
    BaseOptions(
      baseUrl: manager.directBaseUrl,
      receiveTimeout: receiveTimeout,
    ),
  );
  dio.interceptors.add(NetworkFailoverInterceptor(manager));
  return dio;
}

void main() {
  test('1. API accessible : connexion directe', () async {
    var probes = 0;
    final direct = await TestHttpServer.start(
      (request, _) => writeJson(request, 200, {'route': 'direct'}),
    );
    final manager = _manager(
      direct: direct.baseUrl,
      probe: () async {
        probes++;
        return true;
      },
    );
    final dio = _client(manager);
    addTearDown(() async {
      dio.close(force: true);
      await manager.dispose();
      await direct.close();
    });

    final response = await dio.get<dynamic>('/api/v1/health/');

    expect(response.statusCode, 200);
    expect(response.data['route'], 'direct');
    expect(manager.activeRoute, NetworkRoute.direct);
    expect(direct.requests, hasLength(1));
    expect(probes, 0);
  });

  test(
    '2. API bloquée + Google OK : bascule vers un relais alternatif',
    () async {
      final directPort = await unusedTcpPort();
      final relay = await TestHttpServer.start((request, _) async {
        await writeJson(request, 200, {
          'route': 'relay',
          'authorization': request.headers.value('authorization'),
        });
      });
      final manager = _manager(
        direct: 'http://127.0.0.1:$directPort',
        relay: relay.baseUrl,
      );
      final dio = _client(manager);
      addTearDown(() async {
        dio.close(force: true);
        await manager.dispose();
        await relay.close();
      });

      final response = await dio.get<dynamic>(
        '/api/v1/norms/1/',
        queryParameters: {'page': 2},
        options: Options(headers: {'Authorization': 'Bearer secret'}),
      );

      expect(response.statusCode, 200);
      expect(response.data['route'], 'relay');
      expect(response.data['authorization'], 'Bearer secret');
      expect(manager.activeRoute, NetworkRoute.relay);
      expect(relay.requests, hasLength(1));
      expect(relay.requests.single.uri.path, '/api/v1/norms/1/');
      expect(relay.requests.single.uri.queryParameters['page'], '2');
    },
  );

  test('3. API et Google inaccessibles : erreur explicite', () async {
    final directPort = await unusedTcpPort();
    final relay = await TestHttpServer.start(
      (request, _) => writeJson(request, 200, {'route': 'relay'}),
    );
    final manager = _manager(
      direct: 'http://127.0.0.1:$directPort',
      relay: relay.baseUrl,
      probe: () async => false,
    );
    final dio = _client(manager);
    addTearDown(() async {
      dio.close(force: true);
      await manager.dispose();
      await relay.close();
    });

    DioException? caught;
    try {
      await dio.get<dynamic>('/api/v1/health/');
    } on DioException catch (error) {
      caught = error;
    }

    expect(caught, isNotNull);
    final failover = caught!.error;
    expect(failover, isA<NetworkFailoverException>());
    expect(
      (failover as NetworkFailoverException).failure,
      NetworkFailoverFailure.connectivityUnconfirmed,
    );
    expect(manager.activeRoute, NetworkRoute.direct);
    expect(relay.requests, isEmpty);
  });

  test('4. Sonde Internet : seul le code 204 confirme la connectivité', () async {
    var probeStatus = 200;
    final probe = await TestHttpServer.start((request, _) async {
      request.response.statusCode = probeStatus;
      await request.response.close();
    });
    final directPort = await unusedTcpPort();
    final relay = await TestHttpServer.start(
      (request, _) => writeJson(request, 200, {'route': 'relay'}),
    );
    final manager = NetworkFailoverManager(
      directBaseUrl: 'http://127.0.0.1:$directPort',
      relayBaseUrl: relay.baseUrl,
      useLocalProxy: false,
      internetProbeUrl: '${probe.baseUrl}/generate_204',
      internetProbeCache: Duration.zero,
    );
    final dio = _client(manager);
    addTearDown(() async {
      dio.close(force: true);
      await manager.dispose();
      await relay.close();
      await probe.close();
    });

    DioException? caught;
    try {
      await dio.get<dynamic>('/api/v1/health/');
    } on DioException catch (error) {
      caught = error;
    }
    expect(
      (caught!.error as NetworkFailoverException).failure,
      NetworkFailoverFailure.connectivityUnconfirmed,
    );

    probeStatus = 204;
    final response = await dio.get<dynamic>('/api/v1/health/');

    expect(response.data['route'], 'relay');
    expect(manager.activeRoute, NetworkRoute.relay);
  });

  test('5. Proxy actif mais relais inaccessible : erreur sans boucle', () async {
    final directPort = await unusedTcpPort();
    final hang = Completer<void>();
    final relay = await TestHttpServer.start((request, _) async {
      await hang.future;
    });
    final manager = _manager(
      direct: 'http://127.0.0.1:$directPort',
      relay: relay.baseUrl,
      useLocalProxy: true,
      proxyPort: 0,
      relayRequestTimeout: const Duration(milliseconds: 400),
    );
    final dio = _client(manager);
    addTearDown(() async {
      if (!hang.isCompleted) hang.complete();
      dio.close(force: true);
      await manager.dispose();
      await relay.close();
    });

    final response = await dio.get<dynamic>(
      '/api/v1/health/',
      options: Options(validateStatus: (status) => status != null),
    );

    expect(response.statusCode, 504);
    expect(response.data['error_code'], 'upstream_timeout');
    expect(manager.activeRoute, NetworkRoute.localProxy);
  });

  test(
    '5. Relais disponible : la requête suivante y est transmise',
    () async {
      final directPort = await unusedTcpPort();
      final relay = await TestHttpServer.start((request, body) async {
        await writeJson(request, request.method == 'GET' ? 200 : 201, {
          'method': request.method,
          'body': request.method == 'GET' ? null : utf8.decode(body),
          'received': body.length,
        });
      });
      final manager = _manager(
        direct: 'http://127.0.0.1:$directPort',
        relay: relay.baseUrl,
      );
      final dio = _client(manager);
      addTearDown(() async {
        dio.close(force: true);
        await manager.dispose();
        await relay.close();
      });

      await dio.get<dynamic>('/api/v1/start/');
      final response = await dio.post<dynamic>(
        '/api/v1/items/',
        data: {'name': 'CNE-ITP'},
      );

      expect(response.statusCode, 201);
      expect(relay.requests.last.method, 'POST');
      expect(relay.requests.last.bodyText, contains('"name":"CNE-ITP"'));
      expect(manager.activeRoute, NetworkRoute.relay);
    },
  );

  test('6. Erreur HTTP 400/401/403/404/500 : aucune bascule', () async {
    var probes = 0;
    final direct = await TestHttpServer.start((request, _) async {
      final status = int.parse(request.uri.pathSegments.last);
      await writeJson(request, status, {'status': status});
    });
    final relay = await TestHttpServer.start(
      (request, _) => writeJson(request, 200, {'route': 'relay'}),
    );
    final manager = _manager(
      direct: direct.baseUrl,
      relay: relay.baseUrl,
      probe: () async {
        probes++;
        return true;
      },
    );
    final dio = _client(manager);
    addTearDown(() async {
      dio.close(force: true);
      await manager.dispose();
      await relay.close();
      await direct.close();
    });

    for (final status in [400, 401, 403, 404, 500]) {
      DioException? caught;
      try {
        await dio.get<dynamic>('/api/v1/status/$status');
      } on DioException catch (error) {
        caught = error;
      }
      expect(caught?.response?.statusCode, status);
    }

    expect(probes, 0);
    expect(relay.requests, isEmpty);
    expect(manager.activeRoute, NetworkRoute.direct);
  });

  test('7. POST en timeout : aucune double soumission', () async {
    final direct = await TestHttpServer.start((request, _) async {
      await Future<void>.delayed(const Duration(milliseconds: 500));
      try {
        await writeJson(request, 201, {'route': 'direct'});
      } catch (_) {
        // Le client a déjà coupé la connexion.
      }
    });
    final relay = await TestHttpServer.start(
      (request, _) => writeJson(request, 201, {'route': 'relay'}),
    );
    final manager = _manager(direct: direct.baseUrl, relay: relay.baseUrl);
    final dio = _client(
      manager,
      receiveTimeout: const Duration(milliseconds: 100),
    );
    addTearDown(() async {
      dio.close(force: true);
      await manager.dispose();
      await relay.close();
      await direct.close();
    });

    DioException? caught;
    try {
      await dio.post<dynamic>('/api/v1/items/', data: {'name': 'unique'});
    } on DioException catch (error) {
      caught = error;
    }
    await Future<void>.delayed(const Duration(milliseconds: 600));

    expect(caught, isNotNull);
    final failover = caught!.error;
    expect(failover, isA<NetworkFailoverException>());
    expect(
      (failover as NetworkFailoverException).failure,
      NetworkFailoverFailure.requestNotReplayed,
    );
    expect(direct.requests, hasLength(1));
    expect(relay.requests, isEmpty);
    expect(manager.activeRoute, NetworkRoute.relay);
  });

  test('8. Retour du réseau : réactivation du chemin direct', () async {
    var directAvailable = false;
    final direct = await TestHttpServer.start((request, _) async {
      if (!directAvailable) {
        final socket = await request.response.detachSocket(
          writeHeaders: false,
        );
        socket.destroy();
        return;
      }
      await writeJson(request, 200, {'route': 'direct'});
    });
    final relay = await TestHttpServer.start(
      (request, _) => writeJson(request, 200, {'route': 'relay'}),
    );
    var now = DateTime(2026, 1, 1);
    final manager = _manager(
      direct: direct.baseUrl,
      relay: relay.baseUrl,
      now: () => now,
    );
    final dio = _client(manager);
    addTearDown(() async {
      dio.close(force: true);
      await manager.dispose();
      await relay.close();
      await direct.close();
    });

    final fallback = await dio.get<dynamic>('/api/v1/health/');
    expect(fallback.data['route'], 'relay');
    expect(manager.activeRoute, NetworkRoute.relay);

    directAvailable = true;
    now = now.add(const Duration(minutes: 11));
    final restored = await dio.get<dynamic>('/api/v1/health/');

    expect(restored.data['route'], 'direct');
    expect(manager.activeRoute, NetworkRoute.direct);
    expect(direct.requests, hasLength(2));
    expect(relay.requests, hasLength(1));
  });

  test('9. Sans relais configuré : erreur sans bascule', () async {
    final directPort = await unusedTcpPort();
    final manager = _manager(direct: 'http://127.0.0.1:$directPort');
    final dio = _client(manager);
    addTearDown(() async {
      dio.close(force: true);
      await manager.dispose();
    });

    DioException? caught;
    try {
      await dio.get<dynamic>('/api/v1/health/');
    } on DioException catch (error) {
      caught = error;
    }

    expect(caught, isNotNull);
    final failover = caught!.error;
    expect(failover, isA<NetworkFailoverException>());
    expect(
      (failover as NetworkFailoverException).failure,
      NetworkFailoverFailure.noAlternateRoute,
    );
    expect(manager.activeRoute, NetworkRoute.direct);
  });

  test('10. Web : relais joignable sans sonde Google', () async {
    final directPort = await unusedTcpPort();
    final relay = await TestHttpServer.start(
      (request, _) => writeJson(request, 200, {'route': 'relay'}),
    );
    final manager = NetworkFailoverManager(
      directBaseUrl: 'http://127.0.0.1:$directPort',
      relayBaseUrl: relay.baseUrl,
      useLocalProxy: false,
      webMode: true,
      internetProbe: () async => false,
      internetProbeCache: Duration.zero,
    );
    final dio = _client(manager);
    addTearDown(() async {
      dio.close(force: true);
      await manager.dispose();
      await relay.close();
    });

    final response = await dio.get<dynamic>('/api/v1/health/');

    expect(response.data['route'], 'relay');
    expect(manager.activeRoute, NetworkRoute.relay);
    final head = relay.requests.singleWhere(
      (request) => request.method == 'HEAD',
    );
    expect(head.header('authorization'), isNull);
    expect(
      relay.requests.where((request) => request.method == 'GET'),
      hasLength(1),
    );
  });

  test('11. Web : relais injoignable, erreur explicite', () async {
    final directPort = await unusedTcpPort();
    final relayPort = await unusedTcpPort();
    final manager = NetworkFailoverManager(
      directBaseUrl: 'http://127.0.0.1:$directPort',
      relayBaseUrl: 'http://127.0.0.1:$relayPort',
      useLocalProxy: false,
      webMode: true,
      internetProbe: () async => true,
      internetProbeCache: Duration.zero,
    );
    final dio = _client(manager);
    addTearDown(() async {
      dio.close(force: true);
      await manager.dispose();
    });

    DioException? caught;
    try {
      await dio.get<dynamic>('/api/v1/health/');
    } on DioException catch (error) {
      caught = error;
    }

    expect(caught, isNotNull);
    expect(
      (caught!.error as NetworkFailoverException).failure,
      NetworkFailoverFailure.connectivityUnconfirmed,
    );
    expect(manager.activeRoute, NetworkRoute.direct);
  });

  test('12. Web sans relais : noAlternateRoute immédiat', () async {
    final directPort = await unusedTcpPort();
    var probes = 0;
    final manager = NetworkFailoverManager(
      directBaseUrl: 'http://127.0.0.1:$directPort',
      useLocalProxy: false,
      webMode: true,
      internetProbe: () async {
        probes++;
        return true;
      },
    );
    final dio = _client(manager);
    addTearDown(() async {
      dio.close(force: true);
      await manager.dispose();
    });

    DioException? caught;
    try {
      await dio.get<dynamic>('/api/v1/health/');
    } on DioException catch (error) {
      caught = error;
    }

    expect(caught, isNotNull);
    expect(
      (caught!.error as NetworkFailoverException).failure,
      NetworkFailoverFailure.noAlternateRoute,
    );
    expect(manager.activeRoute, NetworkRoute.direct);
    expect(probes, 0);
  });
}

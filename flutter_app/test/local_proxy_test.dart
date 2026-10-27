import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';

import 'package:cnetp_app/core/network/local_proxy_service.dart';

import 'support/http_test_server.dart';

void main() {
  test('transmet méthodes, chemin, query, corps et Authorization', () async {
    final relay = await TestHttpServer.start((request, body) async {
      await writeJson(
        request,
        201,
        {
          'method': request.method,
          'path': request.uri.path,
          'query': request.uri.query,
          'authorization': request.headers.value('authorization'),
          'proxyKey': request.headers.value(LocalProxyConfig.accessKeyHeader),
          'body': utf8.decode(body),
        },
        headers: {'X-Relay': 'yes'},
      );
    });
    final proxy = createLocalProxy(
      LocalProxyConfig(upstreamBaseUrl: relay.baseUrl, port: 0),
    );
    addTearDown(() async {
      await proxy.stop();
      await relay.close();
    });
    final base = await proxy.start();

    expect(base.host, '127.0.0.1');
    for (final method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']) {
      final response = await sendHttp(
        Uri.parse('$base/api/v1/items/?page=2'),
        method,
        jsonBody: method == 'GET' ? null : {'method': method},
        headers: {
          LocalProxyConfig.accessKeyHeader: proxy.accessKey,
          'Authorization': 'Bearer secret',
        },
      );

      expect(response.statusCode, 201);
      final data = jsonDecode(response.bodyText) as Map<String, dynamic>;
      expect(data['method'], method);
      expect(data['path'], '/api/v1/items/');
      expect(data['query'], 'page=2');
      expect(data['authorization'], 'Bearer secret');
      expect(data['proxyKey'], isNull);
      if (method != 'GET') {
        expect(data['body'], contains('"method":"$method"'));
      }
      expect(response.headers['x-relay'], contains('yes'));
    }
  });

  test('refuse une requête sans clé locale', () async {
    final relay = await TestHttpServer.start(
      (request, _) => writeJson(request, 200, {'ok': true}),
    );
    final proxy = createLocalProxy(
      LocalProxyConfig(upstreamBaseUrl: relay.baseUrl, port: 0),
    );
    addTearDown(() async {
      await proxy.stop();
      await relay.close();
    });
    final base = await proxy.start();

    final response = await sendHttp(Uri.parse('$base/api/v1/private/'), 'GET');

    expect(response.statusCode, 403);
    expect(
      (jsonDecode(response.bodyText) as Map<String, dynamic>)['error_code'],
      'proxy_access_denied',
    );
    expect(relay.requests, isEmpty);
  });

  test('relais inaccessible : 502 explicite, pas de fausse réussite', () async {
    final relayPort = await unusedTcpPort();
    final proxy = createLocalProxy(
      LocalProxyConfig(
        upstreamBaseUrl: 'http://127.0.0.1:$relayPort',
        port: 0,
      ),
    );
    addTearDown(proxy.stop);
    final base = await proxy.start();

    final response = await sendHttp(
      Uri.parse('$base/api/v1/private/'),
      'GET',
      headers: {LocalProxyConfig.accessKeyHeader: proxy.accessKey},
    );

    expect(response.statusCode, 502);
    expect(
      (jsonDecode(response.bodyText) as Map<String, dynamic>)['error_code'],
      'upstream_unreachable',
    );
  });

  test('refuse un relais HTTP non loopback', () async {
    final proxy = createLocalProxy(
      const LocalProxyConfig(
        upstreamBaseUrl: 'http://relay.example.org',
        port: 0,
      ),
    );
    addTearDown(proxy.stop);

    await expectLater(proxy.start(), throwsA(isA<ArgumentError>()));
    expect(proxy.isRunning, isFalse);
  });

  test('démarrage idempotent et arrêt propre', () async {
    final relay = await TestHttpServer.start(
      (request, _) => writeJson(request, 200, {'ok': true}),
    );
    final proxy = createLocalProxy(
      LocalProxyConfig(upstreamBaseUrl: relay.baseUrl, port: 0),
    );
    addTearDown(() async {
      await proxy.stop();
      await relay.close();
    });

    final first = await proxy.start();
    final second = await proxy.start();
    expect(second, first);
    expect(proxy.isRunning, isTrue);

    await proxy.stop();
    expect(proxy.isRunning, isFalse);
    expect(proxy.baseUrl, isNull);

    final restarted = await proxy.start();
    expect(restarted.host, '127.0.0.1');
    expect(proxy.isRunning, isTrue);
  });
}

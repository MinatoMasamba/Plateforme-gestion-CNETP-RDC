import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:cnetp_app/core/api/api_client.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

class _Adapter implements HttpClientAdapter {
  final requests = <RequestOptions>[];
  bool denied = false;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? stream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options.copyWith(headers: Map.of(options.headers)));
    final expired = options.headers['Authorization'] == 'Bearer old';
    return ResponseBody.fromString(
      jsonEncode(
        denied
            ? {'detail': 'Accès refusé.'}
            : expired
            ? {'code': 'token_not_valid', 'detail': 'Jeton expiré.'}
            : {'ok': true},
      ),
      denied || expired ? 403 : 200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late _Adapter adapter;
  setUp(() {
    adapter = _Adapter();
    final original = ApiClient.dio.httpClientAdapter;
    final refresh = ApiClient.refreshAccessToken;
    final token = ApiClient.accessToken;
    ApiClient.dio.httpClientAdapter = adapter;
    ApiClient.accessToken = 'old';
    addTearDown(() {
      ApiClient.dio.httpClientAdapter = original;
      ApiClient.refreshAccessToken = refresh;
      ApiClient.accessToken = token;
    });
  });

  test(
    'Expired GED token refreshes once and preserves selected period',
    () async {
      var refreshes = 0;
      ApiClient.refreshAccessToken = () async {
        refreshes++;
        ApiClient.accessToken = 'fresh';
        return true;
      };
      final result = await ApiClient.dio.get(
        '/api/v1/st/ged/',
        queryParameters: {'days': 90},
      );
      expect(result.data['ok'], true);
      expect(refreshes, 1);
      expect(adapter.requests.last.queryParameters['days'], 90);
      expect(adapter.requests.last.headers['Authorization'], 'Bearer fresh');
    },
  );

  test('Binary exports also renew expired authentication', () async {
    ApiClient.refreshAccessToken = () async {
      ApiClient.accessToken = 'fresh';
      return true;
    };
    final result = await ApiClient.dio.get<List<int>>(
      '/api/v1/st/reports/5/export/',
      queryParameters: {'file_format': 'pdf', 'revision': 2},
      options: Options(responseType: ResponseType.bytes),
    );
    expect(result.data, isNotEmpty);
    expect(adapter.requests.last.headers['Authorization'], 'Bearer fresh');
    expect(adapter.requests.last.queryParameters['revision'], 2);
  });

  test('A genuine permission denial does not refresh or retry', () async {
    adapter.denied = true;
    var refreshes = 0;
    ApiClient.refreshAccessToken = () async {
      refreshes++;
      return true;
    };
    await expectLater(
      ApiClient.dio.get('/api/v1/st/ged/'),
      throwsA(isA<DioException>()),
    );
    expect(refreshes, 0);
    expect(adapter.requests, hasLength(1));
  });

  test('Concurrent expired requests share one refresh', () async {
    final ready = Completer<bool>();
    var refreshes = 0;
    ApiClient.refreshAccessToken = () {
      refreshes++;
      return ready.future;
    };
    final first = ApiClient.dio.get('/api/v1/st/ged/');
    final second = ApiClient.dio.get('/api/v1/st/ged/queue/');
    while (adapter.requests.length < 2 || refreshes == 0) {
      await Future<void>.delayed(Duration.zero);
    }
    ApiClient.accessToken = 'fresh';
    ready.complete(true);
    await Future.wait([first, second]);
    expect(refreshes, 1);
  });

  test('Refresh request never carries the expired access token', () async {
    await ApiClient.dio.post(
      '/api/v1/mobile/auth/refresh/',
      data: {'refresh': 'refresh-token'},
    );
    expect(adapter.requests.single.headers.containsKey('Authorization'), false);
  });
}

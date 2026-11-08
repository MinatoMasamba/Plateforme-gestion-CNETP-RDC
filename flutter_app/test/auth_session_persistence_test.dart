import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:cnetp_app/core/api/api_client.dart';
import 'package:cnetp_app/core/auth/auth_controller.dart';
import 'package:cnetp_app/core/auth/session.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

const stored = Session(
  access: 'old',
  refresh: 'refresh-old',
  userId: 1,
  email: 'ctc@example.test',
  fullName: 'CTC',
  userType: 'CTC',
  space: 'ctc',
  isCtc: true,
);

class _AuthAdapter implements HttpClientAdapter {
  int refreshes = 0;
  bool offline = false;
  bool failBootstrapAfterRefresh = false;
  bool invalidRefresh = false;
  final refreshFinished = Completer<void>();

  ResponseBody json(Map<String, dynamic> body, [int status = 200]) =>
      ResponseBody.fromString(
        jsonEncode(body),
        status,
        headers: {
          Headers.contentTypeHeader: [Headers.jsonContentType],
        },
      );

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? stream,
    Future<void>? cancelFuture,
  ) async {
    if (offline) {
      throw DioException(
        requestOptions: options,
        type: DioExceptionType.connectionError,
      );
    }
    if (options.path.endsWith('/refresh/')) {
      refreshes++;
      await Future<void>.delayed(const Duration(milliseconds: 20));
      if (!refreshFinished.isCompleted) refreshFinished.complete();
      return invalidRefresh
          ? json({'code': 'token_not_valid'}, 401)
          : json({'access': 'fresh', 'refresh': 'refresh-rotated'});
    }
    if (options.path.endsWith('/logout/')) return json({});
    if (options.headers['Authorization'] == 'Bearer old') {
      return json({'code': 'token_not_valid'}, 403);
    }
    if (options.path.endsWith('/bootstrap/')) {
      if (failBootstrapAfterRefresh) {
        return json({'detail': 'Indisponible'}, 503);
      }
      return json({'space': 'ctc', 'is_ctc': true});
    }
    return json({'ok': true});
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _AuthAdapter adapter;
  setUp(() {
    SharedPreferences.setMockInitialValues({
      'cnetp_session': jsonEncode(stored.toJson()),
    });
    adapter = _AuthAdapter();
    final original = ApiClient.dio.httpClientAdapter;
    final callback = ApiClient.refreshAccessToken;
    final token = ApiClient.accessToken;
    ApiClient.dio.httpClientAdapter = adapter;
    addTearDown(() {
      ApiClient.dio.httpClientAdapter = original;
      ApiClient.refreshAccessToken = callback;
      ApiClient.accessToken = token;
    });
  });

  test(
    'Reload restores session and shares refresh with concurrent GED reads',
    () async {
      final initial = await AuthController.loadInitialState();
      expect(initial.status, AuthStatus.authenticated);
      final controller = AuthController(initialState: initial);
      addTearDown(controller.dispose);
      await Future.wait([
        ApiClient.dio.get('/api/v1/st/ged/', queryParameters: {'days': 7}),
        ApiClient.dio.get('/api/v1/st/ged/queue/'),
      ]);
      expect(adapter.refreshes, 1);
      expect(controller.state.status, AuthStatus.authenticated);
      final restored = await AuthController.loadInitialState();
      expect(restored.session?.access, 'fresh');
      expect(restored.session?.refresh, 'refresh-rotated');
      final reloadedController = AuthController(initialState: restored);
      await Future<void>.delayed(const Duration(milliseconds: 30));
      expect(reloadedController.state.status, AuthStatus.authenticated);
      expect(adapter.refreshes, 1);
      reloadedController.dispose();
    },
  );

  test('Offline startup keeps persisted session', () async {
    adapter.offline = true;
    final controller = AuthController(
      initialState: await AuthController.loadInitialState(),
    );
    await Future<void>.delayed(const Duration(milliseconds: 30));
    expect(controller.state.status, AuthStatus.authenticated);
    expect(
      (await AuthController.loadInitialState()).session?.refresh,
      'refresh-old',
    );
    controller.dispose();
  });

  test('Rotated refresh survives a temporary bootstrap failure', () async {
    adapter.failBootstrapAfterRefresh = true;
    final controller = AuthController(
      initialState: await AuthController.loadInitialState(),
    );
    addTearDown(controller.dispose);
    await ApiClient.dio.get('/api/v1/st/ged/');
    expect(controller.state.status, AuthStatus.authenticated);
    expect(
      (await AuthController.loadInitialState()).session?.refresh,
      'refresh-rotated',
    );
  });

  test('Rejected refresh still requires a new login', () async {
    adapter.invalidRefresh = true;
    final controller = AuthController(
      initialState: await AuthController.loadInitialState(),
    );
    final signedOut = Completer<void>();
    controller.addListener((state) {
      if (state.status == AuthStatus.unauthenticated && !signedOut.isCompleted) {
        signedOut.complete();
      }
    });
    await signedOut.future.timeout(const Duration(seconds: 5));
    expect(controller.state.status, AuthStatus.unauthenticated);
    expect(
      (await AuthController.loadInitialState()).status,
      AuthStatus.unauthenticated,
    );
    controller.dispose();
  });
}

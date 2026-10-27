import 'dart:convert';
import 'dart:io';

typedef TestHttpHandler =
    Future<void> Function(HttpRequest request, List<int> body);

class CapturedRequest {
  CapturedRequest({
    required this.method,
    required this.uri,
    required this.headers,
    required this.body,
  });

  final String method;
  final Uri uri;
  final Map<String, List<String>> headers;
  final List<int> body;

  String? header(String name) {
    final values = headers[name.toLowerCase()];
    return values == null || values.isEmpty ? null : values.first;
  }

  String get bodyText => utf8.decode(body);
}

class TestHttpResponse {
  TestHttpResponse({
    required this.statusCode,
    required this.headers,
    required this.body,
  });

  final int statusCode;
  final Map<String, List<String>> headers;
  final List<int> body;

  String get bodyText => utf8.decode(body);
}

class TestHttpServer {
  TestHttpServer._(this._server, this._handler);

  final HttpServer _server;
  final TestHttpHandler _handler;
  final List<CapturedRequest> requests = [];

  static Future<TestHttpServer> start(
    TestHttpHandler handler, {
    int port = 0,
  }) async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, port);
    final result = TestHttpServer._(server, handler);
    server.listen(result._handle);
    return result;
  }

  int get port => _server.port;

  String get baseUrl => 'http://127.0.0.1:${_server.port}';

  Future<void> _handle(HttpRequest request) async {
    final body = await request.fold<List<int>>(
      <int>[],
      (buffer, chunk) => buffer..addAll(chunk),
    );
    final headers = <String, List<String>>{};
    request.headers.forEach((name, values) {
      headers[name.toLowerCase()] = List<String>.from(values);
    });
    requests.add(
      CapturedRequest(
        method: request.method,
        uri: request.uri,
        headers: headers,
        body: body,
      ),
    );

    try {
      await _handler(request, body);
    } catch (_) {
      try {
        request.response.statusCode = HttpStatus.internalServerError;
        await request.response.close();
      } catch (_) {
        // La réponse est peut-être déjà fermée.
      }
    }
  }

  Future<void> close() => _server.close(force: true);
}

Future<void> writeJson(
  HttpRequest request,
  int status,
  Object body, {
  Map<String, String>? headers,
}) async {
  request.response.statusCode = status;
  request.response.headers.contentType = ContentType.json;
  headers?.forEach((name, value) {
    request.response.headers.set(name, value);
  });
  request.response.write(jsonEncode(body));
  await request.response.close();
}

Future<int> unusedTcpPort() async {
  final socket = await ServerSocket.bind(InternetAddress.loopbackIPv4, 0);
  final port = socket.port;
  await socket.close();
  return port;
}

Future<TestHttpResponse> sendHttp(
  Uri uri,
  String method, {
  Object? jsonBody,
  List<int>? body,
  Map<String, String>? headers,
}) async {
  final client = HttpClient()..findProxy = (_) => 'DIRECT';
  try {
    final request = await client.openUrl(method, uri);
    headers?.forEach(request.headers.set);
    if (jsonBody != null) {
      request.headers.contentType = ContentType.json;
      request.write(jsonEncode(jsonBody));
    } else if (body != null) {
      request.add(body);
    }
    final response = await request.close();
    final responseBody = await response.fold<List<int>>(
      <int>[],
      (buffer, chunk) => buffer..addAll(chunk),
    );
    final responseHeaders = <String, List<String>>{};
    response.headers.forEach((name, values) {
      responseHeaders[name.toLowerCase()] = List<String>.from(values);
    });
    return TestHttpResponse(
      statusCode: response.statusCode,
      headers: responseHeaders,
      body: responseBody,
    );
  } finally {
    client.close(force: true);
  }
}

import 'local_proxy_contract.dart';

/// Sur le Web, Flutter ne peut pas ouvrir de serveur HTTP local.
LocalProxyService createLocalProxy(LocalProxyConfig _) =>
    const _UnsupportedLocalProxyService();

class _UnsupportedLocalProxyService implements LocalProxyService {
  const _UnsupportedLocalProxyService();

  @override
  bool get isRunning => false;

  @override
  String? get baseUrl => null;

  @override
  String get accessKey => '';

  @override
  Future<Uri> start() async {
    throw UnsupportedError(
      'Le proxy local Dart est indisponible sur le Web. '
      'Configurez un relais HTTPS avec API_RELAY_BASE_URL.',
    );
  }

  @override
  Future<void> stop() async {}
}

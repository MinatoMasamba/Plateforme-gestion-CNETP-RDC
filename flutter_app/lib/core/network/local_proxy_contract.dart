/// Contrat commun du proxy local, partagé par l'implémentation native et le
/// stub utilisé sur le Web.
class LocalProxyConfig {
  const LocalProxyConfig({
    required this.upstreamBaseUrl,
    this.port = 8080,
    this.upstreamTimeout = const Duration(seconds: 30),
    this.startupTimeout = const Duration(seconds: 5),
  });

  /// En-tête secret propre à l'instance, exigé par le proxy local.
  static const String accessKeyHeader = 'X-CNEP-Proxy-Key';

  /// Base du relais HTTPS distant, par exemple `https://relay.example.org`.
  ///
  /// Le proxy ne se connecte jamais directement à l'API Django : sans relais
  /// alternatif, il ne pourrait pas contourner un blocage réseau.
  final String upstreamBaseUrl;

  /// Port d'écoute loopback. `0` choisit un port libre (utile aux tests).
  final int port;

  final Duration upstreamTimeout;
  final Duration startupTimeout;
}

/// Interface minimale du proxy local.
abstract interface class LocalProxyService {
  bool get isRunning;

  /// URL loopback effective, par exemple `http://127.0.0.1:8080`.
  String? get baseUrl;

  /// Secret à envoyer dans [LocalProxyConfig.accessKeyHeader].
  String get accessKey;

  Future<Uri> start();

  Future<void> stop();
}

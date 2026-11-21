import 'dart:convert';
import 'dart:io';

import 'package:cnetp_app/core/network/local_proxy_service.dart';

Future<void> main(List<String> args) async {
  String option(String name, String fallback) {
    final index = args.indexOf(name);
    return index >= 0 ? args[index + 1] : fallback;
  }

  final count = int.parse(option('--samples', '10')).clamp(5, 50);
  final upstream = option(
    '--upstream',
    'https://workalldomain.pythonanywhere.com',
  );
  final path = option('--path', '/api/v1/mobile/public/published_norms/');
  if (!path.startsWith('/api/') || path.contains('?')) {
    throw ArgumentError('Utilisez un chemin API public sans paramètres.');
  }
  final proxy = createLocalProxy(
    LocalProxyConfig(upstreamBaseUrl: upstream, port: 0),
  );
  final client = HttpClient()..connectionTimeout = const Duration(seconds: 15);
  final times = <String, List<double>>{'direct': [], 'local_proxy': []};
  var responseBytes = 0;
  String? reference;
  try {
    final local = await proxy.start();
    for (var sample = -2; sample < count; sample++) {
      for (final route in times.keys) {
        final timer = Stopwatch()..start();
        final base = route == 'direct' ? upstream : '$local';
        final request = await client.getUrl(Uri.parse('$base$path'));
        request.headers.set('Accept', 'application/json');
        if (route == 'local_proxy') {
          request.headers.set(
            LocalProxyConfig.accessKeyHeader,
            proxy.accessKey,
          );
        }
        final response = await request.close().timeout(
          const Duration(seconds: 30),
        );
        final bytes = await response.fold<List<int>>(
          [],
          (all, chunk) => all..addAll(chunk),
        );
        timer.stop();
        if (response.statusCode != 200) {
          throw StateError('$route : HTTP ${response.statusCode}');
        }
        final encoded = base64Encode(bytes);
        reference ??= encoded;
        if (encoded != reference) {
          throw StateError('Réponses direct/proxy différentes.');
        }
        responseBytes = bytes.length;
        if (sample >= 0) times[route]!.add(timer.elapsedMicroseconds / 1000);
      }
    }
    Map<String, dynamic> summarize(List<double> values) {
      final sorted = [...values]..sort();
      return {
        'samples': sorted.length,
        'mean_ms': values.reduce((a, b) => a + b) / values.length,
        'median_ms': sorted[sorted.length ~/ 2],
        'p95_ms':
            sorted[((sorted.length * .95).ceil() - 1).clamp(
              0,
              sorted.length - 1,
            )],
      };
    }

    final report = {
      'time_utc': DateTime.now().toUtc().toIso8601String(),
      'upstream': upstream,
      'path': path,
      'response_bytes': responseBytes,
      'scope':
          'Comparaison direct et proxy local vers le même serveur ; aucun relais alternatif distinct testé.',
      'identical_responses': true,
      'routes': {
        for (final entry in times.entries) entry.key: summarize(entry.value),
      },
    };
    final result = const JsonEncoder.withIndent('  ').convert(report);
    final output = File(
      option('--output', '../reports/expert_beta/proxy_benchmark.json'),
    );
    await output.parent.create(recursive: true);
    await output.writeAsString('$result\n');
    stdout.writeln(result);
  } finally {
    client.close(force: true);
    await proxy.stop();
  }
}

import 'package:cnetp_app/core/diagnostics/client_diagnostics.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  setUp(() {
    ClientDiagnostics.clear();
    ClientDiagnostics.sender = null;
    ClientDiagnostics.authenticated = () => true;
  });
  tearDown(() {
    ClientDiagnostics.clear();
    ClientDiagnostics.sender = null;
    ClientDiagnostics.authenticated = null;
  });

  test('file bornée en mémoire, expurgation et déduplication', () async {
    final sent = <Map<String, dynamic>>[];
    ClientDiagnostics.authenticated = () => false;
    ClientDiagnostics.sender = (data) async => sent.add(data);
    final message = 'password=private_value Bearer private_bearer me@example.test https://example.org/?token=private_token';
    ClientDiagnostics.report('flutter', message);
    ClientDiagnostics.report('flutter', message);
    expect(sent, isEmpty);
    ClientDiagnostics.authenticated = () => true;
    await ClientDiagnostics.flush();
    expect(sent, hasLength(1));
    for (final secret in ['private_value', 'private_bearer', 'private_token', 'me@example.test']) {
      expect(sent.single['message'], isNot(contains(secret)));
    }
    ClientDiagnostics.clear();
    ClientDiagnostics.authenticated = () => false;
    for (var i = 0; i < 30; i++) {
      ClientDiagnostics.report('flutter', 'Incident $i');
    }
    ClientDiagnostics.authenticated = () => true;
    await ClientDiagnostics.flush();
    expect(sent, hasLength(21));
  });

  test('une panne du journal ne produit pas une boucle de requêtes', () async {
    var attempts = 0;
    ClientDiagnostics.sender = (_) async {
      attempts++;
      throw StateError('Journal indisponible');
    };
    ClientDiagnostics.report('flutter', 'Incident unique');
    await Future<void>.delayed(Duration.zero);
    await ClientDiagnostics.flush();
    await ClientDiagnostics.flush();
    expect(attempts, 1);
    ClientDiagnostics.clear();
    final sent = <Map<String, dynamic>>[];
    ClientDiagnostics.sender = (data) async => sent.add(data);
    await ClientDiagnostics.flush();
    expect(sent, isEmpty);
  });
}

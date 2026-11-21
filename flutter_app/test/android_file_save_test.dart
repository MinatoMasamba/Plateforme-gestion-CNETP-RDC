import 'package:cnetp_app/core/files/android_file_save.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('cd.cneitp.expert/files');
  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
  });
  test('transmet le document au dialogue natif Android', () async {
    MethodCall? request;
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
          request = call;
          return true;
        });
    final bytes = Uint8List.fromList([1, 2, 3]);
    expect(await saveAndroidFile(bytes, 'invitation.ics'), isTrue);
    expect(request?.method, 'saveFile');
    expect(request?.arguments['name'], 'invitation.ics');
    expect(request?.arguments['bytes'], bytes);
  });
  test('annuler ne déclare pas le fichier enregistré', () async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (_) async => false);
    expect(await saveAndroidFile(Uint8List(0), 'annule.pdf'), isFalse);
  });
}

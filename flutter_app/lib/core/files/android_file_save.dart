import 'package:flutter/services.dart';

Future<bool> saveAndroidFile(Uint8List bytes, String name) async {
  return await const MethodChannel(
        'cd.cneitp.expert/files',
      ).invokeMethod<bool>('saveFile', {'name': name, 'bytes': bytes}) ??
      false;
}

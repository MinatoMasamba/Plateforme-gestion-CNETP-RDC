import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/foundation.dart';

import '../../../core/api/api_client.dart';
import '../../../core/files/android_file_save.dart';

Future<void> expertDownload(String path, String name) async {
  final response = await ApiClient.dio.get<List<int>>(
    path,
    options: Options(responseType: ResponseType.bytes),
  );
  final bytes = Uint8List.fromList(response.data ?? []);
  if (kIsWeb) {
    await XFile.fromData(bytes, name: name).saveTo(name);
  } else if (defaultTargetPlatform == TargetPlatform.android) {
    if (!await saveAndroidFile(bytes, name)) {
      throw StateError('Enregistrement annulé.');
    }
  } else {
    final location = await getSaveLocation(suggestedName: name);
    if (location != null) {
      await XFile.fromData(bytes, name: name).saveTo(location.path);
    }
  }
}

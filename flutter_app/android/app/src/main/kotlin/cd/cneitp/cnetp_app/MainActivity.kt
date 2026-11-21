package cd.cneitp.cnetp_app

import android.app.Activity
import android.content.Intent
import android.webkit.MimeTypeMap
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private var pendingSave: MethodChannel.Result? = null
    private var pendingBytes: ByteArray? = null
    private val saveRequestCode = 4172

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "cd.cneitp.expert/files")
            .setMethodCallHandler { call, result ->
                if (call.method != "saveFile") {
                    result.notImplemented()
                } else if (pendingSave != null) {
                    result.error("SAVE_BUSY", "Un enregistrement est déjà en cours.", null)
                } else {
                    val bytes = call.argument<ByteArray>("bytes")
                    val name = call.argument<String>("name")?.substringAfterLast('/')?.substringAfterLast('\\')
                    if (bytes == null || name.isNullOrBlank()) {
                        result.error("SAVE_ARGUMENTS", "Nom ou fichier manquant.", null)
                    } else {
                        pendingSave = result
                        pendingBytes = bytes
                        val mime = MimeTypeMap.getSingleton().getMimeTypeFromExtension(name.substringAfterLast('.', "").lowercase())
                            ?: "application/octet-stream"
                        try {
                            startActivityForResult(Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
                                addCategory(Intent.CATEGORY_OPENABLE)
                                type = mime
                                putExtra(Intent.EXTRA_TITLE, name)
                            }, saveRequestCode)
                        } catch (_: Exception) {
                            pendingSave = null
                            pendingBytes = null
                            result.error("SAVE_UNAVAILABLE", "Le dialogue d’enregistrement est indisponible.", null)
                        }
                    }
                }
            }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != saveRequestCode) return
        val result = pendingSave ?: return
        val bytes = pendingBytes
        pendingSave = null
        pendingBytes = null
        val uri = data?.data
        if (resultCode != Activity.RESULT_OK || uri == null || bytes == null) {
            result.success(false)
            return
        }
        Thread {
            try {
                val stream = contentResolver.openOutputStream(uri)
                    ?: throw IllegalStateException("Fichier inaccessible")
                stream.use { it.write(bytes) }
                runOnUiThread { result.success(true) }
            } catch (_: Exception) {
                runOnUiThread { result.error("SAVE_FAILED", "Impossible d’enregistrer le fichier.", null) }
            }
        }.start()
    }
}

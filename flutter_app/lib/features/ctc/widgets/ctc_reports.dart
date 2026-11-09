import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:flutter_quill/flutter_quill.dart' as quill;
import 'report_fixed_editor.dart';
import 'report_cover_editor.dart';
import 'report_tables_editor.dart';

import '../../../core/api/api_client.dart';
import '../../../theme/app_colors.dart';
import 'ged_shared.dart';

typedef ReportFileSaver =
    Future<void> Function(Uint8List bytes, String name, String mime);

class _Section {
  _Section(Map<String, dynamic> data)
    : title = TextEditingController(text: '${data['title'] ?? ''}'),
      content = TextEditingController(text: '${data['content'] ?? ''}'),
      rich = quill.QuillController(
        document: data['delta'] is List
            ? quill.Document.fromJson(data['delta'] as List)
            : (quill.Document()..insert(0, '${data['content'] ?? ''}')),
        selection: const TextSelection.collapsed(offset: 0),
      );
  final TextEditingController title;
  final TextEditingController content;
  final quill.QuillController rich;
  bool formatted = false;
  Map<String, dynamic> get data => {
    'title': title.text.trim(),
    'content': formatted
        ? rich.document.toPlainText().replaceFirst(RegExp(r'\n$'), '')
        : content.text,
    if (formatted) 'delta': rich.document.toDelta().toJson(),
  };
  void dispose() {
    title.dispose();
    content.dispose();
    rich.dispose();
  }
}

/// Reports use the same versioned ST API as the HTML editor.
class CtcReportsView extends StatefulWidget {
  const CtcReportsView({super.key, this.client, this.saveFile});
  final Dio? client;
  final ReportFileSaver? saveFile;
  @override
  State<CtcReportsView> createState() => _CtcReportsViewState();
}

class _CtcReportsViewState extends State<CtcReportsView> {
  Dio get _api => widget.client ?? ApiClient.dio;
  final _title = TextEditingController();
  final _start = TextEditingController();
  final _end = TextEditingController();
  final _modelName = TextEditingController();
  final _sendBody = TextEditingController(
    text: 'Veuillez trouver ci-joint le rapport sélectionné.',
  );
  List<Map<String, dynamic>> _targets = [];
  String? _target, _sendKey, _targetError;
  List<_Section> _sections = [];
  List<Map<String, dynamic>> _reports = [], _templates = [];
  Map<String, dynamic>? _current;
  int? _version, _template, _sourceId;
  Map<String, dynamic>? _source;
  String _mode = 'free';
  Map<String, dynamic> _cover = {};
  int _sourceStart = 0;
  final _modelImages = <int, Future<Uint8List>>{};
  List<Map<String, dynamic>> _fields = [];
  Map<String, dynamic> get _document => {
    'mode': _mode,
    'fields': _fields,
    'cover': _cover,
    'source_start_page': _sourceStart,
  };
  bool _loading = true,
      _busy = false,
      _editing = false,
      _dirty = false,
      _mine = false;
  String? _message, _error;
  bool get _historical => _current != null && _version != _current!['revision'];
  List<Map<String, dynamic>> get _sectionData =>
      _sections.map((s) => s.data).toList();

  @override
  void initState() {
    super.initState();
    _load();
    _loadTargets();
  }

  @override
  void dispose() {
    for (final c in [_title, _start, _end, _modelName, _sendBody]) {
      c.dispose();
    }
    for (final section in _sections) {
      section.dispose();
    }
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final results = await Future.wait([
        _api.get('/api/v1/st/reports/'),
        _api.get('/api/v1/st/reports/templates/'),
      ]);
      if (!mounted) return;
      setState(() {
        _reports = rowsOf(results[0].data['results']);
        _templates = rowsOf(results[1].data['results']);
      });
    } catch (error) {
      _showError(error);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadTargets() async {
    try {
      final response = await _api.get('/api/v1/communications/targets/');
      if (!mounted) return;
      setState(() {
        _targets = rowsOf(response.data['results']);
        _targetError = null;
      });
    } catch (_) {
      if (mounted) {
        setState(() => _targetError = 'Destinataires indisponibles.');
      }
    }
  }

  String _newRequestKey() {
    final random = Random.secure();
    final bytes = List<int>.generate(16, (_) => random.nextInt(256));
    bytes[6] = (bytes[6] & 15) | 64;
    bytes[8] = (bytes[8] & 63) | 128;
    final hex = bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
    return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}';
  }

  Future<void> _send() async {
    if (_target == null || _current == null || _dirty || _busy) return;
    final target = _targets.firstWhere(
      (t) => '${t['type']}:${t['id']}' == _target,
    );
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Transmettre le rapport'),
        content: Text(
          'Joindre la version $_version en PDF à ${target['type']} ${target['code']} pour ${target['recipient_count']} membre(s) confirmé(s) ? La plateforme transmettra également la notification par e-mail.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Confirmer la transmission'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    _sendKey ??= _newRequestKey();
    try {
      final response = await _api.post(
        '/api/v1/st/reports/${_current!['id']}/send/',
        data: {
          'revision': _version,
          'body': _sendBody.text,
          'request_key': _sendKey,
          target['type'] == 'GT' ? 'gt_id' : 'sc_id': target['id'],
        },
      );
      final updated = await _api.get('/api/v1/st/reports/${_current!['id']}/');
      if (!mounted) return;
      setState(() {
        _sendKey = null;
        _current = (updated.data as Map).cast<String, dynamic>();
        _reports = [
          _current!,
          ..._reports.where((r) => r['id'] != _current!['id']),
        ];
        _message =
            'Envoi enregistré pour ${response.data['recipient_count']} destinataire(s). Consultez le suivi de transmission.';
      });
    } catch (error) {
      _showError(error);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _track(Map<String, dynamic> dispatch) async {
    try {
      final response = await _api.get(
        '/api/v1/communications/${dispatch['id']}/',
      );
      if (!mounted) return;
      final data = response.data as Map;
      final counts = <String, int>{};
      for (final row in rowsOf(data['recipients'])) {
        final status = '${row['email_status']}';
        counts[status] = (counts[status] ?? 0) + 1;
      }
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Suivi de la transmission'),
          content: Text(
            '${data['recipient_count']} destinataire(s).\nE-mails acceptés : ${counts['SENT'] ?? 0}\nEn échec : ${counts['FAILED'] ?? 0}\nEn attente : ${(counts['PENDING'] ?? 0) + (counts['SENDING'] ?? 0)}\nNon envoyés : ${counts['SKIPPED'] ?? 0}',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Fermer le suivi'),
            ),
          ],
        ),
      );
    } catch (error) {
      _showError(error);
    }
  }

  void _showError(Object error) {
    if (!mounted) return;
    setState(
      () => _error = error is DioException
          ? errorDetail(error) ?? 'Le serveur a refusé cette opération.'
          : '$error'.replaceFirst('FormatException: ', ''),
    );
  }

  void _replaceSections(List<Map<String, dynamic>> sections) {
    // Old text fields can still be mounted until the next frame.
    final previous = _sections;
    _sections = sections.map(_Section.new).toList();
    for (final section in _sections) {
      section.formatted =
          _sourceId != null ||
          section.data.containsKey('delta') ||
          sections[_sections.indexOf(section)]['delta'] != null;
      section.rich.addListener(() {
        if (mounted && section.formatted && !section.rich.readOnly) {
          setState(() => _dirty = true);
        }
      });
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      for (final s in previous) {
        s.dispose();
      }
    });
  }

  Future<bool> _discard() async {
    if (!_dirty) return true;
    return await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Modifications non enregistrées'),
            content: const Text(
              'Quitter cette rédaction et abandonner les modifications ?',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Continuer la rédaction'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Abandonner les modifications'),
              ),
            ],
          ),
        ) ??
        false;
  }

  void _fill(Map<String, dynamic>? report, Map<String, dynamic> version) {
    setState(() {
      _sourceId = (version['source_id'] as num?)?.toInt();
      _source = null;
      final doc = version['document'] as Map?;
      _mode = '${doc?['mode'] ?? 'free'}';
      _cover = (jsonDecode(jsonEncode(doc?['cover'] ?? {})) as Map)
          .cast<String, dynamic>();
      _sourceStart = (doc?['source_start_page'] as num?)?.toInt() ?? 0;
      _fields = rowsOf(
        doc?['fields'],
      ).map((f) => Map<String, dynamic>.from(f)).toList();
      _current = report;
      _sendKey = null;
      _version = (version['number'] as num?)?.toInt();
      _template = (report?['template_id'] as num?)?.toInt();
      _title.text = '${version['title'] ?? ''}';
      _start.text = '${version['period_start'] ?? ''}';
      _end.text = '${version['period_end'] ?? ''}';
      _replaceSections(rowsOf(version['sections']));
      _editing = true;
      _dirty = false;
      _error = null;
      _message = null;
    });
    if (_sourceId != null) _loadSource(_sourceId!);
  }

  Future<void> _loadSource(int id) async {
    try {
      final result = await _api.get('/api/v1/st/reports/sources/$id/');
      if (mounted && _sourceId == id) {
        setState(() => _source = (result.data as Map).cast<String, dynamic>());
      }
    } catch (error) {
      _showError(error);
    }
  }

  Future<String?> _chooseMode() => showDialog<String>(
    context: context,
    builder: (context) => SimpleDialog(
      title: const Text('Comment utiliser ce document ?'),
      children: [
        SimpleDialogOption(
          onPressed: () => Navigator.pop(context, 'fixed'),
          child: const ListTile(
            leading: Icon(Icons.edit_document),
            title: Text('Conserver la présentation'),
            subtitle: Text(
              'Ajouter des champs sur les pages du modèle original.',
            ),
          ),
        ),
        SimpleDialogOption(
          onPressed: () => Navigator.pop(context, 'free'),
          child: const ListTile(
            leading: Icon(Icons.format_align_left),
            title: Text('Rédaction libre'),
            subtitle: Text(
              'Reprendre le texte et modifier la structure et la mise en forme.',
            ),
          ),
        ),
        SimpleDialogOption(
          onPressed: () => Navigator.pop(context),
          child: const Text('Annuler'),
        ),
      ],
    ),
  );

  Future<void> _useModel(Map<String, dynamic> model) async {
    if (!await _discard() || !mounted) return;
    final sourceId = (model['source_id'] as num?)?.toInt();
    final mode = sourceId == null ? 'free' : await _chooseMode();
    if (mode == null || !mounted) return;
    _fill(null, {
      'title': '${model['name']}'.replaceAll('_', ' '),
      'sections': model['sections'],
      'source_id': sourceId,
      'document': {
        ...?model['document'] as Map?,
        'mode': mode,
        'fields': model['document']?['fields'] ?? [],
      },
    });
    setState(() {
      _template = (model['id'] as num).toInt();
      _dirty = true;
    });
  }

  Future<void> _new() async {
    if (!await _discard() || !mounted) return;
    _fill(null, {
      'sections': [
        {'title': 'Objet', 'content': ''},
      ],
    });
  }

  Future<void> _open(Map<String, dynamic> report) async {
    if (!await _discard() || !mounted) return;
    final versions = rowsOf(report['versions']);
    if (versions.isEmpty) return;
    _fill(
      report,
      versions.firstWhere(
        (v) => v['number'] == report['revision'],
        orElse: () => versions.first,
      ),
    );
  }

  String? _validation() {
    if (_title.text.trim().length > 250) {
      return 'Titre limité à 250 caractères.';
    }
    if (_sections.any((s) => s.title.text.trim().length > 150)) {
      return 'Titre de section limité à 150 caractères.';
    }
    if (_title.text.trim().isEmpty) return 'Le titre du rapport est requis.';
    if (_sections.isEmpty || _sections.length > 20) {
      return 'Prévoir entre une et vingt sections.';
    }
    if (_sections.any((s) => s.title.text.trim().isEmpty)) {
      return 'Chaque section doit avoir un titre.';
    }
    if (_sectionData.fold<int>(
          0,
          (sum, s) => sum + (s['content'] as String).length,
        ) >
        100000) {
      return 'Le rapport dépasse 100 000 caractères.';
    }
    for (final date in [_start.text, _end.text]) {
      if (date.isNotEmpty &&
          (DateTime.tryParse(date) == null ||
              !RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(date))) {
        return 'Dates au format AAAA-MM-JJ attendues.';
      }
    }
    if (_start.text.isNotEmpty &&
        _end.text.isNotEmpty &&
        _start.text.compareTo(_end.text) > 0) {
      return 'La fin de période doit suivre le début.';
    }
    return null;
  }

  Future<void> _save() async {
    final error = _validation();
    if (error != null) {
      setState(() => _error = error);
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final response = await _api.post(
        _current == null
            ? '/api/v1/st/reports/'
            : '/api/v1/st/reports/${_current!['id']}/revise/',
        data: {
          'title': _title.text.trim(),
          'sections': _sectionData,
          'template_id': _template,
          'source_id': _sourceId,
          'document': _document,
          'period_start': _start.text.isEmpty ? null : _start.text,
          'period_end': _end.text.isEmpty ? null : _end.text,
          if (_current != null) 'revision': _current!['revision'],
        },
      );
      if (!mounted) return;
      final report = (response.data as Map).cast<String, dynamic>();
      final versions = rowsOf(report['versions']);
      _fill(
        report,
        versions.firstWhere((v) => v['number'] == report['revision']),
      );
      setState(() {
        _reports = [report, ..._reports.where((r) => r['id'] != report['id'])];
        _message =
            'Rapport enregistré — version ${report['revision']}. Aucun envoi effectué.';
      });
    } catch (error) {
      _showError(error);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _export(String format) async {
    final report = _current;
    if (report == null || _version == null) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final response = await _api.get<List<int>>(
        '/api/v1/st/reports/${report['id']}/export/',
        queryParameters: {'file_format': format, 'revision': _version},
        options: Options(responseType: ResponseType.bytes),
      );
      final bytes = Uint8List.fromList(response.data ?? []);
      if (bytes.isEmpty) {
        throw const FormatException('Le serveur a renvoyé un fichier vide.');
      }
      final name = '${report['reference']}-v$_version.$format';
      final mime = format == 'pdf'
          ? 'application/pdf'
          : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      if (widget.saveFile != null) {
        await widget.saveFile!(bytes, name, mime);
      } else {
        final location = await getSaveLocation(suggestedName: name);
        if (location == null) return;
        await XFile.fromData(
          bytes,
          name: name,
          mimeType: mime,
        ).saveTo(location.path);
      }
      if (mounted) {
        setState(
          () => _message =
              'Export de la version $_version téléchargé${_dirty ? ' : les modifications non enregistrées ne sont pas incluses.' : '.'}',
        );
      }
    } catch (error) {
      _showError(error);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _import() async {
    if (!await _discard() || !mounted) return;
    try {
      final file = await openFile(
        acceptedTypeGroups: [
          const XTypeGroup(
            label: 'Documents',
            extensions: [
              'pdf',
              'doc',
              'docx',
              'odt',
              'rtf',
              'txt',
              'md',
              'png',
              'jpg',
              'jpeg',
              'json',
            ],
          ),
        ],
      );
      if (file == null) return;
      if (await file.length() > 20 * 1024 * 1024) {
        throw const FormatException('Fichier trop volumineux (20 Mo maximum).');
      }
      if (!file.name.toLowerCase().endsWith('.json')) {
        final mode = await _chooseMode();
        if (mode == null || !mounted) return;
        setState(() => _busy = true);
        final response = await _api.post(
          '/api/v1/st/reports/import-document/',
          options: Options(
            receiveTimeout: const Duration(seconds: 150),
            sendTimeout: const Duration(seconds: 60),
          ),
          data: FormData.fromMap({
            'file': MultipartFile.fromBytes(
              await file.readAsBytes(),
              filename: file.name,
            ),
          }),
        );
        if (!mounted) return;
        final source = (response.data as Map).cast<String, dynamic>();
        _fill(null, {
          'title': file.name.replaceFirst(RegExp(r'\.[^.]+$'), ''),
          'sections': source['sections'],
          'source_id': source['id'],
          'document': {'mode': mode, 'fields': []},
        });
        setState(() {
          _source = source;
          _dirty = true;
          _message =
              'Document importé. Original conservé. Vérifiez puis sauvegardez une version.';
        });
        return;
      }
      final parsed = jsonDecode(await file.readAsString());
      final raw = parsed is List
          ? parsed
          : parsed is Map
          ? parsed['sections']
          : null;
      if (raw is! List || raw.isEmpty || raw.length > 20) {
        throw const FormatException(
          'Fichier attendu : une à vingt sections JSON.',
        );
      }
      final sections = <Map<String, dynamic>>[];
      for (final section in raw) {
        if (section is! Map ||
            section['title'] is! String ||
            section['content'] is! String) {
          throw const FormatException(
            'Chaque section doit contenir un titre et un contenu textuels.',
          );
        }
        sections.add({
          'title': section['title'],
          'content': section['content'],
        });
      }
      if (!mounted) return;
      _fill(null, {
        'title': parsed is Map ? parsed['title'] : file.name,
        'sections': sections,
      });
      setState(() {
        _dirty = true;
        _message = 'Rapport importé. Vérifiez le contenu puis sauvegardez.';
      });
    } catch (error) {
      _showError(error);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _saveTemplate() async {
    if (_modelName.text.trim().isEmpty) {
      setState(() => _error = 'Donnez un nom au modèle.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final response = await _api.post(
        '/api/v1/st/reports/templates/',
        data: {
          'name': _modelName.text.trim(),
          'sections': _sectionData,
          'source_id': _sourceId,
          'document': _document,
        },
      );
      if (!mounted) return;
      final template = (response.data as Map).cast<String, dynamic>();
      setState(() {
        _templates.add(template);
        _template = (template['id'] as num).toInt();
        _dirty = true;
        _message = 'Modèle enregistré.';
      });
    } catch (error) {
      _showError(error);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _preview() => showDialog<void>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(_title.text.isEmpty ? 'Rapport sans titre' : _title.text),
      content: SizedBox(
        width: 700,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '${_current?['reference'] ?? 'Nouvelle rédaction'} · Document de travail non approuvé',
              ),
              if (_dirty)
                const Text('Aperçu des modifications non enregistrées.'),
              if (_mode == 'fixed' && _source != null)
                ReportFixedEditor(
                  api: _api,
                  source: _source!,
                  fields: _fields,
                  startPage: _sourceStart,
                  readOnly: true,
                  onChanged: () {},
                ),
              if (_mode == 'free')
                for (final section in _sections) ...[
                  const SizedBox(height: 18),
                  Text(
                    section.title.text,
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  SelectableText('${section.data['content']}'),
                ],
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Fermer l’aperçu'),
        ),
      ],
    ),
  );

  Future<void> _previewCover() async {
    try {
      final now = DateTime.now();
      final data = <String, dynamic>{
        'organization': 'CNE-ITP',
        'department': 'Coordination du Secrétariat technique',
        'title': _title.text,
        'subtitle': 'Document de travail non approuvé',
        'issuer': 'E. Luwenga',
        'footer': 'Consultant Emmany Luwenga',
        'brand': 'CNE-ITP',
        'date':
            '${now.day.toString().padLeft(2, '0')}/${now.month.toString().padLeft(2, '0')}/${now.year}',
        'reference': _current == null
            ? 'Brouillon'
            : '${_current!['reference']} · Version $_version',
        ...Map.fromEntries(_cover.entries.where((e) => e.value != '')),
      };
      final result = await _api.post<List<int>>(
        '/api/v1/st/reports/cover-preview/',
        data: data,
        options: Options(responseType: ResponseType.bytes),
      );
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Page zéro · aperçu'),
          content: SizedBox(
            width: 595,
            child: SingleChildScrollView(
              child: Image.memory(Uint8List.fromList(result.data!)),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Fermer'),
            ),
          ],
        ),
      );
    } catch (error) {
      _showError(error);
    }
  }

  Widget _modelThumbnail(Map<String, dynamic> model) {
    final id = (model['source_id'] as num).toInt();
    final future = _modelImages.putIfAbsent(id, () async {
      final result = await _api.get<List<int>>(
        '/api/v1/st/reports/sources/$id/',
        queryParameters: {'page': 0, 'thumbnail': 1},
        options: Options(responseType: ResponseType.bytes),
      );
      return Uint8List.fromList(result.data!);
    });
    return SizedBox(
      width: 90,
      height: 130,
      child: FutureBuilder<Uint8List>(
        future: future,
        builder: (context, snapshot) => snapshot.hasData
            ? Image.memory(
                snapshot.data!,
                fit: BoxFit.contain,
                errorBuilder: (_, error, stack) =>
                    const Icon(Icons.description_outlined),
              )
            : const Icon(Icons.description_outlined),
      ),
    );
  }

  Future<void> _downloadModel(Map<String, dynamic> model) async {
    try {
      final meta = await _api.get(
        '/api/v1/st/reports/sources/${model['source_id']}/',
      );
      final result = await _api.get<List<int>>(
        '/api/v1/st/reports/sources/${model['source_id']}/',
        queryParameters: {'original': 1},
        options: Options(responseType: ResponseType.bytes),
      );
      final name = '${meta.data['name']}';
      final bytes = Uint8List.fromList(result.data!);
      if (widget.saveFile != null) {
        await widget.saveFile!(bytes, name, 'application/octet-stream');
      } else {
        final location = await getSaveLocation(suggestedName: name);
        if (location != null) {
          await XFile.fromData(bytes, name: name).saveTo(location.path);
        }
      }
    } catch (error) {
      _showError(error);
    }
  }

  Future<void> _downloadOriginal() async {
    try {
      final result = await _api.get<List<int>>(
        '/api/v1/st/reports/sources/$_sourceId/',
        queryParameters: {'original': 1},
        options: Options(responseType: ResponseType.bytes),
      );
      final name = '${_source?['name'] ?? 'original.pdf'}';
      final location = await getSaveLocation(suggestedName: name);
      if (location != null) {
        await XFile.fromData(
          Uint8List.fromList(result.data!),
          name: name,
        ).saveTo(location.path);
      }
    } catch (error) {
      _showError(error);
    }
  }

  Widget _richSection(_Section section, int index) {
    section.rich.readOnly = _historical || _busy;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (section.formatted &&
            !_historical &&
            !_busy &&
            reportTables(section.rich.document.toPlainText()).isNotEmpty)
          OutlinedButton.icon(
            onPressed: () async {
              final tables = await editReportTables(
                context,
                section.rich.document.toPlainText(),
              );
              if (tables == null || !mounted) return;
              for (final table in tables.reversed) {
                section.rich.replaceText(
                  table.start,
                  table.end - table.start,
                  table.text,
                  TextSelection.collapsed(offset: table.start),
                );
              }
            },
            icon: const Icon(Icons.table_chart_outlined),
            label: const Text('Modifier les tableaux'),
          ),

        if (!section.formatted) ...[
          TextButton.icon(
            onPressed: _historical || _busy
                ? null
                : () => setState(() {
                    section.rich.document = quill.Document()
                      ..insert(0, section.content.text);
                    section.formatted = true;
                    _dirty = true;
                  }),
            icon: const Icon(Icons.format_bold),
            label: const Text('Activer la mise en forme'),
          ),
          _field('Contenu de section ${index + 1}', section.content, lines: 5),
        ] else
          Localizations.override(
            context: context,
            locale: const Locale('fr'),
            delegates: quill.FlutterQuillLocalizations.localizationsDelegates,
            child: Column(
              children: [
                if (!_historical && !_busy)
                  quill.QuillSimpleToolbar(
                    controller: section.rich,
                    config: const quill.QuillSimpleToolbarConfig(
                      showFontFamily: false,
                      showFontSize: false,
                      showColorButton: false,
                      showBackgroundColorButton: false,
                      showInlineCode: false,
                      showCodeBlock: false,
                      showLink: false,
                      showSearchButton: false,
                      showSubscript: false,
                      showSuperscript: false,
                      showListCheck: false,
                      showAlignmentButtons: true,
                    ),
                  ),
                Container(
                  constraints: const BoxConstraints(minHeight: 180),
                  decoration: BoxDecoration(
                    border: Border.all(color: const Color(0xffcbd5e1)),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  padding: const EdgeInsets.all(16),
                  child: quill.QuillEditor.basic(
                    controller: section.rich,
                    config: const quill.QuillEditorConfig(
                      scrollable: false,
                      padding: EdgeInsets.zero,
                      placeholder: 'Rédigez votre contenu…',
                    ),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _field(
    String label,
    TextEditingController controller, {
    int lines = 1,
    int? limit,
  }) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: TextField(
      controller: controller,
      readOnly: _historical || _busy,
      maxLines: lines,
      maxLength: limit,
      onChanged: (_) => setState(() => _dirty = true),
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
        alignLabelWithHint: lines > 1,
      ),
    ),
  );

  @override
  Widget build(BuildContext context) {
    final visible = _reports.where((r) => !_mine || r['mine'] == true).toList();
    return Material(
      color: AppColors.page,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          GedCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const GedSectionTitle(
                  'Rapports et exports',
                  Icons.description_outlined,
                ),
                const SizedBox(height: 8),
                const Text(
                  'Rapports de travail du Secrétariat technique · versions conservées · documents non approuvés.',
                  style: TextStyle(color: AppColors.muted),
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    FilledButton.icon(
                      onPressed: _loading || _busy ? null : _new,
                      icon: const Icon(Icons.add),
                      label: const Text('Page blanche'),
                    ),
                    OutlinedButton.icon(
                      onPressed: _loading || _busy ? null : _import,
                      icon: const Icon(Icons.upload_file),
                      label: const Text('Importer un document'),
                    ),
                    OutlinedButton.icon(
                      onPressed: _loading || _busy ? null : _load,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Actualiser les rapports'),
                    ),
                    if (_editing)
                      OutlinedButton(
                        onPressed: _busy
                            ? null
                            : () async {
                                if (await _discard() && mounted) {
                                  setState(() {
                                    _editing = false;
                                    _dirty = false;
                                    _current = null;
                                  });
                                }
                              },
                        child: const Text('Retour à la galerie'),
                      ),
                  ],
                ),
              ],
            ),
          ),
          if (_loading || _busy)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: LinearProgressIndicator(),
            ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.all(12),
              child: Text(
                _error!,
                style: const TextStyle(color: AppColors.danger),
              ),
            ),
          if (_message != null)
            Padding(
              padding: const EdgeInsets.all(12),
              child: Text(
                _message!,
                style: const TextStyle(color: AppColors.success),
              ),
            ),
          const SizedBox(height: 16),
          if (!_editing) ...[
            if (_templates.any((t) => t['source_id'] != null))
              GedCard(
                child: Material(
                  color: Colors.transparent,
                  child: ExpansionTile(
                    initiallyExpanded: true,
                    tilePadding: EdgeInsets.zero,
                    title: const Text(
                      'Modèles Page bleue',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    subtitle: const Text(
                      'Choisissez une référence, puis votre mode de rédaction.',
                    ),
                    children: [
                      SizedBox(
                        height: 248,
                        child: ListView.separated(
                          scrollDirection: Axis.horizontal,
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          itemCount: _templates
                              .where(
                                (t) =>
                                    t['source_id'] != null &&
                                    (!_templates.any(
                                          (m) =>
                                              m['collection'] == 'page_bleue',
                                        ) ||
                                        t['collection'] == 'page_bleue'),
                              )
                              .length,
                          separatorBuilder: (_, _) => const SizedBox(width: 12),
                          itemBuilder: (context, index) {
                            final models = _templates
                                .where(
                                  (t) =>
                                      t['source_id'] != null &&
                                      (!_templates.any(
                                            (m) =>
                                                m['collection'] == 'page_bleue',
                                          ) ||
                                          t['collection'] == 'page_bleue'),
                                )
                                .toList();
                            final model = models[index];
                            return SizedBox(
                              width: 184,
                              child: Card(
                                clipBehavior: Clip.antiAlias,
                                margin: EdgeInsets.zero,
                                child: InkWell(
                                  onTap: _busy ? null : () => _useModel(model),
                                  child: Stack(
                                    fit: StackFit.expand,
                                    children: [
                                      Padding(
                                        padding: const EdgeInsets.fromLTRB(
                                          12,
                                          12,
                                          12,
                                          52,
                                        ),
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            Expanded(
                                              child: Center(
                                                child: _modelThumbnail(model),
                                              ),
                                            ),
                                            Text(
                                              '${model['name']}'.replaceAll(
                                                '_',
                                                ' ',
                                              ),
                                              maxLines: 2,
                                              overflow: TextOverflow.ellipsis,
                                              style: const TextStyle(
                                                fontWeight: FontWeight.w700,
                                              ),
                                            ),
                                            const SizedBox(height: 4),
                                            const Text(
                                              'Modèle de rapport',
                                              style: TextStyle(
                                                fontSize: 11,
                                                color: AppColors.muted,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                      Positioned(
                                        right: 8,
                                        bottom: 8,
                                        child: IconButton.filledTonal(
                                          tooltip:
                                              'Télécharger le modèle original',
                                          icon: const Icon(
                                            Icons.download_outlined,
                                          ),
                                          onPressed: _busy
                                              ? null
                                              : () => _downloadModel(model),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            CheckboxListTile(
              title: const Text('Mon activité uniquement'),
              value: _mine,
              onChanged: (value) => setState(() => _mine = value ?? false),
            ),
            if (!_loading && visible.isEmpty)
              const GedCard(
                child: GedEmpty(
                  'Aucun rapport enregistré. Commencez avec une page blanche ou importez un rapport.',
                ),
              ),
            for (final report in visible)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: GedCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${rowsOf(report['versions']).firstOrNull?['title'] ?? 'Rapport'}',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '${report['reference']} · v${report['revision']} · ${report['owner_name'] ?? ''}',
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.muted,
                        ),
                      ),
                      Text(
                        '${rowsOf(report['versions']).length} version(s) · ${report['dispatch_count'] ?? 0} envoi(s)',
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.muted,
                        ),
                      ),
                      const SizedBox(height: 8),
                      OutlinedButton(
                        onPressed: _busy ? null : () => _open(report),
                        child: const Text('Ouvrir le rapport'),
                      ),
                    ],
                  ),
                ),
              ),
          ] else
            GedCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _current == null
                        ? 'Nouveau rapport'
                        : '${_current!['reference']} · Version $_version',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  if (_dirty)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 8),
                      child: Text(
                        'Modifications non enregistrées',
                        style: TextStyle(color: AppColors.warning),
                      ),
                    ),
                  if (_historical)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 8),
                      child: Text(
                        'Lecture de l’historique — version conservée, non modifiable.',
                      ),
                    ),
                  const SizedBox(height: 16),
                  if (_current != null)
                    DropdownButtonFormField<int>(
                      initialValue: _version,
                      key: ValueKey('${_current!['id']}:$_version'),
                      isExpanded: true,
                      decoration: const InputDecoration(
                        labelText: 'Version',
                        border: OutlineInputBorder(),
                      ),
                      items: rowsOf(_current!['versions'])
                          .map(
                            (v) => DropdownMenuItem<int>(
                              value: (v['number'] as num).toInt(),
                              child: Text(
                                'Version ${v['number']} — ${v['author_name'] ?? ''}',
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          )
                          .toList(),
                      onChanged: _busy
                          ? null
                          : (value) async {
                              if (value != null &&
                                  await _discard() &&
                                  mounted) {
                                _fill(
                                  _current,
                                  rowsOf(
                                    _current!['versions'],
                                  ).firstWhere((v) => v['number'] == value),
                                );
                              }
                            },
                    ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<int>(
                    initialValue: _template,
                    key: ValueKey('template:$_template:${_templates.length}'),
                    isExpanded: true,
                    decoration: const InputDecoration(
                      labelText: 'Modèle réutilisable',
                      border: OutlineInputBorder(),
                    ),
                    items: [
                      const DropdownMenuItem<int>(
                        value: null,
                        child: Text('Rapport libre'),
                      ),
                      ..._templates.map(
                        (t) => DropdownMenuItem<int>(
                          value: (t['id'] as num).toInt(),
                          child: Text(
                            '${t['name']}',
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ),
                    ],
                    onChanged: _historical || _busy
                        ? null
                        : (value) async {
                            if (_dirty && !await _discard() || !mounted) return;
                            final model = value == null
                                ? null
                                : _templates.firstWhere(
                                    (t) => t['id'] == value,
                                  );
                            final sourceId = (model?['source_id'] as num?)
                                ?.toInt();
                            final mode = sourceId == null
                                ? 'free'
                                : await _chooseMode();
                            if (mode == null || !mounted) return;
                            setState(() {
                              _sourceId = sourceId;
                              _source = null;
                              _mode = mode;
                              _cover =
                                  (jsonDecode(
                                            jsonEncode(
                                              model?['document']?['cover'] ??
                                                  {},
                                            ),
                                          )
                                          as Map)
                                      .cast<String, dynamic>();
                              _sourceStart =
                                  (model?['document']?['source_start_page']
                                          as num?)
                                      ?.toInt() ??
                                  0;
                              _fields = rowsOf(model?['document']?['fields'])
                                  .map((f) => Map<String, dynamic>.from(f))
                                  .toList();
                              _template = value;
                              _dirty = true;
                              if (value != null) {
                                _replaceSections(
                                  rowsOf(
                                    _templates.firstWhere(
                                      (t) => t['id'] == value,
                                    )['sections'],
                                  ),
                                );
                              }
                            });
                            if (sourceId != null) await _loadSource(sourceId);
                          },
                  ),
                  const SizedBox(height: 16),
                  _field('Titre du rapport', _title, limit: 250),
                  _field('Début de période (AAAA-MM-JJ)', _start),
                  _field('Fin de période (AAAA-MM-JJ)', _end),
                  ReportCoverEditor(
                    key: ObjectKey(_cover),
                    cover: _cover,
                    readOnly: _historical || _busy,
                    onChanged: () => setState(() => _dirty = true),
                    preview: _previewCover,
                  ),
                  const SizedBox(height: 16),
                  if (_sourceId != null) ...[
                    if (_source?['note'] != null &&
                        '${_source!['note']}'.isNotEmpty)
                      Text('${_source!['note']}'),
                    Wrap(
                      spacing: 8,
                      children: [
                        ChoiceChip(
                          label: const Text('Présentation conservée'),
                          selected: _mode == 'fixed',
                          onSelected: _historical || _busy
                              ? null
                              : (_) => setState(() {
                                  _mode = 'fixed';
                                  _dirty = true;
                                }),
                        ),
                        ChoiceChip(
                          label: const Text('Rédaction libre'),
                          selected: _mode == 'free',
                          onSelected: _historical || _busy
                              ? null
                              : (_) => setState(() {
                                  _mode = 'free';
                                  _dirty = true;
                                }),
                        ),
                        TextButton.icon(
                          onPressed: _busy || _source == null
                              ? null
                              : _downloadOriginal,
                          icon: const Icon(Icons.download),
                          label: const Text('Original'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    if (_mode == 'fixed' && _source == null) ...[
                      if (_error == null) const LinearProgressIndicator(),
                      TextButton(
                        onPressed: _busy ? null : () => _loadSource(_sourceId!),
                        child: const Text('Recharger le modèle'),
                      ),
                    ],
                    if (_mode == 'fixed' && _source != null)
                      ReportFixedEditor(
                        key: ValueKey(_sourceId),
                        api: _api,
                        source: _source!,
                        fields: _fields,
                        startPage: _sourceStart,
                        readOnly: _historical || _busy,
                        onChanged: () => setState(() => _dirty = true),
                      ),
                  ],
                  if (_mode == 'free')
                    for (var i = 0; i < _sections.length; i++)
                      Padding(
                        key: ObjectKey(_sections[i]),
                        padding: const EdgeInsets.only(bottom: 16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    'Section ${i + 1}',
                                    style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                                if (!_historical && _sections.length > 1)
                                  IconButton(
                                    tooltip: 'Retirer la section ${i + 1}',
                                    onPressed: _busy
                                        ? null
                                        : () {
                                            final removed = _sections[i];
                                            setState(() {
                                              _sections.removeAt(i);
                                              _dirty = true;
                                            });
                                            WidgetsBinding.instance
                                                .addPostFrameCallback(
                                                  (_) => removed.dispose(),
                                                );
                                          },
                                    icon: const Icon(Icons.close, size: 18),
                                  ),
                              ],
                            ),
                            _field(
                              'Titre de section ${i + 1}',
                              _sections[i].title,
                              limit: 150,
                            ),
                            _richSection(_sections[i], i),
                          ],
                        ),
                      ),
                  if (_current == null)
                    const Padding(
                      padding: EdgeInsets.only(bottom: 12),
                      child: Text(
                        'Sauvegardez une première version pour activer les exports PDF et Word.',
                        style: TextStyle(color: AppColors.muted),
                      ),
                    ),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      if (!_historical && _mode == 'free')
                        OutlinedButton(
                          onPressed: _busy || _sections.length >= 20
                              ? null
                              : () => setState(() {
                                  _sections.add(
                                    _Section({
                                      'title': 'Nouvelle section',
                                      'content': '',
                                    }),
                                  );
                                  _dirty = true;
                                }),
                          child: const Text('Ajouter une section'),
                        ),
                      if (!_historical)
                        FilledButton(
                          onPressed: _busy ? null : _save,
                          child: const Text('Sauvegarder une version'),
                        ),
                      OutlinedButton(
                        onPressed: _preview,
                        child: const Text('Prévisualiser'),
                      ),
                      if (_current != null) ...[
                        OutlinedButton.icon(
                          onPressed: _busy ? null : () => _export('pdf'),
                          icon: const Icon(Icons.picture_as_pdf_outlined),
                          label: const Text('Exporter en PDF'),
                        ),
                        OutlinedButton.icon(
                          onPressed: _busy ? null : () => _export('docx'),
                          icon: const Icon(Icons.download_outlined),
                          label: const Text('Exporter en Word'),
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 20),
                  const Divider(),
                  const Text(
                    'Enregistrer comme modèle',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _modelName,
                    maxLength: 200,
                    decoration: const InputDecoration(
                      labelText: 'Nom du modèle',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  OutlinedButton(
                    onPressed: _busy ? null : _saveTemplate,
                    child: const Text('Enregistrer le modèle'),
                  ),
                  if (_current != null) ...[
                    const Divider(height: 32),
                    const Text(
                      'Historique des transmissions',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    const Text(
                      'Sauvegarder un rapport ne constitue pas une transmission.',
                      style: TextStyle(fontSize: 12, color: AppColors.muted),
                    ),
                    const SizedBox(height: 12),
                    if (_targetError != null)
                      Text(
                        _targetError!,
                        style: const TextStyle(color: AppColors.warning),
                      ),
                    DropdownButtonFormField<String>(
                      initialValue: _target,
                      isExpanded: true,
                      decoration: const InputDecoration(
                        labelText: 'SC ou GT destinataire',
                        border: OutlineInputBorder(),
                      ),
                      items: _targets
                          .map(
                            (t) => DropdownMenuItem<String>(
                              value: '${t['type']}:${t['id']}',
                              enabled: t['sendable'] == true,
                              child: Text(
                                '${t['type']} · ${t['code']} — ${t['label']}${t['sendable'] == true ? '' : ' · indisponible'}',
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          )
                          .toList(),
                      onChanged: _busy
                          ? null
                          : (value) => setState(() {
                              _target = value;
                              _sendKey = null;
                            }),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _sendBody,
                      maxLines: 3,
                      maxLength: 100000,
                      onChanged: (_) => _sendKey = null,
                      decoration: const InputDecoration(
                        labelText: 'Message d’accompagnement',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    if (_dirty)
                      const Text(
                        'Sauvegardez les modifications avant de transmettre.',
                        style: TextStyle(color: AppColors.warning),
                      ),
                    FilledButton.icon(
                      onPressed: _busy || _dirty || _target == null
                          ? null
                          : _send,
                      icon: const Icon(Icons.send_outlined),
                      label: const Text('Transmettre le rapport'),
                    ),
                    const SizedBox(height: 12),
                    for (final dispatch in rowsOf(_current!['dispatches']))
                      TextButton(
                        onPressed: _busy ? null : () => _track(dispatch),
                        child: Text(
                          'Suivi v${dispatch['revision']} · ${dispatch['target_code']} · ${frDateTime(dispatch['created_at'])}',
                        ),
                      ),
                    if (rowsOf(_current!['dispatches']).isEmpty)
                      const Text('Aucun envoi enregistré.'),
                  ],
                ],
              ),
            ),
        ],
      ),
    );
  }
}

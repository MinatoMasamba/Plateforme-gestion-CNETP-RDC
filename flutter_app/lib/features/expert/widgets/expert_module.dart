import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/api/api_client.dart';
import 'expert_messaging.dart';
import 'expert_theme.dart';

export 'expert_messaging.dart' show expertRows, expertError;

Map<String, dynamic> expertMap(dynamic data) =>
    data is Map ? Map<String, dynamic>.from(data) : {};

Future<List<Map<String, dynamic>>> expertList(String path) async {
  final result = <Map<String, dynamic>>[];
  String? next = path;
  while (next != null) {
    final response = await ApiClient.dio.get(next);
    result.addAll(expertRows(response.data));
    final value = response.data is Map ? response.data['next'] : null;
    next = value is String && value.isNotEmpty ? value : null;
  }
  return result;
}

class ExpertModule extends StatefulWidget {
  const ExpertModule({
    super.key,
    required this.title,
    required this.endpoints,
    required this.builder,
  });
  final String title;
  final Map<String, String> endpoints;
  final Widget Function(ExpertModuleState state) builder;
  @override
  State<ExpertModule> createState() => ExpertModuleState();
}

class ExpertModuleState extends State<ExpertModule> {
  final data = <String, dynamic>{};
  final errors = <String, String>{};
  final values = <String, dynamic>{};
  bool loading = true, busy = false;
  int _request = 0;
  ExpertPalette get p => ExpertTheme.of(context);
  List<Map<String, dynamic>> rows(String key) => expertRows(data[key]);
  Map<String, dynamic> map(String key) => expertMap(data[key]);
  void change(VoidCallback update) => setState(update);

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    final request = ++_request;
    setState(() => loading = true);
    await Future.wait(
      widget.endpoints.entries.map((entry) async {
        try {
          final response = await ApiClient.dio.get(entry.value);
          dynamic value = response.data;
          if (value is Map &&
              value['results'] is List &&
              value['next'] != null) {
            value = [
              ...expertRows(value),
              ...await expertList('${value['next']}'),
            ];
          }
          if (!mounted || request != _request) return;
          setState(() {
            data[entry.key] = value;
            errors.remove(entry.key);
          });
        } catch (error) {
          if (!mounted || request != _request) return;
          setState(() => errors[entry.key] = expertError(error));
        }
      }),
    );
    if (mounted && request == _request) setState(() => loading = false);
  }

  void notify(String message) {
    if (mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  Future<bool> run(
    Future<void> Function() action, {
    String success = 'Modification enregistrée.',
    bool reload = true,
  }) async {
    if (busy) return false;
    setState(() => busy = true);
    try {
      await action();
      if (!mounted) return false;
      notify(success);
      if (reload) await load();
      return true;
    } catch (error) {
      notify(expertError(error));
      return false;
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<bool> post(String path, [Map<String, dynamic>? payload]) =>
      run(() async {
        await ApiClient.dio.post(path, data: payload ?? {});
      });

  Future<void> details(String title, Widget child) => showDialog<void>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(title),
      content: SizedBox(width: 650, child: SingleChildScrollView(child: child)),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Fermer'),
        ),
      ],
    ),
  );

  Future<void> open(String url) async {
    await run(
      () async {
        final uri = Uri.parse(
          url.startsWith('/') ? '${ApiClient.baseUrl}$url' : url,
        );
        if (!['https', 'http'].contains(uri.scheme) ||
            !await launchUrl(uri, mode: LaunchMode.externalApplication)) {
          throw StateError('Ouverture impossible');
        }
      },
      success: 'Lien ouvert.',
      reload: false,
    );
  }

  Future<void> download(String path, String name) async {
    await run(
      () async {
        final response = await ApiClient.dio.get<List<int>>(
          path,
          options: Options(responseType: ResponseType.bytes),
        );
        final bytes = Uint8List.fromList(response.data ?? []);
        if (kIsWeb) {
          await XFile.fromData(bytes, name: name).saveTo(name);
        } else {
          final location = await getSaveLocation(suggestedName: name);
          if (location != null) {
            await XFile.fromData(bytes, name: name).saveTo(location.path);
          }
        }
      },
      success: 'Téléchargement terminé.',
      reload: false,
    );
  }

  Widget card(String title, List<Widget> children) => Container(
    width: double.infinity,
    margin: const EdgeInsets.only(bottom: 14),
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: p.card,
      border: Border.all(color: p.border),
      borderRadius: BorderRadius.circular(12),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: TextStyle(
            color: p.title,
            fontWeight: FontWeight.bold,
            fontSize: 14,
          ),
        ),
        const SizedBox(height: 12),
        ...children,
      ],
    ),
  );

  Widget actions(List<Widget> children) => Padding(
    padding: const EdgeInsets.only(top: 10),
    child: Wrap(spacing: 8, runSpacing: 8, children: children),
  );
  Widget button(
    String label,
    VoidCallback onTap, {
    IconData icon = Icons.arrow_forward,
  }) => OutlinedButton.icon(
    onPressed: busy || loading ? null : onTap,
    icon: Icon(icon, size: 16),
    label: Text(label),
  );

  @override
  Widget build(BuildContext context) => DefaultTextStyle(
    style: TextStyle(color: p.text, fontSize: 12),
    child: SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 16,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              Text(
                widget.title,
                style: TextStyle(
                  color: p.title,
                  fontSize: 22,
                  fontWeight: FontWeight.w800,
                ),
              ),
              IconButton(
                onPressed: loading || busy ? null : load,
                tooltip: 'Actualiser',
                icon: Icon(Icons.refresh, color: p.blue),
              ),
            ],
          ),
          if (loading || busy) const LinearProgressIndicator(),
          for (final error in errors.entries)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Text(
                '${error.key} : ${error.value}',
                style: TextStyle(color: p.red),
              ),
            ),
          const SizedBox(height: 16),
          if (!loading || data.isNotEmpty) widget.builder(this),
          const SizedBox(height: 70),
        ],
      ),
    ),
  );
}

class ExpertField {
  const ExpertField(
    this.key,
    this.label, {
    this.initial = '',
    this.required = true,
    this.lines = 1,
    this.choices,
  });
  final String key, label, initial;
  final bool required;
  final int lines;
  final Map<String, String>? choices;
}

Future<void> expertForm(
  ExpertModuleState state,
  String title,
  List<ExpertField> fields,
  Future<bool> Function(Map<String, String>) submit,
) => showDialog<void>(
  context: state.context,
  builder: (_) => _ExpertForm(title: title, fields: fields, submit: submit),
);

class _ExpertForm extends StatefulWidget {
  const _ExpertForm({
    required this.title,
    required this.fields,
    required this.submit,
  });
  final String title;
  final List<ExpertField> fields;
  final Future<bool> Function(Map<String, String>) submit;
  @override
  State<_ExpertForm> createState() => _ExpertFormState();
}

class _ExpertFormState extends State<_ExpertForm> {
  final _form = GlobalKey<FormState>();
  late final Map<String, TextEditingController> _controllers = {
    for (final f in widget.fields)
      f.key: TextEditingController(text: f.initial),
  };
  bool _busy = false;
  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: !_busy,
    child: AlertDialog(
      title: Text(widget.title),
      content: SizedBox(
        width: 550,
        child: SingleChildScrollView(
          child: Form(
            key: _form,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                for (final field in widget.fields)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    child: field.choices == null
                        ? TextFormField(
                            controller: _controllers[field.key],
                            enabled: !_busy,
                            minLines: field.lines,
                            maxLines: field.lines == 1 ? 1 : field.lines + 4,
                            decoration: InputDecoration(
                              labelText: field.label,
                              border: const OutlineInputBorder(),
                            ),
                            validator: (value) =>
                                field.required && (value ?? '').trim().isEmpty
                                ? 'Champ obligatoire'
                                : null,
                          )
                        : DropdownButtonFormField<String>(
                            initialValue: field.initial.isEmpty
                                ? null
                                : field.initial,
                            isExpanded: true,
                            decoration: InputDecoration(
                              labelText: field.label,
                              border: const OutlineInputBorder(),
                            ),
                            items: [
                              for (final entry in field.choices!.entries)
                                DropdownMenuItem(
                                  value: entry.key,
                                  child: Text(
                                    entry.value,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                            ],
                            onChanged: _busy
                                ? null
                                : (v) =>
                                      _controllers[field.key]!.text = v ?? '',
                            validator: (v) =>
                                field.required && (v ?? '').isEmpty
                                ? 'Champ obligatoire'
                                : null,
                          ),
                  ),
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _busy ? null : () => Navigator.pop(context),
          child: const Text('Annuler'),
        ),
        FilledButton(
          onPressed: _busy
              ? null
              : () async {
                  if (!_form.currentState!.validate()) return;
                  setState(() => _busy = true);
                  final success = await widget.submit({
                    for (final entry in _controllers.entries)
                      entry.key: entry.value.text.trim(),
                  });
                  if (!context.mounted) return;
                  if (success) {
                    Navigator.pop(context);
                  } else {
                    setState(() => _busy = false);
                  }
                },
          child: Text(_busy ? 'Enregistrement…' : 'Enregistrer'),
        ),
      ],
    ),
  );
}

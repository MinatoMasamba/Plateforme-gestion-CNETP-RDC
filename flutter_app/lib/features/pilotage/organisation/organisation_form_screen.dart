import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api/api_client.dart';
import '../theme/copil_theme.dart';

/// Schéma, choix, validation et enregistrement issus du formulaire web Phoenix.
class OrganisationFormScreen extends ConsumerStatefulWidget {
  const OrganisationFormScreen({
    super.key,
    required this.kind,
    this.id,
    this.initial = const {},
  });
  final String kind;
  final int? id;
  final Map<String, dynamic> initial;
  @override
  ConsumerState<OrganisationFormScreen> createState() =>
      _OrganisationFormScreenState();
}

class _OrganisationFormScreenState
    extends ConsumerState<OrganisationFormScreen> {
  String _title = 'Organisation CNE-ITP';
  List<Map<String, dynamic>> _fields = [];
  final _controllers = <String, TextEditingController>{};
  final _values = <String, dynamic>{};
  Map<String, dynamic> _errors = {};
  String? _error;
  bool _loading = true, _saving = false;

  Map<String, dynamic> get query => {
    if (widget.id != null) 'id': widget.id,
    ...widget.initial,
  };
  String get path => '/api/v1/mobile/pilotage/configuration/${widget.kind}/';
  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final response = await ApiClient.dio.get(path, queryParameters: query);
      _title = '${response.data['title']}';
      _fields = (response.data['fields'] as List)
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
      for (final field in _fields) {
        final name = field['name'] as String;
        _values[name] = field['type'] == 'boolean'
            ? field['value'] == true
            : '${field['value'] ?? ''}';
        _controllers.putIfAbsent(name, TextEditingController.new).text =
            '${field['value'] ?? ''}';
      }
      if (mounted) setState(() => _error = null);
    } catch (_) {
      if (mounted) {
        setState(
          () => _error =
              'Impossible de charger ce formulaire. Vérifiez vos habilitations.',
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    if (_saving) return;
    FocusScope.of(context).unfocus();
    setState(() {
      _saving = true;
      _errors = {};
      _error = null;
    });
    final data = <String, dynamic>{};
    for (final field in _fields) {
      final name = field['name'] as String;
      if (field['type'] == 'boolean') {
        if (_values[name] == true) data[name] = 'on';
      } else {
        data[name] = field['type'] == 'choice'
            ? _values[name]
            : _controllers[name]!.text;
      }
    }
    try {
      await ApiClient.dio.post(path, queryParameters: query, data: data);
      if (mounted) Navigator.pop(context, true);
    } on DioException catch (error) {
      if (mounted) {
        setState(() {
          final body = error.response?.data;
          _errors = body is Map
              ? Map<String, dynamic>.from(body['errors'] as Map? ?? {})
              : {};
          _error = _errors.isEmpty
              ? 'Enregistrement impossible. Réessayez.'
              : null;
        });
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = ref.watch(copilDarkProvider)
        ? CopilPalette.dark
        : CopilPalette.light;
    String? errors(String name) => _errors[name] is List
        ? (_errors[name] as List).map((e) => e['message']).join('\n')
        : null;
    return Scaffold(
      backgroundColor: p.bg,
      appBar: AppBar(
        backgroundColor: p.topbar,
        foregroundColor: p.title,
        title: Text(_title, style: const TextStyle(fontSize: 18)),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 820),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      if (_error != null)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: Text(
                            _error!,
                            style: TextStyle(color: p.danger),
                          ),
                        ),
                      if (errors('__all__') != null)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: Text(
                            errors('__all__')!,
                            style: TextStyle(color: p.danger),
                          ),
                        ),
                      for (final field in _fields)
                        Builder(
                          builder: (context) {
                            final name = field['name'] as String;
                            final label =
                                '${field['label']}${field['required'] == true ? ' *' : ''}';
                            final enabled =
                                !_saving && field['disabled'] != true;
                            final decoration = InputDecoration(
                              labelText: label,
                              errorText: errors(name),
                              helperText: '${field['help']}'.isEmpty
                                  ? null
                                  : '${field['help']}',
                              helperMaxLines: 4,
                              filled: true,
                              fillColor: p.field,
                              border: const OutlineInputBorder(),
                            );
                            Widget input;
                            if (field['type'] == 'boolean') {
                              input = CheckboxListTile(
                                value: _values[name] == true,
                                onChanged: enabled
                                    ? (value) =>
                                          setState(() => _values[name] = value)
                                    : null,
                                title: Text(
                                  label,
                                  style: TextStyle(color: p.text),
                                ),
                              );
                            } else if (field['type'] == 'choice') {
                              final options = (field['options'] as List)
                                  .cast<Map>();
                              input = DropdownButtonFormField<String>(
                                initialValue:
                                    options.any(
                                      (option) =>
                                          option['value'] == _values[name],
                                    )
                                    ? _values[name] as String
                                    : null,
                                isExpanded: true,
                                dropdownColor: p.card,
                                style: TextStyle(color: p.text, fontSize: 14),
                                decoration: decoration,
                                items: [
                                  for (final option in options)
                                    DropdownMenuItem(
                                      value: '${option['value']}',
                                      child: Text(
                                        '${option['label']}',
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                ],
                                onChanged: enabled
                                    ? (value) => _values[name] = value ?? ''
                                    : null,
                              );
                            } else {
                              input = TextField(
                                controller: _controllers[name],
                                enabled: enabled,
                                minLines: field['type'] == 'multiline' ? 3 : 1,
                                maxLines: field['type'] == 'multiline' ? 8 : 1,
                                style: TextStyle(color: p.text, fontSize: 14),
                                decoration: decoration,
                              );
                            }
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 20),
                              child: input,
                            );
                          },
                        ),
                      if (_fields.isNotEmpty)
                        FilledButton(
                          onPressed: _saving ? null : _save,
                          child: Text(
                            _saving ? 'Enregistrement…' : 'Enregistrer',
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
    );
  }
}

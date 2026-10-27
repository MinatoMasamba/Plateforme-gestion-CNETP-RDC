import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api/api_client.dart';
import '../theme/copil_theme.dart';

/// Outils accessibles depuis la barre du comité, avec le même compte API.
class CopilToolsScreen extends ConsumerStatefulWidget {
  const CopilToolsScreen({
    super.key,
    required this.tool,
    this.role = '',
    this.structure = '',
    this.onAccount,
  });
  final String tool, role, structure;
  final VoidCallback? onAccount;
  @override
  ConsumerState<CopilToolsScreen> createState() => _CopilToolsScreenState();
}

class _CopilToolsScreenState extends ConsumerState<CopilToolsScreen> {
  bool _loading = true, _sending = false;
  String? _error;
  List<Map<String, dynamic>> _items = [], _messages = [];
  int? _session;
  String _filter = '';
  final _message = TextEditingController();
  final _search = TextEditingController();
  final _fields = <String, TextEditingController>{};

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _message.dispose();
    _search.dispose();
    for (final field in _fields.values) {
      field.dispose();
    }
    super.dispose();
  }

  List<Map<String, dynamic>> maps(dynamic body) =>
      (body is List ? body : body['results'] as List? ?? [])
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
  String errorText(Object error) {
    final data = error is DioException ? error.response?.data : null;
    return data is Map
        ? '${data['error'] ?? data['detail'] ?? 'Action impossible.'}'
        : 'Connexion impossible. Réessayez.';
  }

  Future<void> _load() async {
    try {
      if (widget.tool == 'profile') {
        final response = await ApiClient.dio.get(
          '/api/v1/mobile/profile/edit-data/',
        );
        for (final key in [
          'first_name',
          'last_name',
          'phone',
          'province',
          'bio',
        ]) {
          _fields.putIfAbsent(key, TextEditingController.new).text =
              '${response.data[key] ?? ''}';
        }
      } else if (widget.tool == 'instructions') {
        final response = await ApiClient.dio.get(
          '/api/v1/mobile/pilotage/instructions/',
        );
        _items = maps(response.data['items']);
      } else {
        final response = await ApiClient.dio.get('/api/v1/ia-agent/sessions/');
        _items = maps(
          response.data,
        ).where((s) => s['scope'] == 'pilotage').toList();
      }
      if (mounted) setState(() => _error = null);
    } catch (error) {
      if (mounted) setState(() => _error = errorText(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    setState(() => _sending = true);
    try {
      await ApiClient.dio.patch(
        '/api/v1/mobile/profile/update/',
        data: _fields.map((key, value) => MapEntry(key, value.text.trim())),
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Informations enregistrées.')),
        );
      }
    } catch (error) {
      if (mounted) setState(() => _error = errorText(error));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _selectSession(int id) async {
    setState(() {
      _loading = true;
      _session = id;
    });
    try {
      final response = await ApiClient.dio.get(
        '/api/v1/ia-agent/sessions/$id/messages/',
      );
      if (mounted) {
        setState(() {
          _messages = maps(response.data);
          _error = null;
        });
      }
    } catch (error) {
      if (mounted) setState(() => _error = errorText(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _send() async {
    final text = _message.text.trim();
    if (text.isEmpty || _sending) return;
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      if (_session == null) {
        final response = await ApiClient.dio.post(
          '/api/v1/ia-agent/sessions/',
          data: {'scope': 'pilotage', 'title': text, 'provider': 'deepseek'},
        );
        _session = response.data['id'] as int;
      }
      await ApiClient.dio.post(
        '/api/v1/ia-agent/sessions/$_session/send/',
        data: {'content': text},
      );
      _message.clear();
      await _selectSession(_session!);
      await _load();
    } catch (error) {
      if (mounted) setState(() => _error = errorText(error));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final dark = ref.watch(copilDarkProvider);
    final p = dark ? CopilPalette.dark : CopilPalette.light;
    final profile = widget.tool == 'profile';
    final instructions = widget.tool == 'instructions';
    final title = profile
        ? 'Mon profil COPIL'
        : instructions
        ? 'Instructions de production'
        : 'Neronne de Source Académique AI';
    Widget card(Widget child) => Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: p.card,
        border: Border.all(color: p.border),
        borderRadius: BorderRadius.circular(16),
      ),
      child: child,
    );
    return CopilTheme(
      palette: p,
      child: Scaffold(
        backgroundColor: p.bg,
        appBar: AppBar(
          backgroundColor: p.topbar,
          foregroundColor: p.title,
          title: Text(
            title,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
          ),
        actions: [
          if (profile && widget.onAccount != null) IconButton(tooltip: 'Mon compte', onPressed: widget.onAccount, icon: const Icon(Icons.account_circle_outlined)),
            IconButton(
              tooltip: 'Changer le thème',
              onPressed: () =>
                  ref.read(copilDarkProvider.notifier).state = !dark,
              icon: Icon(
                dark ? Icons.light_mode_outlined : Icons.dark_mode_outlined,
              ),
            ),
          ],
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator())
            : Column(
                children: [
                  if (_error != null)
                    MaterialBanner(
                      content: Text(_error!),
                      actions: [
                        TextButton(
                          onPressed: _load,
                          child: const Text('Réessayer'),
                        ),
                      ],
                    ),
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.all(24),
                      child: Center(
                        child: ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 1100),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              if (profile) ...[
                                Text(
                                  'Identité personnelle et mandat enregistré au Comité de Pilotage.',
                                  style: TextStyle(color: p.muted),
                                ),
                                const SizedBox(height: 24),
                                card(
                                  Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        'MANDAT COPIL',
                                        style: TextStyle(
                                          color: p.blue,
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                      const SizedBox(height: 16),
                                      Text(
                                        widget.role,
                                        style: TextStyle(
                                          color: p.title,
                                          fontSize: 20,
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                      const SizedBox(height: 8),
                                      Text(
                                        widget.structure,
                                        style: TextStyle(color: p.muted),
                                      ),
                                      const SizedBox(height: 16),
                                      Text(
                                        'Le poste et les habilitations sont établis par les données de nomination. Ils ne peuvent pas être modifiés depuis ce profil.',
                                        style: TextStyle(
                                          color: p.muted,
                                          fontSize: 12,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                card(
                                  Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.stretch,
                                    children: [
                                      Text(
                                        'Mes informations personnelles',
                                        style: TextStyle(
                                          fontSize: 18,
                                          fontWeight: FontWeight.w700,
                                          color: p.title,
                                        ),
                                      ),
                                      const SizedBox(height: 16),
                                      for (final entry in {
                                        'first_name': 'Prénom',
                                        'last_name': 'Nom',
                                        'phone': 'Téléphone',
                                        'province': 'Province',
                                        'bio': 'Bio',
                                      }.entries)
                                        Padding(
                                          padding: const EdgeInsets.only(
                                            bottom: 16,
                                          ),
                                          child: TextField(
                                            controller: _fields[entry.key],
                                            maxLines: entry.key == 'bio'
                                                ? 3
                                                : 1,
                                            style: TextStyle(color: p.text),
                                            decoration: InputDecoration(
                                              labelText: entry.value,
                                              border:
                                                  const OutlineInputBorder(),
                                            ),
                                          ),
                                        ),
                                      FilledButton(
                                        onPressed: _sending ? null : _save,
                                        child: Text(
                                          _sending
                                              ? 'Enregistrement…'
                                              : 'Enregistrer mes informations',
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ] else if (instructions) ...[
                                TextField(
                                  controller: _search,
                                  onChanged: (value) => setState(
                                    () => _filter = value.toLowerCase(),
                                  ),
                                  decoration: const InputDecoration(
                                    prefixIcon: Icon(Icons.search),
                                    labelText: 'Rechercher une instruction',
                                    border: OutlineInputBorder(),
                                  ),
                                ),
                                const SizedBox(height: 24),
                                if (_items.isEmpty)
                                  card(
                                    Text(
                                      'Aucune instruction enregistrée.',
                                      style: TextStyle(color: p.muted),
                                    ),
                                  ),
                                for (final item in _items.where(
                                  (item) =>
                                      '${item['title']} ${item['status']} ${item['sender']}'
                                          .toLowerCase()
                                          .contains(_filter),
                                ))
                                  card(
                                    ExpansionTile(
                                      title: Text(
                                        '${item['title']}',
                                        style: TextStyle(
                                          color: p.title,
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                      subtitle: Text(
                                        '${item['type']} · ${item['status']}',
                                        style: TextStyle(color: p.blue),
                                      ),
                                      children: [
                                        ListTile(
                                          title: Text(
                                            'Émetteur : ${item['sender']}\nDestinataire : ${item['recipient']}',
                                            style: TextStyle(color: p.text),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                              ] else ...[
                                Wrap(
                                  spacing: 8,
                                  runSpacing: 8,
                                  children: [
                                    OutlinedButton.icon(
                                      onPressed: _sending
                                          ? null
                                          : () => setState(() {
                                              _session = null;
                                              _messages = [];
                                            }),
                                      icon: const Icon(Icons.add),
                                      label: const Text('Nouvelle session'),
                                    ),
                                    for (final item in _items)
                                      ChoiceChip(
                                        label: Text(
                                          '${item['title']}'.isEmpty
                                              ? 'Session sans titre'
                                              : '${item['title']}',
                                        ),
                                        selected: _session == item['id'],
                                        onSelected: _sending
                                            ? null
                                            : (_) => _selectSession(
                                                item['id'] as int,
                                              ),
                                      ),
                                  ],
                                ),
                                const SizedBox(height: 24),
                                if (_messages.isEmpty)
                                  Padding(
                                    padding: const EdgeInsets.all(40),
                                    child: Text(
                                      'Démarre une conversation avec l’assistant IA du Comité de Pilotage…',
                                      textAlign: TextAlign.center,
                                      style: TextStyle(color: p.subtle),
                                    ),
                                  ),
                                for (final message in _messages)
                                  card(
                                    Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          message['role'] == 'user'
                                              ? 'Vous'
                                              : 'Assistant IA',
                                          style: TextStyle(
                                            color: p.blue,
                                            fontSize: 12,
                                            fontWeight: FontWeight.w700,
                                          ),
                                        ),
                                        const SizedBox(height: 8),
                                        SelectableText(
                                          '${message['content']}',
                                          style: TextStyle(color: p.text),
                                        ),
                                      ],
                                    ),
                                  ),
                              ],
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                  if (!profile && !instructions)
                    SafeArea(
                      top: false,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          children: [
                            Expanded(
                              child: TextField(
                                controller: _message,
                                minLines: 1,
                                maxLines: 4,
                                enabled: !_sending,
                                onSubmitted: (_) => _send(),
                                decoration: const InputDecoration(
                                  hintText: 'Écrivez votre message…',
                                  border: OutlineInputBorder(),
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            IconButton(
                              tooltip: 'Envoyer',
                              onPressed: _sending ? null : _send,
                              icon: _sending
                                  ? const SizedBox(
                                      width: 20,
                                      height: 20,
                                      child: CircularProgressIndicator(),
                                    )
                                  : const Icon(Icons.send),
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
      ),
    );
  }
}

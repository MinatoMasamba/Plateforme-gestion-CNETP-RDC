import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api/api_client.dart';
import '../theme/copil_theme.dart';
import 'organisation_form_screen.dart';

class OrganisationResourcesScreen extends ConsumerStatefulWidget {
  const OrganisationResourcesScreen({super.key, required this.management});
  final bool management;
  @override
  ConsumerState<OrganisationResourcesScreen> createState() =>
      _OrganisationResourcesScreenState();
}

class _OrganisationResourcesScreenState
    extends ConsumerState<OrganisationResourcesScreen> {
  static const _kinds = {
    'mandat': 'Nominations',
    'habilitation': 'Habilitations',
    'circuit': 'Circuits',
    'rattachement': 'Rattachements documentaires',
    'poste': 'Postes',
    'gt': 'Groupes de travail',
  };
  String _kind = 'mandat';
  List<Map<String, dynamic>> _items = [];
  bool _loading = true;
  String? _error;
  int _page = 1, _total = 0;
  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await ApiClient.dio.get(
        widget.management
            ? '/api/v2/organisation/configuration/$_kind/'
            : '/api/v2/organisation/dossiers/',
        queryParameters: {'page': _page},
      );
      final body = response.data;
      final rows = body is List ? body : body['results'] as List;
      if (mounted)
        setState(() {
          _items = rows
              .map((e) => Map<String, dynamic>.from(e as Map))
              .toList();
          _total = body is List ? rows.length : (body['count'] as num).toInt();
        });
    } catch (_) {
      if (mounted)
        setState(
          () => _error =
              'Impossible de charger ces informations. Vérifiez vos habilitations et réessayez.',
        );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _edit([int? id]) async {
    final saved = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => OrganisationFormScreen(kind: _kind, id: id),
      ),
    );
    if (saved == true && mounted) await _load();
  }

  Future<void> _dossier(int id) async {
    try {
      final response = await ApiClient.dio.get(
        '/api/v2/organisation/dossiers/$id/',
      );
      if (!mounted) return;
      final data = Map<String, dynamic>.from(response.data as Map);
      final p = ref.read(copilDarkProvider)
          ? CopilPalette.dark
          : CopilPalette.light;
      await Navigator.push<void>(
        context,
        MaterialPageRoute(
          builder: (_) => Scaffold(
            backgroundColor: p.bg,
            appBar: AppBar(
              backgroundColor: p.topbar,
              foregroundColor: p.title,
              title: Text('${data['reference']}'),
            ),
            body: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    '${data['title']}',
                    style: TextStyle(
                      color: p.title,
                      fontSize: 24,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    '${data['sc']} · ${data['gt']} · ${data['state']} · Révision ${data['revision']}',
                    style: TextStyle(color: p.blue),
                  ),
                  const SizedBox(height: 24),
                  for (final version in data['versions'] as List? ?? [])
                    ExpansionTile(
                      title: Text(
                        'Version ${version['version_number']}',
                        style: TextStyle(color: p.title),
                      ),
                      children: [
                        SelectableText(
                          '${version['content']}',
                          style: TextStyle(color: p.text),
                        ),
                      ],
                    ),
                  for (final piece in data['pieces'] as List? ?? [])
                    ExpansionTile(
                      title: Text(
                        '${piece['reference']} · ${piece['kind']}',
                        style: TextStyle(color: p.title),
                      ),
                      children: [
                        SelectableText(
                          '${piece['content']}',
                          style: TextStyle(color: p.text),
                        ),
                      ],
                    ),
                  for (final decision in data['decisions'] as List? ?? [])
                    ListTile(
                      title: Text(
                        '${decision['decision_reference']}',
                        style: TextStyle(color: p.title),
                      ),
                      subtitle: Text(
                        '${decision['from_state']} → ${decision['to_state']}\n${decision['reason']}',
                        style: TextStyle(color: p.muted),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
      );
    } catch (_) {
      if (mounted) setState(() => _error = 'Impossible de charger ce dossier.');
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = ref.watch(copilDarkProvider)
        ? CopilPalette.dark
        : CopilPalette.light;
    return Scaffold(
      backgroundColor: p.bg,
      appBar: AppBar(
        backgroundColor: p.topbar,
        foregroundColor: p.title,
        title: Text(
          widget.management
              ? 'Nominations, habilitations et circuits'
              : 'Dossiers et supervision',
          style: const TextStyle(fontSize: 18),
        ),
      ),
      body: Column(
        children: [
          if (widget.management)
            Padding(
              padding: const EdgeInsets.all(20),
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final kind in _kinds.entries)
                    ChoiceChip(
                      label: Text(kind.value),
                      selected: _kind == kind.key,
                      onSelected: _loading
                          ? null
                          : (_) {
                              _kind = kind.key;
                              _load();
                            },
                    ),
                  FilledButton.icon(
                    onPressed: _loading ? null : () => _edit(),
                    icon: const Icon(Icons.add),
                    label: const Text('Ajouter'),
                  ),
                ],
              ),
            ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.all(20),
              child: Text(_error!, style: TextStyle(color: p.danger)),
            ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _items.isEmpty
                ? Center(
                    child: Text(
                      'Aucun élément enregistré.',
                      style: TextStyle(color: p.muted),
                    ),
                  )
                : ListView.separated(
                    padding: const EdgeInsets.all(24),
                    itemCount: _items.length,
                    separatorBuilder: (_, _) => Divider(color: p.border),
                    itemBuilder: (context, index) {
                      final item = _items[index];
                      final title =
                          item['title'] ??
                          item['function'] ??
                          item['name'] ??
                          item['code'] ??
                          item['decision_reference'] ??
                          item['appointment_reference'] ??
                          item['action'] ??
                          'Élément ${item['id']}';
                      return ListTile(
                        title: Text(
                          '$title',
                          style: TextStyle(
                            color: p.title,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        subtitle: Text(
                          '${item['reference'] ?? item['code'] ?? ''} · ${item['state'] ?? item['status'] ?? ''}',
                          style: TextStyle(color: p.muted),
                        ),
                        trailing: Icon(
                          widget.management
                              ? Icons.edit_outlined
                              : Icons.arrow_forward,
                          color: p.blue,
                        ),
                        onTap: () => widget.management
                            ? _edit(item['id'] as int)
                            : _dossier(item['id'] as int),
                      );
                    },
                  ),
          ),
          if (!widget.management && _total > 25)
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                TextButton(
                  onPressed: _page <= 1 || _loading
                      ? null
                      : () {
                          _page--;
                          _load();
                        },
                  child: const Text('Précédent'),
                ),
                Text('Page $_page', style: TextStyle(color: p.text)),
                TextButton(
                  onPressed: _page * 25 >= _total || _loading
                      ? null
                      : () {
                          _page++;
                          _load();
                        },
                  child: const Text('Suivant'),
                ),
              ],
            ),
        ],
      ),
    );
  }
}

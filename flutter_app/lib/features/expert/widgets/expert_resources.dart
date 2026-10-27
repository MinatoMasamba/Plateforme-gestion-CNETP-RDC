import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

import 'expert_theme.dart';

/// Parité des ressources web, avec persistance locale explicite.
class ExpertResources extends StatefulWidget {
  const ExpertResources({
    super.key,
    required this.documentId,
    this.userScope = '',
  });
  final String documentId;
  final String userScope;

  @override
  State<ExpertResources> createState() => _ExpertResourcesState();
}

class _ExpertResourcesState extends State<ExpertResources> {
  final _drive = TextEditingController(), _meet = TextEditingController();
  final _title = TextEditingController(),
      _url = TextEditingController(),
      _description = TextEditingController();
  List<Map<String, dynamic>> _references = [];
  bool _ready = false, _saving = false;
  String? _error;
  String get _key =>
      'expert.resources.${widget.userScope}.${widget.documentId}';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final preferences = await SharedPreferences.getInstance();
      final raw = preferences.getString(_key);
      final data = raw == null ? <String, dynamic>{} : jsonDecode(raw) as Map;
      if (!mounted) return;
      _drive.text = data['drive'] as String? ?? '';
      _meet.text = data['meet'] as String? ?? '';
      _references = (data['references'] as List? ?? [])
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
      setState(() => _ready = true);
    } catch (_) {
      if (mounted) {
        setState(() {
          _ready = true;
          _error = 'Impossible de charger les ressources locales.';
        });
      }
    }
  }

  bool _valid(String text) {
    final uri = Uri.tryParse(text.trim());
    return uri != null &&
        ['https', 'http'].contains(uri.scheme) &&
        uri.host.isNotEmpty;
  }

  Future<void> _save({bool add = false, int? remove}) async {
    if (_saving) return;
    if ([
          _drive.text,
          _meet.text,
        ].any((s) => s.trim().isNotEmpty && !_valid(s)) ||
        (add && (_title.text.trim().isEmpty || !_valid(_url.text)))) {
      setState(
        () => _error = 'Renseignez un titre et des liens HTTP(S) valides.',
      );
      return;
    }
    final references = [..._references];
    if (add) {
      references.add({
        'title': _title.text.trim(),
        'url': _url.text.trim(),
        'description': _description.text.trim(),
      });
    }
    if (remove != null) references.removeAt(remove);
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = await prefs.setString(
        _key,
        jsonEncode({
          'drive': _drive.text.trim(),
          'meet': _meet.text.trim(),
          'references': references,
        }),
      );
      if (!saved) throw StateError('Sauvegarde refusée');
      if (!mounted) return;
      setState(() => _references = references);
      if (add) {
        _title.clear();
        _url.clear();
        _description.clear();
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Ressources enregistrées sur cet appareil.'),
        ),
      );
    } catch (_) {
      if (mounted) setState(() => _error = 'Enregistrement local impossible.');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _open(String text) async {
    if (!_valid(text)) {
      setState(() => _error = 'Lien HTTP(S) invalide.');
      return;
    }
    try {
      if (!await launchUrl(
        Uri.parse(text.trim()),
        mode: LaunchMode.externalApplication,
      )) {
        throw StateError('Ouverture impossible');
      }
    } catch (_) {
      if (mounted) setState(() => _error = 'Impossible d’ouvrir ce lien.');
    }
  }

  Widget _field(
    TextEditingController controller,
    String label, {
    bool link = false,
  }) {
    final p = ExpertTheme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              style: TextStyle(color: p.text),
              decoration: InputDecoration(
                labelText: label,
                labelStyle: TextStyle(color: p.muted),
                border: const OutlineInputBorder(),
              ),
            ),
          ),
          if (link)
            IconButton(
              onPressed: () => _open(controller.text),
              tooltip: 'Ouvrir le lien',
              icon: Icon(Icons.open_in_new, color: p.blue),
            ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    for (final c in [_drive, _meet, _title, _url, _description]) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return Container(
      decoration: BoxDecoration(
        color: p.card,
        border: Border.all(color: p.border),
        borderRadius: BorderRadius.circular(12),
      ),
      child: ExpansionTile(
        title: Text(
          'Ressources connexes & espace collaboratif',
          style: TextStyle(color: p.title, fontWeight: FontWeight.bold),
        ),
        subtitle: Text(
          'Liens et références enregistrés uniquement sur cet appareil',
          style: TextStyle(color: p.muted, fontSize: 11),
        ),
        childrenPadding: const EdgeInsets.all(16),
        children: [
          if (!_ready) const LinearProgressIndicator(),
          if (_error != null) Text(_error!, style: TextStyle(color: p.red)),
          if (_ready) ...[
            _field(_drive, 'Google Drive', link: true),
            _field(_meet, 'Google Meet', link: true),
            TextButton(
              onPressed: _saving ? null : _save,
              child: const Text('Enregistrer les liens localement'),
            ),
            const Divider(),
            Text(
              'Pièces liées (${_references.length})',
              style: TextStyle(color: p.text),
            ),
            for (var i = 0; i < _references.length; i++)
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(
                  '${_references[i]['title']}',
                  style: TextStyle(color: p.text),
                ),
                subtitle: Text(
                  '${_references[i]['description'] ?? ''}',
                  style: TextStyle(color: p.muted),
                ),
                onTap: () => _open('${_references[i]['url']}'),
                trailing: IconButton(
                  onPressed: _saving ? null : () => _save(remove: i),
                  tooltip: 'Retirer la référence',
                  icon: Icon(Icons.delete_outline, color: p.red),
                ),
              ),
            _field(_title, 'Titre de la pièce'),
            _field(_url, 'Lien vers la pièce (HTTP/S)'),
            _field(_description, 'Description'),
            FilledButton.icon(
              onPressed: _saving ? null : () => _save(add: true),
              icon: const Icon(Icons.link),
              label: const Text('Lier la pièce localement'),
            ),
          ],
        ],
      ),
    );
  }
}

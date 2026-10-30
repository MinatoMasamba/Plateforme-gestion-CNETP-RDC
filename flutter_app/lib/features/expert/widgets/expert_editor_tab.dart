import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../../core/api/api_client.dart';
import 'expert_messaging.dart';
import 'expert_resources.dart';
import 'expert_theme.dart';

/// Le parent conserve ces brouillons pendant toute la session de l’espace expert.
class ExpertDraft {
  ExpertDraft(this.text, this.comment, this.base);
  String text;
  String comment;
  String base;
}

class ExpertEditorTab extends StatefulWidget {
  const ExpertEditorTab({
    super.key,
    required this.doc,
    required this.loading,
    required this.onSave,
    required this.onOpenProfile,
    this.drafts,
    this.userName = 'Expert',
    this.userScope = '',
  });

  final Map<String, dynamic>? doc;
  final bool loading;
  final VoidCallback onSave;
  final VoidCallback onOpenProfile;
  final Map<String, ExpertDraft>? drafts;
  final String userName;
  final String userScope;

  @override
  State<ExpertEditorTab> createState() => _ExpertEditorTabState();
}

class _ExpertEditorTabState extends State<ExpertEditorTab> {
  final _text = TextEditingController();
  final _comment = TextEditingController();
  final _excerpt = TextEditingController();
  final _focus = FocusNode();
  final _shareKey = GlobalKey();
  final _editorKey = GlobalKey();
  bool _right = true, _voteOpen = true, _saving = false, _voting = false;
  bool _analyzing = false, _sharing = false;
  int _generation = 0, _aiRequest = 0;
  String _base = '';
  String? _recipient, _voteError, _contactsError;
  dynamic _expertId;
  List<Map<String, dynamic>> _votes = [], _contacts = [];
  Map<String, dynamic>? _advice;
  String? _analyzedText;
  final Map<String, ExpertDraft> _localDrafts = {};

  String? get _id => widget.doc?['id']?.toString();
  Map<String, ExpertDraft> get _drafts => widget.drafts ?? _localDrafts;
  bool get _dirty => _text.text != _base || _comment.text.isNotEmpty;
  bool get _closed => ['PUBLISHED', 'ARCHIVED'].contains(widget.doc?['status']);

  @override
  void initState() {
    super.initState();
    _restore();
    _focus.addListener(() {
      if (_focus.hasFocus && mounted) {
        setState(() {
          _right = false;
          _voteOpen = false;
        });
      }
    });
  }

  @override
  void didUpdateWidget(covariant ExpertEditorTab oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.doc?['id'] != widget.doc?['id']) {
      _restore();
    }
  }

  void _restore() {
    _generation++;
    _aiRequest++;
    _advice = null;
    _analyzing = false;
    _votes = [];
    _voteError = null;
    _excerpt.clear();
    _recipient = null;
    final version = widget.doc?['latest_version'];
    final content = version is Map ? version['content'] : null;
    _base = content as String? ?? widget.doc?['content'] as String? ?? '';
    final stored = _drafts[_id];
    final draft =
        stored != null &&
            (stored.text != stored.base || stored.comment.isNotEmpty)
        ? stored
        : null;
    // Affecter les trois valeurs avant de notifier les listeners.
    _text.removeListener(_changed);
    _comment.removeListener(_changed);
    _text.text = draft?.text ?? _base;
    _comment.text = draft?.comment ?? '';
    _base = draft?.base ?? _base;
    _text.addListener(_changed);
    _comment.addListener(_changed);
    if (_id != null) _loadData(_generation);
  }

  void _changed() {
    if (_id != null) {
      _drafts[_id!] = ExpertDraft(_text.text, _comment.text, _base);
    }
    final selection = _text.selection;
    if (selection.isValid &&
        !selection.isCollapsed &&
        selection.end <= _text.text.length) {
      final selected = selection.textInside(_text.text);
      if (_excerpt.text != selected) {
        _excerpt.text = selected;
        _right = true;
      }
    }
    if (mounted) setState(() {});
  }

  Future<void> _loadData(int generation) async {
    await Future.wait([
      _loadVotes(generation),
      () async {
        try {
          final response = await ApiClient.dio.get('/api/v1/experts/me/');
          if (mounted && generation == _generation) {
            setState(() => _expertId = response.data['id']);
          }
        } catch (_) {
          /* Les votes restent consultables sans profil. */
        }
      }(),
      () async {
        try {
          final response = await ApiClient.dio.get(
            '/api/v1/messages/contacts/',
          );
          if (mounted && generation == _generation) {
            setState(() {
              _contacts = expertRows(response.data);
              _contactsError = null;
            });
          }
        } catch (error) {
          if (mounted && generation == _generation) {
            setState(() => _contactsError = expertError(error));
          }
        }
      }(),
    ]);
  }

  Future<void> _loadVotes(int generation) async {
    try {
      final response = await ApiClient.dio.get('/api/v1/norms/$_id/votes/');
      if (mounted && generation == _generation) {
        setState(() {
          _votes = expertRows(response.data);
          _voteError = null;
        });
      }
    } catch (error) {
      if (mounted && generation == _generation) {
        setState(() => _voteError = expertError(error));
      }
    }
  }

  void _notify(String text) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
    }
  }

  Future<void> _save() async {
    final id = _id;
    if (id == null || _saving) return;
    final text = _text.text, comment = _comment.text.trim();
    if (text.trim().isEmpty || comment.isEmpty) {
      _notify('Le contenu et le commentaire de version sont obligatoires.');
      return;
    }
    final generation = _generation;
    setState(() => _saving = true);
    try {
      await ApiClient.dio.post(
        '/api/v1/norms/$id/create_version/',
        data: {
          'title': widget.doc?['title'],
          'content': text,
          'comment': comment,
        },
      );
      final draft = _drafts[id];
      if (draft != null) {
        draft.base = text;
        if (draft.comment.trim() == comment) draft.comment = '';
      }
      if (!mounted || generation != _generation) return;
      _base = text;
      if (_comment.text.trim() == comment) _comment.clear();
      _changed();
      widget.onSave();
      _notify('Nouvelle version sauvegardée.');
    } catch (error) {
      if (mounted && generation == _generation) _notify(expertError(error));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _castVote(String choice) async {
    final generation = _generation;
    setState(() => _voting = true);
    try {
      final response = await ApiClient.dio.post(
        '/api/v1/norms/$_id/vote/',
        data: {'vote': choice},
      );
      if (!mounted || generation != _generation) return;
      await _loadVotes(generation);
      if (!mounted || generation != _generation) return;
      _notify(
        response.data['promoted_to_ctm'] == true
            ? 'Vote enregistré ; norme validée au niveau CTM.'
            : 'Vote enregistré.',
      );
      widget.onSave();
    } catch (error) {
      if (mounted && generation == _generation) _notify(expertError(error));
    } finally {
      if (mounted) setState(() => _voting = false);
    }
  }

  Future<void> _analyze() async {
    if (_text.text.trim().isEmpty) {
      _notify('Saisissez du texte à analyser.');
      return;
    }
    final request = ++_aiRequest, generation = _generation;
    final text = _text.text;
    setState(() {
      _analyzing = true;
      _advice = null;
    });
    try {
      final response = await ApiClient.dio.post(
        '/api/v1/ia-agent/sessions/regulatory-advice/',
        data: {
          'text': text,
          for (final key in [
            'standard_family',
            'norm_type',
            'title',
            'ctm_name',
            'wg_name',
          ])
            key: widget.doc?[key],
        },
        options: Options(receiveTimeout: const Duration(seconds: 65)),
      );
      if (!mounted || request != _aiRequest || generation != _generation) {
        return;
      }
      setState(() {
        _advice = Map<String, dynamic>.from(response.data as Map);
        _analyzedText = text;
      });
    } catch (error) {
      if (mounted && request == _aiRequest && generation == _generation) {
        _notify(expertError(error));
      }
    } finally {
      if (mounted && request == _aiRequest && generation == _generation) {
        setState(() => _analyzing = false);
      }
    }
  }

  void _applyAdvice() {
    if (_text.text != _analyzedText) {
      _notify('Le texte a changé. Relancez l’analyse avant d’appliquer.');
      return;
    }
    final edits = expertRows(
      _advice?['edits'],
    ).where((e) => e['applied'] == true).length;
    final applied = _advice?['applied_text'];
    if (edits == 0 || applied is! String || _advice?['fallback'] == true) {
      return;
    }
    _text.text = applied;
    _comment.text =
        '$edits correction(s) réglementaire(s) proposée(s) par l’Assistant IA';
    setState(() => _advice = null);
  }

  Future<void> _share() async {
    if (_recipient == null || _excerpt.text.trim().isEmpty) return;
    final contact = _contacts.firstWhere(
      (c) => '${c['user_id']}' == _recipient,
    );
    final generation = _generation;
    final code = widget.doc?['reference_number'] ?? '';
    final excerpt = _excerpt.text.trim();
    setState(() => _sharing = true);
    try {
      await ApiClient.dio.post(
        '/api/v1/messages/',
        data: {
          'receiver_id': contact['user_id'],
          'content': '📋 Clause partagée [$code]\n« $excerpt »',
          'is_clause_share': true,
          'clause_code': code,
          'clause_excerpt': excerpt,
        },
      );
      if (!mounted || generation != _generation) return;
      _notify('Clause envoyée.');
      await openExpertMessaging(context, contact: contact);
    } catch (error) {
      if (mounted && generation == _generation) _notify(expertError(error));
    } finally {
      if (mounted) setState(() => _sharing = false);
    }
  }

  Future<void> _groups() async {
    final generation = _generation;
    final ctm = widget.doc?['ctm'];
    try {
      final response = await ApiClient.dio.get(
        '/api/v1/wg/',
        queryParameters: {'ctm': ctm, 'page_size': 100},
      );
      if (!mounted || generation != _generation) return;
      final groups = expertRows(
        response.data,
      ).where((g) => '${g['ctm']}' == '$ctm').toList();
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Groupes de la sous-commission'),
          content: SizedBox(
            width: 480,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (groups.isEmpty) const Text('Aucun groupe disponible.'),
                  for (final group in groups)
                    ListTile(
                      title: Text('${group['name'] ?? ''}'),
                      subtitle: Text('${group['description'] ?? ''}'),
                    ),
                ],
              ),
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
      _notify(expertError(error));
    }
  }

  @override
  void dispose() {
    _generation++;
    _aiRequest++;
    _text.dispose();
    _comment.dispose();
    _excerpt.dispose();
    _focus.dispose();
    super.dispose();
  }

  Widget _panel(String title, Widget child, {VoidCallback? close}) {
    final p = ExpertTheme.of(context);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: p.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: p.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  title,
                  style: TextStyle(
                    color: p.title,
                    fontWeight: FontWeight.w800,
                    fontSize: 12,
                  ),
                ),
              ),
              if (close != null)
                IconButton(
                  onPressed: close,
                  tooltip: 'Masquer',
                  icon: const Icon(Icons.close, size: 18),
                ),
            ],
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }

  InputDecoration _input(String label) {
    final p = ExpertTheme.of(context);
    return InputDecoration(
      labelText: label,
      labelStyle: TextStyle(color: p.muted),
      filled: true,
      fillColor: p.field,
      border: const OutlineInputBorder(),
      contentPadding: const EdgeInsets.all(12),
    );
  }

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    if (widget.doc == null) {
      return Center(
        child: widget.loading
            ? const CircularProgressIndicator()
            : const Text('Aucun document sélectionné'),
      );
    }
    final words = _text.text.trim().isEmpty
        ? 0
        : _text.text.trim().split(RegExp(r'\s+')).length;
    final updated = DateTime.tryParse(
      '${widget.doc?['updated_at']}',
    )?.toLocal();
    final editor = Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _panel(
          'FORMAT : TEXTE BRUT / CLAUSES ISO',
          Column(
            children: [
              Text(
                '${_text.text.length} caractères • $words mots',
                style: TextStyle(color: p.subtle),
              ),
              SizedBox(
                key: _editorKey,
                height: _right ? 384 : 520,
                child: TextField(
                  key: const ValueKey('norm-editor-text'),
                  controller: _text,
                  focusNode: _focus,
                  readOnly: widget.loading,
                  expands: true,
                  maxLines: null,
                  minLines: null,
                  textAlignVertical: TextAlignVertical.top,
                  style: TextStyle(color: p.text, fontSize: 14, height: 1.7),
                  onTap: () => setState(() {
                    _right = false;
                    _voteOpen = false;
                  }),
                  decoration: const InputDecoration(
                    hintText: 'Écrivez le standard ici…',
                    border: InputBorder.none,
                  ),
                ),
              ),
              Wrap(
                spacing: 8,
                children: [
                  TextButton.icon(
                    onPressed: () => setState(() {
                      _right = !_right;
                      _focus.unfocus();
                    }),
                    icon: const Icon(Icons.auto_awesome),
                    label: Text(
                      _right ? 'Masquer IA / partage' : 'Afficher IA / partage',
                    ),
                  ),
                  TextButton.icon(
                    onPressed: () => setState(() => _voteOpen = !_voteOpen),
                    icon: const Icon(Icons.how_to_vote_outlined),
                    label: Text(
                      _voteOpen ? 'Masquer le scrutin' : 'Afficher le scrutin',
                    ),
                  ),
                  if (_excerpt.text.isNotEmpty)
                    TextButton.icon(
                      onPressed: () {
                        setState(() => _right = true);
                        WidgetsBinding.instance.addPostFrameCallback((_) {
                          if (mounted && _shareKey.currentContext != null) {
                            Scrollable.ensureVisible(
                              _shareKey.currentContext!,
                              duration: const Duration(milliseconds: 250),
                            );
                          }
                        });
                      },
                      icon: const Icon(Icons.share),
                      label: const Text('Partager la sélection'),
                    ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        if (_voteOpen) ...[_votePanel(), const SizedBox(height: 16)],
        _panel(
          'JOURNAL DES VERSIONS / COMMENTAIRE',
          Column(
            children: [
              TextField(
                key: const ValueKey('norm-editor-comment'),
                controller: _comment,
                style: TextStyle(color: p.text),
                decoration: _input('Commentaire obligatoire'),
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 12,
                runSpacing: 8,
                alignment: WrapAlignment.spaceBetween,
                children: [
                  TextButton.icon(
                    onPressed: !_dirty || _saving
                        ? null
                        : () {
                            _text.text = _base;
                            _comment.clear();
                            setState(() => _advice = null);
                          },
                    icon: const Icon(Icons.rotate_left),
                    label: const Text('Réinitialiser'),
                  ),
                  FilledButton.icon(
                    onPressed:
                        _saving ||
                            widget.loading ||
                            !_dirty ||
                            _text.text.trim().isEmpty ||
                            _comment.text.trim().isEmpty
                        ? null
                        : _save,
                    icon: const Icon(Icons.save_outlined),
                    label: Text(
                      _saving ? 'Sauvegarde…' : 'Sauvegarder la version',
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
    final right = Column(
      children: [_aiPanel(), const SizedBox(height: 16), _sharePanel()],
    );
    return DefaultTextStyle(
      style: TextStyle(color: p.text, fontSize: 12),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${widget.doc?['reference_number'] ?? '—'} • ${widget.doc?['standard_family'] ?? ''}',
              style: TextStyle(color: p.blue, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              '${widget.doc?['title'] ?? ''}',
              style: TextStyle(
                color: p.title,
                fontSize: 20,
                fontWeight: FontWeight.w700,
              ),
            ),
            if ('${widget.doc?['description'] ?? ''}'.isNotEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: SelectableText('${widget.doc?['description']}'),
              ),
            Wrap(
              spacing: 16,
              runSpacing: 8,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Text(
                  updated == null
                      ? 'Date de modification indisponible'
                      : 'Dernière modification : $updated',
                ),
                TextButton(
                  onPressed: widget.doc?['ctm'] == null ? null : _groups,
                  child: Text(
                    '${widget.doc?['ctm_name'] ?? 'CTM non assignée'} — Voir groupes',
                  ),
                ),
                TextButton(
                  onPressed: widget.onOpenProfile,
                  child: Text('Éditeur : ${widget.userName}'),
                ),
              ],
            ),
            if (widget.loading) const LinearProgressIndicator(),
            const SizedBox(height: 16),
            // Le champ reste au même emplacement dans l’arbre lorsque les panneaux changent.
            LayoutBuilder(
              builder: (context, constraints) {
                final wide = constraints.maxWidth >= 900;
                return Wrap(
                  spacing: 20,
                  runSpacing: 16,
                  crossAxisAlignment: WrapCrossAlignment.start,
                  children: [
                    SizedBox(
                      width: wide && _right
                          ? (constraints.maxWidth - 20) * .64
                          : constraints.maxWidth,
                      child: editor,
                    ),
                    if (_right)
                      SizedBox(
                        width: wide
                            ? (constraints.maxWidth - 20) * .36
                            : constraints.maxWidth,
                        child: right,
                      ),
                  ],
                );
              },
            ),
            const SizedBox(height: 16),
            ExpertResources(
              key: ValueKey('resources-$_id'),
              documentId: _id!,
              userScope: widget.userScope,
            ),
            const SizedBox(height: 70),
          ],
        ),
      ),
    );
  }

  Widget _votePanel() {
    final p = ExpertTheme.of(context);
    final counts = {
      for (final choice in ['FOR', 'AGAINST', 'ABSTAIN'])
        choice: _votes.where((v) => v['vote'] == choice).length,
    };
    final total = _votes.length;
    final rate = total == 0 ? 0 : counts['FOR']! * 100 / total;
    final mine = _votes
        .where((v) => '${v['voter']}' == '$_expertId')
        .firstOrNull;
    return _panel(
      'SCRUTIN & ÉVALUATION THÉMATIQUE',
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Consensus affiché : 75 % minimum'),
          if (_voteError != null) ...[
            Text(_voteError!, style: TextStyle(color: p.red)),
            TextButton(
              onPressed: () => _loadVotes(_generation),
              child: const Text('Réessayer'),
            ),
          ],
          Text(
            'Taux de validation : ${rate.toStringAsFixed(0)} % — ${rate >= 75 ? 'Consensus atteint' : 'Avis partiel'}',
          ),
          const SizedBox(height: 8),
          if (total > 0)
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Row(
                children: [
                  for (final entry in counts.entries)
                    if (entry.value > 0)
                      Expanded(
                        flex: entry.value,
                        child: Container(
                          height: 8,
                          color: entry.key == 'FOR'
                              ? p.blue
                              : entry.key == 'AGAINST'
                              ? p.red
                              : p.subtle,
                        ),
                      ),
                ],
              ),
            ),
          const SizedBox(height: 8),
          Text(
            '$total expert(s) ont émargé — Votre vote : ${mine?['vote'] ?? 'Non voté'}',
          ),
          if (_closed) const Text('Le vote est clos pour cette norme.'),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final choice in [
                ('FOR', 'POUR'),
                ('AGAINST', 'CONTRE'),
                ('ABSTAIN', 'ABS.'),
              ])
                ChoiceChip(
                  label: Text('${choice.$2} (${counts[choice.$1]})'),
                  selected: mine?['vote'] == choice.$1,
                  onSelected: _voting || _closed || widget.loading
                      ? null
                      : (_) => _castVote(choice.$1),
                ),
            ],
          ),
          const SizedBox(height: 12),
          const Text('Registre d’émargement'),
          ConstrainedBox(
            constraints: const BoxConstraints(maxHeight: 180),
            child: ListView(
              shrinkWrap: true,
              children: [
                for (final vote in _votes)
                  ListTile(
                    dense: true,
                    title: Text(
                      '${vote['voter_name'] ?? 'Expert'}',
                      style: TextStyle(color: p.text),
                    ),
                    subtitle: Text(
                      '${vote['voter_structure'] ?? ''}',
                      style: TextStyle(color: p.muted),
                    ),
                    trailing: Text(
                      '${vote['vote']}',
                      style: TextStyle(color: p.blue),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
      close: () => setState(() => _voteOpen = false),
    );
  }

  Widget _aiPanel() {
    final p = ExpertTheme.of(context);
    final edits = expertRows(_advice?['edits']);
    return _panel(
      'CONSEIL RÉGLEMENTAIRE IA',
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Analyse de la rédaction et des exigences réglementaires.',
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: _analyzing || widget.loading ? null : _analyze,
            icon: const Icon(Icons.auto_awesome),
            label: Text(
              _analyzing
                  ? 'Analyse en cours…'
                  : 'Analyser & optimiser le texte',
            ),
          ),
          if (_advice != null) ...[
            const SizedBox(height: 12),
            SelectableText('${_advice!['summary'] ?? 'Analyse terminée.'}'),
            if (_advice!['fallback'] == true)
              Text(
                '${_advice!['error'] ?? 'Analyse indisponible : aucune correction vérifiée.'}',
                style: TextStyle(color: p.amber),
              ),
            Material(
              type: MaterialType.transparency,
              child: ExpansionTile(
                title: Text(
                  'Modifications proposées (${edits.length})',
                  style: TextStyle(color: p.text),
                ),
                initiallyExpanded: true,
                children: [
                  for (final edit in edits)
                    Padding(
                      padding: const EdgeInsets.all(8),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${edit['reason'] ?? ''} — ${edit['applied'] == true ? 'Applicable' : 'Non applicable'}',
                            style: TextStyle(color: p.text),
                          ),
                          SelectableText(
                            '${edit['find'] ?? ''}',
                            style: TextStyle(
                              color: p.red,
                              decoration: TextDecoration.lineThrough,
                            ),
                          ),
                          SelectableText(
                            '${edit['replace'] ?? ''}',
                            style: TextStyle(color: p.blue),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
            if (_analyzedText != _text.text)
              Text(
                'Texte modifié depuis l’analyse : relancez-la.',
                style: TextStyle(color: p.amber),
              ),
            Wrap(
              spacing: 8,
              children: [
                FilledButton(
                  onPressed:
                      _advice!['fallback'] == true ||
                          _analyzedText != _text.text ||
                          !edits.any((e) => e['applied'] == true)
                      ? null
                      : _applyAdvice,
                  child: const Text('Appliquer'),
                ),
                TextButton(
                  onPressed: () => setState(() {
                    _aiRequest++;
                    _analyzing = false;
                    _advice = null;
                  }),
                  child: const Text('Ignorer'),
                ),
              ],
            ),
          ],
        ],
      ),
      close: () => setState(() => _right = false),
    );
  }

  Widget _sharePanel() {
    final p = ExpertTheme.of(context);
    return SizedBox(
      key: _shareKey,
      child: _panel(
        'PARTAGER & DÉBATTRE',
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Surlignez du texte dans l’éditeur pour préremplir l’extrait.',
            ),
            const SizedBox(height: 12),
            TextField(
              key: const ValueKey('norm-share-excerpt'),
              controller: _excerpt,
              minLines: 3,
              maxLines: 6,
              onChanged: (_) => setState(() {}),
              style: TextStyle(color: p.text),
              decoration: _input('Extrait de clause sélectionné'),
            ),
            const SizedBox(height: 12),
            if (_contactsError != null) ...[
              Text(_contactsError!, style: TextStyle(color: p.red)),
              TextButton(
                onPressed: () => _loadData(_generation),
                child: const Text('Recharger les destinataires'),
              ),
            ],
            DropdownButtonFormField<String>(
              key: ValueKey('recipient-$_id'),
              initialValue: _recipient,
              isExpanded: true,
              decoration: _input('Expert destinataire'),
              dropdownColor: p.card,
              items: [
                for (final contact in _contacts)
                  DropdownMenuItem(
                    value: '${contact['user_id']}',
                    child: Text(
                      '${contact['user_name'] ?? 'Expert'}',
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(color: p.text),
                    ),
                  ),
              ],
              onChanged: (value) => setState(() => _recipient = value),
            ),
            if (_contacts.isEmpty && _contactsError == null)
              const Text('Aucun destinataire dans vos CTM.'),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed:
                  _sharing || _recipient == null || _excerpt.text.trim().isEmpty
                  ? null
                  : _share,
              icon: const Icon(Icons.chat_bubble_outline),
              label: Text(
                _sharing ? 'Envoi…' : 'Partager à l’expert & Ouvrir le Chat',
              ),
            ),
          ],
        ),
      ),
    );
  }
}

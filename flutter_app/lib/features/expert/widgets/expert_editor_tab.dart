import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_quill/flutter_quill.dart' as quill;
import 'package:url_launcher/url_launcher.dart';

import '../../../core/api/api_client.dart';
import '../../../core/rich_text/cnetp_markdown.dart';
import 'cnetp_rich_toolbar.dart';
import 'expert_messaging.dart';
import 'expert_module.dart' show expertDownload;
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
  final _comment = TextEditingController();
  final _excerpt = TextEditingController();
  final _focus = FocusNode();
  final _documentController = quill.QuillController.basic();
  late final _formatter = CnetpFormatter(_documentController);
  final _documentScroll = ScrollController();
  final _pageScroll = ScrollController();
  final _quillEditorKey = GlobalKey<quill.EditorState>();
  bool _loadingDocument = false;
  final _shareKey = GlobalKey();
  final _editorKey = GlobalKey();
  final _journalKey = GlobalKey();
  bool _right = true, _voteOpen = true, _saving = false, _voting = false;
  bool _analyzing = false, _sharing = false, _downloading = false;
  bool _layoutInitialized = false, _outlineOpen = false;
  int _generation = 0, _aiRequest = 0;

  /// Source Markdown CNE-ITP courante, dérivée du document Quill.
  String _source = '';
  String _plain = '';
  String _base = '';
  String? _recipient, _voteError, _contactsError;
  dynamic _expertId;
  List<Map<String, dynamic>> _votes = [], _contacts = [];
  Map<String, dynamic>? _advice;
  String? _analyzedText;
  final Map<String, ExpertDraft> _localDrafts = {};

  String? get _id => widget.doc?['id']?.toString();
  Map<String, ExpertDraft> get _drafts => widget.drafts ?? _localDrafts;
  bool get _dirty => _source != _base || _comment.text.isNotEmpty;
  bool get _closed => ['PUBLISHED', 'ARCHIVED'].contains(widget.doc?['status']);
  bool get _compact => MediaQuery.sizeOf(context).width < 700;

  @override
  void initState() {
    super.initState();
    _documentController.addListener(_onDocument);
    _comment.addListener(_onComment);
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

  void _readDocument() {
    final document = _documentController.document;
    _source = cnetpFromDelta(document.toDelta().toJson());
    final plain = document.toPlainText();
    _plain = plain.endsWith('\n')
        ? plain.substring(0, plain.length - 1)
        : plain;
  }

  /// Charge [source] dans l’éditeur sans déclencher l’enregistrement du brouillon.
  void _load(String source, [String format = cnetpFormatMarkdown]) {
    _loadingDocument = true;
    try {
      _documentController.document = quill.Document.fromJson(
        cnetpToDelta(source, format),
      );
      _readDocument();
    } finally {
      _loadingDocument = false;
    }
  }

  void _recordDraft() {
    if (_id != null) {
      _drafts[_id!] = ExpertDraft(_source, _comment.text, _base);
    }
  }

  void _onDocument() {
    if (_loadingDocument) return;
    final previous = _source;
    _readDocument();
    if (_source != previous) _recordDraft();
    final selection = _documentController.selection;
    if (selection.isValid && !selection.isCollapsed) {
      final selected = _documentController.document
          .getPlainText(selection.start, selection.end - selection.start)
          .trim();
      if (selected.isNotEmpty && _excerpt.text != selected) {
        _excerpt.text = selected;
        if (!_compact) _right = true;
      }
    }
    if (mounted) setState(() {});
  }

  void _onComment() {
    _recordDraft();
    if (mounted) setState(() {});
  }

  void _setText(String source) {
    _load(source);
    _recordDraft();
    if (mounted) setState(() {});
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_layoutInitialized) {
      _layoutInitialized = true;
      if (_compact) {
        _right = false;
        _voteOpen = false;
      }
    }
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
    final format = version is Map && version['content_format'] is String
        ? version['content_format'] as String
        : cnetpFormatPlain;
    // Le texte brut historique est converti une fois : la référence de
    // comparaison est donc le Markdown normalisé, pas le contenu stocké.
    _load(
      content as String? ?? widget.doc?['content'] as String? ?? '',
      format,
    );
    _base = _source;
    final stored = _drafts[_id];
    final draft =
        stored != null &&
            (stored.text != stored.base || stored.comment.isNotEmpty)
        ? stored
        : null;
    if (draft != null) {
      _load(draft.text);
      _base = draft.base;
    }
    _comment.removeListener(_onComment);
    _comment.text = draft?.comment ?? '';
    _comment.addListener(_onComment);
    if (_id != null) _loadData(_generation);
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
    if (_closed || _compact) {
      _notify(
        _closed
            ? 'Cette norme est publiée ou archivée : elle est en lecture seule.'
            : 'La rédaction est disponible uniquement sur la version ordinateur.',
      );
      return;
    }
    final text = _source, comment = _comment.text.trim();
    if (_plain.trim().isEmpty || comment.isEmpty) {
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
          'content_format': cnetpFormatMarkdown,
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
      setState(() {});
      widget.onSave();
      _notify('Nouvelle version sauvegardée.');
    } catch (error) {
      if (mounted && generation == _generation) _notify(expertError(error));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _downloadPdf() async {
    final id = _id;
    if (id == null || _downloading) return;
    setState(() => _downloading = true);
    try {
      final reference = '${widget.doc?['reference_number'] ?? 'norme'}';
      await expertDownload('/api/v1/norms/$id/pdf/', '$reference.pdf');
      _notify('PDF téléchargé.');
    } catch (error) {
      _notify(expertError(error));
    } finally {
      if (mounted) setState(() => _downloading = false);
    }
  }

  Future<void> _castVote(String choice) async {
    if (_closed) return;
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
    if (_plain.trim().isEmpty) {
      _notify('Saisissez du texte à analyser.');
      return;
    }
    final request = ++_aiRequest, generation = _generation;
    final text = _source;
    setState(() {
      _analyzing = true;
      _advice = null;
    });
    try {
      final response = await ApiClient.dio.post(
        '/api/v1/ia-agent/sessions/regulatory-advice/',
        data: {
          'text': text,
          'content_format': cnetpFormatMarkdown,
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
    if (_closed || _compact) {
      _notify(
        _closed
            ? 'Cette norme est publiée ou archivée : elle est en lecture seule.'
            : 'La rédaction est disponible uniquement sur la version ordinateur.',
      );
      return;
    }
    if (_source != _analyzedText) {
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
    _setText(applied);
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
    _documentController.removeListener(_onDocument);
    _documentController.dispose();
    _documentScroll.dispose();
    _pageScroll.dispose();
    _comment.dispose();
    _excerpt.dispose();
    _focus.dispose();
    super.dispose();
  }

  void _revealShare() {
    setState(() => _right = true);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted && _shareKey.currentContext != null) {
        Scrollable.ensureVisible(
          _shareKey.currentContext!,
          duration: const Duration(milliseconds: 250),
        );
      }
    });
  }

  Future<void> _openLink(String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null || !cnetpIsSafeUrl(url)) {
      _notify('Lien non autorisé.');
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Ouvrir le lien ?'),
        content: SelectableText(
          'Vous allez quitter l’espace CNE-ITP pour :\n$url',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Ouvrir'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
        _notify('Impossible d’ouvrir ce lien.');
      }
    } catch (_) {
      _notify('Impossible d’ouvrir ce lien.');
    }
  }

  void _scrollToHeading(CnetpHeading heading) {
    final renderEditor = _quillEditorKey.currentState?.renderEditor;
    if (renderEditor == null) return;
    final rect = renderEditor.getLocalRectForCaret(
      TextPosition(offset: heading.offset),
    );
    renderEditor.showOnScreen(
      rect: rect.inflate(24),
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeOut,
    );
  }

  Widget _outline(List<CnetpHeading> headings) {
    final p = ExpertTheme.of(context);
    return Container(
      key: const ValueKey('norm-outline'),
      margin: const EdgeInsets.only(top: 12),
      decoration: BoxDecoration(
        color: p.surface,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: p.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          InkWell(
            borderRadius: BorderRadius.circular(10),
            onTap: () => setState(() => _outlineOpen = !_outlineOpen),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              child: Row(
                children: [
                  Icon(Icons.toc, size: 18, color: p.blue),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Sommaire (${headings.length})',
                      style: TextStyle(
                        color: p.title,
                        fontWeight: FontWeight.w700,
                        fontSize: ExpertType.meta,
                      ),
                    ),
                  ),
                  Icon(
                    _outlineOpen ? Icons.expand_less : Icons.expand_more,
                    color: p.muted,
                  ),
                ],
              ),
            ),
          ),
          if (_outlineOpen)
            for (final heading in headings)
              InkWell(
                onTap: () => _scrollToHeading(heading),
                child: Padding(
                  padding: EdgeInsets.fromLTRB(
                    12.0 + (heading.level - 1) * 14,
                    8,
                    12,
                    8,
                  ),
                  child: Text(
                    heading.text,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: heading.level == 1 ? p.title : p.text,
                      fontSize: ExpertType.meta,
                      fontWeight: heading.level == 1
                          ? FontWeight.w700
                          : FontWeight.w500,
                    ),
                  ),
                ),
              ),
        ],
      ),
    );
  }

  Widget _panel(String title, Widget child, {VoidCallback? close}) {
    final p = ExpertTheme.of(context);
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(_compact ? 12 : 16),
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
                    fontSize: _compact ? ExpertType.meta : ExpertType.body,
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
          SizedBox(height: _compact ? 8 : 12),
          child,
        ],
      ),
    );
  }

  InputDecoration _input(String label) {
    final p = ExpertTheme.of(context);
    return InputDecoration(
      labelText: label,
      labelStyle: TextStyle(
        color: p.muted,
        fontSize: _compact ? ExpertType.meta : ExpertType.body,
      ),
      isDense: _compact,
      filled: true,
      fillColor: p.field,
      border: const OutlineInputBorder(),
      contentPadding: EdgeInsets.all(_compact ? 10 : 12),
    );
  }

  Widget _versionActions() {
    final canSave =
        !_saving &&
        !widget.loading &&
        _dirty &&
        _plain.trim().isNotEmpty &&
        _comment.text.trim().isNotEmpty;
    void reset() {
      _setText(_base);
      _comment.clear();
      setState(() => _advice = null);
    }

    final save = FilledButton.icon(
      key: const ValueKey('norm-save-version'),
      onPressed: canSave ? _save : null,
      icon: const Icon(Icons.save_outlined, size: 18),
      label: Text(
        _saving
            ? 'Sauvegarde…'
            : (_compact ? 'Enregistrer' : 'Sauvegarder la version'),
      ),
    );
    if (_compact) {
      return Row(
        children: [
          IconButton.outlined(
            key: const ValueKey('norm-reset-version'),
            onPressed: !_dirty || _saving ? null : reset,
            tooltip: 'Réinitialiser les modifications',
            icon: const Icon(Icons.rotate_left, size: 18),
          ),
          const SizedBox(width: 8),
          Expanded(child: save),
        ],
      );
    }
    return Wrap(
      spacing: 12,
      runSpacing: 8,
      alignment: WrapAlignment.spaceBetween,
      children: [
        TextButton.icon(
          onPressed: !_dirty || _saving ? null : reset,
          icon: const Icon(Icons.rotate_left),
          label: const Text('Réinitialiser'),
        ),
        save,
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    final compact = _compact;
    _documentController.readOnly = widget.loading || _closed || compact;
    final baseTheme = Theme.of(context);
    final controls = ButtonStyle(
      minimumSize: const WidgetStatePropertyAll(Size(40, 40)),
      padding: const WidgetStatePropertyAll(
        EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      ),
      textStyle: const WidgetStatePropertyAll(
        TextStyle(fontSize: ExpertType.meta, fontWeight: FontWeight.w600),
      ),
      iconSize: const WidgetStatePropertyAll(16),
      shape: WidgetStatePropertyAll(
        RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    );
    final editorTheme = compact
        ? baseTheme.copyWith(
            filledButtonTheme: FilledButtonThemeData(
              style:
                  baseTheme.filledButtonTheme.style?.merge(controls) ??
                  controls,
            ),
            outlinedButtonTheme: OutlinedButtonThemeData(
              style:
                  baseTheme.outlinedButtonTheme.style?.merge(controls) ??
                  controls,
            ),
            textButtonTheme: TextButtonThemeData(
              style:
                  baseTheme.textButtonTheme.style?.merge(controls) ?? controls,
            ),
            iconButtonTheme: IconButtonThemeData(
              style: const ButtonStyle(
                minimumSize: WidgetStatePropertyAll(Size(40, 40)),
                iconSize: WidgetStatePropertyAll(18),
              ),
            ),
          )
        : baseTheme;
    if (widget.doc == null) {
      return Center(
        child: widget.loading
            ? const CircularProgressIndicator()
            : Text(
                'Aucun document sélectionné',
                style: TextStyle(color: p.muted),
              ),
      );
    }
    final words = _plain.trim().isEmpty
        ? 0
        : _plain.trim().split(RegExp(r'\s+')).length;
    final latestVersion = widget.doc?['latest_version'];
    final latestComment = latestVersion is Map
        ? '${latestVersion['comment'] ?? ''}'.trim()
        : '';
    final updated = DateTime.tryParse(
      '${widget.doc?['updated_at']}',
    )?.toLocal();
    final quillConfig = quill.QuillEditorConfig(
      editorKey: _quillEditorKey,
      scrollable: !compact,
      expands: !compact,
      padding: compact ? EdgeInsets.zero : const EdgeInsets.all(16),
      placeholder: compact ? 'Aucun contenu' : 'Écrivez le standard ici…',
      customStyles: cnetpQuillStyles(p, compact: compact),
      customStyleBuilder: cnetpStyleBuilder(p),
      onLaunchUrl: _openLink,
      customShortcuts: cnetpShortcuts(),
      customActions: cnetpActions(context, _formatter),
      contextMenuBuilder: (context, state) => cnetpContextMenu(
        context,
        state,
        _formatter,
        onShare: compact ? null : _revealShare,
      ),
    );
    final outline = compact
        ? cnetpOutline(_documentController.document.toDelta().toJson())
        : const <CnetpHeading>[];
    final editor = Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _panel(
          'TEXTE DE LA NORME',
          Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                '${_plain.length} caractères • $words mots',
                style: TextStyle(
                  color: p.subtle,
                  fontSize: compact ? ExpertType.label : ExpertType.body,
                ),
              ),
              if (compact && outline.isNotEmpty) _outline(outline),
              if (compact)
                Padding(
                  key: _editorKey,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: quill.QuillEditor(
                    key: const ValueKey('norm-editor-text'),
                    controller: _documentController,
                    focusNode: _focus,
                    scrollController: _documentScroll,
                    config: quillConfig,
                  ),
                )
              else
                Container(
                  key: _editorKey,
                  margin: const EdgeInsets.only(top: 12),
                  height: _right ? 360 : 500,
                  decoration: BoxDecoration(
                    color: p.field,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: _focus.hasFocus ? p.blue : p.border,
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      CnetpRichToolbar(formatter: _formatter),
                      Expanded(
                        child: quill.QuillEditor(
                          key: const ValueKey('norm-editor-text'),
                          controller: _documentController,
                          focusNode: _focus,
                          scrollController: _documentScroll,
                          config: quillConfig,
                        ),
                      ),
                    ],
                  ),
                ),
              if (!compact)
                Wrap(
                  spacing: 8,
                  children: [
                    TextButton.icon(
                      key: const ValueKey('editor-ai-toggle'),
                      onPressed: () => setState(() {
                        _right = !_right;
                        _focus.unfocus();
                      }),
                      icon: const Icon(Icons.auto_awesome),
                      label: Text(
                        _right
                            ? 'Masquer IA / partage'
                            : 'Afficher IA / partage',
                      ),
                    ),
                    TextButton.icon(
                      key: const ValueKey('editor-vote-toggle'),
                      onPressed: () => setState(() => _voteOpen = !_voteOpen),
                      icon: const Icon(Icons.how_to_vote_outlined),
                      label: Text(
                        _voteOpen
                            ? 'Masquer le scrutin'
                            : 'Afficher le scrutin',
                      ),
                    ),
                    if (_excerpt.text.isNotEmpty)
                      TextButton.icon(
                        onPressed: _revealShare,
                        icon: const Icon(Icons.share),
                        label: const Text('Partager la sélection'),
                      ),
                  ],
                ),
            ],
          ),
        ),
        SizedBox(height: compact ? 12 : 16),
        if (!compact && _voteOpen) ...[
          _votePanel(),
          SizedBox(height: compact ? 12 : 16),
        ],
        if (_closed)
          _panel(
            'VERSION PUBLIÉE — LECTURE SEULE',
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Le contenu et les votes sont figés. Vous pouvez consulter, partager ou télécharger le PDF.',
                ),
                if (latestComment.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  SelectableText('Dernier commentaire : $latestComment'),
                ],
              ],
            ),
          )
        else if (compact)
          _panel(
            'LECTURE SEULE SUR MOBILE',
            const Text(
              'La modification et la création de versions sont disponibles uniquement sur la version ordinateur.',
            ),
          )
        else
          _panel(
            'JOURNAL DES VERSIONS / COMMENTAIRE',
            Column(
              key: _journalKey,
              children: [
                TextField(
                  key: const ValueKey('norm-editor-comment'),
                  controller: _comment,
                  style: TextStyle(color: p.text, fontSize: ExpertType.body),
                  minLines: compact ? 2 : 1,
                  maxLines: compact ? 3 : 1,
                  decoration: _input('Commentaire obligatoire'),
                ),
                const SizedBox(height: 12),
                _versionActions(),
              ],
            ),
          ),
      ],
    );
    final right = Column(
      children: [_aiPanel(), const SizedBox(height: 16), _sharePanel()],
    );
    final page = SingleChildScrollView(
      controller: _pageScroll,
      padding: compact
          ? const EdgeInsets.fromLTRB(12, 12, 12, expertFabClearance)
          : const EdgeInsets.fromLTRB(24, 24, 24, expertFabClearance),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${widget.doc?['reference_number'] ?? '—'} • ${widget.doc?['standard_family'] ?? ''}',
            style: TextStyle(
              color: p.blue,
              fontWeight: FontWeight.bold,
              fontSize: compact ? 11 : 14,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '${widget.doc?['title'] ?? ''}',
            style: TextStyle(
              color: p.title,
              fontSize: compact ? 18 : 20,
              fontWeight: FontWeight.w700,
            ),
          ),
          if ('${widget.doc?['description'] ?? ''}'.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: SelectableText('${widget.doc?['description']}'),
            ),
          if (_closed)
            Container(
              width: double.infinity,
              margin: const EdgeInsets.only(top: 4, bottom: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: p.amber.withValues(alpha: .12),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: p.amber.withValues(alpha: .45)),
              ),
              child: Text(
                '${widget.doc?['status'] == 'ARCHIVED' ? 'Norme archivée' : 'Norme publiée'} : consultation en lecture seule.',
                style: TextStyle(color: p.amber, fontWeight: FontWeight.w600),
              ),
            ),
          Wrap(
            spacing: compact ? 8 : 16,
            runSpacing: compact ? 0 : 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              Text(
                updated == null
                    ? 'Date de modification indisponible'
                    : compact
                    ? 'Modifié le ${updated.day.toString().padLeft(2, '0')}/${updated.month.toString().padLeft(2, '0')}/${updated.year} à ${updated.hour.toString().padLeft(2, '0')}:${updated.minute.toString().padLeft(2, '0')}'
                    : 'Dernière modification : $updated',
                style: TextStyle(color: p.muted, fontSize: compact ? 11 : 14),
              ),
              TextButton(
                onPressed: widget.doc?['ctm'] == null ? null : _groups,
                child: Text(
                  compact
                      ? 'Voir groupes'
                      : '${widget.doc?['ctm_name'] ?? 'CTM non assignée'} — Voir groupes',
                ),
              ),
              TextButton(
                onPressed: widget.onOpenProfile,
                child: Text(
                  compact
                      ? 'Consultation : ${widget.userName}'
                      : 'Éditeur : ${widget.userName}',
                  maxLines: compact ? 1 : null,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              OutlinedButton.icon(
                onPressed: _id == null || _downloading ? null : _downloadPdf,
                icon: const Icon(Icons.picture_as_pdf_outlined, size: 18),
                label: Text(
                  _downloading
                      ? 'PDF…'
                      : (compact ? 'PDF' : 'Télécharger le PDF'),
                ),
              ),
            ],
          ),
          if (widget.loading) const LinearProgressIndicator(),
          SizedBox(height: compact ? 12 : 16),
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
                    width: wide && !compact && _right
                        ? (constraints.maxWidth - 20) * .64
                        : constraints.maxWidth,
                    child: editor,
                  ),
                  if (!compact && _right)
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
          if (!compact) ...[
            const SizedBox(height: 16),
            ExpertResources(
              key: ValueKey('resources-$_id'),
              documentId: _id!,
              userScope: widget.userScope,
            ),
          ],
          const SizedBox(height: 24),
        ],
      ),
    );
    return Theme(
      data: editorTheme,
      child: DefaultTextStyle(
        style: TextStyle(
          color: p.text,
          fontSize: ExpertType.body,
          height: ExpertType.bodyHeight,
        ),
        child: compact
            ? page
            : Scrollbar(
                key: const ValueKey('norm-desktop-scrollbar'),
                controller: _pageScroll,
                thumbVisibility: true,
                thickness: 7,
                radius: const Radius.circular(999),
                child: page,
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
                  color: WidgetStateProperty.resolveWith((states) {
                    if (states.contains(WidgetState.disabled)) return p.surface;
                    if (states.contains(WidgetState.selected)) {
                      return p.blueSoft;
                    }
                    return p.field;
                  }),
                  side: BorderSide(color: p.borderStrong),
                  surfaceTintColor: Colors.transparent,
                  elevation: 0,
                  pressElevation: 0,
                  checkmarkColor: p.isDark ? p.text : p.blueDeep,
                  labelStyle: TextStyle(color: p.text),
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
                  : (_compact
                        ? 'Analyser le texte'
                        : 'Analyser & optimiser le texte'),
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
            if (_analyzedText != _source)
              Text(
                'Texte modifié depuis l’analyse : relancez-la.',
                style: TextStyle(color: p.amber),
              ),
            Wrap(
              spacing: 8,
              children: [
                if (!_compact)
                  FilledButton(
                    onPressed:
                        _closed ||
                            _advice!['fallback'] == true ||
                            _analyzedText != _source ||
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
            const SizedBox(height: 8),
            TextField(
              key: const ValueKey('norm-share-excerpt'),
              controller: _excerpt,
              minLines: 2,
              maxLines: 4,
              onChanged: (_) => setState(() {}),
              style: TextStyle(color: p.text),
              decoration: _input('Extrait de clause sélectionné'),
            ),
            const SizedBox(height: 8),
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
            const SizedBox(height: 8),
            FilledButton.icon(
              onPressed:
                  _sharing || _recipient == null || _excerpt.text.trim().isEmpty
                  ? null
                  : _share,
              icon: const Icon(Icons.chat_bubble_outline),
              label: Text(
                _sharing
                    ? 'Envoi…'
                    : (_compact
                          ? 'Partager et ouvrir le chat'
                          : 'Partager à l’expert & Ouvrir le Chat'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

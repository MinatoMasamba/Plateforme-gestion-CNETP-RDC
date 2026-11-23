import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/api/api_client.dart';
import 'expert_download.dart';
import 'expert_theme.dart';

class ExpertAssistant extends StatefulWidget {
  const ExpertAssistant({super.key, this.norm});

  final Map<String, dynamic>? norm;

  @override
  State<ExpertAssistant> createState() => _ExpertAssistantState();
}

class _ExpertAssistantState extends State<ExpertAssistant> {
  final _input = TextEditingController();
  final _scroll = ScrollController();
  List<Map<String, dynamic>> _sessions = [];
  List<Map<String, dynamic>> _messages = [];
  List<Map<String, dynamic>> _artifacts = [];
  int? _sessionId;
  bool _loading = true, _sending = false;
  String? _error;

  static const _suggestions = [
    'Résumer la norme ouverte',
    'Vérifier la conformité ISO',
    'Expliquer un terme',
    'Préparer un commentaire',
  ];

  @override
  void initState() {
    super.initState();
    _input.addListener(_onInputChanged);
    _loadSessions();
  }

  void _onInputChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _loadSessions() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await ApiClient.dio.get('/api/v1/ia-agent/sessions/');
      if (!mounted) return;
      setState(() {
        _sessions = _expertRows(
          response.data,
        ).where((session) => session['scope'] == 'expert').toList();
        _loading = false;
      });
    } catch (error) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = _assistantError(error);
        });
      }
    }
  }

  Future<void> _selectSession(int id) async {
    setState(() {
      _sessionId = id;
      _loading = true;
      _messages = [];
      _artifacts = [];
      _error = null;
    });
    try {
      final responses = await Future.wait([
        ApiClient.dio.get('/api/v1/ia-agent/sessions/$id/messages/'),
        ApiClient.dio.get('/api/v1/ia-agent/artifacts/'),
      ]);
      if (!mounted) return;
      setState(() {
        _messages = _expertRows(responses[0].data);
        _artifacts = _expertRows(
          responses[1].data,
        ).where((artifact) => '${artifact['session']}' == '$id').toList();
        _loading = false;
      });
      _toBottom();
    } catch (error) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = _assistantError(error);
        });
      }
    }
  }

  void _newConversation() {
    setState(() {
      _sessionId = null;
      _messages = [];
      _artifacts = [];
      _input.clear();
      _error = null;
    });
  }

  Future<void> _send([String? suggestion]) async {
    final entered = (suggestion ?? _input.text).trim();
    if (_sending || entered.isEmpty) return;
    final displayMessage = suggestion == null ? entered : entered;
    final content = _withNormContext(entered, widget.norm);
    setState(() {
      _sending = true;
      _error = null;
      if (displayMessage.isNotEmpty) {
        _messages.add({
          'id': 'local-${DateTime.now().microsecondsSinceEpoch}',
          'role': 'user',
          'content': displayMessage,
        });
      }
      _input.clear();
    });
    _toBottom();
    try {
      var sessionId = _sessionId;
      if (sessionId == null) {
        final response = await ApiClient.dio.post(
          '/api/v1/ia-agent/sessions/',
          data: {'scope': 'expert', 'title': entered, 'provider': 'deepseek'},
        );
        sessionId = (response.data as Map)['id'] as int;
        _sessionId = sessionId;
        await ApiClient.dio.post('/api/v1/ia-agent/sessions/$sessionId/init/');
      }
      final response = await ApiClient.dio.post(
        '/api/v1/ia-agent/sessions/$sessionId/send/',
        data: {'content': content},
        options: Options(receiveTimeout: const Duration(seconds: 70)),
      );
      if (!mounted) return;
      final body = Map<String, dynamic>.from(response.data as Map);
      final message = body['assistant_message'];
      setState(() {
        if (message is Map) {
          _messages.add(Map<String, dynamic>.from(message));
        }
        _artifacts.addAll(_expertRows(body['artifacts']));
      });
      await _loadSessions();
      if (mounted) _toBottom();
    } catch (error) {
      if (mounted) {
        setState(() {
          _messages.removeWhere(
            (message) =>
                message['role'] == 'user' &&
                message['content'] == displayMessage,
          );
          _error = _assistantError(error);
          _input.text = displayMessage;
        });
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _approve(Map<String, dynamic> artifact) async {
    try {
      final response = await ApiClient.dio.post(
        '/api/v1/ia-agent/artifacts/${artifact['id']}/approve/',
      );
      if (!mounted) return;
      setState(() {
        final index = _artifacts.indexWhere(
          (item) => item['id'] == artifact['id'],
        );
        if (index >= 0) {
          _artifacts[index] = Map<String, dynamic>.from(response.data as Map);
        }
        _error = null;
      });
      _notify('Artefact approuvé.');
    } catch (error) {
      if (mounted) setState(() => _error = _assistantError(error));
    }
  }

  Future<void> _download(Map<String, dynamic> artifact) async {
    try {
      await expertDownload(
        '/api/v1/ia-agent/artifacts/${artifact['id']}/download-pdf/',
        'demande-wg-${artifact['id']}.pdf',
      );
      _notify('PDF téléchargé.');
    } catch (error) {
      if (mounted) setState(() => _error = _assistantError(error));
    }
  }

  void _notify(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
    );
  }

  void _toBottom() => WidgetsBinding.instance.addPostFrameCallback((_) {
    if (mounted && _scroll.hasClients) {
      _scroll.animateTo(
        _scroll.position.maxScrollExtent,
        duration: const Duration(milliseconds: 180),
        curve: Curves.easeOut,
      );
    }
  });

  @override
  void dispose() {
    _input
      ..removeListener(_onInputChanged)
      ..dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final mobile = MediaQuery.sizeOf(context).width < 700;
    final p = ExpertTheme.of(context);
    final body = Row(
      children: [
        if (!mobile)
          SizedBox(
            key: const ValueKey('assistant-history'),
            width: ExpertCommunicationLayout.historyWidth(
              ExpertCommunicationLayout.contentWidth(
                MediaQuery.sizeOf(context).width,
              ),
            ),
            child: _AssistantHistory(
              sessions: _sessions,
              selectedId: _sessionId,
              loading: _loading,
              onNew: _newConversation,
              onSelect: _selectSession,
            ),
          ),
        Expanded(
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.fromLTRB(14, 8, 14, 8),
                decoration: BoxDecoration(
                  color: p.card,
                  border: Border(bottom: BorderSide(color: p.border)),
                ),
                child: _readingFrame(
                  Row(
                    children: [
                      CircleAvatar(
                        backgroundColor: p.blueSoft,
                        child: Icon(Icons.auto_awesome, color: p.blue),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Neronne · Assistant Expert',
                              style: TextStyle(
                                color: p.title,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            Text(
                              'Accompagnement normatif et rédactionnel',
                              style: TextStyle(
                                color: p.muted,
                                fontSize: ExpertType.meta,
                              ),
                            ),
                          ],
                        ),
                      ),
                      if (mobile)
                        PopupMenuButton<String>(
                          tooltip: 'Historique des sessions',
                          icon: const Icon(Icons.history),
                          onSelected: (value) {
                            if (value == 'new') {
                              _newConversation();
                            } else {
                              _selectSession(int.parse(value));
                            }
                          },
                          itemBuilder: (_) => [
                            const PopupMenuItem(
                              value: 'new',
                              child: Text('Nouvelle conversation'),
                            ),
                            if (_sessions.isNotEmpty) const PopupMenuDivider(),
                            for (final session in _sessions)
                              PopupMenuItem(
                                value: '${session['id']}',
                                child: Text(
                                  '${session['title'] ?? 'Conversation IA'}',
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                          ],
                        ),
                    ],
                  ),
                ),
              ),
              if (widget.norm != null)
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                  child: _readingFrame(_NormContext(norm: widget.norm!)),
                ),
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 10, 16, 0),
                  child: _readingFrame(
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: p.red.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: p.red.withValues(alpha: 0.24),
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.smart_toy_outlined, color: p.red),
                          const SizedBox(width: 9),
                          Expanded(
                            child: Text(
                              _error!,
                              style: TextStyle(color: p.red),
                            ),
                          ),
                          TextButton(
                            onPressed: _loadSessions,
                            child: const Text('Réessayer'),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              Expanded(
                child: _readingFrame(
                  _loading && _messages.isEmpty
                      ? const Center(child: CircularProgressIndicator())
                      : _messages.isEmpty
                      ? _AssistantWelcome(onSuggestion: _send)
                      : ListView(
                          key: const ValueKey('assistant-reading-frame'),
                          controller: _scroll,
                          padding: EdgeInsets.fromLTRB(
                            mobile ? 18 : 24,
                            mobile ? 18 : 24,
                            mobile ? 18 : 24,
                            10,
                          ),
                          children: [
                            for (final message in _messages)
                              _AssistantMessage(message: message),
                            for (final artifact in _artifacts)
                              _ArtifactCard(
                                artifact: artifact,
                                onApprove: () => _approve(artifact),
                                onDownload: () => _download(artifact),
                              ),
                            if (_sending)
                              Padding(
                                padding: const EdgeInsets.only(
                                  top: 8,
                                  bottom: 12,
                                ),
                                child: Row(
                                  children: [
                                    const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                      ),
                                    ),
                                    const SizedBox(width: 10),
                                    Text(
                                      'L’assistant rédige…',
                                      style: TextStyle(
                                        color: p.muted,
                                        fontStyle: FontStyle.italic,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                          ],
                        ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
                child: _readingFrame(
                  Row(
                    children: [
                      Icon(Icons.info_outline, size: 15, color: p.amber),
                      const SizedBox(width: 7),
                      Expanded(
                        child: Text(
                          'Réponses générées par IA — à vérifier avant usage officiel',
                          style: TextStyle(
                            color: p.amber,
                            fontSize: ExpertType.label,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              SafeArea(
                top: false,
                child: Container(
                  padding: const EdgeInsets.fromLTRB(14, 10, 14, 12),
                  decoration: BoxDecoration(
                    color: p.card,
                    border: Border(top: BorderSide(color: p.border)),
                  ),
                  child: _readingFrame(
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _input,
                            minLines: 1,
                            maxLines: 5,
                            enabled: !_sending,
                            textInputAction: TextInputAction.send,
                            onSubmitted: (_) => _send(),
                            decoration: const InputDecoration(
                              hintText: 'Posez votre question à l’assistant…',
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.all(
                                  Radius.circular(24),
                                ),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        FilledButton(
                          onPressed: _input.text.trim().isEmpty || _sending
                              ? null
                              : _send,
                          style: FilledButton.styleFrom(
                            minimumSize: const Size(46, 46),
                            padding: EdgeInsets.zero,
                            shape: const CircleBorder(),
                          ),
                          child: _sending
                              ? const SizedBox.square(
                                  dimension: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(Icons.arrow_upward),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
    if (mobile) return body;
    return LayoutBuilder(
      builder: (context, constraints) {
        final frameWidth = ExpertCommunicationLayout.contentWidth(
          constraints.maxWidth,
        );
        return Center(
          child: SizedBox(
            key: const ValueKey('assistant-desktop-frame'),
            width: frameWidth,
            height: constraints.maxHeight,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: p.card,
                border: Border.symmetric(vertical: BorderSide(color: p.border)),
              ),
              child: body,
            ),
          ),
        );
      },
    );
  }

  Widget _readingFrame(Widget child) {
    if (MediaQuery.sizeOf(context).width < 700) return child;
    return Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(
        constraints: const BoxConstraints(
          maxWidth: ExpertCommunicationLayout.readingWidth,
        ),
        child: child,
      ),
    );
  }
}

class _AssistantHistory extends StatelessWidget {
  const _AssistantHistory({
    required this.sessions,
    required this.selectedId,
    required this.loading,
    required this.onNew,
    required this.onSelect,
  });

  final List<Map<String, dynamic>> sessions;
  final int? selectedId;
  final bool loading;
  final VoidCallback onNew;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: p.card,
        border: Border(right: BorderSide(color: p.border)),
      ),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(14),
            child: FilledButton.icon(
              onPressed: onNew,
              icon: const Icon(Icons.add_comment_outlined),
              label: const Text('Nouvelle conversation'),
            ),
          ),
          Expanded(
            child: loading && sessions.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : sessions.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Text(
                        'Aucun historique pour le moment.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: p.muted),
                      ),
                    ),
                  )
                : ListView.builder(
                    itemCount: sessions.length,
                    itemBuilder: (context, index) {
                      final session = sessions[index];
                      final selected = session['id'] == selectedId;
                      return Material(
                        color: selected ? p.blueSoft : Colors.transparent,
                        child: ListTile(
                          selected: selected,
                          onTap: () => onSelect(session['id'] as int),
                          leading: Icon(
                            Icons.chat_bubble_outline,
                            color: selected ? p.blue : p.muted,
                            size: 19,
                          ),
                          title: Text(
                            '${session['title'] ?? 'Conversation IA'}',
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          subtitle: Text(
                            _sessionDate(session['updated_at']),
                            style: TextStyle(
                              color: p.subtle,
                              fontSize: ExpertType.label,
                            ),
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

class _AssistantWelcome extends StatelessWidget {
  const _AssistantWelcome({required this.onSuggestion});

  final ValueChanged<String> onSuggestion;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return SingleChildScrollView(
      padding: const EdgeInsets.all(28),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 660),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 66,
                height: 66,
                decoration: BoxDecoration(
                  color: p.blueSoft,
                  shape: BoxShape.circle,
                ),
                child: Icon(Icons.auto_awesome, color: p.blue, size: 30),
              ),
              const SizedBox(height: 18),
              Text(
                'Bonjour, comment puis-je vous aider ?',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: p.title,
                  fontSize: 22,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Je peux vous aider à analyser, résumer et préparer vos contributions normatives.',
                textAlign: TextAlign.center,
                style: TextStyle(color: p.muted, height: 1.45),
              ),
              const SizedBox(height: 24),
              Wrap(
                alignment: WrapAlignment.center,
                spacing: 10,
                runSpacing: 10,
                children: [
                  for (final suggestion in _ExpertAssistantState._suggestions)
                    ActionChip(
                      avatar: const Icon(Icons.arrow_outward, size: 17),
                      label: Text(suggestion),
                      onPressed: () => onSuggestion(suggestion),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _NormContext extends StatelessWidget {
  const _NormContext({required this.norm});
  final Map<String, dynamic> norm;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    final reference = '${norm['reference_number'] ?? norm['code'] ?? ''}';
    final title = '${norm['title'] ?? ''}';
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: p.blueSoft,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: p.blue.withValues(alpha: 0.25)),
      ),
      child: Row(
        children: [
          Icon(Icons.description_outlined, color: p.blue),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  reference.isEmpty ? 'Norme ouverte' : reference,
                  style: TextStyle(color: p.blue, fontWeight: FontWeight.w700),
                ),
                if (title.isNotEmpty)
                  Text(
                    title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(color: p.text),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _AssistantMessage extends StatelessWidget {
  const _AssistantMessage({required this.message});
  final Map<String, dynamic> message;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    final user = message['role'] == 'user';
    final content = '${message['content'] ?? ''}';
    return Align(
      alignment: user ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.sizeOf(context).width >= 700
              ? ExpertCommunicationLayout.readingWidth
              : MediaQuery.sizeOf(context).width * 0.76,
        ),
        margin: const EdgeInsets.only(bottom: 14),
        padding: const EdgeInsets.all(13),
        decoration: BoxDecoration(
          color: user ? p.blue : p.card,
          border: user ? null : Border.all(color: p.border),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (user)
              SelectableText(
                content,
                style: const TextStyle(color: Colors.white, height: 1.4),
              )
            else
              ExpertMarkdownText(text: content),
            if (!user && content.isNotEmpty) ...[
              const SizedBox(height: 6),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton.icon(
                  onPressed: () async {
                    await Clipboard.setData(ClipboardData(text: content));
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Réponse copiée.')),
                      );
                    }
                  },
                  icon: const Icon(Icons.copy_outlined, size: 15),
                  label: const Text('Copier'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ArtifactCard extends StatelessWidget {
  const _ArtifactCard({
    required this.artifact,
    required this.onApprove,
    required this.onDownload,
  });

  final Map<String, dynamic> artifact;
  final VoidCallback onApprove, onDownload;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    final type = '${artifact['artifact_type'] ?? ''}';
    final payload = artifact['payload'] is Map
        ? Map<String, dynamic>.from(artifact['payload'] as Map)
        : <String, dynamic>{};
    final approved = artifact['status'] != 'DRAFT';
    return Card(
      margin: const EdgeInsets.only(bottom: 14),
      color: p.surface,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  type == 'EMAIL_DRAFT'
                      ? Icons.email_outlined
                      : Icons.description_outlined,
                  color: p.blue,
                ),
                const SizedBox(width: 9),
                Expanded(
                  child: Text(
                    '${artifact['title'] ?? _artifactLabel(type)}',
                    style: TextStyle(
                      color: p.title,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                Chip(
                  label: Text(approved ? 'Approuvé' : 'Brouillon'),
                  visualDensity: VisualDensity.compact,
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (payload['subject']?.toString().isNotEmpty == true)
              Text(
                'Objet : ${payload['subject']}',
                style: TextStyle(color: p.text, fontWeight: FontWeight.w600),
              ),
            Text(
              '${payload['body'] ?? payload['description'] ?? payload['reason'] ?? payload['summary'] ?? ''}',
              maxLines: 6,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(color: p.muted, height: 1.4),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                if (!approved)
                  OutlinedButton.icon(
                    onPressed: onApprove,
                    icon: const Icon(Icons.check),
                    label: const Text('Approuver'),
                  ),
                if (type == 'WG_REQUEST')
                  FilledButton.icon(
                    onPressed: onDownload,
                    icon: const Icon(Icons.picture_as_pdf_outlined),
                    label: const Text('Télécharger PDF'),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class ExpertMarkdownText extends StatelessWidget {
  const ExpertMarkdownText({super.key, required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    final lines = text.trim().split('\n');
    return SelectableText.rich(
      TextSpan(
        children: [
          for (var index = 0; index < lines.length; index++) ...[
            _markdownLine(lines[index], p),
            if (index < lines.length - 1) const TextSpan(text: '\n'),
          ],
        ],
        style: TextStyle(color: p.text, height: 1.5),
      ),
    );
  }
}

InlineSpan _markdownLine(String line, ExpertPalette p) {
  final heading = RegExp(r'^(#{1,3})\s+(.*)$').firstMatch(line);
  final bullet = RegExp(r'^\s*[-*]\s+(.*)$').firstMatch(line);
  final numbered = RegExp(r'^\s*(\d+)\.\s+(.*)$').firstMatch(line);
  final content =
      heading?.group(2) ?? bullet?.group(1) ?? numbered?.group(2) ?? line;
  final prefix = bullet != null
      ? '• '
      : numbered != null
      ? '${numbered.group(1)}. '
      : '';
  final baseStyle = TextStyle(
    fontSize: heading == null ? ExpertType.body : 16,
    fontWeight: heading == null ? FontWeight.normal : FontWeight.w700,
    color: heading == null ? p.text : p.title,
  );
  final spans = <InlineSpan>[];
  if (prefix.isNotEmpty) {
    spans.add(
      TextSpan(
        text: prefix,
        style: baseStyle.copyWith(color: p.blue),
      ),
    );
  }
  final bold = RegExp(r'\*\*(.+?)\*\*');
  var offset = 0;
  for (final match in bold.allMatches(content)) {
    if (match.start > offset) {
      spans.add(TextSpan(text: content.substring(offset, match.start)));
    }
    spans.add(
      TextSpan(
        text: match.group(1),
        style: const TextStyle(fontWeight: FontWeight.w700),
      ),
    );
    offset = match.end;
  }
  if (offset < content.length) {
    spans.add(TextSpan(text: content.substring(offset)));
  }
  return TextSpan(children: spans, style: baseStyle);
}

String _withNormContext(String message, Map<String, dynamic>? norm) {
  if (norm == null) return message;
  final reference = '${norm['reference_number'] ?? norm['code'] ?? ''}'.trim();
  final title = '${norm['title'] ?? ''}'.trim();
  if (reference.isEmpty && title.isEmpty) return message;
  final label = [reference, title].where((part) => part.isNotEmpty).join(' — ');
  return 'Contexte de la norme ouverte : $label\n\n$message';
}

String _assistantError(Object error) {
  if (error is DioException) {
    if (error.response?.statusCode == 503) {
      return 'L’assistant est momentanément indisponible. Réessayez dans quelques instants.';
    }
    if (error.response?.statusCode == 403) {
      return 'Votre compte n’a pas accès à l’assistant dans ce contexte.';
    }
    return 'La requête n’a pas pu être traitée. Réessayez.';
  }
  return 'L’assistant n’a pas pu répondre. Réessayez.';
}

String _artifactLabel(String type) => switch (type) {
  'EMAIL_DRAFT' => 'Brouillon d’e-mail',
  'WG_REQUEST' => 'Demande de groupe de travail',
  'NORM_OVERLAP' => 'Chevauchement de normes',
  'EXTERNAL_PROPOSAL' => 'Proposition de référentiel externe',
  'CHART' => 'Graphique',
  _ => 'Artefact',
};

String _sessionDate(dynamic raw) {
  final date = DateTime.tryParse('$raw')?.toLocal();
  if (date == null) return '';
  return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
}

List<Map<String, dynamic>> _expertRows(dynamic data) {
  final rows = data is List
      ? data
      : data is Map
      ? data['results']
      : null;
  return rows is List
      ? rows.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList()
      : [];
}

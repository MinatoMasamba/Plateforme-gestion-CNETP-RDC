import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../../core/api/api_client.dart';
import 'expert_assistant.dart';
import 'expert_theme.dart';

List<Map<String, dynamic>> expertRows(dynamic data) {
  final rows = data is List
      ? data
      : data is Map
      ? data['results']
      : null;
  return rows is List
      ? rows.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList()
      : [];
}

String expertError(Object error) {
  if (error is DioException) {
    final data = error.response?.data;
    if (data is Map && data.isNotEmpty) {
      final message = data['detail'] ?? data['error'] ?? data.values.first;
      return message is List ? message.join('\n') : '$message';
    }
    return 'Impossible de joindre le serveur. Réessayez.';
  }
  return 'L’opération a échoué. Réessayez.';
}

Future<void> openExpertMessaging(
  BuildContext context, {
  Map<String, dynamic>? contact,
}) => openExpertCommunication(context, contact: contact);

Future<void> openExpertCommunication(
  BuildContext context, {
  Map<String, dynamic>? contact,
  Map<String, dynamic>? norm,
}) async {
  final palette = ExpertTheme.of(context);
  final center = ExpertCommunicationCenter(initialContact: contact, norm: norm);
  await Navigator.of(context).push<void>(
    MaterialPageRoute(
      fullscreenDialog: false,
      builder: (_) => ExpertPageTheme(palette: palette, child: center),
    ),
  );
}

class ExpertCommunicationCenter extends StatelessWidget {
  const ExpertCommunicationCenter({super.key, this.initialContact, this.norm});

  final Map<String, dynamic>? initialContact;
  final Map<String, dynamic>? norm;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: p.bg,
        appBar: AppBar(
          leading: IconButton(
            onPressed: () => Navigator.of(context).pop(),
            tooltip: 'Retour',
            icon: const Icon(Icons.arrow_back),
          ),
          title: const Text('Centre de communication'),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(72),
            child: LayoutBuilder(
              builder: (context, constraints) {
                final desktop = constraints.maxWidth >= 700;
                if (!desktop) {
                  return TabBar(
                    indicatorColor: p.blue,
                    labelColor: p.title,
                    unselectedLabelColor: p.muted,
                    tabs: const [
                      Tab(icon: Icon(Icons.forum_outlined), text: 'Messages'),
                      Tab(
                        icon: Icon(Icons.auto_awesome_outlined),
                        text: 'Assistant IA',
                      ),
                    ],
                  );
                }
                final segments = TabBar(
                  indicator: BoxDecoration(
                    color: p.blue,
                    borderRadius: BorderRadius.circular(9),
                  ),
                  indicatorSize: TabBarIndicatorSize.tab,
                  labelPadding: EdgeInsets.zero,
                  dividerColor: Colors.transparent,
                  labelColor: Colors.white,
                  unselectedLabelColor: p.muted,
                  labelStyle: const TextStyle(
                    fontSize: ExpertType.body,
                    fontWeight: FontWeight.w700,
                  ),
                  unselectedLabelStyle: const TextStyle(
                    fontSize: ExpertType.body,
                    fontWeight: FontWeight.w500,
                  ),
                  tabs: const [
                    Tab(
                      height: 40,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.forum_outlined, size: 18),
                          SizedBox(width: 8),
                          Text('Messages'),
                        ],
                      ),
                    ),
                    Tab(
                      height: 40,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.auto_awesome_outlined, size: 18),
                          SizedBox(width: 8),
                          Text('Assistant IA'),
                        ],
                      ),
                    ),
                  ],
                );
                return Align(
                  alignment: Alignment.center,
                  child: Container(
                    key: const ValueKey('communication-tabs-desktop'),
                    width: ExpertCommunicationLayout.segmentedTabsWidth,
                    height: 72,
                    alignment: Alignment.center,
                    child: Container(
                      height: 48,
                      padding: const EdgeInsets.all(4),
                      decoration: BoxDecoration(
                        color: p.surface,
                        border: Border.all(color: p.border),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: segments,
                    ),
                  ),
                );
              },
            ),
          ),
        ),
        body: TabBarView(
          children: [
            ExpertMessaging(initialContact: initialContact),
            ExpertAssistant(norm: norm),
          ],
        ),
      ),
    );
  }
}

class ExpertMessaging extends StatefulWidget {
  const ExpertMessaging({super.key, this.initialContact});

  final Map<String, dynamic>? initialContact;

  @override
  State<ExpertMessaging> createState() => _ExpertMessagingState();
}

class _ExpertMessagingState extends State<ExpertMessaging> {
  final _message = TextEditingController();
  final _search = TextEditingController();
  final _scroll = ScrollController();
  List<Map<String, dynamic>> _conversations = [], _messages = [];
  Map<String, dynamic>? _contact;
  bool _loading = true, _loadingMessages = false, _sending = false;
  bool _refreshing = false, _mobileThread = false;
  String? _error;
  int _request = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _contact = widget.initialContact;
    _mobileThread = _contact != null;
    _message.addListener(_onComposerChanged);
    _loadConversations();
    _timer = Timer.periodic(const Duration(seconds: 8), (_) => _refresh());
  }

  void _onComposerChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _loadConversations() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await ApiClient.dio.get(
        '/api/v1/messages/conversations/',
      );
      if (!mounted) return;
      final rows = expertRows(response.data);
      setState(() {
        _conversations = rows;
        if (_contact != null) {
          _contact = rows.cast<Map<String, dynamic>?>().firstWhere(
            (row) => '${row?['user_id']}' == '${_contact?['user_id']}',
            orElse: () => _contact,
          );
        }
        _loading = false;
      });
      if (_contact != null) await _refreshMessages();
    } catch (error) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = expertError(error);
        });
      }
    }
  }

  Future<void> _refresh() async {
    if (_refreshing) return;
    _refreshing = true;
    try {
      final response = await ApiClient.dio.get(
        '/api/v1/messages/conversations/',
      );
      if (!mounted) return;
      setState(() => _conversations = expertRows(response.data));
      if (_contact != null) await _refreshMessages();
    } catch (error) {
      if (mounted) setState(() => _error = expertError(error));
    } finally {
      _refreshing = false;
    }
  }

  Future<void> _refreshMessages() async {
    final participant = _contact?['user_id'];
    if (participant == null) return;
    final request = ++_request;
    setState(() => _loadingMessages = _messages.isEmpty);
    try {
      final rows = <Map<String, dynamic>>[];
      String? next = '/api/v1/messages/';
      var first = true;
      while (next != null) {
        final response = await ApiClient.dio.get(
          next,
          queryParameters: first ? {'participant_id': participant} : null,
        );
        if (!mounted || request != _request) return;
        rows.addAll(expertRows(response.data));
        final rawNext = response.data is Map ? response.data['next'] : null;
        next = rawNext is String && rawNext.isNotEmpty ? rawNext : null;
        first = false;
      }
      final changed =
          rows.length != _messages.length ||
          (rows.isNotEmpty && rows.last['id'] != _messages.lastOrNull?['id']);
      setState(() {
        _messages = rows;
        _loadingMessages = false;
        _error = null;
      });
      await ApiClient.dio.post(
        '/api/v1/messages/mark_conversation_as_read/',
        data: {'participant_id': participant},
      );
      if (!mounted || request != _request) return;
      if (changed) _toBottom();
    } catch (error) {
      if (mounted && request == _request) {
        setState(() {
          _loadingMessages = false;
          _error = expertError(error);
        });
      }
    }
  }

  Future<void> _selectContact(Map<String, dynamic> contact) async {
    _request++;
    setState(() {
      _contact = contact;
      _messages = [];
      _message.clear();
      _mobileThread = true;
      _error = null;
    });
    await _refreshMessages();
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

  Future<void> _send() async {
    final text = _message.text.trim();
    final recipient = _contact?['user_id'];
    if (_sending || text.isEmpty || recipient == null) return;
    setState(() => _sending = true);
    try {
      final response = await ApiClient.dio.post(
        '/api/v1/messages/',
        data: {'receiver_id': recipient, 'content': text},
      );
      if (!mounted) return;
      setState(() {
        if (_message.text.trim() == text) _message.clear();
        _messages.add(Map<String, dynamic>.from(response.data as Map));
        _error = null;
      });
      _toBottom();
      await _refresh();
    } catch (error) {
      if (mounted) setState(() => _error = expertError(error));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _request++;
    _message
      ..removeListener(_onComposerChanged)
      ..dispose();
    _search.dispose();
    _scroll.dispose();
    super.dispose();
  }

  List<Map<String, dynamic>> get _filtered {
    final query = _search.text.trim().toLowerCase();
    if (query.isEmpty) return _conversations;
    return _conversations.where((contact) {
      return [
        contact['user_name'],
        contact['structure_name'],
        contact['ctm_name'],
        contact['specialties'],
      ].join(' ').toLowerCase().contains(query);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final mobile = MediaQuery.sizeOf(context).width < 700;
    if (mobile && !_mobileThread) {
      return _ConversationInbox(
        loading: _loading,
        error: _error,
        search: _search,
        conversations: _filtered,
        onRetry: _loadConversations,
        onSelect: _selectContact,
      );
    }
    if (mobile) {
      return _MessageThread(
        contact: _contact,
        messages: _messages,
        composer: _message,
        scroll: _scroll,
        loading: _loadingMessages,
        sending: _sending,
        error: _error,
        onBack: () => setState(() => _mobileThread = false),
        onRetry: _refreshMessages,
        onSend: _send,
      );
    }
    final p = ExpertTheme.of(context);
    return LayoutBuilder(
      builder: (context, constraints) {
        final frameWidth = ExpertCommunicationLayout.contentWidth(
          constraints.maxWidth,
        );
        return Center(
          child: SizedBox(
            key: const ValueKey('communication-content-frame'),
            width: frameWidth,
            height: constraints.maxHeight,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: p.card,
                border: Border.symmetric(vertical: BorderSide(color: p.border)),
              ),
              child: Row(
                children: [
                  SizedBox(
                    key: const ValueKey('communication-inbox'),
                    width: ExpertCommunicationLayout.inboxWidth(frameWidth),
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        color: p.card,
                        border: Border(right: BorderSide(color: p.border)),
                      ),
                      child: _ConversationInbox(
                        loading: _loading,
                        error: _error,
                        search: _search,
                        conversations: _filtered,
                        selectedId: '${_contact?['user_id'] ?? ''}',
                        onRetry: _loadConversations,
                        onSelect: _selectContact,
                      ),
                    ),
                  ),
                  Expanded(
                    child: SizedBox(
                      key: const ValueKey('communication-thread'),
                      width: double.infinity,
                      child: _MessageThread(
                        contact: _contact,
                        messages: _messages,
                        composer: _message,
                        scroll: _scroll,
                        loading: _loadingMessages,
                        sending: _sending,
                        error: _error,
                        onRetry: _refreshMessages,
                        onSend: _send,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _ConversationInbox extends StatelessWidget {
  const _ConversationInbox({
    required this.loading,
    required this.error,
    required this.search,
    required this.conversations,
    required this.onRetry,
    required this.onSelect,
    this.selectedId,
  });

  final bool loading;
  final String? error;
  final TextEditingController search;
  final List<Map<String, dynamic>> conversations;
  final String? selectedId;
  final VoidCallback onRetry;
  final ValueChanged<Map<String, dynamic>> onSelect;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 10),
          child: Text(
            'Boîte de réception',
            style: TextStyle(
              color: p.title,
              fontSize: 18,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: TextField(
            controller: search,
            decoration: InputDecoration(
              hintText: 'Rechercher un expert ou une structure',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: search.text.isEmpty
                  ? null
                  : IconButton(
                      tooltip: 'Effacer',
                      onPressed: () => search.clear(),
                      icon: const Icon(Icons.close),
                    ),
            ),
          ),
        ),
        if (error != null)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: _InlineError(message: error!, onRetry: onRetry),
          ),
        Expanded(
          child: loading
              ? const _ConversationSkeleton()
              : conversations.isEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(28),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.chat_bubble_outline,
                          size: 54,
                          color: p.subtle,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          search.text.isEmpty
                              ? 'Aucune conversation'
                              : 'Aucun résultat',
                          style: TextStyle(
                            color: p.title,
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          search.text.isEmpty
                              ? 'Vos échanges avec les experts de vos CTM apparaîtront ici.'
                              : 'Essayez un autre nom ou une autre structure.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: p.muted),
                        ),
                      ],
                    ),
                  ),
                )
              : ListView.separated(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  itemCount: conversations.length,
                  separatorBuilder: (_, _) =>
                      Divider(height: 1, color: p.border, indent: 76),
                  itemBuilder: (context, index) {
                    final contact = conversations[index];
                    final selected = '${contact['user_id']}' == selectedId;
                    return _ConversationTile(
                      contact: contact,
                      selected: selected,
                      onTap: () => onSelect(contact),
                    );
                  },
                ),
        ),
        Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.lock_outline, size: 14, color: p.subtle),
              const SizedBox(width: 6),
              Flexible(
                child: Text(
                  'Échanges internes CNE-ITP',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(color: p.subtle, fontSize: ExpertType.meta),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ConversationTile extends StatelessWidget {
  const _ConversationTile({
    required this.contact,
    required this.selected,
    required this.onTap,
  });

  final Map<String, dynamic> contact;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    final name = '${contact['user_name'] ?? 'Expert'}';
    final last = contact['last_message'];
    final lastMap = last is Map ? Map<String, dynamic>.from(last) : null;
    final unread = (contact['unread_count'] as num? ?? 0).toInt();
    return Material(
      color: selected ? p.blueSoft : Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 13, 16, 13),
          child: Row(
            children: [
              _InitialAvatar(name: name),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            name,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              color: p.title,
                              fontWeight: unread > 0
                                  ? FontWeight.w800
                                  : FontWeight.w600,
                            ),
                          ),
                        ),
                        if (lastMap != null)
                          Text(
                            _shortDate(lastMap['timestamp']),
                            style: TextStyle(
                              color: unread > 0 ? p.blue : p.subtle,
                              fontSize: ExpertType.label,
                            ),
                          ),
                      ],
                    ),
                    Text(
                      [contact['structure_name'], contact['ctm_name']]
                          .where((value) => '$value'.trim().isNotEmpty)
                          .join(' • '),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: p.subtle,
                        fontSize: ExpertType.meta,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            lastMap == null
                                ? 'Commencer une conversation'
                                : lastMap['is_clause_share'] == true
                                ? 'Clause ${lastMap['clause_code'] ?? ''}'
                                : '${lastMap['content'] ?? ''}',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              color: unread > 0 ? p.text : p.muted,
                              fontWeight: unread > 0
                                  ? FontWeight.w600
                                  : FontWeight.normal,
                            ),
                          ),
                        ),
                        if (unread > 0)
                          Container(
                            margin: const EdgeInsets.only(left: 8),
                            padding: const EdgeInsets.symmetric(
                              horizontal: 7,
                              vertical: 3,
                            ),
                            decoration: BoxDecoration(
                              color: const Color(0xFFDB3832),
                              borderRadius: BorderRadius.circular(999),
                            ),
                            child: Text(
                              unread > 99 ? '99+' : '$unread',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: ExpertType.label,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MessageThread extends StatelessWidget {
  const _MessageThread({
    required this.contact,
    required this.messages,
    required this.composer,
    required this.scroll,
    required this.loading,
    required this.sending,
    required this.error,
    required this.onRetry,
    required this.onSend,
    this.onBack,
  });

  final Map<String, dynamic>? contact;
  final List<Map<String, dynamic>> messages;
  final TextEditingController composer;
  final ScrollController scroll;
  final bool loading, sending;
  final String? error;
  final VoidCallback onRetry, onSend;
  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    final desktop = MediaQuery.sizeOf(context).width >= 700;
    if (contact == null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.mark_chat_unread_outlined, size: 64, color: p.subtle),
            const SizedBox(height: 16),
            Text(
              'Sélectionnez une conversation',
              style: TextStyle(
                color: p.title,
                fontSize: 17,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Vos échanges internes CNE-ITP restent confidentiels.',
              style: TextStyle(color: p.muted),
            ),
          ],
        ),
      );
    }
    final name = '${contact!['user_name'] ?? 'Expert'}';
    return Column(
      children: [
        Container(
          constraints: BoxConstraints(
            minHeight: desktop
                ? ExpertCommunicationLayout.desktopHeaderHeight
                : 0,
          ),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: p.card,
            border: Border(bottom: BorderSide(color: p.border)),
          ),
          child: Row(
            children: [
              if (onBack != null)
                IconButton(
                  tooltip: 'Boîte de réception',
                  onPressed: onBack,
                  icon: const Icon(Icons.arrow_back),
                ),
              _InitialAvatar(name: name, radius: 19),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name,
                      style: TextStyle(
                        color: p.title,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Text(
                      [
                        contact!['structure_name'],
                        contact!['ctm_name'],
                        contact!['specialties'],
                      ].where((v) => '$v'.trim().isNotEmpty).join(' • '),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: p.muted,
                        fontSize: ExpertType.meta,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        if (error != null)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 0),
            child: _InlineError(message: error!, onRetry: onRetry),
          ),
        Expanded(
          child: loading
              ? const Center(child: CircularProgressIndicator())
              : messages.isEmpty
              ? Center(
                  child: Text(
                    'Démarrez la conversation avec $name.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: p.muted),
                  ),
                )
              : ListView.builder(
                  controller: scroll,
                  padding: EdgeInsets.fromLTRB(
                    desktop ? 24 : 18,
                    14,
                    desktop ? 24 : 18,
                    12,
                  ),
                  itemCount: messages.length,
                  itemBuilder: (context, index) {
                    final message = messages[index];
                    final previous = index > 0 ? messages[index - 1] : null;
                    final next = index + 1 < messages.length
                        ? messages[index + 1]
                        : null;
                    final date = DateTime.tryParse(
                      '${message['timestamp']}',
                    )?.toLocal();
                    final previousDate = DateTime.tryParse(
                      '${previous?['timestamp']}',
                    )?.toLocal();
                    final showDay =
                        date != null &&
                        (previousDate == null || !_sameDay(date, previousDate));
                    final received =
                        '${message['sender']}' == '${contact!['user_id']}';
                    final groupedWithPrevious =
                        previous != null &&
                        previous['sender'] == message['sender'] &&
                        previousDate != null &&
                        date != null &&
                        date.difference(previousDate).inMinutes.abs() < 5;
                    final nextDate = DateTime.tryParse(
                      '${next?['timestamp']}',
                    )?.toLocal();
                    final groupedWithNext =
                        next != null &&
                        next['sender'] == message['sender'] &&
                        nextDate != null &&
                        date != null &&
                        nextDate.difference(date).inMinutes.abs() < 5;
                    return Column(
                      children: [
                        if (showDay) _DaySeparator(date),
                        _MessageBubble(
                          message: message,
                          received: received,
                          groupedTop: groupedWithPrevious,
                          groupedBottom: groupedWithNext,
                        ),
                      ],
                    );
                  },
                ),
        ),
        SafeArea(
          top: false,
          child: Container(
            padding: EdgeInsets.fromLTRB(
              desktop ? 20 : 14,
              10,
              desktop ? 20 : 14,
              12,
            ),
            decoration: BoxDecoration(
              color: p.card,
              border: Border(top: BorderSide(color: p.border)),
            ),
            child: Center(
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  maxWidth: desktop
                      ? ExpertCommunicationLayout.readingWidth
                      : double.infinity,
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Expanded(
                      child: TextField(
                        key: const ValueKey('expert-message-composer'),
                        controller: composer,
                        minLines: 1,
                        maxLines: 5,
                        enabled: !sending,
                        textInputAction: TextInputAction.send,
                        onSubmitted: (_) => onSend(),
                        decoration: const InputDecoration(
                          hintText: 'Votre message…',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.all(Radius.circular(24)),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Tooltip(
                      message: 'Envoyer',
                      child: FilledButton(
                        key: const ValueKey('expert-message-send'),
                        onPressed: composer.text.trim().isEmpty || sending
                            ? null
                            : onSend,
                        style: FilledButton.styleFrom(
                          minimumSize: const Size(46, 46),
                          padding: EdgeInsets.zero,
                          shape: const CircleBorder(),
                        ),
                        child: sending
                            ? const SizedBox.square(
                                dimension: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                            : const Icon(Icons.send, size: 20),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({
    required this.message,
    required this.received,
    required this.groupedTop,
    required this.groupedBottom,
  });

  final Map<String, dynamic> message;
  final bool received, groupedTop, groupedBottom;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    final desktop = MediaQuery.sizeOf(context).width >= 700;
    final timestamp = DateTime.tryParse('${message['timestamp']}')?.toLocal();
    final isClause = message['is_clause_share'] == true;
    return Align(
      alignment: received ? Alignment.centerLeft : Alignment.centerRight,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: desktop
              ? ExpertCommunicationLayout.bubbleWidth
              : MediaQuery.sizeOf(context).width * 0.72,
        ),
        margin: EdgeInsets.only(
          top: groupedTop ? 2 : 7,
          bottom: groupedBottom ? 1 : 7,
        ),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
        decoration: BoxDecoration(
          color: received ? p.field : p.blue,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(received && groupedTop ? 6 : 16),
            topRight: Radius.circular(!received && groupedTop ? 6 : 16),
            bottomLeft: Radius.circular(received && groupedBottom ? 6 : 16),
            bottomRight: Radius.circular(!received && groupedBottom ? 6 : 16),
          ),
          border: received ? Border.all(color: p.border) : null,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            if (isClause)
              _ClauseCard(
                code: '${message['clause_code'] ?? ''}',
                excerpt: '${message['clause_excerpt'] ?? message['content']}',
                received: received,
              )
            else
              SelectableText(
                '${message['content'] ?? ''}',
                style: TextStyle(
                  color: received ? p.text : Colors.white,
                  height: 1.35,
                ),
              ),
            const SizedBox(height: 4),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  timestamp == null
                      ? ''
                      : '${timestamp.hour.toString().padLeft(2, '0')}:${timestamp.minute.toString().padLeft(2, '0')}',
                  style: TextStyle(
                    color: received
                        ? p.subtle
                        : Colors.white.withValues(alpha: 0.78),
                    fontSize: ExpertType.label,
                  ),
                ),
                if (!received) ...[
                  const SizedBox(width: 5),
                  Icon(
                    message['is_read'] == true || message['status'] == 'read'
                        ? Icons.done_all
                        : Icons.check,
                    size: 13,
                    color:
                        message['is_read'] == true ||
                            message['status'] == 'read'
                        ? Colors.white
                        : Colors.white.withValues(alpha: 0.7),
                  ),
                  const SizedBox(width: 3),
                  Text(
                    message['is_read'] == true || message['status'] == 'read'
                        ? 'Lu'
                        : 'Envoyé',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.78),
                      fontSize: ExpertType.label,
                    ),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _ClauseCard extends StatelessWidget {
  const _ClauseCard({
    required this.code,
    required this.excerpt,
    required this.received,
  });

  final String code, excerpt;
  final bool received;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    final foreground = received ? p.text : Colors.white;
    return Material(
      color: received ? p.blueSoft : Colors.white.withValues(alpha: 0.14),
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => showDialog<void>(
          context: context,
          builder: (_) => AlertDialog(
            title: Text('Clause $code'),
            content: SelectableText(excerpt),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Fermer'),
              ),
            ],
          ),
        ),
        child: Container(
          width: double.infinity,
          constraints: const BoxConstraints(maxWidth: 420),
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.description_outlined, color: foreground, size: 18),
                  const SizedBox(width: 7),
                  Expanded(
                    child: Text(
                      'Clause $code',
                      style: TextStyle(
                        color: foreground,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  Icon(Icons.open_in_new, color: foreground, size: 15),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                '« $excerpt »',
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: foreground.withValues(alpha: 0.9),
                  height: 1.35,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _InitialAvatar extends StatelessWidget {
  const _InitialAvatar({required this.name, this.radius = 23});

  final String name;
  final double radius;

  @override
  Widget build(BuildContext context) {
    final words = name.trim().split(RegExp(r'\s+'));
    final initials = words
        .where((word) => word.isNotEmpty)
        .take(2)
        .map((word) => word[0].toUpperCase())
        .join();
    final p = ExpertTheme.of(context);
    return CircleAvatar(
      radius: radius,
      backgroundColor: p.blueSoft,
      child: Text(
        initials.isEmpty ? 'E' : initials,
        style: TextStyle(
          color: p.blue,
          fontSize: radius - 8,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _DaySeparator extends StatelessWidget {
  const _DaySeparator(this.date);
  final DateTime date;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 13),
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: p.surface,
          border: Border.all(color: p.border),
          borderRadius: BorderRadius.circular(999),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          child: Text(
            _dayLabel(date),
            style: TextStyle(color: p.muted, fontSize: ExpertType.label),
          ),
        ),
      ),
    );
  }
}

class _ConversationSkeleton extends StatelessWidget {
  const _ConversationSkeleton();

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return ListView.builder(
      itemCount: 5,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      itemBuilder: (_, index) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 9),
        child: Row(
          children: [
            Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(color: p.field, shape: BoxShape.circle),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(height: 11, width: 150, color: p.field),
                  const SizedBox(height: 8),
                  Container(height: 9, color: p.field),
                  const SizedBox(height: 7),
                  Container(height: 9, width: 210, color: p.field),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _InlineError extends StatelessWidget {
  const _InlineError({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: p.red.withValues(alpha: 0.09),
        border: Border.all(color: p.red.withValues(alpha: 0.25)),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Icon(Icons.error_outline, size: 18, color: p.red),
          const SizedBox(width: 8),
          Expanded(
            child: Text(message, style: TextStyle(color: p.red)),
          ),
          TextButton(onPressed: onRetry, child: const Text('Réessayer')),
        ],
      ),
    );
  }
}

bool _sameDay(DateTime a, DateTime b) =>
    a.year == b.year && a.month == b.month && a.day == b.day;

String _dayLabel(DateTime date) {
  final now = DateTime.now();
  if (_sameDay(date, now)) return 'Aujourd’hui';
  if (_sameDay(date, now.subtract(const Duration(days: 1)))) return 'Hier';
  const months = [
    'janv.',
    'févr.',
    'mars',
    'avr.',
    'mai',
    'juin',
    'juil.',
    'août',
    'sept.',
    'oct.',
    'nov.',
    'déc.',
  ];
  return '${date.day} ${months[date.month - 1]}${date.year != now.year ? ' ${date.year}' : ''}';
}

String _shortDate(dynamic raw) {
  final date = DateTime.tryParse('$raw')?.toLocal();
  if (date == null) return '';
  final now = DateTime.now();
  if (_sameDay(date, now)) {
    return '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
  }
  if (_sameDay(date, now.subtract(const Duration(days: 1)))) return 'Hier';
  return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}';
}

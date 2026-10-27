import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../../core/api/api_client.dart';
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
}) {
  final palette = ExpertTheme.of(context);
  return showDialog<void>(
    context: context,
    builder: (context) => ExpertTheme(
      palette: palette,
      child: Dialog(
        insetPadding: const EdgeInsets.all(12),
        backgroundColor: palette.card,
        child: SizedBox(
          width: 780,
          height: 650,
          child: ExpertMessaging(initialContact: contact),
        ),
      ),
    ),
  );
}

class ExpertMessaging extends StatefulWidget {
  const ExpertMessaging({super.key, this.initialContact});
  final Map<String, dynamic>? initialContact;

  @override
  State<ExpertMessaging> createState() => _ExpertMessagingState();
}

class _ExpertMessagingState extends State<ExpertMessaging> {
  final _message = TextEditingController();
  final _scroll = ScrollController();
  List<Map<String, dynamic>> _contacts = [], _messages = [];
  Map<String, dynamic>? _contact;
  bool _loading = true, _sending = false, _refreshing = false;
  String? _error;
  int _request = 0, _unread = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _contact = widget.initialContact;
    _loadContacts();
    _timer = Timer.periodic(const Duration(seconds: 8), (_) => _refresh());
  }

  Future<void> _loadContacts() async {
    try {
      final response = await ApiClient.dio.get('/api/v1/messages/contacts/');
      if (!mounted) return;
      setState(() {
        _contacts = expertRows(response.data);
        _loading = false;
        _error = null;
      });
      await _refresh();
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
    final request = ++_request;
    final participant = _contact?['user_id'];
    try {
      final count = await ApiClient.dio.get('/api/v1/messages/unread_count/');
      if (!mounted || request != _request) return;
      setState(
        () => _unread = (count.data['unread_count'] as num? ?? 0).toInt(),
      );
      if (participant == null) return;
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
        _error = null;
      });
      final read = await ApiClient.dio.post(
        '/api/v1/messages/mark_conversation_as_read/',
        data: {'participant_id': participant},
      );
      if (!mounted || request != _request) return;
      setState(
        () => _unread =
            (_unread - (read.data['marked_read'] as num? ?? 0).toInt()).clamp(
              0,
              1 << 30,
            ),
      );
      if (changed) _toBottom();
    } catch (error) {
      if (mounted && request == _request) {
        setState(() => _error = expertError(error));
      }
    } finally {
      _refreshing = false;
    }
  }

  void _toBottom() => WidgetsBinding.instance.addPostFrameCallback((_) {
    if (mounted && _scroll.hasClients) {
      _scroll.jumpTo(_scroll.position.maxScrollExtent);
    }
  });

  Future<void> _send() async {
    final text = _message.text.trim(), recipient = _contact?['user_id'];
    if (_sending || text.isEmpty || recipient == null) return;
    setState(() => _sending = true);
    try {
      final response = await ApiClient.dio.post(
        '/api/v1/messages/',
        data: {'receiver_id': recipient, 'content': text},
      );
      if (!mounted) return;
      if (_message.text.trim() == text) _message.clear();
      if (_contact?['user_id'] == recipient) {
        setState(() {
          _messages.add(Map<String, dynamic>.from(response.data as Map));
          _error = null;
        });
        _toBottom();
      }
      _request++;
      while (_refreshing && mounted) {
        await Future<void>.delayed(const Duration(milliseconds: 30));
      }
      if (mounted) await _refresh();
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
    _message.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'MESSAGERIE CNE-ITP • $_unread non lu(s)',
                  style: TextStyle(color: p.title, fontWeight: FontWeight.bold),
                ),
              ),
              IconButton(
                onPressed: _refresh,
                tooltip: 'Actualiser',
                icon: Icon(Icons.refresh, color: p.blue),
              ),
              IconButton(
                onPressed: () => Navigator.pop(context),
                tooltip: 'Fermer',
                icon: Icon(Icons.close, color: p.text),
              ),
            ],
          ),
          if (_loading) const LinearProgressIndicator(),
          if (_error != null)
            Row(
              children: [
                Expanded(
                  child: Text(_error!, style: TextStyle(color: p.red)),
                ),
                TextButton(
                  onPressed: _loadContacts,
                  child: const Text('Réessayer'),
                ),
              ],
            ),
          DropdownButton<String>(
            isExpanded: true,
            dropdownColor: p.card,
            value: _contacts.any((c) => c['user_id'] == _contact?['user_id'])
                ? '${_contact!['user_id']}'
                : null,
            hint: const Text('Choisir un expert'),
            items: [
              for (final c in _contacts)
                DropdownMenuItem(
                  value: '${c['user_id']}',
                  child: Text(
                    '${c['user_name'] ?? 'Expert'}',
                    style: TextStyle(color: p.text),
                  ),
                ),
            ],
            onChanged: _sending
                ? null
                : (value) async {
                    setState(() {
                      _contact = _contacts.firstWhere(
                        (c) => '${c['user_id']}' == value,
                      );
                      _messages = [];
                      _message.clear();
                      _request++;
                    });
                    // Invalider l’ancienne conversation puis attendre la fin de son chargement.
                    while (_refreshing && mounted) {
                      await Future<void>.delayed(
                        const Duration(milliseconds: 30),
                      );
                    }
                    if (mounted) await _refresh();
                  },
          ),
          if (!_loading && _contacts.isEmpty)
            Text(
              'Aucun contact disponible dans vos CTM.',
              style: TextStyle(color: p.muted),
            ),
          Expanded(
            child: _contact == null
                ? Center(
                    child: Text(
                      'Sélectionnez une conversation.',
                      style: TextStyle(color: p.muted),
                    ),
                  )
                : ListView.builder(
                    controller: _scroll,
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      final m = _messages[index];
                      final received =
                          '${m['sender']}' == '${_contact!['user_id']}';
                      return Align(
                        alignment: received
                            ? Alignment.centerLeft
                            : Alignment.centerRight,
                        child: Container(
                          constraints: const BoxConstraints(maxWidth: 550),
                          margin: const EdgeInsets.symmetric(vertical: 6),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: received ? p.field : p.blueSoft,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${m['sender_name'] ?? 'Expert'}',
                                style: TextStyle(
                                  color: p.blue,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 11,
                                ),
                              ),
                              SelectableText(
                                '${m['content'] ?? ''}',
                                style: TextStyle(color: p.text),
                              ),
                              Text(
                                '${DateTime.tryParse('${m['timestamp']}')?.toLocal() ?? ''}',
                                style: TextStyle(color: p.subtle, fontSize: 10),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: TextField(
                  controller: _message,
                  enabled: _contact != null && !_sending,
                  minLines: 1,
                  maxLines: 4,
                  style: TextStyle(color: p.text),
                  decoration: const InputDecoration(
                    hintText: 'Votre message…',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
              IconButton(
                onPressed: _contact == null || _sending ? null : _send,
                tooltip: 'Envoyer',
                icon: Icon(
                  _sending ? Icons.hourglass_top : Icons.send,
                  color: p.blue,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

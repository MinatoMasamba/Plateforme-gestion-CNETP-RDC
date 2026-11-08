import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../../core/api/api_client.dart';
import '../../../theme/app_colors.dart';
import 'ged_shared.dart';

class CtcNotifications extends ChangeNotifier {
  CtcNotifications({Dio? client}) : _client = client ?? ApiClient.dio;
  final Dio _client;
  List<Map<String, dynamic>> rows = [];
  int? unread;
  bool loading = false;
  String? opening;
  String? error;
  Map<String, dynamic>? selected;
  bool _disposed = false;
  int _revision = 0;

  void _apply(dynamic body) {
    final data = (body as Map).cast<String, dynamic>();
    rows = rowsOf(data['results']);
    unread =
        (data['unread_count'] as num?)?.toInt() ??
        rows.where((row) => row['is_read'] != true).length;
  }

  Future<void> load() async {
    if (_disposed || loading || opening != null) return;
    final revision = ++_revision;
    loading = true;
    error = null;
    notifyListeners();
    try {
      final response = await _client.get('/api/v1/st/notifications/');
      if (_disposed || revision != _revision) return;
      _apply(response.data);
    } catch (_) {
      if (_disposed || revision != _revision) return;
      error = 'Impossible de charger les notifications. Réessayez.';
    } finally {
      if (!_disposed && revision == _revision) {
        loading = false;
        notifyListeners();
      }
    }
  }

  Future<void> open(Map<String, dynamic> row) async {
    if (_disposed || opening != null) return;
    final key = '${row['key']}';
    ++_revision;
    loading = false;
    opening = key;
    error = null;
    notifyListeners();
    try {
      if (row['is_read'] != true) {
        final response = await _client.post(
          '/api/v1/st/notifications/read/',
          data: {'key': key},
        );
        if (_disposed) return;
        _apply(response.data);
      }
      if (_disposed) return;
      selected = rows.where((item) => item['key'] == key).firstOrNull ?? row;
    } catch (_) {
      if (_disposed) return;
      error =
          'La lecture n’a pas pu être enregistrée. La notification reste non lue.';
    } finally {
      if (!_disposed) {
        opening = null;
        notifyListeners();
      }
    }
  }

  void back() {
    selected = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    ++_revision;
    super.dispose();
  }
}

class CtcNotificationsView extends StatefulWidget {
  const CtcNotificationsView({
    super.key,
    required this.controller,
    required this.onOpenDossier,
  });
  final CtcNotifications controller;
  final ValueChanged<Map<String, dynamic>> onOpenDossier;

  @override
  State<CtcNotificationsView> createState() => _CtcNotificationsViewState();
}

class _CtcNotificationsViewState extends State<CtcNotificationsView> {
  bool _onlyUnread = false;

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: widget.controller,
    builder: (context, _) {
      final controller = widget.controller;
      final selected = controller.selected;
      final visible = controller.rows
          .where((row) => !_onlyUnread || row['is_read'] != true)
          .toList();
      return ListView(
        padding: const EdgeInsets.all(20),
        children: [
          GedCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const GedSectionTitle(
                  'Notifications',
                  Icons.notifications_outlined,
                ),
                const SizedBox(height: 8),
                Text(
                  controller.unread == null
                      ? 'Votre suivi et vos alertes documentaires.'
                      : '${controller.unread} notification(s) non lue(s)',
                  style: const TextStyle(color: AppColors.muted),
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    if (selected != null)
                      OutlinedButton.icon(
                        onPressed: controller.back,
                        icon: const Icon(Icons.arrow_back, size: 16),
                        label: const Text('Toutes les notifications'),
                      ),
                    OutlinedButton.icon(
                      onPressed: controller.loading ? null : controller.load,
                      icon: const Icon(Icons.refresh, size: 16),
                      label: const Text('Actualiser les notifications'),
                    ),
                    if (selected == null) ...[
                      ChoiceChip(
                        label: const Text('Toutes'),
                        selected: !_onlyUnread,
                        onSelected: (_) => setState(() => _onlyUnread = false),
                      ),
                      ChoiceChip(
                        label: const Text('Non lues'),
                        selected: _onlyUnread,
                        onSelected: (_) => setState(() => _onlyUnread = true),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          if (controller.error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Text(
                controller.error!,
                style: const TextStyle(color: AppColors.danger),
              ),
            ),
          if (controller.loading) const LinearProgressIndicator(),
          if (selected != null)
            GedCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  GedBadge(label: 'Lue', color: AppColors.success),
                  const SizedBox(height: 12),
                  Text(
                    '${selected['title'] ?? 'Notification'}',
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${selected['category'] ?? ''} · ${frDateTime(selected['date'])}',
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.muted,
                    ),
                  ),
                  const Divider(height: 32),
                  SelectableText(
                    '${selected['body'] ?? ''}',
                    style: const TextStyle(fontSize: 14, height: 1.6),
                  ),
                  if (selected['process_id'] is num) ...[
                    const SizedBox(height: 20),
                    FilledButton.icon(
                      onPressed: () => widget.onOpenDossier(selected),
                      icon: const Icon(Icons.folder_open_outlined, size: 18),
                      label: const Text('Ouvrir le dossier concerné'),
                    ),
                  ],
                ],
              ),
            )
          else if (!controller.loading &&
              visible.isEmpty &&
              controller.error == null)
            GedCard(
              child: GedEmpty(
                _onlyUnread
                    ? 'Aucune notification non lue.'
                    : 'Aucune notification pour le moment.',
              ),
            )
          else
            for (final row in visible)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: GedCard(
                  child: InkWell(
                    onTap: controller.opening == null
                        ? () => controller.open(row)
                        : null,
                    borderRadius: BorderRadius.circular(12),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(
                            row['is_read'] == true
                                ? Icons.drafts_outlined
                                : Icons.mark_email_unread_outlined,
                            color: row['is_read'] == true
                                ? AppColors.subtle
                                : AppColors.rdcBlue,
                            size: 22,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '${row['title'] ?? 'Notification'}',
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: row['is_read'] == true
                                        ? FontWeight.w500
                                        : FontWeight.w700,
                                  ),
                                ),
                                const SizedBox(height: 5),
                                Text(
                                  '${row['body'] ?? ''}',
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: AppColors.muted,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  '${row['category'] ?? ''} · ${frDateTime(row['date'])}',
                                  style: const TextStyle(
                                    fontSize: 11,
                                    color: AppColors.muted,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 8),
                          if (controller.opening == row['key'])
                            const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          else
                            GedBadge(
                              label: row['is_read'] == true ? '0' : '1',
                              color: row['is_read'] == true
                                  ? AppColors.subtle
                                  : AppColors.rdcBlue,
                            ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
        ],
      );
    },
  );
}

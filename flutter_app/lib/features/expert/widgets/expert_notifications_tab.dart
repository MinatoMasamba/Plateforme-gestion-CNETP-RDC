import 'package:flutter/material.dart';

import 'expert_module.dart';

String _notificationDate(dynamic value) {
  final raw = '${value ?? ''}'.trim();
  if (raw.isEmpty) return '';
  final date = DateTime.tryParse(raw)?.toLocal();
  if (date == null) return raw;
  String two(int number) => number.toString().padLeft(2, '0');
  return '${two(date.day)}/${two(date.month)}/${date.year} · '
      '${two(date.hour)}:${two(date.minute)}';
}

class ExpertNotificationsTab extends StatelessWidget {
  const ExpertNotificationsTab({
    super.key,
    this.onOpenNorm,
    this.onOpenMeeting,
    this.onChanged,
  });
  final ValueChanged<Map<String, dynamic>>? onOpenNorm;
  final ValueChanged<String>? onOpenMeeting;
  final VoidCallback? onChanged;
  @override
  Widget build(BuildContext context) => ExpertModule(
    title: 'Notifications',
    endpoints: const {
      'Notifications': '/api/v1/mobile/notifications/?page_size=100',
      'Non lues': '/api/v1/mobile/notifications/unread_count/',
    },
    builder: (s) {
      final meetingsOnly = s.values['meetingsOnly'] == true;
      final notifications = s
          .rows('Notifications')
          .where(
            (n) => !meetingsOnly || expertMap(n['data'])['reunion_id'] != null,
          )
          .toList();
      final unread = s.map('Non lues')['unread_count'] ?? 0;
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$unread notification(s) non lue(s)',
            style: TextStyle(color: s.p.blue, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: [
              ChoiceChip(
                label: const Text('Toutes'),
                selected: !meetingsOnly,
                onSelected: (_) =>
                    s.change(() => s.values['meetingsOnly'] = false),
              ),
              ChoiceChip(
                label: const Text('Réunions'),
                selected: meetingsOnly,
                onSelected: (_) =>
                    s.change(() => s.values['meetingsOnly'] = true),
              ),
            ],
          ),
          const SizedBox(height: 8),
          s.button('Tout marquer comme lu', () async {
            await s.post('/api/v1/mobile/notifications/mark_all_as_read/');
            onChanged?.call();
          }, icon: Icons.done_all),
          const SizedBox(height: 12),
          if (notifications.isEmpty && s.errors.isEmpty)
            s.card('Notifications', [
              Text(
                meetingsOnly
                    ? 'Aucune notification de réunion pour le moment.'
                    : 'Aucune notification pour le moment.',
              ),
            ]),
          for (final n in notifications)
            s.card('${n['is_read'] == true ? '' : '● '}${n['title']}', [
              Text('${n['body'] ?? ''}'),
              Text(
                _notificationDate(n['created_at']),
                style: TextStyle(color: s.p.muted, fontSize: 12),
              ),
              s.actions([
                if (onOpenMeeting != null &&
                    expertMap(n['data'])['reunion_id'] != null)
                  s.button('Ouvrir la réunion', () async {
                    if (n['is_read'] != true) {
                      final saved = await s.post(
                        '/api/v1/mobile/notifications/${n['id']}/mark_as_read/',
                      );
                      if (!saved || !s.mounted) return;
                      onChanged?.call();
                    }
                    onOpenMeeting!('${n['data']['reunion_id']}');
                  }),
                if (n['is_read'] != true)
                  s.button('Marquer comme lu', () async {
                    await s.post(
                      '/api/v1/mobile/notifications/${n['id']}/mark_as_read/',
                    );
                    onChanged?.call();
                  }),
                if (onOpenNorm != null &&
                    expertMap(n['data'])['norme_id'] != null)
                  s.button(
                    'Ouvrir la norme',
                    () => onOpenNorm!({'id': n['data']['norme_id']}),
                  ),
              ]),
            ]),
        ],
      );
    },
  );
}

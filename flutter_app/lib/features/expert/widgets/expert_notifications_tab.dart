import 'package:flutter/material.dart';

import 'expert_module.dart';

class ExpertNotificationsTab extends StatelessWidget {
  const ExpertNotificationsTab({super.key, this.onOpenNorm});
  final ValueChanged<Map<String, dynamic>>? onOpenNorm;
  @override
  Widget build(BuildContext context) => ExpertModule(
    title: 'Notifications',
    endpoints: const {'Notifications': '/api/v1/mobile/notifications/'},
    builder: (s) {
      final notifications = s.rows('Notifications');
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          s.button(
            'Tout marquer comme lu',
            () => s.post('/api/v1/mobile/notifications/mark_all_as_read/'),
            icon: Icons.done_all,
          ),
          const SizedBox(height: 12),
          if (notifications.isEmpty && s.errors.isEmpty)
            s.card('Notifications', [
              const Text('Aucune notification pour le moment.'),
            ]),
          for (final n in notifications)
            s.card('${n['is_read'] == true ? '' : '● '}${n['title']}', [
              Text('${n['body'] ?? ''}'),
              Text('${n['created_at'] ?? ''}'),
              s.actions([
                if (n['is_read'] != true)
                  s.button(
                    'Marquer comme lu',
                    () => s.post(
                      '/api/v1/mobile/notifications/${n['id']}/mark_as_read/',
                    ),
                  ),
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

import 'package:flutter/material.dart';

import '../../../core/api/api_client.dart';
import 'expert_module.dart';
import 'expert_messaging.dart' show openExpertMessaging;

String expertName(Map<String, dynamic> expert) {
  final user = expertMap(expert['user']);
  final full = '${user['first_name'] ?? ''} ${user['last_name'] ?? ''}'.trim();
  return '${expert['user_name'] ?? expert['full_name'] ?? (full.isEmpty ? 'Expert' : full)}';
}

class ExpertAdhesionsTab extends StatelessWidget {
  const ExpertAdhesionsTab({super.key, this.onChanged});
  final VoidCallback? onChanged;
  @override
  Widget build(BuildContext context) => ExpertModule(
    title: 'Adhésions des membres',
    endpoints: const {
      'Droits': '/api/v1/experts/pending-count-for-my-ctm/',
      'Demandes': '/api/v1/experts/pending-for-my-ctm/',
      'Groupes': '/api/v1/wg/',
    },
    builder: (s) {
      if (s.errors.containsKey('Droits')) return const SizedBox.shrink();
      if (s.map('Droits')['is_ctm_leader'] != true) {
        return s.card('Gestion des adhésions', [
          const Text(
            'Cette action est réservée au bureau d’une sous-commission ou au secrétariat technique.',
          ),
        ]);
      }
      final pending = s.rows('Demandes');
      return Column(
        children: [
          if (pending.isEmpty && !s.errors.containsKey('Demandes'))
            s.card('Demandes en attente', [
              const Text('Aucune demande d’adhésion en attente.'),
            ]),
          for (final expert in pending)
            s.card(expertName(expert), [
              Text('${expertMap(expert['user'])['email'] ?? ''}'),
              Text('${expertMap(expert['structure'])['name'] ?? ''}'),
              Text(
                '${expert['ctm_name'] ?? ''} — ${expert['specialties'] ?? ''}',
              ),
              s.actions([
                s.button(
                  'Accepter et affecter',
                  () => expertForm(
                    s,
                    'Accepter ${expertName(expert)}',
                    [
                      ExpertField(
                        'wg_id',
                        'Groupe de travail obligatoire',
                        choices: {
                          for (final wg
                              in s
                                  .rows('Groupes')
                                  .where(
                                    (g) => '${g['ctm']}' == '${expert['ctm']}',
                                  ))
                            '${wg['id']}': '${wg['name']}',
                        },
                      ),
                    ],
                    (values) async {
                      final ok = await s.post(
                        '/api/v1/experts/${expert['id']}/admit-to-ctm/',
                        {
                          'ctm_id': expert['ctm'],
                          'wg_id': int.parse(values['wg_id']!),
                        },
                      );
                      if (ok) onChanged?.call();
                      return ok;
                    },
                  ),
                  icon: Icons.person_add_alt,
                ),
                s.button(
                  'Refuser',
                  () => expertForm(
                    s,
                    'Motif du refus',
                    const [ExpertField('reason', 'Motif', lines: 3)],
                    (values) async {
                      final ok = await s.post(
                        '/api/v1/experts/${expert['id']}/reject/',
                        values,
                      );
                      if (ok) onChanged?.call();
                      return ok;
                    },
                  ),
                  icon: Icons.person_remove_outlined,
                ),
              ]),
            ]),
        ],
      );
    },
  );
}

class ExpertExpertsTab extends StatelessWidget {
  const ExpertExpertsTab({super.key, this.onAdhesions});
  final VoidCallback? onAdhesions;
  @override
  Widget build(BuildContext context) => ExpertModule(
    title: 'Experts & Groupes',
    endpoints: const {
      'Experts': '/api/v1/experts/',
      'Groupes': '/api/v1/wg/',
      'Contacts': '/api/v1/messages/contacts/',
      'Profil': '/api/v1/experts/me/',
      'Adhésions': '/api/v1/experts/pending-count-for-my-ctm/',
    },
    builder: (s) {
      final query = '${s.values['search'] ?? ''}'.toLowerCase();
      final group = s.values['wg'];
      final groups = s.rows('Groupes');
      final selected = groups.where((g) => '${g['id']}' == group).firstOrNull;
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (onAdhesions != null)
            s.button(
              'Adhésions des membres (${s.map('Adhésions')['count'] ?? '…'})',
              onAdhesions!,
              icon: Icons.person_add_alt,
            ),
          const SizedBox(height: 12),
          TextField(
            style: TextStyle(color: s.p.text),
            decoration: const InputDecoration(
              labelText: 'Rechercher un expert',
              border: OutlineInputBorder(),
            ),
            onChanged: (value) => s.change(() => s.values['search'] = value),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: group,
            dropdownColor: s.p.card,
            isExpanded: true,
            decoration: const InputDecoration(
              labelText: 'Groupe de travail',
              border: OutlineInputBorder(),
            ),
            items: [
              const DropdownMenuItem(
                value: '',
                child: Text('Tous les experts'),
              ),
              for (final g in groups)
                DropdownMenuItem(
                  value: '${g['id']}',
                  child: Text(
                    '${g['name']}',
                    style: TextStyle(color: s.p.text),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
            ],
            onChanged: (value) => s.change(() => s.values['wg'] = value),
          ),
          const SizedBox(height: 16),
          if (selected != null)
            s.card('${selected['name']}', [
              Text('${selected['description'] ?? ''}'),
              Text('Membres : ${selected['expert_count'] ?? 0}'),
              for (final entry in expertMap(selected['leadership']).entries)
                if (entry.value is Map)
                  Text('${entry.key} : ${expertName(expertMap(entry.value))}'),
              for (final norm in expertRows(selected['latest_norms']))
                Text(
                  '${norm['reference_number'] ?? ''} — ${norm['title'] ?? ''}',
                ),
            ]),
          for (final expert in s.rows('Experts').where((e) {
            if (!expertName(e).toLowerCase().contains(query)) return false;
            return selected == null ||
                expertRows(
                  selected['expert_list'],
                ).any((a) => '${a['expert']}' == '${e['id']}');
          }))
            s.card(expertName(expert), [
              Text(
                '${expert['structure_name'] ?? ''} — ${expert['status'] ?? ''}',
              ),
              Text('${expert['specialties'] ?? ''}'),
              s.actions([
                s.button('Voir la fiche', () async {
                  await s.run(
                    () async {
                      final response = await ApiClient.dio.get(
                        '/api/v1/experts/${expert['id']}/',
                      );
                      final detail = expertMap(response.data);
                      if (s.mounted) {
                        await s.details(
                          expertName(detail),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${detail['structure_name'] ?? expertMap(detail['structure'])['name'] ?? ''}',
                              ),
                              Text('${detail['specialties'] ?? ''}'),
                              Text('${detail['ctm_name'] ?? ''}'),
                              for (final a in expertRows(
                                detail['affectations'],
                              ))
                                Text(
                                  '${a['ctm_name'] ?? ''} / ${a['wg_name'] ?? ''}',
                                ),
                            ],
                          ),
                        );
                      }
                    },
                    success: 'Fiche consultée.',
                    reload: false,
                  );
                }),
                if (s
                    .rows('Contacts')
                    .any((c) => '${c['id']}' == '${expert['id']}'))
                  s.button(
                    'Discuter',
                    () => openExpertMessaging(
                      s.context,
                      contact: s
                          .rows('Contacts')
                          .firstWhere((c) => '${c['id']}' == '${expert['id']}'),
                    ),
                    icon: Icons.chat_bubble_outline,
                  ),
              ]),
            ]),
          if (s.rows('Experts').isEmpty && !s.errors.containsKey('Experts'))
            s.card('Annuaire', [const Text('Aucun expert disponible.')]),
        ],
      );
    },
  );
}

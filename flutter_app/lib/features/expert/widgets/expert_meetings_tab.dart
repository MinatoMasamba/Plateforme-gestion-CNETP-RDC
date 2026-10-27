import 'package:flutter/material.dart';

import '../../../core/api/api_client.dart';
import 'expert_module.dart';
import 'expert_theme.dart';

class ExpertMeetingsTab extends StatelessWidget {
  const ExpertMeetingsTab({super.key});
  @override
  Widget build(BuildContext context) => ExpertModule(
    title: 'Réunions techniques & votes',
    endpoints: const {
      'Réunions': '/api/v1/reunions/?ordering=-date',
      'Profil': '/api/v1/experts/me/',
      'Affiliation': '/api/v1/experts/my-affiliation/',
    },
    builder: (s) {
      final staff = ['ADMIN', 'COORD_CTC'].contains(s.map('Profil')['role_id']);
      final bureau = (s.map('Affiliation')['bureau_ctm_ids'] as List? ?? [])
          .map((e) => '$e')
          .toSet();
      final ctms = expertRows(s.map('Affiliation')['ctms']);
      final groups = expertRows(s.map('Affiliation')['workgroups']);
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (staff || bureau.isNotEmpty)
            s.button(
              'Planifier une session',
              () => expertForm(
                s,
                'Planifier une réunion',
                [
                  const ExpertField('titre', 'Titre'),
                  const ExpertField(
                    'type',
                    'Type',
                    initial: 'CTM',
                    choices: {
                      'CTM': 'Sous-commission / CTM',
                      'WG': 'Groupe de travail',
                    },
                  ),
                  ExpertField(
                    'ctm',
                    'Sous-commission',
                    choices: {
                      for (final c in ctms.where(
                        (c) => staff || bureau.contains('${c['id']}'),
                      ))
                        '${c['id']}': '${c['name']}',
                    },
                  ),
                  ExpertField(
                    'wg',
                    'Groupe (pour une réunion WG)',
                    required: false,
                    choices: {
                      for (final g in groups.where(
                        (g) => staff || bureau.contains('${g['ctm_id']}'),
                      ))
                        '${g['id']}': '${g['name']}',
                    },
                  ),
                  const ExpertField('date', 'Date et heure (AAAA-MM-JJ HH:MM)'),
                  const ExpertField('ordre_jour', 'Ordre du jour', lines: 3),
                  const ExpertField('lieu', 'Lieu', required: false),
                  const ExpertField(
                    'lien_reunion_virtuelle',
                    'Lien visioconférence',
                    required: false,
                  ),
                  const ExpertField(
                    'document_reglementaire',
                    'Référence de la norme',
                    required: false,
                  ),
                ],
                (values) async {
                  final date = DateTime.tryParse(values['date']!);
                  if (date == null || !date.isAfter(DateTime.now())) {
                    s.notify(
                      'Choisissez une date et une heure futures valides.',
                    );
                    return false;
                  }
                  final wg = values['wg']!;
                  if (values['type'] == 'WG' && wg.isEmpty) {
                    s.notify('Sélectionnez un groupe de travail.');
                    return false;
                  }
                  if (wg.isNotEmpty &&
                      !groups.any(
                        (g) =>
                            '${g['id']}' == wg &&
                            '${g['ctm_id']}' == values['ctm'],
                      )) {
                    s.notify(
                      'Le groupe doit appartenir à la sous-commission sélectionnée.',
                    );
                    return false;
                  }
                  return s.post('/api/v1/reunions/', {
                    ...values,
                    'ctm': int.parse(values['ctm']!),
                    'wg': wg.isEmpty ? null : int.parse(wg),
                    'date': date.toUtc().toIso8601String(),
                  });
                },
              ),
              icon: Icons.event_available,
            ),
          if (s.rows('Réunions').isEmpty && !s.errors.containsKey('Réunions'))
            s.card('Réunions', [const Text('Aucune réunion disponible.')]),
          for (final meeting in s.rows('Réunions'))
            s.card('${meeting['titre']}', [
              Text('${meeting['date']} — ${meeting['status']}'),
              Text(
                '${meeting['ctm_name'] ?? ''} / ${meeting['wg_name'] ?? ''}',
              ),
              Text('${meeting['ordre_jour'] ?? ''}'),
              s.actions([
                s.button('Ouvrir : présences, votes et PV', () async {
                  final palette = ExpertTheme.of(s.context);
                  await Navigator.of(s.context).push(
                    MaterialPageRoute<void>(
                      builder: (_) => ExpertTheme(
                        palette: palette,
                        child: Scaffold(
                          backgroundColor: palette.bg,
                          appBar: AppBar(title: Text('${meeting['titre']}')),
                          body: _MeetingDetails(
                            id: '${meeting['id']}',
                            canManage:
                                staff || bureau.contains('${meeting['ctm']}'),
                          ),
                        ),
                      ),
                    ),
                  );
                  if (s.mounted) await s.load();
                }),
                if ('${meeting['lien_reunion_virtuelle'] ?? ''}'.isNotEmpty)
                  s.button(
                    'Rejoindre la réunion',
                    () => s.open('${meeting['lien_reunion_virtuelle']}'),
                    icon: Icons.video_call_outlined,
                  ),
              ]),
            ]),
        ],
      );
    },
  );
}

class _MeetingDetails extends StatelessWidget {
  const _MeetingDetails({required this.id, required this.canManage});
  final String id;
  final bool canManage;
  @override
  Widget build(BuildContext context) => ExpertModule(
    title: 'Présences, votes et procès-verbal',
    endpoints: {
      'Réunion': '/api/v1/reunions/$id/details/',
      'Profil': '/api/v1/experts/me/',
    },
    builder: (s) {
      final meeting = s.map('Réunion');
      if (meeting.isEmpty) return const SizedBox.shrink();
      final presences = expertRows(meeting['presences']),
          votes = expertRows(meeting['votes']);
      final expert = s.map('Profil')['id'];
      final present = presences.any(
        (p) => '${p['expert']}' == '$expert' && p['status'] == 'PRESENT',
      );
      final mine = votes
          .where((v) => '${v['expert']}' == '$expert')
          .firstOrNull;
      final active = ['PLANNED', 'IN_PROGRESS'].contains(meeting['status']);
      final pv = expertMap(meeting['pv']);
      return Column(
        children: [
          s.card('${meeting['titre']}', [
            Text('${meeting['date']} — ${meeting['status']}'),
            SelectableText('${meeting['ordre_jour'] ?? ''}'),
            Text('Votre vote : ${mine?['choix'] ?? 'Non voté'}'),
            s.actions([
              if (active && !present)
                s.button(
                  'Émarger ma présence',
                  () => s.post('/api/v1/reunions/$id/checkin_presence/'),
                  icon: Icons.how_to_reg,
                ),
              if (active && present)
                for (final choice in ['POUR', 'CONTRE', 'ABSTENTION'])
                  s.button(
                    'Voter $choice',
                    () =>
                        s.post('/api/v1/reunions/$id/vote/', {'choix': choice}),
                  ),
              if (active && canManage)
                s.button(
                  'Clore le scrutin et générer le PV',
                  () => s.post('/api/v1/reunions/$id/close/'),
                ),
            ]),
          ]),
          s.card(
            'Émargement (${presences.where((p) => p['status'] == 'PRESENT').length}/${presences.length})',
            [
              for (final presence in presences)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(
                    '${presence['expert_name']}',
                    style: TextStyle(color: s.p.text),
                  ),
                  subtitle: Text(
                    '${presence['status']}',
                    style: TextStyle(color: s.p.muted),
                  ),
                  trailing: canManage && active
                      ? PopupMenuButton<String>(
                          tooltip: 'Modifier la présence',
                          itemBuilder: (_) => [
                            for (final status in [
                              'PRESENT',
                              'ABSENT',
                              'EXCUSED',
                            ])
                              PopupMenuItem(value: status, child: Text(status)),
                          ],
                          onSelected: (status) => s.run(() async {
                            await ApiClient.dio.patch(
                              '/api/v1/presences/${presence['id']}/',
                              data: {'status': status},
                            );
                          }),
                        )
                      : null,
                ),
            ],
          ),
          s.card('Votes (${votes.length})', [
            for (final vote in votes)
              Text('${vote['expert_name']} : ${vote['choix']}'),
          ]),
          s.card('Procès-verbal', [
            SelectableText(
              '${pv['contenu'] ?? 'Le PV sera disponible après la clôture du scrutin.'}',
            ),
          ]),
        ],
      );
    },
  );
}

import 'package:flutter/material.dart';

import '../../../core/api/api_client.dart';
import 'expert_module.dart';
import 'expert_theme.dart';

class ExpertMeetingsTab extends StatelessWidget {
  const ExpertMeetingsTab({super.key, this.meetingId});
  final String? meetingId;
  @override
  Widget build(BuildContext context) => ExpertModule(
    title: 'Réunions',
    endpoints: const {
      'Réunions': '/api/v1/mobile/expert/meetings/?ordering=date',
      'Droits': '/api/v1/mobile/expert/meetings/capabilities/',
    },
    builder: (s) {
      final rights = s.map('Droits');
      final canPlan = rights['can_plan'] == true;
      final allowedCtms = (rights['can_plan_ctm_ids'] as List? ?? [])
          .map((id) => '$id')
          .toSet();
      final ctms = expertRows(rights['ctms']);
      final groups = expertRows(rights['workgroups']);
      final period =
          s.values['period'] as String? ?? (meetingId == null ? 'week' : 'all');
      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      final week = today.subtract(Duration(days: today.weekday - 1));
      final meetings = s.rows('Réunions').where((m) {
        if (meetingId != null &&
            s.values['period'] == null &&
            '${m['id']}' != meetingId) {
          return false;
        }
        final date = DateTime.tryParse('${m['date']}')?.toLocal();
        if (period == 'all') return true;
        if (date == null) return false;
        if (period == 'today') {
          return !date.isBefore(today) &&
              date.isBefore(today.add(const Duration(days: 1)));
        }
        return !date.isBefore(week) &&
            date.isBefore(week.add(const Duration(days: 7)));
      }).toList();
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Préparez vos séances et retrouvez votre participation.',
            style: TextStyle(color: s.p.muted),
          ),
          const SizedBox(height: 20),
          Container(
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: s.p.field,
              border: Border.all(color: s.p.border),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                for (final option in [
                  ('week', 'Cette semaine'),
                  ('today', 'Aujourd’hui'),
                  ('all', 'Toutes'),
                ])
                  Expanded(
                    child: SizedBox(
                      height: 46,
                      child: TextButton(
                        style: TextButton.styleFrom(
                          backgroundColor: period == option.$1
                              ? s.p.blueDeep
                              : Colors.transparent,
                          foregroundColor: period == option.$1
                              ? Colors.white
                              : s.p.text,
                          padding: const EdgeInsets.symmetric(horizontal: 6),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        onPressed: () =>
                            s.change(() => s.values['period'] = option.$1),
                        child: Text(
                          option.$2,
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            fontSize: ExpertType.meta,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: Text(
                  period == 'week'
                      ? '${_agendaDay(week)} – ${_agendaDay(week.add(const Duration(days: 6)))}'
                      : period == 'today'
                      ? _agendaDay(today)
                      : 'Toutes les réunions',
                  style: TextStyle(
                    color: s.p.title,
                    fontWeight: FontWeight.w600,
                    fontSize: ExpertType.body,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Text(switch (meetings.length) {
                0 => 'Aucune séance',
                1 => '1 séance',
                final n => '$n séances',
              }, style: TextStyle(color: s.p.muted, fontSize: ExpertType.meta)),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Horaires locaux de votre appareil',
            style: TextStyle(color: s.p.muted, fontSize: ExpertType.meta),
          ),
          const SizedBox(height: 16),
          if (canPlan)
            s.button(
              'Planifier une session',
              () => expertForm(
                s,
                'Planifier une réunion',
                [
                  const ExpertField('titre', 'Titre'),
                  ExpertField(
                    'type',
                    'Type',
                    initial: allowedCtms.isEmpty ? 'WG' : 'CTM',
                    choices: {
                      if (allowedCtms.isNotEmpty)
                        'CTM': 'Sous-commission / CTM',
                      'WG': 'Groupe de travail',
                    },
                  ),
                  ExpertField(
                    'ctm',
                    'Sous-commission',
                    choices: {
                      for (final c in ctms) '${c['id']}': '${c['name']}',
                    },
                  ),
                  ExpertField(
                    'wg',
                    'Groupe (pour une réunion WG)',
                    required: false,
                    choices: {
                      for (final g in groups) '${g['id']}': '${g['name']}',
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
                  if (values['type'] == 'CTM' &&
                      !allowedCtms.contains(values['ctm'])) {
                    s.notify(
                      'Vous ne pouvez pas organiser une réunion de cette sous-commission.',
                    );
                    return false;
                  }
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
                  return s.post('/api/v1/mobile/expert/meetings/', {
                    ...values,
                    'mode': values['lien_reunion_virtuelle']!.trim().isEmpty
                        ? 'PRESENTIEL'
                        : 'EXTERNE',
                    'ctm': int.parse(values['ctm']!),
                    'wg': wg.isEmpty ? null : int.parse(wg),
                    'date': date.toUtc().toIso8601String(),
                  });
                },
              ),
              icon: Icons.event_available,
            ),
          if (canPlan) const SizedBox(height: 16),
          if (meetings.isEmpty && !s.errors.containsKey('Réunions'))
            _MeetingsEmptyState(
              palette: s.p,
              message: switch (period) {
                'week' => 'Aucune réunion prévue cette semaine.',
                'today' => 'Aucune réunion prévue aujourd’hui.',
                _ => 'Aucune réunion enregistrée pour le moment.',
              },
              hint: period == 'all'
                  ? null
                  : 'Consultez l’onglet « Toutes » pour retrouver les séances passées et à venir.',
            ),
          for (final meeting in meetings)
            _MeetingAgendaCard(
              meeting: meeting,
              s: s,
              onOpen: () async {
                final palette = ExpertTheme.of(s.context);
                await Navigator.of(s.context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => ExpertPageTheme(
                      palette: palette,
                      child: Scaffold(
                        backgroundColor: palette.bg,
                        appBar: AppBar(title: Text('${meeting['titre']}')),
                        body: _MeetingDetails(id: '${meeting['id']}'),
                      ),
                    ),
                  ),
                );
                if (s.mounted) await s.load();
              },
            ),
        ],
      );
    },
  );
}

String _agendaDay(DateTime date) {
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
  return '${date.day} ${months[date.month - 1]}';
}

String _presenceLabel(dynamic value) =>
    const {
      'PRESENT': 'Présent',
      'ABSENT': 'Absent',
      'EXCUSED': 'Excusé',
    }[value] ??
    '$value';

class _MeetingAgendaCard extends StatelessWidget {
  const _MeetingAgendaCard({
    required this.meeting,
    required this.s,
    required this.onOpen,
  });
  final Map<String, dynamic> meeting;
  final ExpertModuleState s;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context) {
    final p = s.p;
    final date = DateTime.tryParse('${meeting['date']}')?.toLocal();
    final link = _meetingJoinUrl(meeting) ?? '';
    final join =
        link.isNotEmpty &&
        !['CANCELLED', 'COMPLETED'].contains(meeting['status']);
    final enabled = !s.busy && !s.loading;
    final scope = [
      meeting['ctm_name'],
      meeting['wg_name'],
    ].whereType<String>().where((value) => value.trim().isNotEmpty).join(' · ');
    final agenda = '${meeting['ordre_jour'] ?? ''}'.trim();
    final status = Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: p.surface,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        _meetingStatus(meeting['status']),
        style: TextStyle(
          color: p.muted,
          fontSize: ExpertType.meta,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
    final dateTile = Container(
      width: 66,
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        color: p.blueSoft,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            date == null ? '—' : '${date.day}',
            style: TextStyle(
              color: p.title,
              fontSize: 26,
              height: 1.1,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 5),
          Text(
            date == null ? '' : _agendaDay(date).split(' ').last.toUpperCase(),
            style: TextStyle(
              color: p.isDark ? p.text : p.blueDeep,
              fontSize: ExpertType.label,
              fontWeight: FontWeight.w600,
            ),
          ),
          if (date != null)
            Text(
              '${date.year}',
              style: TextStyle(color: p.muted, fontSize: ExpertType.label),
            ),
        ],
      ),
    );
    final calendar = IconButton.outlined(
      tooltip: 'Ajouter à mon agenda',
      onPressed: enabled
          ? () => s.download(
              '/api/v1/mobile/expert/meetings/${meeting['id']}/calendrier/',
              'reunion-${meeting['id']}.ics',
            )
          : null,
      icon: const Icon(Icons.calendar_month_outlined, size: 20),
    );
    final details = OutlinedButton.icon(
      onPressed: enabled ? onOpen : null,
      icon: const Icon(Icons.article_outlined, size: 18),
      label: const Text('Détails et participation'),
    );
    final meet = FilledButton.icon(
      onPressed: enabled ? () => s.open(link) : null,
      icon: const Icon(Icons.videocam_outlined, size: 20),
      label: Text(
        Uri.tryParse(link)?.host == 'meet.google.com'
            ? 'Rejoindre Meet'
            : 'Rejoindre la réunion',
      ),
    );
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: p.card,
        border: Border.all(color: p.border),
        borderRadius: BorderRadius.circular(14),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxWidth < 580;
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  dateTile,
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${meeting['titre'] ?? 'Réunion'}',
                          style: TextStyle(
                            color: p.title,
                            fontSize: compact ? 16 : 18,
                            height: 1.35,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          date == null
                              ? 'Horaire à confirmer'
                              : '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}',
                          style: TextStyle(
                            color: p.muted,
                            fontSize: ExpertType.body,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        if (compact) ...[const SizedBox(height: 8), status],
                      ],
                    ),
                  ),
                  if (!compact) ...[const SizedBox(width: 12), status],
                ],
              ),
              const SizedBox(height: 16),
              if (scope.isNotEmpty)
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.groups_outlined, size: 18, color: p.muted),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        scope,
                        style: TextStyle(
                          color: p.muted,
                          fontSize: ExpertType.body,
                          height: ExpertType.bodyHeight,
                        ),
                      ),
                    ),
                  ],
                ),
              if (agenda.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(
                  agenda.replaceAll('\n', ' · '),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: p.text,
                    fontSize: ExpertType.body,
                    height: ExpertType.bodyHeight,
                  ),
                ),
              ],
              const SizedBox(height: 18),
              Divider(color: p.border, height: 1),
              const SizedBox(height: 14),
              if (compact) ...[
                if (join) ...[
                  SizedBox(width: double.infinity, child: meet),
                  const SizedBox(height: 10),
                ],
                Row(
                  children: [
                    Expanded(child: details),
                    const SizedBox(width: 10),
                    calendar,
                  ],
                ),
              ] else
                Row(
                  children: [
                    details,
                    const SizedBox(width: 10),
                    calendar,
                    const Spacer(),
                    if (join) meet,
                  ],
                ),
            ],
          );
        },
      ),
    );
  }
}

Future<void> _editMeetingPreparation(
  ExpertModuleState s,
  Map<String, dynamic> meeting,
) => expertForm(
  s,
  'Préparer la séance',
  [
    ExpertField(
      'meet_link',
      'Lien Google Meet',
      required: false,
      initial: '${meeting['lien_reunion_virtuelle'] ?? ''}',
    ),
    ExpertField(
      'ordre_jour',
      'Ordre du jour',
      lines: 4,
      initial: '${meeting['ordre_jour'] ?? ''}',
    ),
    ExpertField(
      'question_vote',
      'Question soumise au vote',
      initial: '${meeting['question_vote'] ?? ''}',
    ),
    ExpertField(
      'documents',
      'Documents : un titre | lien HTTPS par ligne',
      required: false,
      lines: 4,
      initial: expertRows(
        meeting['document_links'],
      ).map((d) => '${d['title']} | ${d['url']}').join('\n'),
    ),
  ],
  (values) async {
    final documents = <Map<String, String>>[];
    for (final line
        in values['documents']!
            .split('\n')
            .where((line) => line.trim().isNotEmpty)) {
      final parts = line.split('|');
      if (parts.length != 2 || parts.first.trim().isEmpty) {
        s.notify(
          'Chaque document doit contenir un titre et un lien HTTPS séparés par |.',
        );
        return false;
      }
      documents.add({'title': parts[0].trim(), 'url': parts[1].trim()});
    }
    return s.run(() async {
      await ApiClient.dio.put(
        '/api/v1/mobile/expert/meetings/${meeting['id']}/preparation/',
        data: {
          ...values,
          'documents': documents,
          'revision': meeting['preparation_revision'] ?? 0,
        },
      );
    });
  },
);

Future<void> _editMeetingPV(
  ExpertModuleState s,
  String id,
  Map<String, dynamic> pv,
) => expertForm(
  s,
  'Brouillon du procès-verbal',
  [
    ExpertField(
      'contenu',
      'Procès-verbal',
      lines: 8,
      initial: '${pv['contenu'] ?? ''}',
    ),
    ExpertField(
      'points_discutes',
      'Points discutés',
      lines: 4,
      initial: '${pv['points_discutes'] ?? ''}',
    ),
    ExpertField(
      'decisions',
      'Décisions',
      lines: 4,
      initial: '${pv['decisions'] ?? ''}',
    ),
    ExpertField(
      'actions',
      'Suivi : action | responsable | AAAA-MM-JJ',
      required: false,
      lines: 4,
      initial: expertRows(pv['actions'])
          .map(
            (a) =>
                '${a['text'] ?? ''} | ${a['responsible'] ?? ''} | ${a['due_date'] ?? ''}',
          )
          .join('\n'),
    ),
  ],
  (values) async {
    final actions = <Map<String, String>>[];
    for (final line
        in values['actions']!
            .split('\n')
            .where((line) => line.trim().isNotEmpty)) {
      final parts = line.split('|').map((part) => part.trim()).toList();
      if (parts.length > 3 || parts.first.isEmpty) {
        s.notify(
          'Utilisez une action, un responsable et une échéance séparés par |.',
        );
        return false;
      }
      actions.add({
        'text': parts[0],
        'responsible': parts.length > 1 ? parts[1] : '',
        'due_date': parts.length > 2 ? parts[2] : '',
      });
    }
    return s.run(() async {
      await ApiClient.dio.put(
        '/api/v1/mobile/expert/meetings/$id/pv_draft/',
        data: {...values, 'actions': actions, 'revision': pv['revision'] ?? 0},
      );
    });
  },
);

class _MeetingDetails extends StatelessWidget {
  const _MeetingDetails({required this.id});
  final String id;
  @override
  Widget build(BuildContext context) => ExpertModule(
    title: 'Participation',
    endpoints: {
      'Réunion': '/api/v1/mobile/expert/meetings/$id/details/',
      'Profil': '/api/v1/experts/me/',
    },
    builder: (s) {
      final meeting = s.map('Réunion');
      if (meeting.isEmpty) return const SizedBox.shrink();
      final rights = expertMap(meeting['capabilities']);
      final canManage = rights['can_manage'] == true;
      final participate = rights['can_participate'] == true;
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
      final validated =
          pv['redaction'] == 'VALIDE' || pv['signature_date'] != null;
      final documents = expertRows(meeting['document_links']);
      return Column(
        children: [
          s.card('Préparation et visioconférence', [
            s.actions([
              if (active && _meetingJoinUrl(meeting) != null)
                s.button(
                  '${meeting['mode']}' == 'SALLE'
                      ? 'Rejoindre la salle web'
                      : 'Rejoindre Meet',
                  () => s.open(_meetingJoinUrl(meeting)!),
                  icon: Icons.videocam_outlined,
                ),
              if (canManage && active)
                s.button(
                  'Préparer la séance',
                  () => _editMeetingPreparation(s, meeting),
                  icon: Icons.edit_outlined,
                ),
            ]),
            const SizedBox(height: 16),
            if (documents.isEmpty) const Text('Aucun document associé.'),
            for (final document in documents)
              s.button(
                '${document['title']}',
                () => s.open('${document['url']}'),
                icon: Icons.attach_file,
              ),
          ]),
          s.card('${meeting['titre']}', [
            Text(
              '${_meetingDate(meeting['date'])} — ${_meetingStatus(meeting['status'])}',
            ),
            const SizedBox(height: 12),
            SelectableText('${meeting['ordre_jour'] ?? ''}'),
            const SizedBox(height: 12),
            Text(
              '${meeting['question_vote'] ?? ''}'.trim().isEmpty
                  ? 'L’organisateur doit préciser la question soumise au vote.'
                  : 'Question soumise au vote : ${meeting['question_vote']}',
            ),
            Text('Votre vote : ${mine?['choix'] ?? 'Non voté'}'),
            s.actions([
              if (active && participate)
                s.button(
                  'Signaler mon absence',
                  () => s.post('/api/v1/mobile/expert/meetings/$id/excuser/'),
                ),
              if (active && !present && rights['can_checkin'] == true)
                s.button(
                  'Émarger ma présence',
                  () => s.post(
                    '/api/v1/mobile/expert/meetings/$id/checkin_presence/',
                  ),
                  icon: Icons.how_to_reg,
                ),
              if (active &&
                  present &&
                  rights['can_vote'] == true &&
                  '${meeting['question_vote'] ?? ''}'.trim().isNotEmpty)
                for (final choice in ['POUR', 'CONTRE', 'ABSTENTION'])
                  s.button(
                    'Voter $choice',
                    () => s.post('/api/v1/mobile/expert/meetings/$id/vote/', {
                      'choix': choice,
                    }),
                  ),
              if (active && canManage)
                s.button(
                  'Clore le scrutin et générer le PV',
                  () => s.post('/api/v1/mobile/expert/meetings/$id/close/'),
                ),
            ]),
          ]),
          s.card('Émargement', [
            Text(
              presences.isEmpty
                  ? 'Aucune présence déclarée pour le moment.'
                  : '${presences.where((p) => p['status'] == 'PRESENT').length} présence(s) confirmée(s)',
            ),
            for (final presence in presences)
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(
                  '${presence['expert_name']}',
                  style: TextStyle(color: s.p.text),
                ),
                subtitle: Text(
                  _presenceLabel(presence['status']),
                  style: TextStyle(color: s.p.muted),
                ),
                trailing: canManage && active
                    ? PopupMenuButton<String>(
                        tooltip: 'Modifier la présence',
                        itemBuilder: (_) => [
                          for (final status in ['PRESENT', 'ABSENT', 'EXCUSED'])
                            PopupMenuItem(
                              value: status,
                              child: Text(_presenceLabel(status)),
                            ),
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
          ]),
          s.card('Votes (${votes.length})', [
            if (votes.isEmpty) const Text('Aucun vote enregistré.'),
            for (final vote in votes)
              Text('${vote['expert_name']} : ${vote['choix']}'),
          ]),
          s.card('Procès-verbal', [
            if (pv.isNotEmpty)
              Text(
                validated ? 'Validé' : 'Brouillon — non validé',
                style: TextStyle(
                  color: validated ? s.p.green : s.p.muted,
                  fontWeight: FontWeight.w600,
                ),
              ),
            SelectableText(
              '${pv['contenu'] ?? 'Le PV sera disponible après la clôture du scrutin.'}',
            ),
            for (final action in expertRows(pv['actions']))
              Text(
                '• ${action['text']} — ${action['responsible'] ?? ''} ${action['due_date'] ?? ''}',
              ),
            s.actions([
              if (canManage && pv.isNotEmpty && !validated)
                s.button(
                  'Rédiger le PV',
                  () => _editMeetingPV(s, id, pv),
                  icon: Icons.edit_note,
                ),
              if (rights['can_validate_pv'] == true &&
                  meeting['status'] == 'COMPLETED' &&
                  pv.isNotEmpty &&
                  !validated &&
                  '${pv['points_discutes'] ?? ''}'.trim().isNotEmpty &&
                  '${pv['decisions'] ?? ''}'.trim().isNotEmpty)
                s.button(
                  'Valider le PV',
                  () => s.run(() async {
                    await ApiClient.dio.post(
                      '/api/v1/pv/${pv['id']}/sign/',
                      data: {'revision': pv['revision']},
                    );
                  }),
                  icon: Icons.verified_outlined,
                ),
            ]),
          ]),
        ],
      );
    },
  );
}

String _meetingDate(dynamic value) {
  final date = DateTime.tryParse('$value')?.toLocal();
  if (date == null) return 'Horaire à confirmer';
  String two(int n) => n.toString().padLeft(2, '0');
  return '${two(date.day)}/${two(date.month)}/${date.year} à ${two(date.hour)}:${two(date.minute)}';
}

String _meetingStatus(dynamic value) =>
    const {
      'PLANNED': 'Planifiée',
      'IN_PROGRESS': 'En cours',
      'COMPLETED': 'Terminée',
      'CANCELLED': 'Annulée',
    }[value] ??
    '$value';

/// Lien de participation : lien externe fourni, sinon la salle web LiveKit
/// de la plateforme pour les réunions en mode SALLE.
String? _meetingJoinUrl(Map<String, dynamic> meeting) {
  final link = '${meeting['lien_reunion_virtuelle'] ?? ''}'.trim();
  if (link.isNotEmpty) return link;
  if ('${meeting['mode'] ?? ''}' == 'SALLE' && meeting['id'] != null) {
    final base = ApiClient.baseUrl.replaceFirst(RegExp(r'/+$'), '');
    return '$base/app/salle/${meeting['id']}/';
  }
  return null;
}

class _MeetingsEmptyState extends StatelessWidget {
  const _MeetingsEmptyState({
    required this.palette,
    required this.message,
    this.hint,
  });

  final ExpertPalette palette;
  final String message;
  final String? hint;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 28),
      decoration: BoxDecoration(
        color: p.card,
        border: Border.all(color: p.border),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: p.blueSoft,
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.event_busy_outlined, color: p.blue, size: 24),
          ),
          const SizedBox(height: 14),
          Text(
            message,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: p.title,
              fontWeight: FontWeight.w600,
              fontSize: ExpertType.body,
            ),
          ),
          if (hint != null) ...[
            const SizedBox(height: 6),
            Text(
              hint!,
              textAlign: TextAlign.center,
              style: TextStyle(color: p.muted, fontSize: ExpertType.meta),
            ),
          ],
        ],
      ),
    );
  }
}

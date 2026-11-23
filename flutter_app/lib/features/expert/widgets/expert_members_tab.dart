import 'package:flutter/material.dart';

import '../../../core/api/api_client.dart';
import 'expert_module.dart';
import 'expert_theme.dart';
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
      final canManage = [
        'ADMIN',
        'COORD_CTC',
      ].contains('${s.map('Profil')['role_id']}');
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
            _expertCard(s, expert, canManage: canManage),
          if (s.rows('Experts').isEmpty && !s.errors.containsKey('Experts'))
            s.card('Annuaire', [const Text('Aucun expert disponible.')]),
        ],
      );
    },
  );
}

const _expertStatuses = {
  'ACTIVE': 'Actif',
  'PENDING': 'En attente',
  'INACTIVE': 'Inactif',
  'SUSPENDED': 'Suspendu',
  'REJECTED': 'Rejeté',
};

String _initials(String name) {
  final parts = name
      .split(RegExp(r'\s+'))
      .where((part) => part.isNotEmpty)
      .take(2);
  final value = parts.map((part) => part[0].toUpperCase()).join();
  return value.isEmpty ? '?' : value;
}

Future<void> _showExpertSheet(
  ExpertModuleState s,
  Map<String, dynamic> expert,
) async {
  await s.run(
    () async {
      final response = await ApiClient.dio.get(
        '/api/v1/experts/${expert['id']}/',
      );
      final detail = expertMap(response.data);
      if (s.mounted) {
        final contacts = s.rows('Contacts');
        final contact = contacts
            .where((c) => '${c['id']}' == '${expert['id']}')
            .firstOrNull;
        await Navigator.of(s.context).push(
          MaterialPageRoute<void>(
            builder: (context) => ExpertProfilePage(
              expert: detail,
              contact: contact,
              palette: s.p,
              onOpenCv: () => s.open('${detail['cv']}'),
              onMessage: contact == null
                  ? null
                  : () => openExpertMessaging(context, contact: contact),
            ),
          ),
        );
      }
    },
    success: '',
    reload: false,
  );
}

class ExpertProfilePage extends StatelessWidget {
  const ExpertProfilePage({
    super.key,
    required this.expert,
    required this.palette,
    this.contact,
    this.onOpenCv,
    this.onMessage,
  });

  final Map<String, dynamic> expert;
  final Map<String, dynamic>? contact;
  final ExpertPalette palette;
  final VoidCallback? onOpenCv;
  final VoidCallback? onMessage;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    final user = expertMap(expert['user']);
    final structure = expertMap(expert['structure']);
    final affectations = expertRows(expert['affectations']);
    final name = expertName(expert);
    final status = '${expert['status'] ?? ''}';
    final cv = '${expert['cv'] ?? ''}';
    final specialties = '${expert['specialties'] ?? ''}'.trim();
    final ctm = '${expert['ctm_name'] ?? ''}'.trim();
    final hasSensitive = [
      expert['bank_name'],
      expert['bank_account'],
      expert['mobile_money_number'],
    ].any((value) => '$value'.trim().isNotEmpty && value != null);
    return Scaffold(
      backgroundColor: p.bg,
      appBar: AppBar(
        backgroundColor: p.nav,
        foregroundColor: p.title,
        elevation: 0,
        scrolledUnderElevation: 1,
        leading: IconButton(
          key: const ValueKey('expert-profile-back'),
          tooltip: 'Retour',
          onPressed: () => Navigator.pop(context),
          icon: const Icon(Icons.arrow_back),
        ),
        titleSpacing: 0,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Fiche expert',
              style: TextStyle(
                color: p.title,
                fontSize: ExpertType.body + 2,
                fontWeight: FontWeight.w700,
              ),
            ),
            Text(
              'Annuaire > Experts & Groupes',
              style: TextStyle(
                color: p.muted,
                fontSize: ExpertType.label,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          Flexible(
            child: ListView(
              key: const ValueKey('expert-profile-scroll'),
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 20),
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    CircleAvatar(
                      radius: 34,
                      backgroundColor: p.blueSoft,
                      child: Text(
                        _initials(name),
                        style: TextStyle(
                          color: p.blue,
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            name,
                            style: TextStyle(
                              color: p.title,
                              fontSize: 22,
                              height: 1.25,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(height: 5),
                          Text(
                            '${structure['name'] ?? expert['structure_name'] ?? ''}',
                            style: TextStyle(
                              color: p.muted,
                              fontSize: ExpertType.body,
                              height: ExpertType.bodyHeight,
                            ),
                          ),
                          if (status.isNotEmpty) ...[
                            const SizedBox(height: 10),
                            _StatusChip(status: status, palette: p),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 22),
                _ProfileSection(
                  palette: p,
                  icon: Icons.person_outline,
                  title: 'Coordonnées',
                  children: [
                    _ProfileLine(p, 'Adresse e-mail', '${user['email'] ?? ''}'),
                    if ('${user['phone'] ?? ''}'.trim().isNotEmpty)
                      _ProfileLine(p, 'Téléphone', '${user['phone']}'),
                    if ('${user['province'] ?? ''}'.trim().isNotEmpty)
                      _ProfileLine(p, 'Province', '${user['province']}'),
                  ],
                ),
                if (specialties.isNotEmpty ||
                    '${structure['category'] ?? ''}'.isNotEmpty)
                  _ProfileSection(
                    palette: p,
                    icon: Icons.work_outline,
                    title: 'Expertise',
                    children: [
                      if (specialties.isNotEmpty)
                        _ProfileLine(p, 'Spécialités', specialties),
                      if ('${structure['category'] ?? ''}'.trim().isNotEmpty)
                        _ProfileLine(
                          p,
                          'Catégorie',
                          '${structure['category']}',
                        ),
                    ],
                  ),
                _ProfileSection(
                  palette: p,
                  icon: Icons.apartment_outlined,
                  title: 'Structure de rattachement',
                  children: [
                    _ProfileLine(
                      p,
                      'Structure',
                      '${structure['name'] ?? expert['structure_name'] ?? ''}',
                    ),
                    if ('${structure['acronym'] ?? ''}'.trim().isNotEmpty)
                      _ProfileLine(p, 'Sigle', '${structure['acronym']}'),
                    if ('${structure['contact_person'] ?? ''}'
                        .trim()
                        .isNotEmpty)
                      _ProfileLine(
                        p,
                        'Contact structure',
                        '${structure['contact_person']}',
                      ),
                    if ('${structure['email'] ?? ''}'.trim().isNotEmpty)
                      _ProfileLine(
                        p,
                        'E-mail structure',
                        '${structure['email']}',
                      ),
                    if ('${structure['phone'] ?? ''}'.trim().isNotEmpty)
                      _ProfileLine(
                        p,
                        'Téléphone structure',
                        '${structure['phone']}',
                      ),
                  ],
                ),
                _ProfileSection(
                  palette: p,
                  icon: Icons.groups_outlined,
                  title: 'CTM / groupes de travail',
                  children: [
                    if (ctm.isNotEmpty)
                      _ProfileLine(p, 'Sous-commission principale', ctm),
                    if (affectations.isEmpty)
                      Text(
                        'Aucune affectation enregistrée.',
                        style: TextStyle(color: p.muted),
                      )
                    else
                      for (final affectation in affectations)
                        _AffiliationTile(palette: p, affectation: affectation),
                  ],
                ),
                if ('${expert['appointment_decree_number'] ?? ''}'
                        .trim()
                        .isNotEmpty ||
                    '${expert['appointment_date'] ?? ''}'.trim().isNotEmpty ||
                    '${expert['inscription_date'] ?? ''}'.trim().isNotEmpty ||
                    '${expert['activation_date'] ?? ''}'.trim().isNotEmpty)
                  _ProfileSection(
                    palette: p,
                    icon: Icons.badge_outlined,
                    title: 'Mandat & activité',
                    children: [
                      if ('${expert['appointment_decree_number'] ?? ''}'
                          .trim()
                          .isNotEmpty)
                        _ProfileLine(
                          p,
                          'Acte de nomination',
                          '${expert['appointment_decree_number']}',
                        ),
                      if ('${expert['appointment_date'] ?? ''}'
                          .trim()
                          .isNotEmpty)
                        _ProfileLine(
                          p,
                          'Date de nomination',
                          _formatDate(expert['appointment_date']),
                        ),
                      if ('${expert['inscription_date'] ?? ''}'
                          .trim()
                          .isNotEmpty)
                        _ProfileLine(
                          p,
                          'Inscription',
                          _formatDate(expert['inscription_date']),
                        ),
                      if ('${expert['activation_date'] ?? ''}'
                          .trim()
                          .isNotEmpty)
                        _ProfileLine(
                          p,
                          'Activation',
                          _formatDate(expert['activation_date']),
                        ),
                      if ('${expert['accepted_by_name'] ?? ''}'
                          .trim()
                          .isNotEmpty)
                        _ProfileLine(
                          p,
                          'Accepté par',
                          '${expert['accepted_by_name']}',
                        ),
                      if ('${expert['rejection_reason'] ?? ''}'
                          .trim()
                          .isNotEmpty)
                        _ProfileLine(
                          p,
                          'Motif du rejet',
                          '${expert['rejection_reason']}',
                        ),
                    ],
                  ),
                if ('${expert['profile_update_status'] ?? ''}'
                    .trim()
                    .isNotEmpty)
                  _ProfileSection(
                    palette: p,
                    icon: Icons.fact_check_outlined,
                    title: 'Conformité du profil',
                    children: [
                      _ProfileLine(
                        p,
                        'État documentaire',
                        _profileStatusLabel(
                          '${expert['profile_update_status']}',
                        ),
                      ),
                      if ('${expert['profile_update_submitted_at'] ?? ''}'
                          .trim()
                          .isNotEmpty)
                        _ProfileLine(
                          p,
                          'Soumis le',
                          _formatDate(expert['profile_update_submitted_at']),
                        ),
                    ],
                  ),
                if (cv.isNotEmpty && cv != 'null')
                  _ProfileSection(
                    palette: p,
                    icon: Icons.description_outlined,
                    title: 'Documents',
                    children: [
                      ListTile(
                        key: const ValueKey('expert-profile-cv'),
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(
                          Icons.picture_as_pdf_outlined,
                          color: p.red,
                        ),
                        title: const Text('Curriculum vitæ'),
                        subtitle: const Text('Ouvrir le document'),
                        trailing: const Icon(Icons.open_in_new),
                        onTap: onOpenCv,
                      ),
                    ],
                  ),
                if (hasSensitive)
                  _ProfileSection(
                    palette: p,
                    icon: Icons.lock_outline,
                    title: 'Paiements — données confidentielles',
                    children: [
                      if ('${expert['bank_name'] ?? ''}'.trim().isNotEmpty)
                        _ProfileLine(p, 'Banque', '${expert['bank_name']}'),
                      if ('${expert['bank_account'] ?? ''}'.trim().isNotEmpty)
                        _ProfileLine(
                          p,
                          'Compte',
                          _maskNumber('${expert['bank_account']}'),
                        ),
                      if ('${expert['mobile_money_number'] ?? ''}'
                          .trim()
                          .isNotEmpty)
                        _ProfileLine(
                          p,
                          'Mobile Money',
                          _maskNumber('${expert['mobile_money_number']}'),
                        ),
                    ],
                  ),
                const SizedBox(height: 8),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 16),
            decoration: BoxDecoration(
              color: p.card,
              border: Border(top: BorderSide(color: p.border)),
            ),
            child: Row(
              children: [
                if (onMessage != null)
                  Expanded(
                    child: FilledButton.icon(
                      key: const ValueKey('expert-sheet-message'),
                      onPressed: onMessage,
                      icon: const Icon(Icons.chat_bubble_outline),
                      label: const Text('Discuter'),
                    ),
                  ),
                if (onMessage != null) const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('Fermer'),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status, required this.palette});

  final String status;
  final ExpertPalette palette;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'ACTIVE' => palette.green,
      'PENDING' => palette.amber,
      'SUSPENDED' || 'REJECTED' => palette.red,
      _ => palette.subtle,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        _expertStatuses[status] ?? status,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w700,
          fontSize: ExpertType.label,
        ),
      ),
    );
  }
}

class _ProfileSection extends StatelessWidget {
  const _ProfileSection({
    required this.palette,
    required this.icon,
    required this.title,
    required this.children,
  });

  final ExpertPalette palette;
  final IconData icon;
  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: p.surface,
        border: Border.all(color: p.border),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 20, color: p.blue),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  title,
                  style: TextStyle(
                    color: p.title,
                    fontWeight: FontWeight.w700,
                    fontSize: ExpertType.body,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ...children,
        ],
      ),
    );
  }
}

class _ProfileLine extends StatelessWidget {
  const _ProfileLine(this.palette, this.label, this.value);

  final ExpertPalette palette;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    if (value.trim().isEmpty || value == 'null') return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 9),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 116,
            child: Text(
              label,
              style: TextStyle(color: palette.muted, fontSize: ExpertType.meta),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                color: palette.text,
                fontSize: ExpertType.body,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _AffiliationTile extends StatelessWidget {
  const _AffiliationTile({required this.palette, required this.affectation});

  final ExpertPalette palette;
  final Map<String, dynamic> affectation;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    final ctm = '${affectation['ctm_name'] ?? ''}'.trim();
    final wg = '${affectation['wg_name'] ?? ''}'.trim();
    final role = '${affectation['role'] ?? ''}'.trim();
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: p.card,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: p.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            wg.isEmpty ? ctm : wg,
            style: TextStyle(
              color: p.title,
              fontWeight: FontWeight.w700,
              fontSize: ExpertType.body,
            ),
          ),
          if (wg.isNotEmpty && ctm.isNotEmpty)
            Text(
              ctm,
              style: TextStyle(color: p.muted, fontSize: ExpertType.meta),
            ),
          if (role.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 5),
              child: Text(
                role,
                style: TextStyle(
                  color: p.blue,
                  fontSize: ExpertType.meta,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

String _formatDate(dynamic value) {
  if (value == null || '$value'.trim().isEmpty) return '';
  final raw = '$value';
  final date = DateTime.tryParse(raw);
  if (date == null) return raw;
  final local = date.toLocal();
  return '${local.day.toString().padLeft(2, '0')}/'
      '${local.month.toString().padLeft(2, '0')}/'
      '${local.year}';
}

String _maskNumber(String value) {
  final compact = value.replaceAll(RegExp(r'\s+'), '');
  if (compact.length <= 4) return compact;
  return '•••• ${compact.substring(compact.length - 4)}';
}

String _profileStatusLabel(String status) => switch (status) {
  'NOT_STARTED' => 'Non commencé',
  'IN_PROGRESS' => 'En cours',
  'SUBMITTED' => 'Soumis',
  'UNDER_REVIEW' => 'En examen',
  'COMPLETE' => 'Conforme et vérifié',
  'NEEDS_CORRECTION' => 'À corriger',
  'REJECTED' => 'Rejeté',
  'EXPIRED' => 'À renouveler',
  _ => status,
};

Widget _expertCard(
  ExpertModuleState s,
  Map<String, dynamic> expert, {
  required bool canManage,
}) {
  final p = s.p;
  final name = expertName(expert);
  final status = '${expert['status'] ?? ''}';
  final structure = '${expert['structure_name'] ?? ''}'.trim();
  final specialties = '${expert['specialties'] ?? ''}'.trim();
  final contacts = s.rows('Contacts');
  final contact = contacts
      .where((c) => '${c['id']}' == '${expert['id']}')
      .firstOrNull;
  final statusColor = switch (status) {
    'ACTIVE' => p.green,
    'PENDING' => p.amber,
    'SUSPENDED' || 'REJECTED' => p.red,
    _ => p.subtle,
  };
  final disabled = s.busy || s.loading;
  return Container(
    width: double.infinity,
    margin: const EdgeInsets.only(bottom: 12),
    padding: const EdgeInsets.fromLTRB(16, 16, 8, 8),
    decoration: BoxDecoration(
      color: p.card,
      border: Border.all(color: p.border),
      borderRadius: BorderRadius.circular(12),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(right: 8),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                radius: 22,
                backgroundColor: p.blueSoft,
                child: Text(
                  _initials(name),
                  style: TextStyle(
                    color: p.blue,
                    fontWeight: FontWeight.w700,
                    fontSize: ExpertType.body,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name,
                      style: TextStyle(
                        color: p.title,
                        fontWeight: FontWeight.w700,
                        fontSize: 16,
                        height: 1.3,
                      ),
                    ),
                    if (structure.isNotEmpty)
                      Text(
                        structure,
                        style: TextStyle(
                          color: p.muted,
                          fontSize: ExpertType.meta,
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              if (status.isNotEmpty)
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 3,
                  ),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    _expertStatuses[status] ?? status,
                    style: TextStyle(
                      color: statusColor,
                      fontWeight: FontWeight.w700,
                      fontSize: ExpertType.label,
                    ),
                  ),
                ),
            ],
          ),
        ),
        if (specialties.isNotEmpty) ...[
          const SizedBox(height: 10),
          Text(specialties, style: TextStyle(color: p.text)),
        ],
        const SizedBox(height: 6),
        Wrap(
          spacing: 4,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            TextButton.icon(
              onPressed: disabled ? null : () => _showExpertSheet(s, expert),
              icon: const Icon(Icons.badge_outlined, size: 18),
              label: const Text('Voir la fiche'),
            ),
            if (contact != null)
              TextButton.icon(
                onPressed: disabled
                    ? null
                    : () => openExpertMessaging(s.context, contact: contact),
                icon: const Icon(Icons.chat_bubble_outline, size: 18),
                label: const Text('Discuter'),
              ),
            if (canManage && status == 'ACTIVE')
              TextButton.icon(
                style: TextButton.styleFrom(foregroundColor: p.red),
                onPressed: disabled
                    ? null
                    : () async {
                        final confirmed = await s.confirm(
                          'Désactiver $name ?',
                          'L’expert ne pourra plus contribuer aux travaux tant qu’il n’aura pas été réactivé.',
                          action: 'Désactiver',
                          destructive: true,
                        );
                        if (!confirmed) return;
                        await s.run(
                          () => ApiClient.dio.post(
                            '/api/v1/experts/${expert['id']}/deactivate/',
                          ),
                          success: 'Expert désactivé.',
                        );
                      },
                icon: const Icon(Icons.person_off_outlined, size: 18),
                label: const Text('Désactiver'),
              ),
            if (canManage && status == 'INACTIVE')
              TextButton.icon(
                onPressed: disabled
                    ? null
                    : () => s.run(
                        () => ApiClient.dio.post(
                          '/api/v1/experts/${expert['id']}/activate/',
                        ),
                        success: 'Expert réactivé.',
                      ),
                icon: const Icon(Icons.person_add_alt_1_outlined, size: 18),
                label: const Text('Réactiver'),
              ),
          ],
        ),
      ],
    ),
  );
}

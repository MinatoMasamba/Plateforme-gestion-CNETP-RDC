import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_client.dart';
import '../theme/copil_theme.dart';
import 'organisation_form_screen.dart';
import 'organisation_resources_screen.dart';

Map<String, dynamic> _map(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return const {};
}

List<Map<String, dynamic>> _maps(dynamic value) {
  if (value is! List) return const [];
  return value.map(_map).toList();
}

String _text(dynamic value, [String fallback = '']) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? fallback : text;
}

int _number(dynamic value) => (value as num?)?.toInt() ?? 0;

String _dateLabel(String raw) {
  final date = DateTime.tryParse(raw)?.toLocal();
  if (date == null) return raw;
  final day = date.day.toString().padLeft(2, '0');
  final month = date.month.toString().padLeft(2, '0');
  final hour = date.hour.toString().padLeft(2, '0');
  final minute = date.minute.toString().padLeft(2, '0');
  return '$day/$month/${date.year} à $hour:$minute';
}

class CopilOrganisationData {
  const CopilOrganisationData({
    required this.canManage,
    required this.versionStatus,
    required this.sourceDocument,
    required this.copilPostCount,
    required this.stPostCount,
    required this.scCount,
    required this.expertCount,
    required this.pendingCount,
    required this.copilGroups,
    required this.stGroups,
    required this.subcommissions,
    required this.pendingExperts,
    required this.journal,
  });

  final bool canManage;
  final String versionStatus;
  final String sourceDocument;
  final int copilPostCount;
  final int stPostCount;
  final int scCount;
  final int expertCount;
  final int pendingCount;
  final List<OrganisationGroup> copilGroups;
  final List<OrganisationGroup> stGroups;
  final List<OrganisationSubcommission> subcommissions;
  final List<PendingExpert> pendingExperts;
  final List<JournalEntry> journal;

  factory CopilOrganisationData.fromJson(Map<String, dynamic> json) {
    final version = _map(json['version']);
    final counts = _map(json['counts']);
    return CopilOrganisationData(
      canManage: json['can_manage'] == true,
      versionStatus: _text(version['status_label'], 'Préparation'),
      sourceDocument: _text(version['source_document']),
      copilPostCount: _number(counts['copil_posts']),
      stPostCount: _number(counts['st_posts']),
      scCount: _number(counts['subcommissions']),
      expertCount: _number(counts['experts']),
      pendingCount: _number(counts['pending']),
      copilGroups: _maps(
        json['copil_groups'],
      ).map(OrganisationGroup.fromJson).toList(),
      stGroups: _maps(
        json['st_groups'],
      ).map(OrganisationGroup.fromJson).toList(),
      subcommissions: _maps(
        json['subcommissions'],
      ).map(OrganisationSubcommission.fromJson).toList(),
      pendingExperts: _maps(
        json['pending_experts'],
      ).map(PendingExpert.fromJson).toList(),
      journal: _maps(json['journal']).map(JournalEntry.fromJson).toList(),
    );
  }
}

class OrganisationGroup {
  const OrganisationGroup({
    required this.code,
    required this.label,
    required this.posts,
  });

  final String code;
  final String label;
  final List<OrganisationPost> posts;

  factory OrganisationGroup.fromJson(Map<String, dynamic> json) {
    return OrganisationGroup(
      code: _text(json['code']),
      label: _text(json['label']),
      posts: _maps(json['posts']).map(OrganisationPost.fromJson).toList(),
    );
  }
}

class OrganisationPost {
  const OrganisationPost({
    required this.id,
    required this.code,
    required this.title,
    required this.origin,
    required this.status,
    required this.holders,
    required this.proposedHolders,
  });

  final int id;
  final String code;
  final String title;
  final String origin;
  final String status;
  final List<OrganisationHolder> holders;
  final List<OrganisationHolder> proposedHolders;

  factory OrganisationPost.fromJson(Map<String, dynamic> json) {
    return OrganisationPost(
      id: _number(json['id']),
      code: _text(json['code']),
      title: _text(json['title'], 'Fonction à renseigner'),
      origin: _text(json['origin'], 'À renseigner'),
      status: _text(json['status'], 'Proposée'),
      holders: _maps(json['holders']).map(OrganisationHolder.fromJson).toList(),
      proposedHolders: _maps(
        json['proposed_holders'],
      ).map(OrganisationHolder.fromJson).toList(),
    );
  }
}

class OrganisationHolder {
  const OrganisationHolder({
    required this.name,
    required this.reference,
    required this.startDate,
  });

  final String name;
  final String reference;
  final String startDate;

  factory OrganisationHolder.fromJson(Map<String, dynamic> json) {
    return OrganisationHolder(
      name: _text(json['name']),
      reference: _text(json['reference']),
      startDate: _text(json['start_date']),
    );
  }
}

class OrganisationSubcommission {
  const OrganisationSubcommission({
    required this.id,
    required this.code,
    required this.name,
    required this.status,
    required this.domain,
    required this.proposedBureauCount,
    required this.experts,
    required this.posts,
    required this.groups,
  });

  final int id;
  final String code;
  final String name;
  final String status;
  final String domain;
  final int proposedBureauCount;
  final List<MigratedExpert> experts;
  final List<OrganisationPost> posts;
  final List<OrganisationWorkingGroup> groups;

  factory OrganisationSubcommission.fromJson(Map<String, dynamic> json) {
    return OrganisationSubcommission(
      id: _number(json['id']),
      code: _text(json['code']),
      name: _text(json['official_name'], _text(json['name'])),
      status: _text(json['status']),
      domain: _text(json['domain']),
      proposedBureauCount: _number(json['proposed_bureau_count']),
      experts: _maps(
        json['migrated_experts'],
      ).map(MigratedExpert.fromJson).toList(),
      posts: _maps(json['posts']).map(OrganisationPost.fromJson).toList(),
      groups: _maps(
        json['groups'],
      ).map(OrganisationWorkingGroup.fromJson).toList(),
    );
  }
}

class MigratedExpert {
  const MigratedExpert({required this.name, required this.structure});

  final String name;
  final String structure;

  factory MigratedExpert.fromJson(Map<String, dynamic> json) {
    return MigratedExpert(
      name: _text(json['name']),
      structure: _text(json['structure']),
    );
  }
}

class OrganisationWorkingGroup {
  const OrganisationWorkingGroup({
    required this.code,
    required this.name,
    required this.mission,
    required this.activity,
    required this.status,
  });

  final String code;
  final String name;
  final String mission;
  final String activity;
  final String status;

  factory OrganisationWorkingGroup.fromJson(Map<String, dynamic> json) {
    return OrganisationWorkingGroup(
      code: _text(json['code']),
      name: _text(json['name']),
      mission: _text(json['mission']),
      activity: _text(json['activity']),
      status: _text(json['status']),
    );
  }
}

class PendingExpert {
  const PendingExpert({
    required this.name,
    required this.structure,
    required this.reason,
  });

  final String name;
  final String structure;
  final String reason;

  factory PendingExpert.fromJson(Map<String, dynamic> json) {
    return PendingExpert(
      name: _text(json['name']),
      structure: _text(json['structure']),
      reason: _text(json['reason']),
    );
  }
}

class JournalEntry {
  const JournalEntry({
    required this.createdAt,
    required this.actor,
    required this.operation,
    required this.reason,
  });

  final String createdAt;
  final String actor;
  final String operation;
  final String reason;

  factory JournalEntry.fromJson(Map<String, dynamic> json) {
    return JournalEntry(
      createdAt: _dateLabel(_text(json['created_at'])),
      actor: _text(json['actor'], 'Non enregistré'),
      operation: _text(json['operation']),
      reason: _text(json['reason']),
    );
  }
}

enum _OrganisationSection { copil, secretariat, subcommissions, journal }

extension on _OrganisationSection {
  String get label {
    switch (this) {
      case _OrganisationSection.copil:
        return 'COPIL';
      case _OrganisationSection.secretariat:
        return 'Secrétariat technique';
      case _OrganisationSection.subcommissions:
        return 'Sous-commissions';
      case _OrganisationSection.journal:
        return 'Journal de préparation';
    }
  }
}

class CopilOrganisationScreen extends ConsumerStatefulWidget {
  const CopilOrganisationScreen({super.key});

  @override
  ConsumerState<CopilOrganisationScreen> createState() =>
      _CopilOrganisationScreenState();
}

class _CopilOrganisationScreenState
    extends ConsumerState<CopilOrganisationScreen> {
  _OrganisationSection _section = _OrganisationSection.copil;
  CopilOrganisationData? _data;
  bool _loading = true;
  String? _error;
  Map<String, dynamic> _configurationIds = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await ApiClient.dio.get(
        '/api/v1/mobile/pilotage/organisation/',
      );
      final data = CopilOrganisationData.fromJson(_map(response.data));
      if (!mounted) return;
      setState(() {
        _data = data;
        _configurationIds = _map(_map(response.data)['ids']);
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = "Impossible de charger l'organisation CNE-ITP.";
        _loading = false;
      });
    }
  }

  void _showInfo(String message) {
    if (message == 'reload') {
      _load();
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
    );
  }

  Future<void> _configure(
    String kind, {
    int? id,
    Map<String, dynamic> initial = const {},
  }) async {
    final saved = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) =>
            OrganisationFormScreen(kind: kind, id: id, initial: initial),
      ),
    );
    if (saved == true && mounted) await _load();
  }

  @override
  Widget build(BuildContext context) {
    final dark = ref.watch(copilDarkProvider);
    final p = dark
        ? CopilPalette.dark.surfaces(
            bg: const Color(0xFF0B1220),
            card: const Color(0xFF111D2D),
            topbar: Colors.black,
            border: const Color(0xFF334155),
          )
        : CopilPalette.light;
    return CopilTheme(
      palette: p,
      child: Scaffold(
        backgroundColor: p.bg,
        body: SafeArea(
          child: Column(
            children: [
              _OrganisationTopbar(
                palette: p,
                status: _data?.versionStatus ?? 'Préparation',
                onBack: () => context.go('/pilotage/directoire'),
                onTheme: () =>
                    ref.read(copilDarkProvider.notifier).state = !dark,
              ),
              Expanded(
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final wide = constraints.maxWidth >= 768;
                    return Row(
                      children: [
                        if (wide)
                          _OrganisationSidebar(
                            palette: p,
                            section: _section,
                            onSelect: (section) =>
                                setState(() => _section = section),
                            onManagement: () => Navigator.push(
                              context,
                              MaterialPageRoute<void>(
                                builder: (_) =>
                                    const OrganisationResourcesScreen(
                                      management: true,
                                    ),
                              ),
                            ),
                            onDossiers: () => Navigator.push(
                              context,
                              MaterialPageRoute<void>(
                                builder: (_) =>
                                    const OrganisationResourcesScreen(
                                      management: false,
                                    ),
                              ),
                            ),
                            onDashboard: () => context.go('/pilotage'),
                          ),
                        Expanded(
                          child: Column(
                            children: [
                              if (!wide)
                                _MobileSectionSelector(
                                  palette: p,
                                  section: _section,
                                  onSelect: (section) =>
                                      setState(() => _section = section),
                                ),
                              Expanded(child: _content(p)),
                            ],
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _content(CopilPalette p) {
    if (_loading) {
      return Center(
        child: CircularProgressIndicator(color: p.blue, strokeWidth: 2),
      );
    }
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.cloud_off_outlined, size: 36, color: p.subtle),
              const SizedBox(height: 12),
              Text(
                _error!,
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 12.5, color: p.muted),
              ),
              const SizedBox(height: 14),
              OutlinedButton(
                onPressed: _load,
                style: OutlinedButton.styleFrom(
                  foregroundColor: p.blue,
                  side: BorderSide(color: p.blue.withValues(alpha: 0.4)),
                ),
                child: const Text('Réessayer'),
              ),
            ],
          ),
        ),
      );
    }
    final data = _data;
    if (data == null) return const SizedBox.shrink();
    return Scrollbar(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(32, 26, 32, 36),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1280),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _pageHeader(p, data),
                const SizedBox(height: 32),
                _statistics(p, data),
                const SizedBox(height: 36),
                switch (_section) {
                  _OrganisationSection.copil => _copilSection(p, data),
                  _OrganisationSection.secretariat => _secretariatSection(
                    p,
                    data,
                  ),
                  _OrganisationSection.subcommissions => _subcommissionsSection(
                    p,
                    data,
                  ),
                  _OrganisationSection.journal => _journalSection(p, data),
                },
                const SizedBox(height: 30),
                Divider(height: 1, color: p.border),
                const SizedBox(height: 16),
                Text(
                  'Structure ${data.versionStatus.toLowerCase()}',
                  style: TextStyle(fontSize: 11.5, color: p.subtle),
                ),
                const SizedBox(height: 6),
                Text(
                  'Document de référence : ${data.sourceDocument}',
                  style: TextStyle(fontSize: 11.5, color: p.subtle),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _pageHeader(CopilPalette p, CopilOrganisationData data) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Text(
                'Organisation CNE-ITP',
                style: TextStyle(
                  fontSize: 21,
                  fontWeight: FontWeight.w700,
                  color: p.title,
                ),
              ),
            ),
            if (data.canManage)
              _ActionLink(
                palette: p,
                label: "Modifier l'organisation",
                onTap: () => _configure(
                  'version',
                  id: _configurationIds['version'] as int?,
                ),
              ),
          ],
        ),
        const SizedBox(height: 6),
        Text(
          'Composition des organes, sous-commissions et nominations.',
          style: TextStyle(fontSize: 13, color: p.muted),
        ),
      ],
    );
  }

  Widget _statistics(CopilPalette p, CopilOrganisationData data) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: p.card,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: p.border),
      ),
      child: Wrap(
        spacing: 32,
        runSpacing: 18,
        children: [
          _Stat(label: 'Postes COPIL', value: '${data.copilPostCount}', p: p),
          _Stat(
            label: 'Postes du Secrétariat technique',
            value: '${data.stPostCount}',
            p: p,
          ),
          _Stat(label: 'Sous-commissions', value: '${data.scCount}', p: p),
          _Stat(
            label: 'Experts affectés dans cette édition',
            value: '${data.expertCount}',
            p: p,
          ),
          _Stat(label: 'À examiner', value: '${data.pendingCount}', p: p),
        ],
      ),
    );
  }

  Widget _copilSection(CopilPalette p, CopilOrganisationData data) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _SectionHeader(
          p: p,
          title: 'Comité de Pilotage · ${data.copilPostCount} postes',
          actions: data.canManage
              ? [
                  _ActionLink(
                    palette: p,
                    label: 'Modifier le COPIL',
                    onTap: () => _configure(
                      'organe',
                      id: _configurationIds['copil'] as int?,
                    ),
                  ),
                  _ActionLink(
                    palette: p,
                    label: 'Ajouter un poste',
                    onTap: () => _configure(
                      'poste',
                      initial: {'organe': _configurationIds['copil']},
                    ),
                  ),
                ]
              : const [],
        ),
        const SizedBox(height: 18),
        for (final group in data.copilGroups) ...[
          _GroupHeader(p: p, group: group),
          _PostsTable(
            p: p,
            posts: group.posts,
            canManage: data.canManage,
            onAction: _showInfo,
          ),
          const SizedBox(height: 24),
        ],
      ],
    );
  }

  Widget _secretariatSection(CopilPalette p, CopilOrganisationData data) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _SectionHeader(
          p: p,
          title: 'Secrétariat technique · ${data.stPostCount} postes',
          actions: data.canManage
              ? [
                  _ActionLink(
                    palette: p,
                    label: 'Modifier le Secrétariat technique',
                    onTap: () => _configure(
                      'organe',
                      id: _configurationIds['st'] as int?,
                    ),
                  ),
                  _ActionLink(
                    palette: p,
                    label: 'Ajouter un poste de coordination',
                    onTap: () => _configure(
                      'poste',
                      initial: {'organe': _configurationIds['st']},
                    ),
                  ),
                  _ActionLink(
                    palette: p,
                    label: 'Ajouter un organe ou un pôle',
                    onTap: () => _configure(
                      'organe',
                      initial: {'parent': _configurationIds['st']},
                    ),
                  ),
                ]
              : const [],
        ),
        const SizedBox(height: 18),
        for (final group in data.stGroups) ...[
          _GroupHeader(p: p, group: group),
          _PostsTable(
            p: p,
            posts: group.posts,
            canManage: data.canManage,
            onAction: _showInfo,
          ),
          const SizedBox(height: 24),
        ],
      ],
    );
  }

  Widget _subcommissionsSection(CopilPalette p, CopilOrganisationData data) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _SectionHeader(
          p: p,
          title: 'Sous-commissions · ${data.scCount}',
          actions: data.canManage
              ? [
                  _ActionLink(
                    palette: p,
                    label: 'Ajouter une sous-commission',
                    onTap: () => _configure('organe', initial: {'type': 'SC'}),
                  ),
                ]
              : const [],
        ),
        const SizedBox(height: 6),
        Text(
          'SC-SOCLE est un nom provisoire. Les dénominations et les effectifs sont renseignés à partir des décisions institutionnelles.',
          style: TextStyle(fontSize: 12, color: p.muted),
        ),
        const SizedBox(height: 18),
        for (final sc in data.subcommissions) ...[
          _SubcommissionCard(
            p: p,
            sc: sc,
            canManage: data.canManage,
            onAction: _showInfo,
          ),
          const SizedBox(height: 18),
        ],
        if (data.pendingExperts.isNotEmpty) ...[
          const SizedBox(height: 8),
          Divider(height: 1, color: p.border),
          const SizedBox(height: 16),
          Text(
            'Experts à orienter · ${data.pendingExperts.length}',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: p.title,
            ),
          ),
          const SizedBox(height: 10),
          _PendingExpertsTable(p: p, experts: data.pendingExperts),
        ],
      ],
    );
  }

  Widget _journalSection(CopilPalette p, CopilOrganisationData data) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Journal de préparation',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w700,
            color: p.title,
          ),
        ),
        const SizedBox(height: 14),
        _JournalTable(p: p, entries: data.journal),
      ],
    );
  }
}

class _OrganisationTopbar extends StatelessWidget {
  const _OrganisationTopbar({
    required this.palette,
    required this.status,
    required this.onBack,
    required this.onTheme,
  });

  final CopilPalette palette;
  final String status;
  final VoidCallback onBack;
  final VoidCallback onTheme;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    final wide = MediaQuery.sizeOf(context).width >= 1080;
    return Container(
      color: p.topbar,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            height: 6,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Expanded(child: ColoredBox(color: p.blue)),
                const Expanded(child: ColoredBox(color: Color(0xFFFFF24B))),
                Expanded(child: const ColoredBox(color: Color(0xFFDB3832))),
              ],
            ),
          ),
          Container(
            height: 72,
            padding: const EdgeInsets.symmetric(horizontal: 20),
            decoration: BoxDecoration(
              border: Border(bottom: BorderSide(color: p.border)),
            ),
            child: Row(
              children: [
                Tooltip(
                  message: 'Bureau Directoire',
                  child: InkWell(
                    onTap: onBack,
                    borderRadius: BorderRadius.circular(8),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 6,
                        vertical: 8,
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.arrow_back, size: 15, color: p.blue),
                          if (wide) ...[
                            const SizedBox(width: 6),
                            Text(
                              'Bureau Directoire',
                              style: TextStyle(
                                fontSize: 11.5,
                                fontWeight: FontWeight.w600,
                                color: p.blue,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white,
                    border: Border.all(color: const Color(0xFFD4AF37)),
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: Image.asset(
                    'assets/img/logo-cnetp.png',
                    fit: BoxFit.cover,
                  ),
                ),
                const SizedBox(width: 10),
                ClipRRect(
                  borderRadius: BorderRadius.circular(2),
                  child: SizedBox(
                    width: 4,
                    height: 34,
                    child: Column(
                      children: [
                        Expanded(flex: 3, child: ColoredBox(color: p.blue)),
                        Expanded(flex: 2, child: ColoredBox(color: p.yellow)),
                        Expanded(
                          flex: 3,
                          child: const ColoredBox(color: Color(0xFFDB3832)),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'SECRÉTARIAT TECHNIQUE',
                      style: TextStyle(
                        fontSize: 9.5,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.2,
                        color: p.subtle,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'PORTAIL CNE-ITP RDC',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w900,
                        color: const Color(0xFF1D4ED8),
                      ),
                    ),
                    const SizedBox(height: 1),
                    Text(
                      'M.I.T.P. & NUMÉRIQUE',
                      style: TextStyle(
                        fontSize: 8.5,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 0.6,
                        color: p.subtle,
                      ),
                    ),
                  ],
                ),
                const Spacer(),
                Text(status, style: TextStyle(fontSize: 12, color: p.muted)),
                const SizedBox(width: 12),
                Material(
                  color: p.card,
                  borderRadius: BorderRadius.circular(8),
                  child: InkWell(
                    onTap: onTheme,
                    borderRadius: BorderRadius.circular(8),
                    child: Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: p.border),
                      ),
                      child: Icon(
                        p.isDark
                            ? Icons.light_mode_outlined
                            : Icons.dark_mode_outlined,
                        size: 17,
                        color: p.subtle,
                      ),
                    ),
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

class _OrganisationSidebar extends StatelessWidget {
  const _OrganisationSidebar({
    required this.palette,
    required this.section,
    required this.onSelect,
    required this.onManagement,
    required this.onDossiers,
    required this.onDashboard,
  });

  final CopilPalette palette;
  final _OrganisationSection section;
  final ValueChanged<_OrganisationSection> onSelect;
  final VoidCallback onManagement;
  final VoidCallback onDossiers;
  final VoidCallback onDashboard;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    return Container(
      width: 240,
      decoration: BoxDecoration(
        color: p.sidebar,
        border: Border(right: BorderSide(color: p.border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 24, 20, 22),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Administration institutionnelle',
                  style: TextStyle(fontSize: 11, color: p.subtle),
                ),
                const SizedBox(height: 6),
                Text(
                  'CNE-ITP',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: p.title,
                  ),
                ),
              ],
            ),
          ),
          Divider(height: 1, color: p.border),
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (final item in _OrganisationSection.values)
                    _OrgNavItem(
                      p: p,
                      label: item.label,
                      active: section == item,
                      onTap: () => onSelect(item),
                    ),
                ],
              ),
            ),
          ),
          Divider(height: 1, color: p.border),
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 18, 20, 22),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _SidebarLink(
                  p: p,
                  label: 'Nominations, habilitations et circuits',
                  onTap: onManagement,
                ),
                const SizedBox(height: 14),
                _SidebarLink(
                  p: p,
                  label: 'Dossiers et supervision',
                  onTap: onDossiers,
                ),
                const SizedBox(height: 14),
                _SidebarLink(
                  p: p,
                  label: 'Tableau de bord Pilotage',
                  onTap: onDashboard,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _OrgNavItem extends StatelessWidget {
  const _OrgNavItem({
    required this.p,
    required this.label,
    required this.active,
    required this.onTap,
  });

  final CopilPalette p;
  final String label;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: active ? p.blueSoft : Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          decoration: BoxDecoration(
            border: Border(
              left: BorderSide(
                width: 3,
                color: active ? p.blue : Colors.transparent,
              ),
            ),
          ),
          child: Text(
            label,
            style: TextStyle(
              fontSize: 12.5,
              fontWeight: active ? FontWeight.w600 : FontWeight.w500,
              color: active ? p.blue : p.muted,
            ),
          ),
        ),
      ),
    );
  }
}

class _SidebarLink extends StatelessWidget {
  const _SidebarLink({
    required this.p,
    required this.label,
    required this.onTap,
  });

  final CopilPalette p;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: p.blue,
          height: 1.35,
        ),
      ),
    );
  }
}

class _MobileSectionSelector extends StatelessWidget {
  const _MobileSectionSelector({
    required this.palette,
    required this.section,
    required this.onSelect,
  });

  final CopilPalette palette;
  final _OrganisationSection section;
  final ValueChanged<_OrganisationSection> onSelect;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 10, 20, 10),
      decoration: BoxDecoration(
        color: palette.topbar,
        border: Border(bottom: BorderSide(color: palette.border)),
      ),
      child: Row(
        children: [
          Text(
            'Rubrique',
            style: TextStyle(fontSize: 11.5, color: palette.muted),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: DropdownButtonHideUnderline(
              child: DropdownButton<_OrganisationSection>(
                value: section,
                isExpanded: true,
                dropdownColor: palette.card,
                style: TextStyle(fontSize: 12, color: palette.text),
                items: [
                  for (final item in _OrganisationSection.values)
                    DropdownMenuItem(value: item, child: Text(item.label)),
                ],
                onChanged: (value) {
                  if (value != null) onSelect(value);
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value, required this.p});

  final String label;
  final String value;
  final CopilPalette p;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(fontSize: 11.5, color: p.muted)),
        const SizedBox(height: 8),
        Text(
          value,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w600,
            color: p.title,
          ),
        ),
      ],
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({
    required this.p,
    required this.title,
    required this.actions,
  });

  final CopilPalette p;
  final String title;
  final List<Widget> actions;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Text(
            title,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: p.title,
            ),
          ),
        ),
        if (actions.isNotEmpty)
          Flexible(
            child: Wrap(
              alignment: WrapAlignment.end,
              spacing: 18,
              runSpacing: 8,
              children: actions,
            ),
          ),
      ],
    );
  }
}

class _ActionLink extends StatelessWidget {
  const _ActionLink({
    required this.palette,
    required this.label,
    required this.onTap,
  });

  final CopilPalette palette;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 11.5,
            fontWeight: FontWeight.w600,
            color: palette.blue,
          ),
        ),
      ),
    );
  }
}

class _GroupHeader extends StatelessWidget {
  const _GroupHeader({required this.p, required this.group});

  final CopilPalette p;
  final OrganisationGroup group;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Text(
        '${group.label} · ${group.posts.length}',
        style: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w700,
          color: p.title,
        ),
      ),
    );
  }
}

class _PostsTable extends StatelessWidget {
  const _PostsTable({
    required this.p,
    required this.posts,
    required this.canManage,
    required this.onAction,
  });

  final CopilPalette p;
  final List<OrganisationPost> posts;
  final bool canManage;
  final ValueChanged<String> onAction;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth < 820 ? 820.0 : constraints.maxWidth;
        return SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SizedBox(
            width: width,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _tableHeader(),
                for (final post in posts) _postRow(context, post),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _tableHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: p.border)),
      ),
      child: Row(
        children: [
          _cell('Fonction', 45),
          _cell('Origine institutionnelle', 25),
          _cell('Titulaire', 13),
          _cell('Statut', 8),
          if (canManage) _cell('Gestion', 12),
        ],
      ),
    );
  }

  Widget _postRow(BuildContext context, OrganisationPost post) {
    Future<void> configure(
      String kind, {
      int? id,
      Map<String, dynamic> initial = const {},
    }) async {
      final saved = await Navigator.of(context).push<bool>(
        MaterialPageRoute(
          builder: (_) =>
              OrganisationFormScreen(kind: kind, id: id, initial: initial),
        ),
      );
      if (saved == true) onAction('reload');
    }

    final holder = post.holders.isNotEmpty
        ? post.holders.first.name
        : post.proposedHolders.isNotEmpty
        ? post.proposedHolders.first.name
        : 'Vacant';
    final proposed = post.holders.isEmpty && post.proposedHolders.isNotEmpty;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 16),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: p.border)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            flex: 45,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  post.title,
                  style: TextStyle(
                    fontSize: 12.5,
                    fontWeight: FontWeight.w600,
                    color: p.text,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  post.code,
                  style: TextStyle(fontSize: 12, color: p.subtle),
                ),
              ],
            ),
          ),
          Expanded(
            flex: 25,
            child: Text(
              post.origin,
              style: TextStyle(fontSize: 12.8, color: p.text),
            ),
          ),
          Expanded(
            flex: 13,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  holder,
                  style: TextStyle(
                    fontSize: 11.5,
                    color: holder == 'Vacant' ? p.subtle : p.text,
                  ),
                ),
                if (proposed)
                  Padding(
                    padding: const EdgeInsets.only(top: 3),
                    child: Text(
                      "Proposition à vérifier",
                      style: TextStyle(fontSize: 9.5, color: p.warning),
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            flex: 8,
            child: Text(
              post.status,
              style: TextStyle(fontSize: 11.5, color: p.text),
            ),
          ),
          if (canManage)
            Expanded(
              flex: 12,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _ActionLink(
                    palette: p,
                    label: 'Modifier',
                    onTap: () => configure('poste', id: post.id),
                  ),
                  const SizedBox(height: 5),
                  _ActionLink(
                    palette: p,
                    label: 'Nommer',
                    onTap: () =>
                        configure('mandat', initial: {'poste': post.id}),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _cell(String label, int flex) {
    return Expanded(
      flex: flex,
      child: Text(
        label,
        style: TextStyle(
          fontSize: 10.5,
          fontWeight: FontWeight.w600,
          color: p.subtle,
        ),
      ),
    );
  }
}

class _SubcommissionCard extends StatelessWidget {
  const _SubcommissionCard({
    required this.p,
    required this.sc,
    required this.canManage,
    required this.onAction,
  });

  final CopilPalette p;
  final OrganisationSubcommission sc;
  final bool canManage;
  final ValueChanged<String> onAction;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: p.card,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: p.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${sc.code} - ${sc.name}',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: p.title,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      sc.status,
                      style: TextStyle(fontSize: 11, color: p.subtle),
                    ),
                  ],
                ),
              ),
              if (canManage)
                Wrap(
                  spacing: 14,
                  children: [
                    _ActionLink(
                      palette: p,
                      label: 'Modifier',
                      onTap: () async {
                        final saved = await Navigator.push<bool>(
                          context,
                          MaterialPageRoute(
                            builder: (_) => OrganisationFormScreen(
                              kind: 'organe',
                              id: sc.id,
                            ),
                          ),
                        );
                        if (saved == true) onAction('reload');
                      },
                    ),
                    _ActionLink(
                      palette: p,
                      label: 'Ajouter un poste',
                      onTap: () async {
                        final saved = await Navigator.push<bool>(
                          context,
                          MaterialPageRoute(
                            builder: (_) => OrganisationFormScreen(
                              kind: 'poste',
                              initial: {'organe': sc.id},
                            ),
                          ),
                        );
                        if (saved == true) onAction('reload');
                      },
                    ),
                  ],
                ),
            ],
          ),
          if (sc.domain.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(sc.domain, style: TextStyle(fontSize: 11.5, color: p.muted)),
          ],
          const SizedBox(height: 14),
          Text(
            'Experts affectés dans cette édition · ${sc.experts.length}',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: p.text,
            ),
          ),
          const SizedBox(height: 8),
          if (sc.experts.isEmpty)
            Text(
              'Aucune affectation dans cette édition.',
              style: TextStyle(fontSize: 11, color: p.subtle),
            )
          else
            for (final expert in sc.experts)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        expert.name,
                        style: TextStyle(fontSize: 11.5, color: p.text),
                      ),
                    ),
                    SizedBox(
                      width: 90,
                      child: Text(
                        expert.structure,
                        style: TextStyle(fontSize: 11, color: p.muted),
                      ),
                    ),
                    Text(
                      'Affecté',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: p.success,
                      ),
                    ),
                  ],
                ),
              ),
          const SizedBox(height: 14),
          _PostsTable(
            p: p,
            posts: sc.posts,
            canManage: canManage,
            onAction: onAction,
          ),
          if (sc.groups.isNotEmpty) ...[
            const SizedBox(height: 14),
            Text(
              'Groupes de travail',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: p.text,
              ),
            ),
            const SizedBox(height: 8),
            for (final group in sc.groups)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        '${group.code} - ${group.name}',
                        style: TextStyle(fontSize: 11.5, color: p.text),
                      ),
                    ),
                    Text(
                      group.activity,
                      style: TextStyle(fontSize: 11, color: p.muted),
                    ),
                  ],
                ),
              ),
          ],
        ],
      ),
    );
  }
}

class _PendingExpertsTable extends StatelessWidget {
  const _PendingExpertsTable({required this.p, required this.experts});

  final CopilPalette p;
  final List<PendingExpert> experts;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: p.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: p.border),
      ),
      child: Column(
        children: [
          for (final expert in experts)
            Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      expert.name,
                      style: TextStyle(fontSize: 11.5, color: p.text),
                    ),
                  ),
                  Expanded(
                    child: Text(
                      expert.structure,
                      style: TextStyle(fontSize: 11, color: p.muted),
                    ),
                  ),
                  Expanded(
                    flex: 2,
                    child: Text(
                      expert.reason,
                      style: TextStyle(fontSize: 11, color: p.subtle),
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

class _JournalTable extends StatelessWidget {
  const _JournalTable({required this.p, required this.entries});

  final CopilPalette p;
  final List<JournalEntry> entries;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: p.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: p.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              border: Border(bottom: BorderSide(color: p.border)),
            ),
            child: Row(
              children: [
                _journalCell('Date', 2),
                _journalCell('Auteur', 2),
                _journalCell('Opération', 2),
                _journalCell('Motif', 3),
              ],
            ),
          ),
          if (entries.isEmpty)
            Padding(
              padding: const EdgeInsets.all(20),
              child: Text(
                'Aucune opération enregistrée.',
                style: TextStyle(fontSize: 11.5, color: p.subtle),
              ),
            )
          else
            for (final entry in entries)
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 12,
                ),
                decoration: BoxDecoration(
                  border: Border(bottom: BorderSide(color: p.border)),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _journalValue(entry.createdAt, 2),
                    _journalValue(entry.actor, 2),
                    _journalValue(entry.operation, 2),
                    _journalValue(entry.reason, 3),
                  ],
                ),
              ),
        ],
      ),
    );
  }

  Widget _journalCell(String label, int flex) {
    return Expanded(
      flex: flex,
      child: Text(
        label,
        style: TextStyle(
          fontSize: 10.5,
          fontWeight: FontWeight.w600,
          color: p.subtle,
        ),
      ),
    );
  }

  Widget _journalValue(String value, int flex) {
    return Expanded(
      flex: flex,
      child: Text(
        value,
        style: TextStyle(fontSize: 11, color: p.muted, height: 1.4),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_client.dart';
import '../../../core/auth/auth_controller.dart';
import '../theme/copil_theme.dart';
import 'widgets/console_content.dart';
import 'widgets/copil_panels.dart';
import 'widgets/copil_sidebar.dart';
import 'widgets/copil_topbar.dart';
import 'widgets/copil_workflow_panel.dart';
import 'widgets/copil_instruction_drawer.dart';
import '../activity/copil_activity_screen.dart';
import 'copil_tools_screen.dart';

class CopilConsoleScreen extends ConsumerStatefulWidget {
  const CopilConsoleScreen({super.key});

  @override
  ConsumerState<CopilConsoleScreen> createState() => _CopilConsoleScreenState();
}

class _CopilConsoleScreenState extends ConsumerState<CopilConsoleScreen> {
  String _activePanel = 'panel-sc';
  bool _sidebarVisible = true;
  final _scaffoldKey = GlobalKey<ScaffoldState>();
  bool _loading = true;
  String? _error;
  Map<String, dynamic> _permissions = {};
  Map<String, dynamic> _panels = {};
  bool _platformLocked = false;
  String _subRole = '';

  List<ScGroup> _scs = [];
  Map<String, int> _counts = const {};
  Map<String, int> _pending = const {};
  CopilProfile _profile = const CopilProfile();
  int _memberCount = 0;

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
      final resp = await ApiClient.dio.get(
        '/api/v1/mobile/pilotage/dashboard/',
      );
      final data = resp.data as Map<String, dynamic>;
      final counts = data['counts'] as Map<String, dynamic>? ?? {};
      final pending = data['pending'] as Map<String, dynamic>? ?? {};
      final profile = data['profile'] as Map<String, dynamic>? ?? {};
      final scs = (data['scs'] as List? ?? [])
          .map(
            (e) => ScGroup(
              id: (e['id'] as num?)?.toInt(),
              code: (e as Map)['code'] as String? ?? '',
              title: e['name'] as String? ?? '',
              memberCount: (e['member_count'] as num?)?.toInt() ?? 0,
              experts: (e['experts'] as List? ?? [])
                  .map((x) => x.toString())
                  .toList(),
            ),
          )
          .toList();
      if (!mounted) return;
      setState(() {
        _counts = counts.map((k, v) => MapEntry(k, (v as num).toInt()));
        _pending = pending.map((k, v) => MapEntry(k, (v as num).toInt()));
        _scs = scs;
        _permissions = Map<String, dynamic>.from(
          data['permissions'] as Map? ?? {},
        );
        _panels = Map<String, dynamic>.from(data['panels'] as Map? ?? {});
        _platformLocked = data['platform_locked'] == true;
        _subRole = data['sub_role'] as String? ?? '';
        _memberCount = (data['member_count'] as num?)?.toInt() ?? 0;
        _profile = CopilProfile(
          fullName: profile['full_name'] as String? ?? '',
          role: profile['role'] as String? ?? '',
          structure: profile['structure'] as String? ?? '',
          status: profile['status'] as String? ?? 'Actif',
          appointmentDate: _date(profile['appointment_date']),
        );
      });
    } catch (_) {
      if (!mounted) return;
      final session = ref.read(authControllerProvider).session;
      setState(() {
        _error =
            'Impossible de charger le tableau de bord. Vérifiez votre connexion puis réessayez.';
        _profile = CopilProfile(
          fullName: session?.fullName ?? 'Membre du COPIL',
          role: 'Comité de Pilotage',
          structure: session?.email ?? '',
          status: 'Actif',
        );
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _date(dynamic value) {
    final date = DateTime.tryParse('$value');
    if (date == null) return '';
    return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
  }

  List<Map<String, dynamic>> _items(String key) => (_panels[key] as List? ?? [])
      .map((e) => Map<String, dynamic>.from(e as Map))
      .toList();

  void _openActivity([ScGroup? group]) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => CopilActivityScreen(scId: group?.id),
      ),
    );
  }

  Future<void> _openTool(String tool) async {
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => CopilToolsScreen(
          tool: tool,
          role: _profile.role,
          structure: _profile.structure,
          onAccount: _showAccount,
        ),
      ),
    );
    if (mounted && tool == 'profile') await _load();
  }

  Future<void> _freeze() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(
          _platformLocked
              ? 'Déverrouiller la plateforme'
              : 'Verrouiller la plateforme',
        ),
        content: Text(
          'Confirmez-vous vouloir ${_platformLocked ? 'déverrouiller' : 'verrouiller'} la plateforme ?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Confirmer'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    try {
      await ApiClient.dio.post(
        '/api/v1/mobile/pilotage/command/',
        data: {'kind': 'freeze'},
      );
      await _load();
    } on DioException catch (error) {
      if (mounted) {
        _showInfo(
          '${error.response?.data is Map ? error.response?.data['error'] ?? error.response?.data['detail'] : 'Connexion impossible.'}',
        );
      }
    }
  }

  void _showInfo(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
    );
  }

  Future<void> _showAccount() async {
    final session = ref.read(authControllerProvider).session;
    final p = ref.read(copilDarkProvider)
        ? CopilPalette.dark
        : CopilPalette.light;
    await showModalBottomSheet<void>(
      context: context,
      backgroundColor: p.card,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  CircleAvatar(
                    radius: 24,
                    backgroundColor: p.blueSoft,
                    child: Text(
                      _initials(_profile.fullName),
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        color: p.blue,
                      ),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _profile.fullName.isEmpty
                              ? session?.fullName ?? 'Membre du COPIL'
                              : _profile.fullName,
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                            color: p.title,
                          ),
                        ),
                        const SizedBox(height: 3),
                        Text(
                          _profile.role,
                          style: TextStyle(fontSize: 12, color: p.muted),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 18),
              _ProfileLine(
                icon: Icons.badge_outlined,
                label: 'Structure',
                value: _profile.structure.isEmpty
                    ? 'Non renseignée'
                    : _profile.structure,
                palette: p,
              ),
              const SizedBox(height: 10),
              _ProfileLine(
                icon: Icons.mail_outline,
                label: 'Email',
                value: session?.email ?? '',
                palette: p,
              ),
              const SizedBox(height: 16),
              OutlinedButton(onPressed: () { Navigator.pop(context); _openTool('profile'); }, child: const Text('Modifier mes informations')),
              FilledButton.icon(
                onPressed: () {
                  Navigator.of(context).pop();
                  ref.read(authControllerProvider.notifier).logout();
                },
                style: FilledButton.styleFrom(backgroundColor: p.blueDeep),
                icon: const Icon(Icons.logout, size: 18),
                label: const Text('Se déconnecter'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _initials(String name) {
    final parts = name
        .trim()
        .split(RegExp(r'\s+'))
        .where((part) => part.isNotEmpty)
        .toList();
    if (parts.isEmpty) return 'CP';
    if (parts.length == 1) return parts.first.substring(0, 1).toUpperCase();
    return '${parts.first.substring(0, 1)}${parts.last.substring(0, 1)}'
        .toUpperCase();
  }

  Widget _panelContent(String panel, CopilPalette p) {
    switch (panel) {
      case 'panel-sc':
        return ConsoleContent(
          scs: _scs,
          counts: _counts,
          profile: _profile,
          onInstruction: () => showCopilInstruction(context),
          onSubcommission: _openActivity,
          onManageExperts: _permissions['can_manage_access'] == true
              ? () => setState(() => _activePanel = 'panel-adhesions')
              : null,
          onFreeze: _subRole == 'president' ? _freeze : null,
          platformLocked: _platformLocked,
        );
      case 'panel-cadrage':
        return _PanelSection(
          header: PanelHeader(
            icon: Icons.explore_outlined,
            title: 'Cadrage Directoire',
            color: p.blue,
          ),
          child: CopilWorkflowPanel(
            key: const ValueKey('cadrage'),
            kind: 'cadrage',
            items: _items('cadrages'),
            onChanged: _load,
          ),
        );
      case 'panel-reception':
        return _PanelSection(
          header: PanelHeader(
            icon: Icons.verified_outlined,
            title: 'Réception technique',
            color: p.success,
            count: _pending['reception'],
          ),
          child: CopilWorkflowPanel(
            key: const ValueKey('reception'),
            kind: 'reception',
            items: _items('reception'),
            onChanged: _load,
          ),
        );
      case 'panel-adhesions':
        return _PanelSection(
          header: PanelHeader(
            icon: Icons.person_add_alt_1_outlined,
            title: "Demandes d'adhésion",
            color: p.success,
            count: _pending['adhesions'],
          ),
          child: CopilWorkflowPanel(
            key: const ValueKey('adhesion'),
            kind: 'adhesion',
            items: _items('adhesions'),
            onChanged: _load,
          ),
        );
      case 'panel-requests':
        return _PanelSection(
          header: PanelHeader(
            icon: Icons.inbox_outlined,
            title: 'Demandes de dérogation',
            color: p.blue,
            count: _pending['derogations'],
          ),
          child: CopilWorkflowPanel(
            key: const ValueKey('derogation'),
            kind: 'derogation',
            items: _items('derogations'),
            onChanged: _load,
          ),
        );
      default:
        return _PanelSection(
          header: PanelHeader(
            icon: Icons.dashboard_outlined,
            title: panel,
            color: p.blue,
          ),
          child: PanelEmpty(
            icon: Icons.construction_outlined,
            color: p.blue,
            title: 'Panneau en cours de construction',
            subtitle: 'Ce module sera disponible prochainement.',
          ),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final dark = ref.watch(copilDarkProvider);
    final p = dark ? CopilPalette.dark : CopilPalette.light;
    final desktop = MediaQuery.sizeOf(context).width >= 1024;
    Widget sidebar() => CopilSidebar(
      activePanel: _activePanel,
      memberCount: _memberCount,
      permissions: _permissions,
      pendingAdhesions: _pending['adhesions'] ?? 0,
      onClose: () {
        if (desktop) {
          setState(() => _sidebarVisible = false);
        } else {
          Navigator.pop(context);
        }
      },
      onSelect: (panel) {
        if (!desktop) Navigator.pop(context);
        if (panel == 'panel-activite') {
          _openActivity();
        } else {
          setState(() => _activePanel = panel);
        }
      },
      onOrganisation: () {
        if (!desktop) Navigator.pop(context);
        context.push('/pilotage/organisation');
      },
        onProfile: () {
        if (!desktop) Navigator.pop(context);
          _openTool('profile');
        },
    );
    return CopilTheme(
      palette: p,
      child: Scaffold(
        key: _scaffoldKey,
        drawer: desktop ? null : Drawer(width: 288, child: sidebar()),
        backgroundColor: p.bg,
        body: SafeArea(
          child: Column(
            children: [
              CopilTopbar(
                memberCount: _memberCount,
                onToggleSidebar: () => desktop
                    ? setState(() => _sidebarVisible = !_sidebarVisible)
                    : _scaffoldKey.currentState?.openDrawer(),
                onBack: () => context.go('/expert'),
                onDirectoire: _permissions['can_trigger_steps'] == true
                    ? () => context.push('/pilotage/directoire')
                    : null,
                onInstructions: () => _openTool('instructions'),
                onAi: () => _openTool('ai'),
                onThemeToggle: () =>
                    ref.read(copilDarkProvider.notifier).state = !dark,
              ),
              Expanded(
                child: Row(
                  children: [
                    if (desktop && _sidebarVisible) sidebar(),
                    Expanded(
                      child: ColoredBox(
                        color: p.bg,
                        child: Stack(
                          children: [
                            Positioned.fill(
                              child: Scrollbar(
                                child: _loading
                                    ? const Center(
                                        child: CircularProgressIndicator(),
                                      )
                                    : _error != null
                                    ? Center(
                                        child: Column(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Padding(
                                              padding: const EdgeInsets.all(24),
                                              child: Text(
                                                _error!,
                                                textAlign: TextAlign.center,
                                                style: TextStyle(
                                                  color: p.muted,
                                                ),
                                              ),
                                            ),
                                            OutlinedButton(
                                              onPressed: _load,
                                              child: const Text('Réessayer'),
                                            ),
                                          ],
                                        ),
                                      )
                                    : SingleChildScrollView(
                                        child: _panelContent(_activePanel, p),
                                      ),
                              ),
                            ),
                            Positioned(
                              right: 24,
                              bottom: 24,
                              child: _AiFab(
                                palette: p,
                                onTap: () => _openTool('ai'),
                              ),
                            ),
                          ],
                        ),
                      ),
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

class _ProfileLine extends StatelessWidget {
  const _ProfileLine({
    required this.icon,
    required this.label,
    required this.value,
    required this.palette,
  });

  final IconData icon;
  final String label;
  final String value;
  final CopilPalette palette;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 16, color: palette.subtle),
        const SizedBox(width: 10),
        SizedBox(
          width: 72,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: palette.subtle,
            ),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(fontSize: 12, color: palette.text),
          ),
        ),
      ],
    );
  }
}

class _PanelSection extends StatelessWidget {
  const _PanelSection({required this.header, required this.child});
  final Widget header;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(28, 24, 28, 40),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [header, const SizedBox(height: 16), child],
      ),
    );
  }
}

class _AiFab extends StatelessWidget {
  const _AiFab({required this.palette, required this.onTap});

  final CopilPalette palette;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: palette.blueDeep,
      shape: const CircleBorder(),
      elevation: 6,
      child: InkWell(
        onTap: onTap,
        customBorder: const CircleBorder(),
        child: const SizedBox(
          width: 52,
          height: 52,
          child: Icon(Icons.auto_awesome, color: Colors.white, size: 24),
        ),
      ),
    );
  }
}

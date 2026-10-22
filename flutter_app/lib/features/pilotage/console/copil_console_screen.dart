import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../../../core/auth/auth_controller.dart';
import '../../../theme/app_colors.dart';
import 'widgets/console_content.dart';
import 'widgets/copil_panels.dart';
import 'widgets/copil_sidebar.dart';
import 'widgets/copil_topbar.dart';

class CopilConsoleScreen extends ConsumerStatefulWidget {
  const CopilConsoleScreen({super.key});

  @override
  ConsumerState<CopilConsoleScreen> createState() => _CopilConsoleScreenState();
}

class _CopilConsoleScreenState extends ConsumerState<CopilConsoleScreen> {
  String _activePanel = 'panel-sc';
  bool _sidebarVisible = true;

  List<ScGroup> _scs = [];
  Map<String, int> _counts = const {};
  Map<String, int> _pending = const {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final resp = await ApiClient.dio.get('/api/v1/mobile/pilotage/dashboard/');
      final data = resp.data as Map<String, dynamic>;
      final counts = (data['counts'] as Map<String, dynamic>? ?? {});
      final pending = (data['pending'] as Map<String, dynamic>? ?? {});
      final scs = (data['scs'] as List? ?? [])
          .map((e) => ScGroup(
                code: (e as Map)['code'] as String? ?? '',
                title: e['name'] as String? ?? '',
                memberCount: (e['member_count'] as num?)?.toInt() ?? 0,
                experts: (e['experts'] as List? ?? []).map((x) => x.toString()).toList(),
              ))
          .toList();
      if (!mounted) return;
      setState(() {
        _counts = counts.map((k, v) => MapEntry(k, (v as num).toInt()));
        _pending = pending.map((k, v) => MapEntry(k, (v as num).toInt()));
        _scs = scs;
      });
    } catch (_) {
      // fallback : données de démo
    }
  }

  Widget _panelContent(String panel) {
    switch (panel) {
      case 'panel-sc':
        return ConsoleContent(scs: _scs, counts: _counts);
      case 'panel-cadrage':
        return const _PanelSection(
          header: PanelHeader(
            icon: Icons.explore_outlined,
            title: 'Cadrage Directoire',
            color: AppColors.rdcBlue,
          ),
          child: CadragePanel(),
        );
      case 'panel-reception':
        return _PanelSection(
          header: PanelHeader(
            icon: Icons.verified_outlined,
            title: 'Réception technique',
            color: AppColors.success,
            count: _pending['reception'],
          ),
          child: const ReceptionPanel(),
        );
      case 'panel-adhesions':
        return _PanelSection(
          header: PanelHeader(
            icon: Icons.person_add_alt_1_outlined,
            title: "Demandes d'adhésion",
            color: AppColors.success,
            count: _pending['adhesions'],
          ),
          child: const AdhesionsPanel(),
        );
      case 'panel-requests':
        return _PanelSection(
          header: PanelHeader(
            icon: Icons.inbox_outlined,
            title: 'Demandes de dérogation',
            color: AppColors.rdcBlue,
            count: _pending['derogations'],
          ),
          child: const DerogationPanel(),
        );
      default:
        return _PanelSection(
          header: PanelHeader(
            icon: Icons.dashboard_outlined,
            title: panel,
            color: AppColors.rdcBlue,
          ),
          child: const PanelEmpty(
            icon: Icons.construction_outlined,
            color: AppColors.rdcBlue,
            title: 'Panneau en cours de construction',
            subtitle: 'Ce module sera disponible prochainement.',
          ),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.page,
      body: SafeArea(
        child: Column(
          children: [
            CopilTopbar(
              memberCount: 0,
              onToggleSidebar: () => setState(() => _sidebarVisible = !_sidebarVisible),
              onLogout: () => ref.read(authControllerProvider.notifier).logout(),
            ),
            Expanded(
              child: Row(
                children: [
                  if (_sidebarVisible)
                    CopilSidebar(
                      activePanel: _activePanel,
                      onSelect: (panel) => setState(() => _activePanel = panel),
                      pendingAdhesions: _pending['adhesions'] ?? 0,
                    ),
                  Expanded(
                    child: ColoredBox(
                      color: Colors.white,
                      child: Stack(
                        children: [
                          Positioned.fill(
                            child: Scrollbar(
                              child: SingleChildScrollView(
                                child: _panelContent(_activePanel),
                              ),
                            ),
                          ),
                          Positioned(
                            right: 24,
                            bottom: 24,
                            child: _AiFab(),
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
        children: [
          header,
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }
}

class _AiFab extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 52,
      height: 52,
      decoration: const BoxDecoration(
        color: AppColors.rdcBlue,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(color: Color(0x330095C9), blurRadius: 16, offset: Offset(0, 6)),
        ],
      ),
      child: const Icon(Icons.auto_awesome, color: Colors.white, size: 24),
    );
  }
}

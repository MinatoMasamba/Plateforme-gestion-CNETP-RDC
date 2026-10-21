import 'package:flutter/material.dart';
import '../../../theme/app_colors.dart';
import 'widgets/console_content.dart';
import 'widgets/copil_panels.dart';
import 'widgets/copil_sidebar.dart';
import 'widgets/copil_topbar.dart';

class CopilConsoleScreen extends StatefulWidget {
  const CopilConsoleScreen({super.key});

  @override
  State<CopilConsoleScreen> createState() => _CopilConsoleScreenState();
}

class _CopilConsoleScreenState extends State<CopilConsoleScreen> {
  String _activePanel = 'panel-sc';
  bool _sidebarVisible = true;

  Widget _panelContent(String panel) {
    switch (panel) {
      case 'panel-sc':
        return const ConsoleContent();
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
        return const _PanelSection(
          header: PanelHeader(
            icon: Icons.verified_outlined,
            title: 'Réception technique',
            color: AppColors.success,
          ),
          child: ReceptionPanel(),
        );
      case 'panel-adhesions':
        return const _PanelSection(
          header: PanelHeader(
            icon: Icons.person_add_alt_1_outlined,
            title: "Demandes d'adhésion",
            color: AppColors.success,
            count: 1,
          ),
          child: AdhesionsPanel(
            items: [
              AdhesionItem(
                name: 'MASAMBA .',
                email: 'eded@gmail.com',
                structure: 'DS',
                date: '—',
              ),
            ],
          ),
        );
      case 'panel-requests':
        return const _PanelSection(
          header: PanelHeader(
            icon: Icons.inbox_outlined,
            title: 'Demandes de dérogation',
            color: AppColors.rdcBlue,
          ),
          child: DerogationPanel(),
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
            ),
            Expanded(
              child: Row(
                children: [
                  if (_sidebarVisible)
                    CopilSidebar(
                      activePanel: _activePanel,
                      onSelect: (panel) => setState(() => _activePanel = panel),
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

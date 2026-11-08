import 'package:flutter/material.dart';

import 'ged_counts.dart';
import 'ctc_menu_icon.dart';
import '../../../theme/app_colors.dart';

class CtcNavItem {
  const CtcNavItem(
    this.view,
    this.label,
    this.icon, {
    this.badgeKey,
    this.dangerBadge = false,
  });
  final String view;
  final String label;
  final IconData icon;
  final String? badgeKey;
  final bool dangerBadge;
}

class CtcNavSection {
  const CtcNavSection(this.title, this.items);
  final String title;
  final List<CtcNavItem> items;
}

/// Postes dont l'espace ST rend une barre « rail » (miroir
/// `sidebar_module.html` : `data-sidebar-rail` pour ST-V3-10 et ST-V3-11).
bool ctcSpaceRailEnabled(String? stPostCode) =>
    stPostCode == 'ST-V3-10' || stPostCode == 'ST-V3-11';

/// Navigation dédiée des postes ST 10 / 11 — miroir exact des boutons
/// `data-sidebar-view` du modèle `ctc/app/components/sidebar_module.html`.
List<CtcNavSection> ctcSpaceSections(String stPostCode) {
  IconData spaceIcon(String view, String lucide) => ctcIconFor(view, lucide);
  final pilotage = CtcNavSection('Pilotage', [
    CtcNavItem(
      'espace_p2',
      'Tableau de bord',
      spaceIcon('espace_p2', 'layout-dashboard'),
    ),
    CtcNavItem(
      'ged_activity',
      stPostCode == 'ST-V3-10' ? 'Activité du pôle' : 'Mon activité',
      spaceIcon('ged_activity', 'history'),
    ),
  ]);
  final traitement = CtcNavSection('Traitement', [
    CtcNavItem(
      'indexation',
      'Dossiers à indexer',
      spaceIcon('indexation', 'files'),
      badgeKey: 'ready',
    ),
    CtcNavItem(
      'ged_versions_todo',
      'Versions à traiter',
      spaceIcon('ged_versions_todo', 'layers'),
      badgeKey: 'versions',
    ),
    CtcNavItem(
      'ged_anomalies',
      'Anomalies',
      spaceIcon('ged_anomalies', 'file-warning'),
      badgeKey: 'anomalies',
      dangerBadge: true,
    ),
  ]);
  final referentiel = CtcNavSection('Référentiel GED', [
    CtcNavItem('ged', 'Documents GED', spaceIcon('ged', 'library')),
    CtcNavItem(
      'codification',
      'Codification',
      spaceIcon('codification', 'scan-line'),
    ),
    CtcNavItem(
      'versions',
      'Historique des versions',
      spaceIcon('versions', 'list-tree'),
    ),
  ]);
  final sorties = CtcNavSection('Sorties', [
    CtcNavItem(
      'rapports',
      'Rapports et exports',
      spaceIcon('rapports', 'file-chart-column'),
    ),
  ]);
  final divers = CtcNavSection('Divers', [
    CtcNavItem(
      'aide',
      "Aide et mode d'emploi",
      spaceIcon('aide', 'circle-help'),
    ),
  ]);
  return [pilotage, traitement, referentiel, sorties, divers];
}

/// Sections de navigation CTC (coordonnateur) — miroir de `sidebar_nav_config`
/// dans `web/ctc_views.py:332`.
const List<CtcNavSection> ctcNavSections = [
  CtcNavSection('Travail', [
    CtcNavItem('dashboard', 'Tableau de bord', Icons.dashboard_outlined),
    CtcNavItem('dossiers', 'Dossiers normatifs', Icons.folder_outlined),
    CtcNavItem('assignations', 'Mes Assignations', Icons.check_circle_outline),
    CtcNavItem('ctc_requests', 'Demandes à Traiter', Icons.send_outlined),
    CtcNavItem(
      'assistant_executif',
      'Assistant Exécutif',
      Icons.inbox_outlined,
    ),
    CtcNavItem(
      'financial',
      'Budget & Comptabilité',
      Icons.account_balance_wallet_outlined,
    ),
  ]),
  CtcNavSection('Supervision', [
    CtcNavItem('statistiques', 'Suivi statistique', Icons.insights_outlined),
    CtcNavItem('homologations', 'Homologations', Icons.verified_user_outlined),
  ]),
  CtcNavSection('Outils', [
    CtcNavItem('instructions', 'Instruction', Icons.assignment_outlined),
    CtcNavItem('reunions', 'Réunions', Icons.calendar_month_outlined),
    CtcNavItem('drive', 'Espace Drive', Icons.cloud_outlined),
  ]),
  CtcNavSection('Système', [
    CtcNavItem('archives', 'Archives', Icons.history),
    CtcNavItem('parametres', 'Paramètres', Icons.settings_outlined),
  ]),
];

/// Icônes par icône lucide déclarée par le serveur (`menu.icon`), miroir de
/// `apps/governance/st_spaces.py` — la sidebar ST suit le serveur, pas l'app.
const Map<String, IconData> ctcLucideIcons = {
  'layout-dashboard': Icons.dashboard_outlined,
  'dossiers': Icons.folder_outlined,
  'folders': Icons.folder_outlined,
  'send': Icons.send_outlined,
  'layers': Icons.layers_outlined,
  'file-chart-column': Icons.insert_chart_outlined,
  'circle-help': Icons.help_outline,
  'assignations': Icons.check_circle_outline,
  'files': Icons.content_copy_outlined,
  'copy': Icons.content_copy_outlined,
  'library': Icons.local_library_outlined,
  'book-copy': Icons.copy_all_outlined,
  'indexation': Icons.copy_all_outlined,
  'scan-line': Icons.qr_code_scanner_outlined,
  'codification': Icons.qr_code_2_outlined,
  'history': Icons.history_outlined,
  'versions': Icons.history_outlined,
  'file-warning': Icons.report_problem_outlined,
  'ged_anomalies': Icons.report_problem_outlined,
  'chart-no-axes-combined': Icons.query_stats_outlined,
  'ged_activity': Icons.query_stats_outlined,
  'calendar-check': Icons.event_available_outlined,
  'calendar-days': Icons.calendar_month_outlined,
  'reunions': Icons.calendar_month_outlined,
  'alarm-clock': Icons.alarm_outlined,
  'delays': Icons.alarm_outlined,
  'clipboard-check': Icons.checklist_outlined,
  'combine': Icons.join_full_outlined,
  'consolidation': Icons.join_full_outlined,
  'ptn': Icons.account_tree_outlined,
  'list-tree': Icons.account_tree_outlined,
  'network': Icons.hub_outlined,
  'matrice_st': Icons.hub_outlined,
  'coordination': Icons.dashboard_outlined,
  'espace_p1': Icons.dashboard_outlined,
  'espace_p2': Icons.dashboard_outlined,
  'espace_p3': Icons.dashboard_outlined,
  'espace_p4': Icons.dashboard_outlined,
  'deliverables': Icons.inventory_2_outlined,
  'package-check': Icons.inventory_2_outlined,
  'planning': Icons.event_note_outlined,
  'exams': Icons.rule_outlined,
  'scale': Icons.balance_outlined,
  'legal': Icons.gavel_outlined,
  'receipt': Icons.receipt_long_outlined,
  'contributions': Icons.receipt_long_outlined,
  'statements': Icons.fact_check_outlined,
  'user-cog': Icons.admin_panel_settings_outlined,
  'accounts': Icons.admin_panel_settings_outlined,
  'database-backup': Icons.backup_outlined,
  'backups': Icons.backup_outlined,
  'graduation-cap': Icons.school_outlined,
  'training': Icons.school_outlined,
  'megaphone': Icons.campaign_outlined,
  'communication': Icons.campaign_outlined,
  'messages-square': Icons.forum_outlined,
  'usagers': Icons.forum_outlined,
  'banknote': Icons.account_balance_wallet_outlined,
  'financial': Icons.account_balance_wallet_outlined,
  'file-search': Icons.search_outlined,
  'experts': Icons.people_outline,
  'tracabilite': Icons.receipt_long_outlined,
  'homologations': Icons.verified_user_outlined,
  'instructions': Icons.assignment_outlined,
  'drive': Icons.cloud_outlined,
  'archives': Icons.history,
  'parametres': Icons.settings_outlined,
  'statistiques': Icons.insights_outlined,
  'assistant_executif': Icons.inbox_outlined,
  'ctc_requests': Icons.send_outlined,
  'wrench': Icons.build_outlined,
  'travaux': Icons.construction_outlined,
};

/// Icônes de repli par clé de vue quand le menu serveur ne porte pas d'icône.
const Map<String, IconData> ctcViewIcons = {
  'dashboard': Icons.dashboard_outlined,
  'dossiers': Icons.folder_outlined,
  'assignations': Icons.check_circle_outline,
  'ctc_requests': Icons.send_outlined,
  'financial': Icons.account_balance_wallet_outlined,
  'statistiques': Icons.insights_outlined,
  'experts': Icons.people_outline,
  'tracabilite': Icons.receipt_long_outlined,
  'indexation': Icons.copy_all_outlined,
  'ged': Icons.local_library_outlined,
  'ptn': Icons.account_tree_outlined,
  'consolidation': Icons.join_full_outlined,
  'planning': Icons.event_note_outlined,
  'deliverables': Icons.inventory_2_outlined,
  'delays': Icons.alarm_outlined,
  'exams': Icons.rule_outlined,
  'legal': Icons.gavel_outlined,
  'contributions': Icons.receipt_long_outlined,
  'statements': Icons.fact_check_outlined,
  'accounts': Icons.admin_panel_settings_outlined,
  'backups': Icons.backup_outlined,
  'training': Icons.school_outlined,
  'communication': Icons.campaign_outlined,
  'usagers': Icons.forum_outlined,
  'homologations': Icons.verified_user_outlined,
  'instructions': Icons.assignment_outlined,
  'reunions': Icons.calendar_month_outlined,
  'drive': Icons.cloud_outlined,
  'archives': Icons.history,
  'matrice_st': Icons.hub_outlined,
  'parametres': Icons.settings_outlined,
};

IconData ctcIconFor(String view, String? serverIcon) {
  for (final key in [?serverIcon, view]) {
    final icon = ctcLucideIcons[key] ?? ctcViewIcons[key];
    if (icon != null) return icon;
  }
  return Icons.circle_outlined;
}

List<CtcNavSection> ctcSectionsFromConfig(Map<String, dynamic> config) {
  const groups = [
    ('principal', 'Travail'),
    ('supervision', 'Supervision'),
    ('outils', 'Outils'),
    ('system', 'Système'),
  ];
  return [
    for (final group in groups)
      if (config[group.$1] is List)
        CtcNavSection(group.$2, [
          for (final raw in config[group.$1] as List)
            if (raw is Map && raw['view'] is String && raw['label'] is String)
              CtcNavItem(
                raw['view'] as String,
                (raw['label'] as String).trim().isEmpty
                    ? raw['view']
                    : raw['label'] as String,
                ctcIconFor(raw['view'] as String, raw['icon'] as String?),
              ),
        ]),
  ];
}

class CtcSidebar extends StatelessWidget {
  const CtcSidebar({
    super.key,
    required this.activeView,
    required this.onSelect,
    required this.poleLabel,
    required this.userName,
    this.sections = ctcNavSections,
    this.onLogout,
    this.stPostCode,
    this.railEnabled = false,
    this.isRail = false,
    this.onRailToggle,
  });

  final String activeView;
  final ValueChanged<String> onSelect;
  final String poleLabel;
  final String userName;
  final List<CtcNavSection> sections;
  final VoidCallback? onLogout;
  final String? stPostCode;
  final bool railEnabled;
  final bool isRail;
  final VoidCallback? onRailToggle;

  bool get _rail => railEnabled && isRail;

  @override
  Widget build(BuildContext context) {
    final spaceSections = railEnabled && stPostCode != null
        ? ctcSpaceSections(stPostCode!)
        : sections;
    return Container(
      width: _rail ? 68 : 256,
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(right: BorderSide(color: AppColors.border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Align(
              alignment: Alignment.centerRight,
              child: IconButton(
                tooltip: _rail ? 'Ouvrir le menu' : 'Réduire le menu',
                padding: const EdgeInsets.all(6),
                constraints: const BoxConstraints.tightFor(
                  width: 28,
                  height: 28,
                ),
                style: IconButton.styleFrom(
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                  hoverColor: const Color(0xB3FFFFFF),
                  minimumSize: const Size(28, 28),
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                onPressed: onRailToggle,
                icon: const CtcMenuIcon(),
              ),
            ),
          ),
          const Divider(height: 1, color: AppColors.border),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
              child: _rail
                  ? _RailNav(
                      activeView: activeView,
                      onSelect: onSelect,
                      sections: spaceSections,
                    )
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        for (final section in spaceSections) ...[
                          Padding(
                            padding: const EdgeInsets.fromLTRB(8, 10, 8, 6),
                            child: Text(
                              section.title.toUpperCase(),
                              style: const TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 1.4,
                                color: AppColors.subtle,
                              ),
                            ),
                          ),
                          for (final item in section.items)
                            _NavItem(
                              item: item,
                              active: activeView == item.view,
                              onTap: () => onSelect(item.view),
                            ),
                        ],
                      ],
                    ),
            ),
          ),
          const Divider(height: 1, color: AppColors.border),
          Padding(
            padding: EdgeInsets.all(_rail ? 10 : 14),
            child: Row(
              mainAxisAlignment: _rail
                  ? MainAxisAlignment.center
                  : MainAxisAlignment.start,
              children: [
                Container(
                  width: 30,
                  height: 30,
                  decoration: const BoxDecoration(
                    color: AppColors.accent,
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      userName.isNotEmpty
                          ? userName.substring(0, 1).toUpperCase()
                          : '?',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ),
                if (!_rail) ...[
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      userName,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: AppColors.muted,
                      ),
                    ),
                  ),
                  if (onLogout != null)
                    IconButton(
                      tooltip: 'Se déconnecter',
                      onPressed: onLogout,
                      icon: const Icon(Icons.logout, size: 18),
                    ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _RailNav extends StatelessWidget {
  const _RailNav({
    required this.activeView,
    required this.onSelect,
    required this.sections,
  });

  final String activeView;
  final ValueChanged<String> onSelect;
  final List<CtcNavSection> sections;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      for (final section in sections)
        for (final item in section.items)
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: ValueListenableBuilder<Map<String, int>>(
              valueListenable: gedSidebarCounts,
              builder: (context, counts, _) {
                final badge = item.badgeKey == null
                    ? 0
                    : counts[item.badgeKey] ?? 0;
                return Material(
                  color: activeView == item.view
                      ? AppColors.accent.withValues(alpha: 0.12)
                      : Colors.transparent,
                  borderRadius: BorderRadius.circular(11),
                  child: Tooltip(
                    message: item.label,
                    preferBelow: false,
                    child: InkWell(
                      onTap: () => onSelect(item.view),
                      borderRadius: BorderRadius.circular(11),
                      child: SizedBox(
                        width: 44,
                        height: 40,
                        child: Stack(
                          alignment: Alignment.center,
                          children: [
                            Icon(
                              item.icon,
                              size: 18,
                              color: activeView == item.view
                                  ? AppColors.accent
                                  : AppColors.muted,
                            ),
                            if (item.badgeKey != null && badge > 0)
                              Positioned(
                                top: 6,
                                right: 4,
                                child: Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 4,
                                    vertical: 1,
                                  ),
                                  decoration: BoxDecoration(
                                    color: item.dangerBadge
                                        ? AppColors.danger
                                        : AppColors.rdcBlue,
                                    borderRadius: BorderRadius.circular(99),
                                  ),
                                  constraints: const BoxConstraints(
                                    minWidth: 18,
                                    minHeight: 14,
                                  ),
                                  child: Text(
                                    '$badge',
                                    textAlign: TextAlign.center,
                                    style: const TextStyle(
                                      fontSize: 9,
                                      fontWeight: FontWeight.w800,
                                      color: Colors.white,
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
    ],
  );
}

class _NavItem extends StatelessWidget {
  const _NavItem({
    required this.item,
    required this.active,
    required this.onTap,
  });

  final CtcNavItem item;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<Map<String, int>>(
      valueListenable: gedSidebarCounts,
      builder: (context, counts, _) {
        final badge = item.badgeKey == null ? 0 : counts[item.badgeKey] ?? 0;
        return Padding(
          padding: const EdgeInsets.only(bottom: 2),
          child: Material(
            color: active ? Colors.white : Colors.transparent,
            borderRadius: BorderRadius.circular(11),
            child: InkWell(
              onTap: onTap,
              borderRadius: BorderRadius.circular(11),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                child: Row(
                  children: [
                    Icon(
                      item.icon,
                      size: 17,
                      color: active ? AppColors.accent : AppColors.subtle,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        item.label,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: active
                              ? FontWeight.w700
                              : FontWeight.w500,
                          color: active ? AppColors.text : AppColors.muted,
                        ),
                      ),
                    ),
                    if (item.badgeKey != null)
                      _SidebarBadge(value: badge, danger: item.dangerBadge),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

class _SidebarBadge extends StatelessWidget {
  const _SidebarBadge({required this.value, required this.danger});

  final int value;
  final bool danger;

  @override
  Widget build(BuildContext context) {
    if (value <= 0) return const SizedBox();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: danger ? AppColors.danger : AppColors.rdcBlue,
        borderRadius: BorderRadius.circular(99),
      ),
      child: Text(
        '$value',
        style: const TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w800,
          color: Colors.white,
        ),
      ),
    );
  }
}

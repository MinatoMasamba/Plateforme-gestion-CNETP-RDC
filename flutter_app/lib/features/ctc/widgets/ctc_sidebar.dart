import 'package:flutter/material.dart';
import '../../../theme/app_colors.dart';

class CtcNavItem {
  const CtcNavItem(this.view, this.label, this.icon);
  final String view;
  final String label;
  final IconData icon;
}

class CtcNavSection {
  const CtcNavSection(this.title, this.items);
  final String title;
  final List<CtcNavItem> items;
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

List<CtcNavSection> ctcSectionsFromConfig(Map<String, dynamic> config) {
  const icons = <String, IconData>{
    'dashboard': Icons.dashboard_outlined,
    'dossiers': Icons.folder_outlined,
    'assignations': Icons.check_circle_outline,
    'ctc_requests': Icons.send_outlined,
    'assistant_executif': Icons.inbox_outlined,
    'financial': Icons.account_balance_wallet_outlined,
    'statistiques': Icons.insights_outlined,
    'experts': Icons.people_outline,
    'tracabilite': Icons.receipt_long_outlined,
    'homologations': Icons.verified_user_outlined,
    'instructions': Icons.assignment_outlined,
    'reunions': Icons.calendar_month_outlined,
    'drive': Icons.cloud_outlined,
    'archives': Icons.history,
    'parametres': Icons.settings_outlined,
  };
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
                raw['label'] as String,
                icons[raw['view']] ?? Icons.circle_outlined,
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
  });

  final String activeView;
  final ValueChanged<String> onSelect;
  final String poleLabel;
  final String userName;
  final List<CtcNavSection> sections;
  final VoidCallback? onLogout;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 256,
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(right: BorderSide(color: AppColors.border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 18, 20, 14),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(11),
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xFF74B9FF), Color(0xFFB7EAF7)],
                    ),
                  ),
                  child: const Icon(Icons.hub, size: 18, color: Colors.white),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Secrétariat technique',
                        style: TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1.2,
                          color: AppColors.subtle,
                        ),
                      ),
                      Text(
                        poleLabel,
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: AppColors.text,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1, color: AppColors.border),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (final section in sections) ...[
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
            padding: const EdgeInsets.all(14),
            child: Row(
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
            ),
          ),
        ],
      ),
    );
  }
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
                      fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                      color: active ? AppColors.text : AppColors.muted,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

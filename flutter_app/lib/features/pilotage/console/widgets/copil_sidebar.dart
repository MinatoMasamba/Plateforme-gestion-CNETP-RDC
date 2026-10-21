import 'package:flutter/material.dart';
import '../../../../theme/app_colors.dart';

class CopilSidebar extends StatelessWidget {
  const CopilSidebar({
    super.key,
    required this.activePanel,
    required this.onSelect,
    this.memberCount = 0,
    this.pendingAdhesions = 1,
  });

  final String activePanel;
  final ValueChanged<String> onSelect;
  final int memberCount;
  final int pendingAdhesions;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 276,
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(right: BorderSide(color: AppColors.border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(22, 22, 22, 18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'PILOTAGE CNE-ITP',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.6,
                    color: AppColors.subtle,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Tableau de bord',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: AppColors.text,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '$memberCount membres enregistrés',
                  style: const TextStyle(fontSize: 11.5, color: AppColors.subtle),
                ),
              ],
            ),
          ),
          const Divider(height: 1, color: AppColors.border),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _NavItem(
                    icon: Icons.hub_outlined,
                    label: 'Organisation CNE-ITP',
                    tint: AppColors.rdcBlue,
                    active: activePanel == 'panel-organisation',
                    onTap: () => onSelect('panel-organisation'),
                  ),
                  _NavItem(
                    icon: Icons.monitor_heart_outlined,
                    label: 'Activité des sous-commissions',
                    tint: const Color(0xFF0EA5A4),
                    active: activePanel == 'panel-activite',
                    onTap: () => onSelect('panel-activite'),
                  ),
                  _NavItem(
                    icon: Icons.grid_view_rounded,
                    label: 'Supervision des sous-commissions',
                    tint: AppColors.indigo,
                    active: activePanel == 'panel-sc',
                    onTap: () => onSelect('panel-sc'),
                  ),
                  const SizedBox(height: 6),
                  _NavItem(
                    icon: Icons.explore_outlined,
                    label: 'Cadrage Directoire',
                    tint: AppColors.rdcBlue,
                    active: activePanel == 'panel-cadrage',
                    onTap: () => onSelect('panel-cadrage'),
                  ),
                  _NavItem(
                    icon: Icons.inbox_outlined,
                    label: 'Réception technique',
                    tint: const Color(0xFF0EA5A4),
                    active: activePanel == 'panel-reception',
                    onTap: () => onSelect('panel-reception'),
                  ),
                  const SizedBox(height: 16),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 10),
                    child: Text(
                      'DEMANDES',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.6,
                        color: AppColors.subtle,
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  _NavItem(
                    icon: Icons.person_add_alt_1_outlined,
                    label: "Demandes d'adhésion",
                    tint: AppColors.success,
                    badge: pendingAdhesions > 0 ? '$pendingAdhesions' : null,
                    active: activePanel == 'panel-adhesions',
                    onTap: () => onSelect('panel-adhesions'),
                  ),
                  _NavItem(
                    icon: Icons.mail_outline,
                    label: 'Demandes de dérogation',
                    tint: AppColors.danger,
                    active: activePanel == 'panel-requests',
                    onTap: () => onSelect('panel-requests'),
                  ),
                ],
              ),
            ),
          ),
          const Divider(height: 1, color: AppColors.border),
          _NavItem(
            icon: Icons.settings_outlined,
            label: 'Paramètres',
            tint: AppColors.muted,
            active: activePanel == 'panel-settings',
            onTap: () => onSelect('panel-settings'),
          ),
          const SizedBox(height: 10),
        ],
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  const _NavItem({
    required this.icon,
    required this.label,
    required this.tint,
    required this.active,
    required this.onTap,
    this.badge,
  });

  final IconData icon;
  final String label;
  final Color tint;
  final bool active;
  final VoidCallback onTap;
  final String? badge;

  @override
  Widget build(BuildContext context) {
    final labelColor = active ? AppColors.indigo : AppColors.muted;
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Material(
        color: active ? AppColors.indigoSoft : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
            child: Row(
              children: [
                Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(
                    color: active
                        ? Colors.white
                        : tint.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(icon, size: 18, color: tint),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    label,
                    style: TextStyle(
                      fontSize: 12.5,
                      height: 1.25,
                      fontWeight: active ? FontWeight.w800 : FontWeight.w600,
                      color: labelColor,
                    ),
                  ),
                ),
                if (badge != null)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.success.withValues(alpha: 0.14),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Text(
                      badge!,
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        color: AppColors.success,
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

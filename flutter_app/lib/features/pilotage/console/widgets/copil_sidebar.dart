import 'package:flutter/material.dart';

import '../../theme/copil_theme.dart';

class CopilSidebar extends StatelessWidget {
  const CopilSidebar({
    super.key,
    required this.activePanel,
    required this.onSelect,
    this.memberCount = 0,
    this.pendingAdhesions = 0,
    this.onClose,
    this.onOrganisation,
    this.onProfile,
    this.permissions = const {},
  });

  final String activePanel;
  final ValueChanged<String> onSelect;
  final int memberCount;
  final int pendingAdhesions;
  final VoidCallback? onClose;
  final VoidCallback? onOrganisation;
  final VoidCallback? onProfile;
  final Map<String, dynamic> permissions;
  bool can(String name) => permissions[name] == true;

  @override
  Widget build(BuildContext context) {
    final p = CopilTheme.of(context);
    return Container(
      width: 288,
      decoration: BoxDecoration(
        color: p.sidebar,
        border: Border(right: BorderSide(color: p.border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 12, 16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'PILOTAGE CNE-ITP',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1.6,
                          color: p.subtle,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'Tableau de bord',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          color: p.title,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '$memberCount membres enregistrés',
                        style: TextStyle(fontSize: 11.5, color: p.subtle),
                      ),
                    ],
                  ),
                ),
                if (onClose != null)
                  IconButton(
                    onPressed: onClose,
                    tooltip: 'Fermer le menu',
                    icon: Icon(Icons.close, size: 18, color: p.subtle),
                  ),
              ],
            ),
          ),
          Divider(height: 1, color: p.border),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (can('can_view_global_console')) ...[
                    _NavItem(
                      icon: Icons.hub_outlined,
                      label: 'Organisation CNE-ITP',
                      tint: p.blue,
                      active: activePanel == 'panel-organisation',
                      onTap:
                          onOrganisation ??
                          () => onSelect('panel-organisation'),
                    ),
                    _NavItem(
                      icon: Icons.monitor_heart_outlined,
                      label: 'Activité des sous-commissions',
                      tint: p.teal,
                      active: activePanel == 'panel-activite',
                      onTap: () => onSelect('panel-activite'),
                    ),
                    _NavItem(
                      icon: Icons.grid_view_rounded,
                      label: 'Supervision des sous-commissions',
                      tint: p.indigo,
                      active: activePanel == 'panel-sc',
                      onTap: () => onSelect('panel-sc'),
                    ),
                  ],
                  const SizedBox(height: 6),
                  if (can('can_trigger_steps'))
                    _NavItem(
                      icon: Icons.explore_outlined,
                      label: 'Cadrage Directoire',
                      tint: p.blue,
                      active: activePanel == 'panel-cadrage',
                      onTap: () => onSelect('panel-cadrage'),
                    ),
                  if (can('can_acknowledge_reception'))
                    _NavItem(
                      icon: Icons.inbox_outlined,
                      label: 'Réception technique',
                      tint: p.teal,
                      active: activePanel == 'panel-reception',
                      onTap: () => onSelect('panel-reception'),
                    ),
                  if (can('can_manage_access') ||
                      can('can_approve_requests')) ...[
                    const SizedBox(height: 16),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 10),
                      child: Text(
                        'DEMANDES',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1.6,
                          color: p.subtle,
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                  ],
                  if (can('can_manage_access'))
                    _NavItem(
                      icon: Icons.person_add_alt_1_outlined,
                      label: "Demandes d'adhésion",
                      tint: p.success,
                      badge: pendingAdhesions > 0 ? '$pendingAdhesions' : null,
                      active: activePanel == 'panel-adhesions',
                      onTap: () => onSelect('panel-adhesions'),
                    ),
                  if (can('can_approve_requests'))
                    _NavItem(
                      icon: Icons.mail_outline,
                      label: 'Demandes de dérogation',
                      tint: p.danger,
                      active: activePanel == 'panel-requests',
                      onTap: () => onSelect('panel-requests'),
                    ),
                ],
              ),
            ),
          ),
          Divider(height: 1, color: p.border),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 14),
            child: _NavItem(
              icon: Icons.person_outline,
              label: 'Mon profil COPIL',
              tint: p.muted,
              active: false,
              onTap: onProfile ?? () {},
            ),
          ),
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
    final p = CopilTheme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Material(
        color: active ? p.indigoSoft : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: active
                    ? p.indigo.withValues(alpha: 0.25)
                    : Colors.transparent,
              ),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: active
                        ? p.card.withValues(alpha: p.isDark ? 0.65 : 1)
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
                      color: active ? p.indigo : p.muted,
                    ),
                  ),
                ),
                if (badge != null)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 7,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: p.successSoft,
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Text(
                      badge!,
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        color: p.success,
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

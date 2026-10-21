import 'package:flutter/material.dart';
import '../../../theme/app_colors.dart';

class CtcTopbar extends StatelessWidget {
  const CtcTopbar({
    super.key,
    required this.poleLabel,
    required this.userName,
    required this.onToggleSidebar,
  });

  final String poleLabel;
  final String userName;
  final VoidCallback onToggleSidebar;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const _TricolorBar(),
          Container(
            color: const Color(0xFF05050B),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 5),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: const [
                Text(
                  'RDC - CABINET INTERMINISTÉRIEL DE CO-GOUVERNANCE',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.4,
                  ),
                ),
                Text(
                  'Secrétariat National CNE-ITP',
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 9,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 1.4,
                  ),
                ),
              ],
            ),
          ),
          Container(
            height: 68,
            padding: const EdgeInsets.symmetric(horizontal: 20),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.border)),
            ),
            child: Row(
              children: [
                IconButton(
                  onPressed: onToggleSidebar,
                  icon: const Icon(Icons.menu, size: 20),
                  color: AppColors.muted,
                  tooltip: 'Ouvrir le menu',
                ),
                const SizedBox(width: 4),
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white,
                    border: Border.all(color: const Color(0xFFD4AF37)),
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: Image.asset('assets/img/logo-cnetp.png', fit: BoxFit.cover),
                ),
                const SizedBox(width: 8),
                const _VerticalTricolor(),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Coordination du Secrétariat technique',
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: AppColors.text,
                        ),
                      ),
                      Text(
                        'Gestion et suivi des travaux de normalisation',
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(fontSize: 10, color: AppColors.muted),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 10),
                _TopAction(icon: Icons.mail_outline, label: 'Annuaire & Mail'),
                const SizedBox(width: 6),
                _TopAction(
                  icon: Icons.videocam_outlined,
                  label: 'Réunion Meet',
                  color: AppColors.rdcBlue,
                ),
                const SizedBox(width: 6),
                _TopAction(
                  icon: Icons.storage_outlined,
                  label: 'Espace Drive',
                  color: AppColors.success,
                ),
                const SizedBox(width: 10),
                const Icon(Icons.notifications_none, size: 20, color: AppColors.muted),
                const SizedBox(width: 14),
                Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: AppColors.accent,
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      _initials(userName),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      userName,
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.text),
                    ),
                    Text(
                      poleLabel,
                      style: TextStyle(fontSize: 9, color: AppColors.subtle),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  static String _initials(String name) {
    final parts = name.trim().split(RegExp(r'\s+'));
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts.first.substring(0, 1).toUpperCase();
    return (parts.first.substring(0, 1) + parts.last.substring(0, 1)).toUpperCase();
  }
}

class _TricolorBar extends StatelessWidget {
  const _TricolorBar();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 4,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: const [
          Expanded(child: ColoredBox(color: AppColors.rdcBlue)),
          Expanded(child: ColoredBox(color: AppColors.rdcYellow)),
          Expanded(child: ColoredBox(color: AppColors.rdcRed)),
        ],
      ),
    );
  }
}

class _VerticalTricolor extends StatelessWidget {
  const _VerticalTricolor();

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(2),
      child: SizedBox(
        width: 3,
        height: 28,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: const [
            Expanded(child: ColoredBox(color: AppColors.rdcBlue)),
            Expanded(child: ColoredBox(color: AppColors.rdcYellow)),
            Expanded(child: ColoredBox(color: AppColors.rdcRed)),
          ],
        ),
      ),
    );
  }
}

class _TopAction extends StatelessWidget {
  const _TopAction({required this.icon, required this.label, this.color = AppColors.muted});

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      child: Row(
        children: [
          Icon(icon, size: 15, color: color),
          const SizedBox(width: 6),
          Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color)),
        ],
      ),
    );
  }
}

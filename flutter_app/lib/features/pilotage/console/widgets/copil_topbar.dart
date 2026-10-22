import 'package:flutter/material.dart';
import '../../../../theme/app_colors.dart';

class CopilTopbar extends StatelessWidget {
  const CopilTopbar({
    super.key,
    required this.onToggleSidebar,
    required this.memberCount,
    this.onThemeToggle,
    this.onLogout,
    this.isDark = false,
  });

  final VoidCallback onToggleSidebar;
  final int memberCount;
  final VoidCallback? onThemeToggle;
  final VoidCallback? onLogout;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const _TricolorBar(height: 4),
          Container(
            height: 74,
            padding: const EdgeInsets.symmetric(horizontal: 20),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.border)),
            ),
            child: Row(
              children: [
                // Armoirie + ligne d'État
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white,
                    border: Border.all(color: const Color(0xFFD4AF37)),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x22000000),
                        blurRadius: 3,
                        offset: Offset(0, 1),
                      ),
                    ],
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: Image.asset(
                    'assets/img/logo-cnetp.png',
                    fit: BoxFit.cover,
                  ),
                ),
                const SizedBox(width: 10),
                const _VerticalTricolor(),
                const SizedBox(width: 14),
                const Text(
                  'PILOTAGE CNE-ITP',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.2,
                    color: AppColors.text,
                  ),
                ),
                const SizedBox(width: 10),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.indigoSoft,
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    '$memberCount MEMBRES',
                    style: const TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w800,
                      color: AppColors.indigo,
                      letterSpacing: 0.6,
                    ),
                  ),
                ),
                const Spacer(),
                _OutlineButton(
                  icon: Icons.dashboard_outlined,
                  label: 'Espace Bureau Directoire',
                  color: AppColors.rdcBlue,
                  background: AppColors.blueSoft,
                  border: const Color(0xFFB7DDF0),
                ),
                const SizedBox(width: 10),
                _OutlineButton(
                  icon: Icons.description_outlined,
                  label: 'Instructions existantes',
                  color: AppColors.purple,
                  background: AppColors.purpleSoft,
                  border: const Color(0xFFDDD6FE),
                ),
                const SizedBox(width: 10),
                _RoundIconButton(
                  icon: Icons.auto_awesome_outlined,
                  color: AppColors.indigo,
                ),
                const SizedBox(width: 8),
                _RoundIconButton(
                  icon: isDark ? Icons.light_mode_outlined : Icons.dark_mode_outlined,
                  color: AppColors.muted,
                  onTap: onThemeToggle,
                ),
                const SizedBox(width: 8),
                if (onLogout != null)
                  _RoundIconButton(
                    icon: Icons.logout,
                    color: AppColors.danger,
                    onTap: onLogout,
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _TricolorBar extends StatelessWidget {
  const _TricolorBar({required this.height});
  final double height;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: height,
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
        width: 4,
        height: 34,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: const [
            Expanded(flex: 3, child: ColoredBox(color: AppColors.rdcBlue)),
            Expanded(flex: 2, child: ColoredBox(color: AppColors.rdcYellow)),
            Expanded(flex: 3, child: ColoredBox(color: AppColors.rdcRed)),
          ],
        ),
      ),
    );
  }
}

class _OutlineButton extends StatelessWidget {
  const _OutlineButton({
    required this.icon,
    required this.label,
    required this.color,
    required this.background,
    required this.border,
  });

  final IconData icon;
  final String label;
  final Color color;
  final Color background;
  final Color border;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(9),
        border: Border.all(color: border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 15, color: color),
          const SizedBox(width: 7),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}

class _RoundIconButton extends StatelessWidget {
  const _RoundIconButton({required this.icon, required this.color, this.onTap});

  final IconData icon;
  final Color color;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(999),
      child: Container(
        width: 38,
        height: 38,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Colors.white,
          border: Border.all(color: AppColors.border),
        ),
        child: Icon(icon, size: 18, color: color),
      ),
    );
  }
}

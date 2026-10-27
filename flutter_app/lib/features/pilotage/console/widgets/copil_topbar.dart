import 'package:flutter/material.dart';
import '../../theme/copil_theme.dart';

class CopilTopbar extends StatelessWidget {
  const CopilTopbar({
    super.key,
    required this.onToggleSidebar,
    required this.memberCount,
    this.onBack,
    this.onDirectoire,
    this.onInstructions,
    this.onAi,
    this.onThemeToggle,
  });
  final VoidCallback onToggleSidebar;
  final int memberCount;
  final VoidCallback? onBack, onDirectoire, onInstructions, onAi, onThemeToggle;

  @override
  Widget build(BuildContext context) {
    final p = CopilTheme.of(context);
    final wide = MediaQuery.sizeOf(context).width >= 640;
    final showActionLabels = MediaQuery.sizeOf(context).width >= 1180;
    Widget icon(
      IconData icon,
      String label,
      VoidCallback? action, {
      Color? color,
      bool outlined = false,
    }) => SizedBox(
      width: 34,
      height: 34,
      child: IconButton(
        padding: EdgeInsets.zero,
        tooltip: label,
        onPressed: action,
        style: IconButton.styleFrom(
          side: outlined ? BorderSide(color: p.border) : BorderSide.none,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
        icon: Icon(icon, size: 17, color: color ?? p.muted),
      ),
    );
    Widget action(
      IconData glyph,
      String label,
      VoidCallback? callback,
      Color tint,
    ) => !showActionLabels
        ? Tooltip(
            message: label,
            child: SizedBox(
              width: 32,
              height: 32,
              child: OutlinedButton(
                onPressed: callback,
                style: OutlinedButton.styleFrom(
                  padding: EdgeInsets.zero,
                  foregroundColor: tint,
                  backgroundColor: tint.withValues(alpha: .08),
                  side: BorderSide(color: tint.withValues(alpha: .3)),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                child: Icon(glyph, size: 14),
              ),
            ),
          )
        : Tooltip(
            message: label,
            child: OutlinedButton.icon(
              onPressed: callback,
              style: OutlinedButton.styleFrom(
                foregroundColor: tint,
                backgroundColor: tint.withValues(alpha: .08),
                side: BorderSide(color: tint.withValues(alpha: .3)),
                minimumSize: Size.zero,
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 10,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              icon: Icon(glyph, size: 14),
              label: showActionLabels
                  ? Text(
                      label,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    )
                  : const SizedBox.shrink(),
            ),
          );
    return Container(
      width: double.infinity,
      color: p.topbar,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            height: 4,
            child: Row(
              children: [
                Expanded(
                  child: ColoredBox(
                    color: p.blue,
                    child: const SizedBox.expand(),
                  ),
                ),
                const Expanded(
                  child: ColoredBox(
                    color: Color(0xFFFFF24B),
                    child: SizedBox.expand(),
                  ),
                ),
                const Expanded(
                  child: ColoredBox(
                    color: Color(0xFFDB3832),
                    child: SizedBox.expand(),
                  ),
                ),
              ],
            ),
          ),
          Container(
            height: wide ? 60 : 56,
            padding: EdgeInsets.symmetric(
              horizontal: wide ? 20 : 12,
              vertical: 0,
            ),
            decoration: BoxDecoration(
              border: Border(bottom: BorderSide(color: p.border)),
            ),
            child: Row(
              children: [
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (wide) ...[
                      Container(
                        width: 36,
                        height: 36,
                        clipBehavior: Clip.antiAlias,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.white,
                          border: Border.all(color: const Color(0xFFD4AF37)),
                        ),
                        child: Image.asset(
                          'assets/img/logo-cnetp.png',
                          fit: BoxFit.cover,
                        ),
                      ),
                      const SizedBox(width: 10),
                      SizedBox(
                        width: 3,
                        height: 26,
                        child: Column(
                          children: [
                            Expanded(child: Container(color: p.blue)),
                            Container(
                              height: 7,
                              color: const Color(0xFFFFF24B),
                            ),
                            Expanded(
                              child: Container(color: const Color(0xFFDB3832)),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                    ],
                    icon(
                      Icons.menu,
                      'Afficher ou masquer le menu',
                      onToggleSidebar,
                    ),
                    if (onBack != null) ...[
                      if (!wide)
                        icon(Icons.arrow_back, 'Espace de Travail', onBack),
                      if (wide)
                        TextButton.icon(
                          onPressed: onBack,
                          icon: Icon(
                            Icons.arrow_back,
                            size: 14,
                            color: p.muted,
                          ),
                          style: TextButton.styleFrom(
                            padding: const EdgeInsets.symmetric(horizontal: 6),
                            minimumSize: Size.zero,
                          ),
                          label: Text(
                            'Espace de Travail',
                            style: TextStyle(fontSize: 12, color: p.muted),
                          ),
                        ),
                      if (wide)
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          child: Text(
                            '|',
                            style: TextStyle(color: p.borderStrong),
                          ),
                        ),
                    ],
                    Text(
                      'PILOTAGE CNE-ITP',
                      style: TextStyle(
                        fontSize: wide ? 14 : 12,
                        fontWeight: FontWeight.w800,
                        color: p.text,
                      ),
                    ),
                    if (wide) ...[
                      const SizedBox(width: 12),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 3,
                        ),
                        decoration: BoxDecoration(
                          color: p.blueSoft,
                          borderRadius: BorderRadius.circular(999),
                          border: Border.all(
                            color: p.blue.withValues(alpha: .3),
                          ),
                        ),
                        child: Text(
                          '$memberCount MEMBRE${memberCount == 1 ? '' : 'S'}',
                          style: TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.w700,
                            color: p.blue,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                const Spacer(),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (onDirectoire != null) ...[
                      action(
                        Icons.view_sidebar_outlined,
                        'Espace Bureau Directoire',
                        onDirectoire,
                        p.blue,
                      ),
                      const SizedBox(width: 8),
                    ],
                    if (onInstructions != null) ...[
                      action(
                        Icons.assignment_outlined,
                        'Instructions existantes',
                        onInstructions,
                        p.purple,
                      ),
                      const SizedBox(width: 8),
                    ],
                    if (onAi != null) ...[
                      icon(
                        Icons.auto_awesome_outlined,
                        'Assistant IA Pilotage',
                        onAi,
                        color: p.blue,
                        outlined: true,
                      ),
                      const SizedBox(width: 8),
                    ],
                    icon(
                      p.isDark
                          ? Icons.dark_mode_outlined
                          : Icons.light_mode_outlined,
                      'Changer le thème',
                      onThemeToggle,
                      outlined: true,
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
}

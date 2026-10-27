import 'package:flutter/material.dart';

class ExpertPalette {
  const ExpertPalette({
    required this.isDark,
    required this.bg,
    required this.sidebar,
    required this.sidebarHeader,
    required this.nav,
    required this.card,
    required this.surface,
    required this.field,
    required this.border,
    required this.borderStrong,
    required this.text,
    required this.title,
    required this.muted,
    required this.subtle,
    required this.blue,
    required this.blueDeep,
    required this.blueSoft,
    required this.amber,
    required this.amberSoft,
    required this.green,
    required this.red,
    required this.teal,
    required this.indigo,
    required this.sky,
  });

  final bool isDark;
  final Color bg;
  final Color sidebar;
  final Color sidebarHeader;
  final Color nav;
  final Color card;
  final Color surface;
  final Color field;
  final Color border;
  final Color borderStrong;
  final Color text;
  final Color title;
  final Color muted;
  final Color subtle;
  final Color blue;
  final Color blueDeep;
  final Color blueSoft;
  final Color amber;
  final Color amberSoft;
  final Color green;
  final Color red;
  final Color teal;
  final Color indigo;
  final Color sky;

  static const dark = ExpertPalette(
    isDark: true,
    bg: Color(0xFF020204),
    sidebar: Color(0xFF06060C),
    sidebarHeader: Color(0xFF08080D),
    nav: Color(0xFF050508),
    card: Color(0xFF0A0A0F),
    surface: Color(0xFF101017),
    field: Color(0xFF030307),
    border: Color(0x1AFFFFFF),
    borderStrong: Color(0x2BFFFFFF),
    text: Color(0xFFE2E8F0),
    title: Color(0xFFF8FAFC),
    muted: Color(0xFF94A3B8),
    subtle: Color(0xFF64748B),
    blue: Color(0xFF3B82F6),
    blueDeep: Color(0xFF2563EB),
    blueSoft: Color(0x1F3B82F6),
    amber: Color(0xFFF59E0B),
    amberSoft: Color(0x1AF59E0B),
    green: Color(0xFF34D399),
    red: Color(0xFFF87171),
    teal: Color(0xFF2DD4BF),
    indigo: Color(0xFF818CF8),
    sky: Color(0xFF38BDF8),
  );

  static const light = ExpertPalette(
    isDark: false,
    bg: Color(0xFFF1F5F9),
    sidebar: Color(0xFFF8FAFC),
    sidebarHeader: Color(0xFFFFFFFF),
    nav: Color(0xFFFFFFFF),
    card: Color(0xFFFFFFFF),
    surface: Color(0xFFF8FAFC),
    field: Color(0xFFFFFFFF),
    border: Color(0xFFE2E8F0),
    borderStrong: Color(0xFFCBD5E1),
    text: Color(0xFF334155),
    title: Color(0xFF0F172A),
    muted: Color(0xFF475569),
    subtle: Color(0xFF64748B),
    blue: Color(0xFF2563EB),
    blueDeep: Color(0xFF1D4ED8),
    blueSoft: Color(0xFFEFF6FF),
    amber: Color(0xFFD97706),
    amberSoft: Color(0xFFFEF3C7),
    green: Color(0xFF059669),
    red: Color(0xFFDC2626),
    teal: Color(0xFF0D9488),
    indigo: Color(0xFF4F46E5),
    sky: Color(0xFF0284C7),
  );

  List<Color> get backgroundGradient => isDark
      ? const [Color(0xFF031514), Color(0xFF020204), Color(0xFF0B1120)]
      : const [Color(0xFFF8FAFC), Color(0xFFF1F5F9), Color(0xFFE2E8F0)];
}

class ExpertTheme extends InheritedWidget {
  const ExpertTheme({super.key, required this.palette, required super.child});

  final ExpertPalette palette;

  static ExpertPalette of(BuildContext context) {
    final theme = context.dependOnInheritedWidgetOfExactType<ExpertTheme>();
    assert(theme != null, 'ExpertTheme is missing from the widget tree.');
    return theme!.palette;
  }

  @override
  bool updateShouldNotify(ExpertTheme oldWidget) =>
      palette.isDark != oldWidget.palette.isDark;
}

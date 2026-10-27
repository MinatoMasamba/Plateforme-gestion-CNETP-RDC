import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class CopilPalette {
  const CopilPalette({
    required this.isDark,
    required this.bg,
    required this.sidebar,
    required this.topbar,
    required this.card,
    required this.cardAlt,
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
    required this.success,
    required this.successSoft,
    required this.warning,
    required this.warningSoft,
    required this.danger,
    required this.dangerSoft,
    required this.indigo,
    required this.indigoSoft,
    required this.purple,
    required this.purpleSoft,
    required this.teal,
    required this.tealSoft,
    required this.yellow,
  });

  final bool isDark;
  final Color bg;
  final Color sidebar;
  final Color topbar;
  final Color card;
  final Color cardAlt;
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
  final Color success;
  final Color successSoft;
  final Color warning;
  final Color warningSoft;
  final Color danger;
  final Color dangerSoft;
  final Color indigo;
  final Color indigoSoft;
  final Color purple;
  final Color purpleSoft;
  final Color teal;
  final Color tealSoft;
  final Color yellow;

  CopilPalette surfaces({
    Color? bg,
    Color? sidebar,
    Color? topbar,
    Color? card,
    Color? border,
  }) => CopilPalette(
    isDark: isDark,
    bg: bg ?? this.bg,
    sidebar: sidebar ?? this.sidebar,
    topbar: topbar ?? this.topbar,
    card: card ?? this.card,
    cardAlt: cardAlt,
    field: field,
    border: border ?? this.border,
    borderStrong: borderStrong,
    text: text,
    title: title,
    muted: muted,
    subtle: subtle,
    blue: blue,
    blueDeep: blueDeep,
    blueSoft: blueSoft,
    success: success,
    successSoft: successSoft,
    warning: warning,
    warningSoft: warningSoft,
    danger: danger,
    dangerSoft: dangerSoft,
    indigo: indigo,
    indigoSoft: indigoSoft,
    purple: purple,
    purpleSoft: purpleSoft,
    teal: teal,
    tealSoft: tealSoft,
    yellow: yellow,
  );

  static const dark = CopilPalette(
    isDark: true,
    bg: Color(0xFF06060C),
    sidebar: Color(0xFF0A0A10),
    topbar: Color(0xFF050508),
    card: Color(0xFF0C0C14),
    cardAlt: Color(0xFF101019),
    field: Color(0xFF030307),
    border: Color(0x1AFFFFFF),
    borderStrong: Color(0x33FFFFFF),
    text: Color(0xFFE2E8F0),
    title: Color(0xFFF8FAFC),
    muted: Color(0xFF94A3B8),
    subtle: Color(0xFF64748B),
    blue: Color(0xFF0095C9),
    blueDeep: Color(0xFF007EA8),
    blueSoft: Color(0x1F0095C9),
    success: Color(0xFF34D399),
    successSoft: Color(0x1F34D399),
    warning: Color(0xFFFBBF24),
    warningSoft: Color(0x1FFBBF24),
    danger: Color(0xFFF87171),
    dangerSoft: Color(0x1FF87171),
    indigo: Color(0xFF818CF8),
    indigoSoft: Color(0x1F6366F1),
    purple: Color(0xFFA78BFA),
    purpleSoft: Color(0x1F7C3AED),
    teal: Color(0xFF2DD4BF),
    tealSoft: Color(0x1F2DD4BF),
    yellow: Color(0xFFFFF24B),
  );

  static const light = CopilPalette(
    isDark: false,
    bg: Color(0xFFF4F8FC),
    sidebar: Color(0xFFFFFFFF),
    topbar: Color(0xFFFFFFFF),
    card: Color(0xFFFFFFFF),
    cardAlt: Color(0xFFF1F5F9),
    field: Color(0xFFFFFFFF),
    border: Color(0xFFE2E8F0),
    borderStrong: Color(0xFFCBD5E1),
    text: Color(0xFF334155),
    title: Color(0xFF0F172A),
    muted: Color(0xFF475569),
    subtle: Color(0xFF94A3B8),
    blue: Color(0xFF0095C9),
    blueDeep: Color(0xFF007EA8),
    blueSoft: Color(0xFFE6F4FA),
    success: Color(0xFF059669),
    successSoft: Color(0xFFD1FAE5),
    warning: Color(0xFFD97706),
    warningSoft: Color(0xFFFEF3C7),
    danger: Color(0xFFDC2626),
    dangerSoft: Color(0xFFFEE2E2),
    indigo: Color(0xFF4F46E5),
    indigoSoft: Color(0xFFEEF2FF),
    purple: Color(0xFF7C3AED),
    purpleSoft: Color(0xFFF5F3FF),
    teal: Color(0xFF0D9488),
    tealSoft: Color(0xFFCCFBF1),
    yellow: Color(0xFFFFD60A),
  );
}

class CopilTheme extends InheritedWidget {
  const CopilTheme({super.key, required this.palette, required super.child});

  final CopilPalette palette;

  static CopilPalette of(BuildContext context) {
    final theme = context.dependOnInheritedWidgetOfExactType<CopilTheme>();
    return theme?.palette ?? CopilPalette.light;
  }

  @override
  bool updateShouldNotify(CopilTheme oldWidget) =>
      palette.isDark != oldWidget.palette.isDark;
}

final copilDarkProvider = StateProvider<bool>((ref) => true);

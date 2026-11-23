import 'package:flutter/material.dart';

/// Échelle typographique des sections Expert, calée sur le texte de l'éditeur de normes.
abstract final class ExpertType {
  static const double body = 15;
  static const double bodyHeight = 1.6;
  static const double meta = 13;
  static const double label = 12;
  static const double section = 16;
  static const double pageTitle = 20;
}

/// Espace laissé sous le contenu défilant pour dégager le bouton Message flottant.
const double expertFabClearance = 96;

abstract final class ExpertCommunicationLayout {
  static const double maxWidth = 1280;
  static const double readingWidth = 760;
  static const double bubbleWidth = 640;
  static const double segmentedTabsWidth = 440;
  static const double compactInboxWidth = 300;
  static const double wideInboxWidth = 360;
  static const double compactHistoryWidth = 260;
  static const double wideHistoryWidth = 300;
  static const double desktopHeaderHeight = 72;

  static double contentWidth(double available) =>
      available > maxWidth ? maxWidth : available;

  static double inboxWidth(double available) =>
      available >= 1200 ? wideInboxWidth : compactInboxWidth;

  static double historyWidth(double available) =>
      available >= 1200 ? wideHistoryWidth : compactHistoryWidth;
}

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
    bg: Color(0xFF101820),
    sidebar: Color(0xFF0C141E),
    sidebarHeader: Color(0xFF0C141E),
    nav: Color(0xFF14202C),
    card: Color(0xFF182430),
    surface: Color(0xFF1D2D3B),
    field: Color(0xFF111D28),
    border: Color(0xFF304252),
    borderStrong: Color(0xFF526A7D),
    text: Color(0xFFE2E8F0),
    title: Color(0xFFF8FAFC),
    muted: Color(0xFFB6C5D4),
    subtle: Color(0xFF97ABBE),
    blue: Color(0xFF0095C9),
    blueDeep: Color(0xFF007CA7),
    blueSoft: Color(0xFF103D50),
    amber: Color(0xFFF59E0B),
    amberSoft: Color(0x1AF59E0B),
    green: Color(0xFF34D399),
    red: Color(0xFFF87171),
    teal: Color(0xFF2DD4BF),
    indigo: Color(0xFF0095C9),
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
    blue: Color(0xFF0095C9),
    blueDeep: Color(0xFF007CA7),
    blueSoft: Color(0xFFE6F5FB),
    amber: Color(0xFFD97706),
    amberSoft: Color(0xFFFEF3C7),
    green: Color(0xFF059669),
    red: Color(0xFFDC2626),
    teal: Color(0xFF0D9488),
    indigo: Color(0xFF007CA7),
    sky: Color(0xFF0284C7),
  );

  List<Color> get backgroundGradient => [bg, bg];
}

ThemeData expertMaterialTheme(BuildContext context, ExpertPalette p) {
  final base = Theme.of(context);
  final scheme =
      ColorScheme.fromSeed(
        seedColor: p.blue,
        brightness: p.isDark ? Brightness.dark : Brightness.light,
      ).copyWith(
        primary: p.blue,
        onPrimary: Colors.white,
        primaryContainer: p.blueSoft,
        onPrimaryContainer: p.text,
        secondary: p.blueDeep,
        surface: p.card,
        onSurface: p.text,
        onSurfaceVariant: p.muted,
        outline: p.borderStrong,
        error: p.red,
      );
  final shape = RoundedRectangleBorder(borderRadius: BorderRadius.circular(10));
  return base.copyWith(
    colorScheme: scheme,
    scaffoldBackgroundColor: p.bg,
    canvasColor: p.card,
    dividerColor: p.border,
    iconTheme: IconThemeData(color: p.muted, size: 20),
    appBarTheme: AppBarTheme(
      backgroundColor: p.nav,
      foregroundColor: p.title,
      elevation: 0,
      titleTextStyle: TextStyle(
        fontFamily: 'Inter',
        fontSize: 18,
        fontWeight: FontWeight.w600,
        color: p.title,
      ),
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: p.surface,
      contentTextStyle: TextStyle(
        fontFamily: 'Inter',
        fontSize: 14,
        color: p.text,
      ),
      actionTextColor: p.blue,
    ),
    popupMenuTheme: PopupMenuThemeData(
      color: p.card,
      textStyle: TextStyle(fontFamily: 'Inter', fontSize: 14, color: p.text),
    ),
    dialogTheme: base.dialogTheme.copyWith(
      backgroundColor: p.card,
      titleTextStyle: TextStyle(
        fontFamily: 'Inter',
        fontSize: 20,
        fontWeight: FontWeight.w600,
        color: p.title,
      ),
      contentTextStyle: TextStyle(
        fontFamily: 'Inter',
        fontSize: 14,
        height: 1.5,
        color: p.text,
      ),
    ),
    textTheme: base.textTheme
        .apply(fontFamily: 'Inter', bodyColor: p.text, displayColor: p.title)
        .copyWith(
          bodyLarge: TextStyle(
            fontFamily: 'Inter',
            fontSize: ExpertType.body,
            height: ExpertType.bodyHeight,
            color: p.text,
          ),
          bodyMedium: TextStyle(
            fontFamily: 'Inter',
            fontSize: ExpertType.body,
            height: ExpertType.bodyHeight,
            color: p.text,
          ),
          bodySmall: TextStyle(
            fontFamily: 'Inter',
            fontSize: ExpertType.meta,
            height: 1.45,
            color: p.muted,
          ),
        ),
    inputDecorationTheme: InputDecorationTheme(
      labelStyle: TextStyle(color: p.muted, fontSize: 14),
      hintStyle: TextStyle(color: p.muted, fontSize: 14),
      filled: true,
      fillColor: p.field,
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: BorderSide(color: p.borderStrong),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: BorderSide(color: p.borderStrong),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: p.blueDeep,
        foregroundColor: Colors.white,
        minimumSize: const Size(44, 44),
        shape: shape,
        textStyle: const TextStyle(
          fontFamily: 'Inter',
          fontSize: 14,
          fontWeight: FontWeight.w600,
        ),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: p.isDark ? p.text : p.blueDeep,
        minimumSize: const Size(44, 44),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        side: BorderSide(color: p.borderStrong),
        shape: shape,
        textStyle: const TextStyle(
          fontFamily: 'Inter',
          fontSize: 14,
          fontWeight: FontWeight.w600,
        ),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: p.isDark ? p.blue : p.blueDeep,
        minimumSize: const Size(44, 44),
      ),
    ),
    chipTheme: base.chipTheme.copyWith(
      backgroundColor: p.field,
      selectedColor: p.blueSoft,
      disabledColor: p.surface,
      labelStyle: TextStyle(color: p.text, fontSize: 13),
      secondaryLabelStyle: TextStyle(color: p.text, fontSize: 13),
      side: BorderSide(color: p.border),
    ),
  );
}

class ExpertPageTheme extends StatelessWidget {
  const ExpertPageTheme({
    super.key,
    required this.palette,
    required this.child,
  });
  final ExpertPalette palette;
  final Widget child;

  @override
  Widget build(BuildContext context) => ExpertTheme(
    palette: palette,
    child: Theme(data: expertMaterialTheme(context, palette), child: child),
  );
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

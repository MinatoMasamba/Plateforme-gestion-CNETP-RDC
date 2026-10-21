import 'package:flutter/material.dart';
import 'app_colors.dart';

class AppTheme {
  static ThemeData light() {
    final base = ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      fontFamily: 'Inter',
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.rdcBlue,
        brightness: Brightness.light,
        primary: AppColors.rdcBlue,
        surface: AppColors.surface,
      ),
    );

    return base.copyWith(
      scaffoldBackgroundColor: AppColors.page,
      dividerColor: AppColors.border,
      textTheme: base.textTheme
          .apply(bodyColor: AppColors.text, displayColor: AppColors.text)
          .copyWith(
            bodySmall: base.textTheme.bodySmall?.copyWith(
              color: AppColors.muted,
              fontSize: 12,
            ),
          ),
      iconTheme: const IconThemeData(color: AppColors.muted, size: 20),
    );
  }
}

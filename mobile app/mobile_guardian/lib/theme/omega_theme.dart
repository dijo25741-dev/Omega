// lib/theme/omega_theme.dart
// Centralized design system for Omega Mobile Guardian

import 'package:flutter/material.dart';

class OmegaColors {
  OmegaColors._();

  // Backgrounds
  static const Color bgPrimary = Color(0xFF090A0F);
  static const Color bgSecondary = Color(0xFF0D1117);
  static const Color bgCard = Color(0xFF111827);
  static const Color bgCardBorder = Color(0xFF1F2937);

  // Accents
  static const Color cyan = Color(0xFF00D4FF);
  static const Color cyanDim = Color(0xFF0E4F6B);
  static const Color cyanSurface = Color(0xFF071E2B);

  // Status
  static const Color safe = Color(0xFF10B981);
  static const Color safeSurface = Color(0xFF052E1C);
  static const Color warning = Color(0xFFF59E0B);
  static const Color warningSurface = Color(0xFF2D1D00);
  static const Color danger = Color(0xFFEF4444);
  static const Color dangerSurface = Color(0xFF2D0A0A);
  static const Color critical = Color(0xFFFF2D2D);
  static const Color criticalSurface = Color(0xFF3D0000);

  // Text
  static const Color textPrimary = Color(0xFFE2E8F0);
  static const Color textSecondary = Color(0xFF94A3B8);
  static const Color textMuted = Color(0xFF475569);
  static const Color textAccent = Color(0xFF00D4FF);

  // Risk colors by level
  static Color riskColor(String level) {
    switch (level.toUpperCase()) {
      case 'LOW':
        return safe;
      case 'MEDIUM':
        return warning;
      case 'HIGH':
        return const Color(0xFFF97316);
      case 'CRITICAL':
        return critical;
      default:
        return safe;
    }
  }

  static Color riskSurface(String level) {
    switch (level.toUpperCase()) {
      case 'LOW':
        return safeSurface;
      case 'MEDIUM':
        return warningSurface;
      case 'HIGH':
        return const Color(0xFF2D1100);
      case 'CRITICAL':
        return criticalSurface;
      default:
        return safeSurface;
    }
  }

  static Color severityColor(String severity) {
    switch (severity.toLowerCase()) {
      case 'critical':
        return critical;
      case 'high':
        return const Color(0xFFF97316);
      case 'info':
        return cyan;
      default:
        return textSecondary;
    }
  }
}

class OmegaTheme {
  OmegaTheme._();

  static ThemeData get dark => ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: OmegaColors.bgPrimary,
        colorScheme: const ColorScheme.dark(
          primary: OmegaColors.cyan,
          secondary: OmegaColors.safe,
          error: OmegaColors.danger,
          surface: OmegaColors.bgCard,
        ),
        textTheme: const TextTheme(
            displayLarge: TextStyle(color: OmegaColors.textPrimary, fontFamily: 'monospace'),
            displayMedium: TextStyle(color: OmegaColors.textPrimary, fontFamily: 'monospace'),
            bodyLarge: TextStyle(color: OmegaColors.textPrimary, fontSize: 14, fontFamily: 'monospace'),
            bodyMedium: TextStyle(color: OmegaColors.textSecondary, fontSize: 12, fontFamily: 'monospace'),
            bodySmall: TextStyle(color: OmegaColors.textMuted, fontSize: 10, fontFamily: 'monospace'),
            labelLarge: TextStyle(
              color: OmegaColors.textPrimary,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.5,
              fontFamily: 'monospace',
            ),
          ),
        appBarTheme: AppBarTheme(
          backgroundColor: OmegaColors.bgSecondary,
          elevation: 0,
          titleTextStyle: const TextStyle(
            color: OmegaColors.textPrimary,
            fontSize: 14,
            fontWeight: FontWeight.bold,
            letterSpacing: 2.0,
            fontFamily: 'monospace',
          ),
          iconTheme: const IconThemeData(color: OmegaColors.textSecondary),
          surfaceTintColor: Colors.transparent,
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: OmegaColors.bgCard,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: const BorderSide(color: OmegaColors.bgCardBorder),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: const BorderSide(color: OmegaColors.bgCardBorder),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: const BorderSide(color: OmegaColors.cyan, width: 1.5),
          ),
          labelStyle: const TextStyle(
            color: OmegaColors.textMuted,
            fontSize: 11,
            letterSpacing: 1.0,
            fontFamily: 'monospace',
          ),
          prefixIconColor: OmegaColors.textMuted,
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: OmegaColors.cyan,
            foregroundColor: OmegaColors.bgPrimary,
            elevation: 0,
            padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            textStyle: const TextStyle(
              fontWeight: FontWeight.bold,
              letterSpacing: 1.5,
              fontSize: 12,
              fontFamily: 'monospace',
            ),
          ),
        ),
        dividerTheme: const DividerThemeData(
          color: OmegaColors.bgCardBorder,
          thickness: 1,
        ),
        cardTheme: CardThemeData(
          color: OmegaColors.bgCard,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: const BorderSide(color: OmegaColors.bgCardBorder),
          ),
        ),
      );
}

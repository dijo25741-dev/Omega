// lib/main.dart
// Omega Mobile Guardian — Entry Point
// External Human Trust Authenticator for critical OT/SCADA infrastructure

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'theme/omega_theme.dart';
import 'screens/splash_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  // Force portrait orientation — mobile guardian is portrait-optimized
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Dark status bar to match cyber theme
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: Color(0xFF090A0F),
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );

  // Initialize flutter_animate default settings
  Animate.defaultDuration = 400.ms;

  runApp(const MobileGuardianApp());
}

class MobileGuardianApp extends StatelessWidget {
  const MobileGuardianApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Omega Mobile Guardian',
      debugShowCheckedModeBanner: false,
      theme: OmegaTheme.dark,

      // Splash → Login → Dashboard
      home: const SplashScreen(),

      // Smooth page transitions
      builder: (context, child) {
        return MediaQuery(
          // Prevent text scaling from system settings breaking the UI
          data: MediaQuery.of(context).copyWith(
            textScaler: const TextScaler.linear(1.0),
          ),
          child: child!,
        );
      },
    );
  }
}
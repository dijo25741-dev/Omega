// lib/screens/splash_screen.dart
// Animated cyber boot sequence splash screen

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../theme/omega_theme.dart';
import 'login_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  final List<String> _bootLines = [
    '> OMEGA TRUST v2.0 — INITIALIZING...',
    '> CRYPTOGRAPHIC CORE: LOADED',
    '> HARDWARE BINDING: SHA256_3A9C7...',
    '> SECURE CHANNEL: AES-256-GCM READY',
    '> AI INTEGRITY ENGINE: ONLINE',
    '> MOBILE GUARDIAN: AUTHENTICATED',
    '',
    '> DEVICE BOUND TO OMEGA NETWORK.',
    '> AWAITING OPERATOR CREDENTIALS...',
  ];

  int _visibleLines = 0;
  bool _showButton = false;

  @override
  void initState() {
    super.initState();
    _runBootSequence();
  }

  Future<void> _runBootSequence() async {
    for (int i = 0; i < _bootLines.length; i++) {
      await Future.delayed(Duration(milliseconds: i == 0 ? 600 : 250));
      if (mounted) {
        setState(() => _visibleLines = i + 1);
      }
    }
    await Future.delayed(const Duration(milliseconds: 500));
    if (mounted) setState(() => _showButton = true);
  }

  void _proceed() {
    Navigator.pushReplacement(
      context,
      PageRouteBuilder(
        pageBuilder: (_, animation, __) => const LoginScreen(),
        transitionsBuilder: (_, animation, __, child) {
          return FadeTransition(opacity: animation, child: child);
        },
        transitionDuration: const Duration(milliseconds: 600),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: OmegaColors.bgPrimary,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(28.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Spacer(),

              // ── Logo ────────────────────────────────────────────────
              Center(
                child: Column(
                  children: [
                    // Shield icon with glow
                    Container(
                      width: 90,
                      height: 90,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: OmegaColors.cyanSurface,
                        border: Border.all(color: OmegaColors.cyan, width: 1.5),
                        boxShadow: [
                          BoxShadow(
                            color: OmegaColors.cyan.withAlpha(80),
                            blurRadius: 24,
                            spreadRadius: 4,
                          ),
                        ],
                      ),
                      child: const Icon(
                        Icons.shield_outlined,
                        color: OmegaColors.cyan,
                        size: 44,
                      ),
                    )
                        .animate(onPlay: (c) => c.repeat(reverse: true))
                        .custom(
                          duration: 2000.ms,
                          builder: (context, value, child) => Container(
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              boxShadow: [
                                BoxShadow(
                                  color: OmegaColors.cyan
                                      .withAlpha((40 + (value * 80)).toInt()),
                                  blurRadius: 24 + value * 12,
                                  spreadRadius: 2 + value * 4,
                                ),
                              ],
                            ),
                            child: child,
                          ),
                        ),

                    const SizedBox(height: 20),

                    Text(
                      'OMEGA GUARDIAN',
                      style: TextStyle(
                        fontFamily: 'JetBrains Mono',
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 4.0,
                        color: OmegaColors.textPrimary,
                      ),
                    ).animate().fadeIn(delay: 200.ms, duration: 600.ms),

                    const SizedBox(height: 6),

                    Text(
                      'EXTERNAL HUMAN TRUST AUTHENTICATOR',
                      style: TextStyle(
                        fontFamily: 'JetBrains Mono',
                        fontSize: 9,
                        letterSpacing: 2.0,
                        color: OmegaColors.cyan,
                      ),
                    ).animate().fadeIn(delay: 500.ms, duration: 600.ms),
                  ],
                ),
              ),

              const SizedBox(height: 48),

              // ── Boot terminal ────────────────────────────────────────
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: OmegaColors.bgSecondary,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: OmegaColors.bgCardBorder),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Terminal title bar
                    Row(
                      children: [
                        _dot(OmegaColors.danger),
                        const SizedBox(width: 5),
                        _dot(OmegaColors.warning),
                        const SizedBox(width: 5),
                        _dot(OmegaColors.safe),
                        const SizedBox(width: 10),
                        const Text(
                          'omega-boot — secure terminal',
                          style: TextStyle(
                            fontFamily: 'JetBrains Mono',
                            fontSize: 9,
                            color: OmegaColors.textMuted,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // Boot lines
                    ...List.generate(_visibleLines, (i) {
                      final line = _bootLines[i];
                      final isLast =
                          i == _visibleLines - 1 && _visibleLines < _bootLines.length;
                      final isGreen = line.contains('ONLINE') ||
                          line.contains('LOADED') ||
                          line.contains('READY') ||
                          line.contains('AUTHENTICATED');

                      return Row(
                        children: [
                          Expanded(
                            child: Text(
                              line.isEmpty ? ' ' : line,
                              style: TextStyle(
                                fontFamily: 'JetBrains Mono',
                                fontSize: 10.5,
                                height: 1.8,
                                color: isGreen
                                    ? OmegaColors.safe
                                    : line.contains('AWAITING')
                                        ? OmegaColors.cyan
                                        : OmegaColors.textSecondary,
                              ),
                            ),
                          ),
                          if (isLast)
                            Container(
                              width: 8,
                              height: 13,
                              color: OmegaColors.cyan,
                            )
                                .animate(onPlay: (c) => c.repeat(reverse: true))
                                .fadeIn(duration: 400.ms)
                                .then()
                                .fadeOut(duration: 400.ms),
                        ],
                      ).animate().fadeIn(duration: 200.ms);
                    }),
                  ],
                ),
              ),

              const Spacer(),

              // ── Enter button ─────────────────────────────────────────
              if (_showButton)
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _proceed,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: OmegaColors.cyan,
                      foregroundColor: OmegaColors.bgPrimary,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: const Text(
                      'ENTER SECURE ZONE',
                      style: TextStyle(
                        fontFamily: 'JetBrains Mono',
                        fontWeight: FontWeight.bold,
                        letterSpacing: 2.0,
                        fontSize: 12,
                        color: OmegaColors.bgPrimary,
                      ),
                    ),
                  ),
                ).animate().fadeIn(duration: 500.ms).slideY(begin: 0.3, end: 0),

              const SizedBox(height: 20),

              // Device fingerprint footer
              Center(
                child: Text(
                  'DEVICE: SHA256_FINGERPRINT_3A9C7B2E',
                  style: TextStyle(
                    fontFamily: 'JetBrains Mono',
                    fontSize: 8,
                    color: OmegaColors.textMuted,
                    letterSpacing: 1.0,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _dot(Color color) => Container(
        width: 10,
        height: 10,
        decoration: BoxDecoration(color: color, shape: BoxShape.circle),
      );
}
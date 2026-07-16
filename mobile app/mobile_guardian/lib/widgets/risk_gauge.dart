// lib/widgets/risk_gauge.dart
// Animated risk gauge widget — linear progress bar with glow effect

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../theme/omega_theme.dart';

class RiskGauge extends StatelessWidget {
  final double value; // 0–100
  final String level;
  final bool animated;

  const RiskGauge({
    super.key,
    required this.value,
    required this.level,
    this.animated = true,
  });

  @override
  Widget build(BuildContext context) {
    final color = OmegaColors.riskColor(level);
    final clampedValue = (value / 100.0).clamp(0.0, 1.0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'CYBER IMMUNITY RISK METER',
              style: TextStyle(
                fontFamily: 'JetBrains Mono',
                fontSize: 9,
                letterSpacing: 1.5,
                color: OmegaColors.textMuted,
              ),
            ),
            _RiskBadge(level: level, value: value),
          ],
        ),
        const SizedBox(height: 8),
        Container(
          height: 10,
          decoration: BoxDecoration(
            color: OmegaColors.bgCard,
            borderRadius: BorderRadius.circular(5),
            border: Border.all(color: OmegaColors.bgCardBorder),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(5),
            child: TweenAnimationBuilder<double>(
              tween: Tween(begin: 0.0, end: clampedValue),
              duration: const Duration(milliseconds: 800),
              curve: Curves.easeOutCubic,
              builder: (context, animatedValue, _) {
                return Stack(
                  children: [
                    FractionallySizedBox(
                      alignment: Alignment.centerLeft,
                      widthFactor: animatedValue,
                      child: Container(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              color.withAlpha(180),
                              color,
                            ],
                          ),
                          boxShadow: level == 'CRITICAL'
                              ? [
                                  BoxShadow(
                                    color: color.withAlpha(120),
                                    blurRadius: 8,
                                    spreadRadius: 2,
                                  )
                                ]
                              : [],
                        ),
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        ),
      ],
    );
  }
}

class _RiskBadge extends StatelessWidget {
  final String level;
  final double value;

  const _RiskBadge({required this.level, required this.value});

  @override
  Widget build(BuildContext context) {
    final color = OmegaColors.riskColor(level);
    final surface = OmegaColors.riskSurface(level);
    final isCritical = level == 'CRITICAL';

    Widget badge = Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: surface,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withAlpha(100)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
              boxShadow: [BoxShadow(color: color.withAlpha(150), blurRadius: 4)],
            ),
          ),
          const SizedBox(width: 5),
          Text(
            '$level — ${value.toStringAsFixed(0)}%',
            style: TextStyle(
              fontFamily: 'JetBrains Mono',
              fontSize: 9,
              fontWeight: FontWeight.bold,
              color: color,
              letterSpacing: 1.0,
            ),
          ),
        ],
      ),
    );

    if (isCritical) {
      return badge
          .animate(onPlay: (c) => c.repeat(reverse: true))
          .fadeIn(duration: 400.ms)
          .then()
          .fadeOut(duration: 400.ms);
    }
    return badge;
  }
}

/// Circular status indicator with pulsing ring for emergencies
class StatusOrb extends StatelessWidget {
  final bool isCompromised;
  final double size;

  const StatusOrb({
    super.key,
    required this.isCompromised,
    this.size = 80,
  });

  @override
  Widget build(BuildContext context) {
    final color = isCompromised ? OmegaColors.critical : OmegaColors.safe;

    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          if (isCompromised)
            Container(
              width: size,
              height: size,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: color.withAlpha(60), width: 1),
              ),
            )
                .animate(onPlay: (c) => c.repeat())
                .scale(
                  begin: const Offset(0.8, 0.8),
                  end: const Offset(1.4, 1.4),
                  duration: 1200.ms,
                  curve: Curves.easeOut,
                )
                .fadeOut(duration: 1200.ms),
          Container(
            width: size * 0.7,
            height: size * 0.7,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isCompromised
                  ? OmegaColors.criticalSurface
                  : OmegaColors.safeSurface,
              border: Border.all(color: color, width: 1.5),
              boxShadow: [
                BoxShadow(color: color.withAlpha(80), blurRadius: 12, spreadRadius: 2),
              ],
            ),
            child: Icon(
              isCompromised ? Icons.warning_amber_rounded : Icons.verified_user_outlined,
              color: color,
              size: size * 0.35,
            ),
          ),
        ],
      ),
    );
  }
}

// lib/widgets/confidence_gauge.dart
// Animated semi-circular AI confidence gauge with custom painter

import 'dart:math';
import 'package:flutter/material.dart';
import '../theme/omega_theme.dart';

class ConfidenceGauge extends StatelessWidget {
  final double confidence; // 0–100
  final double size;

  const ConfidenceGauge({
    super.key,
    required this.confidence,
    this.size = 140,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size * 0.65,
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: 0.0, end: confidence),
        duration: const Duration(milliseconds: 1200),
        curve: Curves.easeOutCubic,
        builder: (context, animatedValue, _) {
          return CustomPaint(
            size: Size(size, size * 0.65),
            painter: _GaugePainter(
              value: animatedValue,
              bgColor: OmegaColors.bgCard,
              borderColor: OmegaColors.bgCardBorder,
            ),
            child: Align(
              alignment: const Alignment(0, 0.6),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '${animatedValue.toStringAsFixed(1)}%',
                    style: TextStyle(
                      fontFamily: 'JetBrains Mono',
                      fontSize: size * 0.15,
                      fontWeight: FontWeight.bold,
                      color: _gaugeColor(animatedValue),
                    ),
                  ),
                  Text(
                    'AI CONFIDENCE',
                    style: TextStyle(
                      fontFamily: 'JetBrains Mono',
                      fontSize: size * 0.055,
                      color: OmegaColors.textMuted,
                      letterSpacing: 1.5,
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  static Color _gaugeColor(double value) {
    if (value >= 90) return OmegaColors.safe;
    if (value >= 70) return OmegaColors.cyan;
    if (value >= 50) return OmegaColors.warning;
    return OmegaColors.danger;
  }
}

class _GaugePainter extends CustomPainter {
  final double value; // 0–100
  final Color bgColor;
  final Color borderColor;

  _GaugePainter({
    required this.value,
    required this.bgColor,
    required this.borderColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height * 0.9);
    final radius = size.width * 0.42;
    const startAngle = pi;
    const sweepAngle = pi;
    final valueSweep = (value / 100.0).clamp(0.0, 1.0) * pi;

    // Background arc
    final bgPaint = Paint()
      ..color = bgColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 12
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      sweepAngle,
      false,
      bgPaint,
    );

    // Border arc
    final borderPaint = Paint()
      ..color = borderColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 14
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      sweepAngle,
      false,
      borderPaint,
    );

    // Value arc with gradient
    final color = ConfidenceGauge._gaugeColor(value);
    final valuePaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 10
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      valueSweep,
      false,
      valuePaint,
    );

    // Glow on the value arc
    final glowPaint = Paint()
      ..color = color.withAlpha(40)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 20
      ..strokeCap = StrokeCap.round
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 6);

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      valueSweep,
      false,
      glowPaint,
    );

    // Needle dot at the end of value arc
    final needleAngle = startAngle + valueSweep;
    final needleX = center.dx + radius * cos(needleAngle);
    final needleY = center.dy + radius * sin(needleAngle);

    final dotPaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;

    canvas.drawCircle(Offset(needleX, needleY), 5, dotPaint);

    final dotGlow = Paint()
      ..color = color.withAlpha(100)
      ..style = PaintingStyle.fill
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4);

    canvas.drawCircle(Offset(needleX, needleY), 8, dotGlow);
  }

  @override
  bool shouldRepaint(covariant _GaugePainter oldDelegate) {
    return oldDelegate.value != value;
  }
}

// lib/widgets/timeline_card.dart
// Individual timeline event card with severity badge

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../models/system_state.dart';
import '../theme/omega_theme.dart';

class TimelineCard extends StatelessWidget {
  final TimelineEvent event;
  final int index;

  const TimelineCard({super.key, required this.event, required this.index});

  @override
  Widget build(BuildContext context) {
    final color = OmegaColors.severityColor(event.severity);
    final isCritical = event.severity.toLowerCase() == 'critical';

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isCritical
            ? OmegaColors.criticalSurface.withAlpha(180)
            : OmegaColors.bgCard,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: isCritical ? OmegaColors.critical.withAlpha(100) : OmegaColors.bgCardBorder,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Severity indicator bar
          Container(
            width: 3,
            height: 40,
            margin: const EdgeInsets.only(right: 10),
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(2),
              boxShadow: [BoxShadow(color: color.withAlpha(80), blurRadius: 4)],
            ),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      event.time,
                      style: const TextStyle(
                        fontFamily: 'JetBrains Mono',
                        fontSize: 9,
                        color: OmegaColors.textMuted,
                        letterSpacing: 0.5,
                      ),
                    ),
                    _SeverityBadge(severity: event.severity, color: color),
                  ],
                ),
                const SizedBox(height: 5),
                Text(
                  event.event,
                  style: TextStyle(
                    fontFamily: 'JetBrains Mono',
                    fontSize: 10.5,
                    color: isCritical ? OmegaColors.textPrimary : OmegaColors.textSecondary,
                    height: 1.5,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    )
        .animate(delay: Duration(milliseconds: index * 30))
        .fadeIn(duration: 300.ms)
        .slideX(begin: 0.1, end: 0, duration: 300.ms);
  }
}

class _SeverityBadge extends StatelessWidget {
  final String severity;
  final Color color;

  const _SeverityBadge({required this.severity, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withAlpha(30),
        borderRadius: BorderRadius.circular(3),
        border: Border.all(color: color.withAlpha(80)),
      ),
      child: Text(
        severity.toUpperCase(),
        style: TextStyle(
          fontFamily: 'JetBrains Mono',
          fontSize: 8,
          fontWeight: FontWeight.bold,
          color: color,
          letterSpacing: 1.0,
        ),
      ),
    );
  }
}

/// Compact metric tile for status values (pump, valve, flow rate, etc.)
class MetricTile extends StatelessWidget {
  final String label;
  final String value;
  final Color? valueColor;
  final IconData? icon;

  const MetricTile({
    super.key,
    required this.label,
    required this.value,
    this.valueColor,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: OmegaColors.bgCard,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: OmegaColors.bgCardBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (icon != null) ...[
                Icon(icon, size: 10, color: OmegaColors.textMuted),
                const SizedBox(width: 4),
              ],
              Text(
                label,
                style: const TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 8,
                  color: OmegaColors.textMuted,
                  letterSpacing: 1.0,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            value,
            style: TextStyle(
              fontFamily: 'JetBrains Mono',
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: valueColor ?? OmegaColors.textPrimary,
            ),
          ),
        ],
      ),
    );
  }
}

/// Section card container
class OmegaCard extends StatelessWidget {
  final String? title;
  final IconData? titleIcon;
  final Color? titleIconColor;
  final Widget child;
  final EdgeInsets? padding;

  const OmegaCard({
    super.key,
    this.title,
    this.titleIcon,
    this.titleIconColor,
    required this.child,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: OmegaColors.bgCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: OmegaColors.bgCardBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (title != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 0),
              child: Row(
                children: [
                  if (titleIcon != null) ...[
                    Icon(titleIcon, size: 14, color: titleIconColor ?? OmegaColors.cyan),
                    const SizedBox(width: 8),
                  ],
                  Text(
                    title!.toUpperCase(),
                    style: const TextStyle(
                      fontFamily: 'JetBrains Mono',
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: OmegaColors.textSecondary,
                      letterSpacing: 2.0,
                    ),
                  ),
                ],
              ),
            ),
          if (title != null) const Divider(height: 16, indent: 16, endIndent: 16),
          Padding(
            padding: padding ?? const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: child,
          ),
        ],
      ),
    );
  }
}

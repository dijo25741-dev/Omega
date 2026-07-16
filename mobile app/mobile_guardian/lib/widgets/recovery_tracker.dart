// lib/widgets/recovery_tracker.dart
// Recovery Progress Tracker Widget - Displays vertical stepper checklist for recovery steps

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../models/system_state.dart';
import '../theme/omega_theme.dart';

class RecoveryTracker extends StatelessWidget {
  final List<RecoveryStep> steps;

  const RecoveryTracker({super.key, required this.steps});

  @override
  Widget build(BuildContext context) {
    if (steps.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: OmegaColors.bgCard,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: OmegaColors.bgCardBorder),
        ),
        child: const Center(
          child: Text(
            'NO RUNNING RECOVERY OPERATIONS',
            style: TextStyle(
              fontFamily: 'JetBrains Mono',
              fontSize: 10,
              color: OmegaColors.textMuted,
              letterSpacing: 1.0,
            ),
          ),
        ),
      );
    }

    return Container(
      decoration: BoxDecoration(
        color: OmegaColors.bgCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: OmegaColors.bgCardBorder),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.loop_outlined, size: 14, color: OmegaColors.cyan),
              const SizedBox(width: 8),
              const Text(
                'SYSTEM RECOVERY STATUS',
                style: TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: OmegaColors.textSecondary,
                  letterSpacing: 1.5,
                ),
              ),
            ],
          ),
          const Divider(height: 16, color: OmegaColors.bgCardBorder),
          const SizedBox(height: 4),
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: steps.length,
            itemBuilder: (context, index) {
              final step = steps[index];
              final isLast = index == steps.length - 1;
              return _buildStepRow(step, isLast, index);
            },
          ),
        ],
      ),
    );
  }

  Widget _buildStepRow(RecoveryStep step, bool isLast, int index) {
    Color iconColor = OmegaColors.textMuted;
    IconData icon = Icons.circle_outlined;
    bool inProgress = false;

    if (step.status == 'done') {
      iconColor = OmegaColors.safe;
      icon = Icons.check_circle_outlined;
    } else if (step.status == 'in_progress') {
      iconColor = OmegaColors.warning;
      icon = Icons.pending_outlined;
      inProgress = true;
    }

    Widget iconWidget = Icon(icon, size: 16, color: iconColor);

    if (inProgress) {
      iconWidget = iconWidget
          .animate(onPlay: (c) => c.repeat(reverse: true))
          .scale(begin: const Offset(0.9, 0.9), end: const Offset(1.15, 1.15), duration: 800.ms)
          .fadeIn(duration: 800.ms)
          .then()
          .fadeOut(duration: 800.ms);
    }

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            children: [
              iconWidget,
              if (!isLast)
                Expanded(
                  child: Container(
                    width: 1.5,
                    color: step.status == 'done' ? OmegaColors.safe : OmegaColors.bgCardBorder,
                    margin: const EdgeInsets.symmetric(vertical: 4),
                  ),
                ),
            ],
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    step.label.toUpperCase(),
                    style: TextStyle(
                      fontFamily: 'JetBrains Mono',
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                      color: step.status == 'pending'
                          ? OmegaColors.textMuted
                          : OmegaColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    step.status == 'done'
                        ? 'COMPLETED'
                        : step.status == 'in_progress'
                            ? 'IN PROGRESS...'
                            : 'AWAITING SEQUENCE',
                    style: TextStyle(
                      fontFamily: 'JetBrains Mono',
                      fontSize: 8,
                      color: iconColor,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.5,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

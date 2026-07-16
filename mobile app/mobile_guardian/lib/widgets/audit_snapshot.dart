// lib/widgets/audit_snapshot.dart
// Audit Snapshot Widget - Displays incident summary bottom sheet for forensic report

import 'package:flutter/material.dart';
import '../models/system_state.dart';
import '../theme/omega_theme.dart';

Future<void> showAuditSnapshot(BuildContext context, SystemState state, String decision) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (_) => _AuditSnapshotContent(state: state, decision: decision),
  );
}

class _AuditSnapshotContent extends StatelessWidget {
  final SystemState state;
  final String decision;

  const _AuditSnapshotContent({required this.state, required this.decision});

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final timeStr = "${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}:${now.second.toString().padLeft(2, '0')}";

    return Container(
      decoration: const BoxDecoration(
        color: OmegaColors.bgSecondary,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        border: Border(
          top: BorderSide(color: OmegaColors.cyan, width: 1),
          left: BorderSide(color: OmegaColors.bgCardBorder, width: 1),
          right: BorderSide(color: OmegaColors.bgCardBorder, width: 1),
        ),
      ),
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
        top: 16,
        left: 24,
        right: 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Handle bar
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: OmegaColors.bgCardBorder,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.assignment_turned_in_outlined, color: OmegaColors.cyan, size: 18),
              const SizedBox(width: 8),
              const Text(
                'INCIDENT FORENSIC REPORT',
                style: TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: OmegaColors.textPrimary,
                  letterSpacing: 1.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          const Center(
            child: Text(
              'COMPLIANCE & AUDIT SNAPSHOT GENERATED',
              style: TextStyle(
                fontFamily: 'JetBrains Mono',
                fontSize: 8,
                color: OmegaColors.textMuted,
                letterSpacing: 0.5,
              ),
            ),
          ),
          const Divider(height: 24, color: OmegaColors.bgCardBorder),

          // Incident details
          _buildDetailRow('INCIDENT TIME', timeStr),
          const SizedBox(height: 10),
          _buildDetailRow('SECURITY VECTOR', state.compromiseType.replaceAll('_', ' ')),
          const SizedBox(height: 10),
          _buildDetailRow('PENDING ACTION', state.pendingEmergencyCommand ?? 'SYSTEM OVERRIDE'),
          const SizedBox(height: 10),
          _buildDetailRow('OPERATOR DECISION', decision, valueColor: decision == 'APPROVE' ? OmegaColors.safe : OmegaColors.danger),
          const SizedBox(height: 10),
          _buildDetailRow('AI CORE CONFIDENCE', '${state.aiExplanation.confidence}%'),
          const SizedBox(height: 10),
          _buildDetailRow('DEVICE FINGERPRINT', 'SHA256_FINGERPRINT_3a9c7'),
          
          const Divider(height: 24, color: OmegaColors.bgCardBorder),

          // Compliance note
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: OmegaColors.bgCard,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: OmegaColors.bgCardBorder),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.info_outline, size: 14, color: OmegaColors.textMuted),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'This cryptographic report has been signed by the Mobile Guardian hardware trust anchor and committed to the SCADA system ledger for non-repudiation and forensic logging.',
                    style: TextStyle(
                      fontFamily: 'JetBrains Mono',
                      fontSize: 9,
                      color: OmegaColors.textSecondary,
                      height: 1.5,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Close button
          ElevatedButton(
            onPressed: () => Navigator.of(context).pop(),
            style: ElevatedButton.styleFrom(
              backgroundColor: OmegaColors.bgCardBorder,
              foregroundColor: OmegaColors.textPrimary,
              elevation: 0,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: const Text(
              'DISMISS REPORT',
              style: TextStyle(
                fontFamily: 'JetBrains Mono',
                fontWeight: FontWeight.bold,
                letterSpacing: 1.0,
                fontSize: 11,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value, {Color? valueColor}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontFamily: 'JetBrains Mono',
            fontSize: 9,
            color: OmegaColors.textMuted,
            letterSpacing: 0.5,
          ),
        ),
        Text(
          value,
          style: TextStyle(
            fontFamily: 'JetBrains Mono',
            fontSize: 10,
            fontWeight: FontWeight.bold,
            color: valueColor ?? OmegaColors.textPrimary,
          ),
        ),
      ],
    );
  }
}

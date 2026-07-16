// lib/widgets/device_trust_card.dart
// Device Trust Verification Widget - Location, Registration, Hardware binding check

import 'package:flutter/material.dart';
import '../theme/omega_theme.dart';

class DeviceTrustCard extends StatelessWidget {
  const DeviceTrustCard({super.key});

  @override
  Widget build(BuildContext context) {
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
              const Icon(Icons.verified_user_outlined, size: 14, color: OmegaColors.cyan),
              const SizedBox(width: 8),
              const Text(
                'DEVICE TRUST VERIFICATION',
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
          _buildTrustRow(
            icon: Icons.fingerprint,
            label: 'Hardware Binding',
            value: 'SHA256_FINGERPRINT_3a9c7',
            status: 'Verified ✓',
            statusColor: OmegaColors.safe,
          ),
          const SizedBox(height: 12),
          _buildTrustRow(
            icon: Icons.location_on_outlined,
            label: 'Operator Location',
            value: 'Verified GPS Boundary',
            status: 'Within Perimeter ✓',
            statusColor: OmegaColors.safe,
          ),
          const SizedBox(height: 12),
          _buildTrustRow(
            icon: Icons.phone_android_outlined,
            label: 'Registration Key',
            value: 'Trust Anchor Cryptographic Signature',
            status: 'Authorized ✓',
            statusColor: OmegaColors.safe,
          ),
        ],
      ),
    );
  }

  Widget _buildTrustRow({
    required IconData icon,
    required String label,
    required String value,
    required String status,
    required Color statusColor,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 16, color: OmegaColors.textMuted),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label.toUpperCase(),
                style: const TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 8,
                  color: OmegaColors.textMuted,
                  letterSpacing: 0.5,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                style: const TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 10,
                  color: OmegaColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
        Text(
          status,
          style: TextStyle(
            fontFamily: 'JetBrains Mono',
            fontSize: 9,
            fontWeight: FontWeight.bold,
            color: statusColor,
          ),
        ),
      ],
    );
  }
}

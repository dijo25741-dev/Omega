// lib/widgets/pin_dialog.dart
// Multi-Factor Authentication — PIN + Biometric simulation for emergency approval

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../theme/omega_theme.dart';

/// Shows a multi-factor auth dialog: PIN entry + fingerprint hold
/// Returns true if authentication succeeds, false/null otherwise
Future<bool?> showPinDialog(BuildContext context) {
  return showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (_) => const _PinDialogContent(),
  );
}

class _PinDialogContent extends StatefulWidget {
  const _PinDialogContent();

  @override
  State<_PinDialogContent> createState() => _PinDialogContentState();
}

class _PinDialogContentState extends State<_PinDialogContent> {
  String _pin = '';
  bool _pinVerified = false;
  bool _biometricActive = false;
  double _biometricProgress = 0.0;
  Timer? _biometricTimer;
  String _errorMsg = '';
  static const String _correctPin = '1234';

  @override
  void dispose() {
    _biometricTimer?.cancel();
    super.dispose();
  }

  void _onDigit(String digit) {
    if (_pin.length >= 4) return;
    setState(() {
      _pin += digit;
      _errorMsg = '';
    });
    if (_pin.length == 4) {
      _verifyPin();
    }
  }

  void _onDelete() {
    if (_pin.isEmpty) return;
    setState(() {
      _pin = _pin.substring(0, _pin.length - 1);
      _errorMsg = '';
    });
  }

  void _verifyPin() {
    if (_pin == _correctPin) {
      setState(() => _pinVerified = true);
    } else {
      setState(() {
        _errorMsg = 'INVALID PIN — ACCESS DENIED';
        _pin = '';
      });
    }
  }

  void _startBiometric() {
    setState(() => _biometricActive = true);
    _biometricTimer = Timer.periodic(const Duration(milliseconds: 50), (timer) {
      setState(() {
        _biometricProgress += 0.033; // ~1.5 seconds to complete
      });
      if (_biometricProgress >= 1.0) {
        timer.cancel();
        Navigator.of(context).pop(true);
      }
    });
  }

  void _cancelBiometric() {
    _biometricTimer?.cancel();
    setState(() {
      _biometricActive = false;
      _biometricProgress = 0.0;
    });
  }

  @override
  Widget build(BuildContext context) {
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
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
        top: 16,
        left: 24,
        right: 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Handle bar
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: OmegaColors.bgCardBorder,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 16),

          // Title
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.security, color: OmegaColors.cyan, size: 18),
              const SizedBox(width: 8),
              const Text(
                'MULTI-FACTOR VERIFICATION',
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
          const SizedBox(height: 6),
          Text(
            _pinVerified ? 'STEP 2: BIOMETRIC CONFIRMATION' : 'STEP 1: ENTER SECURITY PIN',
            style: TextStyle(
              fontFamily: 'JetBrains Mono',
              fontSize: 9,
              color: _pinVerified ? OmegaColors.safe : OmegaColors.textMuted,
              letterSpacing: 1.0,
            ),
          ),
          const SizedBox(height: 20),

          if (!_pinVerified) ...[
            // PIN dots
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(4, (i) {
                final filled = i < _pin.length;
                return Container(
                  width: 16,
                  height: 16,
                  margin: const EdgeInsets.symmetric(horizontal: 8),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: filled ? OmegaColors.cyan : Colors.transparent,
                    border: Border.all(
                      color: filled ? OmegaColors.cyan : OmegaColors.bgCardBorder,
                      width: 1.5,
                    ),
                    boxShadow: filled
                        ? [BoxShadow(color: OmegaColors.cyan.withAlpha(80), blurRadius: 6)]
                        : [],
                  ),
                );
              }),
            ),

            if (_errorMsg.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                _errorMsg,
                style: const TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 10,
                  color: OmegaColors.danger,
                  letterSpacing: 0.5,
                ),
              ).animate().shakeX(hz: 4, amount: 3, duration: 300.ms),
            ],

            const SizedBox(height: 20),

            // Numpad
            _buildNumpad(),
          ] else ...[
            // Biometric fingerprint hold
            _buildBiometricSection(),
          ],

          const SizedBox(height: 12),
        ],
      ),
    );
  }

  Widget _buildNumpad() {
    final rows = [
      ['1', '2', '3'],
      ['4', '5', '6'],
      ['7', '8', '9'],
      ['', '0', '⌫'],
    ];

    return Column(
      children: rows.map((row) {
        return Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: row.map((key) {
            if (key.isEmpty) {
              return const SizedBox(width: 72, height: 52);
            }
            return GestureDetector(
              onTap: () {
                if (key == '⌫') {
                  _onDelete();
                } else {
                  _onDigit(key);
                }
              },
              child: Container(
                width: 72,
                height: 52,
                margin: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: OmegaColors.bgCard,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: OmegaColors.bgCardBorder),
                ),
                child: Center(
                  child: Text(
                    key,
                    style: TextStyle(
                      fontFamily: 'JetBrains Mono',
                      fontSize: key == '⌫' ? 18 : 20,
                      fontWeight: FontWeight.bold,
                      color: OmegaColors.textPrimary,
                    ),
                  ),
                ),
              ),
            );
          }).toList(),
        );
      }).toList(),
    ).animate().fadeIn(duration: 300.ms);
  }

  Widget _buildBiometricSection() {
    return Column(
      children: [
        // Checkmark for PIN
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.check_circle, color: OmegaColors.safe, size: 14),
            const SizedBox(width: 6),
            const Text(
              'PIN VERIFIED',
              style: TextStyle(
                fontFamily: 'JetBrains Mono',
                fontSize: 10,
                color: OmegaColors.safe,
                letterSpacing: 1.0,
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),

        // Fingerprint circle
        GestureDetector(
          onTapDown: (_) => _startBiometric(),
          onTapUp: (_) => _cancelBiometric(),
          onTapCancel: _cancelBiometric,
          child: SizedBox(
            width: 120,
            height: 120,
            child: Stack(
              alignment: Alignment.center,
              children: [
                // Progress ring
                SizedBox(
                  width: 110,
                  height: 110,
                  child: CircularProgressIndicator(
                    value: _biometricProgress,
                    strokeWidth: 3,
                    backgroundColor: OmegaColors.bgCardBorder,
                    valueColor: AlwaysStoppedAnimation<Color>(
                      _biometricProgress > 0.7 ? OmegaColors.safe : OmegaColors.cyan,
                    ),
                  ),
                ),
                // Fingerprint icon
                Container(
                  width: 90,
                  height: 90,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _biometricActive ? OmegaColors.cyanSurface : OmegaColors.bgCard,
                    border: Border.all(
                      color: _biometricActive ? OmegaColors.cyan : OmegaColors.bgCardBorder,
                      width: 1.5,
                    ),
                    boxShadow: _biometricActive
                        ? [BoxShadow(color: OmegaColors.cyan.withAlpha(60), blurRadius: 12)]
                        : [],
                  ),
                  child: Icon(
                    Icons.fingerprint,
                    size: 44,
                    color: _biometricActive ? OmegaColors.cyan : OmegaColors.textMuted,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Text(
          _biometricActive ? 'SCANNING BIOMETRIC...' : 'HOLD TO VERIFY IDENTITY',
          style: TextStyle(
            fontFamily: 'JetBrains Mono',
            fontSize: 10,
            color: _biometricActive ? OmegaColors.cyan : OmegaColors.textMuted,
            letterSpacing: 1.0,
          ),
        ),
      ],
    ).animate().fadeIn(duration: 400.ms);
  }
}

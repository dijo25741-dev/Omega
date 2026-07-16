// lib/screens/guardian_dashboard.dart
// Main Laptop Guardian Dashboard — CPU/RAM/Battery metrics, Process Manager, and Remote Commands

import 'dart:async';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../models/system_state.dart';
import '../services/api_service.dart';
import '../theme/omega_theme.dart';
import '../widgets/risk_gauge.dart';
import '../widgets/timeline_card.dart';
import '../widgets/pin_dialog.dart';
import '../widgets/confidence_gauge.dart';
import '../widgets/device_trust_card.dart';
import '../widgets/recovery_tracker.dart';
import '../widgets/audit_snapshot.dart';
import 'login_screen.dart';

class GuardianDashboard extends StatefulWidget {
  final String token;
  final ApiService api;

  const GuardianDashboard({
    super.key,
    required this.token,
    required this.api,
  });

  @override
  State<GuardianDashboard> createState() => _GuardianDashboardState();
}

class _GuardianDashboardState extends State<GuardianDashboard>
    with TickerProviderStateMixin {
  SystemState _state = const SystemState();
  List<RecoveryStep> _recoverySteps = [];
  bool _isSubmitting = false;
  String _decisionMessage = '';
  bool _decisionSuccess = false;
  
  Timer? _pollTimer;
  Timer? _countdownTimer;
  int _countdownSeconds = 30;
  bool _offlineMode = false;
  String? _lastOfflineCheckTime;
  
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 5, vsync: this); // OVERVIEW, PROCESSES, EMERGENCY, TIMELINE, MOUSE
    _fetchStatus();
    _pollTimer = Timer.periodic(const Duration(seconds: 3), (_) => _fetchStatus());
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _countdownTimer?.cancel();
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _fetchStatus() async {
    try {
      final status = await widget.api.checkIntegrity();
      if (mounted) {
        setState(() {
          _state = status;
          _offlineMode = false;
        });
        
        if (_state.isEmergency && _countdownTimer == null) {
          _startCountdown();
        } else if (!_state.isEmergency && _countdownTimer != null) {
          _stopCountdown();
        }

        if (!_state.isEmergency) {
          _fetchRecoveryStatus();
        }
      }
    } catch (_) {
      final cached = await widget.api.getCachedState();
      final cachedTime = await widget.api.getCachedStateTime();
      if (cached != null && mounted) {
        setState(() {
          _state = cached;
          _offlineMode = true;
          _lastOfflineCheckTime = cachedTime != null 
              ? DateTime.parse(cachedTime).toLocal().toString().substring(11, 19)
              : 'Unknown';
        });
      }
    }
  }

  Future<void> _fetchRecoveryStatus() async {
    try {
      final steps = await widget.api.getRecoveryStatus();
      if (mounted) {
        setState(() => _recoverySteps = steps);
      }
    } catch (_) {}
  }

  void _startCountdown() {
    setState(() => _countdownSeconds = 30);
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) {
        setState(() {
          if (_countdownSeconds > 0) {
            _countdownSeconds--;
          } else {
            _stopCountdown();
            _autoRejectEmergency();
          }
        });
      }
    });
  }

  void _stopCountdown() {
    _countdownTimer?.cancel();
    _countdownTimer = null;
  }

  Future<void> _autoRejectEmergency() async {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('TIMEOUT: Auto-rejecting critical command.'),
          backgroundColor: OmegaColors.critical,
        ),
      );
    }
    _submitDecision('REJECT', bypassMfa: true);
  }

  // Submit Emergency Approval/Rejection
  Future<void> _submitDecision(String decision, {bool bypassMfa = false}) async {
    if (!bypassMfa) {
      final mfaSuccess = await showPinDialog(context);
      if (mfaSuccess != true) return;
    }

    _stopCountdown();

    setState(() {
      _isSubmitting = true;
      _decisionMessage = '';
    });

    try {
      if (_offlineMode) {
        setState(() {
          _decisionMessage = 'OFFLINE MODE: Action queued locally.';
          _decisionSuccess = true;
        });
        await Future.delayed(const Duration(seconds: 1));
        return;
      }

      final result = await widget.api.respondToEmergency(decision, widget.token);
      if (mounted) {
        setState(() {
          _decisionMessage = result['message'] ?? 'Decision submitted: $decision';
          _decisionSuccess = true;
        });
        
        showAuditSnapshot(context, _state, decision);
        await Future.delayed(const Duration(milliseconds: 500));
        await _fetchStatus();
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _decisionMessage = e.message;
          _decisionSuccess = false;
        });
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  // Send System Commands (Lock, Mute, Kill, etc.)
  Future<void> _sendRemoteCommand(String command, {Map<String, dynamic> payload = const {}}) async {
    // Show MFA verification before running critical commands
    if (command == "SHUTDOWN" || command == "KILL_PROCESS") {
      final mfaSuccess = await showPinDialog(context);
      if (mfaSuccess != true) return;
    }

    try {
      final response = await widget.api.sendLaptopCommand(command, payload: payload);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(response['message'] ?? 'Command executed successfully.'),
            backgroundColor: OmegaColors.safe,
          ),
        );
        _fetchStatus();
      }
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.message),
            backgroundColor: OmegaColors.critical,
          ),
        );
      }
    }
  }

  Future<void> _triggerEmergency() async {
    try {
      await widget.api.triggerEmergency();
      await _fetchStatus();
    } catch (_) {}
  }

  Future<void> _triggerKillSwitch() async {
    try {
      await widget.api.killSwitch();
      await _fetchStatus();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('🚨 LOCKDOWN COMPLETED: Kill switch sent!'),
            backgroundColor: OmegaColors.critical,
          ),
        );
      }
    } catch (_) {}
  }

  void _logout() {
    _pollTimer?.cancel();
    _stopCountdown();
    Navigator.pushReplacement(
      context,
      PageRouteBuilder(
        pageBuilder: (_, animation, __) => const LoginScreen(),
        transitionsBuilder: (_, animation, __, child) =>
            FadeTransition(opacity: animation, child: child),
        transitionDuration: const Duration(milliseconds: 400),
      ),
    );
  }

  Color _getRiskAdaptiveBorderColor() {
    if (_offlineMode) return OmegaColors.warning;
    switch (_state.riskLevel.toUpperCase()) {
      case 'CRITICAL':
        return OmegaColors.critical;
      case 'HIGH':
        return const Color(0xFFF97316);
      case 'MEDIUM':
        return OmegaColors.warning;
      default:
        return OmegaColors.bgCardBorder;
    }
  }

  Widget _buildRestrictedAccessScreen() {
    return Container(
      color: OmegaColors.bgPrimary,
      padding: const EdgeInsets.all(24),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: OmegaColors.cyan.withOpacity(0.05),
                border: Border.all(color: OmegaColors.cyan.withOpacity(0.3), width: 2),
              ),
              child: const Icon(
                Icons.shield_outlined,
                size: 64,
                color: OmegaColors.cyan,
              ),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scale(begin: const Offset(0.95, 0.95), end: const Offset(1.05, 1.05), duration: 2.seconds)
             .custom(builder: (context, value, child) => Opacity(opacity: 0.7 + (value * 0.3), child: child)),
            const SizedBox(height: 32),
            const Text(
              'GUARD ACTIVE • STANDBY MODE',
              style: TextStyle(
                color: OmegaColors.cyan,
                fontFamily: 'monospace',
                fontSize: 14,
                fontWeight: FontWeight.bold,
                letterSpacing: 2.0,
              ),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: OmegaColors.bgSecondary,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: OmegaColors.bgCardBorder),
              ),
              child: const Text(
                'Omega AI recognizes the CNI workstation is currently under safe operator control. Mobile Guardian authentication and remote takeover systems are locked to prevent unauthorized tampering.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: OmegaColors.textSecondary,
                  fontSize: 10,
                  height: 1.5,
                ),
              ),
            ),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const SizedBox(
                  width: 12,
                  height: 12,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(OmegaColors.cyan),
                  ),
                ),
                const SizedBox(width: 12),
                Text(
                  'MONITORING CNI TELEMETRY REAL-TIME...',
                  style: TextStyle(
                    color: OmegaColors.cyan.withOpacity(0.8),
                    fontSize: 8.5,
                    fontFamily: 'monospace',
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 48),
            OutlinedButton.icon(
              onPressed: _triggerEmergency,
              icon: const Icon(Icons.warning_amber_rounded, size: 14),
              label: const Text('TRIGGER EMERGENCY DEMO'),
              style: OutlinedButton.styleFrom(
                foregroundColor: OmegaColors.warning,
                side: const BorderSide(color: OmegaColors.warning),
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                textStyle: const TextStyle(fontSize: 10, fontFamily: 'monospace', fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isEmergency = _state.isEmergency;

    return Scaffold(
      backgroundColor: OmegaColors.bgPrimary,
      appBar: _buildAppBar(isEmergency),
      body: Column(
        children: [
          if (_offlineMode)
            Container(
              color: OmegaColors.warningSurface,
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 16),
              child: Text(
                '⚡ OFFLINE MODE — LAST STATE CACHED AT $_lastOfflineCheckTime',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 8.5,
                  fontWeight: FontWeight.bold,
                  color: OmegaColors.warning,
                ),
              ),
            ),
          
          if (isEmergency) _EmergencyBanner(compromiseType: _state.compromiseType),

          if (isEmergency)
            Container(
              color: OmegaColors.bgSecondary,
              child: TabBar(
                controller: _tabController,
                indicatorColor: OmegaColors.critical,
                indicatorWeight: 2,
                labelStyle: const TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 9,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.5,
                ),
                unselectedLabelColor: OmegaColors.textMuted,
                labelColor: OmegaColors.critical,
                tabs: const [
                  Tab(text: 'OVERVIEW'),
                  Tab(text: 'PROCESSES'),
                  Tab(text: 'EMERGENCY'),
                  Tab(text: 'TIMELINE'),
                  Tab(text: 'MOUSE'),
                ],
              ),
            ),

          Expanded(
            child: !isEmergency
                ? _buildRestrictedAccessScreen()
                : TabBarView(
                    controller: _tabController,
                    children: [
                      _OverviewTab(
                        state: _state, 
                        onTriggerEmergency: _triggerEmergency,
                        onTriggerKillSwitch: _triggerKillSwitch,
                        onSendCommand: _sendRemoteCommand,
                        api: widget.api,
                      ),
                      _ProcessesTab(
                        state: _state,
                        onKillProcess: (pid) => _sendRemoteCommand('KILL_PROCESS', payload: {'pid': pid}),
                      ),
                      _EmergencyTab(
                        state: _state,
                        token: widget.token,
                        isSubmitting: _isSubmitting,
                        decisionMessage: _decisionMessage,
                        decisionSuccess: _decisionSuccess,
                        countdownSeconds: _countdownSeconds,
                        onSubmit: _submitDecision,
                      ),
                      _TimelineTab(state: _state),
                      _MouseTab(api: widget.api),
                    ],
                  ),
          ),
        ],
      ),
    );
  }

  AppBar _buildAppBar(bool isEmergency) {
    return AppBar(
      backgroundColor: OmegaColors.bgSecondary,
      elevation: 0,
      leading: Padding(
        padding: const EdgeInsets.all(10),
        child: Icon(
          Icons.laptop_chromebook,
          color: isEmergency ? OmegaColors.critical : OmegaColors.cyan,
          size: 22,
        ),
      ),
      title: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'OMEGA GUARD SENTINEL',
            style: TextStyle(
              fontFamily: 'JetBrains Mono',
              fontSize: 12,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.5,
              color: OmegaColors.textPrimary,
            ),
          ),
          Text(
            isEmergency ? '⚠ LAPTOP COMPROMISED' : '🛡 CLIENT AGENT SECURED',
            style: TextStyle(
              fontFamily: 'JetBrains Mono',
              fontSize: 8,
              color: isEmergency ? OmegaColors.critical : OmegaColors.safe,
              letterSpacing: 1.0,
            ),
          ),
        ],
      ),
      actions: [
        IconButton(
          onPressed: _fetchStatus,
          icon: const Icon(Icons.refresh, color: OmegaColors.textMuted, size: 18),
          tooltip: 'Refresh status',
        ),
        IconButton(
          onPressed: _logout,
          icon: const Icon(Icons.logout, color: OmegaColors.textMuted, size: 18),
          tooltip: 'Logout',
        ),
      ],
      bottom: PreferredSize(
        preferredSize: const Size.fromHeight(1.5),
        child: Container(
          height: 1.5,
          color: _getRiskAdaptiveBorderColor(),
        ),
      ),
    );
  }
}

// ─── Emergency Banner ──────────────────────────────────────────────────────

class _EmergencyBanner extends StatelessWidget {
  final String compromiseType;
  const _EmergencyBanner({required this.compromiseType});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: OmegaColors.criticalSurface,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          const Icon(Icons.warning_amber_rounded, color: OmegaColors.critical, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              '🚨 LAPTOP INTRUSION ALERT — ${compromiseType.replaceAll('_', ' ')}',
              style: const TextStyle(
                fontFamily: 'JetBrains Mono',
                fontSize: 9.5,
                fontWeight: FontWeight.bold,
                color: OmegaColors.critical,
                letterSpacing: 1.0,
              ),
            ),
          ),
        ],
      ),
    )
        .animate(onPlay: (c) => c.repeat(reverse: true))
        .custom(
          duration: 800.ms,
          builder: (context, value, child) => Container(
            color: Color.lerp(
              OmegaColors.criticalSurface,
              const Color(0xFF4D0000),
              value,
            ),
            child: child,
          ),
        );
  }
}

// ─── Overview Tab ──────────────────────────────────────────────────────────

class _OverviewTab extends StatelessWidget {
  final SystemState state;
  final VoidCallback onTriggerEmergency;
  final VoidCallback onTriggerKillSwitch;
  final Function(String, {Map<String, dynamic> payload}) onSendCommand;
  final ApiService api;

  const _OverviewTab({
    required this.state, 
    required this.onTriggerEmergency,
    required this.onTriggerKillSwitch,
    required this.onSendCommand,
    required this.api,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Status Orb + Core Status
          OmegaCard(
            child: Column(
              children: [
                const SizedBox(height: 8),
                Center(child: StatusOrb(isCompromised: state.isCompromised, size: 90)),
                const SizedBox(height: 16),
                Text(
                  state.isCompromised
                      ? '⚠ SYSTEM COMPROMISED'
                      : '🛡 LAPTOP SECURED',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: 'JetBrains Mono',
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: state.isCompromised ? OmegaColors.critical : OmegaColors.safe,
                    letterSpacing: 1.5,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Client Agent status: ${state.status}',
                  style: const TextStyle(
                    fontFamily: 'JetBrains Mono',
                    fontSize: 10,
                    color: OmegaColors.textSecondary,
                  ),
                ),
                const SizedBox(height: 20),
                
                // Confidence Gauge Widget
                ConfidenceGauge(confidence: state.aiExplanation.confidence),
                const SizedBox(height: 14),

                // Risk gauge
                RiskGauge(value: state.riskValue, level: state.riskLevel),
                const SizedBox(height: 8),
              ],
            ),
          ),

          const SizedBox(height: 14),

          // Device Trust Verification Widget (Feature 2)
          const DeviceTrustCard(),

          const SizedBox(height: 14),

          // Real-time Laptop Health & Metrics (Feature 3)
          OmegaCard(
            title: 'Laptop Telemetry Metrics',
            titleIcon: Icons.analytics_outlined,
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: MetricTile(
                        label: 'CPU LOAD',
                        value: '${state.cpuUsage.toStringAsFixed(1)}%',
                        valueColor: state.cpuUsage > 80 
                            ? OmegaColors.danger 
                            : state.cpuUsage > 50 
                                ? OmegaColors.warning 
                                : OmegaColors.cyan,
                        icon: Icons.developer_board,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: MetricTile(
                        label: 'RAM USAGE',
                        value: '${state.ramUsage.toStringAsFixed(1)}%',
                        valueColor: state.ramUsage > 80 
                            ? OmegaColors.danger 
                            : OmegaColors.cyan,
                        icon: Icons.memory,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                MetricTile(
                  label: 'BATTERY CHARGE',
                  value: '${state.batteryLevel}%',
                  valueColor: state.batteryLevel < 20 
                      ? OmegaColors.danger 
                      : OmegaColors.safe,
                  icon: Icons.battery_charging_full,
                ),
              ],
            ),
          ),

          const SizedBox(height: 14),

          // Remote Control Console (Feature 1)
          OmegaCard(
            title: 'Laptop Remote Controls',
            titleIcon: Icons.settings_remote_outlined,
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: () => onSendCommand('LOCK'),
                        icon: const Icon(Icons.lock_outline, size: 14),
                        label: const Text('LOCK WORKSTATION'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: OmegaColors.cyanDim,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          textStyle: const TextStyle(fontSize: 10, fontFamily: 'monospace'),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: () => onSendCommand('MUTE'),
                        icon: const Icon(Icons.volume_off_outlined, size: 14),
                        label: const Text('TOGGLE MUTE'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: OmegaColors.bgCardBorder,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          textStyle: const TextStyle(fontSize: 10, fontFamily: 'monospace'),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => onSendCommand('SHUTDOWN'),
                        icon: const Icon(Icons.power_settings_new, size: 14),
                        label: const Text('SHUTDOWN LAPTOP'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: OmegaColors.danger,
                          side: const BorderSide(color: OmegaColors.danger),
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          textStyle: const TextStyle(fontSize: 10, fontFamily: 'monospace'),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(height: 14),

          // Remote Forensics & Data Wipe (Feature 4, 7 & 12)
          OmegaCard(
            title: 'Remote Forensics & Self-Destruct',
            titleIcon: Icons.visibility_outlined,
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: () => onSendCommand('CAPTURE_SCREEN'),
                        icon: const Icon(Icons.screenshot_monitor, size: 14),
                        label: const Text('CAPTURE SCREEN'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: OmegaColors.cyan,
                          foregroundColor: OmegaColors.bgPrimary,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          textStyle: const TextStyle(fontSize: 10, fontFamily: 'monospace', fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                  ],
                ),
                if (state.screenshotUrl.contains('screenshot.png')) ...[
                  const SizedBox(height: 12),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Image.network(
                      state.screenshotUrl.startsWith('http')
                          ? state.screenshotUrl
                          : '${api.baseUrl}${state.screenshotUrl}',
                      errorBuilder: (context, error, stackTrace) => Container(
                        height: 120,
                        color: OmegaColors.bgSecondary,
                        child: const Center(
                          child: Text(
                            'SCREENSHOT CAPTURE LOAD ERROR',
                            style: TextStyle(fontSize: 8, color: OmegaColors.textMuted),
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () async {
                            final fullUrl = state.screenshotUrl.startsWith('http')
                                ? state.screenshotUrl
                                : '${api.baseUrl}${state.screenshotUrl}';
                            final msg = await _saveScreenshotToDownloads(fullUrl);
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(msg),
                                  backgroundColor: msg.startsWith('Saved') ? OmegaColors.safe : OmegaColors.critical,
                                ),
                              );
                            }
                          },
                          icon: const Icon(Icons.download, size: 14),
                          label: const Text('SAVE TO DOWNLOADS'),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: OmegaColors.cyan,
                            side: const BorderSide(color: OmegaColors.cyan),
                            padding: const EdgeInsets.symmetric(vertical: 10),
                            textStyle: const TextStyle(fontSize: 10, fontFamily: 'monospace', fontWeight: FontWeight.bold),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
                const Divider(height: 24),
                _SecurityRow(
                  icon: Icons.delete_forever_outlined,
                  label: 'SENSITIVE DATA DIRECTORY',
                  value: state.filesDestroyed ? 'WIPED & DESTROYED ✖' : 'SECURED ✓',
                  valueColor: state.filesDestroyed ? OmegaColors.danger : OmegaColors.safe,
                  pulsing: state.filesDestroyed,
                ),
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: () => onSendCommand('WIPE_DATA'),
                    icon: const Icon(Icons.delete_sweep, size: 14),
                    label: const Text('WIPE SENSITIVE FILES'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: OmegaColors.danger,
                      side: const BorderSide(color: OmegaColors.danger),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      textStyle: const TextStyle(fontSize: 10, fontFamily: 'monospace', fontWeight: FontWeight.bold),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 14),

          // Active Session Management
          OmegaCard(
            title: 'Active Agent Logins',
            titleIcon: Icons.people_outline,
            child: Column(
              children: state.activeSessions.map((session) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Row(
                    children: [
                      const Icon(Icons.devices, size: 14, color: OmegaColors.textMuted),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'User: ${session.user} (${session.ip})',
                              style: const TextStyle(
                                fontFamily: 'JetBrains Mono',
                                fontSize: 10,
                                color: OmegaColors.textPrimary,
                              ),
                            ),
                            Text(
                              session.device,
                              style: const TextStyle(
                                fontFamily: 'JetBrains Mono',
                                fontSize: 8,
                                color: OmegaColors.textMuted,
                              ),
                            ),
                          ],
                        ),
                      ),
                      TextButton(
                        onPressed: () => onSendCommand('MUTE'), // Placeholder for session revocation command
                        child: const Text(
                          'REVOKE',
                          style: TextStyle(color: OmegaColors.danger, fontSize: 10, fontFamily: 'monospace'),
                        ),
                      )
                    ],
                  ),
                );
              }).toList(),
            ),
          ),

          const SizedBox(height: 14),

          // Security Controls & Session Kill Switch (Feature 6)
          OmegaCard(
            title: 'Sentinel Security Actions',
            titleIcon: Icons.security_outlined,
            child: Column(
              children: [
                _SecurityRow(
                  icon: Icons.ac_unit_outlined,
                  label: 'ADVERSARIAL SHIELDING',
                  value: state.learningFrozen ? 'FREEZE STATE (ACTIVE RECOVERY)' : 'SHIELD ENFORCED',
                  valueColor: state.learningFrozen ? OmegaColors.warning : OmegaColors.safe,
                  pulsing: state.learningFrozen,
                ),
                const Divider(height: 18),
                _SecurityRow(
                  icon: Icons.lock_outline,
                  label: 'WORKSTATION BLOCKER',
                  value: state.workstationBlocked ? 'LOCKED' : 'ONLINE',
                  valueColor: state.workstationBlocked ? OmegaColors.danger : OmegaColors.safe,
                  pulsing: state.workstationBlocked,
                ),
                const SizedBox(height: 14),
                
                // One-Tap Lockdown Kill Switch (Feature 6)
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: onTriggerKillSwitch,
                    icon: const Icon(Icons.gavel_outlined, size: 14),
                    label: const Text(
                      '🚫 LOCK SYSTEM NOW',
                      style: TextStyle(
                        fontFamily: 'JetBrains Mono',
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1.0,
                      ),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: OmegaColors.danger,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 20),
        ],
      ),
    );
  }
}

// ─── Processes Tab (Process Manager UI) ────────────────────────────────────

class _ProcessesTab extends StatelessWidget {
  final SystemState state;
  final Function(int) onKillProcess;

  const _ProcessesTab({required this.state, required this.onKillProcess});

  @override
  Widget build(BuildContext context) {
    final procs = state.activeProcesses;

    if (procs.isEmpty) {
      return const Center(
        child: Text(
          'No active processes detected.',
          style: TextStyle(
            fontFamily: 'JetBrains Mono',
            fontSize: 11,
            color: OmegaColors.textMuted,
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
          child: Row(
            children: [
              const Icon(Icons.list_alt_outlined, size: 14, color: OmegaColors.cyan),
              const SizedBox(width: 8),
              const Text(
                'TOP PROCESSES BY CPU',
                style: TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 9,
                  fontWeight: FontWeight.bold,
                  color: OmegaColors.textMuted,
                  letterSpacing: 1.5,
                ),
              ),
              const Spacer(),
              Text(
                '${procs.length} RUNNING',
                style: const TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 8,
                  color: OmegaColors.cyan,
                  letterSpacing: 1.0,
                ),
              ),
            ],
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: procs.length,
            itemBuilder: (context, index) {
              final proc = procs[index];
              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: OmegaColors.bgCard,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: OmegaColors.bgCardBorder),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.code, size: 16, color: OmegaColors.textMuted),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            proc.name,
                            style: const TextStyle(
                              fontFamily: 'JetBrains Mono',
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: OmegaColors.textPrimary,
                            ),
                          ),
                          Text(
                            'PID: ${proc.pid}  |  CPU: ${proc.cpu}%',
                            style: const TextStyle(
                              fontFamily: 'JetBrains Mono',
                              fontSize: 8.5,
                              color: OmegaColors.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                    ElevatedButton(
                      onPressed: () => onKillProcess(proc.pid),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: OmegaColors.criticalSurface,
                        foregroundColor: OmegaColors.critical,
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        elevation: 0,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                        textStyle: const TextStyle(fontSize: 9, fontFamily: 'monospace', fontWeight: FontWeight.bold),
                      ),
                      child: const Text('KILL'),
                    ),
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

// ─── Emergency Tab ─────────────────────────────────────────────────────────

class _EmergencyTab extends StatelessWidget {
  final SystemState state;
  final String token;
  final bool isSubmitting;
  final String decisionMessage;
  final bool decisionSuccess;
  final int countdownSeconds;
  final Future<void> Function(String) onSubmit;

  const _EmergencyTab({
    super.key,
    required this.state,
    required this.token,
    required this.isSubmitting,
    required this.decisionMessage,
    required this.decisionSuccess,
    required this.countdownSeconds,
    required this.onSubmit,
  });

  String _getImpactReason() {
    final cmd = state.pendingEmergencyCommand ?? 'LOCK';
    if (cmd == 'LOCK') {
      return 'Forcing lock sequence secures local data layers, disabling active operator shell input access.';
    } else if (cmd == 'SHUTDOWN') {
      return 'Initiating shutdown will terminate all background agent loops and disconnect the real-time link.';
    }
    return 'Terminating running processes forcibly can cause local data loss if file descriptors remain unwritten.';
  }

  @override
  Widget build(BuildContext context) {
    if (!state.isEmergency) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.verified_user_outlined, size: 56, color: OmegaColors.safe.withAlpha(120)),
            const SizedBox(height: 16),
            const Text(
              'NO ACTIVE EMERGENCY',
              style: TextStyle(
                fontFamily: 'JetBrains Mono',
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: OmegaColors.safe,
                letterSpacing: 2.0,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Sentinel client agent has zero alerts.\nListening on encrypted telemetry channel.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: 'JetBrains Mono',
                fontSize: 10,
                color: OmegaColors.textMuted,
                height: 1.7,
              ),
            ),
          ],
        ),
      ).animate().fadeIn(duration: 400.ms);
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Time-Bound countdown timer (Feature 3)
          Center(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: BoxDecoration(
                color: countdownSeconds <= 10 
                    ? OmegaColors.criticalSurface 
                    : OmegaColors.bgCard,
                borderRadius: BorderRadius.circular(6),
                border: Border.all(
                  color: countdownSeconds <= 10 
                      ? OmegaColors.critical 
                      : OmegaColors.bgCardBorder,
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.timer_outlined, 
                    size: 14, 
                    color: countdownSeconds <= 10 ? OmegaColors.critical : OmegaColors.warning,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'APPROVE WITHIN: 00:${countdownSeconds.toString().padLeft(2, '0')}',
                    style: TextStyle(
                      fontFamily: 'JetBrains Mono',
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: countdownSeconds <= 10 ? OmegaColors.critical : OmegaColors.warning,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Pulse Fingerprint
          Center(
            child: SizedBox(
              width: 100,
              height: 100,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Container(
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: OmegaColors.critical.withAlpha(40), width: 1),
                    ),
                  )
                      .animate(onPlay: (c) => c.repeat())
                      .scale(begin: const Offset(0.7, 0.7), end: const Offset(1.2, 1.2), duration: 1000.ms)
                      .fadeOut(duration: 1000.ms),
                  Container(
                    width: 70,
                    height: 70,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: OmegaColors.criticalSurface,
                      border: Border.all(color: OmegaColors.critical, width: 1.5),
                      boxShadow: [BoxShadow(color: OmegaColors.critical.withAlpha(100), blurRadius: 16)],
                    ),
                    child: const Icon(Icons.fingerprint, color: OmegaColors.critical, size: 32),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          const Text(
            '🚨 CRITICAL ACTION REQUIRED',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: 'JetBrains Mono',
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: OmegaColors.critical,
              letterSpacing: 1.5,
            ),
          ),

          const SizedBox(height: 16),

          // Command detail card
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: OmegaColors.criticalSurface,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: OmegaColors.critical.withAlpha(100)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'INTERCEPTED COMMAND DETAILS',
                  style: TextStyle(
                    fontFamily: 'JetBrains Mono',
                    fontSize: 9,
                    color: OmegaColors.critical,
                    letterSpacing: 2.0,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 10),
                const Text(
                  'A highly sensitive system command was issued to the client laptop. Execution is halted pending secure biometric confirmation by Mobile Root of Trust.',
                  style: TextStyle(
                    fontFamily: 'JetBrains Mono',
                    fontSize: 10,
                    color: OmegaColors.textSecondary,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 12),
                _DetailRow('INTERCEPTED ACTION', state.pendingEmergencyCommand ?? 'REMOTE SHUTDOWN'),
                const SizedBox(height: 6),
                _DetailRow('ALERT TYPE', state.compromiseType.replaceAll('_', ' ')),
                const SizedBox(height: 6),
                _DetailRow('AGENT LOCKOUT', state.workstationBlocked ? 'ACTIVE ⛔' : 'OFFLINE'),
              ],
            ),
          ),

          const SizedBox(height: 14),

          // "Why This Matters" Info Screen
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: OmegaColors.bgCard,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: OmegaColors.bgCardBorder),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '💡 WHY THIS MATTERS',
                  style: TextStyle(
                    fontFamily: 'JetBrains Mono',
                    fontSize: 9,
                    fontWeight: FontWeight.bold,
                    color: OmegaColors.warning,
                    letterSpacing: 1.0,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  _getImpactReason(),
                  style: const TextStyle(
                    fontFamily: 'JetBrains Mono',
                    fontSize: 9.5,
                    color: OmegaColors.textSecondary,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 14),

          // Mini Threat Timeline
          const Text(
            'THREAT TIMELINE CONTEXT',
            style: TextStyle(
              fontFamily: 'JetBrains Mono',
              fontSize: 8.5,
              fontWeight: FontWeight.bold,
              color: OmegaColors.textMuted,
              letterSpacing: 1.0,
            ),
          ),
          const SizedBox(height: 6),
          Container(
            height: 120,
            decoration: BoxDecoration(
              color: OmegaColors.bgSecondary,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: OmegaColors.bgCardBorder),
            ),
            child: ListView.builder(
              padding: const EdgeInsets.all(8),
              itemCount: state.timeline.length > 3 ? 3 : state.timeline.length,
              itemBuilder: (context, index) {
                final event = state.timeline.reversed.toList()[index];
                return Padding(
                  padding: const EdgeInsets.only(bottom: 6.0),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '[${event.time}] ',
                        style: const TextStyle(
                          fontFamily: 'JetBrains Mono',
                          fontSize: 8,
                          color: OmegaColors.textMuted,
                        ),
                      ),
                      Expanded(
                        child: Text(
                          event.event,
                          style: TextStyle(
                            fontFamily: 'JetBrains Mono',
                            fontSize: 8.5,
                            color: event.severity == 'critical' 
                                ? OmegaColors.critical 
                                : OmegaColors.textSecondary,
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),

          const SizedBox(height: 16),

          // Decision Message
          if (decisionMessage.isNotEmpty) ...[
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: decisionSuccess ? OmegaColors.safeSurface : OmegaColors.criticalSurface,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: decisionSuccess
                      ? OmegaColors.safe.withAlpha(80)
                      : OmegaColors.danger.withAlpha(80),
                ),
              ),
              child: Text(
                decisionMessage,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 10,
                  color: decisionSuccess ? OmegaColors.safe : OmegaColors.danger,
                ),
              ),
            ).animate().fadeIn(duration: 300.ms),
          ],

          // Approve / Reject buttons
          if (isSubmitting)
            const Center(
              child: Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: CircularProgressIndicator(color: OmegaColors.critical, strokeWidth: 2),
              ),
            )
          else
            Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                ElevatedButton.icon(
                  onPressed: () => onSubmit('APPROVE'),
                  icon: const Icon(Icons.check_circle_outline, size: 18),
                  label: const Text(
                    'APPROVE OVERRIDE',
                    style: TextStyle(
                      fontFamily: 'JetBrains Mono',
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.5,
                      fontSize: 13,
                    ),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: OmegaColors.safe,
                    foregroundColor: OmegaColors.bgPrimary,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                ),
                const SizedBox(height: 10),
                ElevatedButton.icon(
                  onPressed: () => onSubmit('REJECT'),
                  icon: const Icon(Icons.cancel_outlined, size: 18),
                  label: const Text(
                    'BLOCK COMMAND',
                    style: TextStyle(
                      fontFamily: 'JetBrains Mono',
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.5,
                      fontSize: 13,
                    ),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: OmegaColors.danger,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                ),
              ],
            ).animate().fadeIn(duration: 300.ms),
        ],
      ),
    ).animate().fadeIn(duration: 300.ms);
  }
}

class _DetailRow extends StatelessWidget {
  final String label;
  final String value;

  const _DetailRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '$label: ',
          style: const TextStyle(
            fontFamily: 'JetBrains Mono',
            fontSize: 9,
            color: OmegaColors.textMuted,
            letterSpacing: 0.5,
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(
              fontFamily: 'JetBrains Mono',
              fontSize: 10,
              fontWeight: FontWeight.bold,
              color: OmegaColors.textPrimary,
            ),
          ),
        ),
      ],
    );
  }
}

// ─── Timeline Tab ──────────────────────────────────────────────────────────

class _TimelineTab extends StatelessWidget {
  final SystemState state;

  const _TimelineTab({required this.state});

  @override
  Widget build(BuildContext context) {
    final reversed = state.timeline.reversed.toList();

    if (reversed.isEmpty) {
      return const Center(
        child: Text(
          'No events recorded.',
          style: TextStyle(
            fontFamily: 'JetBrains Mono',
            fontSize: 12,
            color: OmegaColors.textMuted,
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
          child: Row(
            children: [
              const Icon(Icons.timeline_outlined, size: 14, color: OmegaColors.cyan),
              const SizedBox(width: 8),
              const Text(
                'LIVE SENTINEL EVENT LOG',
                style: TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 9,
                  fontWeight: FontWeight.bold,
                  color: OmegaColors.textMuted,
                  letterSpacing: 2.0,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                decoration: BoxDecoration(
                  color: OmegaColors.cyanSurface,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: OmegaColors.cyanDim),
                ),
                child: Text(
                  '${reversed.length} EVENTS',
                  style: const TextStyle(
                    fontFamily: 'JetBrains Mono',
                    fontSize: 8,
                    color: OmegaColors.cyan,
                  ),
                ),
              ),
            ],
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: reversed.length,
            itemBuilder: (context, index) {
              return TimelineCard(event: reversed[index], index: index);
            },
          ),
        ),
      ],
    );
  }
}

class _SecurityRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color valueColor;
  final bool pulsing;

  const _SecurityRow({
    required this.icon,
    required this.label,
    required this.value,
    required this.valueColor,
    this.pulsing = false,
  });

  @override
  Widget build(BuildContext context) {
    Widget valueText = Text(
      value,
      style: TextStyle(
        fontFamily: 'JetBrains Mono',
        fontSize: 10,
        fontWeight: FontWeight.bold,
        color: valueColor,
      ),
    );

    if (pulsing) {
      valueText = valueText
          .animate(onPlay: (c) => c.repeat(reverse: true))
          .fadeIn(duration: 600.ms)
          .then()
          .fadeOut(duration: 600.ms);
    }

    return Row(
      children: [
        Icon(icon, size: 14, color: OmegaColors.textMuted),
        const SizedBox(width: 8),
        Text(
          label,
          style: const TextStyle(
            fontFamily: 'JetBrains Mono',
            fontSize: 9,
            color: OmegaColors.textMuted,
            letterSpacing: 1.0,
          ),
        ),
        const Spacer(),
        valueText,
      ],
    );
  }
}

// ── Touchpad Mouse Controller Tab ─────────────────────────────────────────
class _MouseTab extends StatefulWidget {
  final ApiService api;

  const _MouseTab({required this.api});

  @override
  State<_MouseTab> createState() => _MouseTabState();
}

class _MouseTabState extends State<_MouseTab> {
  double _accumulatedDx = 0;
  double _accumulatedDy = 0;
  Timer? _sendTimer;
  double _sensitivity = 1.8;

  @override
  void dispose() {
    _sendTimer?.cancel();
    super.dispose();
  }

  void _handlePanUpdate(DragUpdateDetails details) {
    _accumulatedDx += details.delta.dx * _sensitivity;
    _accumulatedDy += details.delta.dy * _sensitivity;

    if (_sendTimer == null) {
      _sendTimer = Timer(const Duration(milliseconds: 50), () {
        if (_accumulatedDx != 0 || _accumulatedDy != 0) {
          widget.api.sendMouseControl(_accumulatedDx, _accumulatedDy, '');
          _accumulatedDx = 0;
          _accumulatedDy = 0;
        }
        _sendTimer = null;
      });
    }
  }

  void _sendClick(String clickType) {
    widget.api.sendMouseControl(0, 0, clickType);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: OmegaColors.bgPrimary,
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'FULLSCREEN TOUCHPAD',
                  style: TextStyle(
                    color: OmegaColors.cyan,
                    fontFamily: 'monospace',
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
                Row(
                  children: [
                    const Text('SENSITIVITY: ', style: TextStyle(color: OmegaColors.textMuted, fontSize: 10)),
                    DropdownButton<double>(
                      value: _sensitivity,
                      dropdownColor: OmegaColors.bgSecondary,
                      style: const TextStyle(color: OmegaColors.cyan, fontSize: 10, fontFamily: 'monospace'),
                      underline: Container(),
                      items: [1.0, 1.5, 1.8, 2.2, 3.0].map((val) {
                        return DropdownMenuItem<double>(
                          value: val,
                          child: Text('${val}x'),
                        );
                      }).toList(),
                      onChanged: (val) {
                        if (val != null) setState(() => _sensitivity = val);
                      },
                    ),
                  ],
                ),
              ],
            ),
          ),
          Expanded(
            child: GestureDetector(
              onPanUpdate: _handlePanUpdate,
              onTap: () => _sendClick('left'),
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: OmegaColors.bgSecondary,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: OmegaColors.cyan.withOpacity(0.3), width: 1.5),
                ),
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.touch_app, size: 48, color: OmegaColors.cyan.withOpacity(0.5)),
                      const SizedBox(height: 12),
                      Text(
                        'DRAG TO MOVE CURSOR',
                        style: TextStyle(
                          color: OmegaColors.cyan.withOpacity(0.8),
                          fontFamily: 'monospace',
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        'TAP FOR LEFT CLICK | USE BUTTONS BELOW FOR CLICKS',
                        style: TextStyle(
                          color: OmegaColors.textMuted,
                          fontSize: 8,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: () => _sendClick('left'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: OmegaColors.cyan,
                      foregroundColor: OmegaColors.bgPrimary,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    child: const Text(
                      'LEFT CLICK',
                      style: TextStyle(fontFamily: 'monospace', fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => _sendClick('right'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: OmegaColors.cyan,
                      side: const BorderSide(color: OmegaColors.cyan),
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    child: const Text(
                      'RIGHT CLICK',
                      style: TextStyle(fontFamily: 'monospace', fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Screenshot Downloader Helper ──────────────────────────────────────────
Future<String> _saveScreenshotToDownloads(String url) async {
  try {
    final response = await http.get(Uri.parse(url));
    if (response.statusCode == 200) {
      final dir = Directory('/storage/emulated/0/Download');
      if (await dir.exists()) {
        final file = File('${dir.path}/omega_screenshot_${DateTime.now().millisecondsSinceEpoch}.png');
        await file.writeAsBytes(response.bodyBytes);
        return 'Saved to Downloads: ${file.path}';
      }
      
      final fallbackDir = Directory('/sdcard/Download');
      if (await fallbackDir.exists()) {
        final file = File('${fallbackDir.path}/omega_screenshot_${DateTime.now().millisecondsSinceEpoch}.png');
        await file.writeAsBytes(response.bodyBytes);
        return 'Saved to Downloads: ${file.path}';
      }
      
      final file = File('omega_screenshot.png');
      await file.writeAsBytes(response.bodyBytes);
      return 'Saved to: ${file.absolute.path}';
    } else {
      return 'Failed to download screenshot: Status ${response.statusCode}';
    }
  } catch (e) {
    return 'Error saving screenshot: $e';
  }
}

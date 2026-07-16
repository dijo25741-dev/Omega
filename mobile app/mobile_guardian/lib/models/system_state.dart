// lib/models/system_state.dart
// Data models for the Laptop Security System

import 'dart:convert';

class SystemState {
  final String status;
  final String action;
  final String activeModelHash;
  final double riskValue;
  final String riskLevel;
  final double cpuUsage;
  final double ramUsage;
  final int batteryLevel;
  final bool filesDestroyed;
  final String screenshotUrl;
  final List<ProcessItem> activeProcesses;
  final List<SessionItem> activeSessions;
  final bool learningFrozen;
  final bool emergencyActive;
  final bool workstationBlocked;
  final String? pendingEmergencyCommand;
  final String compromiseType;
  final List<TimelineEvent> timeline;
  final AiExplanation aiExplanation;

  const SystemState({
    this.status = 'SAFE',
    this.action = 'NONE',
    this.activeModelHash = '',
    this.riskValue = 12.0,
    this.riskLevel = 'LOW',
    this.cpuUsage = 0.0,
    this.ramUsage = 0.0,
    this.batteryLevel = 100,
    this.filesDestroyed = false,
    this.screenshotUrl = '/static/placeholder.png',
    this.activeProcesses = const [],
    this.activeSessions = const [],
    this.learningFrozen = false,
    this.emergencyActive = false,
    this.workstationBlocked = false,
    this.pendingEmergencyCommand,
    this.compromiseType = 'NONE',
    this.timeline = const [],
    this.aiExplanation = const AiExplanation(),
  });

  factory SystemState.fromJson(Map<String, dynamic> json) {
    return SystemState(
      status: json['status'] ?? 'SAFE',
      action: json['action'] ?? 'NONE',
      activeModelHash: json['active_model_hash'] ?? '',
      riskValue: (json['risk_value'] ?? 12.0).toDouble(),
      riskLevel: json['risk_level'] ?? 'LOW',
      cpuUsage: (json['cpu_usage'] ?? 0.0).toDouble(),
      ramUsage: (json['ram_usage'] ?? 0.0).toDouble(),
      batteryLevel: json['battery_level'] ?? 100,
      filesDestroyed: json['files_destroyed'] ?? false,
      screenshotUrl: json['screenshot_url'] ?? '/static/placeholder.png',
      activeProcesses: (json['active_processes'] as List<dynamic>? ?? [])
          .map((e) => ProcessItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      activeSessions: (json['active_sessions'] as List<dynamic>? ?? [])
          .map((e) => SessionItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      learningFrozen: json['learning_frozen'] ?? false,
      emergencyActive: json['emergency_active'] ?? false,
      workstationBlocked: json['workstation_blocked'] ?? false,
      pendingEmergencyCommand: json['pending_emergency_command'],
      compromiseType: json['compromise_type'] ?? 'NONE',
      timeline: (json['timeline'] as List<dynamic>? ?? [])
          .map((e) => TimelineEvent.fromJson(e as Map<String, dynamic>))
          .toList(),
      aiExplanation: json['ai_explanation'] != null
          ? AiExplanation.fromJson(json['ai_explanation'] as Map<String, dynamic>)
          : const AiExplanation(),
    );
  }

  Map<String, dynamic> toJson() => {
        'status': status,
        'action': action,
        'active_model_hash': activeModelHash,
        'risk_value': riskValue,
        'risk_level': riskLevel,
        'cpu_usage': cpuUsage,
        'ram_usage': ramUsage,
        'battery_level': batteryLevel,
        'files_destroyed': filesDestroyed,
        'screenshot_url': screenshotUrl,
        'active_processes': activeProcesses.map((e) => e.toJson()).toList(),
        'active_sessions': activeSessions.map((e) => e.toJson()).toList(),
        'learning_frozen': learningFrozen,
        'emergency_active': emergencyActive,
        'workstation_blocked': workstationBlocked,
        'pending_emergency_command': pendingEmergencyCommand,
        'compromise_type': compromiseType,
        'timeline': timeline.map((e) => e.toJson()).toList(),
        'ai_explanation': aiExplanation.toJson(),
      };

  String toJsonString() => jsonEncode(toJson());

  factory SystemState.fromJsonString(String jsonStr) =>
      SystemState.fromJson(jsonDecode(jsonStr) as Map<String, dynamic>);

  bool get isCompromised => status == 'COMPROMISED';
  bool get isEmergency => emergencyActive || isCompromised;
}

class ProcessItem {
  final int pid;
  final String name;
  final double cpu;

  const ProcessItem({required this.pid, required this.name, required this.cpu});

  factory ProcessItem.fromJson(Map<String, dynamic> json) {
    return ProcessItem(
      pid: json['pid'] ?? 0,
      name: json['name'] ?? 'Unknown',
      cpu: (json['cpu'] ?? 0.0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'pid': pid,
        'name': name,
        'cpu': cpu,
      };
}

class SessionItem {
  final String sessionId;
  final String user;
  final String ip;
  final String device;

  const SessionItem({
    required this.sessionId,
    required this.user,
    required this.ip,
    required this.device,
  });

  factory SessionItem.fromJson(Map<String, dynamic> json) {
    return SessionItem(
      sessionId: json['session_id'] ?? '',
      user: json['user'] ?? '',
      ip: json['ip'] ?? '',
      device: json['device'] ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'session_id': sessionId,
        'user': user,
        'ip': ip,
        'device': device,
      };
}

class TimelineEvent {
  final String time;
  final String event;
  final String severity;

  const TimelineEvent({
    required this.time,
    required this.event,
    required this.severity,
  });

  factory TimelineEvent.fromJson(Map<String, dynamic> json) {
    return TimelineEvent(
      time: json['time'] ?? '',
      event: json['event'] ?? '',
      severity: json['severity'] ?? 'info',
    );
  }

  Map<String, dynamic> toJson() => {
        'time': time,
        'event': event,
        'severity': severity,
      };
}

class AiExplanation {
  final String action;
  final List<String> reason;
  final double confidence;

  const AiExplanation({
    this.action = 'MONITORING',
    this.reason = const [],
    this.confidence = 99.8,
  });

  factory AiExplanation.fromJson(Map<String, dynamic> json) {
    return AiExplanation(
      action: json['action'] ?? 'MONITORING',
      reason: List<String>.from(json['reason'] ?? []),
      confidence: (json['confidence'] ?? 99.8).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'action': action,
        'reason': reason,
        'confidence': confidence,
      };
}

class LoginResponse {
  final String accessToken;
  final String tokenType;

  const LoginResponse({required this.accessToken, required this.tokenType});

  factory LoginResponse.fromJson(Map<String, dynamic> json) {
    return LoginResponse(
      accessToken: json['access_token'] ?? '',
      tokenType: json['token_type'] ?? 'bearer',
    );
  }
}

class RecoveryStep {
  final String label;
  final String status; // 'done', 'in_progress', 'pending'

  const RecoveryStep({required this.label, required this.status});

  factory RecoveryStep.fromJson(Map<String, dynamic> json) {
    return RecoveryStep(
      label: json['label'] ?? '',
      status: json['status'] ?? 'pending',
    );
  }
}

// lib/services/api_service.dart
// Centralized API service for all backend calls — with offline caching and laptop controls

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/system_state.dart';

class ApiService {
  String baseUrl;

  ApiService({required this.baseUrl});

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'bypass-tunnel-reminder': 'true',
      };

  /// Login with operator credentials, returns JWT token on success
  Future<LoginResponse> login(String username, String password) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/api/login'),
          headers: _headers,
          body: jsonEncode({'username': username, 'password': password}),
        )
        .timeout(const Duration(seconds: 10));

    if (response.statusCode == 200) {
      return LoginResponse.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    } else if (response.statusCode == 401) {
      throw ApiException('Authentication failed. Check operator credentials.');
    } else {
      throw ApiException('Server error: ${response.statusCode}');
    }
  }

  /// Fetch current system integrity status (returns full laptop telemetry)
  Future<SystemState> checkIntegrity() async {
    final response = await http
        .get(Uri.parse('$baseUrl/api/check-integrity'), headers: _headers)
        .timeout(const Duration(seconds: 8));

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final state = SystemState.fromJson(data);
      // Cache for offline mode
      await _cacheState(state);
      return state;
    }
    throw ApiException('Failed to fetch system status');
  }

  /// Send a command to the remote laptop (e.g. LOCK, MUTE, KILL_PROCESS)
  Future<Map<String, dynamic>> sendLaptopCommand(String command, {Map<String, dynamic> payload = const {}}) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/api/laptop/command'),
          headers: _headers,
          body: jsonEncode({'command': command, 'payload': payload}),
        )
        .timeout(const Duration(seconds: 10));

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else if (response.statusCode == 403) {
      throw ApiException('Action Blocked: Mobile Guardian MFA authorization signature required.');
    } else {
      throw ApiException('Failed to execute remote command: ${response.statusCode}');
    }
  }

  /// Submit APPROVE or REJECT decision for a pending emergency command
  Future<Map<String, dynamic>> respondToEmergency(String decision, String token) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/api/respond-emergency'),
          headers: _headers,
          body: jsonEncode({'decision': decision, 'token': token}),
        )
        .timeout(const Duration(seconds: 10));

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else if (response.statusCode == 401) {
      throw ApiException('Authorization token rejected by server.');
    } else {
      throw ApiException('Failed to submit decision: ${response.statusCode}');
    }
  }

  /// Trigger an immediate workstation lockout emergency
  Future<void> triggerEmergency() async {
    await http
        .post(Uri.parse('$baseUrl/api/trigger-emergency'), headers: _headers)
        .timeout(const Duration(seconds: 8));
  }

  /// Kill Switch — immediate total lockdown from mobile guardian
  Future<Map<String, dynamic>> killSwitch() async {
    final response = await http
        .post(Uri.parse('$baseUrl/api/kill-switch'), headers: _headers)
        .timeout(const Duration(seconds: 8));

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw ApiException('Kill switch failed: ${response.statusCode}');
  }

  /// Get recovery progress steps
  Future<List<RecoveryStep>> getRecoveryStatus() async {
    final response = await http
        .get(Uri.parse('$baseUrl/api/recovery-status'), headers: _headers)
        .timeout(const Duration(seconds: 8));

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      return (data['steps'] as List<dynamic>)
          .map((e) => RecoveryStep.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    throw ApiException('Failed to fetch recovery status');
  }

  /// Reset entire system state to secure baseline
  Future<void> resetState() async {
    await http
        .post(Uri.parse('$baseUrl/api/reset'), headers: _headers)
        .timeout(const Duration(seconds: 8));
  }

  /// Send a relative mouse movement or click to the laptop
  Future<void> sendMouseControl(double dx, double dy, String click) async {
    try {
      await http.post(
        Uri.parse('$baseUrl/api/laptop/mouse'),
        headers: _headers,
        body: jsonEncode({'dx': dx, 'dy': dy, 'click': click}),
      ).timeout(const Duration(seconds: 3));
    } catch (_) {}
  }

  /// Test connectivity to backend
  Future<bool> testConnection() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/check-integrity'), headers: _headers)
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  // ── Offline Caching ─────────────────────────────────────────────────────

  /// Cache current state to SharedPreferences for offline mode
  Future<void> _cacheState(SystemState state) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('cached_system_state', state.toJsonString());
      await prefs.setString('cached_state_time', DateTime.now().toIso8601String());
    } catch (_) {}
  }

  /// Load cached state from SharedPreferences (for offline mode)
  Future<SystemState?> getCachedState() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final json = prefs.getString('cached_system_state');
      if (json != null) {
        return SystemState.fromJsonString(json);
      }
    } catch (_) {}
    return null;
  }

  /// Get the timestamp of the last cached state
  Future<String?> getCachedStateTime() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('cached_state_time');
  }
}

class ApiException implements Exception {
  final String message;
  const ApiException(this.message);

  @override
  String toString() => message;
}

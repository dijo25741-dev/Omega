// lib/screens/login_screen.dart
// Premium dark cyber login with animated shield and secure device binding

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme/omega_theme.dart';
import '../services/api_service.dart';
import 'guardian_dashboard.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController(text: 'admin');
  final _passwordController = TextEditingController(text: 'omega2026');
  final _serverUrlController = TextEditingController(text: 'http://localhost:8000');

  bool _isLoading = false;
  bool _obscurePassword = true;
  bool _showServerConfig = false;
  String _errorMsg = '';
  String _statusMsg = '';

  @override
  void initState() {
    super.initState();
    _loadSavedUrl();
  }

  Future<void> _loadSavedUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString('backend_url');
    if (saved != null && mounted) {
      setState(() => _serverUrlController.text = saved);
    }
  }

  Future<void> _saveUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('backend_url', url);
  }

  Future<void> _login() async {
    String url = _serverUrlController.text.trim();
    if (url.isEmpty) {
      setState(() => _errorMsg = 'Server IP or URL cannot be empty.');
      return;
    }

    // Automatically format raw IP or hostname inputs into full HTTP URL
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      if (!url.contains(':')) {
        url = 'http://$url:8000';
      } else {
        url = 'http://$url';
      }
    }

    setState(() {
      _isLoading = true;
      _errorMsg = '';
      _statusMsg = 'VERIFYING OPERATOR CREDENTIALS...';
    });

    await _saveUrl(url);
    final api = ApiService(baseUrl: url);

    try {
      setState(() => _statusMsg = 'BINDING DEVICE TO SECURE CHANNEL...');
      final response = await api.login(
        _usernameController.text.trim(),
        _passwordController.text,
      );

      setState(() => _statusMsg = 'HANDSHAKE COMPLETE — LOADING GUARDIAN...');
      await Future.delayed(const Duration(milliseconds: 600));

      if (mounted) {
        Navigator.pushReplacement(
          context,
          PageRouteBuilder(
            pageBuilder: (_, animation, __) => GuardianDashboard(
              token: response.accessToken,
              api: api,
            ),
            transitionsBuilder: (_, animation, __, child) {
              return FadeTransition(opacity: animation, child: child);
            },
            transitionDuration: const Duration(milliseconds: 500),
          ),
        );
      }
    } on ApiException catch (e) {
      setState(() {
        _errorMsg = e.message;
        _statusMsg = '';
      });
    } catch (e) {
      setState(() {
        _errorMsg = 'CONNECTIVITY ERROR: Cannot reach backend server.\nCheck IP and ensure the server is running.';
        _statusMsg = '';
      });
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _serverUrlController.dispose();
    super.dispose();
  }

  Widget _FieldLabel(String label) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Text(
        label,
        style: const TextStyle(
          fontFamily: 'JetBrains Mono',
          fontSize: 10,
          fontWeight: FontWeight.bold,
          color: OmegaColors.textSecondary,
          letterSpacing: 1.5,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: OmegaColors.bgPrimary,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 40),
              
              // Animated Shield/Cyber icon
              Center(
                child: TweenAnimationBuilder<double>(
                  tween: Tween<double>(begin: 0.0, end: 1.0),
                  duration: const Duration(seconds: 2),
                  builder: (context, value, child) {
                    return Container(
                      width: 90,
                      height: 90,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: OmegaColors.cyanSurface,
                        border: Border.all(
                          color: OmegaColors.cyan.withOpacity(0.5 * value),
                          width: 1.5,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: OmegaColors.cyan.withOpacity(0.15 * value),
                            blurRadius: 15,
                            spreadRadius: 2,
                          ),
                        ],
                      ),
                      child: child,
                    );
                  },
                  child: const Center(
                    child: Icon(
                      Icons.shield_outlined,
                      color: OmegaColors.cyan,
                      size: 42,
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 24),
              
              const Text(
                'OMEGA GUARDIAN',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 4.0,
                  color: OmegaColors.textPrimary,
                ),
              ).animate().fadeIn(delay: 200.ms, duration: 600.ms),

              const SizedBox(height: 6),

              const Text(
                'EXTERNAL HUMAN TRUST AUTHENTICATOR',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 9,
                  letterSpacing: 2.0,
                  color: OmegaColors.cyan,
                ),
              ).animate().fadeIn(delay: 400.ms, duration: 600.ms),

              const SizedBox(height: 48),

              // Inputs form card
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: OmegaColors.bgSecondary,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: OmegaColors.bgCardBorder),
                ),
                child: Column(
                  children: [
                    _FieldLabel('OPERATOR ID'),
                    const SizedBox(height: 6),
                    TextField(
                      controller: _usernameController,
                      style: const TextStyle(
                        fontFamily: 'JetBrains Mono',
                        fontSize: 13,
                        color: OmegaColors.textPrimary,
                      ),
                      decoration: InputDecoration(
                        hintText: 'Enter operator ID',
                        hintStyle: const TextStyle(color: OmegaColors.textMuted, fontSize: 12),
                        prefixIcon: const Icon(Icons.person_outline, size: 18),
                        filled: true,
                        fillColor: OmegaColors.bgCard,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: OmegaColors.bgCardBorder),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: OmegaColors.bgCardBorder),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: OmegaColors.cyan, width: 1.5),
                        ),
                      ),
                    ),

                    const SizedBox(height: 16),
                    _FieldLabel('SECURITY PASSCODE'),
                    const SizedBox(height: 6),
                    TextField(
                      controller: _passwordController,
                      obscureText: _obscurePassword,
                      style: const TextStyle(
                        fontFamily: 'JetBrains Mono',
                        fontSize: 13,
                        color: OmegaColors.textPrimary,
                      ),
                      decoration: InputDecoration(
                        hintText: 'Enter passcode',
                        hintStyle: const TextStyle(color: OmegaColors.textMuted, fontSize: 12),
                        prefixIcon: const Icon(Icons.lock_outline, size: 18),
                        suffixIcon: IconButton(
                          onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                          icon: Icon(
                            _obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                            size: 18,
                            color: OmegaColors.textMuted,
                          ),
                        ),
                        filled: true,
                        fillColor: OmegaColors.bgCard,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: OmegaColors.bgCardBorder),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: OmegaColors.bgCardBorder),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: OmegaColors.cyan, width: 1.5),
                        ),
                      ),
                    ),

                    const SizedBox(height: 16),
                    GestureDetector(
                      onTap: () => setState(() => _showServerConfig = !_showServerConfig),
                      child: Row(
                        children: [
                          Icon(
                            _showServerConfig ? Icons.expand_less : Icons.expand_more,
                            size: 16,
                            color: OmegaColors.textMuted,
                          ),
                          const SizedBox(width: 6),
                          const Text(
                            'NETWORK CONFIGURATION',
                            style: TextStyle(
                              fontFamily: 'JetBrains Mono',
                              fontSize: 9,
                              color: OmegaColors.textMuted,
                              letterSpacing: 1.5,
                            ),
                          ),
                        ],
                      ),
                    ),

                    if (_showServerConfig) ...[
                      const SizedBox(height: 10),
                      _FieldLabel('BACKEND SERVER URL'),
                      const SizedBox(height: 6),
                      TextField(
                        controller: _serverUrlController,
                        keyboardType: TextInputType.url,
                        style: const TextStyle(
                          fontFamily: 'JetBrains Mono',
                          fontSize: 12,
                          color: OmegaColors.cyan,
                        ),
                        decoration: InputDecoration(
                          hintText: 'http://192.168.x.x:8000',
                          hintStyle: const TextStyle(color: OmegaColors.textMuted, fontSize: 11),
                          prefixIcon: const Icon(Icons.dns_outlined, size: 16),
                          filled: true,
                          fillColor: OmegaColors.bgSecondary,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                            borderSide: const BorderSide(color: OmegaColors.cyanDim),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                            borderSide: const BorderSide(color: OmegaColors.cyanDim),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                            borderSide: const BorderSide(color: OmegaColors.cyan, width: 1.5),
                          ),
                        ),
                      ).animate().fadeIn(duration: 200.ms),
                      const SizedBox(height: 6),
                      const Text(
                        '  Android emulator: use http://10.0.2.2:8000\n  Physical device: use your machine\'s local IP',
                        style: TextStyle(
                          fontFamily: 'JetBrains Mono',
                          fontSize: 9,
                          color: OmegaColors.textMuted,
                          height: 1.7,
                        ),
                      ),
                    ],

                    const SizedBox(height: 28),

                    // Status display when loading
                    if (_isLoading && _statusMsg.isNotEmpty) ...[
                      Text(
                        _statusMsg,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontFamily: 'JetBrains Mono',
                          fontSize: 10,
                          color: OmegaColors.cyan,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    // Error warning box
                    if (_errorMsg.isNotEmpty) ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        margin: const EdgeInsets.only(bottom: 16),
                        decoration: BoxDecoration(
                          color: OmegaColors.criticalSurface,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: OmegaColors.danger.withAlpha(100)),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(Icons.error_outline, color: OmegaColors.danger, size: 16),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                _errorMsg,
                                style: const TextStyle(
                                  fontFamily: 'JetBrains Mono',
                                  fontSize: 10,
                                  color: OmegaColors.danger,
                                  height: 1.5,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ).animate().fadeIn(duration: 300.ms),
                    ],

                    // Login button
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton(
                        onPressed: _isLoading ? null : _login,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: OmegaColors.cyan,
                          disabledBackgroundColor: OmegaColors.cyanDim,
                          foregroundColor: OmegaColors.bgPrimary,
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        child: _isLoading
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor: AlwaysStoppedAnimation<Color>(OmegaColors.bgPrimary),
                                ),
                              )
                            : const Text(
                                'AUTHENTICATE ACCESS',
                                style: TextStyle(
                                  fontFamily: 'JetBrains Mono',
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  letterSpacing: 2.0,
                                ),
                              ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 40),

              // Device fingerprint footer
              const Center(
                child: Text(
                  'DEVICE: SHA256_FINGERPRINT_3A9C7B2E',
                  style: TextStyle(
                    fontFamily: 'JetBrains Mono',
                    fontSize: 8,
                    color: OmegaColors.textMuted,
                    letterSpacing: 1.0,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/auth/auth_controller.dart';
import '../../core/routing/app_router.dart';
import '../../theme/app_colors.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _obscure = true;
  bool _remember = false;
  bool _dark = false;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final email = _email.text.trim();
    final password = _password.text;
    if (email.isEmpty || password.isEmpty) return;

    await ref.read(authControllerProvider.notifier).login(email, password);

    final auth = ref.read(authControllerProvider);
    if (auth.status == AuthStatus.authenticated && auth.session != null) {
      if (mounted) context.go(spacePath(auth.session!.space));
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final loading = auth.loading;

    return Scaffold(
      backgroundColor: _dark ? const Color(0xFF020204) : Colors.white,
      body: Stack(
        children: [
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: Container(
              height: 3,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: const [
                  Expanded(child: ColoredBox(color: AppColors.brand500)),
                  Expanded(child: ColoredBox(color: Color(0xFFFFED00))),
                  Expanded(child: ColoredBox(color: Color(0xFFE30613))),
                ],
              ),
            ),
          ),
          Positioned(
            top: 16,
            right: 16,
            child: _RoundToggle(
              dark: _dark,
              onTap: () => setState(() => _dark = !_dark),
            ),
          ),
          Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(vertical: 48, horizontal: 24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 430),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: _dark
                            ? AppColors.brand500.withValues(alpha: 0.1)
                            : const Color(0xFFE6F6FD),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: _dark
                              ? AppColors.brand500.withValues(alpha: 0.2)
                              : const Color(0xFFCCEDFB),
                        ),
                      ),
                      child: const Icon(Icons.lock_outline,
                          size: 24, color: AppColors.brand600),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Espace Expert',
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.w700,
                        color: _dark ? Colors.white : const Color(0xFF0F172A),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Connectez-vous à la plateforme CNE-ITP.',
                      style: TextStyle(
                        fontSize: 13,
                        color: _dark ? const Color(0xFF94A3B8) : AppColors.muted,
                      ),
                    ),
                    const SizedBox(height: 28),
                    Container(
                      padding: const EdgeInsets.all(28),
                      decoration: BoxDecoration(
                        color: _dark
                            ? Colors.white.withValues(alpha: 0.05)
                            : Colors.white,
                        borderRadius: BorderRadius.circular(22),
                        border: Border.all(
                          color: _dark
                              ? Colors.white.withValues(alpha: 0.1)
                              : const Color(0xFFE2E8F0),
                        ),
                        boxShadow: _dark
                            ? null
                            : const [
                                BoxShadow(
                                  color: Color(0x0A000000),
                                  blurRadius: 2,
                                  offset: Offset(0, 1),
                                ),
                              ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          if (auth.error != null &&
                              auth.status == AuthStatus.failure) ...[
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: AppColors.danger.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(
                                  color:
                                      AppColors.danger.withValues(alpha: 0.2),
                                ),
                              ),
                              child: Row(
                                children: [
                                  const Icon(Icons.shield_outlined,
                                      size: 18, color: AppColors.danger),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    child: Text(
                                      auth.error!,
                                      style: const TextStyle(
                                        fontSize: 12,
                                        color: AppColors.danger,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 16),
                          ],
                          _Field(
                            controller: _email,
                            label: 'Email',
                            hint: 'votre@email.com',
                            icon: Icons.mail_outline,
                            dark: _dark,
                          ),
                          const SizedBox(height: 16),
                          _Field(
                            controller: _password,
                            label: 'Mot de passe',
                            hint: '••••••••',
                            icon: Icons.key_outlined,
                            dark: _dark,
                            obscure: _obscure,
                            onToggle: () => setState(() => _obscure = !_obscure),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              SizedBox(
                                width: 16,
                                height: 16,
                                child: Checkbox(
                                  value: _remember,
                                  onChanged: (v) =>
                                      setState(() => _remember = v ?? false),
                                  activeColor: AppColors.brand500,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  'Se souvenir de moi',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: _dark
                                        ? const Color(0xFFCBD5E1)
                                        : AppColors.muted,
                                  ),
                                ),
                              ),
                              GestureDetector(
                                onTap: () {},
                                child: const Text(
                                  'Mot de passe oublié ?',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: AppColors.brand600,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 20),
                          SizedBox(
                            height: 48,
                            child: Material(
                              color: AppColors.brand500,
                              borderRadius: BorderRadius.circular(12),
                              child: InkWell(
                                onTap: loading ? null : _submit,
                                borderRadius: BorderRadius.circular(12),
                                child: Center(
                                  child: loading
                                      ? const SizedBox(
                                          width: 20,
                                          height: 20,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                            color: Colors.white,
                                          ),
                                        )
                                      : Row(
                                          mainAxisAlignment:
                                              MainAxisAlignment.center,
                                          children: const [
                                            Text(
                                              'Se connecter',
                                              style: TextStyle(
                                                fontSize: 14,
                                                fontWeight: FontWeight.w600,
                                                color: Colors.white,
                                              ),
                                            ),
                                            SizedBox(width: 8),
                                            Icon(Icons.login,
                                                size: 16, color: Colors.white),
                                          ],
                                        ),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                    Text.rich(
                      TextSpan(
                        text: 'Pas encore accrédité ? ',
                        style: TextStyle(
                          fontSize: 12,
                          color: _dark
                              ? const Color(0xFF94A3B8)
                              : AppColors.subtle,
                        ),
                        children: const [
                          TextSpan(
                            text: 'Déposer une candidature expert',
                            style: TextStyle(
                              color: AppColors.brand600,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _RoundToggle extends StatelessWidget {
  const _RoundToggle({required this.dark, required this.onTap});
  final bool dark;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(999),
      child: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: dark ? Colors.white.withValues(alpha: 0.05) : Colors.white,
          border: Border.all(
            color: dark ? Colors.white.withValues(alpha: 0.1) : const Color(0xFFE2E8F0),
          ),
        ),
        child: Icon(
          dark ? Icons.light_mode_outlined : Icons.dark_mode_outlined,
          size: 18,
          color: dark ? const Color(0xFFCBD5E1) : AppColors.muted,
        ),
      ),
    );
  }
}

class _Field extends StatelessWidget {
  const _Field({
    required this.controller,
    required this.label,
    required this.hint,
    required this.icon,
    required this.dark,
    this.obscure = false,
    this.onToggle,
  });

  final TextEditingController controller;
  final String label;
  final String hint;
  final IconData icon;
  final bool dark;
  final bool obscure;
  final VoidCallback? onToggle;

  @override
  Widget build(BuildContext context) {
    final borderColor = dark
        ? Colors.white.withValues(alpha: 0.1)
        : const Color(0xFFE2E8F0);
    final fillColor =
        dark ? Colors.white.withValues(alpha: 0.05) : const Color(0xFFF8FAFC);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label.toUpperCase(),
          style: TextStyle(
            fontSize: 10.5,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.1,
            color: dark ? const Color(0xFF94A3B8) : AppColors.muted,
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: controller,
          obscureText: obscure,
          style: TextStyle(
            fontSize: 14,
            color: dark ? Colors.white : const Color(0xFF0F172A),
          ),
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: TextStyle(
              fontSize: 13,
              color: dark ? const Color(0xFF475569) : const Color(0xFF94A3B8),
            ),
            filled: true,
            fillColor: fillColor,
            prefixIcon: Icon(icon, size: 18, color: AppColors.subtle),
            suffixIcon: onToggle != null
                ? IconButton(
                    onPressed: onToggle,
                    icon: Icon(
                      obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                      size: 18,
                      color: AppColors.subtle,
                    ),
                  )
                : null,
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: borderColor),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: AppColors.brand500),
            ),
          ),
        ),
      ],
    );
  }
}

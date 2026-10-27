import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_client.dart';
import '../../theme/app_colors.dart';

class PasswordResetScreen extends StatefulWidget {
  const PasswordResetScreen({super.key});

  @override
  State<PasswordResetScreen> createState() => _PasswordResetScreenState();
}

class _PasswordResetScreenState extends State<PasswordResetScreen> {
  final _email = TextEditingController();
  final _code = TextEditingController();
  final _password = TextEditingController();
  final _confirmation = TextEditingController();
  int _step = 0;
  bool _loading = false;
  bool _obscure = true;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _code.dispose();
    _password.dispose();
    _confirmation.dispose();
    super.dispose();
  }

  String _message(DioException e) {
    final data = e.response?.data;
    if (data is Map && data['error'] != null) return data['error'].toString();
    if (data is Map && data['detail'] != null) return data['detail'].toString();
    if (data is Map) {
      return data.values.map((v) => v is List ? v.join(', ') : '$v').join('\n');
    }
    return 'Le service est momentanément indisponible.';
  }

  Future<void> _requestCode() async {
    if (!RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(_email.text.trim())) {
      setState(() => _error = 'Saisissez une adresse email valide.');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ApiClient.dio.post(
        '/api/v1/mobile/auth/password-reset/request/',
        data: {'email': _email.text.trim()},
      );
      if (mounted) setState(() => _step = 1);
    } on DioException catch (e) {
      if (mounted) setState(() => _error = _message(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _confirm() async {
    if (!RegExp(r'^\d{6}$').hasMatch(_code.text.trim()) ||
        _password.text.isEmpty ||
        _confirmation.text.isEmpty) {
      setState(() => _error = 'Complétez le code et les deux mots de passe.');
      return;
    }
    if (_password.text.length < 8 || _password.text != _confirmation.text) {
      setState(
        () => _error =
            'Les mots de passe doivent être identiques et contenir au moins 8 caractères.',
      );
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ApiClient.dio.post(
        '/api/v1/mobile/auth/password-reset/confirm/',
        data: {
          'email': _email.text.trim(),
          'code': _code.text.trim(),
          'password': _password.text,
          'password2': _confirmation.text,
        },
      );
      if (mounted) setState(() => _step = 2);
    } on DioException catch (e) {
      if (mounted) setState(() => _error = _message(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: const Color(0xFFF7FAFC),
    body: Stack(
      children: [
        Positioned(
          top: 0,
          left: 0,
          right: 0,
          child: Row(
            children: const [
              Expanded(
                child: ColoredBox(
                  color: AppColors.brand500,
                  child: SizedBox(height: 3),
                ),
              ),
              Expanded(
                child: ColoredBox(
                  color: AppColors.rdcYellow,
                  child: SizedBox(height: 3),
                ),
              ),
              Expanded(
                child: ColoredBox(
                  color: AppColors.rdcRed,
                  child: SizedBox(height: 3),
                ),
              ),
            ],
          ),
        ),
        Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 460),
              child: Column(
                children: [
                  Align(
                    alignment: Alignment.centerLeft,
                    child: TextButton.icon(
                      onPressed: () => context.go('/login'),
                      icon: const Icon(Icons.arrow_back, size: 17),
                      label: const Text('Retour à la connexion'),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    width: 52,
                    height: 52,
                    decoration: BoxDecoration(
                      color: AppColors.brand500.withValues(alpha: .1),
                      borderRadius: BorderRadius.circular(15),
                    ),
                    child: Icon(
                      _step == 2
                          ? Icons.check_circle_outline
                          : Icons.key_outlined,
                      color: _step == 2
                          ? AppColors.success
                          : AppColors.brand600,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    _step == 2
                        ? 'Mot de passe mis à jour'
                        : (_step == 1 ? 'Vérification' : 'Mot de passe oublié'),
                    style: const TextStyle(
                      fontSize: 27,
                      fontWeight: FontWeight.w800,
                      color: AppColors.text,
                    ),
                  ),
                  const SizedBox(height: 7),
                  Text(
                    _step == 0
                        ? 'Entrez votre email pour recevoir un code.'
                        : (_step == 1
                              ? 'Saisissez le code à 6 chiffres reçu par email.'
                              : 'Vous pouvez maintenant vous connecter.'),
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: AppColors.muted),
                  ),
                  const SizedBox(height: 25),
                  Container(
                    padding: const EdgeInsets.all(28),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(22),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: AnimatedSwitcher(
                      duration: const Duration(milliseconds: 200),
                      child: _content(),
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

  Widget _content() {
    if (_step == 2) {
      return Column(
        key: const ValueKey(2),
        children: [
          const Icon(
            Icons.verified_outlined,
            size: 56,
            color: AppColors.success,
          ),
          const SizedBox(height: 18),
          const Text(
            'Votre mot de passe a été réinitialisé avec succès.',
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 22),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: () => context.go('/login'),
              child: const Text('Se connecter'),
            ),
          ),
        ],
      );
    }
    return Column(
      key: ValueKey(_step),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (_error != null) ...[
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.danger.withValues(alpha: .08),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              _error!,
              style: const TextStyle(fontSize: 12, color: AppColors.danger),
            ),
          ),
          const SizedBox(height: 16),
        ],
        if (_step == 0) ...[
          _field(
            _email,
            'Adresse email',
            'votre@email.com',
            Icons.mail_outline,
          ),
          const SizedBox(height: 20),
          FilledButton.icon(
            onPressed: _loading ? null : _requestCode,
            icon: _loading
                ? const SizedBox.square(
                    dimension: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.send_outlined, size: 17),
            label: const Text('Envoyer le code'),
          ),
        ] else ...[
          Text(
            _email.text,
            style: const TextStyle(
              color: AppColors.brand600,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 18),
          _field(
            _code,
            'Code à 6 chiffres',
            '000000',
            Icons.pin_outlined,
            keyboard: TextInputType.number,
          ),
          const SizedBox(height: 14),
          _field(
            _password,
            'Nouveau mot de passe',
            'Minimum 8 caractères',
            Icons.lock_outline,
            obscure: _obscure,
          ),
          const SizedBox(height: 14),
          _field(
            _confirmation,
            'Confirmer le mot de passe',
            'Répétez le mot de passe',
            Icons.lock_outline,
            obscure: _obscure,
          ),
          Align(
            alignment: Alignment.centerRight,
            child: TextButton.icon(
              onPressed: () => setState(() => _obscure = !_obscure),
              icon: Icon(
                _obscure
                    ? Icons.visibility_outlined
                    : Icons.visibility_off_outlined,
                size: 16,
              ),
              label: Text(_obscure ? 'Afficher' : 'Masquer'),
            ),
          ),
          FilledButton(
            onPressed: _loading ? null : _confirm,
            child: _loading
                ? const SizedBox.square(
                    dimension: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Réinitialiser'),
          ),
          TextButton(
            onPressed: _loading ? null : _requestCode,
            child: const Text('Renvoyer le code'),
          ),
        ],
      ],
    );
  }

  Widget _field(
    TextEditingController controller,
    String label,
    String hint,
    IconData icon, {
    bool obscure = false,
    TextInputType? keyboard,
  }) => TextField(
    controller: controller,
    obscureText: obscure,
    keyboardType: keyboard,
    decoration: InputDecoration(
      labelText: label,
      hintText: hint,
      prefixIcon: Icon(icon, size: 19),
    ),
  );
}

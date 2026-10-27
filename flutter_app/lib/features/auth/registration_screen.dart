import 'dart:ui' show ImageFilter;

import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_client.dart';
import '../../theme/app_colors.dart';

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({super.key});

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen> {
  final _scroll = ScrollController();
  final _firstName = TextEditingController();
  final _lastName = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _specialties = TextEditingController();
  final _password = TextEditingController();
  final _confirmation = TextEditingController();
  List<Map<String, dynamic>> _structures = [];
  XFile? _cv;
  int _step = 0;
  int? _structureId;

  bool _dark = false;
  bool _loadingData = true;
  bool _submitting = false;
  bool _success = false;
  String? _error;

  static const _titles = [
    'Identité & Sécurité',
    'Profil Professionnel',
    'Comités & Gouvernance',
  ];
  static const _descriptions = [
    'Renseignez vos informations de connexion de base.',
    'Précisez votre structure et vos compétences.',
    'Affectation technique et rôles nominatifs.',
  ];

  @override
  void initState() {
    super.initState();
    _loadOptions();
  }

  @override
  void dispose() {
    _scroll.dispose();
    for (final c in [
      _firstName,
      _lastName,
      _email,
      _phone,
      _specialties,
      _password,
      _confirmation,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _loadOptions() async {
    try {
      final response = await ApiClient.dio.get(
        '/api/v1/expert-registration/structures/',
      );
      if (!mounted) return;
      setState(() {
        _structures = _list(response.data);

        _loadingData = false;
      });
    } on DioException catch (e) {
      if (!mounted) return;
      setState(() {
        _loadingData = false;
        _error = _errorText(e);
      });
    }
  }

  List<Map<String, dynamic>> _list(dynamic data) {
    final raw = data is Map
        ? (data['results'] as List? ?? const [])
        : (data as List? ?? const []);
    return raw.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  String _errorText(DioException e) {
    final data = e.response?.data;
    if (data is Map) {
      if (data['error'] != null) return data['error'].toString();
      if (data['detail'] != null) return data['detail'].toString();
      return data.values.map((v) => v is List ? v.join(', ') : '$v').join('\n');
    }
    return 'Le service de candidature est momentanément indisponible.';
  }

  Future<void> _selectCv() async {
    try {
      final file = await openFile(
        acceptedTypeGroups: [
          const XTypeGroup(
            label: 'Curriculum Vitae',
            extensions: ['pdf', 'doc', 'docx'],
            uniformTypeIdentifiers: [
              'com.adobe.pdf',
              'com.microsoft.word.doc',
              'org.openxmlformats.wordprocessingml.document',
            ],
          ),
        ],
      );
      if (file == null) return;
      if (!RegExp(
        r'\.(pdf|docx?)$',
        caseSensitive: false,
      ).hasMatch(file.name)) {
        if (mounted) {
          setState(() => _error = 'Format PDF, DOC, DOCX uniquement.');
        }
        return;
      }
      final size = await file.length();
      if (!mounted) return;
      if (size > 5 * 1024 * 1024) {
        setState(() => _error = 'Le fichier CV ne doit pas dépasser 5 MB.');
        return;
      }
      setState(() {
        _cv = file;
        _error = null;
      });
    } catch (_) {
      if (mounted) {
        setState(() => _error = "Impossible d'ouvrir ce document. Réessayez.");
      }
    }
  }

  String? _validateStep() {
    if (_step == 0) {
      if (_firstName.text.trim().isEmpty ||
          _lastName.text.trim().isEmpty ||
          _email.text.trim().isEmpty ||
          _password.text.isEmpty ||
          _confirmation.text.isEmpty) {
        return 'Veuillez remplir tous les champs obligatoires avant de poursuivre.';
      }
      if (!RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(_email.text.trim())) {
        return 'Veuillez insérer une adresse email valide.';
      }
      if (_password.text.length < 8) {
        return 'Le mot de passe doit contenir au moins 8 caractères.';
      }
      if (_password.text != _confirmation.text) {
        return 'Les mots de passe ne correspondent pas.';
      }
    }
    if (_step == 1 && _structureId == null) {
      return 'Veuillez sélectionner votre structure officielle.';
    }
    return null;
  }

  void _scrollToTop() {
    if (!_scroll.hasClients) return;
    _scroll.animateTo(
      0,
      duration: const Duration(milliseconds: 280),
      curve: Curves.easeOut,
    );
  }

  void _next() {
    final message = _validateStep();
    if (message != null) {
      setState(() => _error = message);
      _scrollToTop();
      return;
    }
    setState(() {
      _step++;
      _error = null;
    });
    _scrollToTop();
  }

  void _previous() {
    setState(() {
      _step--;
      _error = null;
    });
    _scrollToTop();
  }

  Future<void> _submit() async {
    if (_submitting) return;
    final message = _validateStep();
    if (message != null) {
      setState(() => _error = message);
      _scrollToTop();
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final cv = _cv;
      final body = FormData.fromMap({
        'email': _email.text.trim().toLowerCase(),
        'password': _password.text,
        'password_confirm': _confirmation.text,
        'first_name': _firstName.text.trim(),
        'last_name': _lastName.text.trim(),
        'whatsapp_number': _phone.text.trim(),
        'structure': _structureId,
        'specialties': _specialties.text.trim(),
        if (cv != null)
          'cv': MultipartFile.fromBytes(
            await cv.readAsBytes(),
            filename: cv.name,
          ),
      });
      await ApiClient.dio.post(
        '/api/v1/expert-registration/candidature/',
        data: body,
      );
      if (mounted) {
        setState(() => _success = true);
        _scrollToTop();
      }
    } on DioException catch (e) {
      if (mounted) setState(() => _error = _errorText(e));
    } catch (_) {
      if (mounted) {
        setState(
          () => _error =
              "Le document n'a pas pu être lu. Sélectionnez-le à nouveau.",
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = _dark ? _Palette.dark : _Palette.light;
    return Scaffold(
      backgroundColor: p.gradientEnd,
      body: Stack(
        children: [
          Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [p.gradientStart, p.gradientEnd],
                ),
              ),
            ),
          ),
          Positioned(
            top: -150,
            left: -200,
            child: _Glow(color: p.glow, size: 500),
          ),
          Positioned(
            bottom: -150,
            right: -200,
            child: _Glow(color: p.glow, size: 500),
          ),
          const Positioned(top: 0, left: 0, right: 0, child: _FlagBar()),
          Positioned(
            top: 24,
            right: 24,
            child: _ThemeToggle(
              dark: _dark,
              palette: p,
              onTap: () => setState(() => _dark = !_dark),
            ),
          ),
          SafeArea(
            top: false,
            child: LayoutBuilder(
              builder: (context, constraints) {
                final wide = constraints.maxWidth >= 640;
                return SingleChildScrollView(
                  controller: _scroll,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 48,
                  ),
                  child: Center(
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 672),
                      child: Column(
                        children: [
                          _header(p, wide),
                          const SizedBox(height: 32),
                          _card(p, wide),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _header(_Palette p, bool wide) {
    return Column(
      children: [
        Container(
          width: 64,
          height: 64,
          decoration: BoxDecoration(
            color: AppColors.brand500.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: AppColors.brand500.withValues(alpha: 0.2),
            ),
            boxShadow: [
              BoxShadow(
                color: AppColors.brand500.withValues(alpha: 0.15),
                blurRadius: 30,
              ),
            ],
          ),
          child: const Icon(
            Icons.gpp_good_outlined,
            size: 32,
            color: AppColors.brand400,
          ),
        ),
        const SizedBox(height: 20),
        Text(
          'DEVENIR EXPERT',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: wide ? 30 : 24,
            fontWeight: FontWeight.w900,
            letterSpacing: wide ? 3 : 2.4,
            height: 1.15,
            color: p.title,
          ),
        ),
        const SizedBox(height: 8),
        const Text(
          "BUREAU D'ACCÈS TECHNIQUE CNE-ITP",
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            letterSpacing: 2.4,
            color: AppColors.brand500,
          ),
        ),
      ],
    );
  }

  Widget _card(_Palette p, bool wide) {
    final pad = wide ? 40.0 : 24.0;
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: p.card,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: p.cardBorder),
        boxShadow: p.cardShadow,
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              height: 4,
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    Color(0x33009FE3),
                    Color(0xCC33B7EF),
                    Color(0x33009FE3),
                  ],
                ),
              ),
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(pad, pad, pad, _success ? pad : 32),
              child: _body(p, wide),
            ),
            if (!_success) _footer(p, wide),
          ],
        ),
      ),
    );
  }

  Widget _body(_Palette p, bool wide) {
    if (_success) {
      return Column(
        children: [
          const SizedBox(height: 8),
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: p.successText.withValues(alpha: 0.1),
            ),
            child: Icon(
              Icons.mark_email_read_outlined,
              size: 40,
              color: p.successText,
            ),
          ),
          const SizedBox(height: 22),
          Text(
            'Candidature envoyée',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: p.title,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            "Votre dossier est enregistré et sera examiné par l'administration.",
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 13, height: 1.6, color: p.desc),
          ),
          const SizedBox(height: 26),
          _PrimaryButton(
            label: 'REVENIR À LA CONNEXION',
            icon: Icons.arrow_forward,
            palette: p,
            onTap: () => context.go('/login'),
          ),
        ],
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _stepHeader(p),
        if (_error != null) ...[_errorBox(p), const SizedBox(height: 24)],
        if (_step == 0) _identityStep(p, wide),
        if (_step == 1) _profileStep(p, wide),
        if (_step == 2) _governanceStep(p),
        _navigation(p, wide),
        const SizedBox(height: 16),
        _infoNote(p),
      ],
    );
  }

  Widget _stepHeader(_Palette p) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _titles[_step],
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      height: 1.3,
                      color: p.title,
                    ),
                  ),
                  Text(
                    _descriptions[_step],
                    style: TextStyle(fontSize: 12, color: p.desc),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: AppColors.brand500.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: AppColors.brand500.withValues(alpha: 0.2),
                ),
              ),
              child: Text(
                'Étape ${_step + 1} / 3',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: AppColors.brand500,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        ClipRRect(
          borderRadius: BorderRadius.circular(999),
          child: SizedBox(
            height: 6,
            child: Stack(
              fit: StackFit.expand,
              children: [
                ColoredBox(color: p.progressTrack),
                TweenAnimationBuilder<double>(
                  tween: Tween(end: (_step + 1) / 3),
                  duration: const Duration(milliseconds: 300),
                  curve: Curves.easeOut,
                  builder: (context, value, _) => FractionallySizedBox(
                    alignment: Alignment.centerLeft,
                    widthFactor: value,
                    child: const ColoredBox(color: AppColors.brand500),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 32),
      ],
    );
  }

  Widget _errorBox(_Palette p) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.danger.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.danger.withValues(alpha: 0.2)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(top: 1),
            child: Icon(Icons.error_outline, size: 20, color: AppColors.danger),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              _error!,
              style: const TextStyle(
                fontSize: 12,
                height: 1.6,
                fontWeight: FontWeight.w500,
                color: AppColors.danger,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _identityStep(_Palette p, bool wide) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _two(
          wide,
          _labeledField(
            p,
            _firstName,
            'Prénom',
            'Votre prénom',
            Icons.text_fields,
          ),
          _labeledField(
            p,
            _lastName,
            'Nom et Post-nom',
            'Votre nom et post-nom',
            Icons.text_fields,
          ),
        ),
        const SizedBox(height: 20),
        _two(
          wide,
          _labeledField(
            p,
            _email,
            'Email',
            'votre.email@exemple.com',
            Icons.mail_outline,
            keyboard: TextInputType.emailAddress,
          ),
          _labeledField(
            p,
            _phone,
            'Numéro WhatsApp',
            '+243 81 234 5678',
            Icons.phone_outlined,
            keyboard: TextInputType.phone,
          ),
        ),
        const SizedBox(height: 20),
        _two(
          wide,
          _labeledField(
            p,
            _password,
            'Mot de passe',
            'Min 8 caractères',
            Icons.lock_outline,
            obscure: true,
          ),
          _labeledField(
            p,
            _confirmation,
            'Confirmer mot de passe',
            'Confirmez',
            Icons.gpp_good_outlined,
            obscure: true,
          ),
        ),
      ],
    );
  }

  Widget _profileStep(_Palette p, bool wide) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [_label(p, "Organisation d'origine"), _structureSelect(p)],
        ),
        const SizedBox(height: 24),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _label(p, 'Domaines de compétence'),
            _input(
              p,
              _specialties,
              'Ex: Géotechnique tropicale, Dimensionnement des ponts, BIM ISO 19650...',
              null,
              maxLines: 3,
            ),
          ],
        ),
        const SizedBox(height: 24),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _label(p, 'Curriculum Vitae (CV)'),
            _cvBox(p),
            if (!_loadingData && _structures.isEmpty)
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton(
                  onPressed: _loadOptions,
                  style: TextButton.styleFrom(
                    padding: EdgeInsets.zero,
                    foregroundColor: AppColors.brand600,
                  ),
                  child: const Text(
                    'Recharger les organisations',
                    style: TextStyle(fontSize: 12),
                  ),
                ),
              ),
          ],
        ),
      ],
    );
  }

  Widget _governanceStep(_Palette p) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: p.panelBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: p.panelBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Choix de votre groupe de travail',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w700,
              color: p.title,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Après validation de votre compte, vous pourrez choisir votre '
            'sous-commission et l’un des 35 groupes de travail du rapport '
            'adopté dans la mise à jour de votre profil. Votre choix sera '
            'examiné avant tout rattachement institutionnel.',
            style: TextStyle(fontSize: 14, height: 1.7, color: p.panelText),
          ),
          const SizedBox(height: 8),
          Text(
            'Les fonctions du Comité de pilotage et de la Coordination du '
            'Secrétariat technique sont attribuées sur décision vérifiée ; '
            'l’inscription ne crée aucun mandat.',
            style: TextStyle(fontSize: 14, height: 1.7, color: p.panelText),
          ),
        ],
      ),
    );
  }

  Widget _navigation(_Palette p, bool wide) {
    final previous = _SecondaryButton(
      palette: p,
      onTap: _submitting ? null : _previous,
    );

    Widget nextButton({required bool expand}) => _PrimaryButton(
      label: 'ÉTAPE SUIVANTE',
      icon: Icons.arrow_forward,
      palette: p,
      onTap: _submitting ? null : _next,
      compact: !expand,
    );

    Widget submitButton() => _PrimaryButton(
      label: 'SOUMETTRE LA CANDIDATURE',
      icon: Icons.check,
      palette: p,
      onTap: _submitting ? null : _submit,
      loading: _submitting,
      loadingLabel: 'TRAITEMENT DE LA CANDIDATURE...',
    );

    final buttons = <Widget>[];
    if (_step == 0) {
      buttons.add(nextButton(expand: true));
    } else if (_step == 1) {
      if (!wide) {
        buttons
          ..add(previous)
          ..add(const SizedBox(height: 12))
          ..add(nextButton(expand: true));
      } else {
        buttons.add(
          Row(children: [previous, const Spacer(), nextButton(expand: false)]),
        );
      }
    } else {
      if (!wide) {
        buttons
          ..add(previous)
          ..add(const SizedBox(height: 12))
          ..add(submitButton());
      } else {
        buttons.add(
          Row(
            children: [
              previous,
              const SizedBox(width: 20),
              Expanded(child: submitButton()),
            ],
          ),
        );
      }
    }

    return Padding(
      padding: const EdgeInsets.only(top: 24),
      child: Container(
        padding: const EdgeInsets.only(top: 24),
        decoration: BoxDecoration(
          border: Border(top: BorderSide(color: p.panelBorder)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: buttons,
        ),
      ),
    );
  }

  Widget _infoNote(_Palette p) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.brand500.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.brand500.withValues(alpha: 0.1)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(top: 2),
            child: Icon(
              Icons.info_outline,
              size: 20,
              color: AppColors.brand500,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text.rich(
              TextSpan(
                style: TextStyle(fontSize: 11, height: 1.6, color: p.infoText),
                children: [
                  const TextSpan(
                    text:
                        "Votre demande d'inscription sera directement soumise "
                        'en statut ',
                  ),
                  TextSpan(
                    text: 'En attente (PENDING)',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: p.title,
                    ),
                  ),
                  const TextSpan(
                    text:
                        ' auprès de la Haute Direction pour authentification '
                        'des mandats.',
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _footer(_Palette p, bool wide) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(wide ? 32 : 24),
      decoration: BoxDecoration(
        color: p.footerBg,
        border: Border(top: BorderSide(color: p.footerBorder)),
      ),
      child: Wrap(
        alignment: WrapAlignment.center,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          Text(
            'Vous possédez déjà un compte validé ?',
            style: TextStyle(fontSize: 12, color: p.footerText),
          ),
          const SizedBox(width: 4),
          InkWell(
            onTap: () => context.go('/login'),
            borderRadius: BorderRadius.circular(4),
            child: const Padding(
              padding: EdgeInsets.symmetric(vertical: 4),
              child: Text(
                'SE CONNECTER',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.6,
                  color: AppColors.brand500,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _label(_Palette p, String text) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8),
      child: Text(
        text.toUpperCase(),
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.1,
          color: p.label,
        ),
      ),
    );
  }

  Widget _labeledField(
    _Palette p,
    TextEditingController controller,
    String label,
    String hint,
    IconData icon, {
    bool obscure = false,
    TextInputType? keyboard,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _label(p, label),
        _input(p, controller, hint, icon, obscure: obscure, keyboard: keyboard),
      ],
    );
  }

  Widget _input(
    _Palette p,
    TextEditingController controller,
    String hint,
    IconData? icon, {
    bool obscure = false,
    TextInputType? keyboard,
    int maxLines = 1,
  }) {
    final multiline = maxLines > 1;
    return TextField(
      controller: controller,
      obscureText: obscure,
      keyboardType: keyboard,
      maxLines: maxLines,
      cursorColor: AppColors.brand500,
      style: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w500,
        letterSpacing: obscure ? 2 : 0,
        color: p.inputText,
      ),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w500,
          letterSpacing: obscure ? 2 : 0,
          color: p.inputHint,
        ),
        filled: true,
        fillColor: p.inputBg,
        isDense: true,
        contentPadding: EdgeInsets.fromLTRB(
          icon == null ? 16 : 0,
          multiline ? 12 : 13,
          16,
          multiline ? 12 : 13,
        ),
        prefixIcon: icon == null
            ? null
            : Icon(icon, size: 18, color: p.inputIcon),
        prefixIconConstraints: const BoxConstraints(
          minWidth: 44,
          minHeight: 44,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: p.inputBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.brand500, width: 1.6),
        ),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  Widget _structureSelect(_Palette p) {
    return Container(
      height: 46,
      padding: const EdgeInsets.symmetric(horizontal: 14),
      decoration: BoxDecoration(
        color: p.inputBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: p.inputBorder),
      ),
      child: Row(
        children: [
          Icon(Icons.apartment_outlined, size: 18, color: p.inputIcon),
          const SizedBox(width: 11),
          Expanded(
            child: DropdownButtonHideUnderline(
              child: DropdownButton<int>(
                value: _structureId,
                isExpanded: true,
                isDense: true,
                itemHeight: 48,
                borderRadius: BorderRadius.circular(12),
                dropdownColor: p.menuBg,
                hint: Text(
                  'Sélectionnez votre structure officielle',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: p.inputHint,
                  ),
                ),
                icon: _loadingData
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: AppColors.brand500,
                        ),
                      )
                    : Icon(
                        Icons.keyboard_arrow_down,
                        size: 18,
                        color: p.inputIcon,
                      ),
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  color: p.inputText,
                ),
                items: [
                  for (final item in _structures)
                    DropdownMenuItem(
                      value: item['id'] as int,
                      child: Text(
                        '${item['name']}',
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                ],
                onChanged: _loadingData
                    ? null
                    : (value) => setState(() => _structureId = value),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _cvBox(_Palette p) {
    final hasFile = _cv != null;
    return CustomPaint(
      foregroundPainter: _DashedRRectPainter(color: p.cvBorder, radius: 12),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: _selectCv,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
            decoration: BoxDecoration(
              color: p.cvBg,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              children: [
                if (!hasFile) ...[
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: p.cvCircle,
                      boxShadow: p.cvCircleShadow,
                    ),
                    child: Icon(
                      Icons.upload_outlined,
                      size: 24,
                      color: p.cvIcon,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Cliquez pour ajouter le document',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: p.cvTitle,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Format PDF, DOC, DOCX uniquement (Max: 5MB)',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12, color: p.cvSubtitle),
                  ),
                ] else ...[
                  Icon(Icons.check_circle, size: 32, color: p.successText),
                  const SizedBox(height: 8),
                  Text(
                    'Document attaché',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: p.successText,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _cv!.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 12, color: p.cvSubtitle),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _two(bool wide, Widget a, Widget b) {
    if (!wide) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [a, const SizedBox(height: 20), b],
      );
    }
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(child: a),
        const SizedBox(width: 20),
        Expanded(child: b),
      ],
    );
  }
}

class _FlagBar extends StatelessWidget {
  const _FlagBar();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 4,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: const [
          Expanded(child: ColoredBox(color: Color(0xFF009FE3))),
          Expanded(child: ColoredBox(color: Color(0xFFFFED00))),
          Expanded(child: ColoredBox(color: Color(0xFFE30613))),
        ],
      ),
    );
  }
}

class _Glow extends StatelessWidget {
  const _Glow({required this.color, required this.size});

  final Color color;
  final double size;

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: ImageFiltered(
        imageFilter: ImageFilter.blur(sigmaX: 60, sigmaY: 60),
        child: Container(
          width: size,
          height: size,
          decoration: BoxDecoration(shape: BoxShape.circle, color: color),
        ),
      ),
    );
  }
}

class _ThemeToggle extends StatelessWidget {
  const _ThemeToggle({
    required this.dark,
    required this.palette,
    required this.onTap,
  });

  final bool dark;
  final _Palette palette;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(999),
        child: Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: palette.toggleBg,
            border: Border.all(color: palette.toggleBorder),
            boxShadow: palette.toggleShadow,
          ),
          child: Icon(
            dark ? Icons.light_mode_outlined : Icons.dark_mode_outlined,
            size: 20,
            color: palette.toggleIcon,
          ),
        ),
      ),
    );
  }
}

class _PrimaryButton extends StatelessWidget {
  const _PrimaryButton({
    required this.label,
    required this.icon,
    required this.palette,
    required this.onTap,
    this.compact = false,
    this.loading = false,
    this.loadingLabel,
  });

  final String label;
  final IconData icon;
  final _Palette palette;
  final VoidCallback? onTap;
  final bool compact;
  final bool loading;
  final String? loadingLabel;

  @override
  Widget build(BuildContext context) {
    final enabled = onTap != null;
    return Opacity(
      opacity: enabled ? 1 : 0.6,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: AppColors.brand500.withValues(alpha: 0.2),
              blurRadius: 20,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Material(
          color: AppColors.brand500,
          borderRadius: BorderRadius.circular(12),
          clipBehavior: Clip.antiAlias,
          child: InkWell(
            onTap: onTap,
            child: Padding(
              padding: compact
                  ? const EdgeInsets.symmetric(horizontal: 24, vertical: 14)
                  : const EdgeInsets.symmetric(horizontal: 24, vertical: 17),
              child: Row(
                mainAxisSize: compact ? MainAxisSize.min : MainAxisSize.max,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (loading) ...[
                    const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.black,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Flexible(
                      child: Text(
                        loadingLabel ?? label,
                        textAlign: TextAlign.center,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: compact ? 12 : 14,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.4,
                          color: Colors.black,
                        ),
                      ),
                    ),
                  ] else ...[
                    Flexible(
                      child: Text(
                        label,
                        textAlign: TextAlign.center,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: compact ? 12 : 14,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.4,
                          color: Colors.black,
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Icon(icon, size: compact ? 18 : 20, color: Colors.black),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _SecondaryButton extends StatelessWidget {
  const _SecondaryButton({required this.palette, required this.onTap});

  final _Palette palette;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final enabled = onTap != null;
    return Opacity(
      opacity: enabled ? 1 : 0.6,
      child: Material(
        color: palette.prevBg,
        borderRadius: BorderRadius.circular(12),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.arrow_back, size: 16, color: palette.prevText),
                const SizedBox(width: 8),
                Text(
                  'PRÉCÉDENT',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.2,
                    color: palette.prevText,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _DashedRRectPainter extends CustomPainter {
  _DashedRRectPainter({required this.color, required this.radius});

  final Color color;
  final double radius;

  static const double _strokeWidth = 2;
  static const double _dash = 5;
  static const double _gap = 4;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = _strokeWidth;
    final path = Path()
      ..addRRect(
        RRect.fromRectAndRadius(Offset.zero & size, Radius.circular(radius)),
      );
    for (final metric in path.computeMetrics()) {
      var distance = 0.0;
      while (distance < metric.length) {
        final end = distance + _dash;
        canvas.drawPath(
          metric.extractPath(
            distance,
            end > metric.length ? metric.length : end,
          ),
          paint,
        );
        distance = end + _gap;
      }
    }
  }

  @override
  bool shouldRepaint(_DashedRRectPainter oldDelegate) =>
      oldDelegate.color != color || oldDelegate.radius != radius;
}

class _Palette {
  const _Palette({
    required this.gradientStart,
    required this.gradientEnd,
    required this.glow,
    required this.card,
    required this.cardBorder,
    required this.cardShadow,
    required this.title,
    required this.desc,
    required this.label,
    required this.inputBg,
    required this.inputBorder,
    required this.inputText,
    required this.inputHint,
    required this.inputIcon,
    required this.progressTrack,
    required this.prevBg,
    required this.prevText,
    required this.panelBg,
    required this.panelBorder,
    required this.panelText,
    required this.footerBg,
    required this.footerBorder,
    required this.footerText,
    required this.infoText,
    required this.cvBg,
    required this.cvBorder,
    required this.cvTitle,
    required this.cvSubtitle,
    required this.cvCircle,
    required this.cvCircleShadow,
    required this.cvIcon,
    required this.toggleBg,
    required this.toggleBorder,
    required this.toggleIcon,
    required this.toggleShadow,
    required this.menuBg,
    required this.successText,
  });

  final Color gradientStart;
  final Color gradientEnd;
  final Color glow;
  final Color card;
  final Color cardBorder;
  final List<BoxShadow> cardShadow;
  final Color title;
  final Color desc;
  final Color label;
  final Color inputBg;
  final Color inputBorder;
  final Color inputText;
  final Color inputHint;
  final Color inputIcon;
  final Color progressTrack;
  final Color prevBg;
  final Color prevText;
  final Color panelBg;
  final Color panelBorder;
  final Color panelText;
  final Color footerBg;
  final Color footerBorder;
  final Color footerText;
  final Color infoText;
  final Color cvBg;
  final Color cvBorder;
  final Color cvTitle;
  final Color cvSubtitle;
  final Color cvCircle;
  final List<BoxShadow> cvCircleShadow;
  final Color cvIcon;
  final Color toggleBg;
  final Color toggleBorder;
  final Color toggleIcon;
  final List<BoxShadow> toggleShadow;
  final Color menuBg;
  final Color successText;

  static const light = _Palette(
    gradientStart: Color(0xFFE6F6FD),
    gradientEnd: Color(0xFFF1F5F9),
    glow: Color(0x0D009FE3),
    card: Color(0xE6FFFFFF),
    cardBorder: Color(0xFFE2E8F0),
    cardShadow: [
      BoxShadow(
        color: Color(0x1A000000),
        blurRadius: 25,
        spreadRadius: -5,
        offset: Offset(0, 20),
      ),
      BoxShadow(
        color: Color(0x1A000000),
        blurRadius: 10,
        spreadRadius: -6,
        offset: Offset(0, 8),
      ),
    ],
    title: Color(0xFF0F172A),
    desc: Color(0xFF475569),
    label: Color(0xFF64748B),
    inputBg: Color(0xFFFFFFFF),
    inputBorder: Color(0xFFCBD5E1),
    inputText: Color(0xFF0F172A),
    inputHint: Color(0xFF94A3B8),
    inputIcon: Color(0xFF94A3B8),
    progressTrack: Color(0xFFE2E8F0),
    prevBg: Color(0xFFE2E8F0),
    prevText: Color(0xFF0F172A),
    panelBg: Color(0xFFF9FBFC),
    panelBorder: Color(0xFFE2E8F0),
    panelText: Color(0xFF334155),
    footerBg: Color(0xCCF8FAFC),
    footerBorder: Color(0xFFE2E8F0),
    footerText: Color(0xFF475569),
    infoText: Color(0xFF475569),
    cvBg: Color(0xFFF8FAFC),
    cvBorder: Color(0xFFCBD5E1),
    cvTitle: Color(0xFF1E293B),
    cvSubtitle: Color(0xFF64748B),
    cvCircle: Color(0xFFFFFFFF),
    cvCircleShadow: [
      BoxShadow(color: Color(0x14000000), blurRadius: 2, offset: Offset(0, 1)),
    ],
    cvIcon: Color(0xFF64748B),
    toggleBg: Color(0xCCFFFFFF),
    toggleBorder: Color(0xFFE2E8F0),
    toggleIcon: Color(0xFF334155),
    toggleShadow: [
      BoxShadow(color: Color(0x14000000), blurRadius: 12, offset: Offset(0, 4)),
    ],
    menuBg: Color(0xFFFFFFFF),
    successText: Color(0xFF16A34A),
  );

  static const dark = _Palette(
    gradientStart: Color(0xFF07141C),
    gradientEnd: Color(0xFF020204),
    glow: Color(0x0D009FE3),
    card: Color(0xCC06060C),
    cardBorder: Color(0x0DFFFFFF),
    cardShadow: [BoxShadow(color: Color(0x80000000), blurRadius: 50)],
    title: Color(0xFFFFFFFF),
    desc: Color(0xFF64748B),
    label: Color(0xFF64748B),
    inputBg: Color(0x0DFFFFFF),
    inputBorder: Color(0x1AFFFFFF),
    inputText: Color(0xFFFFFFFF),
    inputHint: Color(0xFF475569),
    inputIcon: Color(0xFF64748B),
    progressTrack: Color(0x1AFFFFFF),
    prevBg: Color(0x0DFFFFFF),
    prevText: Color(0xFFFFFFFF),
    panelBg: Color(0x05FFFFFF),
    panelBorder: Color(0x1AFFFFFF),
    panelText: Color(0xFFCBD5E1),
    footerBg: Color(0x0DFFFFFF),
    footerBorder: Color(0x0DFFFFFF),
    footerText: Color(0xFF94A3B8),
    infoText: Color(0xFF94A3B8),
    cvBg: Color(0x0DFFFFFF),
    cvBorder: Color(0x1AFFFFFF),
    cvTitle: Color(0xFFFFFFFF),
    cvSubtitle: Color(0xFF94A3B8),
    cvCircle: Color(0x0DFFFFFF),
    cvCircleShadow: [],
    cvIcon: Color(0xFF94A3B8),
    toggleBg: Color(0x0DFFFFFF),
    toggleBorder: Color(0x1AFFFFFF),
    toggleIcon: Color(0xFFFACC15),
    toggleShadow: [],
    menuBg: Color(0xFF0B0B12),
    successText: Color(0xFF4ADE80),
  );
}

import 'package:flutter/material.dart';
import 'package:dio/dio.dart';

import '../../../core/api/api_client.dart';
import 'expert_theme.dart';

class ExpertProfileTab extends StatefulWidget {
  const ExpertProfileTab({
    super.key,
    required this.dark,
    required this.fallbackName,
    required this.fallbackEmail,
    required this.onThemeChanged,
    this.onAffiliationSaved,
  });

  final bool dark;
  final String fallbackName;
  final String fallbackEmail;
  final ValueChanged<bool> onThemeChanged;
  final VoidCallback? onAffiliationSaved;

  @override
  State<ExpertProfileTab> createState() => _ExpertProfileTabState();
}

class _ExpertProfileTabState extends State<ExpertProfileTab> {
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _specialties = TextEditingController();
  final _account = TextEditingController();
  final _structure = TextEditingController();

  Map<String, dynamic> _expert = const {};
  String _ctm = '';
  List<Map<String, dynamic>> _ctms = [];
  List<Map<String, dynamic>> _workgroups = [];
  Set<String> _selectedWgs = {};
  Set<String> _bureauCtms = {};
  bool _affiliationDirty = false;
  bool _saving = false;
  String? _loadError;
  final _affiliationKey = GlobalKey();
  String _payout = 'Equity BCDC';
  String _roleId = 'EXPERT';
  bool _loading = true;
  bool _dirty = false;
  bool _notifications = true;

  @override
  void initState() {
    super.initState();
    _name.text = widget.fallbackName;
    _email.text = widget.fallbackEmail;
    _load();
  }

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _phone.dispose();
    _specialties.dispose();
    _account.dispose();
    _structure.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final resp = await ApiClient.dio.get('/api/v1/experts/me/');
      final data = Map<String, dynamic>.from(resp.data as Map);
      final affiliationResponse = await ApiClient.dio.get(
        '/api/v1/experts/my-affiliation/',
      );
      final affiliation = Map<String, dynamic>.from(
        affiliationResponse.data as Map,
      );
      if (!mounted) return;
      final user = data['user'] is Map
          ? Map<String, dynamic>.from(data['user'] as Map)
          : const <String, dynamic>{};
      final structure = data['structure'] is Map
          ? Map<String, dynamic>.from(data['structure'] as Map)
          : const <String, dynamic>{};
      final fullName = '${user['first_name'] ?? ''} ${user['last_name'] ?? ''}'
          .trim();
      setState(() {
        _expert = data;
        _name.text = fullName.isEmpty ? widget.fallbackName : fullName;
        _email.text = (user['email'] as String?) ?? widget.fallbackEmail;
        _phone.text = (user['phone'] as String?) ?? '';
        _specialties.text = (data['specialties'] as String?) ?? '';
        _account.text = (data['bank_account'] as String?) ?? '';
        _payout = (data['bank_name'] as String?)?.trim().isNotEmpty == true
            ? data['bank_name'] as String
            : 'Equity BCDC';
        _structure.text = (structure['name'] as String?) ?? '';
        _ctm = affiliation['ctm']?.toString() ?? '';
        _ctms = (affiliation['ctms'] as List)
            .map((e) => Map<String, dynamic>.from(e as Map))
            .toList();
        _workgroups = (affiliation['workgroups'] as List)
            .map((e) => Map<String, dynamic>.from(e as Map))
            .toList();
        _selectedWgs = (affiliation['wgs'] as List)
            .map((e) => e.toString())
            .toSet();
        _bureauCtms = (affiliation['bureau_ctm_ids'] as List)
            .map((e) => e.toString())
            .toSet();
        _loadError = null;
        _roleId = (data['role_id'] as String?) ?? 'EXPERT';
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _loadError = 'Impossible de charger le profil et les sous-commissions.';
      });
    }
  }

  void _markDirty([String? _]) {
    if (!_dirty) setState(() => _dirty = true);
  }

  Future<void> _save(ExpertPalette p) async {
    if (_saving) return;
    if (_affiliationDirty &&
        (_ctm.isEmpty || (_availableWgs.isNotEmpty && _selectedWgs.isEmpty))) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Choisissez une sous-commission et un groupe de travail.',
          ),
        ),
      );
      return;
    }
    setState(() => _saving = true);
    final id = _expert['id'];
    final parts = _name.text
        .trim()
        .split(RegExp(r'\s+'))
        .where((part) => part.isNotEmpty)
        .toList();
    final firstName = parts.length > 1
        ? parts.sublist(0, parts.length - 1).join(' ')
        : '';
    final lastName = parts.isEmpty ? '' : parts.last;
    try {
      if (_affiliationDirty) {
        await ApiClient.dio.patch(
          '/api/v1/experts/my-affiliation/',
          data: {
            'ctm': int.parse(_ctm),
            'wgs': _selectedWgs.map(int.parse).toList(),
          },
        );
        _affiliationDirty = false;
        widget.onAffiliationSaved?.call();
      }
      final requests = <Future<dynamic>>[
        ApiClient.dio.patch(
          '/api/v1/auth/profile/',
          data: {
            'first_name': firstName,
            'last_name': lastName,
            'email': _email.text.trim(),
            'phone': _phone.text.trim(),
          },
        ),
      ];
      if (id != null) {
        requests.add(
          ApiClient.dio.patch(
            '/api/v1/experts/$id/',
            data: {
              'specialties': _specialties.text,
              'bank_name': _payout,
              'bank_account': _account.text,
            },
          ),
        );
      }
      await Future.wait(requests);
      if (!mounted) return;
      setState(() => _dirty = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Profil enregistré.'),
          backgroundColor: p.card,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            error is DioException && error.response?.data is Map
                ? (error.response!.data as Map).values
                      .map(
                        (value) => value is List ? value.join(' ') : '$value',
                      )
                      .join('\n')
                : 'Enregistrement impossible. Vérifiez la connexion au serveur.',
          ),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 32),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 896),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _header(p),
              const SizedBox(height: 14),
              _cvButton(p),
              const SizedBox(height: 22),
              if (_loading)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 60),
                  child: Center(
                    child: CircularProgressIndicator(
                      color: p.blue,
                      strokeWidth: 2,
                    ),
                  ),
                )
              else if (_loadError != null)
                Column(
                  children: [
                    Text(_loadError!, style: TextStyle(color: p.muted)),
                    TextButton(
                      onPressed: () {
                        setState(() => _loading = true);
                        _load();
                      },
                      child: const Text('Réessayer'),
                    ),
                  ],
                )
              else
                LayoutBuilder(
                  builder: (context, constraints) {
                    final twoColumns = constraints.maxWidth >= 760;
                    final left = _leftColumn(p);
                    final right = _rightColumn(p);
                    if (!twoColumns) {
                      return Column(
                        children: [left, const SizedBox(height: 24), right],
                      );
                    }
                    return Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(child: left),
                        const SizedBox(width: 24),
                        Expanded(child: right),
                      ],
                    );
                  },
                ),
              if (_dirty) ...[
                const SizedBox(height: 20),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.only(top: 16),
                  decoration: BoxDecoration(
                    border: Border(top: BorderSide(color: p.border)),
                  ),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: FilledButton.icon(
                      onPressed: _saving ? null : () => _save(p),
                      style: FilledButton.styleFrom(
                        backgroundColor: p.blue,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 20,
                          vertical: 13,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                      icon: const Icon(Icons.save_outlined, size: 15),
                      label: const Text(
                        'SAUVEGARDER',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _header(ExpertPalette p) {
    return Row(
      children: [
        Container(
          width: 34,
          height: 34,
          decoration: BoxDecoration(
            color: p.blueSoft,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: p.blue.withValues(alpha: 0.2)),
          ),
          child: Icon(Icons.person_outline, size: 19, color: p.blue),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'MON PROFIL EXPERT',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.5,
                  color: p.title,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                'Mettez à jour vos informations personnelles et professionnelles.',
                style: TextStyle(fontSize: 10.5, color: p.muted),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _cvButton(ExpertPalette p) {
    return Material(
      color: p.isDark ? const Color(0xFF1D4ED8) : const Color(0xFF1D4ED8),
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        onTap: () {
          final target = _affiliationKey.currentContext;
          if (target != null) {
            Scrollable.ensureVisible(
              target,
              duration: const Duration(milliseconds: 300),
              alignment: 0.2,
            );
          }
        },
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Flexible(
                child: Text(
                  'Choisir ma sous-commission et mon groupe de travail',
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w600,
                    color: Colors.white,
                    decoration: TextDecoration.underline,
                    decorationColor: Colors.white.withValues(alpha: 0.7),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              const Text(
                '→',
                style: TextStyle(fontSize: 12, color: Colors.white),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _leftColumn(ExpertPalette p) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _sectionTitle(p, '1', "FICHE D'IDENTITÉ", p.blue),
        const SizedBox(height: 12),
        _textField(
          p,
          label: "Nom complet de l'expert :",
          controller: _name,
          icon: Icons.person_outline,
          hint: 'Ex: Ir. Jean-Pierre Kabange',
          onChanged: _markDirty,
        ),
        _textField(
          p,
          label: 'Adresse courriel :',
          controller: _email,
          icon: Icons.mail_outline,
          hint: 'Ex: jp.kabange@cne-itp.cd',
          monospace: true,
          onChanged: _markDirty,
        ),
        _textField(
          p,
          label: "Structure d'affiliation :",
          controller: _structure,
          icon: Icons.business_outlined,
          hint: 'Définie par l\'administration',
          enabled: false,
          helper: "La structure est définie par l'administration.",
        ),
        _textField(
          p,
          label: 'Téléphone :',
          controller: _phone,
          icon: Icons.phone_outlined,
          hint: 'Ex: +243 970 000 000',
          monospace: true,
          onChanged: _markDirty,
        ),
        _textField(
          p,
          label: 'Spécialités :',
          controller: _specialties,
          icon: Icons.sell_outlined,
          hint: 'Ex: Électricité, Plomberie, ICT...',
          helper: 'Champ libre — séparez par des virgules.',
          onChanged: _markDirty,
        ),
        Container(
          key: _affiliationKey,
          child: _dropdownField(
            p,
            label: 'Sous-commission (CTM/SC) :',
            icon: Icons.layers_outlined,
            value: _ctm,
            items: _ctms.map((e) => '${e['id']}').toList(),
            labels: {for (final ctm in _ctms) '${ctm['id']}': '${ctm['name']}'},
            helper:
                'Choisissez votre sous-commission, puis sauvegardez le profil.',
            enabled: !_saving,
            onChanged: (value) => setState(() {
              _ctm = value ?? '';
              _selectedWgs = {};
              _affiliationDirty = true;
              _dirty = true;
            }),
          ),
        ),
        if (_bureauCtms.contains(_ctm))
          ..._availableWgs.map(
            (wg) => CheckboxListTile(
              dense: true,
              title: Text(
                '${wg['name']}',
                style: TextStyle(color: p.text, fontSize: 11.5),
              ),
              value: _selectedWgs.contains('${wg['id']}'),
              onChanged: _saving
                  ? null
                  : (selected) => setState(() {
                      if (selected == true) {
                        _selectedWgs.add('${wg['id']}');
                      } else {
                        _selectedWgs.remove('${wg['id']}');
                      }
                      _affiliationDirty = true;
                      _dirty = true;
                    }),
            ),
          )
        else
          _dropdownField(
            p,
            label: 'Groupe(s) de travail (WG) :',
            icon: Icons.workspaces_outline,
            value: _selectedWgs.firstOrNull ?? '',
            items: _availableWgs.map((e) => '${e['id']}').toList(),
            labels: {
              for (final wg in _availableWgs) '${wg['id']}': '${wg['name']}',
            },
            helper: _ctm.isEmpty
                ? 'Choisissez d’abord une sous-commission.'
                : _availableWgs.isEmpty
                ? 'Aucun groupe de travail pour cette sous-commission.'
                : 'Sélectionnez votre groupe de travail.',
            enabled: !_saving && _availableWgs.isNotEmpty,
            onChanged: (value) => setState(() {
              _selectedWgs = {?value};
              _affiliationDirty = true;
              _dirty = true;
            }),
          ),
        const SizedBox(height: 8),
        _sectionTitle(p, '2', 'COORDONNÉES FINANCIÈRES', p.indigo),
        const SizedBox(height: 12),
        LayoutBuilder(
          builder: (context, constraints) {
            final fields = [
              _dropdownField(
                p,
                label: 'Mode de règlement :',
                icon: Icons.account_balance_wallet_outlined,
                value: _payout,
                items: const [
                  'Equity BCDC',
                  'Rawbank',
                  'M-Pesa',
                  'Orange Money',
                ],
                onChanged: (value) {
                  setState(() => _payout = value ?? _payout);
                  _markDirty();
                },
              ),
              _textField(
                p,
                label: 'N° Compte / Coordonnées :',
                controller: _account,
                icon: Icons.numbers_outlined,
                hint: 'Ex: 00019-992381...',
                monospace: true,
                onChanged: _markDirty,
              ),
            ];
            if (constraints.maxWidth < 420) {
              return Column(children: fields);
            }
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(child: fields[0]),
                const SizedBox(width: 14),
                Expanded(child: fields[1]),
              ],
            );
          },
        ),
      ],
    );
  }

  Widget _rightColumn(ExpertPalette p) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _sectionTitle(p, '3', 'RÔLE ET PERMISSIONS', p.amber),
        const SizedBox(height: 12),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: p.amberSoft,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: p.amber.withValues(alpha: 0.22)),
          ),
          child: Text(
            "Le rôle réglementaire est attribué par l'administrateur du CNE-ITP et ne peut être modifié depuis cette interface.",
            style: TextStyle(
              fontSize: 11,
              height: 1.6,
              color: p.isDark ? p.amber : const Color(0xFF92400E),
            ),
          ),
        ),
        const SizedBox(height: 16),
        _sectionTitle(p, '4', 'STATISTIQUES ET RÉMUNÉRATION', p.teal),
        const SizedBox(height: 12),
        _readOnlyField(
          p,
          label: 'Taux journalier (simulation) :',
          value: '0 USD',
        ),
        _readOnlyField(
          p,
          label: 'Allocation mensuelle recherche (simulation) :',
          value: '0 USD',
        ),
        _readOnlyField(
          p,
          label: 'Nombre de présences (simulation) :',
          value: '0 Présences',
        ),
        _readOnlyField(
          p,
          label: 'ID du rôle (simulation) :',
          value: _roleId.toUpperCase(),
        ),
        const SizedBox(height: 8),
        _sectionTitle(p, '5', 'PRÉFÉRENCES', p.muted),
        const SizedBox(height: 12),
        _preferenceTile(
          p,
          icon: Icons.dark_mode_outlined,
          label: 'Thème',
          trailing: _themeSwitch(p),
        ),
        const SizedBox(height: 8),
        _preferenceTile(
          p,
          icon: Icons.notifications_none,
          label: 'Recevoir des notifications',
          trailing: Switch(
            value: _notifications,
            onChanged: (value) => setState(() => _notifications = value),
            activeTrackColor: p.green,
            activeThumbColor: Colors.white,
          ),
        ),
        const SizedBox(height: 16),
        _sectionTitle(p, '6', 'APPLICATION', p.sky),
        const SizedBox(height: 12),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: p.isDark ? Colors.white.withValues(alpha: 0.02) : p.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: p.border),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.smartphone, size: 16, color: p.sky),
                  const SizedBox(width: 8),
                  Text(
                    "Installer l'application",
                    style: TextStyle(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w600,
                      color: p.text,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                "Ajoutez CNE-ITP à votre écran d'accueil pour un accès rapide et une utilisation hors ligne.",
                style: TextStyle(fontSize: 10.5, height: 1.6, color: p.muted),
              ),
              const SizedBox(height: 10),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: () {},
                  style: FilledButton.styleFrom(
                    backgroundColor: const Color(0xFF0095C9),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 11),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  icon: const Icon(Icons.download, size: 14),
                  label: const Text(
                    "INSTALLER L'APPLICATION",
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  List<Map<String, dynamic>> get _availableWgs =>
      _workgroups.where((wg) => '${wg['ctm_id']}' == _ctm).toList();

  Widget _sectionTitle(
    ExpertPalette p,
    String number,
    String label,
    Color color,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 18,
              height: 18,
              decoration: BoxDecoration(
                color: color.withValues(alpha: p.isDark ? 0.18 : 0.13),
                shape: BoxShape.circle,
              ),
              child: Center(
                child: Text(
                  number,
                  style: TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w900,
                    color: color,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 7),
            Text(
              label,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w800,
                letterSpacing: 1.1,
                color: color,
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Container(height: 1, color: p.border),
      ],
    );
  }

  Widget _textField(
    ExpertPalette p, {
    required String label,
    required TextEditingController controller,
    required IconData icon,
    String? hint,
    String? helper,
    bool enabled = true,
    bool monospace = false,
    ValueChanged<String>? onChanged,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label.toUpperCase(),
            style: TextStyle(
              fontSize: 9,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.4,
              color: p.muted,
            ),
          ),
          const SizedBox(height: 5),
          Container(
            height: 36,
            padding: const EdgeInsets.symmetric(horizontal: 10),
            decoration: BoxDecoration(
              color: enabled ? p.field : p.surface,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: enabled ? p.borderStrong : p.border),
            ),
            child: Row(
              children: [
                Icon(icon, size: 15, color: p.subtle),
                const SizedBox(width: 8),
                Expanded(
                  child: enabled
                      ? TextField(
                          controller: controller,
                          onChanged: onChanged,
                          style: TextStyle(
                            fontSize: 11.5,
                            fontFamily: monospace ? 'monospace' : null,
                            fontWeight: FontWeight.w600,
                            color: p.text,
                          ),
                          decoration: InputDecoration(
                            isDense: true,
                            border: InputBorder.none,
                            hintText: hint,
                            hintStyle: TextStyle(fontSize: 11, color: p.subtle),
                            contentPadding: const EdgeInsets.symmetric(
                              vertical: 9,
                            ),
                          ),
                        )
                      : Text(
                          controller.text.isEmpty
                              ? (hint ?? '—')
                              : controller.text,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 11.5,
                            fontWeight: FontWeight.w600,
                            color: p.subtle,
                          ),
                        ),
                ),
              ],
            ),
          ),
          if (helper != null) ...[
            const SizedBox(height: 4),
            Text(helper, style: TextStyle(fontSize: 9, color: p.subtle)),
          ],
        ],
      ),
    );
  }

  Widget _readOnlyField(
    ExpertPalette p, {
    required String label,
    required String value,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label.toUpperCase(),
            style: TextStyle(
              fontSize: 9,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.4,
              color: p.muted,
            ),
          ),
          const SizedBox(height: 5),
          Container(
            height: 36,
            width: double.infinity,
            alignment: Alignment.centerLeft,
            padding: const EdgeInsets.symmetric(horizontal: 11),
            decoration: BoxDecoration(
              color: p.isDark
                  ? Colors.white.withValues(alpha: 0.02)
                  : p.surface,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: p.border),
            ),
            child: Text(
              value,
              style: TextStyle(
                fontSize: 11.5,
                fontWeight: FontWeight.w600,
                color: p.muted,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _dropdownField(
    ExpertPalette p, {
    required String label,
    required IconData icon,
    required String value,
    required List<String> items,
    Map<String, String> labels = const {},
    ValueChanged<String?>? onChanged,
    String? helper,
    bool enabled = true,
  }) {
    final cleaned = items.where((e) => e.trim().isNotEmpty).toSet().toList();
    final current = cleaned.contains(value) ? value : null;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label.toUpperCase(),
            style: TextStyle(
              fontSize: 9,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.4,
              color: p.muted,
            ),
          ),
          const SizedBox(height: 5),
          Container(
            height: 36,
            padding: const EdgeInsets.symmetric(horizontal: 10),
            decoration: BoxDecoration(
              color: enabled ? p.field : p.surface,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: enabled ? p.borderStrong : p.border),
            ),
            child: Row(
              children: [
                Icon(icon, size: 15, color: p.subtle),
                const SizedBox(width: 8),
                Expanded(
                  child: DropdownButtonHideUnderline(
                    child: DropdownButton<String>(
                      value: current,
                      isExpanded: true,
                      isDense: true,
                      dropdownColor: p.card,
                      icon: Icon(Icons.expand_more, size: 16, color: p.subtle),
                      style: TextStyle(
                        fontSize: 11.5,
                        fontWeight: FontWeight.w600,
                        color: enabled ? p.text : p.muted,
                      ),
                      hint: Text(
                        'Sélectionnez',
                        style: TextStyle(fontSize: 11, color: p.subtle),
                      ),
                      items: [
                        for (final item in cleaned)
                          DropdownMenuItem<String>(
                            value: item,
                            child: Text(
                              labels[item] ?? item,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                      ],
                      onChanged: enabled ? onChanged : null,
                    ),
                  ),
                ),
              ],
            ),
          ),
          if (helper != null) ...[
            const SizedBox(height: 4),
            Text(helper, style: TextStyle(fontSize: 9, color: p.subtle)),
          ],
        ],
      ),
    );
  }

  Widget _preferenceTile(
    ExpertPalette p, {
    required IconData icon,
    required String label,
    required Widget trailing,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: p.isDark ? Colors.white.withValues(alpha: 0.02) : p.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: p.border),
      ),
      child: Row(
        children: [
          Icon(icon, size: 16, color: p.muted),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              label,
              style: TextStyle(
                fontSize: 11.5,
                fontWeight: FontWeight.w600,
                color: p.text,
              ),
            ),
          ),
          trailing,
        ],
      ),
    );
  }

  Widget _themeSwitch(ExpertPalette p) {
    return Container(
      height: 28,
      padding: const EdgeInsets.all(2),
      decoration: BoxDecoration(
        color: p.field,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: p.borderStrong),
      ),
      child: Row(
        children: [
          _themeButton(p, true, Icons.dark_mode, 'Sombre'),
          _themeButton(p, false, Icons.light_mode, 'Clair'),
        ],
      ),
    );
  }

  Widget _themeButton(
    ExpertPalette p,
    bool dark,
    IconData icon,
    String tooltip,
  ) {
    final selected = widget.dark == dark;
    return Tooltip(
      message: tooltip,
      child: InkWell(
        onTap: () => widget.onThemeChanged(dark),
        borderRadius: BorderRadius.circular(999),
        child: Container(
          width: 34,
          height: 24,
          decoration: BoxDecoration(
            color: selected ? p.blueDeep : Colors.transparent,
            borderRadius: BorderRadius.circular(999),
          ),
          child: Icon(
            icon,
            size: 14,
            color: selected ? Colors.white : p.subtle,
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/auth/auth_controller.dart';
import 'widgets/expert_editor_tab.dart';
import 'widgets/expert_history_tab.dart';
import 'widgets/expert_messaging.dart';
import 'widgets/expert_other_tabs.dart';
import 'widgets/expert_profile_tab.dart';
import 'widgets/expert_theme.dart';

class ExpertScreen extends ConsumerStatefulWidget {
  const ExpertScreen({super.key, this.initialTab = 0});

  final int initialTab;

  @override
  ConsumerState<ExpertScreen> createState() => _ExpertScreenState();
}

class _ExpertScreenState extends ConsumerState<ExpertScreen> {
  int _tab = 0;
  bool _dark = true;
  List<Map<String, dynamic>> _documents = [];
  Map<String, dynamic>? _doc;
  Map<String, dynamic> _activity = const {};
  bool _loadingDoc = false;
  String _search = '';
  final _searchController = TextEditingController();
  final Map<String, ExpertDraft> _drafts = {};
  int _documentRequest = 0;
  int? _pendingCount;

  static const _tabs = <(IconData, String)>[
    (Icons.description_outlined, 'Éditeur de Normes'),
    (Icons.history, 'Historique'),
    (Icons.groups_outlined, 'Experts & Groupes'),
    (Icons.how_to_vote_outlined, 'Réunions & Votes'),
    (Icons.account_balance_outlined, 'Cotisations & Indemnités'),
    (Icons.verified_outlined, 'Processus ISO'),
    (Icons.gavel_outlined, 'Bureau Légistique'),
  ];

  @override
  void initState() {
    super.initState();
    _tab = widget.initialTab;
    _loadDocuments();
    _loadActivity();
    _loadPending();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadDocuments() async {
    try {
      final resp = await ApiClient.dio.get('/api/v1/sidebar/documents/');
      final data = resp.data as Map<String, dynamic>;
      final results = (data['results'] as List? ?? [])
          .map((e) => e as Map<String, dynamic>)
          .toList();
      if (!mounted) return;
      setState(() => _documents = results);
      if (results.isNotEmpty) _selectDocument(results.first);
    } catch (_) {
      if (mounted) setState(() => _documents = []);
    }
  }

  Future<void> _loadActivity() async {
    try {
      final resp = await ApiClient.dio.get('/api/v1/activity/my-counter/');
      if (!mounted) return;
      setState(() => _activity = resp.data as Map<String, dynamic>);
    } catch (_) {}
  }

  Future<void> _loadPending() async {
    try {
      final response = await ApiClient.dio.get(
        '/api/v1/experts/pending-count-for-my-ctm/',
      );
      if (mounted) {
        setState(
          () => _pendingCount = (response.data['count'] as num? ?? 0).toInt(),
        );
      }
    } catch (_) {
      if (mounted) setState(() => _pendingCount = null);
    }
  }

  void _openNorm(Map<String, dynamic> norm) {
    _selectDocument(norm);
    setState(() => _tab = 0);
  }

  Future<void> _selectDocument(Map<String, dynamic> doc) async {
    if (doc['id'] == null) return;
    final request = ++_documentRequest;
    setState(() => _loadingDoc = true);
    try {
      final resp = await ApiClient.dio.get('/api/v1/norms/${doc['id']}/');
      if (!mounted || request != _documentRequest) return;
      setState(() => _doc = resp.data as Map<String, dynamic>);
    } catch (_) {
      if (!mounted || request != _documentRequest) return;
      _showInfo(
        context,
        'Impossible de charger le document. Votre saisie actuelle est conservée.',
      );
    } finally {
      if (mounted && request == _documentRequest) {
        setState(() => _loadingDoc = false);
      }
    }
  }

  List<Map<String, dynamic>> get _filteredDocuments {
    if (_search.trim().isEmpty) return _documents;
    final q = _search.toLowerCase();
    return _documents.where((d) {
      final title = (d['title'] as String? ?? '').toLowerCase();
      final code = (d['code'] as String? ?? '').toLowerCase();
      return title.contains(q) || code.contains(q);
    }).toList();
  }

  Widget _content(ExpertPalette p, String userName, String userEmail) {
    switch (_tab) {
      case 1:
        return ExpertHistoryTab(
          key: ValueKey('history-${_doc?['id']}'),
          docId: _doc?['id']?.toString(),
          docTitle: _doc?['title'] as String?,
        );
      case 2:
        return ExpertExpertsTab(onAdhesions: () => setState(() => _tab = 9));
      case 3:
        return const ExpertMeetingsTab();
      case 4:
        return const ExpertFinancialTab();
      case 5:
        return ExpertValidationTab(onOpenNorm: _openNorm);
      case 6:
        return const ExpertLegistiqueTab();
      case 7:
        return ExpertNotificationsTab(onOpenNorm: _openNorm);
      case 9:
        return ExpertAdhesionsTab(onChanged: _loadPending);
      case 8:
        return ExpertProfileTab(
          dark: _dark,
          fallbackName: userName,
          fallbackEmail: userEmail,
          onThemeChanged: (value) => setState(() => _dark = value),
          onAffiliationSaved: () {
            setState(() {
              _doc = null;
              _documents = [];
            });
            _loadDocuments();
            _loadActivity();
            _loadPending();
          },
        );
      default:
        return ExpertEditorTab(
          doc: _doc,
          drafts: _drafts,
          userName: userName,
          userScope: userEmail,
          loading: _loadingDoc,
          onSave: () {
            if (_doc != null) _selectDocument(_doc!);
          },
          onOpenProfile: () => setState(() => _tab = 8),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final palette = _dark ? ExpertPalette.dark : ExpertPalette.light;
    final session = ref.watch(authControllerProvider).session;
    final userName = session?.fullName ?? 'Expert';
    final userEmail = session?.email ?? '';

    return ExpertTheme(
      palette: palette,
      child: Scaffold(
        backgroundColor: palette.bg,
        drawer: Drawer(
          child: _ExpertSidebar(
            width: 280,
            tab: _tab,
            documents: _filteredDocuments,
            selectedId: _doc?['id']?.toString(),
            searchController: _searchController,
            onSearch: (value) => setState(() => _search = value),
            onSelect: (doc) {
              Navigator.of(context).pop();
              _selectDocument(doc);
              setState(() => _tab = 0);
            },
            onProfile: () {
              Navigator.of(context).pop();
              setState(() => _tab = 8);
            },
            onCreate: () => _showInfo(
              context,
              'La création de norme se fait depuis le portail web.',
            ),
            userName: userName,
            activity: _activity,
          ),
        ),
        body: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) {
              final mobile = constraints.maxWidth < 700;
              final sidebarWidth = constraints.maxWidth < 900 ? 268.0 : 320.0;
              return Stack(
                children: [
                  Row(
                    children: [
                      if (!mobile)
                        _ExpertSidebar(
                          width: sidebarWidth,
                          tab: _tab,
                          documents: _filteredDocuments,
                          selectedId: _doc?['id']?.toString(),
                          searchController: _searchController,
                          onSearch: (value) => setState(() => _search = value),
                          onSelect: (doc) {
                            _selectDocument(doc);
                            if (_tab != 1) setState(() => _tab = 0);
                          },
                          onProfile: () => setState(() => _tab = 8),
                          onCreate: () => _showInfo(
                            context,
                            'La création de norme se fait depuis le portail web.',
                          ),
                          userName: userName,
                          activity: _activity,
                        ),
                      Expanded(
                        child: Column(
                          children: [
                            _ExpertTopbar(
                              pendingCount: _pendingCount,
                              mobile: mobile,
                              tab: _tab,
                              dark: _dark,
                              onTab: (i) => setState(() => _tab = i),
                              onTheme: () => setState(() => _dark = !_dark),
                              onNotifications: () => setState(() => _tab = 7),
                              onLogout: () => ref
                                  .read(authControllerProvider.notifier)
                                  .logout(),
                            ),
                            Expanded(
                              child: DecoratedBox(
                                decoration: BoxDecoration(
                                  gradient: LinearGradient(
                                    begin: Alignment.topLeft,
                                    end: Alignment.bottomRight,
                                    colors: palette.backgroundGradient,
                                  ),
                                ),
                                child: _content(palette, userName, userEmail),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  Positioned(
                    right: 24,
                    bottom: 20,
                    child: _MessagingButton(palette: palette),
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  void _showInfo(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
    );
  }
}

class _ExpertTopbar extends StatelessWidget {
  const _ExpertTopbar({
    required this.tab,
    required this.dark,
    required this.onTab,
    required this.onTheme,
    required this.onNotifications,
    required this.onLogout,
    this.mobile = false,
    this.pendingCount,
  });

  final int tab;
  final bool dark;
  final ValueChanged<int> onTab;
  final VoidCallback onTheme;
  final VoidCallback onNotifications;
  final VoidCallback onLogout;
  final bool mobile;
  final int? pendingCount;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return Container(
      height: 72,
      decoration: BoxDecoration(
        color: p.nav,
        border: Border(bottom: BorderSide(color: p.border)),
      ),
      child: Row(
        children: [
          if (mobile)
            Builder(
              builder: (context) => IconButton(
                onPressed: () => Scaffold.of(context).openDrawer(),
                tooltip: 'Documents',
                icon: Icon(Icons.menu, color: p.text),
              ),
            ),
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: [
                  for (int i = 0; i < _ExpertScreenState._tabs.length; i++)
                    _NavTab(
                      icon: _ExpertScreenState._tabs[i].$1,
                      label: _ExpertScreenState._tabs[i].$2,
                      active: tab == i,
                      onTap: () => onTab(i),
                    ),
                  _NavTab(
                    icon: Icons.person_add_alt,
                    label: pendingCount == null
                        ? 'Adhésions'
                        : 'Adhésions ($pendingCount)',
                    active: tab == 9,
                    onTap: () => onTab(9),
                  ),
                ],
              ),
            ),
          ),
          IconButton(
            tooltip: 'Adhésions des membres',
            onPressed: () => onTab(9),
            icon: Badge(
              isLabelVisible: (pendingCount ?? 0) > 0,
              label: Text('$pendingCount'),
              child: Icon(
                Icons.person_add_alt,
                color: tab == 9 ? p.blue : p.muted,
              ),
            ),
          ),
          if (!mobile)
            _TopbarAction(
              icon: dark ? Icons.dark_mode_outlined : Icons.light_mode_outlined,
              label: 'Thème',
              onTap: onTheme,
            ),
          if (!mobile)
            _TopbarAction(
              icon: Icons.notifications_none,
              label: 'Notifications',
              active: tab == 7,
              onTap: onNotifications,
            ),
          if (mobile)
            PopupMenuButton<String>(
              tooltip: 'Actions',
              onSelected: (value) =>
                  value == 'theme' ? onTheme() : onNotifications(),
              itemBuilder: (_) => const [
                PopupMenuItem(value: 'theme', child: Text('Thème')),
                PopupMenuItem(
                  value: 'notifications',
                  child: Text('Notifications'),
                ),
              ],
            ),
          const SizedBox(width: 6),
          IconButton(
            onPressed: onLogout,
            tooltip: 'Se déconnecter',
            icon: Icon(Icons.logout, size: 18, color: p.subtle),
          ),
          const SizedBox(width: 4),
        ],
      ),
    );
  }
}

class _NavTab extends StatelessWidget {
  const _NavTab({
    required this.icon,
    required this.label,
    required this.active,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 2),
      child: Material(
        color: active ? p.blueSoft : Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(8),
          child: Container(
            height: 40,
            padding: const EdgeInsets.symmetric(horizontal: 13),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: active
                    ? p.blue.withValues(alpha: 0.28)
                    : Colors.transparent,
              ),
            ),
            child: Row(
              children: [
                Icon(icon, size: 16, color: active ? p.blue : p.subtle),
                const SizedBox(width: 7),
                Text(
                  label.toUpperCase(),
                  style: TextStyle(
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.35,
                    color: active ? p.blue : p.muted,
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

class _TopbarAction extends StatelessWidget {
  const _TopbarAction({
    required this.icon,
    required this.label,
    required this.onTap,
    this.active = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final bool active;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return Tooltip(
      message: label,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          child: Row(
            children: [
              Icon(icon, size: 18, color: active ? p.blue : p.muted),
              const SizedBox(width: 6),
              Text(
                label.toUpperCase(),
                style: TextStyle(
                  fontSize: 9.5,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.4,
                  color: active ? p.blue : p.muted,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ExpertSidebar extends StatelessWidget {
  const _ExpertSidebar({
    required this.width,
    required this.tab,
    required this.documents,
    required this.selectedId,
    required this.searchController,
    required this.onSearch,
    required this.onSelect,
    required this.onProfile,
    required this.onCreate,
    required this.userName,
    required this.activity,
  });

  final double width;
  final int tab;
  final List<Map<String, dynamic>> documents;
  final String? selectedId;
  final TextEditingController searchController;
  final ValueChanged<String> onSearch;
  final ValueChanged<Map<String, dynamic>> onSelect;
  final VoidCallback onProfile;
  final VoidCallback onCreate;
  final String userName;
  final Map<String, dynamic> activity;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    final collaborators = _collaborators();
    return Container(
      width: width,
      decoration: BoxDecoration(
        color: p.sidebar,
        border: Border(right: BorderSide(color: p.border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _SidebarBrand(palette: p),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(12, 16, 12, 16),
              children: [
                Row(
                  children: [
                    Icon(Icons.folder_outlined, size: 16, color: p.subtle),
                    const SizedBox(width: 7),
                    Expanded(
                      child: Text(
                        'DOCUMENTS',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1.1,
                          color: p.muted,
                        ),
                      ),
                    ),
                    _MiniButton(
                      label: '+ Nouveau',
                      palette: p,
                      onTap: onCreate,
                    ),
                  ],
                ),
                ...[
                  const SizedBox(height: 12),
                  _SidebarSearch(
                    controller: searchController,
                    palette: p,
                    onChanged: onSearch,
                  ),
                ],
                const SizedBox(height: 12),
                for (final doc in documents)
                  _DocItem(
                    doc: doc,
                    active: selectedId == doc['id']?.toString(),
                    palette: p,
                    onTap: () => onSelect(doc),
                  ),
                if (documents.isEmpty)
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(
                      'Aucun document',
                      style: TextStyle(fontSize: 12, color: p.subtle),
                    ),
                  ),
                const SizedBox(height: 24),
                Row(
                  children: [
                    Icon(Icons.people_outline, size: 16, color: p.subtle),
                    const SizedBox(width: 7),
                    Text(
                      'COLLABORATEURS',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.1,
                        color: p.muted,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                for (final collaborator in collaborators)
                  _Collaborator(
                    name: collaborator.$1,
                    role: collaborator.$2,
                    palette: p,
                  ),
              ],
            ),
          ),
          _SidebarFooter(palette: p, activity: activity, onProfile: onProfile),
        ],
      ),
    );
  }

  List<(String, String)> _collaborators() {
    final names = <String>[];
    for (final doc in documents) {
      final name = doc['updatedBy'] as String?;
      if (name != null && name.trim().isNotEmpty && !names.contains(name)) {
        names.add(name);
      }
    }
    if (names.isEmpty) names.add('Eddy Masamba  mpaka-yoka');
    return [
      (userName, 'Membre CTM / Membre WG'),
      for (final name in names.take(2))
        if (name != userName) (name, 'Membre CTM / Membre WG'),
    ];
  }
}

class _SidebarBrand extends StatelessWidget {
  const _SidebarBrand({required this.palette});

  final ExpertPalette palette;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 72,
      padding: const EdgeInsets.symmetric(horizontal: 14),
      decoration: BoxDecoration(
        color: palette.sidebarHeader,
        border: Border(bottom: BorderSide(color: palette.border)),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: const Color(0xFFD4AF37)),
              color: Colors.white,
            ),
            clipBehavior: Clip.antiAlias,
            child: Image.asset('assets/img/logo-cnetp.png', fit: BoxFit.cover),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 4,
            height: 32,
            child: Column(
              children: const [
                Expanded(child: ColoredBox(color: Color(0xFF0095C9))),
                SizedBox(
                  height: 8,
                  child: ColoredBox(color: Color(0xFFFFF24B)),
                ),
                Expanded(child: ColoredBox(color: Color(0xFFDB3832))),
              ],
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'CNE-ITP',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1,
                    color: palette.muted,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  'ESPACE DE TRAVAIL',
                  style: TextStyle(
                    fontSize: 13.5,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 0.3,
                    color: palette.blue,
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

class _SidebarSearch extends StatelessWidget {
  const _SidebarSearch({
    required this.controller,
    required this.palette,
    required this.onChanged,
  });

  final TextEditingController controller;
  final ExpertPalette palette;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      onChanged: onChanged,
      style: TextStyle(fontSize: 11, color: palette.text),
      decoration: InputDecoration(
        isDense: true,
        hintText: 'Rechercher...',
        hintStyle: TextStyle(fontSize: 11, color: palette.subtle),
        prefixIcon: Icon(Icons.search, size: 15, color: palette.subtle),
        prefixIconConstraints: const BoxConstraints(minWidth: 34),
        filled: true,
        fillColor: palette.field,
        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: palette.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: palette.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: palette.blue.withValues(alpha: 0.5)),
        ),
      ),
    );
  }
}

class _DocItem extends StatelessWidget {
  const _DocItem({
    required this.doc,
    required this.active,
    required this.palette,
    required this.onTap,
  });

  final Map<String, dynamic> doc;
  final bool active;
  final ExpertPalette palette;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    final code = doc['code'] as String? ?? '';
    final updatedBy = doc['updatedBy'] as String? ?? '';
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Material(
        color: active
            ? (p.isDark ? const Color(0xFF0B1627) : const Color(0xFFEFF6FF))
            : Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(8),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: active
                    ? p.blue.withValues(alpha: p.isDark ? 0.35 : 0.25)
                    : Colors.transparent,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  doc['title'] as String? ?? 'Document',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: active ? p.title : p.text,
                  ),
                ),
                const SizedBox(height: 5),
                Row(
                  children: [
                    Text(
                      code,
                      style: TextStyle(
                        fontSize: 9.5,
                        fontFamily: 'monospace',
                        color: active ? p.blue : p.subtle,
                      ),
                    ),
                    const Spacer(),
                    Flexible(
                      child: Text(
                        updatedBy,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        textAlign: TextAlign.right,
                        style: TextStyle(fontSize: 9.5, color: p.subtle),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Collaborator extends StatelessWidget {
  const _Collaborator({
    required this.name,
    required this.role,
    required this.palette,
  });

  final String name;
  final String role;
  final ExpertPalette palette;

  String get _initials {
    final parts = name.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty);
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts.first.substring(0, 1).toUpperCase();
    return '${parts.elementAt(0)[0]}${parts.elementAt(1)[0]}'.toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    final p = palette;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: const BoxDecoration(
              color: Color(0xFF2563EB),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                _initials,
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: Colors.white,
                ),
              ),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: p.text,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  role,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 9.5, color: p.subtle),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SidebarFooter extends StatelessWidget {
  const _SidebarFooter({
    required this.palette,
    required this.activity,
    required this.onProfile,
  });

  final ExpertPalette palette;
  final Map<String, dynamic> activity;
  final VoidCallback onProfile;

  int _int(String key) {
    final value = activity[key];
    if (value is int) return value;
    if (value is num) return value.toInt();
    return int.tryParse('$value') ?? 0;
  }

  String _duration(int seconds) {
    if (seconds <= 0) return '0 min';
    final hours = seconds ~/ 3600;
    final minutes = (seconds % 3600) ~/ 60;
    if (hours > 0) {
      return '${hours}h ${minutes.toString().padLeft(2, '0')}min';
    }
    return '$minutes min';
  }

  @override
  Widget build(BuildContext context) {
    final p = palette;
    final totalSeconds = _int('active_seconds_total');
    final totalEditions = _int('editions_total');
    final todaySeconds = _int('active_seconds_today');
    final todayEditions = _int('editions_today');

    return Container(
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      decoration: BoxDecoration(
        border: Border(top: BorderSide(color: p.border)),
        color: p.isDark ? const Color(0xFF030307) : p.surface,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                'ISO COMPLIANCE MODE',
                style: TextStyle(
                  fontSize: 8.5,
                  fontFamily: 'monospace',
                  color: p.subtle,
                ),
              ),
              const Spacer(),
              Container(
                width: 6,
                height: 6,
                decoration: BoxDecoration(
                  color: p.blue,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: p.blue.withValues(alpha: 0.7),
                      blurRadius: 6,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 4),
              Text('SYNC', style: TextStyle(fontSize: 9, color: p.muted)),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Text(
                'POSTE ACTIF :',
                style: TextStyle(fontSize: 9, color: p.subtle),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                decoration: BoxDecoration(
                  color: p.amberSoft,
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: p.amber.withValues(alpha: 0.3)),
                ),
                child: Text(
                  'RAPPORTEUR CTM',
                  style: TextStyle(
                    fontSize: 8,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.3,
                    color: p.amber,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Icon(Icons.show_chart, size: 12, color: p.subtle),
              const SizedBox(width: 5),
              Text(
                'MON ACTIVITÉ',
                style: TextStyle(fontSize: 9, color: p.muted),
              ),
              const Spacer(),
              Text('Sync', style: TextStyle(fontSize: 8, color: p.subtle)),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              Expanded(
                child: _ActivityTile(
                  label: 'TEMPS',
                  value: _duration(totalSeconds),
                  palette: p,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _ActivityTile(
                  label: 'ÉDITIONS',
                  value: '$totalEditions',
                  palette: p,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Center(
            child: Text(
              "Aujourd'hui : ${_duration(todaySeconds)} • $todayEditions édition(s)",
              style: TextStyle(fontSize: 8, color: p.subtle),
            ),
          ),
          const SizedBox(height: 8),
          Material(
            color: p.amberSoft,
            borderRadius: BorderRadius.circular(8),
            child: InkWell(
              onTap: onProfile,
              borderRadius: BorderRadius.circular(8),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: p.amber.withValues(alpha: 0.3)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.settings_outlined, size: 12, color: p.amber),
                    const SizedBox(width: 5),
                    Flexible(
                      child: Text(
                        'CONFIGURER TOTAL DU PROFIL',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 0.3,
                          color: p.amber,
                        ),
                      ),
                    ),
                    const SizedBox(width: 4),
                    Text('→', style: TextStyle(fontSize: 10, color: p.amber)),
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

class _ActivityTile extends StatelessWidget {
  const _ActivityTile({
    required this.label,
    required this.value,
    required this.palette,
  });

  final String label;
  final String value;
  final ExpertPalette palette;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      decoration: BoxDecoration(
        color: p.isDark ? p.surface : p.field,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: p.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(fontSize: 8, letterSpacing: 0.3, color: p.subtle),
          ),
          const SizedBox(height: 2),
          Text(
            value,
            style: TextStyle(
              fontSize: 11.5,
              fontWeight: FontWeight.w800,
              color: p.isDark ? p.title : p.text,
            ),
          ),
        ],
      ),
    );
  }
}

class _MiniButton extends StatelessWidget {
  const _MiniButton({
    required this.label,
    required this.palette,
    required this.onTap,
  });

  final String label;
  final ExpertPalette palette;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    return Material(
      color: p.blueSoft,
      borderRadius: BorderRadius.circular(6),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(6),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: p.blue.withValues(alpha: 0.3)),
          ),
          child: Text(
            label,
            style: TextStyle(
              fontSize: 9.5,
              fontWeight: FontWeight.w700,
              color: p.blue,
            ),
          ),
        ),
      ),
    );
  }
}

class _MessagingButton extends StatelessWidget {
  const _MessagingButton({required this.palette});

  final ExpertPalette palette;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    return Material(
      color: p.card,
      elevation: 8,
      shadowColor: Colors.black.withValues(alpha: 0.35),
      borderRadius: BorderRadius.circular(999),
      child: InkWell(
        onTap: () => openExpertMessaging(context),
        borderRadius: BorderRadius.circular(999),
        child: Container(
          height: 42,
          padding: const EdgeInsets.symmetric(horizontal: 18),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: p.border),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.chat_bubble_outline, size: 20, color: p.blue),
              const SizedBox(width: 10),
              Text(
                'MESSAGERIE CNE-ITP',
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.3,
                  color: p.title,
                ),
              ),
              const SizedBox(width: 12),
              Container(
                width: 7,
                height: 7,
                decoration: BoxDecoration(
                  color: p.blue,
                  shape: BoxShape.circle,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

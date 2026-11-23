import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/api/api_client.dart';
import '../../core/auth/auth_controller.dart';
import 'widgets/expert_editor_tab.dart';
import 'widgets/expert_history_tab.dart';
import 'widgets/expert_messaging.dart';
import 'widgets/expert_other_tabs.dart';
import 'widgets/expert_profile_tab.dart';
import 'widgets/expert_theme.dart';
import 'widgets/expert_module.dart';

class ExpertScreen extends ConsumerStatefulWidget {
  const ExpertScreen({super.key, this.initialTab = 0});

  final int initialTab;

  @override
  ConsumerState<ExpertScreen> createState() => _ExpertScreenState();
}

class _ExpertScreenState extends ConsumerState<ExpertScreen>
    with WidgetsBindingObserver {
  Timer? _activityTimer;
  DateTime _lastInteraction = DateTime.now();
  final String _deviceId = 'flutter-${DateTime.now().microsecondsSinceEpoch}';
  bool _visible = true;
  bool _sidebarCollapsed = false;

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _visible = state == AppLifecycleState.resumed;
    if (_visible) unawaited(_refreshUnreadCounts());
  }

  Future<void> _heartbeat() async {
    try {
      await ApiClient.dio.post(
        '/api/v1/mobile/expert/activity/heartbeat/',
        data: {
          'device_id': _deviceId,
          'visible':
              _visible &&
              DateTime.now().difference(_lastInteraction).inSeconds < 120,
          'interacted':
              DateTime.now().difference(_lastInteraction).inSeconds < 30,
          if (_doc != null) 'norme_id': _doc!['id'],
        },
      );
      await _loadActivity();
    } catch (_) {
      /* La saisie reste possible si le compteur est indisponible. */
    }
  }

  static const _themeKey = 'expert.theme.dark';
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
  int? _unreadCount;
  int? _unreadMessagesCount;
  String? _meetingToOpen;
  String? _documentsError;

  Future<void> _createNorm() async {
    final palette = _dark ? ExpertPalette.dark : ExpertPalette.light;
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => ExpertPageTheme(
          palette: palette,
          child: Scaffold(
            backgroundColor: palette.bg,
            appBar: AppBar(title: const Text('Nouveau projet de norme')),
            body: ExpertModule(
              title: 'Créer un projet',
              endpoints: const {
                'Affiliation': '/api/v1/experts/my-affiliation/',
              },
              builder: (s) {
                final affiliation = s.map('Affiliation');
                final ctms = expertRows(affiliation['ctms']);
                final groups = expertRows(affiliation['workgroups']);

                Future<void> openForm({
                  String title = '',
                  String content = '',
                  String comment = '',
                }) => expertForm(
                  s,
                  'Nouveau projet de norme',
                  [
                    ExpertField('title', 'Titre', initial: title),
                    const ExpertField('description', 'Description', lines: 4),
                    ExpertField(
                      'ctm',
                      'Sous-commission',
                      choices: {
                        for (final c in ctms) '${c['id']}': '${c['name']}',
                      },
                    ),
                    ExpertField(
                      'wg',
                      'Groupe de travail',
                      choices: {
                        for (final g in groups) '${g['id']}': '${g['name']}',
                      },
                    ),
                    if (content.isNotEmpty)
                      ExpertField(
                        'content',
                        'Contenu extrait',
                        initial: content,
                        lines: 12,
                      ),
                  ],
                  (values) async {
                    if (!groups.any(
                      (g) =>
                          '${g['id']}' == values['wg'] &&
                          '${g['ctm_id']}' == values['ctm'],
                    )) {
                      s.notify(
                        'Le groupe doit appartenir à la sous-commission choisie.',
                      );
                      return false;
                    }
                    try {
                      final created = await ApiClient.dio.post(
                        '/api/v1/norms/',
                        data: {
                          'title': values['title'],
                          'description': values['description'],
                          'ctm': int.parse(values['ctm']!),
                          'wg': int.parse(values['wg']!),
                        },
                      );
                      final id = (created.data as Map)['id'];
                      if (content.isNotEmpty) {
                        await ApiClient.dio.post(
                          '/api/v1/norms/$id/create_version/',
                          data: {
                            'title': values['title'],
                            'content': content,
                            'comment': comment,
                          },
                        );
                      }
                      if (mounted) _loadDocuments();
                      return true;
                    } catch (error) {
                      s.notify(expertError(error));
                      return false;
                    }
                  },
                );

                Future<void> importDocument() async {
                  final file = await openFile(
                    acceptedTypeGroups: const [
                      XTypeGroup(
                        label: 'Document',
                        extensions: ['pdf', 'doc', 'docx', 'txt', 'md'],
                      ),
                    ],
                  );
                  if (file == null) return;
                  try {
                    final response = await ApiClient.dio.post(
                      '/api/v1/norms/extract_document/',
                      data: FormData.fromMap({
                        'document': MultipartFile.fromBytes(
                          await file.readAsBytes(),
                          filename: file.name,
                        ),
                      }),
                    );
                    final content = '${(response.data as Map)['content'] ?? ''}'
                        .trim();
                    if (content.isEmpty) {
                      s.notify('Aucun texte exploitable dans ce document.');
                      return;
                    }
                    await openForm(
                      title: file.name.replaceFirst(RegExp(r'\.[^.]+$'), ''),
                      content: content,
                      comment: 'Import initial : ${file.name}',
                    );
                  } catch (error) {
                    s.notify(expertError(error));
                  }
                }

                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    s.button(
                      'Renseigner le projet',
                      () => openForm(),
                      icon: Icons.edit_note_outlined,
                    ),
                    const SizedBox(height: 8),
                    s.button(
                      'Importer un PDF / DOCX',
                      importDocument,
                      icon: Icons.upload_file_outlined,
                    ),
                  ],
                );
              },
            ),
          ),
        ),
      ),
    );
  }

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
    _loadTheme();
    _loadDocuments();
    _loadActivity();
    _loadPending();
    unawaited(_refreshUnreadCounts());
    WidgetsBinding.instance.addObserver(this);
    _activityTimer = Timer.periodic(const Duration(seconds: 60), (_) {
      _heartbeat();
      if (_visible) unawaited(_refreshUnreadCounts());
    });
    _heartbeat();
  }

  @override
  void didUpdateWidget(covariant ExpertScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.initialTab != oldWidget.initialTab) {
      _tab = widget.initialTab.clamp(0, 9);
    }
  }

  @override
  void dispose() {
    _activityTimer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadDocuments() async {
    try {
      final resp = await ApiClient.dio.get(
        '/api/v1/sidebar/documents/',
        queryParameters: {'page_size': 100},
      );
      final data = resp.data as Map<String, dynamic>;
      final results = (data['results'] as List? ?? [])
          .map((e) => e as Map<String, dynamic>)
          .toList();
      if (!mounted) return;
      setState(() {
        _documents = results;
        _documentsError = null;
      });
      if (results.isNotEmpty) _selectDocument(results.first);
    } catch (_) {
      if (mounted) {
        setState(
          () => _documentsError = 'Impossible de charger vos documents.',
        );
      }
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

  Future<void> _loadTheme() async {
    final preferences = await SharedPreferences.getInstance();
    final saved = preferences.getBool(_themeKey);
    if (saved != null && mounted) setState(() => _dark = saved);
  }

  Future<void> _setTheme(bool value) async {
    setState(() => _dark = value);
    final preferences = await SharedPreferences.getInstance();
    await preferences.setBool(_themeKey, value);
  }

  Future<void> _loadUnread() async {
    try {
      final response = await ApiClient.dio.get(
        '/api/v1/mobile/notifications/unread_count/',
      );
      if (!mounted) return;
      final raw = response.data;
      final count = raw is Map ? raw['unread_count'] : raw;
      setState(
        () => _unreadCount = count is num
            ? count.toInt()
            : int.tryParse('${count ?? ''}'),
      );
    } catch (_) {
      if (mounted) setState(() => _unreadCount = null);
    }
  }

  Future<void> _loadUnreadMessages() async {
    try {
      final response = await ApiClient.dio.get(
        '/api/v1/messages/unread_count/',
      );
      if (!mounted) return;
      final raw = response.data;
      final count = raw is Map ? raw['unread_count'] : raw;
      setState(
        () => _unreadMessagesCount = count is num
            ? count.toInt()
            : int.tryParse('${count ?? ''}'),
      );
    } catch (_) {
      if (mounted) setState(() => _unreadMessagesCount = null);
    }
  }

  Future<void> _refreshUnreadCounts() async {
    await Future.wait([_loadUnread(), _loadUnreadMessages()]);
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
        return ExpertMeetingsTab(
          key: ValueKey(_meetingToOpen),
          meetingId: _meetingToOpen,
        );
      case 4:
        return const ExpertFinancialTab();
      case 5:
        return ExpertValidationTab(onOpenNorm: _openNorm);
      case 6:
        return const ExpertLegistiqueTab();
      case 7:
        return ExpertNotificationsTab(
          onOpenNorm: _openNorm,
          onOpenMeeting: (id) => setState(() {
            _meetingToOpen = id;
            _tab = 3;
          }),
          onChanged: _loadUnread,
        );
      case 9:
        return ExpertAdhesionsTab(onChanged: _loadPending);
      case 8:
        return ExpertProfileTab(
          dark: _dark,
          fallbackName: userName,
          fallbackEmail: userEmail,
          onThemeChanged: _setTheme,
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
      child: Theme(
        data: expertMaterialTheme(context, palette),
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
              onCreate: _createNorm,
              showNavigation: false,
              userName: userName,
              activity: _activity,
            ),
          ),
          body: Listener(
            onPointerDown: (_) => _lastInteraction = DateTime.now(),
            onPointerSignal: (_) => _lastInteraction = DateTime.now(),
            child: SafeArea(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final mobile = constraints.maxWidth < 700;
                  final sidebarWidth = _sidebarCollapsed ? 68.0 : 280.0;
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
                              onSearch: (value) =>
                                  setState(() => _search = value),
                              onSelect: (doc) {
                                _selectDocument(doc);
                                if (_tab != 1) setState(() => _tab = 0);
                              },
                              onProfile: () => setState(() => _tab = 8),
                              onCreate: _createNorm,
                              showNavigation: true,
                              collapsed: _sidebarCollapsed,
                              onToggle: () => setState(
                                () => _sidebarCollapsed = !_sidebarCollapsed,
                              ),
                              onTab: (value) => setState(() => _tab = value),
                              userName: userName,
                              activity: _activity,
                            ),
                          Expanded(
                            child: Column(
                              children: [
                                if (_documentsError != null)
                                  MaterialBanner(
                                    content: Text(_documentsError!),
                                    actions: [
                                      TextButton(
                                        onPressed: _loadDocuments,
                                        child: const Text('Réessayer'),
                                      ),
                                    ],
                                  ),
                                _ExpertTopbar(
                                  pendingCount: _pendingCount,
                                  unreadCount: _unreadCount,
                                  mobile: mobile,
                                  tab: _tab,
                                  dark: _dark,
                                  onTab: (i) {
                                    setState(() => _tab = i);
                                    if (i == 7) _loadUnread();
                                  },
                                  onTheme: () => _setTheme(!_dark),
                                  onNotifications: () {
                                    setState(() => _tab = 7);
                                    _loadUnread();
                                  },
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
                                    child: _content(
                                      palette,
                                      userName,
                                      userEmail,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      Positioned(
                        right: 16,
                        bottom: 16,
                        child: _MessagingButton(
                          palette: palette,
                          unreadCount: _unreadMessagesCount,
                          onPressed: () async {
                            await openExpertCommunication(context, norm: _doc);
                            await _refreshUnreadCounts();
                          },
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
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
    this.unreadCount,
  });

  final int tab;
  final bool dark;
  final ValueChanged<int> onTab;
  final VoidCallback onTheme;
  final VoidCallback onNotifications;
  final VoidCallback onLogout;
  final bool mobile;
  final int? pendingCount;
  final int? unreadCount;

  static const _compactLabels = [
    'Éditeur',
    'Historique',
    'Experts',
    'Réunions',
    'Cotisations',
    'ISO',
    'Légistique',
    'Notifications',
    'Profil',
    'Adhésions',
  ];

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    final compactNavigation = mobile;
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
            child: compactNavigation
                ? Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<int>(
                        isExpanded: true,
                        value: tab.clamp(0, 9),
                        dropdownColor: p.nav,
                        style: TextStyle(color: p.text, fontSize: 14),
                        items: [
                          for (
                            var i = 0;
                            i < _ExpertScreenState._tabs.length;
                            i++
                          )
                            DropdownMenuItem(
                              value: i,
                              child: Text(
                                mobile && i == 0
                                    ? 'Consultation des normes'
                                    : _ExpertScreenState._tabs[i].$2,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          const DropdownMenuItem(
                            value: 7,
                            child: Text('Notifications'),
                          ),
                          const DropdownMenuItem(
                            value: 8,
                            child: Text('Mon profil'),
                          ),
                          const DropdownMenuItem(
                            value: 9,
                            child: Text('Adhésions'),
                          ),
                        ],
                        selectedItemBuilder: (context) => [
                          for (var i = 0; i < 10; i++)
                            Align(
                              alignment: Alignment.centerLeft,
                              child: Text(
                                mobile && i == 0 ? 'Normes' : _compactLabels[i],
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                        ],
                        onChanged: (value) {
                          if (value != null) onTab(value);
                        },
                      ),
                    ),
                  )
                : Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'ESPACE EXPERT',
                          style: TextStyle(
                            color: p.subtle,
                            fontSize: 10,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1.2,
                          ),
                        ),
                        const SizedBox(height: 3),
                        Text(
                          tab < _ExpertScreenState._tabs.length
                              ? _ExpertScreenState._tabs[tab].$2
                              : _compactLabels[tab.clamp(0, 9)],
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: p.title,
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
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
              badgeCount: unreadCount,
              onTap: onNotifications,
            ),
          if (mobile)
            IconButton(
              tooltip: 'Notifications',
              onPressed: onNotifications,
              icon: Badge(
                isLabelVisible: (unreadCount ?? 0) > 0,
                label: Text('$unreadCount'),
                child: Icon(
                  Icons.notifications_none,
                  color: tab == 7 ? p.blue : p.muted,
                ),
              ),
            ),
          if (mobile)
            PopupMenuButton<String>(
              tooltip: 'Actions',
              onSelected: (value) =>
                  value == 'theme' ? onTheme() : onNotifications(),
              itemBuilder: (_) => [
                const PopupMenuItem(value: 'theme', child: Text('Thème')),
                PopupMenuItem(
                  value: 'notifications',
                  child: Text(
                    (unreadCount ?? 0) > 0
                        ? 'Notifications ($unreadCount)'
                        : 'Notifications',
                  ),
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

class _TopbarAction extends StatelessWidget {
  const _TopbarAction({
    required this.icon,
    required this.label,
    required this.onTap,
    this.active = false,
    this.badgeCount,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final bool active;
  final int? badgeCount;

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
              Badge(
                isLabelVisible: (badgeCount ?? 0) > 0,
                label: Text('$badgeCount'),
                child: Icon(icon, size: 18, color: active ? p.blue : p.muted),
              ),
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
    this.showNavigation = false,
    this.collapsed = false,
    this.onToggle,
    this.onTab,
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
  final bool showNavigation;
  final bool collapsed;
  final VoidCallback? onToggle;
  final ValueChanged<int>? onTab;

  static const _navGroups = <String, List<int>>{
    'TRAVAIL': [0, 1, 2],
    'SUPERVISION': [3, 4, 5, 6],
    'SYSTÈME': [7, 8, 9],
  };

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    final collaborators = _collaborators();
    final rail = showNavigation && collapsed;
    return AnimatedContainer(
      key: ValueKey(
        showNavigation ? 'expert-desktop-sidebar' : 'expert-drawer-sidebar',
      ),
      duration: const Duration(milliseconds: 180),
      curve: Curves.easeOut,
      width: width,
      decoration: BoxDecoration(
        color: p.sidebar,
        border: Border(right: BorderSide(color: p.border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _SidebarBrand(
            palette: p,
            collapsed: rail,
            onToggle: showNavigation ? onToggle : null,
          ),
          Expanded(
            child: ListView(
              padding: EdgeInsets.fromLTRB(
                rail ? 10 : 12,
                12,
                rail ? 10 : 12,
                16,
              ),
              children: [
                if (showNavigation) ...[
                  for (final group in _navGroups.entries) ...[
                    if (!rail)
                      Padding(
                        padding: const EdgeInsets.fromLTRB(10, 8, 10, 6),
                        child: Text(
                          group.key,
                          style: TextStyle(
                            color: p.subtle,
                            fontSize: 10,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1.3,
                          ),
                        ),
                      ),
                    for (final index in group.value)
                      _ExpertSidebarNavButton(
                        icon: _navIcon(index),
                        label: _navLabel(index),
                        active: tab == index,
                        collapsed: rail,
                        onTap: () => onTab?.call(index),
                      ),
                    const SizedBox(height: 8),
                  ],
                ],
                if (!rail) ...[
                  if (showNavigation) Divider(height: 28, color: p.border),
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
                      if (MediaQuery.sizeOf(context).width >= 700)
                        _MiniButton(
                          label: '+ Nouveau',
                          palette: p,
                          onTap: onCreate,
                        ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  _SidebarSearch(
                    controller: searchController,
                    palette: p,
                    onChanged: onSearch,
                  ),
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
              ],
            ),
          ),
          if (rail)
            Tooltip(
              message: 'Mon profil',
              child: Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  border: Border(top: BorderSide(color: p.border)),
                ),
                child: IconButton(
                  onPressed: onProfile,
                  tooltip: 'Mon profil',
                  icon: const Icon(Icons.settings_outlined),
                ),
              ),
            )
          else
            _SidebarFooter(
              palette: p,
              activity: activity,
              onProfile: onProfile,
            ),
        ],
      ),
    );
  }

  String _navLabel(int index) => switch (index) {
    0 => 'Éditeur de Normes',
    1 => 'Historique',
    2 => 'Experts & Groupes',
    3 => 'Réunions & Votes',
    4 => 'Cotisations & Indemnités',
    5 => 'Processus ISO',
    6 => 'Bureau Légistique',
    7 => 'Notifications',
    8 => 'Mon profil',
    9 => 'Adhésions',
    _ => 'Navigation',
  };

  IconData _navIcon(int index) => switch (index) {
    0 => Icons.description_outlined,
    1 => Icons.history,
    2 => Icons.groups_outlined,
    3 => Icons.how_to_vote_outlined,
    4 => Icons.account_balance_outlined,
    5 => Icons.verified_outlined,
    6 => Icons.gavel_outlined,
    7 => Icons.notifications_none,
    8 => Icons.person_outline,
    9 => Icons.person_add_alt,
    _ => Icons.circle_outlined,
  };

  List<(String, String)> _collaborators() {
    final names = <String>[];
    for (final doc in documents) {
      final name = doc['updatedBy'] as String?;
      if (name != null && name.trim().isNotEmpty && !names.contains(name))
        names.add(name);
    }
    return [
      (userName, 'Compte connecté'),
      for (final name in names.take(2))
        if (name != userName) (name, 'Contributeur du document'),
    ];
  }
}

class _ExpertSidebarNavButton extends StatelessWidget {
  const _ExpertSidebarNavButton({
    required this.icon,
    required this.label,
    required this.active,
    required this.collapsed,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final bool active;
  final bool collapsed;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    final button = Semantics(
      button: true,
      selected: active,
      label: label,
      child: Material(
        color: active ? p.surface : Colors.transparent,
        borderRadius: BorderRadius.circular(10),
        elevation: active ? 1 : 0,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(10),
          child: SizedBox(
            height: 42,
            child: Row(
              mainAxisAlignment: collapsed
                  ? MainAxisAlignment.center
                  : MainAxisAlignment.start,
              children: [
                Container(
                  width: collapsed ? 0 : 3,
                  color: active ? p.blue : Colors.transparent,
                ),
                SizedBox(width: collapsed ? 0 : 10),
                Icon(icon, size: 18, color: active ? p.blue : p.subtle),
                if (!collapsed) ...[
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      label,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: active ? p.title : p.muted,
                        fontSize: 13,
                        fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: collapsed ? Tooltip(message: label, child: button) : button,
    );
  }
}

class _SidebarBrand extends StatelessWidget {
  const _SidebarBrand({
    required this.palette,
    this.collapsed = false,
    this.onToggle,
  });

  final ExpertPalette palette;
  final bool collapsed;
  final VoidCallback? onToggle;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 72,
      padding: EdgeInsets.symmetric(horizontal: collapsed ? 8 : 14),
      decoration: BoxDecoration(
        color: palette.sidebarHeader,
        border: Border(bottom: BorderSide(color: palette.border)),
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          Row(
            children: [
              Container(
                width: collapsed ? 28 : 44,
                height: collapsed ? 28 : 44,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: const Color(0xFFD4AF37)),
                  color: Colors.white,
                ),
                clipBehavior: Clip.antiAlias,
                child: Image.asset(
                  'assets/img/logo-cnetp.png',
                  fit: BoxFit.cover,
                ),
              ),
              if (!collapsed) ...[
                const SizedBox(width: 8),
                SizedBox(
                  width: 4,
                  height: 32,
                  child: const Column(
                    children: [
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
                  child: Padding(
                    padding: EdgeInsets.only(right: onToggle == null ? 0 : 42),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'CNE-ITP',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1,
                            color: palette.muted,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'EXPERT · BÊTA',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
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
                ),
              ],
            ],
          ),
          if (onToggle != null)
            Positioned(
              right: 0,
              child: Tooltip(
                message: collapsed ? 'Ouvrir le menu' : 'Réduire le menu',
                child: InkWell(
                  onTap: onToggle,
                  borderRadius: BorderRadius.circular(8),
                  child: SizedBox(
                    width: collapsed ? 20 : 34,
                    height: 40,
                    child: Center(
                      child: Icon(
                        collapsed ? Icons.chevron_right : Icons.chevron_left,
                        size: 18,
                      ),
                    ),
                  ),
                ),
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
        color: p.sidebar,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                'ACTIVITÉ PERSONNELLE',
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
              Text('SERVEUR', style: TextStyle(fontSize: 9, color: p.muted)),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Text('COMPTE :', style: TextStyle(fontSize: 9, color: p.subtle)),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                decoration: BoxDecoration(
                  color: p.amberSoft,
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: p.amber.withValues(alpha: 0.3)),
                ),
                child: Text(
                  'PROFIL EXPERT',
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
  const _MessagingButton({
    required this.palette,
    required this.onPressed,
    this.unreadCount,
  });

  final ExpertPalette palette;
  final VoidCallback onPressed;
  final int? unreadCount;

  @override
  Widget build(BuildContext context) {
    final count = unreadCount ?? 0;
    final label = 'Messagerie CNE-ITP, $count non lu${count > 1 ? 's' : ''}';
    return Semantics(
      button: true,
      label: label,
      excludeSemantics: true,
      child: Tooltip(
        message: label,
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            Material(
              color: palette.blue,
              elevation: 4,
              shape: const CircleBorder(),
              child: InkWell(
                onTap: onPressed,
                customBorder: const CircleBorder(),
                child: const SizedBox.square(
                  dimension: 56,
                  child: Icon(
                    Icons.chat_bubble_outline,
                    color: Colors.white,
                    size: 25,
                  ),
                ),
              ),
            ),
            if (count > 0)
              Positioned(
                top: -3,
                right: -5,
                child: Container(
                  constraints: const BoxConstraints(
                    minWidth: 22,
                    minHeight: 22,
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 5),
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: const Color(0xFFDB3832),
                    shape: BoxShape.circle,
                    border: Border.all(color: palette.bg, width: 2),
                  ),
                  child: Text(
                    count > 99 ? '99+' : '$count',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.w900,
                      height: 1,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

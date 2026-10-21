import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/auth/auth_controller.dart';
import 'widgets/expert_editor_tab.dart';
import 'widgets/expert_other_tabs.dart';

/// Espace Expert — « Espace de travail » (refonte fidèle de /app/).
/// Thème sombre comme le template Django.
class ExpertScreen extends ConsumerStatefulWidget {
  const ExpertScreen({super.key, this.initialTab = 0});

  final int initialTab;

  @override
  ConsumerState<ExpertScreen> createState() => _ExpertScreenState();
}

class _ExpertScreenState extends ConsumerState<ExpertScreen> {
  int _tab = 0;
  List<Map<String, dynamic>> _documents = [];
  Map<String, dynamic>? _doc;
  bool _loadingDoc = false;

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

  Future<void> _selectDocument(Map<String, dynamic> doc) async {
    setState(() => _loadingDoc = true);
    try {
      final resp = await ApiClient.dio.get('/api/v1/norms/${doc['id']}/');
      if (!mounted) return;
      setState(() => _doc = resp.data as Map<String, dynamic>);
    } catch (_) {
      if (!mounted) return;
      setState(() => _doc = doc);
    } finally {
      if (mounted) setState(() => _loadingDoc = false);
    }
  }

  Widget _content() {
    switch (_tab) {
      case 1:
        return const ExpertHistoryTab();
      case 2:
        return const ExpertExpertsTab();
      case 3:
        return const ExpertMeetingsTab();
      case 4:
        return const ExpertFinancialTab();
      case 5:
        return const ExpertValidationTab();
      case 6:
        return const ExpertLegistiqueTab();
      case 7:
        return const ExpertNotificationsTab();
      case 8:
        return const ExpertProfileTab();
      default:
        return ExpertEditorTab(
          doc: _doc,
          loading: _loadingDoc,
          onSave: () => _selectDocument(_doc ?? {}),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(authControllerProvider).session;
    final userName = session?.fullName ?? 'Expert';

    return Scaffold(
      backgroundColor: ExpertColors.bg,
      body: SafeArea(
        child: Column(
          children: [
            _ExpertTopbar(
              tab: _tab,
              userName: userName,
              onTab: (i) => setState(() => _tab = i),
              onNotifications: () => setState(() => _tab = 7),
            ),
            Expanded(
              child: Row(
                children: [
                  _ExpertSidebar(
                    documents: _documents,
                    selectedId: _doc?['id']?.toString(),
                    onSelect: (d) {
                      setState(() => _tab = 0);
                      _selectDocument(d);
                    },
                    onProfile: () => setState(() => _tab = 8),
                    userName: userName,
                  ),
                  Expanded(child: _content()),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ExpertTopbar extends StatelessWidget {
  const _ExpertTopbar({
    required this.tab,
    required this.userName,
    required this.onTab,
    required this.onNotifications,
  });

  final int tab;
  final String userName;
  final ValueChanged<int> onTab;
  final VoidCallback onNotifications;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: ExpertColors.bg,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            height: 3,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: const [
                Expanded(child: ColoredBox(color: Color(0xFF0095C9))),
                Expanded(child: ColoredBox(color: Color(0xFFFFF24B))),
                Expanded(child: ColoredBox(color: Color(0xFFDB3832))),
              ],
            ),
          ),
          Container(
            height: 58,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: ExpertColors.border))),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: const Color(0xFFD4AF37)),
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: Image.asset('assets/img/logo-cnetp.png', fit: BoxFit.cover),
                ),
                const SizedBox(width: 10),
                const Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('CNE-ITP', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: ExpertColors.subtle, letterSpacing: 1.2)),
                    Text('ESPACE DE TRAVAIL', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: Color(0xFF3B82F6), letterSpacing: 0.5)),
                  ],
                ),
                const SizedBox(width: 18),
                Expanded(
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        for (int i = 0; i < _ExpertScreenState._tabs.length; i++)
                          _TabItem(
                            icon: _ExpertScreenState._tabs[i].$1,
                            label: _ExpertScreenState._tabs[i].$2,
                            active: tab == i,
                            onTap: () => onTab(i),
                          ),
                      ],
                    ),
                  ),
                ),
                InkWell(
                  onTap: onNotifications,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                    child: Icon(Icons.notifications_none,
                        size: 20, color: tab == 7 ? ExpertColors.blue : ExpertColors.muted),
                  ),
                ),
                const SizedBox(width: 6),
                Container(
                  width: 28,
                  height: 28,
                  decoration: const BoxDecoration(color: ExpertColors.blueDeep, shape: BoxShape.circle),
                  child: Center(
                    child: Text(
                      userName.isNotEmpty ? userName.substring(0, 1).toUpperCase() : '?',
                      style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w800),
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

class _TabItem extends StatelessWidget {
  const _TabItem({required this.icon, required this.label, required this.active, required this.onTap});
  final IconData icon;
  final String label;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        height: 58,
        padding: const EdgeInsets.symmetric(horizontal: 11),
        decoration: BoxDecoration(
          border: Border(bottom: BorderSide(color: active ? ExpertColors.blue : Colors.transparent, width: 2)),
        ),
        child: Row(
          children: [
            Icon(icon, size: 14, color: active ? ExpertColors.blue : ExpertColors.subtle),
            const SizedBox(width: 6),
            Text(
              label.toUpperCase(),
              style: TextStyle(
                fontSize: 9,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.3,
                color: active ? ExpertColors.blue : ExpertColors.muted,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ExpertSidebar extends StatelessWidget {
  const _ExpertSidebar({
    required this.documents,
    required this.selectedId,
    required this.onSelect,
    required this.onProfile,
    required this.userName,
  });

  final List<Map<String, dynamic>> documents;
  final String? selectedId;
  final ValueChanged<Map<String, dynamic>> onSelect;
  final VoidCallback onProfile;
  final String userName;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 250,
      decoration: const BoxDecoration(
        color: Color(0xFF06060C),
        border: Border(right: BorderSide(color: ExpertColors.border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 10),
            child: Row(
              children: [
                const Icon(Icons.folder_outlined, size: 14, color: ExpertColors.subtle),
                const SizedBox(width: 6),
                const Expanded(
                  child: Text('DOCUMENTS',
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 1.2, color: ExpertColors.muted)),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: ExpertColors.surface,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: ExpertColors.border),
                  ),
                  child: const Text('+ Nouveau', style: TextStyle(fontSize: 9, color: ExpertColors.blue)),
                ),
              ],
            ),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              children: [
                for (final doc in documents)
                  _DocItem(
                    doc: doc,
                    active: selectedId == doc['id']?.toString(),
                    onTap: () => onSelect(doc),
                  ),
                if (documents.isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('Aucun document', style: TextStyle(fontSize: 12, color: ExpertColors.subtle)),
                  ),
                const SizedBox(height: 12),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                  child: Text('COLLABORATEURS',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 1.2, color: ExpertColors.muted)),
                ),
                const _Collaborator(initials: 'EX', name: 'Expert', role: 'Expert'),
                const _Collaborator(initials: 'MA', name: 'MASAMBA .', role: 'Membre CTM / Membre WG'),
                const _Collaborator(initials: 'SI', name: 'Simon Barnabas PAKU MATONDO', role: 'Expert'),
              ],
            ),
          ),
          const Divider(height: 1, color: ExpertColors.border),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: const [
                    Text('ISO COMPLIANCE MODE', style: TextStyle(fontSize: 8, fontFamily: 'monospace', color: ExpertColors.subtle)),
                    Spacer(),
                    Icon(Icons.circle, size: 6, color: ExpertColors.blue),
                    SizedBox(width: 4),
                    Text('SYNC', style: TextStyle(fontSize: 9, color: ExpertColors.muted)),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: const [
                    Expanded(
                      child: Text('POSTE ACTIF :', overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 9, color: ExpertColors.subtle)),
                    ),
                    Text('RAPPORTEUR CTM', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: ExpertColors.amber)),
                  ],
                ),
                const SizedBox(height: 10),
                InkWell(
                  onTap: onProfile,
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
                    decoration: BoxDecoration(
                      color: ExpertColors.amber.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: ExpertColors.amber.withValues(alpha: 0.3)),
                    ),
                    child: const FittedBox(
                      fit: BoxFit.scaleDown,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text('CONFIGURER TOTAL DU PROFIL', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: ExpertColors.amber)),
                          SizedBox(width: 4),
                          Text('→', style: TextStyle(fontSize: 9, color: ExpertColors.amber)),
                        ],
                      ),
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

class _DocItem extends StatelessWidget {
  const _DocItem({required this.doc, required this.active, required this.onTap});
  final Map<String, dynamic> doc;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Material(
        color: active ? ExpertColors.blue.withValues(alpha: 0.10) : Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(8),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  doc['title'] as String? ?? 'Document',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w600,
                    color: active ? ExpertColors.blue : ExpertColors.text,
                  ),
                ),
                const SizedBox(height: 3),
                Row(
                  children: [
                    Flexible(
                      child: Text(
                        doc['code'] as String? ?? '',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 9, fontFamily: 'monospace', color: ExpertColors.subtle),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Flexible(
                      child: Text(
                        doc['category'] as String? ?? '',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 9, color: ExpertColors.subtle),
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
  const _Collaborator({required this.initials, required this.name, required this.role});
  final String initials;
  final String name;
  final String role;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      child: Row(
        children: [
          Container(
            width: 28,
            height: 28,
            decoration: const BoxDecoration(color: ExpertColors.blueDeep, shape: BoxShape.circle),
            child: Center(
              child: Text(initials,
                  style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: Colors.white)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: ExpertColors.text)),
                Text(role,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 9, color: ExpertColors.subtle)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

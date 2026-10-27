import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/api/api_client.dart';
import '../theme/copil_theme.dart';
import '../activity/copil_activity_screen.dart';
import '../console/copil_tools_screen.dart';
import '../console/widgets/copil_workflow_panel.dart';

class DirectoireBoardScreen extends ConsumerStatefulWidget {
  const DirectoireBoardScreen({super.key});
  @override
  ConsumerState<DirectoireBoardScreen> createState() =>
      _DirectoireBoardScreenState();
}

class _DirectoireBoardScreenState extends ConsumerState<DirectoireBoardScreen> {
  final _scaffold = GlobalKey<ScaffoldState>();
  Map<String, dynamic> _post = {}, _profile = {};
  int _phase = 1;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final response = await ApiClient.dio.get(
        '/api/v1/mobile/pilotage/directoire/',
      );
      final posts = (response.data['posts'] as List).cast<Map>();
      final mine = posts.where((p) => p['is_mine'] == true);
      if (mounted) {
        setState(() {
          _post = mine.isEmpty ? {} : Map<String, dynamic>.from(mine.first);
          _profile = Map<String, dynamic>.from(
            response.data['profile'] as Map? ?? {},
          );
          _error = mine.isEmpty
              ? 'Aucun poste du Bureau Directoire confirmé.'
              : null;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Impossible de charger le Bureau Directoire.');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final dark = ref.watch(copilDarkProvider);
    final p = dark ? CopilPalette.dark : CopilPalette.light;
    final size = MediaQuery.sizeOf(context);
    final desktop = size.width >= 1024;
    final wide = size.width >= 640;
    final receptionPhase = _post['n'] == 1
        ? 3
        : _post['n'] == 5
        ? 2
        : 0;
    final phases = (_post['phases'] as List? ?? []).cast<Map>();
    final phase = phases.where((row) => row['phase'] == _phase).firstOrNull;
    final items =
        (_phase == receptionPhase ? _post['reception'] : phase?['items'])
            as List? ??
        [];
    final title = '${_post['phase${_phase}_title'] ?? ''}';
    void closeMenu() {
      if (!desktop) Navigator.pop(context);
    }

    Widget navItem(
      IconData icon,
      String label,
      VoidCallback onTap, {
      bool selected = false,
      bool green = false,
    }) => Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Material(
        color: selected ? p.blueSoft : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              border: Border.all(
                color: selected
                    ? p.blue.withValues(alpha: .3)
                    : Colors.transparent,
              ),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: green ? p.successSoft : p.blueSoft,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    icon,
                    size: 16,
                    color: green ? p.success : p.blue,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    label,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      height: 1.3,
                      color: selected ? p.blue : p.text,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
    Widget navigation() => Container(
      width: 288,
      decoration: BoxDecoration(
        color: dark ? const Color(0xFF040408) : Colors.white,
        border: Border(right: BorderSide(color: p.border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              border: Border(bottom: BorderSide(color: p.border)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'PILOTAGE CNE-ITP',
                  style: TextStyle(
                    fontSize: 10,
                    letterSpacing: 1,
                    fontWeight: FontWeight.w700,
                    color: p.subtle,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${_post['title'] ?? ''}',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: p.title,
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Padding(
                    padding: const EdgeInsets.only(left: 12, bottom: 10),
                    child: Text(
                      'MES FONCTIONS',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1,
                        color: p.subtle,
                      ),
                    ),
                  ),
                  for (
                    var n = 1;
                    n <= (_post['phase3_title'] != null ? 3 : 2);
                    n++
                  )
                    navItem(
                      n == receptionPhase
                          ? Icons.task_outlined
                          : n == 1
                          ? Icons.play_circle_outline
                          : Icons.flag_outlined,
                      '${_post['phase${n}_title'] ?? 'Contrôle'}',
                      () {
                        closeMenu();
                        setState(() => _phase = n);
                      },
                      selected: _phase == n,
                      green: n == receptionPhase,
                    ),
                  navItem(Icons.hub_outlined, 'Organisation CNE-ITP', () {
                    closeMenu();
                    context.push('/pilotage/organisation');
                  }),
                  navItem(
                    Icons.monitor_heart_outlined,
                    'Activité des sous-commissions',
                    () {
                      closeMenu();
                      Navigator.push(
                        context,
                        MaterialPageRoute<void>(
                          builder: (_) => const CopilActivityScreen(),
                        ),
                      );
                    },
                  ),
                  navItem(
                    Icons.grid_view_outlined,
                    'Supervision des sous-commissions',
                    () {
                      closeMenu();
                      context.go('/pilotage');
                    },
                  ),
                ],
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              border: Border(top: BorderSide(color: p.border)),
            ),
            child: TextButton.icon(
              onPressed: () => context.go('/pilotage'),
              icon: Icon(Icons.dashboard_outlined, size: 14, color: p.muted),
              label: Text(
                'Retour au tableau de bord Pilotage',
                style: TextStyle(fontSize: 12, color: p.muted),
              ),
            ),
          ),
        ],
      ),
    );
    Widget iconAction(
      IconData icon,
      String label,
      VoidCallback onPressed, {
      Color? color,
    }) => SizedBox(
      width: 34,
      height: 34,
      child: IconButton(
        tooltip: label,
        onPressed: onPressed,
        padding: EdgeInsets.zero,
        style: IconButton.styleFrom(
          side: BorderSide(color: p.border),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
        icon: Icon(icon, size: 16, color: color ?? p.muted),
      ),
    );
    return CopilTheme(
      palette: p,
      child: Scaffold(
        key: _scaffold,
        backgroundColor: p.bg,
        drawer: desktop ? null : Drawer(width: 288, child: navigation()),
        body: SafeArea(
          child: Column(
            children: [
              Container(
                color: dark ? Colors.black : Colors.white,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SizedBox(
                      height: 4,
                      child: Row(
                        children: [
                          for (final color in const [
                            Color(0xFF0095C9),
                            Color(0xFFFFF24B),
                            Color(0xFFDB3832),
                          ])
                            Expanded(
                              child: ColoredBox(
                                color: color,
                                child: const SizedBox.expand(),
                              ),
                            ),
                        ],
                      ),
                    ),
                    Container(
                      height: 64,
                      padding: EdgeInsets.symmetric(horizontal: wide ? 20 : 16),
                      decoration: BoxDecoration(
                        border: Border(bottom: BorderSide(color: p.border)),
                      ),
                      child: Row(
                        children: [
                          if (wide) ...[
                            Container(
                              width: 36,
                              height: 36,
                              clipBehavior: Clip.antiAlias,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: Colors.white,
                                border: Border.all(
                                  color: const Color(0xFFD4AF37),
                                ),
                              ),
                              child: Image.asset(
                                'assets/img/logo-cnetp.png',
                                fit: BoxFit.cover,
                              ),
                            ),
                            const SizedBox(width: 10),
                            SizedBox(
                              width: 3,
                              height: 26,
                              child: Column(
                                children: [
                                  Expanded(child: Container(color: p.blue)),
                                  Container(
                                    height: 7,
                                    color: const Color(0xFFFFF24B),
                                  ),
                                  Expanded(
                                    child: Container(
                                      color: const Color(0xFFDB3832),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 12),
                          ],
                          if (!desktop)
                            IconButton(
                              tooltip: 'Ouvrir le menu',
                              onPressed: () =>
                                  _scaffold.currentState?.openDrawer(),
                              icon: Icon(Icons.menu, size: 20, color: p.muted),
                            ),
                          TextButton.icon(
                            onPressed: () => context.go('/pilotage'),
                            style: TextButton.styleFrom(
                              padding: EdgeInsets.zero,
                              minimumSize: Size.zero,
                            ),
                            icon: Icon(
                              Icons.arrow_back,
                              size: 14,
                              color: p.muted,
                            ),
                            label: wide
                                ? Text(
                                    'Pilotage',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: p.muted,
                                    ),
                                  )
                                : const SizedBox.shrink(),
                          ),
                          if (wide)
                            Padding(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                              ),
                              child: Text(
                                '|',
                                style: TextStyle(color: p.borderStrong),
                              ),
                            ),
                          Expanded(
                            child: Text(
                              'BUREAU DIRECTOIRE',
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                fontSize: desktop ? 16 : 12,
                                fontWeight: FontWeight.w800,
                                color: p.title,
                              ),
                            ),
                          ),
                          if (size.width >= 768 && _post.isNotEmpty)
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 6,
                              ),
                              decoration: BoxDecoration(
                                color: p.card,
                                border: Border.all(color: p.border),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  CircleAvatar(
                                    radius: 12,
                                    backgroundColor: p.blue,
                                    child: Text(
                                      '${_profile['initials'] ?? ''}',
                                      style: const TextStyle(
                                        fontSize: 10,
                                        fontWeight: FontWeight.w700,
                                        color: Colors.white,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Column(
                                    mainAxisSize: MainAxisSize.min,
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        '${_profile['name'] ?? ''}',
                                        style: TextStyle(
                                          fontSize: 11,
                                          fontWeight: FontWeight.w700,
                                          color: p.text,
                                        ),
                                      ),
                                      Text(
                                        '${_post['title']}'.toUpperCase(),
                                        style: TextStyle(
                                          fontSize: 9,
                                          color: p.subtle,
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          const SizedBox(width: 12),
                          iconAction(
                            Icons.auto_awesome_outlined,
                            'Assistant IA Pilotage',
                            () => Navigator.push(
                              context,
                              MaterialPageRoute<void>(
                                builder: (_) =>
                                    const CopilToolsScreen(tool: 'ai'),
                              ),
                            ),
                            color: p.blue,
                          ),
                          const SizedBox(width: 12),
                          iconAction(
                            dark
                                ? Icons.dark_mode_outlined
                                : Icons.light_mode_outlined,
                            'Changer le thème',
                            () => ref.read(copilDarkProvider.notifier).state =
                                !dark,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    if (desktop) navigation(),
                    Expanded(
                      child: _loading
                          ? const Center(child: CircularProgressIndicator())
                          : _error != null
                          ? Center(
                              child: TextButton(
                                onPressed: _load,
                                child: Text(_error!),
                              ),
                            )
                          : SingleChildScrollView(
                              padding: EdgeInsets.symmetric(
                                horizontal: wide ? 32 : 16,
                                vertical: 32,
                              ),
                              child: Center(
                                child: ConstrainedBox(
                                  constraints: const BoxConstraints(
                                    maxWidth: 832,
                                  ),
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.stretch,
                                    children: [
                                      Row(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Expanded(
                                            child: Text(
                                              title,
                                              style: TextStyle(
                                                fontSize: 18,
                                                fontWeight: FontWeight.w600,
                                                color: p.title,
                                              ),
                                            ),
                                          ),
                                          const SizedBox(width: 16),
                                          Text(
                                            '${items.length} dossier${items.length == 1 ? '' : 's'} ${_phase == receptionPhase ? 'transmis' : 'en attente'}',
                                            style: TextStyle(
                                              fontSize: 12,
                                              color: p.subtle,
                                            ),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 16),
                                      Divider(height: 1, color: p.border),
                                      if (items.isEmpty)
                                        Padding(
                                          padding: const EdgeInsets.symmetric(
                                            vertical: 24,
                                          ),
                                          child: Text(
                                            _phase == receptionPhase
                                                ? 'Aucun dossier transmis en attente de réception.'
                                                : 'Aucun dossier de cadrage enregistré à cette étape.',
                                            style: TextStyle(
                                              fontSize: 14,
                                              color: p.subtle,
                                            ),
                                          ),
                                        )
                                      else
                                        Padding(
                                          padding: const EdgeInsets.only(
                                            top: 16,
                                          ),
                                          child: CopilWorkflowPanel(
                                            key: ValueKey(_phase),
                                            kind: _phase == receptionPhase
                                                ? 'reception'
                                                : 'cadrage',
                                            items: items
                                                .map(
                                                  (e) =>
                                                      Map<String, dynamic>.from(
                                                        e as Map,
                                                      ),
                                                )
                                                .toList(),
                                            onChanged: _load,
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                              ),
                            ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

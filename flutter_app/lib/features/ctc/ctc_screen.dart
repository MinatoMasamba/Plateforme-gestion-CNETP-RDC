import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/auth/auth_controller.dart';
import '../../theme/app_colors.dart';
import 'widgets/ctc_dashboard.dart';
import 'widgets/ctc_modules.dart';
import 'widgets/ctc_sidebar.dart';
import 'widgets/ctc_topbar.dart';
import 'widgets/ctc_requests_view.dart';
import 'widgets/ctc_read_only_view.dart';

class CtcScreen extends ConsumerStatefulWidget {
  const CtcScreen({super.key});

  @override
  ConsumerState<CtcScreen> createState() => _CtcScreenState();
}

class _CtcScreenState extends ConsumerState<CtcScreen> {
  String _activeView = 'dashboard';
  bool _sidebarVisible = true;
  bool _mobileMenuVisible = false;

  Map<String, int> _counts = const {};
  String? _poleLabel;
  String? _subRole;
  bool _canAdminSystem = false;
  bool _blockedPolitical = false;
  List<CtcNavSection> _navSections = ctcNavSections;
  List<Map<String, dynamic>> _dossiers = [];
  List<Map<String, dynamic>> _assignations = [];
  List<Map<String, dynamic>> _stageRows = [];
  List<Map<String, dynamic>> _groupNormRows = [];
  List<Map<String, dynamic>> _requests = [];
  bool _loading = true;
  bool _hasLoaded = false;
  String? _loadError;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _loadError = null;
    });
    try {
      final results = await Future.wait([
        ApiClient.dio.get('/api/v1/mobile/ctc/dashboard/'),
        ApiClient.dio.get('/api/v1/mobile/ctc/dossiers/'),
        ApiClient.dio.get('/api/v1/mobile/ctc/assignations/'),
        ApiClient.dio.get('/api/v1/mobile/ctc/requests/'),
      ]);
      final dash = (results[0].data as Map<String, dynamic>);
      final dossiers =
          (results[1].data as Map<String, dynamic>)['results'] as List? ?? [];
      final assignations =
          (results[2].data as Map<String, dynamic>)['results'] as List? ?? [];
      final requests =
          (results[3].data as Map<String, dynamic>)['results'] as List? ?? [];
      final countsRaw = (dash['counts'] as Map<String, dynamic>?) ?? {};
      if (!mounted) return;
      setState(() {
        _counts = countsRaw.map((k, v) => MapEntry(k, (v as num).toInt()));
        _poleLabel = dash['pole_label']?.toString();
        _subRole = dash['ctc_sub_role']?.toString();
        _canAdminSystem = dash['can_admin_system'] == true;
        _blockedPolitical = dash['blocked_political'] == true;
        final nav = dash['sidebar_nav_config'];
        if (nav is Map<String, dynamic>) {
          _navSections = ctcSectionsFromConfig(nav);
        }
        _dossiers = dossiers.map((e) => e as Map<String, dynamic>).toList();
        _assignations = assignations
            .map((e) => e as Map<String, dynamic>)
            .toList();
        _requests = requests.map((e) => e as Map<String, dynamic>).toList();
        _stageRows = (dash['stage_rows'] as List? ?? [])
            .whereType<Map<String, dynamic>>()
            .toList();
        _groupNormRows = (dash['group_norm_rows'] as List? ?? [])
            .whereType<Map<String, dynamic>>()
            .toList();
        _loading = false;
        _hasLoaded = true;
        _loadError = null;
      });
    } catch (error) {
      if (!mounted) return;
      final detail = error is DioException && error.response?.data is Map
          ? (error.response!.data as Map)['detail']?.toString()
          : null;
      setState(() {
        _loading = false;
        _loadError = detail ?? 'Impossible de charger les données CTC.';
      });
    }
  }

  Future<void> _reviewRequest(int id, String decision, String comment) async {
    try {
      await ApiClient.dio.post(
        '/api/v1/mobile/ctc/$id/review_request/',
        data: {'decision': decision, 'comment': comment},
      );
      if (!mounted) return;
      setState(() {
        _requests.removeWhere((item) => item['id'] == id);
        _counts = {..._counts, 'demandes_en_attente': _requests.length};
      });
      await _load();
    } on DioException catch (error) {
      final data = error.response?.data;
      final detail = data is Map ? data['detail']?.toString() : null;
      throw Exception(detail ?? 'Décision refusée par le serveur.');
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(authControllerProvider).session;
    final userName = session?.fullName.trim().isNotEmpty == true
        ? session!.fullName
        : (session?.email ?? 'Expert');
    final poleLabel = _poleLabel ?? session?.ctcRole ?? 'Coordination';

    return Scaffold(
      backgroundColor: AppColors.page,
      body: SafeArea(
        child: Column(
          children: [
            CtcTopbar(
              poleLabel: poleLabel,
              userName: userName,
              onToggleSidebar: () => setState(() {
                if (MediaQuery.sizeOf(context).width < 760) {
                  _mobileMenuVisible = !_mobileMenuVisible;
                } else {
                  _sidebarVisible = !_sidebarVisible;
                }
              }),
              onLogout: () =>
                  ref.read(authControllerProvider.notifier).logout(),
            ),
            Expanded(
              child: LayoutBuilder(
                builder: (context, box) {
                  final compact = box.maxWidth < 760;
                  final sidebar = CtcSidebar(
                    activeView: _activeView,
                    onSelect: (view) => setState(() {
                      _activeView = view;
                      if (compact) _mobileMenuVisible = false;
                    }),
                    poleLabel: poleLabel,
                    userName: userName,
                    sections: _navSections,
                    onLogout: () =>
                        ref.read(authControllerProvider.notifier).logout(),
                  );
                  return Stack(
                    children: [
                      Row(
                        children: [
                          if (!compact && _sidebarVisible) sidebar,
                          Expanded(
                            child: ColoredBox(
                              color: AppColors.page,
                              child: Column(
                                children: [
                                  if (_loadError != null)
                                    MaterialBanner(
                                      content: Text(_loadError!),
                                      actions: [
                                        TextButton(
                                          onPressed: _load,
                                          child: const Text('Réessayer'),
                                        ),
                                      ],
                                    ),
                                  Expanded(child: _buildView()),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                      if (compact && _mobileMenuVisible) ...[
                        Positioned.fill(
                          child: GestureDetector(
                            onTap: () =>
                                setState(() => _mobileMenuVisible = false),
                            child: const ColoredBox(color: Color(0x66000000)),
                          ),
                        ),
                        Positioned(top: 0, bottom: 0, left: 0, child: sidebar),
                      ],
                    ],
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildView() {
    if (_loadError != null && !_hasLoaded) {
      return const Center(child: Text('Les données CTC sont indisponibles.'));
    }
    if (_loading &&
        _counts.isEmpty &&
        _dossiers.isEmpty &&
        _assignations.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }
    switch (_activeView) {
      case 'dashboard':
        return CtcDashboardView(
          poleLabel: _poleLabel ?? 'Coordination',
          subRole: _subRole,
          canAdminSystem: _canAdminSystem,
          blockedPolitical: _blockedPolitical,
          counts: _counts,
          dossiers: _dossiers,
          stageRows: _stageRows,
          groupNormRows: _groupNormRows,
          assignations: _assignations,
          onOpenAssignations: () =>
              setState(() => _activeView = 'assignations'),
          onOpenDossiers: () => setState(() => _activeView = 'dossiers'),
        );
      case 'dossiers':
        return _DossiersView(dossiers: _dossiers);
      case 'assignations':
        return _AssignationsView(assignations: _assignations);
      case 'ctc_requests':
      case 'assistant_executif':
        return CtcRequestsView(
          requests: _requests,
          canReview: _subRole == 'assistant_executif',
          assistantPage: _activeView == 'assistant_executif',
          onDecision: _reviewRequest,
        );
      case 'experts':
      case 'tracabilite':
        return CtcReadOnlyView(key: ValueKey(_activeView), view: _activeView);
      case 'instructions':
        return const CtcInstructionsView();
      case 'homologations':
      case 'archives':
        return CtcNormsView(key: ValueKey(_activeView), view: _activeView);
      default:
        return CtcModuleView(
          view: _activeView,
          counts: _counts,
          dossiers: _dossiers,
          stageRows: _stageRows,
          groupNormRows: _groupNormRows,
        );
    }
  }
}

class _DossiersView extends StatelessWidget {
  const _DossiersView({required this.dossiers});
  final List<Map<String, dynamic>> dossiers;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Dossiers normatifs',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              color: AppColors.text,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            '${dossiers.length} dossier(s) dans le circuit CTC.',
            style: const TextStyle(fontSize: 13, color: AppColors.muted),
          ),
          const SizedBox(height: 20),
          if (dossiers.isEmpty)
            const _Empty('Aucun dossier dans le circuit CTC.')
          else
            for (final d in dossiers) _DossierCard(d),
        ],
      ),
    );
  }
}

class _DossierCard extends StatelessWidget {
  const _DossierCard(this.d);
  final Map<String, dynamic> d;

  @override
  Widget build(BuildContext context) {
    final icon = Container(
      width: 38,
      height: 38,
      decoration: BoxDecoration(
        color: AppColors.rdcBlue.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(10),
      ),
      child: const Icon(
        Icons.folder_outlined,
        size: 18,
        color: AppColors.rdcBlue,
      ),
    );
    final details = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          d['reference'] as String? ?? '',
          style: const TextStyle(
            fontSize: 11,
            color: AppColors.subtle,
            fontFamily: 'monospace',
          ),
        ),
        const SizedBox(height: 2),
        Text(
          d['title'] as String? ?? '',
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w700,
            color: AppColors.text,
          ),
        ),
      ],
    );
    final stage = Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: AppColors.rdcBlue.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        d['stage_label'] as String? ?? '',
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w700,
          color: AppColors.rdcBlue,
        ),
      ),
    );
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: LayoutBuilder(
        builder: (context, box) {
          if (box.maxWidth < 600) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    icon,
                    const SizedBox(width: 12),
                    Expanded(child: details),
                  ],
                ),
                const SizedBox(height: 12),
                stage,
              ],
            );
          }
          return Row(
            children: [
              icon,
              const SizedBox(width: 12),
              Expanded(child: details),
              const SizedBox(width: 12),
              Flexible(child: stage),
            ],
          );
        },
      ),
    );
  }
}

class _AssignationsView extends StatelessWidget {
  const _AssignationsView({required this.assignations});
  final List<Map<String, dynamic>> assignations;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Mes Assignations',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              color: AppColors.text,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            '${assignations.length} assignation(s) attribuée(s) à votre poste.',
            style: const TextStyle(fontSize: 13, color: AppColors.muted),
          ),
          const SizedBox(height: 20),
          if (assignations.isEmpty)
            const _Empty("Aucune assignation explicite n'attend ce poste.")
          else
            for (final a in assignations)
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppColors.border),
                ),
                child: LayoutBuilder(
                  builder: (context, box) {
                    final details = Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          a['type_label'] as String? ?? 'Traitement CTC',
                          style: const TextStyle(
                            fontSize: 11,
                            color: AppColors.muted,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          a['title'] as String? ?? '',
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w700,
                            color: AppColors.text,
                          ),
                        ),
                      ],
                    );
                    final status = Text(
                      a['status_display'] as String? ?? '',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: AppColors.warning,
                      ),
                    );
                    const icon = Icon(
                      Icons.check_circle_outline,
                      size: 20,
                      color: AppColors.success,
                    );
                    if (box.maxWidth < 600) {
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              icon,
                              const SizedBox(width: 12),
                              Expanded(child: details),
                            ],
                          ),
                          const SizedBox(height: 10),
                          status,
                        ],
                      );
                    }
                    return Row(
                      children: [
                        icon,
                        const SizedBox(width: 12),
                        Expanded(child: details),
                        const SizedBox(width: 12),
                        Flexible(child: status),
                      ],
                    );
                  },
                ),
              ),
        ],
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty(this.msg);
  final String msg;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 40),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Text(
        msg,
        textAlign: TextAlign.center,
        style: const TextStyle(color: AppColors.muted),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/auth/auth_controller.dart';
import '../../theme/app_colors.dart';
import 'widgets/ctc_dashboard.dart';
import 'widgets/ctc_modules.dart';
import 'widgets/ctc_sidebar.dart';
import 'widgets/ctc_topbar.dart';

class CtcScreen extends ConsumerStatefulWidget {
  const CtcScreen({super.key});

  @override
  ConsumerState<CtcScreen> createState() => _CtcScreenState();
}

class _CtcScreenState extends ConsumerState<CtcScreen> {
  String _activeView = 'dashboard';
  bool _sidebarVisible = true;

  Map<String, int> _counts = const {};
  List<Map<String, dynamic>> _dossiers = [];
  List<Map<String, dynamic>> _assignations = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final results = await Future.wait([
        ApiClient.dio.get('/api/v1/mobile/ctc/dashboard/'),
        ApiClient.dio.get('/api/v1/mobile/ctc/dossiers/'),
        ApiClient.dio.get('/api/v1/mobile/ctc/assignations/'),
      ]);
      final dash = (results[0].data as Map<String, dynamic>);
      final dossiers =
          (results[1].data as Map<String, dynamic>)['results'] as List? ?? [];
      final assignations =
          (results[2].data as Map<String, dynamic>)['results'] as List? ?? [];
      final countsRaw = (dash['counts'] as Map<String, dynamic>?) ?? {};
      if (!mounted) return;
      setState(() {
        _counts = countsRaw.map((k, v) => MapEntry(k, (v as num).toInt()));
        _dossiers = dossiers.map((e) => e as Map<String, dynamic>).toList();
        _assignations = assignations
            .map((e) => e as Map<String, dynamic>)
            .toList();
        _loading = false;
      });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(authControllerProvider).session;
    final userName = session?.fullName ?? 'Expert';
    final poleLabel = session?.ctcRole ?? 'Coordination';

    return Scaffold(
      backgroundColor: AppColors.page,
      body: SafeArea(
        child: Column(
          children: [
            CtcTopbar(
              poleLabel: poleLabel,
              userName: userName,
              onToggleSidebar: () =>
                  setState(() => _sidebarVisible = !_sidebarVisible),
              onLogout: () =>
                  ref.read(authControllerProvider.notifier).logout(),
            ),
            Expanded(
              child: Row(
                children: [
                  if (_sidebarVisible)
                    CtcSidebar(
                      activeView: _activeView,
                      onSelect: (v) => setState(() => _activeView = v),
                      poleLabel: poleLabel,
                      userName: userName,
                    ),
                  Expanded(
                    child: ColoredBox(
                      color: AppColors.page,
                      child: _buildView(),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildView() {
    if (_loading && _activeView == 'dashboard') {
      return const Center(child: CircularProgressIndicator());
    }
    switch (_activeView) {
      case 'dashboard':
        return CtcDashboardView(
          poleLabel: 'Secrétariat technique',
          counts: _counts,
          dossiers: _dossiers,
          assignations: _assignations,
          onOpenAssignations: () =>
              setState(() => _activeView = 'assignations'),
        );
      case 'dossiers':
        return _DossiersView(dossiers: _dossiers);
      case 'assignations':
        return _AssignationsView(assignations: _assignations);
      default:
        return CtcModuleView(
          view: _activeView,
          counts: _counts,
          dossiers: _dossiers,
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
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Container(
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
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
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
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: AppColors.text,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: AppColors.rdcBlue.withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(999),
            ),
            child: Text(
              d['stage_label'] as String? ?? '',
              style: const TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w700,
                color: AppColors.rdcBlue,
              ),
            ),
          ),
        ],
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
                child: Row(
                  children: [
                    const Icon(
                      Icons.check_circle_outline,
                      size: 20,
                      color: AppColors.success,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
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
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w700,
                              color: AppColors.text,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      a['status_display'] as String? ?? '',
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: AppColors.warning,
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

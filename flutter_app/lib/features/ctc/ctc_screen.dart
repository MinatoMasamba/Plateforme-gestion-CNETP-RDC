import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/auth/auth_controller.dart';
import '../../theme/app_colors.dart';
import 'widgets/ctc_dashboard.dart';
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

  static const _titles = <String, String>{
    'dashboard': 'Tableau de bord',
    'dossiers': 'Dossiers normatifs',
    'assignations': 'Mes Assignations',
    'ctc_requests': 'Demandes à traiter',
    'assistant_executif': 'Assistant Exécutif',
    'financial': 'Budget & Comptabilité',
    'statistiques': 'Suivi statistique',
    'homologations': 'Homologations',
    'instructions': 'Instructions',
    'reunions': 'Réunions',
    'drive': 'Espace Drive CNE-ITP',
    'archives': 'Archives',
    'parametres': 'Paramètres',
  };

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(authControllerProvider).session;
    final userName = session?.fullName ?? 'Expert';
    final poleLabel = 'Coordination';

    return Scaffold(
      backgroundColor: AppColors.page,
      body: SafeArea(
        child: Column(
          children: [
            CtcTopbar(
              poleLabel: poleLabel,
              userName: userName,
              onToggleSidebar: () => setState(() => _sidebarVisible = !_sidebarVisible),
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
                      child: _activeView == 'dashboard'
                          ? CtcDashboardView(poleLabel: poleLabel)
                          : _PlaceholderView(title: _titles[_activeView] ?? _activeView),
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
}

class _PlaceholderView extends StatelessWidget {
  const _PlaceholderView({required this.title});
  final String title;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: AppColors.text),
          ),
          const SizedBox(height: 6),
          const Text(
            'Gestion et suivi des travaux de normalisation.',
            style: TextStyle(fontSize: 13, color: AppColors.muted),
          ),
          const SizedBox(height: 24),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 48),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: AppColors.border),
            ),
            child: const Column(
              children: [
                Icon(Icons.construction_outlined, size: 40, color: AppColors.subtle),
                SizedBox(height: 12),
                Text(
                  'Cette vue est en cours de construction.',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.muted),
                ),
                SizedBox(height: 4),
                Text(
                  'Le contenu détaillé sera disponible prochainement.',
                  style: TextStyle(fontSize: 12, color: AppColors.subtle),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

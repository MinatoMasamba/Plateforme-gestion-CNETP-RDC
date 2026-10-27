import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/auth_controller.dart';
import '../../../theme/app_colors.dart';
import '../console/widgets/copil_topbar.dart';

/// Espace "Bureau Directoire" / "Conseillers" (postes nominatifs).
///
/// Les postes sont calculés côté serveur ; en l'absence de postes en base,
/// l'écran affiche la structure (topbar + sidebar + phases) avec des états vides.
class DirectoireScreen extends ConsumerStatefulWidget {
  const DirectoireScreen({super.key, this.conseillers = false});

  final bool conseillers;

  @override
  ConsumerState<DirectoireScreen> createState() => _DirectoireScreenState();
}

class _DirectoireScreenState extends ConsumerState<DirectoireScreen> {
  int _phase = 1;
  bool _sidebarVisible = true;

  static const _phaseTitles = <String>[
    'Cadrage stratégique',
    'Contrôle technique',
    'Mandat',
    'Réception',
    'Homologation',
  ];

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(authControllerProvider).session;
    final userName = session?.fullName ?? 'Expert';
    final title = widget.conseillers
        ? 'Conseillers Institutionnels'
        : 'Bureau Directoire';

    return Scaffold(
      backgroundColor: AppColors.page,
      body: SafeArea(
        child: Column(
          children: [
            CopilTopbar(
              memberCount: 0,
              onToggleSidebar: () =>
                  setState(() => _sidebarVisible = !_sidebarVisible),
            ),
            Expanded(
              child: Row(
                children: [
                  if (_sidebarVisible) _buildSidebar(title),
                  Expanded(
                    child: ColoredBox(
                      color: AppColors.page,
                      child: SingleChildScrollView(
                        child: Container(
                          constraints: const BoxConstraints(maxWidth: 860),
                          margin: const EdgeInsets.symmetric(
                            vertical: 28,
                            horizontal: 24,
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              _PosteCard(
                                title: '$title — $userName',
                                origin: 'Manuel organisationnel CNETP 2026',
                                mission:
                                    'Coordination et validation des travaux de normalisation.',
                              ),
                              const SizedBox(height: 16),
                              for (final p in _phaseTitles.take(
                                widget.conseillers ? 3 : 5,
                              ))
                                Padding(
                                  padding: const EdgeInsets.only(bottom: 12),
                                  child: _PhaseCard(title: p),
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
    );
  }

  Widget _buildSidebar(String title) {
    return Container(
      width: 264,
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(right: BorderSide(color: AppColors.border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Pilotage CNE-ITP',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.5,
                    color: AppColors.subtle,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    color: AppColors.text,
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1, color: AppColors.border),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                    child: Text(
                      'MES FONCTIONS',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.4,
                        color: AppColors.subtle,
                      ),
                    ),
                  ),
                  for (int i = 0; i < _phaseTitles.length; i++)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Material(
                        color: _phase == i
                            ? AppColors.rdcBlue.withValues(alpha: 0.10)
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(11),
                        child: InkWell(
                          onTap: () => setState(() => _phase = i),
                          borderRadius: BorderRadius.circular(11),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 10,
                              vertical: 10,
                            ),
                            child: Text(
                              _phaseTitles[i],
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: _phase == i
                                    ? FontWeight.w800
                                    : FontWeight.w600,
                                color: _phase == i
                                    ? AppColors.rdcBlue
                                    : AppColors.muted,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PosteCard extends StatelessWidget {
  const _PosteCard({
    required this.title,
    required this.origin,
    required this.mission,
  });
  final String title;
  final String origin;
  final String mission;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: AppColors.rdcBlue.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Icon(
              Icons.badge_outlined,
              size: 22,
              color: AppColors.rdcBlue,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: AppColors.text,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  origin.toUpperCase(),
                  style: const TextStyle(
                    fontSize: 10,
                    letterSpacing: 1.2,
                    color: AppColors.subtle,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  mission,
                  style: const TextStyle(
                    fontSize: 13,
                    height: 1.5,
                    color: AppColors.muted,
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

class _PhaseCard extends StatelessWidget {
  const _PhaseCard({required this.title});
  final String title;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title.toUpperCase(),
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.3,
                  color: AppColors.rdcBlue,
                ),
              ),
              const Text(
                '0 dossier en attente',
                style: TextStyle(fontSize: 11, color: AppColors.subtle),
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Text(
            'Aucun dossier de cadrage enregistré à cette étape.',
            style: TextStyle(fontSize: 13, color: AppColors.muted),
          ),
        ],
      ),
    );
  }
}

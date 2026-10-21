import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/auth/auth_controller.dart';
import '../../core/routing/app_router.dart';
import '../../theme/app_colors.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final loggedIn = auth.status == AuthStatus.authenticated;
    final space = auth.session?.space ?? '';

    return Scaffold(
      backgroundColor: Colors.white,
      body: Stack(
        children: [
          Positioned.fill(
            child: SingleChildScrollView(
              child: Column(
                children: [
                  const _Hero(),
                  const _StatsBand(),
                  const _FeatureGrid(),
                  const SizedBox(height: 80),
                ],
              ),
            ),
          ),
          // Barre de navigation supérieure (transparente sur le hero)
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: _TopNav(loggedIn: loggedIn, space: space),
          ),
        ],
      ),
    );
  }
}

class _TopNav extends StatelessWidget {
  const _TopNav({required this.loggedIn, required this.space});
  final bool loggedIn;
  final String space;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 16),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: Colors.white,
              border: Border.all(color: const Color(0xFFD4AF37)),
            ),
            clipBehavior: Clip.antiAlias,
            child: Image.asset('assets/img/logo-cnetp.png', fit: BoxFit.cover),
          ),
          const SizedBox(width: 10),
          const Text(
            'CNE-ITP',
            style: TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.w800,
              letterSpacing: 1,
            ),
          ),
          const Spacer(),
          if (loggedIn)
            _NavChip(
              label: 'Ouvrir mon espace',
              onTap: () => context.go(spacePath(space)),
            )
          else ...[
            _NavChip(
              label: 'Se connecter',
              solid: true,
              onTap: () => context.go('/login'),
            ),
          ],
        ],
      ),
    );
  }
}

class _NavChip extends StatelessWidget {
  const _NavChip({required this.label, required this.onTap, this.solid = false});
  final String label;
  final VoidCallback onTap;
  final bool solid;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: solid ? AppColors.rdcYellow : Colors.transparent,
      borderRadius: BorderRadius.circular(8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8),
            border: solid ? null : Border.all(color: Colors.white.withValues(alpha: 0.4)),
          ),
          child: Text(
            label.toUpperCase(),
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.4,
              color: solid ? const Color(0xFF0F172A) : Colors.white,
            ),
          ),
        ),
      ),
    );
  }
}

class _Hero extends StatelessWidget {
  const _Hero();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 560,
      width: double.infinity,
      child: Stack(
        fit: StackFit.expand,
        children: [
          Image.asset('assets/img/hero.jpg', fit: BoxFit.cover),
          Container(color: const Color(0xFF071527).withValues(alpha: 0.75)),
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.bottomCenter,
                end: Alignment.topCenter,
                colors: [
                  const Color(0xFF020617),
                  const Color(0xFF020617).withValues(alpha: 0),
                ],
              ),
            ),
          ),
          Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 900),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 28),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        border: Border.all(
                          color: Colors.white.withValues(alpha: 0.2),
                        ),
                        color: Colors.white.withValues(alpha: 0.1),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 8,
                            height: 8,
                            decoration: const BoxDecoration(
                              color: AppColors.rdcYellow,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 8),
                          const Text(
                            'RÉPUBLIQUE DÉMOCRATIQUE DU CONGO',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 1.6,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                    const Text(
                      'Le portail national des normes techniques',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 44,
                        fontWeight: FontWeight.w900,
                        height: 1.1,
                      ),
                    ),
                    const SizedBox(height: 18),
                    const Text(
                      'Le CNETP centralise la rédaction, l\'examen et la publication des normes applicables à la construction, aux infrastructures et aux travaux publics.',
                      style: TextStyle(
                        color: Color(0xFFE2E8F0),
                        fontSize: 15,
                        height: 1.6,
                      ),
                    ),
                    const SizedBox(height: 28),
                    Row(
                      children: [
                        Material(
                          color: AppColors.rdcYellow,
                          borderRadius: BorderRadius.circular(8),
                          child: InkWell(
                            onTap: () => context.go('/login'),
                            borderRadius: BorderRadius.circular(8),
                            child: const Padding(
                              padding: EdgeInsets.symmetric(horizontal: 22, vertical: 13),
                              child: Text(
                                'SE CONNECTER',
                                style: TextStyle(
                                  fontSize: 10.5,
                                  fontWeight: FontWeight.w800,
                                  letterSpacing: 1.4,
                                  color: Color(0xFF0F172A),
                                ),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Material(
                          color: Colors.white.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(8),
                          child: InkWell(
                            onTap: () {},
                            borderRadius: BorderRadius.circular(8),
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 13),
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: Colors.white.withValues(alpha: 0.4)),
                              ),
                              child: const Text(
                                'DÉCOUVRIR LE FONCTIONNEMENT',
                                style: TextStyle(
                                  fontSize: 10.5,
                                  fontWeight: FontWeight.w800,
                                  letterSpacing: 1.4,
                                  color: Colors.white,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
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

class _StatsBand extends StatelessWidget {
  const _StatsBand();

  static const _stats = [
    ('25+', 'Normes en traitement'),
    ('200', 'Experts mobilisés'),
    ('8', 'Comités techniques'),
    ('24', 'Groupes de travail'),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 28),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1100),
          child: Transform.translate(
            offset: const Offset(0, -40),
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(2),
                border: Border.all(color: const Color(0xFFE2E8F0)),
                boxShadow: const [
                  BoxShadow(color: Color(0x1A000000), blurRadius: 24, offset: Offset(0, 8)),
                ],
              ),
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final cols = constraints.maxWidth >= 760 ? 4 : 2;
                  const gap = 1.0;
                  final w = (constraints.maxWidth - gap * (cols - 1)) / cols;
                  return Wrap(
                    children: [
                      for (int i = 0; i < _stats.length; i++)
                        Container(
                          width: w,
                          padding: const EdgeInsets.symmetric(vertical: 26, horizontal: 16),
                          decoration: BoxDecoration(
                            border: Border(
                              right: (i % cols != cols - 1)
                                  ? const BorderSide(color: Color(0xFFE2E8F0))
                                  : BorderSide.none,
                            ),
                          ),
                          child: Column(
                            children: [
                              Text(
                                _stats[i].$1,
                                style: const TextStyle(
                                  fontSize: 30,
                                  fontWeight: FontWeight.w900,
                                  color: AppColors.text,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                _stats[i].$2,
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: AppColors.muted,
                                ),
                              ),
                            ],
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
}

class _FeatureGrid extends StatelessWidget {
  const _FeatureGrid();

  static const _features = [
    (Icons.menu_book_outlined, 'Bibliothèque des normes', 'Consultez les normes publiées, les projets soumis à consultation et les documents associés.'),
    (Icons.edit_note_outlined, 'Élaboration des normes', 'Rédigez, relisez et consolidez les projets avec les contributions des experts concernés.'),
    (Icons.groups_outlined, 'Réseau d\'experts', 'Identifiez les membres, les compétences et les structures associés aux travaux des comités.'),
    (Icons.event_outlined, 'Réunions et décisions', 'Préparez les réunions, suivez les participants et conservez les décisions prises par les instances.'),
    (Icons.gavel_outlined, 'Relecture juridique', 'Contrôlez la cohérence des textes et leur conformité avec le cadre juridique applicable.'),
    (Icons.fact_check_outlined, 'Suivi administratif', 'Suivez les engagements, les présences et les éléments administratifs liés aux travaux des experts.'),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 28),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1100),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Des outils pour chaque étape',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w800,
                  color: AppColors.text,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Les modules réunissent les ressources documentaires, les échanges de travail et le suivi administratif nécessaires à la conduite des travaux.',
                style: TextStyle(fontSize: 14, color: AppColors.muted, height: 1.6),
              ),
              const SizedBox(height: 28),
              LayoutBuilder(
                builder: (context, constraints) {
                  final cols = constraints.maxWidth >= 900 ? 3 : constraints.maxWidth >= 560 ? 2 : 1;
                  const gap = 20.0;
                  final w = (constraints.maxWidth - gap * (cols - 1)) / cols;
                  return Wrap(
                    spacing: gap,
                    runSpacing: gap,
                    children: [
                      for (final f in _features)
                        Container(
                          width: w,
                          padding: const EdgeInsets.all(22),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF8FAFC),
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(color: const Color(0xFFE2E8F0)),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                width: 42,
                                height: 42,
                                decoration: BoxDecoration(
                                  color: AppColors.rdcBlue.withValues(alpha: 0.1),
                                  borderRadius: BorderRadius.circular(11),
                                ),
                                child: Icon(f.$1, size: 20, color: AppColors.rdcBlue),
                              ),
                              const SizedBox(height: 14),
                              Text(
                                f.$2,
                                style: const TextStyle(
                                  fontSize: 14,
                                  fontWeight: FontWeight.w800,
                                  color: AppColors.text,
                                ),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                f.$3,
                                style: const TextStyle(
                                  fontSize: 12,
                                  height: 1.5,
                                  color: AppColors.muted,
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}

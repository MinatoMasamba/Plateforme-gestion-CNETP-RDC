import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/link.dart';
import '../../core/api/api_client.dart';

import '../../core/auth/auth_controller.dart';
import '../../core/routing/app_router.dart';
import '../../theme/app_colors.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final _scroll = ScrollController();
  final _workflowKey = GlobalKey();
  final _modulesKey = GlobalKey();

  void _discover(GlobalKey key) {
    final target = key.currentContext;
    if (target != null) {
      Scrollable.ensureVisible(
        target,
        duration: const Duration(milliseconds: 550),
        curve: Curves.easeOutCubic,
      );
    }
  }

  @override
  void dispose() {
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final loggedIn = auth.status == AuthStatus.authenticated;
    final space = auth.session?.space ?? '';

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            _TopNav(loggedIn: loggedIn, space: space),
            Expanded(
              child: SingleChildScrollView(
                controller: _scroll,
                child: Column(
                  children: [
                    _Hero(
                      onDiscover: () => _discover(_workflowKey),
                      onOpen: () =>
                          context.go(loggedIn ? spacePath(space) : '/login'),
                      loggedIn: loggedIn,
                    ),
                    const _StatsBand(),
                    _WorkflowSection(key: _workflowKey),
                    _FeatureGrid(key: _modulesKey),
                    const _AudienceSection(),
                    const _FinalCta(),
                    _Footer(
                      onFeatures: () => _discover(_workflowKey),
                      onModules: () => _discover(_modulesKey),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Brand extends StatelessWidget {
  const _Brand({this.dark = false});
  final bool dark;
  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Container(
        width: 46,
        height: 46,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(color: const Color(0xFFD4AF37)),
          color: Colors.white,
        ),
        clipBehavior: Clip.antiAlias,
        child: Image.asset('assets/img/logo-cnetp.png', fit: BoxFit.cover),
      ),
      const SizedBox(width: 10),
      SizedBox(
        width: 3,
        height: 30,
        child: Column(
          children: const [
            Expanded(
              child: ColoredBox(
                color: AppColors.rdcBlue,
                child: SizedBox.expand(),
              ),
            ),
            Expanded(
              child: ColoredBox(
                color: AppColors.rdcYellow,
                child: SizedBox.expand(),
              ),
            ),
            Expanded(
              child: ColoredBox(
                color: AppColors.rdcRed,
                child: SizedBox.expand(),
              ),
            ),
          ],
        ),
      ),
      const SizedBox(width: 10),
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'SECRÉTARIAT TECHNIQUE',
            style: TextStyle(
              fontSize: 9,
              fontWeight: FontWeight.w700,
              letterSpacing: .6,
              color: dark ? Colors.white70 : AppColors.muted,
            ),
          ),
          Text(
            'PORTAIL CNE-ITP RDC',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w900,
              color: dark ? Colors.white : AppColors.accentDark,
            ),
          ),
          Text(
            'M.I.T.P. & NUMÉRIQUE',
            style: TextStyle(
              fontSize: 9,
              color: dark ? Colors.white60 : AppColors.muted,
            ),
          ),
        ],
      ),
    ],
  );
}

class _TopNav extends StatelessWidget {
  const _TopNav({required this.loggedIn, required this.space});
  final bool loggedIn;
  final String space;

  @override
  Widget build(BuildContext context) => Container(
    color: Colors.white,
    height: 80,
    padding: const EdgeInsets.symmetric(horizontal: 20),
    child: Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 1216),
        child: LayoutBuilder(
          builder: (context, box) => Row(
            children: [
              InkWell(onTap: () => context.go('/'), child: const _Brand()),
              const Spacer(),
              if (box.maxWidth >= 900) ...[
                TextButton(
                  onPressed: () => context.go('/'),
                  child: const Text('ACCUEIL'),
                ),
                const _PortalLink('/about/', 'À PROPOS'),
                const _PortalLink('/contact/', 'CONTACT'),
                const Spacer(),
                if (!loggedIn)
                  TextButton(
                    onPressed: () => context.go('/login'),
                    child: const Text('SE CONNECTER'),
                  ),
                const SizedBox(width: 12),
                FilledButton(
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.rdcYellow,
                    foregroundColor: AppColors.text,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                  onPressed: () =>
                      context.go(loggedIn ? spacePath(space) : '/candidature'),
                  child: Text(
                    loggedIn ? 'MON ESPACE' : 'FORUM CNE-ITP',
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ] else
                PopupMenuButton<String>(
                  tooltip: 'Menu',
                  icon: const Icon(Icons.menu),
                  onSelected: (path) => context.go(path),
                  itemBuilder: (_) => [
                    const PopupMenuItem(value: '/', child: Text('Accueil')),
                    PopupMenuItem(
                      value: loggedIn ? spacePath(space) : '/login',
                      child: Text(loggedIn ? 'Mon espace' : 'Se connecter'),
                    ),
                    const PopupMenuItem(
                      value: '/candidature',
                      child: Text('Forum CNE-ITP · Candidature'),
                    ),
                    const PopupMenuItem(
                      enabled: false,
                      child: _PortalLink('/about/', 'À propos'),
                    ),
                    const PopupMenuItem(
                      enabled: false,
                      child: _PortalLink('/contact/', 'Contact'),
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

class _PortalLink extends StatelessWidget {
  const _PortalLink(this.path, this.label, {this.dark = false});
  final String path, label;
  final bool dark;
  @override
  Widget build(BuildContext context) => Link(
    uri: ApiClient.api(path),
    target: LinkTarget.blank,
    builder: (_, followLink) => TextButton(
      onPressed: followLink,
      style: TextButton.styleFrom(
        foregroundColor: dark ? const Color(0xFFCBD5E1) : AppColors.muted,
      ),
      child: Text(
        label,
        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
      ),
    ),
  );
}

class _Hero extends StatelessWidget {
  const _Hero({
    required this.onDiscover,
    required this.onOpen,
    required this.loggedIn,
  });
  final VoidCallback onDiscover, onOpen;
  final bool loggedIn;

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, box) {
      final mobile = box.maxWidth < 640;
      return SizedBox(
        height: mobile ? 540 : 560,
        width: double.infinity,
        child: Stack(
          fit: StackFit.expand,
          children: [
            Image.asset('assets/img/hero.jpg', fit: BoxFit.cover),
            const ColoredBox(color: Color(0xBF071527)),
            const DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.bottomCenter,
                  end: Alignment.topCenter,
                  colors: [Color(0xFF020617), Color(0x00020617)],
                  stops: [0, .4],
                ),
              ),
            ),
            Center(
              child: SizedBox(
                width: 1280,
                child: Padding(
                  padding: EdgeInsets.symmetric(horizontal: mobile ? 20 : 32),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 768),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 7,
                            ),
                            decoration: BoxDecoration(
                              color: const Color(0x1AFFFFFF),
                              border: Border.all(color: Colors.white24),
                            ),
                            child: const Text(
                              '●  RÉPUBLIQUE DÉMOCRATIQUE DU CONGO',
                              style: TextStyle(
                                fontSize: 9,
                                letterSpacing: 1,
                                color: Colors.white,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ),
                          const SizedBox(height: 20),
                          Text(
                            'Le portail national des normes techniques',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: mobile ? 32 : 58,
                              fontWeight: FontWeight.w900,
                              height: 1.12,
                              letterSpacing: -1,
                            ),
                          ),
                          const SizedBox(height: 20),
                          Text(
                            "Le CNETP centralise la rédaction, l'examen et la publication des normes applicables à la construction, aux infrastructures et aux travaux publics.",
                            style: TextStyle(
                              color: const Color(0xFFF1F5F9),
                              fontSize: mobile ? 14 : 18,
                              height: 1.6,
                            ),
                          ),
                          const SizedBox(height: 28),
                          Wrap(
                            spacing: 12,
                            runSpacing: 12,
                            children: [
                              FilledButton(
                                style: FilledButton.styleFrom(
                                  backgroundColor: AppColors.rdcYellow,
                                  foregroundColor: AppColors.text,
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 22,
                                    vertical: 18,
                                  ),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                ),
                                onPressed: onOpen,
                                child: Text(
                                  loggedIn
                                      ? 'OUVRIR MON ESPACE'
                                      : 'SE CONNECTER',
                                  style: const TextStyle(
                                    fontSize: 10,
                                    letterSpacing: 1.2,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                              ),
                              OutlinedButton(
                                style: OutlinedButton.styleFrom(
                                  backgroundColor: Colors.white10,
                                  foregroundColor: Colors.white,
                                  side: const BorderSide(color: Colors.white38),
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 20,
                                    vertical: 18,
                                  ),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                ),
                                onPressed: onDiscover,
                                child: const Text(
                                  'DÉCOUVRIR LE FONCTIONNEMENT',
                                  style: TextStyle(
                                    fontSize: 10,
                                    letterSpacing: 1,
                                    fontWeight: FontWeight.w800,
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
              ),
            ),
          ],
        ),
      );
    },
  );
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
                  BoxShadow(
                    color: Color(0x1A000000),
                    blurRadius: 24,
                    offset: Offset(0, 8),
                  ),
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
                          padding: const EdgeInsets.symmetric(
                            vertical: 26,
                            horizontal: 16,
                          ),
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
                                  fontSize: 36,
                                  fontWeight: FontWeight.w900,
                                  color: AppColors.rdcBlue,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                _stats[i].$2.toUpperCase(),
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
  const _FeatureGrid({super.key});

  static const _features = [
    (
      Icons.menu_book_outlined,
      'Bibliothèque des normes',
      'Consultez les normes publiées, les projets soumis à consultation et les documents associés.',
    ),
    (
      Icons.edit_note_outlined,
      'Élaboration des normes',
      'Rédigez, relisez et consolidez les projets avec les contributions des experts concernés.',
    ),
    (
      Icons.groups_outlined,
      'Réseau d\'experts',
      'Identifiez les membres, les compétences et les structures associés aux travaux des comités.',
    ),
    (
      Icons.event_outlined,
      'Réunions et décisions',
      'Préparez les réunions, suivez les participants et conservez les décisions prises par les instances.',
    ),
    (
      Icons.gavel_outlined,
      'Relecture juridique',
      'Contrôlez la cohérence des textes et leur conformité avec le cadre juridique applicable.',
    ),
    (
      Icons.fact_check_outlined,
      'Suivi administratif',
      'Suivez les engagements, les présences et les éléments administratifs liés aux travaux des experts.',
    ),
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
                style: TextStyle(
                  fontSize: 14,
                  color: AppColors.muted,
                  height: 1.6,
                ),
              ),
              const SizedBox(height: 28),
              LayoutBuilder(
                builder: (context, constraints) {
                  final cols = constraints.maxWidth >= 900
                      ? 3
                      : constraints.maxWidth >= 560
                      ? 2
                      : 1;
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
                                  color: AppColors.rdcBlue.withValues(
                                    alpha: 0.1,
                                  ),
                                  borderRadius: BorderRadius.circular(11),
                                ),
                                child: Icon(
                                  f.$1,
                                  size: 20,
                                  color: AppColors.rdcBlue,
                                ),
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

class _WorkflowSection extends StatelessWidget {
  const _WorkflowSection({super.key});

  static const items = [
    (
      Icons.description_outlined,
      'Rédaction normative',
      'Les projets de normes sont préparés, relus et consolidés avec les contributions des experts concernés.',
    ),
    (
      Icons.groups_2_outlined,
      'Travail en commissions',
      "Les comités techniques et groupes de travail disposent d'un cadre commun pour organiser leurs échanges.",
    ),
    (
      Icons.verified_outlined,
      'Validation officielle',
      "Les avis, votes et validations accompagnent chaque référentiel jusqu'à son adoption et sa publication.",
    ),
  ];

  @override
  Widget build(BuildContext context) => _HomeSection(
    color: Colors.white,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'UN PROCESSUS PARTAGÉ',
          style: TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w900,
            color: AppColors.brand600,
            letterSpacing: 2,
          ),
        ),
        const SizedBox(height: 10),
        const Text(
          'Un même espace pour élaborer et suivre les normes.',
          style: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.w900,
            color: AppColors.text,
          ),
        ),
        const SizedBox(height: 10),
        const Text(
          'Le portail réunit les experts, les sous-commissions techniques et les institutions autour d’un parcours documenté, de la première version à la publication du texte adopté.',
          style: TextStyle(fontSize: 14, height: 1.6, color: AppColors.muted),
        ),
        const SizedBox(height: 30),
        LayoutBuilder(
          builder: (_, box) {
            final width = box.maxWidth < 680
                ? box.maxWidth
                : (box.maxWidth - 40) / 3;
            return Wrap(
              spacing: 20,
              runSpacing: 20,
              children: [
                for (final item in items)
                  Container(
                    width: width,
                    constraints: const BoxConstraints(minHeight: 210),
                    padding: const EdgeInsets.all(26),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF8FAFC),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 52,
                          height: 52,
                          decoration: BoxDecoration(
                            color: AppColors.brand500.withValues(alpha: .1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Icon(item.$1, color: AppColors.brand600),
                        ),
                        const SizedBox(height: 20),
                        Text(
                          item.$2,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          item.$3,
                          style: const TextStyle(
                            fontSize: 12,
                            height: 1.55,
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
  );
}

class _AudienceSection extends StatelessWidget {
  const _AudienceSection();
  static const items = [
    (
      Icons.engineering_outlined,
      'Experts et ingénieurs',
      'Contribuez à la rédaction, à la relecture et à l’évaluation des projets relevant de votre domaine.',
    ),
    (
      Icons.school_outlined,
      'Universités et recherche',
      'Mettez les travaux scientifiques à la disposition des comités et participez à l’évolution des référentiels.',
    ),
    (
      Icons.apartment_outlined,
      'Entreprises et organismes techniques',
      'Suivez les projets et participez aux consultations sur les normes en préparation.',
    ),
    (
      Icons.account_balance_outlined,
      'Institutions publiques',
      'Pilotez les travaux, instruisez les dossiers et suivez les étapes de validation officielle.',
    ),
  ];

  @override
  Widget build(BuildContext context) => _HomeSection(
    color: Colors.white,
    child: Column(
      children: [
        const Text(
          'Qui peut utiliser la plateforme ?',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.w900,
            color: AppColors.text,
          ),
        ),
        const SizedBox(height: 10),
        const Text(
          'L’accès dépend du rôle et du périmètre de chaque organisation.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 14, color: AppColors.muted),
        ),
        const SizedBox(height: 34),
        LayoutBuilder(
          builder: (_, box) {
            final width = box.maxWidth < 700
                ? box.maxWidth
                : (box.maxWidth - 22) / 2;
            return Wrap(
              spacing: 22,
              runSpacing: 22,
              children: [
                for (final item in items)
                  Container(
                    width: width,
                    padding: const EdgeInsets.all(26),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF8FAFC),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                            color: AppColors.brand500.withValues(alpha: .1),
                            borderRadius: BorderRadius.circular(11),
                          ),
                          child: Icon(item.$1, color: AppColors.brand600),
                        ),
                        const SizedBox(width: 18),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                item.$2,
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              const SizedBox(height: 7),
                              Text(
                                item.$3,
                                style: const TextStyle(
                                  fontSize: 12,
                                  height: 1.55,
                                  color: AppColors.muted,
                                ),
                              ),
                              const SizedBox(height: 12),
                              const Text(
                                '✓ ACCÈS SELON HABILITATION',
                                style: TextStyle(
                                  fontSize: 9,
                                  fontWeight: FontWeight.w800,
                                  letterSpacing: 1,
                                  color: AppColors.brand600,
                                ),
                              ),
                            ],
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
  );
}

class _FinalCta extends StatelessWidget {
  const _FinalCta();
  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    color: const Color(0xFF0A2540),
    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 78),
    child: Column(
      children: [
        const Text(
          'Participez à l’élaboration des normes',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 30,
            fontWeight: FontWeight.w800,
            color: Colors.white,
          ),
        ),
        const SizedBox(height: 14),
        const Text(
          'Rejoignez les travaux du CNE-ITP et contribuez à des référentiels utiles aux professionnels et aux institutions.',
          textAlign: TextAlign.center,
          style: TextStyle(color: Color(0xFFCBD5E1), height: 1.5),
        ),
        const SizedBox(height: 28),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          alignment: WrapAlignment.center,
          children: [
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: AppColors.rdcYellow,
                foregroundColor: AppColors.text,
                padding: const EdgeInsets.symmetric(
                  horizontal: 25,
                  vertical: 18,
                ),
              ),
              onPressed: () => context.go('/login'),
              child: const Text(
                'SE CONNECTER',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1,
                ),
              ),
            ),
            OutlinedButton(
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.white,
                side: const BorderSide(color: Color(0x55FFFFFF)),
                padding: const EdgeInsets.symmetric(
                  horizontal: 25,
                  vertical: 18,
                ),
              ),
              onPressed: () => context.go('/candidature'),
              child: const Text(
                'DÉPOSER UNE CANDIDATURE',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1,
                ),
              ),
            ),
          ],
        ),
      ],
    ),
  );
}

class _Footer extends StatelessWidget {
  const _Footer({required this.onFeatures, required this.onModules});
  final VoidCallback onFeatures, onModules;
  @override
  Widget build(BuildContext context) => Column(
    children: [
      Row(
        children: const [
          Expanded(
            child: ColoredBox(
              color: AppColors.rdcBlue,
              child: SizedBox(height: 5),
            ),
          ),
          Expanded(
            child: ColoredBox(
              color: AppColors.rdcYellow,
              child: SizedBox(height: 5),
            ),
          ),
          Expanded(
            child: ColoredBox(
              color: AppColors.rdcRed,
              child: SizedBox(height: 5),
            ),
          ),
        ],
      ),
      Container(
        width: double.infinity,
        color: const Color(0xFF0A2540),
        padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 40),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1216),
            child: Column(
              children: [
                Wrap(
                  spacing: 55,
                  runSpacing: 28,
                  children: [
                    const _Brand(dark: true),
                    _group('PLATEFORME', [
                      _button("Fonctionnalités de l'Éditeur", onFeatures),
                      _button('Bibliothèque des Normes', onModules),
                      _button(
                        "Conditions d'accréditation",
                        () => context.go('/candidature'),
                      ),
                    ]),
                    _group('RESSOURCES', [
                      const _PortalLink('/about/', 'À propos', dark: true),
                      const _PortalLink(
                        '/contact/',
                        'Assistance technique',
                        dark: true,
                      ),
                      _button(
                        'Accéder à la plateforme',
                        () => context.go('/login'),
                      ),
                    ]),
                    _group('CONTACT', [
                      const Text(
                        'support@cne-itp.cd',
                        style: TextStyle(fontSize: 12, color: Colors.white70),
                      ),
                      const SizedBox(height: 14),
                      const Text(
                        '+243 81 234 56 78',
                        style: TextStyle(fontSize: 12, color: Colors.white70),
                      ),
                    ]),
                  ],
                ),
                const SizedBox(height: 34),
                const Divider(color: Colors.white12),
                const SizedBox(height: 14),
                const Text(
                  '© 2026 République Démocratique du Congo — CNE-ITP. Tous droits réservés.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 11, color: Colors.white54),
                ),
              ],
            ),
          ),
        ),
      ),
    ],
  );

  Widget _group(String title, List<Widget> items) => SizedBox(
    width: 200,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 10,
            color: Colors.white54,
            letterSpacing: 1.3,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: 14),
        ...items,
      ],
    ),
  );
  Widget _button(String text, VoidCallback tap) => TextButton(
    style: TextButton.styleFrom(
      foregroundColor: Colors.white70,
      alignment: Alignment.centerLeft,
    ),
    onPressed: tap,
    child: Text(text, style: const TextStyle(fontSize: 11)),
  );
}

class _HomeSection extends StatelessWidget {
  const _HomeSection({required this.child, required this.color});
  final Widget child;
  final Color color;
  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    color: color,
    padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 72),
    child: Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 1100),
        child: child,
      ),
    ),
  );
}

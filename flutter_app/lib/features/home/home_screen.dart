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
  const _Brand({this.dark = false, this.compact = false});
  final bool dark;
  final bool compact;
  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Container(
        width: compact ? 42 : 46,
        height: compact ? 42 : 46,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(color: const Color(0xFFD4AF37)),
          color: Colors.white,
        ),
        clipBehavior: Clip.antiAlias,
        child: Image.asset('assets/img/logo-cnetp.png', fit: BoxFit.cover),
      ),
      SizedBox(width: compact ? 8 : 10),
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
      SizedBox(width: compact ? 8 : 10),
      Column(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!compact)
            Text(
              'SECRÉTARIAT TECHNIQUE',
              style: TextStyle(
                fontSize: 9,
                fontWeight: FontWeight.w700,
                letterSpacing: .6,
                color: dark ? Colors.white70 : AppColors.muted,
              ),
            ),
          if (compact)
            Text(
              'PORTAIL NATIONAL',
              style: TextStyle(
                fontSize: 9,
                fontWeight: FontWeight.w700,
                letterSpacing: .5,
                color: dark ? Colors.white70 : AppColors.muted,
              ),
            ),
          Text(
            compact ? 'CNE-ITP RDC' : 'PORTAIL CNE-ITP RDC',
            style: TextStyle(
              fontSize: compact ? 13 : 12,
              fontWeight: FontWeight.w900,
              color: dark ? Colors.white : AppColors.accentDark,
            ),
          ),
          if (!compact)
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

  void _showMobileMenu(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      useSafeArea: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (sheetContext) {
        void go(String path) {
          Navigator.of(sheetContext).pop();
          context.go(path);
        }

        Widget external(String path, String label, IconData icon) => Link(
          uri: ApiClient.api(path),
          target: LinkTarget.blank,
          builder: (_, followLink) => ListTile(
            leading: Icon(icon, color: AppColors.rdcBlue),
            title: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            onTap: () {
              Navigator.of(sheetContext).pop();
              followLink?.call();
            },
          ),
        );

        return Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const ListTile(
                title: Text(
                  'Navigation',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
                ),
              ),
              ListTile(
                leading: const Icon(Icons.home_outlined),
                title: const Text('Accueil'),
                onTap: () => go('/'),
              ),
              ListTile(
                leading: const Icon(Icons.login_outlined),
                title: Text(loggedIn ? 'Mon espace' : 'Se connecter'),
                onTap: () => go(loggedIn ? spacePath(space) : '/login'),
              ),
              ListTile(
                leading: const Icon(Icons.how_to_reg_outlined),
                title: const Text('Forum CNE-ITP · Candidature'),
                onTap: () => go('/candidature'),
              ),
              external('/about/', 'À propos', Icons.info_outline),
              external('/contact/', 'Contact', Icons.support_agent_outlined),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, viewport) {
      final compact = viewport.maxWidth < 640;
      return Container(
        color: Colors.white,
        height: compact ? 78 : 80,
        padding: EdgeInsets.symmetric(
          horizontal: compact ? 16 : 20,
          vertical: compact ? 8 : 0,
        ),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1216),
            child: LayoutBuilder(
              builder: (context, box) => Row(
                children: [
                  InkWell(
                    onTap: () => context.go('/'),
                    child: _Brand(compact: compact),
                  ),
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
                      onPressed: () => context.go(
                        loggedIn ? spacePath(space) : '/candidature',
                      ),
                      child: Text(
                        loggedIn ? 'MON ESPACE' : 'FORUM CNE-ITP',
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ] else
                    IconButton(
                      tooltip: 'Ouvrir le menu',
                      icon: Icon(Icons.menu_rounded, size: compact ? 28 : 24),
                      onPressed: () => _showMobileMenu(context),
                    ),
                ],
              ),
            ),
          ),
        ),
      );
    },
  );
}

class _PortalLink extends StatelessWidget {
  const _PortalLink(this.path, this.label);
  final String path, label;
  @override
  Widget build(BuildContext context) => Link(
    uri: ApiClient.api(path),
    target: LinkTarget.blank,
    builder: (_, followLink) => TextButton(
      onPressed: followLink,
      style: TextButton.styleFrom(foregroundColor: AppColors.muted),
      child: Text(
        label,
        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
      ),
    ),
  );
}

class _ActionButton extends StatelessWidget {
  const _ActionButton({
    required this.label,
    required this.onPressed,
    this.secondary = false,
    this.inverse = false,
    this.fullWidth = false,
  });

  final String label;
  final VoidCallback onPressed;
  final bool secondary;
  final bool inverse;
  final bool fullWidth;

  @override
  Widget build(BuildContext context) {
    final style = ButtonStyle(
      minimumSize: WidgetStatePropertyAll(
        Size(fullWidth ? double.infinity : 0, 52),
      ),
      padding: const WidgetStatePropertyAll(
        EdgeInsets.symmetric(horizontal: 22, vertical: 16),
      ),
      shape: WidgetStatePropertyAll(
        RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
    final child = Text(
      label,
      textAlign: TextAlign.center,
      style: const TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w800,
        letterSpacing: .6,
      ),
    );

    if (secondary) {
      return OutlinedButton(
        style: OutlinedButton.styleFrom(
          foregroundColor: inverse ? Colors.white : AppColors.accentDark,
          side: BorderSide(color: inverse ? Colors.white38 : AppColors.border),
          backgroundColor: inverse ? Colors.white10 : Colors.white,
        ).merge(style),
        onPressed: onPressed,
        child: child,
      );
    }

    return FilledButton(
      style: FilledButton.styleFrom(
        backgroundColor: AppColors.rdcYellow,
        foregroundColor: AppColors.text,
      ).merge(style),
      onPressed: onPressed,
      child: child,
    );
  }
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
      final primaryButton = _ActionButton(
        fullWidth: mobile,
        onPressed: onOpen,
        label: loggedIn ? 'OUVRIR MON ESPACE' : 'SE CONNECTER',
      );
      final secondaryButton = _ActionButton(
        fullWidth: mobile,
        secondary: true,
        inverse: true,
        onPressed: onDiscover,
        label: 'DÉCOUVRIR LE FONCTIONNEMENT',
      );
      return SizedBox(
        height: mobile ? 470 : 560,
        width: double.infinity,
        child: Stack(
          fit: StackFit.expand,
          children: [
            Image.asset('assets/img/hero.jpg', fit: BoxFit.cover),
            const ColoredBox(color: Color(0xAD071527)),
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
                                fontSize: 10,
                                letterSpacing: 1,
                                color: Colors.white,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ),
                          SizedBox(height: mobile ? 14 : 20),
                          Text(
                            'Le portail national des normes techniques',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: mobile ? 28 : 58,
                              fontWeight: FontWeight.w900,
                              height: 1.15,
                              letterSpacing: mobile ? -.5 : -1,
                            ),
                          ),
                          SizedBox(height: mobile ? 12 : 20),
                          Text(
                            "La CNE-ITP centralise la rédaction, l'examen et la publication des normes applicables à la construction, aux infrastructures et aux travaux publics.",
                            style: TextStyle(
                              color: const Color(0xFFF1F5F9),
                              fontSize: mobile ? 14 : 18,
                              height: mobile ? 1.5 : 1.6,
                            ),
                          ),
                          SizedBox(height: mobile ? 20 : 28),
                          if (mobile)
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                primaryButton,
                                const SizedBox(height: 12),
                                secondaryButton,
                              ],
                            )
                          else
                            Wrap(
                              spacing: 12,
                              runSpacing: 12,
                              children: [primaryButton, secondaryButton],
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
    (Icons.description_outlined, 'Normes techniques'),
    (Icons.groups_2_outlined, 'Réseau d’experts'),
    (Icons.account_tree_outlined, 'Comités techniques'),
    (Icons.verified_outlined, 'Validation officielle'),
  ];

  @override
  Widget build(BuildContext context) {
    final mobile = MediaQuery.sizeOf(context).width < 640;
    return Container(
      color: Colors.white,
      padding: EdgeInsets.symmetric(horizontal: mobile ? 16 : 28),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1100),
          child: Padding(
            padding: EdgeInsets.symmetric(vertical: mobile ? 20 : 24),
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.border),
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
                          padding: EdgeInsets.symmetric(
                            vertical: mobile ? 22 : 26,
                            horizontal: mobile ? 10 : 16,
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
                                _stats[i].$2.toUpperCase(),
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  fontSize: mobile ? 12 : 13,
                                  height: 1.35,
                                  fontWeight: FontWeight.w800,
                                  color: AppColors.text,
                                ),
                              ),
                              const SizedBox(height: 10),
                              Icon(
                                _stats[i].$1,
                                size: mobile ? 28 : 30,
                                color: AppColors.rdcBlue,
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
    final mobile = MediaQuery.sizeOf(context).width < 640;
    return Container(
      color: Colors.white,
      padding: EdgeInsets.symmetric(horizontal: mobile ? 20 : 28),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1100),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Des outils pour chaque étape',
                style: TextStyle(
                  fontSize: mobile ? 26 : 24,
                  fontWeight: FontWeight.w800,
                  color: AppColors.text,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Les modules réunissent les ressources documentaires, les échanges de travail et le suivi administratif nécessaires à la conduite des travaux.',
                style: TextStyle(
                  fontSize: mobile ? 15 : 14,
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
                  final cards = [
                    for (final f in _features)
                      Container(
                        width: mobile ? 300 : w,
                        padding: EdgeInsets.all(mobile ? 20 : 22),
                        decoration: BoxDecoration(
                          color: AppColors.surfaceAlt,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: AppColors.border),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              width: mobile ? 46 : 42,
                              height: mobile ? 46 : 42,
                              decoration: BoxDecoration(
                                color: AppColors.rdcBlue.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(11),
                              ),
                              child: Icon(
                                f.$1,
                                size: mobile ? 22 : 20,
                                color: AppColors.rdcBlue,
                              ),
                            ),
                            const SizedBox(height: 14),
                            Text(
                              f.$2,
                              style: TextStyle(
                                fontSize: mobile ? 17 : 14,
                                fontWeight: FontWeight.w800,
                                color: AppColors.text,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              f.$3,
                              style: TextStyle(
                                fontSize: mobile ? 14 : 12,
                                height: 1.5,
                                color: AppColors.muted,
                              ),
                            ),
                          ],
                        ),
                      ),
                  ];
                  if (mobile) {
                    return SizedBox(
                      height: 230,
                      child: ListView.separated(
                        scrollDirection: Axis.horizontal,
                        itemCount: cards.length,
                        separatorBuilder: (_, _) => const SizedBox(width: 16),
                        itemBuilder: (_, index) => cards[index],
                      ),
                    );
                  }
                  return Wrap(spacing: gap, runSpacing: gap, children: cards);
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
        Text(
          'UN PROCESSUS PARTAGÉ',
          style: TextStyle(
            fontSize: MediaQuery.sizeOf(context).width < 640 ? 11 : 10,
            fontWeight: FontWeight.w900,
            color: AppColors.brand600,
            letterSpacing: 2,
          ),
        ),
        const SizedBox(height: 10),
        Text(
          'Un même espace pour élaborer et suivre les normes.',
          style: TextStyle(
            fontSize: MediaQuery.sizeOf(context).width < 640 ? 26 : 28,
            fontWeight: FontWeight.w900,
            color: AppColors.text,
          ),
        ),
        const SizedBox(height: 10),
        Text(
          'Le portail réunit les experts, les sous-commissions techniques et les institutions autour d’un parcours documenté, de la première version à la publication du texte adopté.',
          style: TextStyle(
            fontSize: MediaQuery.sizeOf(context).width < 640 ? 15 : 14,
            height: 1.6,
            color: AppColors.muted,
          ),
        ),
        const SizedBox(height: 30),
        LayoutBuilder(
          builder: (_, box) {
            final mobile = box.maxWidth < 680;
            final width = mobile ? box.maxWidth : (box.maxWidth - 40) / 3;
            final cards = [
              for (final item in items)
                Container(
                  width: mobile ? 300 : width,
                  constraints: BoxConstraints(minHeight: mobile ? 0 : 210),
                  padding: EdgeInsets.all(mobile ? 20 : 26),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceAlt,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.border),
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
                        style: TextStyle(
                          fontSize: mobile ? 18 : 16,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        item.$3,
                        style: TextStyle(
                          fontSize: mobile ? 14 : 12,
                          height: 1.55,
                          color: AppColors.muted,
                        ),
                      ),
                    ],
                  ),
                ),
            ];
            if (mobile) {
              return SizedBox(
                height: 260,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: cards.length,
                  separatorBuilder: (_, _) => const SizedBox(width: 16),
                  itemBuilder: (_, index) => cards[index],
                ),
              );
            }
            return Wrap(spacing: 20, runSpacing: 20, children: cards);
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
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Qui peut utiliser la plateforme ?',
          style: TextStyle(
            fontSize: MediaQuery.sizeOf(context).width < 640 ? 26 : 28,
            fontWeight: FontWeight.w900,
            color: AppColors.text,
          ),
        ),
        const SizedBox(height: 10),
        Text(
          'L’accès dépend du rôle et du périmètre de chaque organisation.',
          style: TextStyle(
            fontSize: MediaQuery.sizeOf(context).width < 640 ? 15 : 14,
            color: AppColors.muted,
          ),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: AppColors.blueSoft,
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Text(
            'ACCÈS SELON HABILITATION',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              letterSpacing: .5,
              color: AppColors.brand600,
            ),
          ),
        ),
        const SizedBox(height: 34),
        LayoutBuilder(
          builder: (_, box) {
            final mobile = box.maxWidth < 700;
            final width = mobile ? box.maxWidth : (box.maxWidth - 22) / 2;
            final cards = [
              for (final item in items)
                Container(
                  width: mobile ? 300 : width,
                  padding: EdgeInsets.all(mobile ? 20 : 26),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceAlt,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 46,
                        height: 46,
                        decoration: BoxDecoration(
                          color: AppColors.brand500.withValues(alpha: .1),
                          borderRadius: BorderRadius.circular(11),
                        ),
                        child: Icon(item.$1, color: AppColors.brand600),
                      ),
                      SizedBox(height: mobile ? 16 : 18),
                      Text(
                        item.$2,
                        style: TextStyle(
                          fontSize: mobile ? 17 : 16,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        item.$3,
                        style: TextStyle(
                          fontSize: mobile ? 14 : 12,
                          height: 1.55,
                          color: AppColors.muted,
                        ),
                      ),
                    ],
                  ),
                ),
            ];
            if (mobile) {
              return SizedBox(
                height: 250,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: cards.length,
                  separatorBuilder: (_, _) => const SizedBox(width: 16),
                  itemBuilder: (_, index) => cards[index],
                ),
              );
            }
            return Wrap(spacing: 22, runSpacing: 22, children: cards);
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
    padding: EdgeInsets.symmetric(
      horizontal: 20,
      vertical: MediaQuery.sizeOf(context).width < 640 ? 56 : 78,
    ),
    child: Column(
      children: [
        Text(
          'Participez à l’élaboration des normes',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: MediaQuery.sizeOf(context).width < 640 ? 28 : 30,
            fontWeight: FontWeight.w800,
            color: Colors.white,
          ),
        ),
        const SizedBox(height: 14),
        Text(
          'Rejoignez les travaux du CNE-ITP et contribuez à des référentiels utiles aux professionnels et aux institutions.',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: MediaQuery.sizeOf(context).width < 640 ? 15 : 14,
            color: const Color(0xFFCBD5E1),
            height: 1.5,
          ),
        ),
        const SizedBox(height: 28),
        if (MediaQuery.sizeOf(context).width < 640) ...[
          _ActionButton(
            label: 'SE CONNECTER',
            fullWidth: true,
            onPressed: () => context.go('/login'),
          ),
          const SizedBox(height: 12),
          _ActionButton(
            label: 'DÉPOSER UNE CANDIDATURE',
            secondary: true,
            inverse: true,
            fullWidth: true,
            onPressed: () => context.go('/candidature'),
          ),
        ] else
          Wrap(
            spacing: 12,
            runSpacing: 12,
            alignment: WrapAlignment.center,
            children: [
              _ActionButton(
                label: 'SE CONNECTER',
                onPressed: () => context.go('/login'),
              ),
              _ActionButton(
                label: 'DÉPOSER UNE CANDIDATURE',
                secondary: true,
                inverse: true,
                onPressed: () => context.go('/candidature'),
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
  Widget build(BuildContext context) {
    final mobile = MediaQuery.sizeOf(context).width < 640;
    final platformLinks = [
      _FooterLink('Découvrir le processus', onTap: onFeatures),
      _FooterLink('Voir les modules', onTap: onModules),
      _FooterLink(
        "Conditions d'accréditation",
        onTap: () => context.go('/candidature'),
      ),
    ];
    final resourceLinks = [
      _FooterLink('À propos', uri: ApiClient.api('/about/')),
      _FooterLink('Assistance technique', uri: ApiClient.api('/contact/')),
      _FooterLink(
        'Accéder à la plateforme',
        onTap: () => context.go('/login'),
      ),
    ];
    final contactLinks = [
      _FooterLink(
        'support@cne-itp.cd',
        icon: Icons.mail_outline_rounded,
        uri: Uri.parse('mailto:support@cne-itp.cd'),
      ),
    ];
    const tagline = Text(
      'Portail national d’élaboration et de publication des normes '
      'techniques des infrastructures et travaux publics.',
      style: TextStyle(fontSize: 13, height: 1.5, color: Colors.white60),
    );

    return Column(
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
          padding: EdgeInsets.fromLTRB(
            mobile ? 20 : 28,
            mobile ? 36 : 44,
            mobile ? 20 : 28,
            mobile ? 24 : 28,
          ),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1216),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (mobile) ...[
                    const _Brand(dark: true, compact: true),
                    const SizedBox(height: 14),
                    tagline,
                    const SizedBox(height: 28),
                    // Les autres liens sont déjà dans le menu mobile.
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: _group('PLATEFORME', platformLinks.take(2)),
                        ),
                        const SizedBox(width: 16),
                        Expanded(child: _group('CONTACT', contactLinks)),
                      ],
                    ),
                  ] else
                    Wrap(
                      spacing: 55,
                      runSpacing: 28,
                      children: [
                        const SizedBox(
                          width: 300,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              _Brand(dark: true),
                              SizedBox(height: 14),
                              tagline,
                            ],
                          ),
                        ),
                        SizedBox(
                          width: 200,
                          child: _group('PLATEFORME', platformLinks),
                        ),
                        SizedBox(
                          width: 200,
                          child: _group('RESSOURCES', resourceLinks),
                        ),
                        SizedBox(
                          width: 200,
                          child: _group('CONTACT', contactLinks),
                        ),
                      ],
                    ),
                  if (!mobile) ...[
                    const SizedBox(height: 34),
                    const Divider(color: Colors.white12, height: 1),
                    const SizedBox(height: 18),
                    const SizedBox(
                      width: double.infinity,
                      child: Text(
                        '© 2026 République Démocratique du Congo — CNE-ITP.\n'
                        'Tous droits réservés.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 12,
                          height: 1.5,
                          color: Colors.white54,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _group(String title, Iterable<Widget> items) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        title,
        style: const TextStyle(
          fontSize: 11,
          color: Colors.white54,
          letterSpacing: 1.3,
          fontWeight: FontWeight.w800,
        ),
      ),
      const SizedBox(height: 8),
      ...items,
    ],
  );
}

class _FooterLink extends StatelessWidget {
  const _FooterLink(this.label, {this.onTap, this.uri, this.icon});
  final String label;
  final VoidCallback? onTap;
  final Uri? uri;
  final IconData? icon;

  Widget _content(VoidCallback? tap) => InkWell(
    onTap: tap,
    borderRadius: BorderRadius.circular(6),
    child: ConstrainedBox(
      constraints: const BoxConstraints(minHeight: 40),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null) ...[
              Icon(icon, size: 16, color: AppColors.rdcBlue),
              const SizedBox(width: 8),
            ],
            Flexible(
              child: Text(
                label,
                style: const TextStyle(
                  fontSize: 13.5,
                  height: 1.35,
                  color: Color(0xFFE2E8F0),
                ),
              ),
            ),
          ],
        ),
      ),
    ),
  );

  @override
  Widget build(BuildContext context) {
    final target = uri;
    if (target == null) return _content(onTap);
    return Link(
      uri: target,
      target: LinkTarget.blank,
      builder: (_, followLink) => _content(followLink),
    );
  }
}

class _HomeSection extends StatelessWidget {
  const _HomeSection({required this.child, required this.color});
  final Widget child;
  final Color color;
  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    color: color,
    padding: EdgeInsets.symmetric(
      horizontal: MediaQuery.sizeOf(context).width < 640 ? 20 : 28,
      vertical: MediaQuery.sizeOf(context).width < 640 ? 48 : 72,
    ),
    child: Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 1100),
        child: child,
      ),
    ),
  );
}

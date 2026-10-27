import 'package:flutter/material.dart';

import '../../theme/copil_theme.dart';

class ScGroup {
  const ScGroup({
    required this.code,
    required this.title,
    required this.memberCount,
    required this.experts,
    this.id,
  });

  final String code;
  final int? id;
  final String title;
  final int memberCount;
  final List<String> experts;
}

class CopilProfile {
  const CopilProfile({
    this.fullName = '',
    this.role = '',
    this.structure = '',
    this.status = '',
    this.appointmentDate = '',
  });

  final String fullName;
  final String role;
  final String structure;
  final String status;
  final String appointmentDate;
}

/// Données réelles de la version d'organisation courante (base locale).
/// Source : Organe.Type.SC + AffectationSousCommission (MIGRATED/REVIEW).
const demoScGroups = <ScGroup>[
  ScGroup(
    code: 'SC-BAT',
    title: 'Bâtiments Courants & Spéciaux (SC-BAT)',
    memberCount: 28,
    experts: [
      'Kizito MATABARO KIZITO',
      'Gradi BANINGIME KEBWIJINA',
      'FREDERIC BAWILU MAFUTA',
      'Israël-Tshany BENDERA MUSANGANI',
      'Joseph Bamenikio',
      'Belinda Betuku Nkoy',
      'Romain Bussa Mbule',
      'Zatus KIAKU',
      'Nkashamba Kazadi N\'as',
      'jérôme Kazambu',
      'Patrick Kibangu Mampuya',
      'Mymmon Kilunga Nsenga',
      'Yannick Kindimbu Matondo',
      'Christian Kyalumba Makindu',
      'Leon Levo Nakanza',
      'WIREN MONDU KITSHIAKA',
      'John MUTUMBI',
      'Gisele Nsiangani Miezi',
      'Corneille Muntenge Iboy',
      'Jean Marie N\'SAPU KUMWAMBA',
      'Rosine NGALULA KALANDA',
      'Joseph Nono NKIERE NANA',
      'Jules NKOMBWA KABOFI',
      'Deborah Omoyi pongombo',
      'Alexandre Tshiamala Wa Tshiamala',
      'Richard VIBILA MBIVANGA',
      'CHRISPIN ZIGABE',
      'eddie masamba',
    ],
  ),
  ScGroup(
    code: 'SC-ENV',
    title: 'Environnement, Santé & Sécurité (SC-ENV)',
    memberCount: 5,
    experts: [
      'Guycele Malabi Mpioko',
      'Péguy Malu Ngalamulume',
      'ChrisBardol Ngindu Wa ngindu',
      'olivier ROGHO PASHO-LAWATA',
      'Willy VALE MANGA',
    ],
  ),
  ScGroup(
    code: 'SC-GF',
    title: 'Géotechnique & Fondations (SC-GF)',
    memberCount: 9,
    experts: [
      'RUDY ALONDA KYATANGALWA',
      'Dieudonné Bambu Ndombasi',
      'GABAIN MULOWAYI',
      'GABAIN MULOWAYI Kankolongo',
      'Christian Mafolo Mfumu',
      'Chico Mwadi',
      'Samuel Ndengani Monzele',
      'ed masamba',
      'exaucer tefala',
    ],
  ),
  ScGroup(
    code: 'SC-IT',
    title: 'Infrastructures de Transport (SC-IT)',
    memberCount: 28,
    experts: [
      'Lucien BATULI NKASANGALI',
      'Jean de Dieu BOBO KOEBONI',
      'Serge Banza',
      'Jean Bosco Bifulu Malele',
      'Christian Esiki Yolo',
      'Papy Fataki Lukumu',
      'Freddy KAZADI KAMUANGA',
      'Fabien LASANGA NDASA',
      'AMBROISE LUKOKI LUA MBOZI',
      'Flory MAMPIA NSANGA',
      'CHARLES MIKWARI NGAL',
      'CHRISTIAN MUNIAMPALA LESUYA',
      'Emmanuel MWILA KIBWE',
      'Winner Mapanda Balinga',
      'Michel Miseka Mubake',
      'Anatol Mpungu Mpungu',
      'Estimé Mambula Wa Kanyinda Mukandila',
      'Vital Musungaie Tshitundu',
      'Christ NSIMBULU MASSAMBA',
      'ANDRE TAYEYE NTELA',
      'Jean Paul NYEMBO TAMPAKANYA',
      'Simon Barnabas PAKU MATONDO',
      'THEONESTE RUVIRI KANANI',
      'Enock SANGANA MALONDA WASOLUA',
      'TSHISE TSHISEKEDI KALADI',
      'Yves UTUBULA NZUNDU',
      'Roger Vibila Kandu Mayi',
      'Josué Wandje Owamba',
    ],
  ),
  ScGroup(
    code: 'SC-OH',
    title: 'Ouvrages Hydrauliques (SC-OH)',
    memberCount: 19,
    experts: [
      'Pierre Asabi Kwagba',
      'Glody Baang’osema Basele',
      'Pierrot ILUNGA',
      'Papy KABADI LELO ODIMBA',
      'Daniel KAZADI CIBUMBU',
      'Gabriel Zaatcha KAZADI MUHOLA LASER',
      'Désire Loole Babongola',
      'Josaphat MUKALA MULUMBA',
      'Flory Mbuyi',
      'René Mpuru Mazembe',
      'Meschack Mukendi',
      'Parfait Mutambay Muaba',
      'Luc Mwamba Miteo',
      'Azarias Fiston Mwatoike Ligbakelo',
      'Yves Ngoma Muzola',
      'Joseph Nkayilu Lumbanzu',
      'olivier ROGHO PASHO-LAWATA',
      'Xavier SAKA-SAKA NGALA',
      'Steve TSHITENDE wa TSHITENDE',
    ],
  ),
  ScGroup(
    code: 'SC-SOCLE',
    title: 'Matériaux & Essais / Socle Commun (SC-SOCLE)',
    memberCount: 12,
    experts: [
      'CHRISTIAN ACIZA',
      'Jean Marie Bena Diakiese',
      'Judith Bwalelo Wabenia',
      'Patrick Ilho Kituba',
      'PAPY KANGUDI',
      'Daniel KIBIKONDA LUIZI',
      'Dimitri KINDUNDU MUKOMBO',
      'Doris Kayamba Kilungu',
      'Pires LISINGO TOFOFA',
      'GUY LAROCHE NGWAMA PERO',
      'Annie Ntumba Lusamba',
      'Jeancy Tshiamala Kumwamba',
    ],
  ),
  ScGroup(
    code: 'SC-VRD',
    title:
        'Réseaux Divers (VRD), Équipements & Fluides (Proposition d\'expert)',
    memberCount: 0,
    experts: [],
  ),
];

class ConsoleContent extends StatelessWidget {
  const ConsoleContent({
    super.key,
    this.scs = const [],
    this.counts = const {},
    this.profile = const CopilProfile(),
    this.onInstruction,
    this.onSubcommission,
    this.onManageExperts,
    this.onFreeze,
    this.platformLocked = false,
  });

  final List<ScGroup> scs;
  final Map<String, int> counts;
  final CopilProfile profile;
  final VoidCallback? onInstruction;
  final ValueChanged<ScGroup>? onSubcommission;
  final VoidCallback? onManageExperts;
  final VoidCallback? onFreeze;
  final bool platformLocked;

  List<ScGroup> get _groups => scs;

  @override
  Widget build(BuildContext context) {
    final groups = _groups;
    final p = CopilTheme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _Hero(profile: profile),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 32, 16, 64),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const _ConsoleHeading(),
              const SizedBox(height: 16),
              _KpiRow(counts: counts),
              const SizedBox(height: 26),
              Wrap(
                alignment: WrapAlignment.spaceBetween,
                crossAxisAlignment: WrapCrossAlignment.center,
                spacing: 12,
                runSpacing: 12,
                children: [
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.hub_outlined, size: 15, color: p.subtle),
                      const SizedBox(width: 8),
                      Text(
                        'LES ${groups.length} SOUS-COMMISSIONS TECHNIQUES',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1.4,
                          color: p.muted,
                        ),
                      ),
                    ],
                  ),
                  _PrimaryButton(
                    label: 'Donner une instruction',
                    onTap: onInstruction ?? () {},
                  ),
                ],
              ),
              const SizedBox(height: 12),
              LayoutBuilder(
                builder: (context, constraints) {
                  final viewport = MediaQuery.sizeOf(context).width;
                  final columns = viewport >= 1280
                      ? 3
                      : viewport >= 640
                      ? 2
                      : 1;
                  const gap = 12.0;
                  final width =
                      (constraints.maxWidth - gap * (columns - 1)) / columns;
                  return Wrap(
                    spacing: gap,
                    runSpacing: gap,
                    children: [
                      for (final group in groups)
                        SizedBox(
                          width: width,
                          child: _ScCard(
                            group: group,
                            onTap: onSubcommission == null
                                ? null
                                : () => onSubcommission!(group),
                          ),
                        ),
                    ],
                  );
                },
              ),
              if (groups.isEmpty)
                Padding(
                  padding: const EdgeInsets.all(32),
                  child: Text(
                    "La structure des sous-commissions n'est pas encore disponible.",
                    textAlign: TextAlign.center,
                    style: TextStyle(color: p.muted),
                  ),
                ),
              if (onManageExperts != null) ...[
                const SizedBox(height: 24),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: p.card,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: p.border),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'GESTION DES ACCÈS EXPERTS',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                          color: p.subtle,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Consultez la sous-commission de chaque expert et gérez son accès à la plateforme.',
                        style: TextStyle(fontSize: 12, color: p.subtle),
                      ),
                      const SizedBox(height: 12),
                      OutlinedButton.icon(
                        onPressed: onManageExperts,
                        icon: const Icon(Icons.people_outline, size: 14),
                        label: const Text('Gérer les experts'),
                      ),
                    ],
                  ),
                ),
              ],
              if (onFreeze != null) ...[
                const SizedBox(height: 32),
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: p.blueSoft,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: p.border),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Verrouillage de la plateforme',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w800,
                          color: p.title,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        platformLocked
                            ? 'Plateforme verrouillée. Les actions opérationnelles sont suspendues.'
                            : 'Cette action suspend les opérations techniques et le cadrage sur toute la plateforme.',
                        style: TextStyle(fontSize: 12, color: p.muted),
                      ),
                      const SizedBox(height: 12),
                      OutlinedButton(
                        onPressed: onFreeze,
                        child: Text(
                          platformLocked ? 'Déverrouiller' : 'Verrouiller',
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

class _ConsoleHeading extends StatelessWidget {
  const _ConsoleHeading();

  @override
  Widget build(BuildContext context) {
    final p = CopilTheme.of(context);
    return Row(
      children: [
        Icon(Icons.dashboard_outlined, size: 16, color: p.blue),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            'CONSOLE GLOBALE DE SUPERVISION',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.6,
              color: p.blue,
            ),
          ),
        ),
      ],
    );
  }
}

class _Hero extends StatelessWidget {
  const _Hero({required this.profile});

  final CopilProfile profile;

  @override
  Widget build(BuildContext context) {
    final p = CopilTheme.of(context);
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 20),
      decoration: BoxDecoration(
        color: p.bg,
        border: Border(bottom: BorderSide(color: p.border)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  profile.fullName,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    color: p.title,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  profile.role,
                  style: TextStyle(fontSize: 13, color: p.muted),
                ),
                const SizedBox(height: 6),
                Text(
                  profile.structure,
                  style: TextStyle(fontSize: 11.5, color: p.subtle),
                ),
                if (profile.appointmentDate.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    'Nommé le ${profile.appointmentDate}',
                    style: TextStyle(fontSize: 12, color: p.subtle),
                  ),
                ],
              ],
            ),
          ),
          Text(
            profile.status,
            style: TextStyle(fontSize: 11.5, color: p.subtle),
          ),
        ],
      ),
    );
  }
}

class _KpiRow extends StatelessWidget {
  const _KpiRow({required this.counts});
  final Map<String, int> counts;

  @override
  Widget build(BuildContext context) {
    final p = CopilTheme.of(context);
    final items = [
      _KpiData(
        '${counts['sous_commissions'] ?? 0}',
        'SOUS-COMMISSIONS',
        p.blue,
      ),
      _KpiData('${counts['experts'] ?? 0}', 'EXPERTS', p.success),
      _KpiData('${counts['a_examiner'] ?? 0}', 'À EXAMINER', p.warning),
      _KpiData(
        '${counts['normes_travaillees'] ?? 0}',
        'NORMES TRAVAILLÉES',
        p.danger,
      ),
    ];
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = MediaQuery.sizeOf(context).width >= 640 ? 4 : 2;
        const gap = 12.0;
        final width = (constraints.maxWidth - gap * (columns - 1)) / columns;
        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: [
            for (final item in items)
              SizedBox(
                width: width,
                child: _KpiCard(data: item),
              ),
          ],
        );
      },
    );
  }
}

class _KpiData {
  const _KpiData(this.value, this.label, this.color);
  final String value;
  final String label;
  final Color color;
}

class _KpiCard extends StatelessWidget {
  const _KpiCard({required this.data});
  final _KpiData data;

  @override
  Widget build(BuildContext context) {
    final p = CopilTheme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: data.color.withValues(alpha: p.isDark ? 0.08 : 0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: data.color.withValues(alpha: 0.2)),
      ),
      child: Column(
        children: [
          Text(
            data.value,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w900,
              height: 1,
              color: data.color,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            data.label,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 9.5,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.5,
              color: p.muted,
            ),
          ),
        ],
      ),
    );
  }
}

class _ScCard extends StatelessWidget {
  const _ScCard({required this.group, this.onTap});
  final ScGroup group;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final p = CopilTheme.of(context);
    return Material(
      color: p.card,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: p.card,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: p.border),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: p.blueSoft,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: p.blue.withValues(alpha: 0.25)),
                    ),
                    child: Text(
                      group.code,
                      style: TextStyle(
                        fontSize: 9,
                        fontWeight: FontWeight.w900,
                        color: p.blue,
                      ),
                    ),
                  ),
                  const Spacer(),
                  Text(
                    '${group.memberCount} experts',
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                      color: p.subtle,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              SizedBox(
                height: 32,
                child: Text(
                  group.title,
                  maxLines: 2,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    height: 1.3,
                    color: p.title,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Divider(height: 1, color: p.border),
              const SizedBox(height: 10),
              SizedBox(
                height: group.experts.isEmpty ? 16 : 128,
                child: group.experts.isEmpty
                    ? Text(
                        'Aucun expert classé dans cette sous-commission.',
                        style: TextStyle(
                          fontSize: 10,
                          fontStyle: FontStyle.italic,
                          color: p.subtle,
                        ),
                      )
                    : SingleChildScrollView(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            for (final expert in group.experts)
                              Padding(
                                padding: const EdgeInsets.only(bottom: 6),
                                child: Row(
                                  children: [
                                    Container(
                                      width: 5,
                                      height: 5,
                                      decoration: BoxDecoration(
                                        color: p.success,
                                        shape: BoxShape.circle,
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Text(
                                        expert,
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: TextStyle(
                                          fontSize: 10,
                                          color: p.muted,
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
            ],
          ),
        ),
      ),
    );
  }
}

class _PrimaryButton extends StatelessWidget {
  const _PrimaryButton({required this.label, required this.onTap});
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: const Color(0xFF2563EB),
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(9),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          child: Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: Colors.white,
            ),
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import '../../../../theme/app_colors.dart';

class ScGroup {
  const ScGroup({
    required this.code,
    required this.title,
    required this.memberCount,
    required this.experts,
  });

  final String code;
  final String title;
  final int memberCount;
  final List<String> experts;
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
    title: 'Réseaux Divers (VRD), Équipements & Fluides (Proposition d\'expert)',
    memberCount: 0,
    experts: [],
  ),
];

class ConsoleContent extends StatelessWidget {
  const ConsoleContent({super.key, this.scs = const [], this.counts = const {}});

  final List<ScGroup> scs;
  final Map<String, int> counts;

  List<ScGroup> get _groups => scs.isNotEmpty ? scs : demoScGroups;

  @override
  Widget build(BuildContext context) {
    final groups = _groups;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const _Hero(),
        Padding(
          padding: const EdgeInsets.fromLTRB(28, 22, 28, 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const _ConsoleHeading(),
              const SizedBox(height: 16),
              _KpiRow(counts: counts),
              const SizedBox(height: 26),
              Row(
                children: [
                  const Icon(Icons.hub_outlined, size: 15, color: AppColors.subtle),
                  const SizedBox(width: 8),
                  Text(
                    'LES ${groups.length} SOUS-COMMISSIONS TECHNIQUES',
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1.4,
                      color: AppColors.muted,
                    ),
                  ),
                  const Spacer(),
                  _PrimaryButton(label: 'Donner une Instruction', onTap: () {}),
                ],
              ),
              const SizedBox(height: 12),
              LayoutBuilder(
                builder: (context, constraints) {
                  final columns = constraints.maxWidth >= 1080
                      ? 3
                      : constraints.maxWidth >= 700
                          ? 2
                          : 1;
                  const gap = 14.0;
                  final width =
                      (constraints.maxWidth - gap * (columns - 1)) / columns;
                  return Wrap(
                    spacing: gap,
                    runSpacing: gap,
                    children: [
                      for (final group in groups)
                        SizedBox(
                          width: width,
                          child: _ScCard(group: group),
                        ),
                    ],
                  );
                },
              ),
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
    return Row(
      children: const [
        Icon(Icons.settings_suggest_outlined, size: 17, color: AppColors.subtle),
        SizedBox(width: 8),
        Text(
          'CONSOLE GLOBALE DE SUPERVISION',
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.6,
            color: AppColors.muted,
          ),
        ),
      ],
    );
  }
}

class _Hero extends StatelessWidget {
  const _Hero();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(28, 20, 28, 20),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(bottom: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text(
                  'eddie masamba',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    color: AppColors.text,
                  ),
                ),
                SizedBox(height: 3),
                Text(
                  'Bureau Directoire · Président',
                  style: TextStyle(fontSize: 13, color: AppColors.muted),
                ),
                SizedBox(height: 6),
                Text(
                  'Default Structure (DS)',
                  style: TextStyle(fontSize: 11.5, color: AppColors.subtle),
                ),
                SizedBox(height: 3),
                Text(
                  'Nommé le 30/05/2026',
                  style: TextStyle(fontSize: 11.5, color: AppColors.subtle),
                ),
              ],
            ),
          ),
          const Text(
            'Actif',
            style: TextStyle(fontSize: 11.5, color: AppColors.subtle),
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
    final items = [
      _KpiData('${counts['sous_commissions'] ?? 0}', 'SOUS-COMMISSIONS', AppColors.rdcBlue),
      _KpiData('${counts['experts'] ?? 0}', 'EXPERTS', AppColors.success),
      _KpiData('${counts['a_examiner'] ?? 0}', 'À EXAMINER', AppColors.warning),
      _KpiData('${counts['normes_travaillees'] ?? 0}', 'NORMES TRAVAILLÉES', AppColors.danger),
    ];
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 760 ? 4 : 2;
        const gap = 12.0;
        final width = (constraints.maxWidth - gap * (columns - 1)) / columns;
        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: [
            for (final item in items)
              SizedBox(width: width, child: _KpiCard(data: item)),
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
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 12),
      decoration: BoxDecoration(
        color: data.color.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: data.color.withValues(alpha: 0.2)),
      ),
      child: Column(
        children: [
          Text(
            data.value,
            style: TextStyle(
              fontSize: 27,
              fontWeight: FontWeight.w900,
              height: 1,
              color: data.color,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            data.label,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 9.5,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.5,
              color: AppColors.muted,
            ),
          ),
        ],
      ),
    );
  }
}

class _ScCard extends StatelessWidget {
  const _ScCard({required this.group});
  final ScGroup group;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.rdcBlue.withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(
                    color: AppColors.rdcBlue.withValues(alpha: 0.2),
                  ),
                ),
                child: Text(
                  group.code,
                  style: const TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w900,
                    color: AppColors.rdcBlue,
                  ),
                ),
              ),
              const Spacer(),
              Text(
                '${group.memberCount} experts',
                style: const TextStyle(
                  fontSize: 9,
                  fontWeight: FontWeight.w700,
                  color: AppColors.subtle,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            group.title,
            maxLines: 2,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              height: 1.3,
              color: AppColors.text,
            ),
          ),
          const SizedBox(height: 12),
          const Divider(height: 1, color: Color(0xFFF1F5F9)),
          const SizedBox(height: 10),
          SizedBox(
            height: 104,
            child: group.experts.isEmpty
                ? const Text(
                    'Aucun expert classé dans cette sous-commission.',
                    style: TextStyle(
                      fontSize: 10,
                      fontStyle: FontStyle.italic,
                      color: AppColors.subtle,
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
                                  decoration: const BoxDecoration(
                                    color: AppColors.success,
                                    shape: BoxShape.circle,
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    expert,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(
                                      fontSize: 10,
                                      color: AppColors.muted,
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
      color: AppColors.accent,
      borderRadius: BorderRadius.circular(9),
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

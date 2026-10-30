import 'package:flutter/material.dart';
import '../../../theme/app_colors.dart';

/// Tableau de bord CTC — reproduit `dashboard_module.html` (design "premium").
class CtcDashboardView extends StatelessWidget {
  const CtcDashboardView({
    super.key,
    required this.poleLabel,
    this.subRole,
    this.canAdminSystem = false,
    this.blockedPolitical = false,
    required this.counts,
    required this.dossiers,
    required this.assignations,
    this.stageRows = const [],
    this.groupNormRows = const [],
    this.onOpenAssignations,
    this.onOpenDossiers,
  });

  final String poleLabel;
  final String? subRole;
  final bool canAdminSystem;
  final bool blockedPolitical;
  final Map<String, int> counts;
  final List<Map<String, dynamic>> dossiers;
  final List<Map<String, dynamic>> assignations;
  final List<Map<String, dynamic>> stageRows;
  final List<Map<String, dynamic>> groupNormRows;
  final VoidCallback? onOpenAssignations;
  final VoidCallback? onOpenDossiers;

  int _c(String k) => counts[k] ?? 0;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 900;
        return SingleChildScrollView(
          child: Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topRight,
                end: Alignment.bottomLeft,
                colors: [Color(0xFFF2F9FF), AppColors.page, AppColors.page],
              ),
            ),
            padding: EdgeInsets.all(compact ? 16 : 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Secrétariat technique · $poleLabel',
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 1.1,
                              color: AppColors.rdcBlue,
                            ),
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            'Tableau de bord',
                            style: TextStyle(
                              fontSize: 30,
                              fontWeight: FontWeight.w800,
                              letterSpacing: -0.5,
                              color: AppColors.text,
                            ),
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            'Dossiers, assignations et suivi de votre poste.',
                            style: TextStyle(
                              fontSize: 13,
                              color: AppColors.muted,
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (!compact && onOpenAssignations != null)
                      _AccentButton(
                        label: 'Mes assignations',
                        onTap: onOpenAssignations!,
                      ),
                  ],
                ),
                const SizedBox(height: 20),
                if (compact && onOpenAssignations != null) ...[
                  _AccentButton(
                    label: 'Mes assignations',
                    onTap: onOpenAssignations!,
                  ),
                  const SizedBox(height: 20),
                ],
                _Card(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Mon rôle et mes droits',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          color: AppColors.text,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        poleLabel,
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: AppColors.rdcBlue,
                        ),
                      ),
                      if (subRole != null && subRole!.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Text(
                          'Sous-rôle « $subRole »',
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppColors.muted,
                          ),
                        ),
                      ],
                      if (canAdminSystem || blockedPolitical) ...[
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            if (canAdminSystem)
                              const Chip(
                                label: Text('Administration système'),
                                backgroundColor: Color(0xFFE3F6EC),
                                side: BorderSide.none,
                                labelStyle: TextStyle(
                                  fontSize: 11,
                                  color: Color(0xFF148A53),
                                ),
                              ),
                            if (blockedPolitical)
                              const Chip(
                                label: Text('Validations politiques bloquées'),
                                backgroundColor: Color(0xFFECEFF3),
                                side: BorderSide.none,
                                labelStyle: TextStyle(
                                  fontSize: 11,
                                  color: AppColors.muted,
                                ),
                              ),
                          ],
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                _Card(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Votre activité',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.1,
                          color: AppColors.rdcBlue,
                        ),
                      ),
                      const SizedBox(height: 2),
                      const Text(
                        "Vue d'ensemble",
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                          color: AppColors.text,
                        ),
                      ),
                      const SizedBox(height: 16),
                      if (compact)
                        Wrap(
                          spacing: 16,
                          runSpacing: 20,
                          children: [
                            SizedBox(
                              width: 140,
                              child: _Kpi(
                                label: 'Dossiers',
                                value: '${_c('dossiers')}',
                                note: 'Dans le circuit',
                              ),
                            ),
                            SizedBox(
                              width: 140,
                              child: _Kpi(
                                label: 'Mes assignations',
                                value: '${_c('assignations')}',
                                note: 'À votre poste',
                              ),
                            ),
                            SizedBox(
                              width: 140,
                              child: _Kpi(
                                label: 'Normes suivies',
                                value: '${_c('normes_suivies')}',
                                note: 'Rattachement explicite',
                              ),
                            ),
                            SizedBox(
                              width: 140,
                              child: _Kpi(
                                label: 'Tâches en retard',
                                value: '${_c('taches_en_retard')}',
                                note: 'Selon échéance',
                              ),
                            ),
                          ],
                        )
                      else
                        Row(
                          children: [
                            Expanded(
                              child: _Kpi(
                                label: 'Dossiers du Secrétariat technique',
                                value: '${_c('dossiers')}',
                                note: 'Enregistrés dans le circuit',
                              ),
                            ),
                            const _KpiDivider(),
                            Expanded(
                              child: _Kpi(
                                label: 'Mes assignations',
                                value: '${_c('assignations')}',
                                note: 'Attribuées à votre poste',
                              ),
                            ),
                            const _KpiDivider(),
                            Expanded(
                              child: _Kpi(
                                label: 'Normes suivies',
                                value: '${_c('normes_suivies')}',
                                note: 'Rattachement explicite',
                              ),
                            ),
                            const _KpiDivider(),
                            Expanded(
                              child: _Kpi(
                                label: 'Tâches en retard',
                                value: '${_c('taches_en_retard')}',
                                note: 'Selon leur échéance',
                              ),
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                if (compact) ...[
                  _Card(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _CardHeader(
                          title: 'Travail attribué',
                          onTap: onOpenAssignations,
                        ),
                        const SizedBox(height: 10),
                        if (assignations.isEmpty)
                          const _EmptyLine(
                            title: 'Aucun dossier à réceptionner',
                            subtitle:
                                "Aucune assignation explicite n'attend ce poste.",
                          )
                        else
                          for (final a in assignations.take(5)) _TaskLine(a),
                      ],
                    ),
                  ),
                  const SizedBox(height: 18),
                  _Card(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _CardHeader(
                          title: 'Dossiers normatifs',
                          onTap: onOpenDossiers,
                        ),
                        const SizedBox(height: 10),
                        if (dossiers.isEmpty)
                          const _EmptyLine(
                            title: 'Aucun dossier dans le circuit CTC.',
                            subtitle: '',
                          )
                        else
                          for (final d in dossiers.take(5)) _DossierLine(d),
                      ],
                    ),
                  ),
                ] else
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: _Card(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              _CardHeader(
                                title: 'Travail attribué',
                                onTap: onOpenAssignations,
                              ),
                              const SizedBox(height: 10),
                              if (assignations.isEmpty)
                                const _EmptyLine(
                                  title: 'Aucun dossier à réceptionner',
                                  subtitle:
                                      "Aucune assignation explicite n'attend ce poste.",
                                )
                              else
                                for (final a in assignations.take(5))
                                  _TaskLine(a),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: 18),
                      Expanded(
                        child: _Card(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              _CardHeader(
                                title: 'Dossiers normatifs',
                                onTap: onOpenDossiers,
                              ),
                              const SizedBox(height: 10),
                              if (dossiers.isEmpty)
                                const _EmptyLine(
                                  title: 'Aucun dossier dans le circuit CTC.',
                                  subtitle: '',
                                )
                              else
                                for (final d in dossiers.take(5))
                                  _DossierLine(d),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                const SizedBox(height: 18),
                if (compact) ...[
                  _BreakdownCard(title: 'Normes par statut', rows: stageRows),
                  const SizedBox(height: 18),
                  _BreakdownCard(
                    title: 'Normes suivies par groupe',
                    rows: groupNormRows,
                  ),
                ] else
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: _BreakdownCard(
                          title: 'Normes par statut',
                          rows: stageRows,
                        ),
                      ),
                      const SizedBox(width: 18),
                      Expanded(
                        child: _BreakdownCard(
                          title: 'Normes suivies par groupe',
                          rows: groupNormRows,
                        ),
                      ),
                    ],
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _AccentButton extends StatelessWidget {
  const _AccentButton({required this.label, required this.onTap});
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.accent,
      borderRadius: BorderRadius.circular(11),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(11),
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

class _BreakdownCard extends StatelessWidget {
  const _BreakdownCard({required this.title, required this.rows});

  final String title;
  final List<Map<String, dynamic>> rows;

  @override
  Widget build(BuildContext context) => _Card(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w700,
            color: AppColors.text,
          ),
        ),
        const SizedBox(height: 14),
        if (rows.isEmpty)
          const Text(
            'Aucune donnée disponible.',
            style: TextStyle(color: AppColors.muted),
          )
        else
          for (final row in rows.take(8)) ...[
            Row(
              children: [
                Expanded(
                  child: Text(
                    [
                      if (row['parent'] != null) row['parent'],
                      row['label'],
                    ].join(' · '),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 12, color: AppColors.text),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  '${row['count'] ?? 0}',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 5),
            LinearProgressIndicator(
              value:
                  ((row['width'] as num?)?.toDouble() ?? 0).clamp(0, 100) / 100,
              minHeight: 5,
              borderRadius: BorderRadius.circular(5),
              backgroundColor: const Color(0xFFEDF3F7),
              color: AppColors.sky,
            ),
            const SizedBox(height: 12),
          ],
      ],
    ),
  );
}

class _TaskLine extends StatelessWidget {
  const _TaskLine(this.a);
  final Map<String, dynamic> a;
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${a['type_label'] ?? 'Traitement CTC'} · ${a['status_display'] ?? ''}',
            style: const TextStyle(fontSize: 11, color: AppColors.muted),
          ),
          const SizedBox(height: 2),
          Text(
            a['title'] as String? ?? '',
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: AppColors.text,
            ),
          ),
        ],
      ),
    );
  }
}

class _DossierLine extends StatelessWidget {
  const _DossierLine(this.d);
  final Map<String, dynamic> d;
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${d['reference'] ?? ''} · ${d['stage_label'] ?? ''}',
            style: const TextStyle(fontSize: 11, color: AppColors.muted),
          ),
          const SizedBox(height: 2),
          Text(
            d['title'] as String? ?? '',
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: AppColors.text,
            ),
          ),
        ],
      ),
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.border),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0D0F1B2D),
            blurRadius: 24,
            offset: Offset(0, 8),
          ),
        ],
      ),
      child: child,
    );
  }
}

class _Kpi extends StatelessWidget {
  const _Kpi({required this.label, required this.value, required this.note});
  final String label;
  final String value;
  final String note;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: AppColors.muted,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          value,
          style: const TextStyle(
            fontSize: 30,
            fontWeight: FontWeight.w800,
            letterSpacing: -1,
            color: AppColors.text,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          note,
          style: const TextStyle(fontSize: 11, color: AppColors.muted),
        ),
      ],
    );
  }
}

class _KpiDivider extends StatelessWidget {
  const _KpiDivider();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 1,
      height: 72,
      color: AppColors.border,
      margin: const EdgeInsets.symmetric(horizontal: 14),
    );
  }
}

class _CardHeader extends StatelessWidget {
  const _CardHeader({required this.title, this.onTap});
  final String title;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Expanded(
          child: Text(
            title,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: AppColors.text,
            ),
          ),
        ),
        if (onTap != null)
          TextButton(onPressed: onTap, child: const Text('Tout voir')),
      ],
    );
  }
}

class _EmptyLine extends StatelessWidget {
  const _EmptyLine({required this.title, required this.subtitle});
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: AppColors.text,
          ),
        ),
        if (subtitle.isNotEmpty) ...[
          const SizedBox(height: 2),
          Text(
            subtitle,
            style: const TextStyle(fontSize: 12, color: AppColors.muted),
          ),
        ],
      ],
    );
  }
}

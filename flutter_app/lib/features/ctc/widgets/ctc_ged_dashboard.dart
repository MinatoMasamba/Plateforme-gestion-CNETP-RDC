import 'dart:math' as math;
import 'package:flutter/material.dart';

import '../../../theme/app_colors.dart';
import 'ged_shared.dart';

/// Tableau de bord du poste 11 (dashboard GED) — section `data-ged-panel="dashboard"`
/// de `ged_workspace.html` : KPI réels, activité des sous-commissions, tuyaux
/// poste 6 → indexation → contrôle du pôle 2, anomalies, mon activité.

const _scStatusLabels = {
  'aucune': 'Aucun',
  'retard': 'Retard',
  'partielle': 'Partielle',
  'normale': 'Normale',
};
const _scStatusColors = {
  'aucune': AppColors.subtle,
  'retard': AppColors.danger,
  'partielle': AppColors.warning,
  'normale': AppColors.success,
};

const _anomalyKinds = <String, String>{
  'MISSING_FILE': 'Fichier manquant',
  'CORRUPT': 'Fichier corrompu',
  'MISFILED': 'Pièce mal classée',
  'INCONSISTENT': 'Information incohérente',
};

const _historyLabels = <String, String>{
  'ged_code_authorized': 'Code autorisé',
  'ged_file_uploaded': 'Fichier préparé',
  'ged_indexed': 'Indexation enregistrée',
  'ged_restored': 'Version restaurée',
  'ged_confirmed': 'Version confirmée',
  'ged_returned': 'Correction demandée',
  'ged_anomaly_reported': 'Anomalie signalée',
  'ged_anomaly_resolved': 'Anomalie résolue',
};

class GedDashboardPanel extends StatelessWidget {
  const GedDashboardPanel({
    super.key,
    required this.data,
    required this.wide,
    required this.onOpenWork,
    required this.onOpenAnomalies,
    required this.onOpenActivity,
    required this.onOpenFollowup,
    required this.onOpenSc,
    required this.onOpenProcess,
  });

  final Map<String, dynamic> data;
  final bool wide;
  final void Function() onOpenWork;
  final void Function() onOpenAnomalies;
  final void Function() onOpenActivity;
  final VoidCallback onOpenFollowup;
  final ValueChanged<String> onOpenSc;
  final void Function(int id, String reference) onOpenProcess;

  @override
  Widget build(BuildContext context) {
    final kpis = (data['kpis'] as Map? ?? {}).cast<String, dynamic>();
    final statistics = (data['statistics'] as Map? ?? {})
        .cast<String, dynamic>();
    final conformity = (statistics['conformity'] as Map? ?? {})
        .cast<String, dynamic>();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _ScActivityCard(data: data, onOpenSc: onOpenSc),
        const SizedBox(height: 16),
        GedCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const GedSectionTitle(
                'Contrôle documentaire',
                Icons.fact_check_outlined,
              ),
              const SizedBox(height: 14),
              Wrap(
                spacing: 18,
                runSpacing: 16,
                children: [
                  GedKpi(
                    value: kpis['ready'] ?? 0,
                    label: 'Admissibles à indexer',
                  ),
                  GedKpi(
                    value: kpis['waiting_report'] ?? 0,
                    label: 'Rapport SC attendu',
                  ),
                  GedKpi(
                    value: kpis['blocked'] ?? 0,
                    label: 'Bloqués / à corriger',
                  ),
                  InkWell(
                    onTap: onOpenFollowup,
                    borderRadius: BorderRadius.circular(8),
                    child: Padding(
                      padding: const EdgeInsets.all(2),
                      child: GedKpi(
                        value: kpis['versions_todo'] ?? 0,
                        label: 'Versions à traiter',
                      ),
                    ),
                  ),
                  GedKpi(value: kpis['indexed'] ?? 0, label: 'Déjà indexés'),
                  GedKpi(value: kpis['pending'] ?? 0, label: 'À confirmer'),
                  GedKpi(
                    value: kpis['anomalies'] ?? 0,
                    label: 'Anomalies ouvertes',
                  ),
                  GedKpi(
                    value: kpis['overdue_14'] ?? 0,
                    label: 'Retards > 14 jours',
                  ),
                  GedKpi(
                    value: kpis['confirmed_period'] ?? 0,
                    label: 'Confirmés sur la période',
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                'Délai médian de confirmation : '
                '${kpis['median_delay_days'] ?? '—'} jours · '
                "objectif ${statistics['objective_days'] ?? 3} jours · "
                '${statistics['scope'] ?? ''}',
                style: const TextStyle(fontSize: 12, color: AppColors.muted),
              ),
              if (conformity['total'] != null &&
                  conformity['total'] is num &&
                  (conformity['total'] as num).toInt() > 0) ...[
                const SizedBox(height: 8),
                Text(
                  'Indexations contrôlées : ${conformity['total']} · '
                  "référence unique : ${conformity['reference_unique'] == true ? 'oui' : 'non'} · "
                  "classement SC / GT : ${conformity['classified'] == true ? 'oui' : 'non'}",
                  style: const TextStyle(fontSize: 12, color: AppColors.muted),
                ),
              ],
              const SizedBox(height: 4),
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton.icon(
                  onPressed: onOpenWork,
                  icon: const Icon(Icons.arrow_forward, size: 16),
                  label: const Text('Ouvrir la file d’indexation'),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        if (wide)
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _UpstreamCard(
                  data: data,
                  onOpenWork: onOpenWork,
                  onOpenProcess: onOpenProcess,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _DownstreamCard(
                  data: data,
                  onOpenFollowup: onOpenFollowup,
                ),
              ),
            ],
          )
        else ...[
          _UpstreamCard(
            data: data,
            onOpenWork: onOpenWork,
            onOpenProcess: onOpenProcess,
          ),
          const SizedBox(height: 16),
          _DownstreamCard(data: data, onOpenFollowup: onOpenFollowup),
          const SizedBox(height: 16),
        ],
        _AnomalySummaryCard(data: data, onOpenAnomalies: onOpenAnomalies),
        const SizedBox(height: 16),
        _MyActivityCard(data: data, onOpenAll: onOpenActivity),
      ],
    );
  }
}

class _ScActivityCard extends StatefulWidget {
  const _ScActivityCard({required this.data, required this.onOpenSc});

  final Map<String, dynamic> data;
  final ValueChanged<String> onOpenSc;

  @override
  State<_ScActivityCard> createState() => _ScActivityCardState();
}

class _ScActivityCardState extends State<_ScActivityCard> {
  final Set<String> _hidden = {};
  Offset? _pointer;
  Offset? _selectedPoint;

  @override
  Widget build(BuildContext context) {
    final data = widget.data;
    final activity = (data['sc_activity'] as Map? ?? {})
        .cast<String, dynamic>();
    final rows = rowsOf(activity['results'])
      ..sort((a, b) => '${a['code']}'.compareTo('${b['code']}'));
    final buckets = rowsOf(activity['buckets']);
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GedSectionTitle(
            'Activité des sept sous-commissions',
            Icons.insights_outlined,
          ),
          const SizedBox(height: 6),
          Text(
            'Une ligne par sous-commission · période '
            '${frDate(activity['period_start'])} → ${frDate(activity['period_end'])}',
            style: const TextStyle(fontSize: 12, color: AppColors.muted),
          ),
          const SizedBox(height: 12),
          if (rows.isNotEmpty && buckets.isNotEmpty) ...[
            const Text(
              'Actions enregistrées : votes, transmissions au CTC et rapports SC reçus. '
              'Les connexions ne sont pas comptées. Le volume ne mesure pas la qualité des normes.',
              style: TextStyle(fontSize: 11, color: AppColors.muted),
            ),
            const SizedBox(height: 12),
            TweenAnimationBuilder<double>(
              key: ValueKey(
                '${activity['period_start']}:${activity['period_end']}:${rows.map((r) => r['series']).join()}',
              ),
              tween: Tween(begin: 0, end: 1),
              duration: MediaQuery.disableAnimationsOf(context)
                  ? Duration.zero
                  : const Duration(milliseconds: 1500),
              curve: Curves.easeOutCubic,
              builder: (context, progress, _) => LayoutBuilder(
                builder: (context, constraints) {
                  final painter = _ActivityPainter(
                    rows,
                    buckets,
                    progress: progress,
                    hidden: _hidden,
                    pointer: _pointer,
                  );
                  final hit = _pointer == null
                      ? null
                      : painter.nearest(
                          _pointer!,
                          Size(constraints.maxWidth, 230),
                        );
                  return Semantics(
                    label:
                        'Évolution du nombre d’actions enregistrées par sous-commission',
                    child: MouseRegion(
                      onHover: (event) =>
                          setState(() => _pointer = event.localPosition),
                      onExit: (_) => setState(() => _pointer = _selectedPoint),
                      child: GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onTap: () {},
                        onTapDown: (details) => setState(() {
                          _selectedPoint = details.localPosition;
                          _pointer = details.localPosition;
                        }),
                        onHorizontalDragUpdate: (details) => setState(() {
                          _selectedPoint = details.localPosition;
                          _pointer = details.localPosition;
                        }),
                        child: SizedBox(
                          height: 230,
                          width: double.infinity,
                          child: Stack(
                            children: [
                              Positioned.fill(
                                child: CustomPaint(painter: painter),
                              ),
                              if (hit != null)
                                Positioned(
                                  left: (_pointer!.dx - 90)
                                      .clamp(
                                        0,
                                        math.max(0, constraints.maxWidth - 210),
                                      )
                                      .toDouble(),
                                  top: 0,
                                  child: IgnorePointer(
                                    child: Container(
                                      constraints: const BoxConstraints(
                                        maxWidth: 210,
                                      ),
                                      padding: const EdgeInsets.all(10),
                                      decoration: BoxDecoration(
                                        color: Theme.of(context)
                                            .colorScheme
                                            .surface
                                            .withValues(alpha: .97),
                                        borderRadius: BorderRadius.circular(10),
                                        border: Border.all(
                                          color: AppColors.border,
                                        ),
                                        boxShadow: const [
                                          BoxShadow(
                                            color: Color(0x14000000),
                                            blurRadius: 12,
                                          ),
                                        ],
                                      ),
                                      child: Text(
                                        hit,
                                        style: const TextStyle(
                                          fontSize: 11,
                                          color: AppColors.text,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
            const Text(
              'Touchez un point pour le détail. Cliquez sur une légende pour afficher ou masquer sa courbe.',
              style: TextStyle(fontSize: 11, color: AppColors.muted),
            ),
            const SizedBox(height: 12),
            if (rows.every(
              (row) =>
                  (row['series'] as List? ?? []).every((value) => value == 0),
            ))
              const Padding(
                padding: EdgeInsets.only(bottom: 12),
                child: GedEmpty(
                  'Aucun événement daté sur la période. Une sous-commission sans activité n’est pas considérée comme défaillante.',
                ),
              ),
          ],
          if (rows.isEmpty)
            const GedEmpty('Aucune sous-commission active sur la période.')
          else
            for (final row in rows)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: InkWell(
                  onTap: () => setState(() {
                    final code = '${row['code'] ?? ''}';
                    if (!_hidden.remove(code)) _hidden.add(code);
                    _pointer = null;
                    _selectedPoint = null;
                  }),
                  borderRadius: BorderRadius.circular(8),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              width: 9,
                              height: 9,
                              decoration: BoxDecoration(
                                color: _hidden.contains('${row['code']}')
                                    ? AppColors.subtle
                                    : _chartColors[rows.indexOf(row) %
                                          _chartColors.length],
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                '${_hidden.contains('${row['code']}') ? '○' : '●'} ${row['code'] ?? ''} · ${row['name'] ?? row['official_name'] ?? ''}',
                                style: const TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700,
                                  color: AppColors.text,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            GedBadge(
                              label: row['idle'] == true
                                  ? 'Aucune activité'
                                  : (_scStatusLabels[row['status']] ?? '—'),
                              color:
                                  _scStatusColors[row['status']] ??
                                  AppColors.subtle,
                            ),
                          ],
                        ),
                        Align(
                          alignment: Alignment.centerLeft,
                          child: TextButton(
                            onPressed: () =>
                                widget.onOpenSc('${row['code'] ?? ''}'),
                            child: const Text(
                              'Voir les dossiers',
                              style: TextStyle(fontSize: 11),
                            ),
                          ),
                        ),
                        Text(
                          'Dossiers ${row['dossiers'] ?? 0} · votes ${row['votes'] ?? 0} · '
                          'transmissions ${row['transmitted'] ?? 0} · rapports reçus ${row['reports'] ?? 0}',
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppColors.muted,
                          ),
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

const _chartColors = [
  Color(0xFF2778D9),
  Color(0xFF148B78),
  Color(0xFFC9821B),
  Color(0xFFC94C4C),
  Color(0xFF7C5CD6),
  Color(0xFF0E8FA8),
  Color(0xFF5B6B82),
];

class _ActivityPainter extends CustomPainter {
  _ActivityPainter(
    this.rows,
    this.buckets, {
    this.progress = 1,
    required this.hidden,
    this.pointer,
  });
  final double progress;
  final Set<String> hidden;
  final Offset? pointer;

  double get maximum {
    final peak = rows
        .expand((r) => (r['series'] as List? ?? []).whereType<num>())
        .fold<double>(1, (a, b) => math.max(a, b.toDouble()))
        .ceilToDouble();
    final steps = math.min(4, peak.toInt());
    return (peak / steps).ceilToDouble() * steps;
  }

  String? nearest(Offset pointer, Size size) {
    final plot = Rect.fromLTRB(26, 12, size.width - 15, size.height - 32);
    double distance = double.infinity;
    String? result;
    for (final row in rows) {
      if (hidden.contains('${row['code']}')) continue;
      final values = row['series'] as List? ?? [];
      for (var i = 0; i < math.min(values.length, buckets.length); i++) {
        final point = Offset(
          plot.left +
              plot.width *
                  (buckets.length == 1 ? .5 : i / (buckets.length - 1)),
          plot.bottom - plot.height * (values[i] as num) / maximum * progress,
        );
        final delta = (point - pointer).distance;
        if (delta < distance) {
          distance = delta;
          result =
              '${row['code']} · ${row['name'] ?? row['official_name'] ?? ''}\n'
              '${frDate(buckets[i]['start'])} → ${frDate(buckets[i]['end'])}\n${values[i]} action(s)';
        }
      }
    }
    return distance <= 50 ? result : null;
  }

  final List<Map<String, dynamic>> rows;
  final List<Map<String, dynamic>> buckets;
  @override
  void paint(Canvas canvas, Size size) {
    final plot = Rect.fromLTRB(26, 12, size.width - 15, size.height - 32);
    final observedMax = rows
        .expand((row) => (row['series'] as List? ?? []).whereType<num>())
        .fold<double>(1, (max, value) => math.max(max, value.toDouble()))
        .ceilToDouble();
    final steps = math.min(4, observedMax.toInt());
    final maximum = (observedMax / steps).ceilToDouble() * steps;
    void label(String text, Offset position) {
      final painter = TextPainter(
        text: TextSpan(
          text: text,
          style: const TextStyle(fontSize: 10, color: AppColors.muted),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      painter.paint(
        canvas,
        Offset(
          position.dx
              .clamp(0, math.max(0, size.width - painter.width))
              .toDouble(),
          position.dy,
        ),
      );
    }

    for (var tick = 0; tick <= steps; tick++) {
      final value = maximum * tick / steps;
      final y = plot.bottom - plot.height * tick / steps;
      canvas.drawLine(
        Offset(plot.left, y),
        Offset(plot.right, y),
        Paint()..color = AppColors.border,
      );
      label(
        value == value.roundToDouble()
            ? '${value.toInt()}'
            : value.toStringAsFixed(1),
        Offset(0, y - 6),
      );
    }
    final stride = math.max(
      1,
      (buckets.length / (size.width < 400 ? 3 : 6)).ceil(),
    );
    for (var index = 0; index < buckets.length; index++) {
      final x =
          plot.left +
          plot.width *
              (buckets.length == 1 ? .5 : index / (buckets.length - 1));
      if (index % stride == 0 || index == buckets.length - 1) {
        label(
          '${buckets[index]['label'] ?? ''}',
          Offset(x - 14, plot.bottom + 10),
        );
      }
    }
    for (var rowIndex = 0; rowIndex < rows.length; rowIndex++) {
      if (hidden.contains('${rows[rowIndex]['code']}')) continue;
      final values = (rows[rowIndex]['series'] as List? ?? [])
          .whereType<num>()
          .toList();
      final color = _chartColors[rowIndex % _chartColors.length];
      final points = <Offset>[
        for (var i = 0; i < math.min(values.length, buckets.length); i++)
          Offset(
            plot.left +
                plot.width *
                    (buckets.length == 1 ? .5 : i / (buckets.length - 1)),
            plot.bottom - plot.height * values[i] / maximum * progress,
          ),
      ];
      if (points.isEmpty) continue;
      final path = Path()..moveTo(points.first.dx, points.first.dy);
      // Horizontal tangent at each sample: smooth, bounded and without negative overshoot.
      for (var i = 1; i < points.length; i++) {
        final middle = (points[i - 1].dx + points[i].dx) / 2;
        path.cubicTo(
          middle,
          points[i - 1].dy,
          middle,
          points[i].dy,
          points[i].dx,
          points[i].dy,
        );
      }
      final area = Path.from(path)
        ..lineTo(points.last.dx, plot.bottom)
        ..lineTo(points.first.dx, plot.bottom)
        ..close();
      canvas.drawPath(
        area,
        Paint()
          ..shader = LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              color.withValues(alpha: .09),
              color.withValues(alpha: .005),
            ],
          ).createShader(plot),
      );
      canvas.drawPath(
        path,
        Paint()
          ..color = color
          ..strokeWidth = 2
          ..style = PaintingStyle.stroke,
      );
      for (final point in points) {
        canvas.drawCircle(point, 3, Paint()..color = color);
        if (pointer != null && (point - pointer!).distance < 20) {
          canvas.drawCircle(
            point,
            6,
            Paint()..color = color.withValues(alpha: .2),
          );
        }
      }
    }
  }

  @override
  bool shouldRepaint(covariant _ActivityPainter oldDelegate) => true;
}

class _UpstreamCard extends StatelessWidget {
  const _UpstreamCard({
    required this.data,
    required this.onOpenWork,
    required this.onOpenProcess,
  });

  final Map<String, dynamic> data;
  final VoidCallback onOpenWork;
  final void Function(int id, String reference) onOpenProcess;

  @override
  Widget build(BuildContext context) {
    final upstream = (data['pipeline_upstream'] as Map? ?? {})
        .cast<String, dynamic>();
    final latest = rowsOf(upstream['latest']);
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GedSectionTitle(
            'Poste 6 · Réceptions du secrétariat',
            Icons.move_to_inbox_outlined,
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 16,
            runSpacing: 12,
            children: [
              GedKpi(
                value: upstream['registered_after_vote'] ?? 0,
                label: 'Réceptions enregistrées',
              ),
              GedKpi(
                value: upstream['recently_transmitted'] ?? 0,
                label: 'Transmises (7 j)',
              ),
              GedKpi(
                value: upstream['awaiting_sc_report'] ?? 0,
                label: 'Rapport attendu',
              ),
              GedKpi(
                value: upstream['eligible_for_indexation'] ?? 0,
                label: 'Admissibles',
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (latest.isEmpty)
            const GedEmpty('Aucune réception récente enregistrée.')
          else
            for (final item in latest.take(4))
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: InkWell(
                  onTap: item['process_id'] is num
                      ? () => onOpenProcess(
                          (item['process_id'] as num).toInt(),
                          '${item['reference'] ?? ''}',
                        )
                      : null,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${item['reference'] ?? ''} · ${item['sc'] ?? ''}',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AppColors.text,
                        ),
                      ),
                      Text(
                        '${item['title'] ?? ''} · ${item['has_report'] == true ? 'rapport reçu' : 'rapport attendu'}',
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.muted,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          TextButton.icon(
            onPressed: onOpenWork,
            icon: const Icon(Icons.arrow_forward, size: 16),
            label: const Text('Voir les réceptions'),
          ),
        ],
      ),
    );
  }
}

class _DownstreamCard extends StatelessWidget {
  const _DownstreamCard({required this.data, required this.onOpenFollowup});

  final Map<String, dynamic> data;
  final VoidCallback onOpenFollowup;

  String _decision(dynamic state) {
    switch (state) {
      case 'CONFIRMED':
        return 'Confirmé';
      case 'RETURNED':
        return 'À corriger';
      default:
        return 'À confirmer';
    }
  }

  @override
  Widget build(BuildContext context) {
    final downstream = (data['pipeline_downstream'] as Map? ?? {})
        .cast<String, dynamic>();
    final latest = rowsOf(downstream['latest']);
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GedSectionTitle(
            'Après indexation · suite du traitement',
            Icons.move_up_outlined,
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 16,
            runSpacing: 12,
            children: [
              GedKpi(
                value: downstream['sent_to_p2_control'] ?? 0,
                label: 'Contrôle Pôle 2',
              ),
              GedKpi(
                value: downstream['awaiting_post_10'] ?? 0,
                label: 'Contrôle pôle 2 attendu',
              ),
              GedKpi(value: downstream['left_p2'] ?? 0, label: 'Hors Pôle 2'),
              GedKpi(
                value: downstream['returned_after_exam'] ?? 0,
                label: 'Corrections demandées',
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (latest.isEmpty)
            const GedEmpty('Aucune indexation enregistrée pour le moment.')
          else
            for (final item in latest.take(4))
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${item['reference'] ?? ''} · ${item['code'] ?? ''} · v${item['version'] ?? ''}',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: AppColors.text,
                      ),
                    ),
                    Text(
                      "Indexé par ${item['author'] ?? ''} · décision : ${_decision(item['state'])}",
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.muted,
                      ),
                    ),
                  ],
                ),
              ),
          TextButton.icon(
            onPressed: onOpenFollowup,
            icon: const Icon(Icons.arrow_forward, size: 16),
            label: const Text('Voir le suivi'),
          ),
        ],
      ),
    );
  }
}

class _AnomalySummaryCard extends StatelessWidget {
  const _AnomalySummaryCard({
    required this.data,
    required this.onOpenAnomalies,
  });

  final Map<String, dynamic> data;
  final void Function() onOpenAnomalies;

  @override
  Widget build(BuildContext context) {
    final open = rowsOf(
      data['anomalies'],
    ).where((item) => item['resolved_at'] == null).toList();
    final counts = <String, int>{};
    for (final item in open) {
      final kind =
          _anomalyKinds[item['kind']] ??
          (item['kind_label'] ?? 'Anomalie').toString();
      counts[kind] = (counts[kind] ?? 0) + 1;
    }
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GedSectionTitle(
            'Anomalies et retours',
            Icons.warning_amber_outlined,
          ),
          TextButton(
            onPressed: onOpenAnomalies,
            child: const Text('Voir toutes les anomalies'),
          ),
          const SizedBox(height: 8),
          if (open.isEmpty)
            const GedEmpty('Aucune anomalie documentaire ouverte.')
          else
            for (final entry in counts.entries)
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        entry.key,
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.text,
                        ),
                      ),
                    ),
                    Text(
                      '${entry.value}',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                ),
              ),
          for (final item in open.take(4))
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: InkWell(
                onTap: onOpenAnomalies,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${item['reference'] ?? ''} · ${item['kind_label'] ?? _anomalyKinds[item['kind']] ?? 'Anomalie'}',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Text(
                      '${item['comment'] ?? ''}',
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.muted,
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

class _MyActivityCard extends StatelessWidget {
  const _MyActivityCard({required this.data, required this.onOpenAll});

  final Map<String, dynamic> data;
  final void Function() onOpenAll;

  @override
  Widget build(BuildContext context) {
    final events = rowsOf(data['activity']);
    final activity = events.take(6).toList();
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GedSectionTitle('Mon activité', Icons.history_outlined),
          TextButton(
            onPressed: onOpenAll,
            child: const Text('Voir toute l’activité'),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              GedKpi(
                value: events.where((e) => e['action'] == 'ged_indexed').length,
                label: 'Indexations récentes',
              ),
              GedKpi(
                value: events
                    .where(
                      (e) => [
                        'ged_restored',
                        'ged_confirmed',
                      ].contains(e['action']),
                    )
                    .length,
                label: 'Versions suivies',
              ),
              GedKpi(
                value: events
                    .where(
                      (e) => [
                        'ged_returned',
                        'ged_anomaly_resolved',
                      ].contains(e['action']),
                    )
                    .length,
                label: 'Corrections récentes',
              ),
              GedKpi(value: events.length, label: 'Opérations récentes'),
            ],
          ),
          const SizedBox(height: 14),
          if (activity.isEmpty)
            const GedEmpty('Aucune opération enregistrée sur la période.')
          else
            for (final item in activity)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "${_historyLabels[item['action']] ?? item['action'] ?? 'Opération'} · ${frDateTime(item['date'])}",
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: AppColors.text,
                      ),
                    ),
                    Text(
                      "${item['reference'] ?? ''}"
                      "${asText(item['code']) != null ? ' · ${item['code']}' : ''}"
                      "${item['version'] != null ? ' · v${item['version']}' : ''}"
                      "${asText(item['author']) != null ? ' · ${item['author']}' : ''}",
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 12,
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

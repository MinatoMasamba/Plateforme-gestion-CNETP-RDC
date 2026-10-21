import 'package:flutter/material.dart';
import '../../../theme/app_colors.dart';

/// Tableau de bord CTC — reproduit `dashboard_module.html` (design "premium").
class CtcDashboardView extends StatelessWidget {
  const CtcDashboardView({super.key, required this.poleLabel});

  final String poleLabel;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topRight,
          end: Alignment.bottomLeft,
          colors: [Color(0xFFF2F9FF), AppColors.page, AppColors.page],
        ),
      ),
      padding: const EdgeInsets.all(24),
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
                      style: TextStyle(fontSize: 13, color: AppColors.muted),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: AppColors.accent,
                  borderRadius: BorderRadius.circular(11),
                ),
                child: const Text(
                  'Mes assignations',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Colors.white),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          _Card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Votre activité',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.1, color: AppColors.rdcBlue),
                ),
                const SizedBox(height: 2),
                const Text(
                  "Vue d'ensemble",
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: AppColors.text),
                ),
                const SizedBox(height: 16),
                Row(
                  children: const [
                    Expanded(child: _Kpi(label: 'Dossiers du Secrétariat technique', value: '0', note: 'Enregistrés dans le circuit')),
                    _KpiDivider(),
                    Expanded(child: _Kpi(label: 'Mes assignations', value: '0', note: 'Attribuées à votre poste')),
                    _KpiDivider(),
                    Expanded(child: _Kpi(label: 'Normes suivies', value: '0', note: 'Rattachement explicite')),
                    _KpiDivider(),
                    Expanded(child: _Kpi(label: 'Tâches en retard', value: '0', note: 'Selon leur échéance')),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _Card(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const _CardHeader(title: 'Travail attribué'),
                      const SizedBox(height: 10),
                      _EmptyLine(title: 'Aucun dossier à réceptionner', subtitle: "Aucune assignation explicite n'attend ce poste."),
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
                      const _CardHeader(title: 'Dossiers normatifs'),
                      const SizedBox(height: 10),
                      _EmptyLine(title: 'Aucun dossier dans le circuit CTC.', subtitle: ''),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          _Card(
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      Text('Suivi statistique', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.text)),
                      SizedBox(height: 4),
                      Text('0 sous-commissions et CTM · 0 groupes suivis.', style: TextStyle(fontSize: 12, color: AppColors.muted)),
                    ],
                  ),
                ),
                const _Donut(value: 0, color: AppColors.sky),
              ],
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
        boxShadow: const [BoxShadow(color: Color(0x0D0F1B2D), blurRadius: 24, offset: Offset(0, 8))],
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
        Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.muted)),
        const SizedBox(height: 6),
        Text(value, style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w800, letterSpacing: -1, color: AppColors.text)),
        const SizedBox(height: 8),
        Text(note, style: const TextStyle(fontSize: 11, color: AppColors.muted)),
      ],
    );
  }
}

class _KpiDivider extends StatelessWidget {
  const _KpiDivider();

  @override
  Widget build(BuildContext context) {
    return Container(width: 1, height: 72, color: AppColors.border, margin: const EdgeInsets.symmetric(horizontal: 14));
  }
}

class _CardHeader extends StatelessWidget {
  const _CardHeader({required this.title});
  final String title;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.text)),
        const Text('Tout voir', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.accent)),
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
        Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.text)),
        if (subtitle.isNotEmpty) ...[
          const SizedBox(height: 2),
          Text(subtitle, style: const TextStyle(fontSize: 12, color: AppColors.muted)),
        ],
      ],
    );
  }
}

class _Donut extends StatelessWidget {
  const _Donut({required this.value, required this.color});
  final int value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 72,
      height: 72,
      child: Stack(
        fit: StackFit.expand,
        children: [
          CircularProgressIndicator(
            value: value / 100,
            strokeWidth: 9,
            backgroundColor: const Color(0xFFEDF3F7),
            valueColor: AlwaysStoppedAnimation(color),
          ),
          Center(
            child: Text(
              '$value%',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppColors.text),
            ),
          ),
        ],
      ),
    );
  }
}

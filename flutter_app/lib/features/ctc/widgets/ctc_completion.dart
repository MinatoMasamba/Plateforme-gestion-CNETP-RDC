import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../theme/app_colors.dart';

/// Donut « Avancement des tâches » — miroir du `premium-donut--value` web
/// (conic-gradient sur `--donut-value` dans institutional-ui.css:161).
/// La visualisation tourne en boucle : chaque cycle redessine l'arc 0 → valeur
/// comme le compteur `ctc-animations.js` du web.
class CtcCompletionDonut extends StatefulWidget {
  const CtcCompletionDonut({
    super.key,
    required this.value,
    this.colorHex,
    this.size = 88,
    this.repeat = true,
  });

  /// Pourcentage de complétion (0–100), déjà arrondi côté serveur.
  final double? value;

  /// Couleur calculée côté serveur (`global_color`, format `#hex`).
  final String? colorHex;

  final double size;

  /// Boucle permanente de la visualisation (correspondance web ↔ app).
  final bool repeat;

  static Color donutColor(String? hex) {
    final raw = (hex ?? '').replaceFirst('#', '').trim();
    final parsed = int.tryParse(raw, radix: 16);
    if (parsed == null || raw.length != 6) return AppColors.sky;
    return Color(0xFF000000 | parsed);
  }

  @override
  State<CtcCompletionDonut> createState() => _CtcCompletionDonutState();
}

class _CtcCompletionDonutState extends State<CtcCompletionDonut>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  /// 75 % du cycle : l'arc se remplit de 0 à la valeur, puis une courte
  /// pause affichant la valeur finale avant de recommencer la boucle.
  Animation<double> get _fill => CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.0, 0.75, curve: Curves.easeOutCubic),
      );

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2800),
    );
    if (widget.repeat) {
      _controller.repeat();
    } else {
      _controller.forward();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final value = (widget.value ?? 0).clamp(0, 100).toDouble();
    final color = CtcCompletionDonut.donutColor(widget.colorHex);
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final eased = _fill.value;
        return SizedBox(
          width: widget.size,
          height: widget.size,
          child: CustomPaint(
            painter: _DonutPainter(sweep: value / 100 * eased, color: color),
            child: Center(
              child: Text(
                widget.value == null
                    ? '—'
                    : '${(value * eased).round()}%',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: widget.size >= 80 ? 19 : 15,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.5,
                  color: AppColors.text,
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

/// Fond du donut — miroir `--donut-track: #edf3f7` (institutional-ui.css).
const Color _donutTrack = Color(0xFFEDF3F7);

/// Full-circle constant: `dart:math` n'expose pas de "tau".
const double _tau = math.pi * 2;

class _DonutPainter extends CustomPainter {
  const _DonutPainter({required this.sweep, required this.color});

  /// Fraction peinte (0 → valeur %) pour le cycle courant.
  final double sweep;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final stroke = size.shortestSide * 0.11;
    final radius = size.shortestSide / 2 - stroke / 2;
    final center = Offset(size.width / 2, size.height / 2);
    final rect = Rect.fromCircle(
      center: center,
      radius: radius,
    );
    final trackPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke
      ..color = _donutTrack;
    canvas.drawArc(rect, 0, _tau, false, trackPaint);
    if (sweep > 0) {
      final valuePaint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = stroke
        ..strokeCap = StrokeCap.round
        ..color = color;
      // Départ à 12h (-90°), sens horaire, comme le conic-gradient web
      // (`conic-gradient(from -90deg, …)`).
      canvas.drawArc(rect, -math.pi / 2, _tau * sweep, false, valuePaint);
    }
  }

  @override
  bool shouldRepaint(_DonutPainter old) =>
      old.sweep != sweep || old.color != color;
}

/// Carte « Suivi statistique » du dashboard — miroir de la ligne
/// `dashboard_module.html:52` : titre, périmètre suivi, donut bouclé et
/// bouton vers la vue statistiques.
class CtcCompletionCard extends StatelessWidget {
  const CtcCompletionCard({
    super.key,
    required this.performance,
    this.title = 'Suivi statistique',
    this.subtitle,
    this.note,
    this.centerLabel,
    this.onOpenStatistics,
  });

  final Map<String, dynamic>? performance;
  final String title;
  final String? subtitle;
  final String? note;
  final String? centerLabel;
  final VoidCallback? onOpenStatistics;

  double? get _value {
    final raw = performance?['value'];
    return raw is num ? raw.toDouble() : null;
  }

  String? get _colorHex => performance?['color']?.toString();

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
      child: Row(
        children: [
          Expanded(
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
                if (subtitle?.isNotEmpty ?? false) ...[
                  const SizedBox(height: 4),
                  Text(
                    subtitle!,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.muted,
                    ),
                  ),
                ],
                const SizedBox(height: 10),
                Text(
                  _value == null
                      ? 'Aucune tâche pondérée.'
                      : 'Avancement des tâches : ${_value! % 1 == 0 ? _value!.toInt() : _value} %',
                  style: TextStyle(
                    fontSize: _value == null ? 12 : 22,
                    fontWeight: FontWeight.w800,
                    color: _value == null
                        ? AppColors.muted
                        : CtcCompletionDonut.donutColor(_colorHex),
                  ),
                ),
                Text(
                  note ?? 'Σ poids × progression ÷ Σ poids planifiés. '
                      'Mise à jour en boucle.',
                  style: const TextStyle(
                    fontSize: 11,
                    color: AppColors.muted,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          CtcCompletionDonut(value: _value, colorHex: _colorHex),
          if (onOpenStatistics != null) ...[
            const SizedBox(width: 8),
            TextButton(
              onPressed: onOpenStatistics,
              child: const Text('Consulter dans la CTC'),
            ),
          ],
        ],
      ),
    );
  }
}

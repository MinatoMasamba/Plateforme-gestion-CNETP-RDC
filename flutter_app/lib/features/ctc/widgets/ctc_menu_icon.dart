import 'package:flutter/material.dart';

import '../../../theme/app_colors.dart';

/// Tracé Lucide `panel-left-close` du bouton HTML `sidebar-toggle-btn`.
class CtcMenuIcon extends StatelessWidget {
  const CtcMenuIcon({super.key});

  @override
  Widget build(BuildContext context) => const SizedBox(
    width: 16,
    height: 16,
    child: CustomPaint(painter: _PanelLeftPainter()),
  );
}

class _PanelLeftPainter extends CustomPainter {
  const _PanelLeftPainter();

  @override
  void paint(Canvas canvas, Size size) {
    canvas.scale(size.width / 24, size.height / 24);
    final stroke = Paint()
      ..color = AppColors.muted
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(3, 3, 18, 18),
        const Radius.circular(2),
      ),
      stroke,
    );
    canvas.drawLine(const Offset(9, 3), const Offset(9, 21), stroke);
    canvas.drawPath(
      Path()
        ..moveTo(16, 15)
        ..lineTo(13, 12)
        ..lineTo(16, 9),
      stroke,
    );
  }

  @override
  bool shouldRepaint(_PanelLeftPainter oldDelegate) => false;
}

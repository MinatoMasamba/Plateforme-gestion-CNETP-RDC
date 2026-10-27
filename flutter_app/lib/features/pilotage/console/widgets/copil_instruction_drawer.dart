import 'package:flutter/material.dart';
import '../../theme/copil_theme.dart';

Future<void> showCopilInstruction(BuildContext context, {bool global = true}) {
  final p = CopilTheme.of(context);
  return showGeneralDialog<void>(
    context: context,
    barrierDismissible: true,
    barrierLabel: 'Fermer',
    barrierColor: const Color(0x8C0F172A),
    pageBuilder: (context, animation, secondaryAnimation) => Align(
      alignment: Alignment.centerRight,
      child: Material(
        color: p.card,
        child: SizedBox(
          width: 520,
          height: double.infinity,
          child: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(
                          'Donner une instruction',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w700,
                            color: p.title,
                          ),
                        ),
                      ),
                      OutlinedButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('Fermer'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    global
                        ? 'Portée : toutes les sous-commissions et leurs groupes. L’envoi global, les pièces jointes, la récurrence et le suivi par destinataire sont non disponibles dans ce lot.'
                        : 'Portée : tous les groupes de cette sous-commission. Envoi et suivi par destinataire : Non disponible dans ce lot.',
                    style: TextStyle(
                      fontSize: 14,
                      height: 1.45,
                      color: p.muted,
                    ),
                  ),
                  const SizedBox(height: 20),
                  Chip(
                    label: const Text('Non disponible'),
                    backgroundColor: p.cardAlt,
                    side: BorderSide.none,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    ),
  );
}

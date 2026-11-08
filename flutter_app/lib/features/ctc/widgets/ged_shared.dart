import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../../theme/app_colors.dart';

/// Briques graphiques partagées de l'espace GED (poste 11) — style issu de
/// `templates/static/css/ged-workspace.css` et des libellés du template
/// `ctc/app/components/ged_workspace.html`.

class GedCard extends StatelessWidget {
  const GedCard({super.key, required this.child, this.padding = const EdgeInsets.all(20)});

  final Widget child;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: padding,
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: AppColors.border),
      boxShadow: const [BoxShadow(color: Color(0x0A0F1B2D), blurRadius: 18, offset: Offset(0, 6))],
    ),
    child: child,
  );
}

class GedSectionTitle extends StatelessWidget {
  const GedSectionTitle(this.title, this.icon, {super.key});

  final String title;
  final IconData icon;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      Icon(icon, size: 17, color: AppColors.rdcBlue),
      const SizedBox(width: 8),
      Expanded(
        child: Text(
          title,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w800,
            color: AppColors.text,
          ),
        ),
      ),
    ],
  );
}

class GedEmpty extends StatelessWidget {
  const GedEmpty(this.message, {super.key});

  final String message;

  @override
  Widget build(BuildContext context) => Text(
    message,
    style: const TextStyle(fontSize: 12, color: AppColors.muted),
  );
}

class GedKpi extends StatelessWidget {
  const GedKpi({super.key, required this.value, required this.label});

  final dynamic value;
  final String label;

  @override
  Widget build(BuildContext context) {
    final text = value is num ? '${(value as num).toInt()}' : (value ?? '—').toString();
    return SizedBox(
      width: 132,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            text,
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              letterSpacing: -0.5,
              color: AppColors.text,
            ),
          ),
          Text(
            label,
            style: const TextStyle(fontSize: 11, color: AppColors.muted),
          ),
        ],
      ),
    );
  }
}

class GedBadge extends StatelessWidget {
  const GedBadge({super.key, required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
    decoration: BoxDecoration(
      color: color.withValues(alpha: 0.12),
      borderRadius: BorderRadius.circular(999),
    ),
    child: Text(
      label,
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: color),
    ),
  );
}

class GedButton extends StatelessWidget {
  const GedButton({
    super.key,
    required this.label,
    required this.icon,
    required this.onTap,
    this.secondary = false,
    this.busy = false,
  });

  final String label;
  final IconData icon;
  final VoidCallback? onTap;
  final bool secondary;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final enabled = onTap != null && !busy;
    final background = secondary ? Colors.white : AppColors.rdcBlue;
    final foreground = secondary ? AppColors.rdcBlue : Colors.white;
    return Material(
      color: enabled ? background : (secondary ? background : background.withValues(alpha: 0.5)),
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        onTap: enabled ? onTap : null,
        borderRadius: BorderRadius.circular(10),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 8),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (busy)
                SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(strokeWidth: 2, color: foreground),
                )
              else
                Icon(icon, size: 15, color: foreground),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: foreground),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Liste des objets sérialisés d'une charge utile API.
List<Map<String, dynamic>> rowsOf(Object? payload) => [
  for (final item in payload is List ? payload : const [])
    if (item is Map) item.cast<String, dynamic>(),
];

String? asText(Object? value) {
  if (value == null) return null;
  final text = value.toString();
  return text.isEmpty ? null : text;
}

/// Date fr (jj/mm/aaaa) à partir d'un ISO `YYYY-MM-DD…`.
String frDate(Object? value) {
  final text = value?.toString() ?? '';
  if (text.length >= 10) return '${text.substring(8, 10)}/${text.substring(5, 7)}/${text.substring(0, 4)}';
  return '—';
}

/// Date + heure fr (jj/mm hh:mm) pour les journaux.
String frDateTime(Object? value) {
  final text = value?.toString() ?? '';
  if (text.length >= 16) {
    return '${text.substring(8, 10)}/${text.substring(5, 7)} · ${text.substring(11, 16)}';
  }
  return frDate(value);
}

/// Origine du dossier : « SC · Tome n · GT ».
String gedOrigin(Object? sc, Object? tome, Object? group) {
  final scText = asText(sc);
  final tone = asText(tome);
  final tomeText = tone == null ? null : (tone.startsWith('Tome') ? tone : 'Tome $tone');
  final groupText = asText(group);
  final parts = [
    ?scText,
    ?tomeText,
    ?groupText,
  ];
  return parts.isEmpty ? 'Origine à compléter' : parts.join(' · ');
}

/// Messages d'erreur serveur : détail plat ou liste de motifs.
String? errorDetail(DioException error) {
  final data = error.response?.data;
  if (data is Map) {
    final detail = data['detail'] ?? data['reasons'] ?? data['non_field_errors'];
    return flattenDetail(detail);
  }
  if (data is List) return flattenDetail(data);
  return error.message;
}

String? flattenDetail(Object? value) {
  if (value == null) return null;
  if (value is List) {
    return [
      for (final item in value)
        if (flattenDetail(item) != null) flattenDetail(item)!,
    ].join(' · ');
  }
  return value.toString();
}

// ─────────────────────────────────────────────────────────────────────────────
// Actions serveur partagées du workspace GED.
// ─────────────────────────────────────────────────────────────────────────────

sealed class GedAction {
  const GedAction();
}

class GedIndexAction extends GedAction {
  const GedIndexAction({
    required this.processId,
    required this.codeId,
    required this.sourceId,
    required this.baseVersionId,
    required this.verified,
    required this.observation,
    required this.metadata,
  });

  final int processId;
  final int? codeId;
  final int? sourceId;
  final int? baseVersionId;
  final bool verified;
  final String observation;
  final Map<String, String> metadata;
}

class GedUploadAction extends GedAction {
  const GedUploadAction({required this.processId});
  final int processId;
}

class GedAnomalyAction extends GedAction {
  const GedAnomalyAction({
    required this.processId,
    required this.kind,
    required this.comment,
    required this.recipientId,
  });

  final int processId;
  final String kind;
  final String comment;
  final int? recipientId;
}

class GedResolveAnomalyAction extends GedAction {
  const GedResolveAnomalyAction({
    required this.processId,
    required this.anomalyId,
    required this.comment,
  });

  final int processId;
  final int anomalyId;
  final String comment;
}

class GedCodeCheckAction extends GedAction {
  const GedCodeCheckAction({required this.code});
  final String code;
}

/// Écran d'échec explicite avec relance (aucun faux état).
class GedFailed extends StatelessWidget {
  const GedFailed({super.key, required this.title, required this.detail, required this.onRetry});

  final String title;
  final String detail;
  final void Function() onRetry;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(28),
      child: GedCard(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.cloud_off_outlined, color: AppColors.danger, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: AppColors.text),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(detail, style: const TextStyle(fontSize: 12, color: AppColors.muted)),
            const SizedBox(height: 14),
            GedButton(
              label: 'Réessayer',
              icon: Icons.refresh_outlined,
              onTap: onRetry,
            ),
          ],
        ),
      ),
    ),
  );
}

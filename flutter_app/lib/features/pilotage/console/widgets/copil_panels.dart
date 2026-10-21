import 'package:flutter/material.dart';
import '../../../../theme/app_colors.dart';

/// En-tête de section de panneau Copil (icône + titre + badge de compteur).
class PanelHeader extends StatelessWidget {
  const PanelHeader({
    super.key,
    required this.icon,
    required this.title,
    required this.color,
    this.count,
  });

  final IconData icon;
  final String title;
  final Color color;
  final int? count;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 15, color: color),
        const SizedBox(width: 8),
        Text(
          title.toUpperCase(),
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.4,
            color: color,
          ),
        ),
        if (count != null && count! > 0) ...[
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(999),
              border: Border.all(color: color.withValues(alpha: 0.3)),
            ),
            child: Text(
              '$count en attente',
              style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: color),
            ),
          ),
        ],
      ],
    );
  }
}

/// État vide générique d'un panneau.
class PanelEmpty extends StatelessWidget {
  const PanelEmpty({
    super.key,
    required this.icon,
    required this.color,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final Color color;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Column(
        children: [
          Icon(icon, size: 40, color: color.withValues(alpha: 0.4)),
          const SizedBox(height: 12),
          Text(
            title,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: AppColors.muted,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            subtitle,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 11.5, color: AppColors.subtle),
          ),
        ],
      ),
    );
  }
}

/// Carte d'action générique (icône + contenu + boutons à droite).
class PanelCard extends StatelessWidget {
  const PanelCard({
    super.key,
    required this.icon,
    required this.iconColor,
    required this.title,
    this.subtitle,
    this.trailing,
    this.child,
    this.actions,
  });

  final IconData icon;
  final Color iconColor;
  final String title;
  final String? subtitle;
  final Widget? trailing;
  final Widget? child;
  final Widget? actions;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: iconColor.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, size: 16, color: iconColor),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: AppColors.text,
                      ),
                    ),
                    if (subtitle != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        subtitle!,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 10, color: AppColors.subtle),
                      ),
                    ],
                  ],
                ),
              ),
              if (trailing != null) trailing!,
            ],
          ),
          if (child != null) ...[
            const SizedBox(height: 12),
            child!,
          ],
          if (actions != null) ...[
            const SizedBox(height: 14),
            Row(mainAxisAlignment: MainAxisAlignment.end, children: [actions!]),
          ],
        ],
      ),
    );
  }
}

class _SolidButton extends StatelessWidget {
  const _SolidButton({
    required this.label,
    required this.color,
    this.outline = false,
  });

  final String label;
  final Color color;
  final bool outline;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
      decoration: BoxDecoration(
        color: outline ? Colors.transparent : color,
        borderRadius: BorderRadius.circular(10),
        border: outline ? Border.all(color: color.withValues(alpha: 0.4)) : null,
      ),
      child: Text(
        label.toUpperCase(),
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.3,
          color: outline ? color : Colors.white,
        ),
      ),
    );
  }
}

/// Panneau Cadrage Directoire (Phases 1 & 2).
class CadragePanel extends StatelessWidget {
  const CadragePanel({super.key, this.items = const []});
  final List<CadrageItem> items;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const PanelEmpty(
        icon: Icons.explore_outlined,
        color: AppColors.rdcBlue,
        title: 'Aucune action de cadrage en attente',
        subtitle: 'Aucun dossier ne requiert votre intervention sur les Phases 1 ou 2 du Bureau Directoire.',
      );
    }
    return Column(
      children: [
        for (final item in items)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: PanelCard(
              icon: Icons.explore_outlined,
              iconColor: AppColors.rdcBlue,
              title: '${item.normeRef} — ${item.normeTitle}',
              subtitle: item.actionLabel,
              child: TextField(
                maxLines: 2,
                style: const TextStyle(fontSize: 11.5),
                decoration: InputDecoration(
                  hintText: item.hint,
                  hintStyle: const TextStyle(fontSize: 11.5, color: AppColors.subtle),
                  filled: true,
                  fillColor: const Color(0xFFF8FAFC),
                  contentPadding: const EdgeInsets.all(12),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
                  ),
                ),
              ),
              actions: _SolidButton(label: item.buttonLabel, color: AppColors.rdcBlue),
            ),
          ),
      ],
    );
  }
}

class CadrageItem {
  const CadrageItem({
    required this.normeRef,
    required this.normeTitle,
    required this.actionLabel,
    required this.hint,
    required this.buttonLabel,
  });
  final String normeRef;
  final String normeTitle;
  final String actionLabel;
  final String hint;
  final String buttonLabel;
}

/// Panneau Réception technique (Étape 5).
class ReceptionPanel extends StatelessWidget {
  const ReceptionPanel({super.key, this.items = const []});
  final List<ReceptionItem> items;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const PanelEmpty(
        icon: Icons.inbox_outlined,
        color: AppColors.success,
        title: 'Aucune norme en attente de réception',
        subtitle: 'Toutes les normes transmises par la CTC ont été réceptionnées.',
      );
    }
    return Column(
      children: [
        for (final item in items)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: PanelCard(
              icon: Icons.verified_outlined,
              iconColor: AppColors.success,
              title: '${item.normeRef} — ${item.normeTitle}',
              subtitle: item.signedBy,
              actions: _SolidButton(label: 'Accuser réception', color: AppColors.success),
            ),
          ),
      ],
    );
  }
}

class ReceptionItem {
  const ReceptionItem({
    required this.normeRef,
    required this.normeTitle,
    required this.signedBy,
  });
  final String normeRef;
  final String normeTitle;
  final String signedBy;
}

/// Panneau Demandes de dérogation.
class DerogationPanel extends StatelessWidget {
  const DerogationPanel({super.key, this.items = const []});
  final List<DerogationItem> items;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const PanelEmpty(
        icon: Icons.inbox_outlined,
        color: AppColors.success,
        title: 'Aucune demande en attente',
        subtitle: 'Toutes les demandes de dérogation ont été traitées.',
      );
    }
    return Column(
      children: [
        for (final item in items)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: PanelCard(
              icon: Icons.person_outline,
              iconColor: AppColors.rdcBlue,
              title: item.name,
              subtitle: '${item.structure} — ${item.date}',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'RESSOURCE DEMANDÉE',
                    style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: AppColors.rdcBlue),
                  ),
                  const SizedBox(height: 2),
                  Text(item.resource, style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w600, color: AppColors.text)),
                  const SizedBox(height: 8),
                  const Text('MOTIF', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: AppColors.subtle)),
                  const SizedBox(height: 2),
                  Text(item.reason, style: const TextStyle(fontSize: 10.5, color: AppColors.muted)),
                ],
              ),
              actions: Row(
                children: [
                  _SolidButton(label: 'Approuver', color: AppColors.success),
                  const SizedBox(width: 8),
                  _SolidButton(label: 'Refuser', color: AppColors.danger, outline: true),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

class DerogationItem {
  const DerogationItem({
    required this.name,
    required this.structure,
    required this.date,
    required this.resource,
    required this.reason,
  });
  final String name;
  final String structure;
  final String date;
  final String resource;
  final String reason;
}

/// Panneau Demandes d'adhésion.
class AdhesionsPanel extends StatelessWidget {
  const AdhesionsPanel({super.key, this.items = const []});
  final List<AdhesionItem> items;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const PanelEmpty(
        icon: Icons.inbox_outlined,
        color: AppColors.success,
        title: "Aucune demande d'adhésion en attente",
        subtitle: 'Tous les experts inscrits ont été traités.',
      );
    }
    return Column(
      children: [
        for (final item in items)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: PanelCard(
              icon: Icons.person_outline,
              iconColor: AppColors.rdcBlue,
              title: item.name,
              subtitle: '${item.email} · ${item.structure}',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Inscrit le ${item.date}',
                    style: const TextStyle(fontSize: 10, color: AppColors.subtle),
                  ),
                  if (item.specialties != null) ...[
                    const SizedBox(height: 6),
                    Text(
                      'Spécialités : ${item.specialties}',
                      style: const TextStyle(fontSize: 10, color: AppColors.muted),
                    ),
                  ],
                ],
              ),
              actions: Row(
                children: [
                  _SolidButton(label: 'Activer', color: AppColors.success),
                  const SizedBox(width: 8),
                  _SolidButton(label: 'Refuser', color: AppColors.danger, outline: true),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

class AdhesionItem {
  const AdhesionItem({
    required this.name,
    required this.email,
    required this.structure,
    required this.date,
    this.specialties,
  });
  final String name;
  final String email;
  final String structure;
  final String date;
  final String? specialties;
}

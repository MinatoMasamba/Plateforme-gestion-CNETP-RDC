import 'package:flutter/material.dart';

import '../../../theme/app_colors.dart';

typedef CtcRequestDecision =
    Future<void> Function(int id, String decision, String comment);

class CtcRequestsView extends StatefulWidget {
  const CtcRequestsView({
    super.key,
    required this.requests,
    required this.onDecision,
    required this.canReview,
    this.assistantPage = false,
  });

  final List<Map<String, dynamic>> requests;
  final CtcRequestDecision onDecision;
  final bool canReview;
  final bool assistantPage;

  @override
  State<CtcRequestsView> createState() => _CtcRequestsViewState();
}

class _CtcRequestsViewState extends State<CtcRequestsView> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final visible = widget.requests.where((item) {
      final searchable =
          '${item['restricted_resource'] ?? ''} ${item['requester'] ?? ''}'
              .toLowerCase();
      return searchable.contains(_query.toLowerCase());
    }).toList();
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 48),
      children: [
        Text(
          widget.assistantPage ? 'Assistant Exécutif' : 'Demandes à traiter',
          style: const TextStyle(
            fontSize: 26,
            fontWeight: FontWeight.w800,
            color: AppColors.text,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          widget.canReview
              ? 'Demandes opérationnelles attribuées à votre poste.'
              : "L'examen des demandes est réservé au poste Assistant Exécutif.",
          style: const TextStyle(fontSize: 13, color: AppColors.muted),
        ),
        const SizedBox(height: 20),
        Text(
          '${widget.requests.length} demande(s) en attente',
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w700,
            color: AppColors.rdcBlue,
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          onChanged: (value) => setState(() => _query = value),
          decoration: const InputDecoration(
            labelText: 'Rechercher',
            hintText: 'Objet ou émetteur',
            prefixIcon: Icon(Icons.search),
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 16),
        if (visible.isEmpty)
          const _EmptyRequests()
        else
          for (final item in visible)
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Material(
                color: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                  side: const BorderSide(color: AppColors.border),
                ),
                child: ListTile(
                  title: Text(
                    item['restricted_resource']?.toString() ?? '',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  subtitle: Text(
                    '${item['requester'] ?? ''} · ${item['status_label'] ?? 'En attente'}',
                  ),
                  trailing: widget.canReview
                      ? const Icon(
                          Icons.chevron_right,
                          color: AppColors.rdcBlue,
                        )
                      : null,
                  onTap: widget.canReview ? () => _openReview(item) : null,
                ),
              ),
            ),
      ],
    );
  }

  Future<void> _openReview(Map<String, dynamic> item) async {
    String comment = '';
    String? error;
    bool busy = false;
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (dialogContext, update) {
          Future<void> decide(String decision) async {
            update(() => busy = true);
            try {
              await widget.onDecision(
                item['id'] as int,
                decision,
                comment.trim(),
              );
              if (dialogContext.mounted) {
                Navigator.pop(dialogContext);
              }
            } catch (failure) {
              if (dialogContext.mounted) {
                update(() {
                  busy = false;
                  error = failure.toString().replaceFirst('Exception: ', '');
                });
              }
            }
          }

          return AlertDialog(
            title: Text(
              item['restricted_resource']?.toString() ?? 'Demande CTC',
            ),
            content: SizedBox(
              width: 480,
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${item['requester'] ?? ''} · ${item['status_label'] ?? ''}',
                      style: const TextStyle(color: AppColors.muted),
                    ),
                    const SizedBox(height: 18),
                    const Text(
                      'Motif',
                      style: TextStyle(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 6),
                    Text(item['reason']?.toString() ?? ''),
                    const SizedBox(height: 18),
                    TextField(
                      onChanged: (value) => comment = value,
                      maxLines: 3,
                      decoration: const InputDecoration(
                        labelText: 'Commentaire',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    if (error != null) ...[
                      const SizedBox(height: 10),
                      Text(
                        error!,
                        style: const TextStyle(color: AppColors.rdcRed),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            actions: [
              TextButton(
                onPressed: busy ? null : () => Navigator.pop(dialogContext),
                child: const Text('Fermer'),
              ),
              TextButton(
                onPressed: busy ? null : () => decide('REJECTED'),
                child: const Text('Refuser'),
              ),
              FilledButton(
                onPressed: busy ? null : () => decide('APPROVED'),
                child: const Text('Approuver'),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _EmptyRequests extends StatelessWidget {
  const _EmptyRequests();

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(30),
    decoration: BoxDecoration(
      color: Colors.white,
      border: Border.all(color: AppColors.border),
      borderRadius: BorderRadius.circular(14),
    ),
    child: const Text(
      'Aucune demande opérationnelle attribuée à ce poste.',
      style: TextStyle(color: AppColors.muted),
    ),
  );
}

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../../../core/api/api_client.dart';
import '../../theme/copil_theme.dart';
import 'copil_panels.dart';

/// Les mêmes dossiers et commandes que les panneaux du portail Django.
class CopilWorkflowPanel extends StatefulWidget {
  const CopilWorkflowPanel({
    super.key,
    required this.kind,
    required this.items,
    required this.onChanged,
  });
  final String kind;
  final List<Map<String, dynamic>> items;
  final Future<void> Function() onChanged;

  @override
  State<CopilWorkflowPanel> createState() => _CopilWorkflowPanelState();
}

class _CopilWorkflowPanelState extends State<CopilWorkflowPanel> {
  final Map<String, TextEditingController> _fields = {};
  final Set<int> _busy = {};
  final Map<int, String> _errors = {};

  TextEditingController field(int id, String key) =>
      _fields.putIfAbsent('$id-$key', TextEditingController.new);

  @override
  void dispose() {
    for (final controller in _fields.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> submit(Map<String, dynamic> item, String action) async {
    final id = item['id'] as int;
    final values = <String, dynamic>{'kind': widget.kind, 'id': id};
    if (widget.kind == 'derogation') {
      final comment = field(id, 'comment').text.trim();
      if (comment.isEmpty) {
        setState(
          () => _errors[id] = 'Veuillez rédiger une réponse au demandeur.',
        );
        return;
      }
      values.addAll({'decision': action, 'comment': comment});
    } else {
      values['action'] = action;
      for (final key in inputFields(item).keys) {
        values[key] = field(id, key).text.trim();
      }
    }
    setState(() {
      _busy.add(id);
      _errors.remove(id);
    });
    try {
      final response = await ApiClient.dio.post(
        '/api/v1/mobile/pilotage/command/',
        data: values,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            response.data['message'] as String? ?? 'Action enregistrée.',
          ),
        ),
      );
      await widget.onChanged();
    } on DioException catch (error) {
      if (!mounted) return;
      final body = error.response?.data;
      setState(
        () => _errors[id] = body is Map
            ? '${body['error'] ?? body['detail'] ?? 'Action impossible.'}'
            : 'Connexion impossible. Réessayez.',
      );
    } finally {
      if (mounted) setState(() => _busy.remove(id));
    }
  }

  Map<String, String> inputFields(Map<String, dynamic> item) {
    if (widget.kind == 'derogation') return {'comment': 'Réponse au demandeur'};
    if (widget.kind == 'adhesion') return {'reason': 'Motif du refus'};
    return switch (item['action']) {
      'open' => {'strategic_orientation': 'Orientations stratégiques'},
      'formalize_mandate' => {'operational_mandate': 'Mandat opérationnel'},
      'schedule' => {
        'deadline_ctm_review': 'Échéance CTM (AAAA-MM-JJ)',
        'deadline_ctc_handoff': 'Transmission CTC (AAAA-MM-JJ)',
        'deadline_pilotage_review': 'Revue Pilotage (AAAA-MM-JJ)',
      },
      'verify_pv' => {'pv_reference': 'Référence du procès-verbal'},
      'final_validate' => {
        'resolution_reference': 'Référence de la résolution',
      },
      'validate_onic' || 'validate_btp' => {'notes': 'Notes'},
      _ => {},
    };
  }

  @override
  Widget build(BuildContext context) {
    final p = CopilTheme.of(context);
    if (widget.items.isEmpty) {
      final (title, subtitle) = switch (widget.kind) {
        'cadrage' => (
          'Aucune action de cadrage en attente',
          'Aucun dossier ne requiert votre intervention sur les Phases 1 ou 2 du Bureau Directoire.',
        ),
        'reception' => (
          'Aucune norme en attente de réception',
          'Toutes les normes transmises par la CTC ont été réceptionnées.',
        ),
        'adhesion' => (
          "Aucune demande d’adhésion en attente",
          'Tous les experts inscrits ont été traités.',
        ),
        _ => (
          'Aucune demande en attente',
          'Toutes les demandes de dérogation ont été traitées.',
        ),
      };
      return PanelEmpty(
        icon: Icons.inbox_outlined,
        color: p.success,
        title: title,
        subtitle: subtitle,
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final item in widget.items) ...[
          Builder(
            builder: (context) {
              final id = item['id'] as int;
              final disabled = _busy.contains(id) || item['blocked'] == true;
              Widget button(
                String label,
                String action, {
                bool reject = false,
              }) => OutlinedButton(
                onPressed: disabled ? null : () => submit(item, action),
                style: OutlinedButton.styleFrom(
                  foregroundColor: reject ? p.danger : p.blue,
                ),
                child: Text(label),
              );
              return PanelCard(
                icon: widget.kind == 'cadrage'
                    ? Icons.explore_outlined
                    : Icons.inbox_outlined,
                iconColor: p.blue,
                title: item['reference'] != null
                    ? '${item['reference']} — ${item['title']}'
                    : '${item['name']}',
                subtitle:
                    '${item['label'] ?? item['signed_by'] ?? item['email'] ?? item['structure'] ?? ''}',
                body: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    if (item['resource'] != null)
                      Text(
                        '${item['resource']}\n${item['reason']}',
                        style: TextStyle(color: p.text, fontSize: 13),
                      ),
                    if (item['blocked'] == true)
                      Text(
                        'En attente de la transmission complète du dossier CTC.',
                        style: TextStyle(color: p.warning),
                      ),
                    for (final entry in inputFields(item).entries)
                      Padding(
                        padding: const EdgeInsets.only(top: 12),
                        child: TextField(
                          controller: field(id, entry.key),
                          minLines: 1,
                          maxLines: entry.key.startsWith('deadline') ? 1 : 3,
                          style: TextStyle(color: p.text, fontSize: 13),
                          decoration: InputDecoration(
                            labelText: entry.value,
                            filled: true,
                            fillColor: p.field,
                            border: const OutlineInputBorder(),
                          ),
                        ),
                      ),
                    if (_errors[id] != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Text(
                          _errors[id]!,
                          style: TextStyle(color: p.danger),
                        ),
                      ),
                    if (_busy.contains(id))
                      const Padding(
                        padding: EdgeInsets.only(top: 8),
                        child: LinearProgressIndicator(),
                      ),
                  ],
                ),
                actions: Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: switch (widget.kind) {
                    'reception' => [button('Accuser réception', 'receive')],
                    'adhesion' => [
                      button('Activer', 'activate'),
                      button('Refuser', 'reject', reject: true),
                    ],
                    'derogation' => [
                      button('Approuver', 'APPROVED'),
                      button('Refuser', 'REJECTED', reject: true),
                    ],
                    _ => [button('Valider', '${item['action']}')],
                  },
                ),
              );
            },
          ),
          const SizedBox(height: 12),
        ],
      ],
    );
  }
}

import 'package:flutter/material.dart';

import 'expert_module.dart';

class ExpertValidationTab extends StatelessWidget {
  const ExpertValidationTab({super.key, this.onOpenNorm});
  final ValueChanged<Map<String, dynamic>>? onOpenNorm;
  @override
  Widget build(BuildContext context) => ExpertModule(
    title: 'Processus ISO',
    endpoints: const {
      'Circuit': '/api/v1/legistic-reviews/workspace/',
      'Profil': '/api/v1/experts/me/',
    },
    builder: (s) {
      final publicOnly = s.values['publicOnly'] == true;
      final norms = expertRows(
        s.map('Circuit')['normes'],
      ).where((n) => !publicOnly || n['is_public'] == true).toList();
      final steps = expertRows(s.map('Circuit')['steps']);
      final staff = ['ADMIN', 'COORD_CTC'].contains(s.map('Profil')['role_id']);
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          s.button(
            publicOnly
                ? 'Afficher tout le circuit'
                : 'Portail public : normes consultables',
            () => s.change(() => s.values['publicOnly'] = !publicOnly),
            icon: Icons.public,
          ),
          const SizedBox(height: 12),
          if (norms.isEmpty && !s.errors.containsKey('Circuit'))
            s.card('Circuit normatif', [
              const Text('Aucune norme disponible.'),
            ]),
          for (final norm in norms)
            s.card('${norm['code']} — ${norm['title']}', [
              Text('${norm['status_label']} — ${norm['workflow_title']}'),
              Text('${norm['ctm'] ?? ''} / ${norm['wg'] ?? ''}'),
              Text(
                'Validation : ${expertMap(norm['votes'])['percent_for'] ?? 0} % (${expertMap(norm['votes'])['total'] ?? 0} votes)',
              ),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final step in steps)
                    Chip(
                      label: Text('${step['id']}. ${step['title']}'),
                      backgroundColor: step['id'] == norm['step']
                          ? s.p.blueSoft
                          : s.p.field,
                      labelStyle: TextStyle(color: s.p.text),
                    ),
                ],
              ),
              if (norm['ctc'] is Map) ...[
                const SizedBox(height: 10),
                Text('Circuit CTC : ${norm['ctc']['current_stage_label']}'),
                for (final stage in expertRows(norm['ctc']['stages']))
                  Text(
                    '${stage['done'] == true
                        ? '✓'
                        : stage['current'] == true
                        ? '→'
                        : '·'} ${stage['label']}',
                  ),
              ],
              s.actions([
                if (onOpenNorm != null)
                  s.button('Ouvrir dans l’éditeur', () => onOpenNorm!(norm)),
                s.button(
                  'Télécharger le PDF',
                  () => s.download(
                    '/api/v1/norms/${norm['id']}/pdf/',
                    'norme-${norm['id']}.pdf',
                  ),
                  icon: Icons.download,
                ),
                if (staff)
                  s.button(
                    'Changer la phase',
                    () => expertForm(
                      s,
                      'Phase réglementaire',
                      [
                        ExpertField(
                          'step',
                          'Nouvelle phase',
                          initial: '${norm['step']}',
                          choices: {
                            for (final step in steps)
                              '${step['id']}': '${step['title']}',
                          },
                        ),
                      ],
                      (values) => s.post('/api/v1/legistic-reviews/set-step/', {
                        'norme_id': norm['id'],
                        'step': int.parse(values['step']!),
                      }),
                    ),
                  ),
              ]),
            ]),
        ],
      );
    },
  );
}

class ExpertLegistiqueTab extends StatelessWidget {
  const ExpertLegistiqueTab({super.key});
  @override
  Widget build(BuildContext context) => ExpertModule(
    title: 'Bureau Légistique',
    endpoints: const {
      'Bureau': '/api/v1/legistic-reviews/legistique-workspace/',
    },
    builder: (s) {
      if (s.map('Bureau')['can_access'] != true) {
        return s.errors.isNotEmpty
            ? const SizedBox.shrink()
            : s.card('Accès réservé', [
                const Text(
                  'Le bureau légistique est réservé aux membres CTC autorisés par le serveur.',
                ),
              ]);
      }
      final reviews = expertRows(s.map('Bureau')['reviews']);
      return Column(
        children: [
          if (reviews.isEmpty)
            s.card('Toilettages', [const Text('Aucun toilettage en attente.')]),
          for (final review in reviews)
            s.card('${review['code']} — ${review['title']}', [
              Text(
                '${review['review_status_label']} — ${review['assigned_to'] ?? 'Non assigné'}',
              ),
              SelectableText('${review['comments'] ?? ''}'),
              s.actions([
                s.button(
                  'Consulter le texte',
                  () => s.details(
                    '${review['title']}',
                    SelectableText('${review['content'] ?? ''}'),
                  ),
                ),
                if (review['review_status'] == 'PENDING' ||
                    review['review_status'] == 'ASSIGNED')
                  s.button(
                    'M’assigner',
                    () => s.post(
                      '/api/v1/legistic-reviews/${review['review_id']}/assign-self/',
                    ),
                  ),
                s.button(
                  'Valider le toilettage CTC',
                  () => expertForm(
                    s,
                    'Validation légistique',
                    [
                      ExpertField(
                        'content',
                        'Texte révisé',
                        initial: '${review['content'] ?? ''}',
                        lines: 8,
                      ),
                      ExpertField(
                        'comments',
                        'Commentaire de relecture',
                        initial: '${review['comments'] ?? ''}',
                        lines: 3,
                      ),
                    ],
                    (values) => s.post(
                      '/api/v1/legistic-reviews/${review['review_id']}/validate-ctc/',
                      values,
                    ),
                  ),
                ),
              ]),
            ]),
        ],
      );
    },
  );
}

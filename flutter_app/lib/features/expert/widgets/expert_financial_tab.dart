import 'package:flutter/material.dart';

import '../../../core/api/api_client.dart';
import 'expert_module.dart';

String _contestationLabel(String? value) => switch (value) {
  'PENDING' => 'En attente d’instruction',
  'ACCEPTED' => 'Contestation acceptée',
  'REJECTED' => 'Contestation rejetée',
  _ => 'Aucune contestation',
};

class ExpertFinancialTab extends StatelessWidget {
  const ExpertFinancialTab({super.key});
  @override
  Widget build(BuildContext context) => ExpertModule(
    title: 'Cotisations & Indemnités',
    endpoints: const {
      'Tableau de bord': '/api/v1/cotisations/dashboard/',
      'Cotisations': '/api/v1/cotisations/',
      'Paiements': '/api/v1/paiements/',
      'Jetons': '/api/v1/jetons/',
      'Profil': '/api/v1/experts/me/',
    },
    builder: (s) {
      final dashboard = s.map('Tableau de bord');
      final staff = ['ADMIN', 'COORD_CTC'].contains(s.map('Profil')['role_id']);
      final expert = s.map('Profil')['id'];
      final jetons = s
          .rows('Jetons')
          .where((j) => staff || '${j['expert']}' == '$expert')
          .toList();
      final pendingJetons = jetons
          .where((j) => j['status'] == 'PENDING')
          .toList();
      final pendingTotal = pendingJetons.fold<double>(
        0,
        (total, jeton) => total + (double.tryParse('${jeton['montant']}') ?? 0),
      );
      return Column(
        children: [
          s.card('Situation financière', [
            Text('Montant perçu : ${dashboard['total_paye'] ?? '—'} USD'),
            Text(
              'Reste à percevoir : ${dashboard['total_en_attente'] ?? '—'} USD',
            ),
            Text(
              'Taux de recouvrement : ${dashboard['percentage_paye'] ?? '—'} %',
            ),
            Text(
              'Vos jetons en attente : ${jetons.where((j) => j['status'] == 'PENDING').length}',
            ),
          ]),
          for (final cot in s.rows('Cotisations'))
            s.card('${cot['structure_name']} — ${cot['annee']}', [
              Text('Cotisation : ${cot['montant']} USD — ${cot['status']}'),
              Text(
                'Payé : ${cot['montant_paye']} USD • Reste : ${cot['reste_payer']} USD',
              ),
              Text('Échéance : ${cot['due_date']}'),
              s.actions([
                if (cot['status'] != 'PAID')
                  s.button(
                    'Déclarer un paiement',
                    () => expertForm(
                      s,
                      'Déclarer un paiement',
                      [
                        const ExpertField('montant', 'Montant (USD)'),
                        const ExpertField(
                          'methode_paiement',
                          'Mode de paiement',
                          initial: 'VIREMENT',
                          choices: {
                            'VIREMENT': 'Virement bancaire',
                            'CHEQUE': 'Chèque',
                            'ESPECES': 'Espèces',
                            'MOBILE_MONEY': 'Mobile Money',
                            'AUTRE': 'Autre',
                          },
                        ),
                        ExpertField(
                          'payment_date',
                          'Date (AAAA-MM-JJ)',
                          initial: DateTime.now()
                              .toIso8601String()
                              .split('T')
                              .first,
                        ),
                        const ExpertField(
                          'numero_transaction',
                          'Référence de transaction',
                          required: false,
                        ),
                      ],
                      (values) async {
                        final amount = double.tryParse(
                          values['montant']!.replaceAll(',', '.'),
                        );
                        final date = DateTime.tryParse(values['payment_date']!);
                        if (amount == null ||
                            amount <= 0 ||
                            !amount.isFinite ||
                            date == null) {
                          s.notify(
                            'Le montant doit être positif et la date valide.',
                          );
                          return false;
                        }
                        return s.post('/api/v1/paiements/', {
                          ...values,
                          'cotisation': cot['id'],
                          'montant': values['montant']!.replaceAll(',', '.'),
                        });
                      },
                    ),
                    icon: Icons.payments_outlined,
                  ),
                s.button('Voir les paiements', () async {
                  await s.run(
                    () async {
                      final payments = await expertList(
                        '/api/v1/paiements/by_cotisation/?cotisation_id=${cot['id']}',
                      );
                      if (s.mounted) {
                        await s.details(
                          'Paiements — ${cot['structure_name']}',
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (payments.isEmpty)
                                const Text('Aucun paiement enregistré.'),
                              for (final p in payments)
                                ListTile(
                                  title: Text(
                                    '${p['numero_recu']} — ${p['montant']} USD',
                                  ),
                                  subtitle: Text(
                                    '${p['payment_date']} — ${p['status']}',
                                  ),
                                ),
                            ],
                          ),
                        );
                      }
                    },
                    success: 'Paiements consultés.',
                    reload: false,
                  );
                }),
                if (staff && cot['status'] != 'PAID')
                  s.button(
                    'Envoyer un rappel',
                    () => s.post(
                      '/api/v1/cotisations/${cot['id']}/send_reminder/',
                    ),
                  ),
              ]),
            ]),
          if (s.rows('Cotisations').isEmpty &&
              !s.errors.containsKey('Cotisations'))
            s.card('Cotisations', [
              const Text('Aucune cotisation enregistrée.'),
            ]),
          s.card('Paiements et reçus', [
            for (final payment in s.rows('Paiements'))
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${payment['numero_recu']} — ${payment['montant']} USD — ${payment['status']}',
                    ),
                    s.actions([
                      s.button(
                        'Détail du reçu',
                        () => s.run(
                          () async {
                            final response = await ApiClient.dio.get(
                              '/api/v1/paiements/${payment['id']}/',
                            );
                            final p = expertMap(response.data);
                            if (s.mounted) {
                              await s.details(
                                'Reçu ${p['numero_recu']}',
                                SelectableText(
                                  '${expertMap(p['cotisation_info'])['structure'] ?? ''}\n${p['montant']} USD\n${p['payment_date']}\n${p['methode_paiement']}\n${p['numero_transaction'] ?? ''}\n${p['status']}',
                                ),
                              );
                            }
                          },
                          success: 'Reçu consulté.',
                          reload: false,
                        ),
                      ),
                      s.button(
                        'Télécharger le reçu PDF',
                        () => s.download(
                          '/api/v1/paiements/${payment['id']}/receipt/',
                          'recu-${payment['numero_recu'] ?? payment['id']}.pdf',
                        ),
                        icon: Icons.picture_as_pdf_outlined,
                      ),
                      if (staff && payment['status'] == 'PENDING') ...[
                        s.button(
                          'Confirmer le paiement',
                          () => s.post(
                            '/api/v1/paiements/${payment['id']}/confirm/',
                          ),
                        ),
                        s.button(
                          'Rejeter le paiement',
                          () => s.post(
                            '/api/v1/paiements/${payment['id']}/reject/',
                          ),
                        ),
                      ],
                    ]),
                  ],
                ),
              ),
          ]),
          s.card(staff ? 'Jetons de présence' : 'Mes indemnités', [
            if (jetons.isEmpty && !s.errors.containsKey('Jetons'))
              const Text('Aucune indemnité enregistrée.'),
            for (final jeton in jetons)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${jeton['expert_name']} — ${jeton['montant']} USD — ${jeton['status']}',
                    ),
                    Text(
                      'Contestation : ${_contestationLabel('${jeton['contestation_status'] ?? 'NONE'}')}',
                    ),
                    if ('${jeton['contestation_motif'] ?? ''}'.isNotEmpty)
                      Text('Motif : ${jeton['contestation_motif']}'),
                    if ('${jeton['contestation_resolution'] ?? ''}'.isNotEmpty)
                      Text(
                        'Décision : ${jeton['contestation_resolution']}'
                        '${jeton['contestation_resolved_by_name'] == null ? '' : ' — ${jeton['contestation_resolved_by_name']}'}',
                      ),
                    Wrap(
                      spacing: 8,
                      children: [
                        s.button(
                          'Télécharger le reçu PDF',
                          () => s.download(
                            '/api/v1/jetons/${jeton['id']}/receipt/',
                            'indemnite-${jeton['id']}.pdf',
                          ),
                          icon: Icons.picture_as_pdf_outlined,
                        ),
                        if (staff && jeton['status'] == 'PENDING')
                          s.button(
                            'Liquider le jeton',
                            () => s.post(
                              '/api/v1/jetons/${jeton['id']}/mark_as_paid/',
                            ),
                          ),
                        if ('${jeton['expert']}' == '$expert' &&
                            jeton['contestation_status'] != 'PENDING')
                          s.button(
                            'Contester l’indemnité',
                            () => expertForm(
                              s,
                              'Contester l’indemnité',
                              [
                                const ExpertField(
                                  'motif',
                                  'Motif de la contestation',
                                  lines: 3,
                                ),
                              ],
                              (values) => s.post(
                                '/api/v1/jetons/${jeton['id']}/contest/',
                                values,
                              ),
                            ),
                            icon: Icons.report_outlined,
                          ),
                        if (staff && jeton['contestation_status'] == 'PENDING')
                          s.button(
                            'Instruire la contestation',
                            () => expertForm(
                              s,
                              'Instruction de la contestation',
                              [
                                const ExpertField(
                                  'decision',
                                  'Décision',
                                  initial: 'ACCEPTED',
                                  choices: {
                                    'ACCEPTED': 'Accepter la contestation',
                                    'REJECTED': 'Rejeter la contestation',
                                  },
                                ),
                                const ExpertField(
                                  'resolution',
                                  'Note d’instruction',
                                  lines: 3,
                                ),
                              ],
                              (values) => s.post(
                                '/api/v1/jetons/${jeton['id']}/resolve_contestation/',
                                values,
                              ),
                            ),
                            icon: Icons.fact_check_outlined,
                          ),
                      ],
                    ),
                  ],
                ),
              ),
          ]),
          if (staff)
            s.card('Mandatement bancaire', [
              Text(
                '${pendingJetons.length} indemnité(s) en attente — '
                '${pendingTotal.toStringAsFixed(2)} USD',
              ),
              const Text(
                'Le fichier pain.001 reprend les coordonnées bancaires de chaque '
                'expert. Les dossiers incomplets bloquent la génération.',
              ),
              if (pendingJetons.isNotEmpty)
                s.button(
                  'Générer le fichier pain.001',
                  () => s.download(
                    '/api/v1/jetons/sepa_export/',
                    'pain001-${DateTime.now().toIso8601String().split('T').first}.xml',
                  ),
                  icon: Icons.account_balance_outlined,
                )
              else
                const Text('Aucune indemnité en attente à mandater.'),
            ]),
        ],
      );
    },
  );
}

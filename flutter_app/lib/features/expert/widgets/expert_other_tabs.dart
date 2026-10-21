import 'package:flutter/material.dart';
import 'expert_editor_tab.dart' show ExpertColors;

Widget _card({required Widget child, EdgeInsets? padding}) => Container(
      padding: padding ?? const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: ExpertColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: ExpertColors.border),
      ),
      child: child,
    );

Widget _pageTitle(String eyebrow, String title, String subtitle) => Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(eyebrow.toUpperCase(),
            style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 1.2, color: ExpertColors.blue)),
        const SizedBox(height: 4),
        Text(title, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: ExpertColors.text)),
        const SizedBox(height: 4),
        Text(subtitle, style: const TextStyle(fontSize: 12, color: ExpertColors.muted)),
        const SizedBox(height: 18),
      ],
    );

Widget _kpi(String label, String value, Color color) => Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.07),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.22)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: color)),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(fontSize: 10, color: ExpertColors.muted)),
          ],
        ),
      ),
    );

Widget _pill(String text, Color color) => Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(999)),
      child: Text(text, style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: color)),
    );

// ───────────────────────────── HISTORIQUE ─────────────────────────────
class ExpertHistoryTab extends StatelessWidget {
  const ExpertHistoryTab({super.key});
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _pageTitle('Espace de travail', 'Historique des Modifications',
              'Comparez les versions et suivez les contributions des experts.'),
          Row(children: [
            _pill('Tous', ExpertColors.blue),
            const SizedBox(width: 8),
            _pill('Filtre actif : Collaborateur', ExpertColors.muted),
          ]),
          const SizedBox(height: 16),
          _card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: const [
                  Text('Analyse des différences', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: ExpertColors.text)),
                  Spacer(),
                  Text('Source : —   Cible : —', style: TextStyle(fontSize: 10, color: ExpertColors.subtle)),
                ]),
                const SizedBox(height: 12),
                Row(children: [
                  _pill('inchangé', ExpertColors.subtle),
                  const SizedBox(width: 8),
                  _pill('supprimé', ExpertColors.red),
                  const SizedBox(width: 8),
                  _pill('ajout', ExpertColors.blue),
                ]),
                const SizedBox(height: 12),
                Container(
                  height: 160,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: ExpertColors.surface,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: ExpertColors.border),
                  ),
                  child: const Text('Sélectionnez une version pour afficher les différences.',
                      style: TextStyle(fontSize: 11, color: ExpertColors.subtle)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────── EXPERTS & GROUPES ───────────────────────────
class ExpertExpertsTab extends StatelessWidget {
  const ExpertExpertsTab({super.key});
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _pageTitle('Co-gouvernance', 'Gestion de la Co-Gouvernance CNE-ITP',
              'Sélectionnez un Groupe de Travail (WG) ou un Expert dans la barre latérale.'),
          _card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  const Text('STATUT LOCAL', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, letterSpacing: 1, color: ExpertColors.subtle)),
                  const Spacer(),
                  _pill('Actif', ExpertColors.green),
                ]),
                const SizedBox(height: 10),
                const Text('Comité de Rapprochement : CTC Miroir RDC',
                    style: TextStyle(fontSize: 12, color: ExpertColors.muted)),
                const SizedBox(height: 4),
                const Text('Norme Directrice : ISO/CD National',
                    style: TextStyle(fontSize: 12, color: ExpertColors.muted)),
              ],
            ),
          ),
          const SizedBox(height: 14),
          Row(children: [
            Expanded(flex: 2, child: _card(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
              Text('Évolution des Normes de l\'Atelier', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: ExpertColors.text)),
              SizedBox(height: 6),
              Text('Livrables techniques en cours d\'évaluation.', style: TextStyle(fontSize: 11, color: ExpertColors.muted)),
              SizedBox(height: 14),
              Text('Membres Officiels (0)', style: TextStyle(fontSize: 11, color: ExpertColors.subtle)),
            ]))),
            const SizedBox(width: 14),
            Expanded(child: _card(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
              Text('Alignement Légistique', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: ExpertColors.text)),
              SizedBox(height: 6),
              Text('Tous les livrables transitent par une relecture du Secrétariat CTC RDC avant publication au Journal Officiel.',
                  style: TextStyle(fontSize: 11, height: 1.5, color: ExpertColors.muted)),
              SizedBox(height: 10),
              Text('Droit de vote réglementaire : Oui', style: TextStyle(fontSize: 11, color: ExpertColors.muted)),
              Text('Quorum Requis : 2/3 des votants', style: TextStyle(fontSize: 11, color: ExpertColors.muted)),
              Text('Période d\'enquête publique : 90 jours', style: TextStyle(fontSize: 11, color: ExpertColors.muted)),
            ]))),
          ]),
          const SizedBox(height: 14),
          _card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Indicateurs Clés de la Commission CNE-ITP RDC',
                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: ExpertColors.text)),
                const SizedBox(height: 12),
                Row(children: [
                  _kpi('Normes Actives', '25+', ExpertColors.blue),
                  const SizedBox(width: 10),
                  _kpi('Réunions Planifiées', '8', ExpertColors.green),
                  const SizedBox(width: 10),
                  _kpi('Experts', '200', ExpertColors.amber),
                ]),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────── RÉUNIONS & VOTES ───────────────────────────
class ExpertMeetingsTab extends StatelessWidget {
  const ExpertMeetingsTab({super.key});
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _pageTitle('CTM / WG', 'Réunions techniques & scrutin électronique',
              'Planification des réunions, émargement, vote électronique, clôture du scrutin et génération du PV.'),
          Row(children: [
            Expanded(child: _card(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
              Text('Planification verrouillée', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: ExpertColors.amber)),
              SizedBox(height: 6),
              Text('Votre rôle ne permet pas d\'initier une convocation officielle.',
                  style: TextStyle(fontSize: 11, color: ExpertColors.muted)),
              SizedBox(height: 12),
              Text('Planifier une session', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: ExpertColors.subtle)),
            ]))),
            const SizedBox(width: 14),
            Expanded(child: _card(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Votes par norme', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: ExpertColors.text)),
              const SizedBox(height: 10),
              _rowValue('Sujet', '—'),
              _rowValue('Quorum', '2/3'),
              _rowValue('Émargement', '0 / 0'),
              _rowValue('Vote', '—'),
              _rowValue('PV', '—'),
            ]))),
          ]),
          const SizedBox(height: 14),
          _card(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
            Text('Réunions', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: ExpertColors.text)),
            SizedBox(height: 10),
            Text('Aucune réunion planifiée.', style: TextStyle(fontSize: 11, color: ExpertColors.subtle)),
          ])),
        ],
      ),
    );
  }
}

Widget _rowValue(String label, String value) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(children: [
        Text(label, style: const TextStyle(fontSize: 11, color: ExpertColors.subtle)),
        const Spacer(),
        Text(value, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: ExpertColors.text)),
      ]),
    );

// ─────────────────────────── COTISATIONS ───────────────────────────
class ExpertFinancialTab extends StatelessWidget {
  const ExpertFinancialTab({super.key});
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _pageTitle('Portail financier', 'Portail de Gestion Financière CNE-ITP',
              'Perception des cotisations des 16 structures et liquidation des jetons de présence.'),
          Row(children: [
            _kpi('Trésor perçu', '0 \$', ExpertColors.green),
            const SizedBox(width: 10),
            _kpi('Quote-part restante', '0 \$', ExpertColors.amber),
            const SizedBox(width: 10),
            _kpi('Jetons en cours', '0', ExpertColors.blue),
            const SizedBox(width: 10),
            _kpi('Liquidations en attente', '0', ExpertColors.red),
          ]),
          const SizedBox(height: 16),
          Row(children: [
            Expanded(child: _card(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
              Text('Cotisations Structures (CNE-ITP-16)', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: ExpertColors.text)),
              SizedBox(height: 10),
              Text('Aucune cotisation enregistrée.', style: TextStyle(fontSize: 11, color: ExpertColors.subtle)),
            ]))),
            const SizedBox(width: 14),
            Expanded(child: _card(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
              Text('Double Taux Experts (Jetons / Recherche)', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: ExpertColors.text)),
              SizedBox(height: 10),
              Text('Espace Personnel d\'Indemnisation du Membre CNE-ITP.', style: TextStyle(fontSize: 11, color: ExpertColors.muted)),
            ]))),
          ]),
          const SizedBox(height: 14),
          _card(child: Row(children: const [
            Icon(Icons.description_outlined, size: 16, color: ExpertColors.blue),
            SizedBox(width: 8),
            Expanded(child: Text('Transfert de fonds XML pain.001.001.03 (RDC-CNE-ITP-STANDARD)',
                style: TextStyle(fontSize: 11, color: ExpertColors.muted))),
            SizedBox(width: 8),
            Text('REÇU D\'EFFETS D\'INDEMNITÉ · PDF', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: ExpertColors.blue)),
          ])),
        ],
      ),
    );
  }
}

// ─────────────────────── BIBLIOTHÈQUE / PROCESSUS ISO ───────────────────────
class ExpertValidationTab extends StatelessWidget {
  const ExpertValidationTab({super.key});
  @override
  Widget build(BuildContext context) {
    const steps = [
      'Rédaction', 'Relecture CTM', 'Validation CTC', 'Toilettage légistique',
      'Avis Ministère', 'Signature', 'Publication', 'Enquête publique',
      'Homologation', 'Diffusion', 'Archivage',
    ];
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _pageTitle('Modules 6 & 7', 'Bureau Légistique & Bibliothèque Publique',
              'Cycle de vie légistique en boucle fermée (11 étapes) et guichet public de consultation.'),
          _card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Suivi des phases réglementaires', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: ExpertColors.text)),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (int i = 0; i < steps.length; i++)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(
                          color: i < 3 ? ExpertColors.blue.withValues(alpha: 0.14) : ExpertColors.surface,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: i < 3 ? ExpertColors.blue.withValues(alpha: 0.35) : ExpertColors.border),
                        ),
                        child: Text('${i + 1}. ${steps[i]}',
                            style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600,
                                color: i < 3 ? ExpertColors.blue : ExpertColors.muted)),
                      ),
                  ],
                ),
                const SizedBox(height: 14),
                Row(children: const [
                  Text('Renvoyer au niveau précédent', style: TextStyle(fontSize: 11, color: ExpertColors.subtle)),
                  Spacer(),
                  Text('Promouvoir au niveau supérieur →', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: ExpertColors.blue)),
                ]),
              ],
            ),
          ),
          const SizedBox(height: 14),
          _card(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
            Text('Portail Public des Normes — Module 7', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: ExpertColors.text)),
            SizedBox(height: 6),
            Text('Guichet libre de relecture citoyenne. Téléchargez les versions intermédiaires ou définitives homologuées par le Ministère.',
                style: TextStyle(fontSize: 11, height: 1.5, color: ExpertColors.muted)),
            SizedBox(height: 12),
            Text('Ouvrir le Portail Public →', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: ExpertColors.blue)),
          ])),
        ],
      ),
    );
  }
}

// ─────────────────────────── LÉGISTIQUE ───────────────────────────
class ExpertLegistiqueTab extends StatelessWidget {
  const ExpertLegistiqueTab({super.key});
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _pageTitle('Accès restreint', 'Toilettage Légistique',
              'Normes en attente de conformité juridique (CTC).'),
          _card(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
            Row(children: [
              Icon(Icons.lock_outline, size: 16, color: ExpertColors.amber),
              SizedBox(width: 8),
              Text('Accès réservé aux conseillers juridiques', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: ExpertColors.amber)),
            ]),
            SizedBox(height: 8),
            Text('Les modifications apportées ici ne doivent concerner que la forme légistique et la numérotation (sans altérer le fond technique).',
                style: TextStyle(fontSize: 11, height: 1.5, color: ExpertColors.muted)),
          ])),
        ],
      ),
    );
  }
}

// ─────────────────────────── NOTIFICATIONS ───────────────────────────
class ExpertNotificationsTab extends StatelessWidget {
  const ExpertNotificationsTab({super.key});
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _pageTitle('Espace de travail', 'Notifications', 'Vos alertes et activités récentes.'),
          _card(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
            Text('Aucune notification pour le moment.', style: TextStyle(fontSize: 12, color: ExpertColors.muted)),
          ])),
        ],
      ),
    );
  }
}

// ─────────────────────────── PROFIL ───────────────────────────
class ExpertProfileTab extends StatelessWidget {
  const ExpertProfileTab({super.key});
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _pageTitle('Mon compte', 'Mon Profil Expert',
              'Mettez à jour vos informations personnelles et professionnelles.'),
          Row(children: [
            Expanded(flex: 2, child: _card(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
              Text('Fiche d\'Identité', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: ExpertColors.text)),
              SizedBox(height: 12),
              _ProfileField('Nom complet de l\'expert'),
              _ProfileField('Adresse courriel'),
              _ProfileField('Structure d\'affiliation'),
              _ProfileField('Téléphone'),
              _ProfileField('Spécialités (séparées par des virgules)'),
              _ProfileField('CTM (2 maximum)'),
              _ProfileField('Groupe de travail (WG)'),
            ]))),
            const SizedBox(width: 14),
            Expanded(child: Column(children: [
              _card(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
                Text('Coordonnées Financières', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: ExpertColors.text)),
                SizedBox(height: 12),
                _ProfileField('Mode de règlement (Equity BCDC)'),
                _ProfileField('Compte / Coordonnées'),
              ])),
              const SizedBox(height: 14),
              _card(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
                Text('Rôle et Permissions', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: ExpertColors.text)),
                SizedBox(height: 8),
                Text('Le rôle réglementaire est attribué par l\'administrateur du CNE-ITP et ne peut être modifié ici.',
                    style: TextStyle(fontSize: 11, height: 1.5, color: ExpertColors.muted)),
                SizedBox(height: 12),
                Text('Statistiques et Rémunération', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: ExpertColors.text)),
              ])),
            ])),
          ]),
        ],
      ),
    );
  }
}

class _ProfileField extends StatelessWidget {
  const _ProfileField(this.label);
  final String label;
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label.toUpperCase(),
              style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w700, letterSpacing: 0.6, color: ExpertColors.subtle)),
          const SizedBox(height: 5),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 10),
            decoration: BoxDecoration(
              color: ExpertColors.surface,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: ExpertColors.border),
            ),
            child: const Text('—', style: TextStyle(fontSize: 12, color: ExpertColors.muted)),
          ),
        ],
      ),
    );
  }
}

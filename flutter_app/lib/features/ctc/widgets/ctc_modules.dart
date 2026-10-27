import 'package:flutter/material.dart';

import '../../../theme/app_colors.dart';

/// Vues CTC secondaires, structurées d'après les écrans Django de référence.
/// Les valeurs métier absentes de l'API restent explicitement indisponibles :
/// aucune donnée financière ou décision n'est simulée.
class CtcModuleView extends StatelessWidget {
  const CtcModuleView({
    super.key,
    required this.view,
    required this.counts,
    required this.dossiers,
  });

  final String view;
  final Map<String, int> counts;
  final List<Map<String, dynamic>> dossiers;

  @override
  Widget build(BuildContext context) {
    switch (view) {
      case 'ctc_requests':
        return const _Requests();
      case 'assistant_executif':
        return const _Assistant();
      case 'financial':
        return const _Financial();
      case 'statistiques':
        return _Statistics(counts);
      case 'homologations':
        return const _SimpleTable(
          eyebrow: 'Supervision',
          title: 'Homologations',
          subtitle:
              'Consultation des normes homologuées ou publiées. Cette page ne signe aucune décision.',
          headers: ['DOSSIER', 'DÉCISION', 'PREUVE'],
          empty: 'Aucune norme homologuée enregistrée.',
        );
      case 'instructions':
        return const _Instructions();
      case 'reunions':
        return const _Unavailable();
      case 'drive':
        return _Drive(dossiers);
      case 'archives':
        return const _Archives();
      case 'parametres':
        return const _Settings();
      default:
        return const SizedBox.shrink();
    }
  }
}

class _Page extends StatelessWidget {
  const _Page(this.eyebrow, this.title, this.subtitle, this.child);
  final String eyebrow;
  final String title;
  final String subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    padding: const EdgeInsets.fromLTRB(30, 26, 30, 48),
    child: Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 1120),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              eyebrow,
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w800,
                color: AppColors.rdcBlue,
                letterSpacing: .6,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              title,
              style: const TextStyle(
                fontSize: 28,
                height: 1.05,
                fontWeight: FontWeight.w800,
                color: AppColors.text,
              ),
            ),
            const SizedBox(height: 7),
            Text(
              subtitle,
              style: const TextStyle(fontSize: 13, color: AppColors.muted),
            ),
            const SizedBox(height: 24),
            child,
          ],
        ),
      ),
    ),
  );
}

class _Card extends StatelessWidget {
  const _Card({
    required this.child,
    this.tint = Colors.white,
    this.padding = const EdgeInsets.all(20),
  });
  final Widget child;
  final Color tint;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: padding,
    decoration: BoxDecoration(
      color: tint,
      borderRadius: BorderRadius.circular(18),
      border: Border.all(color: AppColors.border),
      boxShadow: const [
        BoxShadow(
          color: Color(0x0A0F1B2D),
          blurRadius: 24,
          offset: Offset(0, 8),
        ),
      ],
    ),
    child: child,
  );
}

class _Requests extends StatefulWidget {
  const _Requests();
  @override
  State<_Requests> createState() => _RequestsState();
}

class _RequestsState extends State<_Requests> {
  String type = 'Demande opérationnelle';
  String status = 'En attente';

  @override
  Widget build(BuildContext context) => _Page(
    'Travail',
    'Demandes à traiter',
    "Demandes opérationnelles attribuées au poste. Les décisions d'étape restent contrôlées par le serveur.",
    Column(
      children: [
        const _Card(
          child: Align(
            alignment: Alignment.centerLeft,
            child: _Badge('Opérationnelles · 0'),
          ),
        ),
        const SizedBox(height: 18),
        LayoutBuilder(
          builder: (_, box) {
            final fields = <Widget>[
              _Drop('Type', type, const [
                'Demande opérationnelle',
                "Demande d'adhésion",
              ], (v) => setState(() => type = v)),
              _Drop('Statut', status, const [
                'En attente',
                'Traitée',
                'Toutes',
              ], (v) => setState(() => status = v)),
              const _Input('Rechercher', 'Objet ou émetteur'),
            ];
            return box.maxWidth < 700
                ? Column(
                    children: [
                      for (final f in fields)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: f,
                        ),
                    ],
                  )
                : Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      for (final f in fields)
                        Expanded(
                          child: Padding(
                            padding: const EdgeInsets.only(right: 12),
                            child: f,
                          ),
                        ),
                    ],
                  );
          },
        ),
        const SizedBox(height: 18),
        const _EmptyTable([
          'TYPE',
          'OBJET',
          'ÉMETTEUR',
          'DATE',
          'ÉCHÉANCE',
          'STATUT',
          'ACTION',
        ], 'Aucune demande opérationnelle attribuée à ce poste.'),
      ],
    ),
  );
}

class _Assistant extends StatelessWidget {
  const _Assistant();
  @override
  Widget build(BuildContext context) => _Page(
    'TRAVAIL · COORDINATION DU SECRÉTARIAT TECHNIQUE',
    'Assistant Exécutif',
    'Gestion des réceptions, arbitrage des demandes et suivi des transmissions.',
    Column(
      children: [
        const _ResponsiveCards(
          children: [
            _Metric(
              'EN ATTENTE',
              '0',
              'Demandes à traiter maintenant',
              Color(0xFF00AFA0),
            ),
            _Metric(
              'RÉCEPTION',
              'CTC',
              "Flux d'entrée de la Direction",
              Color(0xFFFFA000),
            ),
            _Metric(
              'PRIORITÉ',
              'Haute',
              'Tri, réponse, transmission',
              AppColors.rdcBlue,
            ),
          ],
        ),
        const SizedBox(height: 18),
        const _Card(
          child: _Section('RÉCEPTION TECHNIQUE', [
            _Tile('PRIORITÉ', 'Réception des dossiers entrants'),
            _Tile('ACTION', 'Valider ou rejeter les demandes'),
            _Tile('SUIVI', 'Notifications vers les requérants'),
          ]),
        ),
        const SizedBox(height: 18),
        const _Card(
          child: _Section('PROCÉDURE', [
            _Tile('1. RÉCEPTION', 'Identifier la demande et son auteur'),
            _Tile('2. DÉCISION', 'Approuver ou rejeter avec commentaire'),
            _Tile('3. NOTIFICATION', 'Informer immédiatement le requérant'),
            _Tile('4. TRAÇABILITÉ', 'Conserver la trace de la décision'),
          ]),
        ),
      ],
    ),
  );
}

class _Financial extends StatelessWidget {
  const _Financial();
  @override
  Widget build(BuildContext context) => const _Page(
    'ESPACE DU GESTIONNAIRE ADMINISTRATIF ET FINANCIER',
    'Budget & Comptabilité',
    'Suivi du budget opérationnel de la CTC, des cotisations et des dépenses de logistique.',
    Column(
      children: [
        _ResponsiveCards(
          children: [
            _Metric(
              'BUDGET DISPONIBLE',
              '—',
              'Données financières à connecter',
              Color(0xFF00B57A),
            ),
            _Metric('ENGAGÉ', '—', 'Aucune valeur simulée', Color(0xFFFFA000)),
            _Metric(
              'À LIQUIDER',
              '—',
              'Source serveur requise',
              Color(0xFF3478F6),
            ),
          ],
        ),
        SizedBox(height: 18),
        _Card(
          child: _Section('LIGNES BUDGÉTAIRES', [
            _Empty(
              Icons.account_balance_wallet_outlined,
              'Aucune ligne budgétaire reçue',
              "L'API financière n'est pas encore disponible.",
            ),
          ], purple: true),
        ),
        SizedBox(height: 18),
        _Card(
          child: _Section('GESTION DU BUDGET', [
            _Tile('RÔLE', 'Gestionnaire Administratif et Financier'),
            _Tile('PÉRIMÈTRE', 'Budget de fonctionnement CTC'),
          ], purple: true),
        ),
      ],
    ),
  );
}

class _Statistics extends StatelessWidget {
  const _Statistics(this.counts);
  final Map<String, int> counts;
  int get norms => counts['normes_suivies'] ?? 0;

  @override
  Widget build(BuildContext context) => _Page(
    'SUPERVISION · COORDINATION DU SECRÉTARIAT TECHNIQUE',
    'Suivi statistique',
    'Une vue des sous-commissions, groupes et normes rattachés explicitement.',
    Column(
      children: [
        _Card(
          tint: const Color(0xFFF5FCFF),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _Label("VUE D'ENSEMBLE"),
              const Text(
                'Statistique globale',
                style: TextStyle(fontSize: 23, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 6),
              const Text(
                'Les mesures utilisent seulement les tâches affectées explicitement.',
                style: TextStyle(color: AppColors.muted),
              ),
              const SizedBox(height: 22),
              Wrap(
                spacing: 54,
                runSpacing: 20,
                children: [
                  _Stat(
                    'Normes rattachées',
                    '$norms',
                    'Dans les groupes suivis',
                  ),
                  const _Stat(
                    'Sous-commissions et CTM',
                    '—',
                    'Référentiel à connecter',
                  ),
                  const _Stat(
                    'Groupes de travail',
                    '—',
                    'Rattachement explicite',
                  ),
                  _Stat(
                    'Tâches en retard',
                    '${counts['taches_en_retard'] ?? 0}',
                    'Selon leur échéance',
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        _Card(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _Label('PRODUCTION NORMATIVE'),
              const Text(
                'Normes par statut',
                style: TextStyle(fontSize: 19, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 20),
              Center(
                child: SizedBox(
                  width: 130,
                  height: 130,
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      const CircularProgressIndicator(
                        value: 1,
                        strokeWidth: 14,
                        color: Color(0xFF70B5FF),
                        backgroundColor: Color(0xFFEDF3F7),
                      ),
                      Center(
                        child: Text(
                          '$norms\nnormes',
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontWeight: FontWeight.w800),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

class _SimpleTable extends StatelessWidget {
  const _SimpleTable({
    required this.eyebrow,
    required this.title,
    required this.subtitle,
    required this.headers,
    required this.empty,
  });
  final String eyebrow, title, subtitle, empty;
  final List<String> headers;
  @override
  Widget build(BuildContext context) =>
      _Page(eyebrow, title, subtitle, _EmptyTable(headers, empty));
}

class _Instructions extends StatelessWidget {
  const _Instructions();
  @override
  Widget build(BuildContext context) => _Page(
    'TRAVAIL · COORDINATION DU SECRÉTARIAT TECHNIQUE',
    'Instructions',
    'Directives de production adressées aux sous-commissions (CTM).',
    Column(
      children: [
        const _Card(
          tint: Color(0xFFF5FCFF),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _Label('INSTRUCTION GÉNÉRALE'),
              Text(
                'Aucune instruction générale active',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
              ),
              SizedBox(height: 6),
              Text(
                "Les instructions apparaîtront ici dès qu'elles seront exposées par l'API.",
                style: TextStyle(color: AppColors.muted),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        const Align(
          alignment: Alignment.centerLeft,
          child: Text(
            'Sous-commissions (CTM)',
            style: TextStyle(fontSize: 19, fontWeight: FontWeight.w800),
          ),
        ),
        const SizedBox(height: 14),
        LayoutBuilder(
          builder: (_, box) => GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: 7,
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: box.maxWidth < 650
                  ? 1
                  : (box.maxWidth < 950 ? 2 : 3),
              childAspectRatio: 1.65,
              crossAxisSpacing: 14,
              mainAxisSpacing: 14,
            ),
            itemBuilder: (_, i) => _Card(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'CTM ${i + 1}',
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: AppColors.muted,
                    ),
                  ),
                  const SizedBox(height: 7),
                  const Text(
                    'Sous-commission technique',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800),
                  ),
                  const Spacer(),
                  const Divider(color: AppColors.border),
                  const Text(
                    'Aucune instruction reçue',
                    style: TextStyle(fontSize: 11, color: AppColors.muted),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    ),
  );
}

class _Unavailable extends StatelessWidget {
  const _Unavailable();
  @override
  Widget build(BuildContext context) => const _Page(
    'Outils',
    'Réunions',
    'Planification et convocations de la Coordination technique.',
    _Card(
      child: Padding(
        padding: EdgeInsets.symmetric(vertical: 24),
        child: _Empty(
          Icons.calendar_month_outlined,
          'Non disponible',
          "La création d'une réunion sera proposée lorsque le service d'enregistrement et d'envoi sera opérationnel.",
        ),
      ),
    ),
  );
}

class _Drive extends StatefulWidget {
  const _Drive(this.dossiers);
  final List<Map<String, dynamic>> dossiers;
  @override
  State<_Drive> createState() => _DriveState();
}

class _DriveState extends State<_Drive> {
  String query = '';
  @override
  Widget build(BuildContext context) {
    final rows = widget.dossiers.where(
      (d) => '${d['reference']} ${d['title']}'.toLowerCase().contains(
        query.toLowerCase(),
      ),
    );
    return _Page(
      'OUTILS DOCUMENTAIRES',
      'Espace Drive CNE-ITP',
      'Stockage partagé et centralisé des projets de normes.',
      Column(
        children: [
          _Card(
            padding: const EdgeInsets.all(12),
            child: Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                OutlinedButton.icon(
                  onPressed: () => _message(context),
                  icon: const Icon(Icons.create_new_folder_outlined),
                  label: const Text('Créer'),
                ),
                FilledButton.icon(
                  onPressed: () => _message(context),
                  icon: const Icon(Icons.cloud_upload_outlined),
                  label: const Text('Téléverser'),
                ),
                SizedBox(
                  width: 290,
                  child: TextField(
                    onChanged: (v) => setState(() => query = v),
                    decoration: const InputDecoration(
                      prefixIcon: Icon(Icons.search),
                      hintText: 'Rechercher dans le Drive',
                      isDense: true,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),
          _Card(
            padding: EdgeInsets.zero,
            child: Column(
              children: [
                const ListTile(
                  leading: Icon(Icons.check_box_outline_blank),
                  title: Text(
                    'Tous les fichiers',
                    style: TextStyle(fontWeight: FontWeight.w800),
                  ),
                  trailing: Text(
                    '0 sélectionné(s)',
                    style: TextStyle(fontSize: 11),
                  ),
                ),
                const Divider(height: 1, color: AppColors.border),
                if (rows.isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(28),
                    child: _Empty(
                      Icons.folder_open_outlined,
                      'Aucun fichier disponible',
                      "L'API Drive n'est pas encore connectée.",
                    ),
                  )
                else
                  for (final d in rows)
                    ListTile(
                      leading: const Icon(
                        Icons.picture_as_pdf_outlined,
                        color: Colors.redAccent,
                      ),
                      title: Text(
                        '${d['reference']} — ${d['title']}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      subtitle: Text('${d['stage_label'] ?? ''}'),
                    ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Archives extends StatelessWidget {
  const _Archives();
  @override
  Widget build(BuildContext context) => const _Page(
    'Système',
    'Archives',
    'Recherche dans les dossiers réellement archivés.',
    Column(
      children: [
        _ResponsiveCards(
          children: [
            _Input('Rechercher une norme archivée', 'Référence ou titre'),
            _Input('Archivée depuis le', 'jj/mm/aaaa'),
          ],
        ),
        SizedBox(height: 18),
        _EmptyTable([
          'RÉFÉRENCE',
          'NORME',
          'STATUT',
          'DERNIÈRE MISE À JOUR',
        ], 'Aucun dossier réellement archivé.'),
      ],
    ),
  );
}

class _Settings extends StatefulWidget {
  const _Settings();
  @override
  State<_Settings> createState() => _SettingsState();
}

class _SettingsState extends State<_Settings> {
  bool dark = false;
  final prefs = <String, bool>{
    'Notifications du système': true,
    'Actualités des normes': true,
    'Invitations aux réunions': true,
    'Votes': true,
    'Amendements': true,
    'Paiements': true,
  };
  @override
  Widget build(BuildContext context) => _Page(
    'Système',
    'Paramètres',
    'Préférences locales. La synchronisation serveur sera ajoutée avec le service dédié.',
    Column(
      children: [
        _Card(
          child: SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text(
              'Mode sombre',
              style: TextStyle(fontWeight: FontWeight.w700),
            ),
            subtitle: const Text(
              "Prévisualisation en attente de la bascule globale du thème.",
            ),
            value: dark,
            onChanged: (v) => setState(() => dark = v),
          ),
        ),
        const SizedBox(height: 18),
        _Card(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Notifications',
                style: TextStyle(fontSize: 19, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 4),
              const Text(
                'Ces choix sont conservés pendant cette session.',
                style: TextStyle(color: AppColors.muted),
              ),
              const SizedBox(height: 10),
              for (final p in prefs.entries)
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(p.key),
                  value: p.value,
                  onChanged: (v) => setState(() => prefs[p.key] = v),
                ),
            ],
          ),
        ),
      ],
    ),
  );
}

class _ResponsiveCards extends StatelessWidget {
  const _ResponsiveCards({required this.children});
  final List<Widget> children;
  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (_, box) => box.maxWidth < 700
        ? Column(
            children: [
              for (final c in children)
                Padding(padding: const EdgeInsets.only(bottom: 12), child: c),
            ],
          )
        : Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (final c in children)
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.only(right: 12),
                    child: c,
                  ),
                ),
            ],
          ),
  );
}

class _Metric extends StatelessWidget {
  const _Metric(this.label, this.value, this.note, this.color);
  final String label, value, note;
  final Color color;
  @override
  Widget build(BuildContext context) => Container(
    constraints: const BoxConstraints(minHeight: 115),
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: color.withValues(alpha: .06),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: color.withValues(alpha: .24)),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w800,
            color: color,
            letterSpacing: .8,
          ),
        ),
        const SizedBox(height: 10),
        Text(
          value,
          style: const TextStyle(fontSize: 25, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 5),
        Text(
          note,
          style: const TextStyle(fontSize: 11, color: AppColors.muted),
        ),
      ],
    ),
  );
}

class _Section extends StatelessWidget {
  const _Section(this.title, this.children, {this.purple = false});
  final String title;
  final List<Widget> children;
  final bool purple;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        title,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w800,
          color: purple ? const Color(0xFFA548F5) : const Color(0xFF00AFA0),
          letterSpacing: 1.7,
        ),
      ),
      const SizedBox(height: 18),
      Wrap(spacing: 12, runSpacing: 12, children: children),
    ],
  );
}

class _Tile extends StatelessWidget {
  const _Tile(this.label, this.text);
  final String label, text;
  @override
  Widget build(BuildContext context) => Container(
    width: 310,
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: const Color(0xFFF8FAFD),
      borderRadius: BorderRadius.circular(14),
      border: Border.all(color: AppColors.border),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w800,
            color: AppColors.subtle,
            letterSpacing: .7,
          ),
        ),
        const SizedBox(height: 7),
        Text(
          text,
          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
        ),
      ],
    ),
  );
}

class _Stat extends StatelessWidget {
  const _Stat(this.label, this.value, this.note);
  final String label, value, note;
  @override
  Widget build(BuildContext context) => SizedBox(
    width: 190,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w700,
            color: AppColors.muted,
          ),
        ),
        const SizedBox(height: 5),
        Text(
          value,
          style: const TextStyle(fontSize: 31, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 4),
        Text(
          note,
          style: const TextStyle(fontSize: 11, color: AppColors.muted),
        ),
      ],
    ),
  );
}

class _Label extends StatelessWidget {
  const _Label(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 4),
    child: Text(
      text,
      style: const TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w800,
        color: AppColors.rdcBlue,
        letterSpacing: .7,
      ),
    ),
  );
}

class _Badge extends StatelessWidget {
  const _Badge(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
    decoration: BoxDecoration(
      color: const Color(0xFFE9EEF5),
      borderRadius: BorderRadius.circular(99),
    ),
    child: Text(
      text,
      style: const TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w800,
        color: AppColors.muted,
      ),
    ),
  );
}

class _Drop extends StatelessWidget {
  const _Drop(this.label, this.value, this.items, this.changed);
  final String label, value;
  final List<String> items;
  final ValueChanged<String> changed;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        label,
        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
      ),
      const SizedBox(height: 6),
      DropdownButtonFormField<String>(
        initialValue: value,
        isDense: true,
        items: [
          for (final i in items) DropdownMenuItem(value: i, child: Text(i)),
        ],
        onChanged: (v) {
          if (v != null) changed(v);
        },
      ),
    ],
  );
}

class _Input extends StatelessWidget {
  const _Input(this.label, this.hint);
  final String label, hint;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        label,
        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
      ),
      const SizedBox(height: 6),
      TextField(decoration: InputDecoration(hintText: hint, isDense: true)),
    ],
  );
}

class _EmptyTable extends StatelessWidget {
  const _EmptyTable(this.headers, this.message);
  final List<String> headers;
  final String message;
  @override
  Widget build(BuildContext context) => _Card(
    padding: EdgeInsets.zero,
    child: Column(
      children: [
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SizedBox(
            width: 900,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              child: Row(
                children: [
                  for (final h in headers)
                    Expanded(
                      child: Text(
                        h,
                        style: const TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          color: AppColors.muted,
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
        const Divider(height: 1, color: AppColors.border),
        Padding(
          padding: const EdgeInsets.all(16),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Text(
              message,
              style: const TextStyle(color: AppColors.muted),
            ),
          ),
        ),
      ],
    ),
  );
}

class _Empty extends StatelessWidget {
  const _Empty(this.icon, this.title, this.subtitle);
  final IconData icon;
  final String title, subtitle;
  @override
  Widget build(BuildContext context) => SizedBox(
    width: 620,
    child: Column(
      children: [
        Icon(icon, size: 30, color: AppColors.subtle),
        const SizedBox(height: 9),
        Text(
          title,
          textAlign: TextAlign.center,
          style: const TextStyle(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 5),
        Text(
          subtitle,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 12, color: AppColors.muted),
        ),
      ],
    ),
  );
}

void _message(BuildContext context) =>
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text("Le service Drive n'est pas encore disponible."),
      ),
    );

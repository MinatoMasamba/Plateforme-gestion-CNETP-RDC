import 'package:flutter/material.dart';

import '../../../theme/app_colors.dart';
import 'ged_shared.dart';

/// Panneau « Dossiers à indexer » du poste 11 — sections `data-ged-panel="work"`
/// de `ged_workspace.html` : file filtrée, fiche de vérification (contrôle des
/// pièces, métadonnées, indexation), anomalies et suite du dossier.

const _queueStateLabels = {
  'READY': 'À vérifier',
  'REPORT': 'Rapport attendu',
  'BLOCKED': 'Bloqué',
  'CORRECTION': 'À corriger',
  'INDEXED': 'Indexé · à confirmer',
  'CONFIRMED': 'Confirmé',
};

const _queueStateColors = {
  'READY': AppColors.warning,
  'REPORT': AppColors.indigo,
  'BLOCKED': AppColors.danger,
  'CORRECTION': AppColors.danger,
  'INDEXED': AppColors.rdcBlue,
  'CONFIRMED': AppColors.success,
};

const _anomalyKinds = <String, String>{
  'MISSING_FILE': 'Fichier manquant',
  'CORRUPT': 'Fichier corrompu',
  'MISFILED': 'Pièce mal classée',
  'INCONSISTENT': 'Information incohérente',
};

class GedWorkPanel extends StatelessWidget {
  const GedWorkPanel({
    super.key,
    required this.data,
    required this.queue,
    required this.queueTotal,
    required this.detailId,
    required this.states,
    required this.search,
    required this.busy,
    required this.onSelect,
    required this.onToggleState,
    required this.onClearFilters,
    required this.onSearch,
    required this.onAction,
  });

  final Map<String, dynamic> data;
  final List<Map<String, dynamic>> queue;
  final int queueTotal;
  final int? detailId;
  final Set<String> states;
  final TextEditingController search;
  final bool busy;
  final ValueChanged<Map<String, dynamic>> onSelect;
  final void Function(String state) onToggleState;
  final void Function() onClearFilters;
  final void Function() onSearch;
  final void Function(GedAction action) onAction;

  Map<String, dynamic>? get detailRow {
    final id = detailId;
    if (id == null) return null;
    for (final row in queue) {
      if (row['id'] == id) return row;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final hasFilter =
        states.isNotEmpty || search.text.isNotEmpty;
    final selected = detailRow;
    return LayoutBuilder(
      builder: (context, box) {
        final sideBySide = box.maxWidth >= 1060;
        final queueColumn = Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            GedCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          'Dossiers à indexer${queueTotal > 0 ? ' · $queueTotal' : ''}',
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w800,
                            color: AppColors.text,
                          ),
                        ),
                      ),
                      if (hasFilter)
                        TextButton(onPressed: onClearFilters, child: const Text('Réinitialiser les filtres')),
                    ],
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: search,
                    decoration: InputDecoration(
                      isDense: true,
                      prefixIcon: const Icon(Icons.search, size: 18),
                      hintText: 'Référence, titre, tome ou code…',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    onSubmitted: (_) => onSearch(),
                  ),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: [
                      for (final entry in _queueStateLabels.entries)
                        FilterChip(
                          label: Text(
                            entry.value,
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: states.contains(entry.key) ? Colors.white : AppColors.muted,
                            ),
                          ),
                          selected: states.contains(entry.key),
                          selectedColor: AppColors.rdcBlue,
                          showCheckmark: false,
                          side: const BorderSide(color: AppColors.border),
                          onSelected: (_) => onToggleState(entry.key),
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${queue.length} dossier(s) affiché(s) · file du poste 11',
                    style: const TextStyle(fontSize: 11, color: AppColors.subtle),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),
            if (queue.isEmpty)
              const GedCard(
                child: GedEmpty('Aucun dossier dans la file pour ces filtres.'),
              )
            else
              for (final row in queue.take(14))
                Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: _QueueRowCard(row: row, selected: selected != null && row['id'] == selected['id'], onTap: () => onSelect(row)),
                ),
          ],
        );
        final fiche = selected == null
            ? GedCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.touch_app_outlined, size: 17, color: AppColors.rdcBlue),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Choisissez un dossier dans la file pour vérifier ses conditions réelles et préparer l’indexation.',
                            style: const TextStyle(fontSize: 12, color: AppColors.muted),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'Étapes de vérification du poste 11',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: AppColors.text),
                    ),
                    const SizedBox(height: 6),
                    const GedEmpty('1. Contrôler les pièces  2. Corriger les métadonnées  3. Enregistrer l’indexation.'),
                  ],
                ),
              )
            : _WorkFiche(
                key: ValueKey('fiche-${(selected['id'] as num).toInt()}-${selected['base_version_id'] ?? 0}'),
                row: selected,
                data: data,
                busy: busy,
                onAction: onAction,
              );
        if (sideBySide) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(flex: 5, child: queueColumn),
              const SizedBox(width: 16),
              Expanded(flex: 7, child: fiche),
            ],
          );
        }
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            queueColumn,
            const SizedBox(height: 16),
            fiche,
          ],
        );
      },
    );
  }
}

class _QueueRowCard extends StatelessWidget {
  const _QueueRowCard({
    required this.row,
    required this.selected,
    required this.onTap,
  });

  final Map<String, dynamic> row;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final state = (row['queue_state'] ?? 'READY').toString();
    final age = row['age_days'];
    final ageLabel = age is num && age > 0 ? ' · ${age.toStringAsFixed(0)} j' : '';
    final origin = gedOrigin(row['sc'], row['tome'], row['group']);
    return Material(
      color: selected ? AppColors.rdcBlue.withValues(alpha: 0.06) : Colors.white,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: selected ? AppColors.rdcBlue : AppColors.border,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      (row['reference'] ?? '').toString(),
                      style: const TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 12,
                        fontWeight: FontWeight.w800,
                        color: AppColors.text,
                      ),
                    ),
                  ),
                  GedBadge(
                    label: _queueStateLabels[state] ?? state,
                    color: _queueStateColors[state] ?? AppColors.warning,
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                (row['title'] ?? '').toString(),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.text),
              ),
              const SizedBox(height: 3),
              Text(
                '$origin$ageLabel · ${row['eligible'] == true ? 'admissible' : 'visible'}',
                style: const TextStyle(fontSize: 11, color: AppColors.muted),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Fiche de vérification et d'indexation du dossier sélectionné.
// ─────────────────────────────────────────────────────────────────────────────

class _WorkFiche extends StatefulWidget {
  const _WorkFiche({
    super.key,
    required this.row,
    required this.data,
    required this.busy,
    required this.onAction,
  });

  final Map<String, dynamic> row;
  final Map<String, dynamic> data;
  final bool busy;
  final void Function(GedAction action) onAction;

  @override
  State<_WorkFiche> createState() => _WorkFicheState();
}

class _WorkFicheState extends State<_WorkFiche> {
  late final int _processId = (widget.row['id'] as num).toInt();
  late int? _codeId = _initialCodeId();
  late int? _sourceId = _initialSourceId();
  late bool _pvChecked = false;
  late bool _reportChecked = false;
  late bool _verified = false;
  String _anomalyKind = 'INCONSISTENT';
  int? _recipientId;
  final _observation = TextEditingController();
  final _anomalyComment = TextEditingController();
  bool _anomalyFormOpen = false;
  late final Map<String, TextEditingController> _metadata = _buildMetadata();

  String _metadataDefault(String key, {String fallback = ''}) {
    final latest = widget.row['latest'];
    final stored = latest is Map && latest['metadata'] is Map
        ? (latest['metadata'] as Map)[key]
        : null;
    if (stored is String && stored.isNotEmpty) return stored;
    final fallbackValue = widget.row[key];
    if (fallbackValue == null) return fallback;
    final text = fallbackValue.toString();
    if (text.isEmpty) return fallback;
    if (key == 'received_at' && text.length >= 10) return text.substring(0, 10);
    if (key == 'tome') return text.startsWith('Tome') ? text : 'Tome $text';
    return text;
  }

  Map<String, TextEditingController> _buildMetadata() {
    return {
      'reference': TextEditingController(text: _metadataDefault('reference')),
      'version': TextEditingController(text: _metadataDefault('version')),
      'title': TextEditingController(text: _metadataDefault('title')),
      'tome': TextEditingController(text: _metadataDefault('tome')),
      'sc': TextEditingController(text: _metadataDefault('sc')),
      'group': TextEditingController(text: _metadataDefault('group')),
      'vote_date': TextEditingController(text: _metadataDefault('vote_date')),
      'received_at': TextEditingController(text: _metadataDefault('received_at')),
      'sender': TextEditingController(text: _metadataDefault('sender')),
    };
  }

  int? _initialCodeId() {
    final codes = rowsOf(widget.data['codes']).where(
      (item) => item['norme_id'] == widget.row['norme_id'],
    );
    if (codes.isEmpty) return null;
    return (codes.first['id'] as num).toInt();
  }

  int? _initialSourceId() {
    final files = rowsOf(widget.row['files']);
    if (files.isEmpty) return null;
    return (files.first['id'] as num).toInt();
  }

  @override
  void dispose() {
    for (final controller in _metadata.values) {
      controller.dispose();
    }
    _observation.dispose();
    _anomalyComment.dispose();
    super.dispose();
  }

  String get _stateLabel {
    final state = (widget.row['queue_state'] ?? 'READY').toString();
    return _queueStateLabels[state] ?? state;
  }

  Color get _stateColor {
    final state = (widget.row['queue_state'] ?? 'READY').toString();
    return _queueStateColors[state] ?? AppColors.warning;
  }

  List<String> get _blockers =>
      [for (final item in widget.row['blockers'] as List? ?? const []) item.toString()];

  @override
  Widget build(BuildContext context) {
    final stateKey = (widget.row['queue_state'] ?? 'READY').toString();
    final indexed = stateKey == 'INDEXED' || stateKey == 'CONFIRMED';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _FicheHeader(row: widget.row, stateLabel: _stateLabel, stateColor: _stateColor),
        const SizedBox(height: 12),
        _PiecesCard(
          blockers: _blockers,
          pvPresent: widget.row['pv_present'] == true,
          report: widget.row['report'] is Map ? (widget.row['report'] as Map).cast<String, dynamic>() : null,
          pvChecked: _pvChecked,
          reportChecked: _reportChecked,
          onPvChanged: (value) => setState(() => _pvChecked = value ?? false),
          onReportChanged: (value) => setState(() => _reportChecked = value ?? false),
        ),
        const SizedBox(height: 12),
        if (!indexed) ...[
          _MetadataCard(controllers: _metadata),
          const SizedBox(height: 12),
          _IndexCard(
            state: this,
            codeId: _codeId,
            sourceId: _sourceId,
            verified: _verified,
            observation: _observation,
            busy: widget.busy,
            onSubmit: _submitIndex,
          ),
          const SizedBox(height: 12),
        ],
        _SuiteCard(
          state: this,
          anomalies: rowsOf(widget.row['anomalies']),
          busy: widget.busy,
        ),
      ],
    );
  }

  void selectCode(int? value) => setState(() => _codeId = value);

  void selectSource(int? value) => setState(() => _sourceId = value);

  void setVerified(bool value) => setState(() => _verified = value);

  void toggleAnomalyForm() => setState(() => _anomalyFormOpen = !_anomalyFormOpen);

  void selectAnomalyKind(String? value) =>
      setState(() => _anomalyKind = value ?? 'INCONSISTENT');

  void selectRecipient(int? value) => setState(() => _recipientId = value);

  void _submitIndex() {
    final nextVersion = (widget.row['next_version'] as num?)?.toInt() ?? 1;
    final metadata = {
      for (final entry in _metadata.entries) entry.key: entry.value.text.trim(),
    };
    metadata['version'] = 'v$nextVersion · nouvelle version';
    widget.onAction(
      GedIndexAction(
        processId: _processId,
        codeId: _codeId,
        sourceId: _sourceId,
        baseVersionId: (widget.row['base_version_id'] as num?)?.toInt() ?? 0,
        verified: _verified,
        observation: _observation.text.trim(),
        metadata: metadata,
      ),
    );
  }

  void _submitAnomaly() {
    widget.onAction(
      GedAnomalyAction(
        processId: _processId,
        kind: _anomalyKind,
        comment: _anomalyComment.text.trim(),
        recipientId: _recipientId,
      ),
    );
    setState(() => _anomalyFormOpen = false);
  }

  void _resolveAnomaly(int anomalyId) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Résoudre l’anomalie'),
        content: TextField(
          controller: controller,
          autofocus: true,
          maxLines: 3,
          decoration: const InputDecoration(hintText: 'Commentaire de résolution…'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(dialogContext).pop(), child: const Text('Annuler')),
          FilledButton(
            onPressed: () {
              Navigator.of(dialogContext).pop();
              widget.onAction(
                GedResolveAnomalyAction(
                  processId: _processId,
                  anomalyId: anomalyId,
                  comment: controller.text.trim(),
                ),
              );
            },
            child: const Text('Enregistrer'),
          ),
        ],
      ),
    );
  }
}

class _FicheHeader extends StatelessWidget {
  const _FicheHeader({required this.row, required this.stateLabel, required this.stateColor});

  final Map<String, dynamic> row;
  final String stateLabel;
  final Color stateColor;

  @override
  Widget build(BuildContext context) => GedCard(
    child: Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                (row['reference'] ?? '').toString(),
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                  color: AppColors.rdcBlue,
                ),
              ),
              Text(
                (row['title'] ?? '').toString(),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: AppColors.text),
              ),
              Text(
                '${gedOrigin(row['sc'], row['tome'], row['group'])} · émetteur ${row['sender'] ?? '—'}',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 11, color: AppColors.muted),
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        GedBadge(label: stateLabel, color: stateColor),
      ],
    ),
  );
}

class _PiecesCard extends StatelessWidget {
  const _PiecesCard({
    required this.blockers,
    required this.pvPresent,
    required this.report,
    required this.pvChecked,
    required this.reportChecked,
    required this.onPvChanged,
    required this.onReportChanged,
  });

  final List<String> blockers;
  final bool pvPresent;
  final Map<String, dynamic>? report;
  final bool pvChecked;
  final bool reportChecked;
  final ValueChanged<bool?> onPvChanged;
  final ValueChanged<bool?> onReportChanged;

  @override
  Widget build(BuildContext context) {
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GedSectionTitle('Contrôle des pièces', Icons.fact_check_outlined),
          const SizedBox(height: 10),
          if (blockers.isEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.success.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Text(
                'Toutes les conditions documentaires sont réunies ; préparez l’indexation.',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Color(0xFF166534)),
              ),
            )
          else ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.danger.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.lock_outline, size: 15, color: AppColors.danger),
                      SizedBox(width: 6),
                      Text(
                        'Indexation verrouillée',
                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: AppColors.danger),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  for (final blocker in blockers)
                    Text(
                      '· $blocker',
                      style: const TextStyle(fontSize: 12, color: AppColors.danger),
                    ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 10),
          Material(
            type: MaterialType.transparency,
            child: CheckboxListTile(
              dense: true,
              value: pvChecked,
              onChanged: onPvChanged,
              controlAffinity: ListTileControlAffinity.leading,
              contentPadding: EdgeInsets.zero,
              title: Text(
                pvPresent ? 'PV consulté' : 'PV consulté — pièce absente',
                style: const TextStyle(fontSize: 12, color: AppColors.text),
              ),
            ),
          ),
          Material(
            type: MaterialType.transparency,
            child: CheckboxListTile(
              dense: true,
              value: reportChecked,
              onChanged: onReportChanged,
              controlAffinity: ListTileControlAffinity.leading,
              contentPadding: EdgeInsets.zero,
              title: Text(
                report == null
                    ? 'Rapport de revue vérifié — pièce attendue'
                    : 'Rapport de revue vérifié · ${asText(report!['name']) ?? ''} · ${((report!['size'] ?? 0) as num)} o',
                style: const TextStyle(fontSize: 12, color: AppColors.text),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MetadataCard extends StatelessWidget {
  const _MetadataCard({required this.controllers});

  final Map<String, TextEditingController> controllers;

  @override
  Widget build(BuildContext context) {
    Widget field(String key, String label, {bool wide = false, String? hint}) {
      return SizedBox(
        width: wide ? double.infinity : 220,
        child: TextField(
          controller: controllers[key],
          style: const TextStyle(fontSize: 13),
          decoration: InputDecoration(
            isDense: true,
            labelText: label,
            hintText: hint,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
          ),
        ),
      );
    }
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GedSectionTitle('Métadonnées documentaires', Icons.edit_note_outlined),
          const SizedBox(height: 4),
          const Text(
            'Corrigez les champs avant de confirmer l’indexation. La réception d’origine reste conservée.',
            style: TextStyle(fontSize: 12, color: AppColors.muted),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              field('reference', 'Référence'),
              field('version', 'Version du document'),
              field('title', 'Titre', wide: true),
              field('tome', 'Tome'),
              field('sc', 'Sous-commission'),
              field('group', 'Groupe de travail'),
              field('vote_date', 'Date du vote', hint: 'AAAA-MM-JJ'),
              field('received_at', 'Réception', hint: 'AAAA-MM-JJ'),
              field('sender', 'Émetteur'),
            ],
          ),
          const SizedBox(height: 6),
          const Text(
            'Ces champs sont enregistrés avec la nouvelle indexation.',
            style: TextStyle(fontSize: 11, color: AppColors.subtle),
          ),
        ],
      ),
    );
  }
}

class _IndexCard extends StatelessWidget {
  const _IndexCard({
    required this.state,
    required this.codeId,
    required this.sourceId,
    required this.verified,
    required this.observation,
    required this.busy,
    required this.onSubmit,
  });

  final _WorkFicheState state;
  final int? codeId;
  final int? sourceId;
  final bool verified;
  final TextEditingController observation;
  final bool busy;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    final row = state.widget.row;
    final data = state.widget.data;
    final normeId = row['norme_id'];
    final codes = rowsOf(data['codes']).where((item) => item['norme_id'] == normeId).toList();
    final files = rowsOf(row['files']);
    final report = row['report'] is Map ? (row['report'] as Map).cast<String, dynamic>() : null;
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GedSectionTitle('Indexation documentaire', Icons.document_scanner_outlined),
          const SizedBox(height: 10),
          DropdownButtonFormField<int?>(
            initialValue: codeId,
            isDense: true,
            decoration: InputDecoration(
              isDense: true,
              labelText: 'Code documentaire',
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
            ),
            items: [
              const DropdownMenuItem(value: null, child: Text('Choisir un code autorisé', style: TextStyle(fontSize: 13))),
              for (final code in codes)
                DropdownMenuItem(
                  value: (code['id'] as num).toInt(),
                  child: Text(
                    '${code['code']} · autorisé par ${code['author']}',
                    style: const TextStyle(fontSize: 13),
                  ),
                ),
            ],
            onChanged: state.selectCode,
          ),
          const SizedBox(height: 4),
          Text(
            codes.isEmpty
                ? 'Code documentaire autorisé attendu du chef du pôle 2.'
                : 'Source de l’autorisation : la SC du dossier et le registre des codes autorisés.',
            style: const TextStyle(fontSize: 11, color: AppColors.subtle),
          ),
          const SizedBox(height: 8),
          Text(
            'Version v${(row['next_version'] as num?)?.toInt() ?? 1} · nouvelle version',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.text),
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<int?>(
            initialValue: sourceId,
            isDense: true,
            decoration: InputDecoration(
              isDense: true,
              labelText: 'Fichier préparé',
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
            ),
            items: [
              const DropdownMenuItem(value: null, child: Text('Choisir un fichier', style: TextStyle(fontSize: 13))),
              for (final file in files)
                DropdownMenuItem(
                  value: (file['id'] as num).toInt(),
                  child: SizedBox(
                    width: 320,
                    child: Text(
                      '${file['name']} · ${file['author']}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 13),
                    ),
                  ),
                ),
            ],
            onChanged: state.selectSource,
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 10,
            runSpacing: 8,
            children: [
              GedButton(
                label: 'Joindre',
                icon: Icons.upload_outlined,
                secondary: true,
                busy: busy,
                onTap: () => state.widget.onAction(GedUploadAction(processId: state._processId)),
              ),
              if (report != null)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Text(
                    'Rapport de revue : ${report['name'] ?? '—'}',
                    style: const TextStyle(fontSize: 12, color: AppColors.muted),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 10),
          TextField(
            controller: observation,
            maxLines: 3,
            maxLength: 10000,
            style: const TextStyle(fontSize: 13),
            decoration: InputDecoration(
              isDense: true,
              labelText: 'Observation',
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
            ),
          ),
          const SizedBox(height: 6),
          Material(
            type: MaterialType.transparency,
            child: CheckboxListTile(
              dense: true,
              value: verified,
              onChanged: (value) => state.setVerified(value ?? false),
              controlAffinity: ListTileControlAffinity.leading,
              contentPadding: EdgeInsets.zero,
              title: const Text('Pièces vérifiées et lisibles', style: TextStyle(fontSize: 12)),
            ),
          ),
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerLeft,
            child: GedButton(
              label: 'Confirmer l’indexation',
              icon: Icons.document_scanner_outlined,
              busy: busy,
              onTap: onSubmit,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'Le dossier passe au contrôle du chef du pôle 2 ; la validation normative reste distincte.',
            style: TextStyle(fontSize: 11, color: AppColors.subtle),
          ),
        ],
      ),
    );
  }
}

class _SuiteCard extends StatelessWidget {
  const _SuiteCard({
    required this.state,
    required this.anomalies,
    required this.busy,
  });

  final _WorkFicheState state;
  final List<Map<String, dynamic>> anomalies;
  final bool busy;

  void _openAnomalyForm() => state.toggleAnomalyForm();

  @override
  Widget build(BuildContext context) {
    final recipients = rowsOf(state.widget.data['recipients']);
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GedSectionTitle('Suite du dossier', Icons.folder_open_outlined),
          const SizedBox(height: 10),
          Wrap(
            spacing: 10,
            runSpacing: 8,
            children: [
              GedButton(
                label: state._anomalyFormOpen ? 'Fermer le formulaire' : 'Signaler une anomalie',
                icon: state._anomalyFormOpen ? Icons.close : Icons.report_problem_outlined,
                secondary: true,
                onTap: _openAnomalyForm,
              ),
            ],
          ),
          if (state._anomalyFormOpen) ...[
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              initialValue: state._anomalyKind,
              isDense: true,
              decoration: InputDecoration(
                isDense: true,
                labelText: 'Type d’anomalie',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
              ),
              items: [
                for (final entry in _anomalyKinds.entries)
                  DropdownMenuItem(value: entry.key, child: Text(entry.value, style: const TextStyle(fontSize: 13))),
              ],
              onChanged: state.selectAnomalyKind,
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<int?>(
              initialValue: state._recipientId,
              isDense: true,
              decoration: InputDecoration(
                isDense: true,
                labelText: 'Destinataire',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
              ),
              items: [
                const DropdownMenuItem(value: null, child: Text('Choisir un destinataire', style: TextStyle(fontSize: 13))),
                for (final recipient in recipients)
                  DropdownMenuItem(
                    value: (recipient['id'] as num).toInt(),
                    child: Text(
                      '${recipient['name']} · ${recipient['title']}',
                      style: const TextStyle(fontSize: 13),
                    ),
                  ),
              ],
              onChanged: state.selectRecipient,
            ),
            const SizedBox(height: 8),
            TextField(
              controller: state._anomalyComment,
              maxLines: 3,
              maxLength: 10000,
              style: const TextStyle(fontSize: 13),
              decoration: InputDecoration(
                isDense: true,
                labelText: 'Pièce ou information à corriger',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
              ),
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerLeft,
              child: GedButton(
                label: 'Signaler et notifier',
                icon: Icons.send_outlined,
                busy: busy,
                onTap: state._submitAnomaly,
              ),
            ),
          ],
          const SizedBox(height: 12),
          Text(
            'Anomalies du dossier (${anomalies.length})',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: AppColors.text),
          ),
          const SizedBox(height: 6),
          if (anomalies.isEmpty)
            const GedEmpty('Aucune anomalie enregistrée sur ce dossier.')
          else
            for (final anomaly in anomalies)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    border: Border.all(color: AppColors.border),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              '${anomaly['kind_label'] ?? anomaly['kind'] ?? 'Anomalie'}'
                              '${asText(anomaly['recipient']) != null ? ' · destinataire ${anomaly['recipient']}' : ''}',
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                                color: AppColors.text,
                              ),
                            ),
                          ),
                          GedBadge(
                            label: anomaly['status_label'] ?? (anomaly['status'] == 'RESOLVED' ? 'Résolue' : 'Ouverte'),
                            color: anomaly['status'] == 'RESOLVED' ? AppColors.success : AppColors.danger,
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        (anomaly['comment'] ?? '').toString(),
                        style: const TextStyle(fontSize: 12, color: AppColors.muted),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Signalée par ${anomaly['author'] ?? '—'} · ${frDate(anomaly['date'])} · ancienneté ${anomaly['age_days']?.toInt() ?? 0} j',
                        style: const TextStyle(fontSize: 11, color: AppColors.subtle),
                      ),
                      if (anomaly['status'] != 'RESOLVED')
                        Align(
                          alignment: Alignment.centerLeft,
                          child: TextButton(
                            onPressed: busy ? null : () => state._resolveAnomaly((anomaly['id'] as num).toInt()),
                            child: const Text('Résoudre'),
                          ),
                        ),
                      if (asText(anomaly['resolution']) != null)
                        Text(
                          'Résolution : ${anomaly['resolution']}',
                          style: const TextStyle(fontSize: 11, color: AppColors.muted),
                        ),
                    ],
                  ),
                ),
              ),
        ],
      ),
    );
  }
}

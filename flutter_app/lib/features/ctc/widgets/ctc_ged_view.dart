import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';

import '../../../core/api/api_client.dart';
import '../../../theme/app_colors.dart';
import 'ctc_ged_dashboard.dart';
import 'ctc_ged_work.dart';
import 'ged_counts.dart';
import 'ged_shared.dart';

/// `CtcGedWorkspace` — en-tête, routeur d'onglets et panneaux secondaires du
/// poste 11 (GED du pôle 2). Charge `/api/v1/st/ged/`, `/api/v1/st/ged/queue/`
/// et les opérations d'indexation, anomalies et vérification de code.

const _panelEntries = <String, String>{
  'dashboard': 'Tableau de bord',
  'work': 'Dossiers à indexer',
  'library': 'Bibliothèque',
  'versions_todo': 'Versions à traiter',
  'codes': 'Codification',
  'anomalies': 'Anomalies',
  'activity': 'Mon activité',
};

class CtcGedWorkspace extends StatefulWidget {
  const CtcGedWorkspace({
    super.key,
    this.initialPanel = 'dashboard',
    this.initialProcessId,
    this.showPanelTabs = true,
  });

  /// Onglet de départ. La vue `#indexation` du web affiche d'abord la file du poste.
  final String initialPanel;
  final int? initialProcessId;
  final bool showPanelTabs;

  @override
  State<CtcGedWorkspace> createState() => _CtcGedWorkspaceState();
}

class _CtcGedWorkspaceState extends State<CtcGedWorkspace> {
  String _panel = 'dashboard';
  Map<String, dynamic>? _data;
  List<Map<String, dynamic>> _queue = [];
  int _queueTotal = 0;
  Map<String, dynamic>? _detail;
  bool _loading = true;
  bool _busy = false;
  int _periodDays = 30;
  String? _scFilter;
  String? _error;

  final Set<String> _states = {};
  final TextEditingController _search = TextEditingController();

  @override
  void initState() {
    super.initState();
    _panel = widget.initialPanel;
    _reload();
  }

  @override
  void didUpdateWidget(covariant CtcGedWorkspace oldWidget) {
    super.didUpdateWidget(oldWidget);
    // La barre latérale relit une autre vue du poste 11 : basculer le panneau
    // sans recharger toute l'espace.
    if (widget.initialPanel != oldWidget.initialPanel &&
        _panel != widget.initialPanel) {
      setState(() => _panel = widget.initialPanel);
    }
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _reload({int? periodDays}) async {
    final requestedDays = periodDays ?? _periodDays;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final responses = await Future.wait([
        ApiClient.dio.get(
          '/api/v1/st/ged/',
          queryParameters: {'days': requestedDays},
        ),
        _queueRequest(),
        if (widget.initialProcessId != null)
          ApiClient.dio.get('/api/v1/st/ged/${widget.initialProcessId}/'),
      ]);
      final data = (responses[0].data as Map).cast<String, dynamic>();
      final queueBody = (responses[1].data as Map).cast<String, dynamic>();
      final rows = rowsOf(queueBody['results']);
      final count = (queueBody['total'] as num?)?.toInt() ?? rows.length;
      // Badges de la barre latérale ST (miroir de l'événement web
      // `st-ged-counts`).
      final kpisMap = data['kpis'] as Map?;
      publishGedCounts(kpisMap?.cast<String, dynamic>());
      if (!mounted) return;
      final id = _detailId ?? widget.initialProcessId;
      setState(() {
        _data = data;
        _periodDays = requestedDays;
        _queue = rows;
        _queueTotal = count;
        _loading = false;
        _detail = responses.length > 2
            ? (responses[2].data as Map).cast<String, dynamic>()
            : id == null
            ? null
            : _rowById(id);
        if (_detail != null && widget.initialProcessId != null) _panel = 'work';
      });
    } on DioException catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = errorDetail(error) ?? 'Espace GED indisponible.';
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'Espace GED indisponible.';
      });
    }
  }

  Future<Response<dynamic>> _queueRequest() {
    final query = <String, String>{'page': '1', 'page_size': '50'};
    if (_scFilter != null) query['sc'] = _scFilter!;
    if (_states.isNotEmpty) query['states'] = _states.join(',');
    final text = _search.text.trim();
    if (text.isNotEmpty) query['q'] = text;
    return ApiClient.dio.get('/api/v1/st/ged/queue/', queryParameters: query);
  }

  int? get _detailId {
    final value = _detail?['id'];
    return value is num ? value.toInt() : null;
  }

  Map<String, dynamic>? _rowById(int id) {
    for (final row in _queue) {
      if (row['id'] == id) return row;
    }
    for (final row in rowsOf(_data?['results'] ?? const [])) {
      if (row['id'] == id) return row;
    }
    return null;
  }

  void _select(Map<String, dynamic> row) {
    setState(() {
      _detail = row;
      _panel = 'work';
    });
  }

  void _toggleState(String state) {
    setState(() {
      if (_states.contains(state)) {
        _states.remove(state);
      } else {
        _states.add(state);
      }
    });
    _reload();
  }

  Future<void> _runAction(GedAction action) async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      await switch (action) {
        GedIndexAction() => _postIndex(action),
        GedUploadAction() => _postUpload(action),
        GedAnomalyAction() => _postAnomaly(action),
        GedResolveAnomalyAction() => _postResolveAnomaly(action),
        GedCodeCheckAction() => _checkCode(action.code),
      };
    } on DioException catch (error) {
      _flash(
        errorDetail(error) ?? 'Action refusée par le serveur.',
        error: true,
      );
    } catch (error) {
      _flash('Action refusée par le serveur.', error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _postIndex(GedIndexAction action) async {
    if ((action.metadata['reference'] ?? '').trim().isEmpty ||
        (action.metadata['title'] ?? '').trim().isEmpty) {
      _flash(
        'La référence et le titre documentaires sont obligatoires.',
        error: true,
      );
      return;
    }
    if (action.codeId == null) {
      _flash('Sélectionnez le code documentaire autorisé.', error: true);
      return;
    }
    if (action.sourceId == null) {
      _flash('Sélectionnez le fichier source préparé.', error: true);
      return;
    }
    if (!action.verified) {
      _flash(
        'Vérifiez le rapport de revue et la lisibilité des pièces avant de confirmer.',
        error: true,
      );
      return;
    }
    final response = await ApiClient.dio.post(
      '/api/v1/st/ged/${action.processId}/index/',
      data: {
        'code_id': action.codeId,
        'source_id': action.sourceId,
        'base_version_id': action.baseVersionId ?? 0,
        'verified': true,
        'observation': action.observation,
        'metadata': action.metadata,
      },
    );
    final body = (response.data as Map).cast<String, dynamic>();
    await _reload();
    _flash(
      'Indexation enregistrée · ${body['code']} · v${body['number']}. '
      'Le chef du pôle 2 est notifié pour confirmation.',
    );
  }

  Future<void> _postUpload(GedUploadAction action) async {
    const group = XTypeGroup(
      label: 'Documents indexables (PDF, PNG, JPEG)',
      mimeTypes: ['application/pdf', 'image/png', 'image/jpeg'],
    );
    final file = await openFile(acceptedTypeGroups: const [group]);
    if (file == null) return;
    final name = file.name.toLowerCase();
    if (!const ['.pdf', '.png', '.jpg', '.jpeg'].any(name.endsWith)) {
      _flash('Format accepté : PDF, PNG ou JPEG.', error: true);
      return;
    }
    final bytes = await file.readAsBytes();
    final form = FormData.fromMap({
      'file': MultipartFile.fromBytes(bytes, filename: file.name),
    });
    await ApiClient.dio.post(
      '/api/v1/st/ged/${action.processId}/files/',
      data: form,
    );
    await _reload();
    _flash('Fichier préparé enregistré : ${file.name}');
  }

  Future<void> _postAnomaly(GedAnomalyAction action) async {
    if (action.comment.trim().isEmpty) {
      _flash('Motif documentaire obligatoire.', error: true);
      return;
    }
    await ApiClient.dio.post(
      '/api/v1/st/ged/${action.processId}/anomalies/',
      data: {
        'comment': action.comment,
        'kind': action.kind,
        'recipient_id': action.recipientId,
      },
    );
    await _reload();
    _flash('Anomalie signalée · notification envoyée.');
  }

  Future<void> _postResolveAnomaly(GedResolveAnomalyAction action) async {
    if (action.comment.trim().isEmpty) {
      _flash('Commentaire de résolution obligatoire.', error: true);
      return;
    }
    await ApiClient.dio.post(
      '/api/v1/st/ged/${action.processId}/anomalies/',
      data: {'comment': action.comment, 'resolve_id': action.anomalyId},
    );
    await _reload();
    _flash('Anomalie résolue.');
  }

  Future<void> _checkCode(String code) async {
    final trimmed = code.trim();
    if (trimmed.isEmpty) {
      _flash('Saisissez un code documentaire à vérifier.', error: true);
      return;
    }
    final response = await ApiClient.dio.get(
      '/api/v1/st/ged/code-lookup/',
      queryParameters: {'code': trimmed},
    );
    final body = (response.data as Map).cast<String, dynamic>();
    if (body['available'] == true) {
      _flash('Code $trimmed disponible (non utilisé).');
    } else {
      _flash(
        'Code déjà utilisé : ${body['reference']} · autorisé par ${body['author']}.',
        error: true,
      );
    }
  }

  void _flash(String message, {bool error = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..clearSnackBars()
      ..showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: error
              ? const Color(0xFFB91C1C)
              : const Color(0xFF166534),
        ),
      );
  }

  @override
  Widget build(BuildContext context) {
    final data = _data;
    return LayoutBuilder(
      builder: (context, box) {
        final wide = box.maxWidth >= 900;
        return ColoredBox(
          color: AppColors.page,
          child: _error != null && data == null
              ? GedFailed(
                  title: 'Suivi documentaire indisponible',
                  detail: _error!,
                  onRetry: _reload,
                )
              : _loading || data == null
              ? const Center(
                  child: Padding(
                    padding: EdgeInsets.all(48),
                    child: CircularProgressIndicator(),
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(20, 20, 20, 44),
                  child: Align(
                    alignment: Alignment.topCenter,
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 1280),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          if (_error != null) ...[
                            GedFailed(
                              title:
                                  'Actualisation impossible — période précédente conservée',
                              detail: _error!,
                              onRetry: _reload,
                            ),
                            const SizedBox(height: 14),
                          ],
                          _Heading(
                            data: data,
                            busy: _busy || _loading,
                            onRefresh: _reload,
                            periodDays: _periodDays,
                            onPeriodChanged: (days) {
                              if (days == null) return;
                              _reload(periodDays: days);
                            },
                          ),
                          const SizedBox(height: 14),
                          if (widget.showPanelTabs)
                            _PanelTabs(
                              panel: _panel,
                              head: data['head'] == true,
                              onNavigate: (value) =>
                                  setState(() => _panel = value),
                            ),
                          const SizedBox(height: 16),
                          if (_panel == 'work' && _scFilter != null)
                            Align(
                              alignment: Alignment.centerLeft,
                              child: InputChip(
                                label: Text('Sous-commission : $_scFilter'),
                                onDeleted: () {
                                  setState(() => _scFilter = null);
                                  _reload();
                                },
                              ),
                            ),
                          if (_panel == 'work')
                            GedWorkPanel(
                              data: data,
                              queue: _queue,
                              queueTotal: _queueTotal,
                              detailId: _detailId,
                              states: _states,
                              search: _search,
                              busy: _busy,
                              onSelect: _select,
                              onToggleState: _toggleState,
                              onClearFilters: () {
                                setState(() {
                                  _states.clear();
                                  _search.clear();
                                  _scFilter = null;
                                });
                                _reload();
                              },
                              onSearch: _reload,
                              onAction: _runAction,
                            )
                          else if (_panel == 'library')
                            _LibraryPanel(data: data)
                          else if (_panel == 'versions_todo')
                            _VersionsTodoPanel(data: data)
                          else if (_panel == 'codes')
                            _CodesPanel(
                              data: data,
                              onAction: _runAction,
                              busy: _busy,
                            )
                          else if (_panel == 'anomalies')
                            _AnomaliesPanel(
                              data: data,
                              onAction: _runAction,
                              busy: _busy,
                            )
                          else if (_panel == 'activity')
                            _ActivityPanel(data: data)
                          else
                            GedDashboardPanel(
                              data: data,
                              wide: wide,
                              onOpenWork: () => setState(() => _panel = 'work'),
                              onOpenAnomalies: () =>
                                  setState(() => _panel = 'anomalies'),
                              onOpenActivity: () =>
                                  setState(() => _panel = 'activity'),
                              onOpenFollowup: () =>
                                  setState(() => _panel = 'versions_todo'),
                              onOpenSc: (sc) {
                                setState(() {
                                  _scFilter = sc;
                                  _states.clear();
                                  _search.clear();
                                  _panel = 'work';
                                });
                                _reload();
                              },
                              onOpenProcess: (id, reference) {
                                final row = _rowById(id);
                                if (row != null) {
                                  _select(row);
                                } else {
                                  setState(() {
                                    _scFilter = null;
                                    _states.clear();
                                    _search.text = reference;
                                    _panel = 'work';
                                  });
                                  _reload();
                                }
                              },
                            ),
                        ],
                      ),
                    ),
                  ),
                ),
        );
      },
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// En-tête et routeur d'onglets.
// ─────────────────────────────────────────────────────────────────────────────

class _Heading extends StatelessWidget {
  const _Heading({
    required this.data,
    required this.busy,
    required this.onRefresh,
    required this.periodDays,
    required this.onPeriodChanged,
  });

  final Map<String, dynamic> data;
  final bool busy;
  final void Function() onRefresh;
  final int periodDays;
  final ValueChanged<int?> onPeriodChanged;

  @override
  Widget build(BuildContext context) {
    final updated = (data['updated_at'] ?? '').toString();
    return GedCard(
      child: Wrap(
        spacing: 14,
        runSpacing: 12,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AppColors.rdcBlue.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.local_library_outlined,
              color: AppColors.rdcBlue,
            ),
          ),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  data['head'] == true
                      ? 'CNE-ITP · Pôle 2 · Supervision'
                      : 'CNE-ITP · Pôle 2 · Poste 11',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    letterSpacing: .6,
                    color: AppColors.rdcBlue,
                  ),
                ),
                Text(
                  'Espace documentaire',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.w800,
                    color: AppColors.text,
                  ),
                ),
                Text(
                  'Suivi et supervision documentaire',
                  style: TextStyle(fontSize: 12, color: AppColors.muted),
                ),
              ],
            ),
          ),
          Text(
            updated.isEmpty ? '' : 'Mise à jour · ${frDateTime(updated)}',
            style: const TextStyle(fontSize: 11, color: AppColors.subtle),
          ),
          Semantics(
            label: 'Période du tableau de bord',
            child: DropdownButton<int>(
              value: periodDays,
              items: const [
                DropdownMenuItem(value: 7, child: Text('7 jours')),
                DropdownMenuItem(value: 30, child: Text('30 jours')),
                DropdownMenuItem(value: 90, child: Text('90 jours')),
              ],
              onChanged: busy ? null : onPeriodChanged,
            ),
          ),
          GedButton(
            label: 'Actualiser',
            icon: Icons.refresh_outlined,
            secondary: true,
            busy: busy,
            onTap: onRefresh,
          ),
        ],
      ),
    );
  }
}

class _PanelTabs extends StatelessWidget {
  const _PanelTabs({
    required this.panel,
    required this.head,
    required this.onNavigate,
  });

  final String panel;
  final bool head;
  final ValueChanged<String> onNavigate;

  @override
  Widget build(BuildContext context) {
    return GedCard(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            for (final entry in _panelEntries.entries)
              Padding(
                padding: const EdgeInsets.only(right: 6),
                child: ChoiceChip(
                  label: Text(
                    entry.value,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: panel == entry.key
                          ? Colors.white
                          : AppColors.muted,
                    ),
                  ),
                  selected: panel == entry.key,
                  selectedColor: AppColors.rdcBlue,
                  showCheckmark: false,
                  side: const BorderSide(color: AppColors.border),
                  onSelected: (_) => onNavigate(entry.key),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Bibliothèque documentaire (data-ged-panel="library").
// ─────────────────────────────────────────────────────────────────────────────

class _LibraryPanel extends StatelessWidget {
  const _LibraryPanel({required this.data});

  final Map<String, dynamic> data;

  static const _statusLabels = {
    'CONFIRMED': 'Confirmé',
    'PENDING': 'À confirmer',
    'RETURNED': 'À corriger',
  };

  @override
  Widget build(BuildContext context) {
    final results = rowsOf(
      data['results'],
    ).where((row) => row['latest'] != null).toList();
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GedSectionTitle('Documents GED', Icons.library_books_outlined),
          const SizedBox(height: 4),
          const Text(
            'Bibliothèque des documents indexés : code, statut de contrôle et versions enregistrées.',
            style: TextStyle(fontSize: 12, color: AppColors.muted),
          ),
          const SizedBox(height: 12),
          if (results.isEmpty)
            const GedEmpty('Aucune version documentaire enregistrée.')
          else
            for (final row in results.take(25))
              _LibraryRow(row: row, statusLabels: _statusLabels),
        ],
      ),
    );
  }
}

class _LibraryRow extends StatelessWidget {
  const _LibraryRow({required this.row, required this.statusLabels});

  final Map<String, dynamic> row;
  final Map<String, String> statusLabels;

  @override
  Widget build(BuildContext context) {
    final latest = row['latest'] as Map? ?? {};
    final confirmation = latest['confirmation'];
    final status = confirmation is Map
        ? (confirmation['decision'] == 'RETURNED'
              ? 'À corriger'
              : confirmation['decision'] == 'CONFIRMED'
              ? 'Confirmé'
              : 'À confirmer')
        : 'À confirmer';
    final versions = rowsOf(row['versions']);
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.border),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '${row['reference'] ?? ''} · ${latest['code'] ?? 'code —'} · v${latest['number'] ?? ''}',
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    color: AppColors.text,
                  ),
                ),
              ),
              GedBadge(
                label: status,
                color: status == 'Confirmé'
                    ? AppColors.success
                    : status == 'À corriger'
                    ? AppColors.danger
                    : AppColors.rdcBlue,
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            (row['title'] ?? '').toString(),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: AppColors.text,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            '${gedOrigin(row['sc'], row['tome'], row['group'])}'
            '${asText(latest['author']) != null ? ' · indexé par ${latest['author']}' : ''}'
            ' · ${versions.length} version(s)',
            style: const TextStyle(fontSize: 11, color: AppColors.muted),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Versions à traiter (data-ged-panel="versions_todo").
// ─────────────────────────────────────────────────────────────────────────────

class _VersionsTodoPanel extends StatelessWidget {
  const _VersionsTodoPanel({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final items = rowsOf(data['versions_todo']);
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: GedSectionTitle(
                  'Versions à traiter',
                  Icons.copy_all_outlined,
                ),
              ),
              Text(
                '${items.length}',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                  color: AppColors.rdcBlue,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          const Text(
            'Nouvelles versions en attente de contrôle ou renvoyées pour correction. '
            'La validation normative reste distincte.',
            style: TextStyle(fontSize: 12, color: AppColors.muted),
          ),
          const SizedBox(height: 12),
          if (items.isEmpty)
            const GedEmpty(
              'Aucune version en attente de contrôle documentaire.',
            )
          else
            for (final item in items)
              Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(color: AppColors.border),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${item['reference'] ?? ''} · ${item['code'] ?? ''} · v${item['version'] ?? ''}',
                            style: const TextStyle(
                              fontFamily: 'monospace',
                              fontSize: 12,
                              fontWeight: FontWeight.w800,
                              color: AppColors.text,
                            ),
                          ),
                          Text(
                            '${item['title'] ?? ''} · indexé par ${item['author'] ?? '—'} · ${frDate(item['created_at'])}',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 11,
                              color: AppColors.muted,
                            ),
                          ),
                        ],
                      ),
                    ),
                    GedBadge(
                      label:
                          item['confirmation'] is Map &&
                              (item['confirmation'] as Map)['decision'] ==
                                  'RETURNED'
                          ? 'À corriger'
                          : 'À contrôler',
                      color:
                          (item['confirmation'] is Map &&
                              (item['confirmation'] as Map)['decision'] ==
                                  'RETURNED')
                          ? AppColors.danger
                          : AppColors.rdcBlue,
                    ),
                  ],
                ),
              ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Codification (data-ged-panel="codes").
// ─────────────────────────────────────────────────────────────────────────────

class _CodesPanel extends StatefulWidget {
  const _CodesPanel({
    required this.data,
    required this.onAction,
    required this.busy,
  });

  final Map<String, dynamic> data;
  final void Function(GedAction action) onAction;
  final bool busy;

  @override
  State<_CodesPanel> createState() => _CodesPanelState();
}

class _CodesPanelState extends State<_CodesPanel> {
  final _lookup = TextEditingController();

  @override
  void dispose() {
    _lookup.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final analysis = (widget.data['codification_analysis'] as Map? ?? {})
        .cast<String, dynamic>();
    final rows = rowsOf(analysis['rows']);
    final codes = rowsOf(widget.data['codes']);
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GedSectionTitle(
            'Contrôle des codifications',
            Icons.qr_code_2_outlined,
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 16,
            runSpacing: 12,
            children: [
              GedKpi(value: analysis['verified'] ?? 0, label: 'Codes vérifiés'),
              GedKpi(value: analysis['conflicts'] ?? 0, label: 'Conflits'),
              GedKpi(value: analysis['duplicates'] ?? 0, label: 'Doublons'),
              GedKpi(value: analysis['missing'] ?? 0, label: 'Manquants'),
              GedKpi(
                value: analysis['inconsistent'] ?? 0,
                label: 'Incohérents',
              ),
              GedKpi(
                value: analysis['format_errors'] ?? 0,
                label: 'Formats invalides',
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            crossAxisAlignment: WrapCrossAlignment.end,
            children: [
              SizedBox(
                width: 220,
                child: TextField(
                  controller: _lookup,
                  style: const TextStyle(fontSize: 13),
                  decoration: InputDecoration(
                    isDense: true,
                    labelText: 'Vérifier un code',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                ),
              ),
              GedButton(
                label: 'Vérifier',
                icon: Icons.rule_outlined,
                secondary: true,
                busy: widget.busy,
                onTap: () => widget.onAction(
                  GedCodeCheckAction(code: _lookup.text.trim()),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            'Registre des codes autorisés (${codes.length})',
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              color: AppColors.text,
            ),
          ),
          const SizedBox(height: 8),
          if (codes.isEmpty)
            const GedEmpty('Aucun code autorisé par le chef du pôle 2.')
          else
            for (final code in codes.take(20))
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        '${code['code']} · ${code['source_reference'] ?? ''}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 12,
                          fontFamily: 'monospace',
                          color: AppColors.text,
                        ),
                      ),
                    ),
                    Text(
                      'Par ${code['author'] ?? '—'}',
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppColors.muted,
                      ),
                    ),
                  ],
                ),
              ),
          const SizedBox(height: 14),
          GeAnchorTitle(
            label: 'Constats du contrôle automatique (${rows.length})',
          ),
          const SizedBox(height: 8),
          if (rows.isEmpty)
            const GedEmpty('Aucun constat sur les codes documentaires.')
          else
            for (final row in rows.take(20))
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        '${row['norme'] ?? ''} · ${row['reference'] ?? 'code absent'} · ${row['anomaly'] ?? ''}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.text,
                        ),
                      ),
                    ),
                    GedBadge(
                      label: (row['level'] ?? 'alerte').toString(),
                      color: row['level'] == 'erreur'
                          ? AppColors.danger
                          : AppColors.warning,
                    ),
                  ],
                ),
              ),
        ],
      ),
    );
  }
}

class GeAnchorTitle extends StatelessWidget {
  const GeAnchorTitle({super.key, required this.label});

  final String label;

  @override
  Widget build(BuildContext context) => Text(
    label,
    style: const TextStyle(
      fontSize: 12,
      fontWeight: FontWeight.w800,
      color: AppColors.text,
    ),
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Anomalies transverses (data-ged-panel="anomalies").
// ─────────────────────────────────────────────────────────────────────────────

class _AnomaliesPanel extends StatelessWidget {
  const _AnomaliesPanel({
    required this.data,
    required this.onAction,
    required this.busy,
  });

  final Map<String, dynamic> data;
  final void Function(GedAction action) onAction;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final anomalies = rowsOf(data['anomalies']);
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GedSectionTitle(
            'Anomalies documentaires',
            Icons.warning_amber_outlined,
          ),
          const SizedBox(height: 4),
          const Text(
            'Pièces manquantes, corrompues, mal classées ou informations incohérentes. '
            'La notification part au destinataire retenu.',
            style: TextStyle(fontSize: 12, color: AppColors.muted),
          ),
          const SizedBox(height: 12),
          if (anomalies.isEmpty)
            const GedEmpty('Aucune anomalie enregistrée.')
          else
            for (final anomaly in anomalies.take(30))
              Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(color: AppColors.border),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            '${anomaly['reference'] ?? ''} · ${anomaly['kind_label'] ?? anomaly['kind']}',
                            style: const TextStyle(
                              fontFamily: 'monospace',
                              fontSize: 12,
                              fontWeight: FontWeight.w800,
                              color: AppColors.text,
                            ),
                          ),
                        ),
                        GedBadge(
                          label:
                              anomaly['status_label'] ??
                              (anomaly['status'] == 'RESOLVED'
                                  ? 'Résolue'
                                  : 'Ouverte'),
                          color: anomaly['status'] == 'RESOLVED'
                              ? AppColors.success
                              : AppColors.danger,
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      (anomaly['comment'] ?? '').toString(),
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.muted,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Dossier : ${anomaly['title'] ?? '—'} · signalée par ${anomaly['author'] ?? '—'} · ${frDate(anomaly['date'])}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppColors.subtle,
                      ),
                    ),
                    if (asText(anomaly['resolution']) != null)
                      Text(
                        'Résolution : ${anomaly['resolution']}',
                        style: const TextStyle(
                          fontSize: 11,
                          color: AppColors.muted,
                        ),
                      ),
                  ],
                ),
              ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Piste d'audit (data-ged-panel="activity").
// ─────────────────────────────────────────────────────────────────────────────

class _ActivityPanel extends StatelessWidget {
  const _ActivityPanel({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final activity = rowsOf(data['activity']);
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GedSectionTitle(
            "Mon activité documentaire",
            Icons.history_outlined,
          ),
          const SizedBox(height: 4),
          const Text(
            'Opérations enregistrées et suivi des dossiers documentaires.',
            style: TextStyle(fontSize: 12, color: AppColors.muted),
          ),
          const SizedBox(height: 12),
          if (activity.isEmpty)
            const GedEmpty('Aucune opération enregistrée sur la période.')
          else
            for (final entry in activity)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    border: Border.all(color: AppColors.border),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "${_historyLabels[entry['action']] ?? entry['action'] ?? 'Opération'} · ${frDateTime(entry['date'])}",
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                          color: AppColors.text,
                        ),
                      ),
                      Text(
                        '${entry['reference'] ?? ''}'
                        '${asText(entry['code']) != null ? ' · ${entry['code']}' : ''}'
                        '${entry['version'] != null ? ' · v${entry['version']}' : ''}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 11,
                          color: AppColors.muted,
                        ),
                      ),
                      if (asText(entry['comment']) != null)
                        Text(
                          (entry['comment'] ?? '').toString(),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 11,
                            color: AppColors.muted,
                          ),
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

const _historyLabels = <String, String>{
  'ged_code_authorized': 'Code autorisé',
  'ged_file_uploaded': 'Fichier préparé',
  'ged_indexed': 'Indexation enregistrée',
  'ged_restored': 'Version restaurée',
  'ged_confirmed': 'Version confirmée',
  'ged_returned': 'Correction demandée',
  'ged_anomaly_reported': 'Anomalie signalée',
  'ged_anomaly_resolved': 'Anomalie résolue',
};

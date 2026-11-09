import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';

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
  'history': 'Historique des versions',
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

  Future<void> _printReport() async {
    final kpis = (_data?['kpis'] as Map? ?? {}).cast<String, dynamic>();
    const labels = <String, String>{
      'ready': 'Prêts à indexer',
      'waiting_report': 'Rapports attendus',
      'blocked': 'Bloqués ou à corriger',
      'versions_todo': 'Versions à traiter',
      'indexed': 'Déjà indexés',
      'pending': 'À confirmer',
      'anomalies': 'Anomalies',
      'overdue_14': 'En retard de plus de 14 jours',
      'confirmed_period': 'Confirmés sur la période',
    };
    final report = pw.Document();
    report.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(36),
        header: (_) => pw.Container(
          padding: const pw.EdgeInsets.only(bottom: 8),
          decoration: const pw.BoxDecoration(
            border: pw.Border(
              bottom: pw.BorderSide(color: PdfColors.blue, width: 1.5),
            ),
          ),
          child: pw.Text(
            'CNE-ITP  |  COORDINATION DU SECRÉTARIAT TECHNIQUE',
            style: pw.TextStyle(
              fontSize: 9,
              fontWeight: pw.FontWeight.bold,
              color: PdfColors.blue900,
            ),
          ),
        ),
        footer: (context) => pw.Align(
          alignment: pw.Alignment.centerRight,
          child: pw.Text(
            'Page ${context.pageNumber} / ${context.pagesCount}',
            style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey700),
          ),
        ),
        build: (_) => [
          pw.SizedBox(height: 18),
          pw.Text(
            'Rapport de suivi documentaire',
            style: pw.TextStyle(fontSize: 19, fontWeight: pw.FontWeight.bold),
          ),
          pw.SizedBox(height: 5),
          pw.Text(
            'CNE-ITP · Pôle 2 · ${_data?['head'] == true ? 'Supervision' : 'Poste 11'}',
            style: const pw.TextStyle(fontSize: 10, color: PdfColors.grey700),
          ),
          pw.Text(
            'Vue : ${_panelEntries[_panel] ?? 'Suivi documentaire'} · Période : $_periodDays jours · Édité le ${frDateTime(DateTime.now().toIso8601String())}',
            style: const pw.TextStyle(fontSize: 9, color: PdfColors.grey700),
          ),
          pw.SizedBox(height: 18),
          pw.Text(
            'Indicateurs de suivi',
            style: pw.TextStyle(fontSize: 13, fontWeight: pw.FontWeight.bold),
          ),
          pw.SizedBox(height: 7),
          pw.TableHelper.fromTextArray(
            headers: const ['Indicateur', 'Valeur'],
            data: labels.entries
                .where((entry) => kpis.containsKey(entry.key))
                .map((entry) => [entry.value, '${kpis[entry.key]}'])
                .toList(),
            headerStyle: pw.TextStyle(
              fontWeight: pw.FontWeight.bold,
              color: PdfColors.white,
            ),
            headerDecoration: const pw.BoxDecoration(color: PdfColors.blue800),
            cellStyle: const pw.TextStyle(fontSize: 9),
            cellPadding: const pw.EdgeInsets.symmetric(
              horizontal: 8,
              vertical: 5,
            ),
          ),
          pw.SizedBox(height: 18),
          pw.Text(
            'Dossiers affichés (${_queue.length})',
            style: pw.TextStyle(fontSize: 13, fontWeight: pw.FontWeight.bold),
          ),
          pw.SizedBox(height: 7),
          if (_queue.isEmpty)
            pw.Text(
              'Aucun dossier dans la file pour les filtres actuels.',
              style: const pw.TextStyle(fontSize: 9),
            )
          else
            pw.TableHelper.fromTextArray(
              headers: const ['Référence', 'Document', 'Étape', 'État'],
              data: _queue
                  .map(
                    (row) => [
                      '${row['reference'] ?? ''}',
                      '${row['title'] ?? ''}',
                      '${row['stage_label'] ?? row['current_stage'] ?? ''}',
                      '${row['state_label'] ?? row['state'] ?? ''}',
                    ],
                  )
                  .toList(),
              headerStyle: pw.TextStyle(
                fontWeight: pw.FontWeight.bold,
                color: PdfColors.white,
              ),
              headerDecoration: const pw.BoxDecoration(
                color: PdfColors.blue800,
              ),
              cellStyle: const pw.TextStyle(fontSize: 8),
              cellPadding: const pw.EdgeInsets.symmetric(
                horizontal: 6,
                vertical: 5,
              ),
              columnWidths: {
                0: const pw.FlexColumnWidth(1.4),
                1: const pw.FlexColumnWidth(3.6),
                2: const pw.FlexColumnWidth(1.4),
                3: const pw.FlexColumnWidth(1.4),
              },
            ),
        ],
      ),
    );
    await Printing.layoutPdf(
      name: 'rapport-suivi-documentaire.pdf',
      onLayout: (_) => report.save(),
    );
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
                            onPrint: _printReport,
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
                          else if (_panel == 'versions_todo' ||
                              _panel == 'history')
                            _VersionsTodoPanel(
                              data: data,
                              historyMode: _panel == 'history',
                            )
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
    required this.onPrint,
    required this.periodDays,
    required this.onPeriodChanged,
  });

  final Map<String, dynamic> data;
  final bool busy;
  final void Function() onRefresh;
  final void Function() onPrint;
  final int periodDays;
  final ValueChanged<int?> onPeriodChanged;

  @override
  Widget build(BuildContext context) {
    final updated = (data['updated_at'] ?? '').toString();
    return GedCard(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxWidth < 620;
          final contextLabel = data['head'] == true
              ? 'CNE-ITP · Pôle 2 · Supervision'
              : 'CNE-ITP · Pôle 2 · Poste 11';
          final controls = Wrap(
            spacing: 10,
            runSpacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            alignment: compact ? WrapAlignment.start : WrapAlignment.end,
            children: [
              if (updated.isNotEmpty)
                Text(
                  'Mise à jour · ${frDateTime(updated)}',
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
                label: 'Imprimer',
                icon: Icons.print_outlined,
                secondary: true,
                busy: false,
                onTap: onPrint,
              ),
              GedButton(
                label: 'Actualiser',
                icon: Icons.refresh_outlined,
                secondary: true,
                busy: busy,
                onTap: onRefresh,
              ),
            ],
          );
          if (compact) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  contextLabel,
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    letterSpacing: .4,
                    color: AppColors.rdcBlue,
                  ),
                ),
                const SizedBox(height: 8),
                controls,
              ],
            );
          }
          return Row(
            children: [
              Expanded(
                child: Text(
                  contextLabel,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    letterSpacing: .4,
                    color: AppColors.rdcBlue,
                  ),
                ),
              ),
              controls,
            ],
          );
        },
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

class _LibraryPanel extends StatefulWidget {
  const _LibraryPanel({required this.data});

  final Map<String, dynamic> data;

  @override
  State<_LibraryPanel> createState() => _LibraryPanelState();
}

class _LibraryPanelState extends State<_LibraryPanel> {
  final _search = TextEditingController();

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  static const _statusLabels = {
    'CONFIRMED': 'Confirmé',
    'PENDING': 'À confirmer',
    'RETURNED': 'À corriger',
  };

  @override
  Widget build(BuildContext context) {
    final allRows = rowsOf(widget.data['results']);
    final query = _search.text.trim().toLowerCase();
    final results = allRows.where((row) {
      final latest = row['latest'] as Map? ?? const {};
      final haystack =
          '${row['reference'] ?? ''} ${row['title'] ?? ''} '
                  '${row['sc'] ?? ''} ${latest['code'] ?? ''}'
              .toLowerCase();
      return query.isEmpty || haystack.contains(query);
    }).toList();
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const GedSectionTitle('Documents GED', Icons.library_books_outlined),
          const SizedBox(height: 4),
          const Text(
            'Registre des dossiers reçus au CTC, avec leur code, leur contrôle et les versions disponibles.',
            style: TextStyle(fontSize: 12, color: AppColors.muted),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 18,
            runSpacing: 8,
            children: [
              GedKpi(value: allRows.length, label: 'Dossiers accessibles'),
              GedKpi(
                value: allRows.where((row) => row['latest'] != null).length,
                label: 'Avec version GED',
              ),
            ],
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _search,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search),
              hintText: 'Rechercher par référence, titre, SC ou code…',
              border: OutlineInputBorder(),
              isDense: true,
            ),
          ),
          const SizedBox(height: 12),
          if (results.isEmpty)
            GedEmpty(
              allRows.isEmpty
                  ? 'Aucun dossier documentaire accessible pour ce poste.'
                  : 'Aucun dossier ne correspond à votre recherche.',
            )
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
        : latest.isEmpty
        ? 'À indexer'
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
                  '${row['reference'] ?? ''} · ${latest['code'] ?? 'code à attribuer'}${latest['number'] == null ? '' : ' · v${latest['number']}'}',
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
            ' · ${versions.length} version(s) enregistrée(s)',
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

class _VersionsTodoPanel extends StatefulWidget {
  const _VersionsTodoPanel({required this.data, this.historyMode = false});

  final Map<String, dynamic> data;
  final bool historyMode;

  @override
  State<_VersionsTodoPanel> createState() => _VersionsTodoPanelState();
}

class _VersionsTodoPanelState extends State<_VersionsTodoPanel> {
  List<Map<String, dynamic>> _norms = [];
  Map<String, dynamic>? _selected;
  List<Map<String, dynamic>> _history = [];
  List<Map<String, dynamic>> _diffSegments = [];
  int? _leftVersionId;
  int? _rightVersionId;
  String? _diffNote;
  bool _comparing = false;
  final _search = TextEditingController();
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadNorms();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _loadNorms() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final rows = <Map<String, dynamic>>[];
      var page = 1;
      while (true) {
        final response = await ApiClient.dio.get(
          '/api/v1/st/ged/received-norms/',
          queryParameters: {'page': page},
        );
        final body = (response.data as Map).cast<String, dynamic>();
        rows.addAll(rowsOf(body['results']));
        final next = body['next'];
        if (next == null) break;
        page = (next as num).toInt();
      }
      if (!mounted) return;
      setState(() {
        _norms = rows;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _error = '$error';
        _loading = false;
      });
    }
  }

  Future<void> _openNorm(Map<String, dynamic> norm) async {
    setState(() {
      _selected = norm;
      _history = [];
      _diffSegments = [];
      _leftVersionId = null;
      _rightVersionId = null;
      _diffNote = null;
      _loading = true;
      _error = null;
    });
    try {
      final response = await ApiClient.dio.get(
        '/api/v1/st/ged/${norm['id']}/version-history/',
      );
      if (!mounted) return;
      setState(() {
        _history =
            (response.data as List)
                .whereType<Map>()
                .map((row) => row.cast<String, dynamic>())
                .toList()
              ..sort(
                (a, b) => ((b['version_number'] as num?)?.toInt() ?? 0)
                    .compareTo((a['version_number'] as num?)?.toInt() ?? 0),
              );
        _rightVersionId = _history.firstOrNull?['id'] as int?;
        _leftVersionId =
            (_history.length > 1 ? _history[1]['id'] : _rightVersionId) as int?;
        _loading = false;
      });
      await _compareVersions();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _error = '$error';
        _loading = false;
      });
    }
  }

  Future<void> _compareVersions() async {
    final selected = _selected;
    final left = _history
        .where((row) => row['id'] == _leftVersionId)
        .firstOrNull;
    final right = _history
        .where((row) => row['id'] == _rightVersionId)
        .firstOrNull;
    if (selected == null || right == null) return;
    if (left == null || left['id'] == right['id']) {
      setState(() {
        _diffSegments = [
          {
            'type': 'equal',
            'text':
                right['content'] ??
                'Aucun texte disponible pour cette version.',
          },
        ];
        _diffNote = _history.length < 2
            ? 'Une seule version enregistrée · v${right['version_number']}'
            : 'Lecture de la version v${right['version_number']}.';
        _comparing = false;
      });
      return;
    }
    setState(() => _comparing = true);
    try {
      final response = await ApiClient.dio.get(
        '/api/v1/st/ged/${selected['id']}/version-history/compare/',
        queryParameters: {'left': left['id'], 'right': right['id']},
      );
      if (!mounted || _selected?['id'] != selected['id']) return;
      final result = (response.data as Map).cast<String, dynamic>();
      setState(() {
        _diffSegments = rowsOf(result['diff_segments']);
        _diffNote =
            'Comparaison de v${left['version_number']} vers v${right['version_number']}'
            '${result['note'] == null ? '' : ' · ${result['note']}'}';
        _comparing = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _diffSegments = [];
        _diffNote = '$error';
        _comparing = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final query = _search.text.trim().toLowerCase();
    final filtered = _norms.where((item) {
      final haystack =
          '${item['reference'] ?? ''} ${item['title'] ?? ''} ${item['sc'] ?? ''}'
              .toLowerCase();
      return query.isEmpty || haystack.contains(query);
    }).toList();
    final selected = _selected;
    return GedCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: GedSectionTitle(
                  widget.historyMode
                      ? 'Historique des versions'
                      : 'Versions à traiter',
                  widget.historyMode ? Icons.history : Icons.copy_all_outlined,
                ),
              ),
              Text(
                '${_norms.length}',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                  color: AppColors.rdcBlue,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            widget.historyMode
                ? 'Toutes les normes reçues au CTC. Sélectionnez une norme pour consulter et comparer ses versions.'
                : 'Normes réceptionnées au CTC. Sélectionnez un dossier pour examiner les versions en attente de contrôle.',
            style: const TextStyle(fontSize: 12, color: AppColors.muted),
          ),
          const SizedBox(height: 12),
          if (_error != null)
            GedFailed(
              title: 'Chargement impossible',
              detail: _error!,
              onRetry: selected == null
                  ? _loadNorms
                  : () => _openNorm(selected),
            ),
          if (_loading)
            const Padding(
              padding: EdgeInsets.all(20),
              child: Center(child: CircularProgressIndicator()),
            ),
          if (!_loading && _error == null && selected == null) ...[
            TextField(
              controller: _search,
              onChanged: (_) => setState(() {}),
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.search),
                hintText: 'Référence, titre ou sous-commission…',
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),
            const SizedBox(height: 12),
            if (_norms.isEmpty)
              const GedEmpty('Aucune norme réceptionnée au CTC.')
            else if (filtered.isEmpty)
              const GedEmpty('Aucune norme ne correspond à votre recherche.')
            else
              for (final norm in filtered)
                Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  clipBehavior: Clip.antiAlias,
                  child: InkWell(
                    onTap: () => _openNorm(norm),
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Row(
                        children: [
                          Container(
                            width: 42,
                            height: 42,
                            decoration: BoxDecoration(
                              color: AppColors.rdcBlue.withValues(alpha: .10),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(
                              Icons.description_outlined,
                              color: AppColors.rdcBlue,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '${norm['reference'] ?? ''}',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w800,
                                    color: AppColors.rdcBlue,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  '${norm['title'] ?? ''}',
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  '${norm['sc']?.toString().isNotEmpty == true ? norm['sc'] : 'SC non renseignée'} · ${norm['version_count'] ?? 0} version(s) · Réception · ${frDate(norm['received_at'])}',
                                  style: const TextStyle(
                                    fontSize: 11,
                                    color: AppColors.muted,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const Icon(
                            Icons.chevron_right,
                            color: AppColors.muted,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
          ],
          if (!_loading && _error == null && selected != null) ...[
            Row(
              children: [
                IconButton(
                  onPressed: () => setState(() {
                    _selected = null;
                  }),
                  icon: const Icon(Icons.arrow_back),
                  tooltip: 'Retour aux normes',
                ),
                Expanded(
                  child: Text(
                    '${selected['reference']} · ${selected['title']}',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontWeight: FontWeight.w800,
                      fontSize: 16,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              '${selected['sc']?.toString().isNotEmpty == true ? selected['sc'] : 'SC non renseignée'} · Réception le ${frDate(selected['received_at'])}',
              style: const TextStyle(fontSize: 12, color: AppColors.muted),
            ),
            const SizedBox(height: 12),
            LayoutBuilder(
              builder: (context, constraints) => constraints.maxWidth >= 650
                  ? Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(flex: 4, child: _historyTimeline()),
                        const SizedBox(width: 16),
                        Expanded(flex: 6, child: _differencePanel()),
                      ],
                    )
                  : Column(
                      children: [
                        _differencePanel(),
                        const SizedBox(height: 14),
                        _historyTimeline(),
                      ],
                    ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _historyTimeline() {
    final contributors = _history
        .map((row) => row['version_author'])
        .where((id) => id != null)
        .toSet()
        .length;
    return _historyPanel(
      icon: Icons.history,
      title: 'Historique des modifications',
      child: _history.isEmpty
          ? const GedEmpty('Aucune version enregistrée pour ce document.')
          : Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (contributors > 0) ...[
                  Container(
                    margin: const EdgeInsets.only(bottom: 10),
                    padding: const EdgeInsets.symmetric(
                      horizontal: 9,
                      vertical: 5,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.blueSoft,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      '$contributors contributeur${contributors > 1 ? 's' : ''}',
                      style: const TextStyle(
                        fontSize: 10,
                        color: AppColors.rdcBlue,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ],
                for (var index = 0; index < _history.length; index++)
                  _versionHistoryTile(_history[index], index),
              ],
            ),
    );
  }

  Widget _versionHistoryTile(Map<String, dynamic> version, int index) {
    final selected = version['id'] == _rightVersionId;
    final author = '${version['author_name'] ?? 'Auteur non renseigné'}'.trim();
    final status = version['status_label']?.toString();
    final compareIndex = _history.length > 1 ? (index == 0 ? 1 : 0) : index;
    return Padding(
      padding: const EdgeInsets.only(bottom: 7),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 18,
            child: Column(
              children: [
                Container(
                  width: 11,
                  height: 11,
                  margin: const EdgeInsets.only(top: 11),
                  decoration: BoxDecoration(
                    color: selected ? AppColors.rdcBlue : AppColors.surface,
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: AppColors.rdcBlue,
                      width: selected ? 3 : 2,
                    ),
                  ),
                ),
                if (index < _history.length - 1)
                  Container(
                    width: 1.5,
                    height: 54,
                    margin: const EdgeInsets.symmetric(vertical: 3),
                    color: AppColors.border,
                  ),
              ],
            ),
          ),
          const SizedBox(width: 7),
          Expanded(
            child: Material(
              color: selected ? AppColors.blueSoft : AppColors.surfaceAlt,
              borderRadius: BorderRadius.circular(10),
              child: InkWell(
                borderRadius: BorderRadius.circular(10),
                onTap: () {
                  setState(() {
                    _rightVersionId = version['id'] as int?;
                    _leftVersionId = _history[compareIndex]['id'] as int?;
                  });
                  _compareVersions();
                },
                child: Container(
                  padding: const EdgeInsets.fromLTRB(10, 8, 8, 7),
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: selected
                          ? AppColors.rdcBlue.withValues(alpha: .32)
                          : AppColors.border,
                    ),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 7,
                              vertical: 3,
                            ),
                            decoration: BoxDecoration(
                              color: selected
                                  ? AppColors.rdcBlue
                                  : AppColors.surface,
                              borderRadius: BorderRadius.circular(5),
                            ),
                            child: Text(
                              'v${version['version_number']}',
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w800,
                                color: selected ? Colors.white : AppColors.text,
                              ),
                            ),
                          ),
                          const Spacer(),
                          Flexible(
                            child: Text(
                              frDateTime(version['created_at']),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              textAlign: TextAlign.right,
                              style: const TextStyle(
                                fontSize: 10,
                                color: AppColors.muted,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 5),
                      Text(
                        '${version['summary'] ?? 'Aucun résumé fourni.'}',
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 11,
                          height: 1.25,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 5),
                      Row(
                        children: [
                          const Icon(
                            Icons.person_outline,
                            size: 13,
                            color: AppColors.muted,
                          ),
                          const SizedBox(width: 3),
                          Expanded(
                            child: Text(
                              author,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                fontSize: 10,
                                color: AppColors.muted,
                              ),
                            ),
                          ),
                          if (status != null && status.isNotEmpty) ...[
                            const SizedBox(width: 6),
                            Flexible(
                              child: Text(
                                status,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                textAlign: TextAlign.right,
                                style: const TextStyle(
                                  fontSize: 9,
                                  color: AppColors.muted,
                                ),
                              ),
                            ),
                          ],
                          const SizedBox(width: 4),
                          Icon(
                            _history.length < 2
                                ? Icons.visibility_outlined
                                : Icons.compare_arrows,
                            size: 15,
                            color: AppColors.rdcBlue,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _differencePanel() {
    final versions = _history;
    final canCompare = versions.length > 1;
    final versionOptions = versions
        .map(
          (row) => DropdownMenuItem<int>(
            value: (row['id'] as num).toInt(),
            child: Text(
              'v${row['version_number']} · ${row['author_name'] ?? 'Auteur non renseigné'}',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        )
        .toList();
    return _historyPanel(
      icon: Icons.compare_arrows,
      title: 'Analyse des différences',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (versions.isNotEmpty)
            Row(
              children: [
                Expanded(
                  child: _versionSelector(
                    'Source',
                    _leftVersionId,
                    versionOptions,
                    canCompare,
                    (id) {
                      setState(() => _leftVersionId = id);
                      _compareVersions();
                    },
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _versionSelector(
                    'Cible',
                    _rightVersionId,
                    versionOptions,
                    true,
                    (id) {
                      setState(() => _rightVersionId = id);
                      _compareVersions();
                    },
                  ),
                ),
              ],
            ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12,
            runSpacing: 6,
            children: const [
              _DiffLegend(label: 'Inchangé'),
              _DiffLegend(label: 'Suppression', color: Color(0xffffdddd)),
              _DiffLegend(label: 'Ajout', color: Color(0xffe6eaff)),
            ],
          ),
          if (_diffNote != null)
            Padding(
              padding: const EdgeInsets.only(top: 10, bottom: 8),
              child: Text(
                _diffNote!,
                style: const TextStyle(fontSize: 11, color: AppColors.muted),
              ),
            ),
          Container(
            constraints: const BoxConstraints(minHeight: 170, maxHeight: 470),
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.surface,
              border: Border.all(color: AppColors.border),
              borderRadius: BorderRadius.circular(12),
            ),
            child: _comparing
                ? const Center(child: CircularProgressIndicator())
                : _history.isEmpty
                ? const Text(
                    'Aucun contenu versionné disponible.',
                    style: TextStyle(color: AppColors.muted),
                  )
                : SingleChildScrollView(
                    child: SelectableText.rich(
                      TextSpan(
                        children: _diffSegments.map((segment) {
                          final type = segment['type'];
                          final color = type == 'delete'
                              ? const Color(0xffc62828)
                              : type == 'insert'
                              ? const Color(0xff3216a8)
                              : AppColors.text;
                          final background = type == 'delete'
                              ? const Color(0xffffdddd)
                              : type == 'insert'
                              ? const Color(0xffe6eaff)
                              : Colors.transparent;
                          return TextSpan(
                            text: '${segment['text'] ?? ''}',
                            style: TextStyle(
                              color: color,
                              backgroundColor: background,
                              fontSize: 12,
                              height: 1.6,
                              decoration: type == 'delete'
                                  ? TextDecoration.lineThrough
                                  : TextDecoration.none,
                              fontWeight: type == 'equal'
                                  ? FontWeight.normal
                                  : FontWeight.w700,
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _versionSelector(
    String label,
    int? value,
    List<DropdownMenuItem<int>> options,
    bool enabled,
    ValueChanged<int?> onChanged,
  ) {
    return Column(
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
        const SizedBox(height: 4),
        DropdownButtonFormField<int>(
          key: ValueKey('$label:$value:${options.length}'),
          initialValue: value,
          isExpanded: true,
          items: options,
          onChanged: enabled ? onChanged : null,
          decoration: const InputDecoration(
            isDense: true,
            border: OutlineInputBorder(),
            contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 10),
          ),
        ),
      ],
    );
  }

  Widget _historyPanel({
    required IconData icon,
    required String title,
    required Widget child,
  }) => Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: AppColors.surface,
      border: Border.all(color: AppColors.border),
      borderRadius: BorderRadius.circular(14),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 18, color: AppColors.rdcBlue),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                title,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ],
        ),
        const Divider(height: 20),
        child,
      ],
    ),
  );
}

class _DiffLegend extends StatelessWidget {
  const _DiffLegend({required this.label, this.color = Colors.transparent});
  final String label;
  final Color color;
  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Container(
        width: 10,
        height: 10,
        decoration: BoxDecoration(
          color: color,
          border: Border.all(color: AppColors.border),
          borderRadius: BorderRadius.circular(2),
        ),
      ),
      const SizedBox(width: 4),
      Text(label, style: const TextStyle(fontSize: 10, color: AppColors.muted)),
    ],
  );
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

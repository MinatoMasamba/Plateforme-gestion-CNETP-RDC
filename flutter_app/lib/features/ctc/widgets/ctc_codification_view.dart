import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../../core/api/api_client.dart';
import '../../../theme/app_colors.dart';

/// Vue « Pôle 2 · Codification » — miroir de
/// `templates/ctc/app/components/codification_view.html`.
///
/// Références existantes et rattachements du catalogue : aucun code n'est
/// attribué automatiquement, la liste est rafraîchie manuellement.
class CtcCodificationView extends StatefulWidget {
  const CtcCodificationView({super.key});

  @override
  State<CtcCodificationView> createState() => _CtcCodificationViewState();
}

class _CtcCodificationViewState extends State<CtcCodificationView> {
  bool _loading = true;
  String? _error;
  String _query = '';
  List<Map<String, dynamic>> _rows = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await ApiClient.dio.get(
        '/api/v1/mobile/ctc/codification/',
      );
      final results = response.data['results'] as List? ?? [];
      if (!mounted) return;
      setState(() {
        _rows = results.whereType<Map<String, dynamic>>().toList();
        _loading = false;
      });
    } on DioException catch (error) {
      final data = error.response?.data;
      final detail = data is Map ? data['detail']?.toString() : null;
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = detail ?? 'Codification indisponible depuis le serveur CTC.';
      });
    }
  }

  List<Map<String, dynamic>> get _filtered {
    final query = _query.trim().toLowerCase();
    if (query.isEmpty) return _rows;
    return _rows.where((row) {
      final haystack =
          [
            row['reference'],
            row['title'],
            row['type_label'],
            row['status_label'],
            row['ctm'],
            row['wg'],
          ].join(' ').toLowerCase();
      return haystack.contains(query);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final rows = _filtered;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'PÔLE 2 · CODIFICATION',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.4,
              color: AppColors.rdcBlue,
            ),
          ),
          const SizedBox(height: 4),
          const Text(
            'Codification',
            style: TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.w800,
              color: AppColors.text,
            ),
          ),
          const SizedBox(height: 4),
          const Text(
            "Références existantes et rattachements du pôle 2. "
            "Aucun code n'est attribué automatiquement.",
            style: TextStyle(fontSize: 13, color: AppColors.muted),
          ),
          const SizedBox(height: 16),
          _Toolbar(
            query: _query,
            loading: _loading,
            total: _rows.length,
            shown: rows.length,
            onQuery: (value) => setState(() => _query = value),
            onRefresh: _load,
          ),
          const SizedBox(height: 16),
          if (_error != null)
            _Banner(
              icon: Icons.error_outline,
              text: _error!,
              color: AppColors.danger,
              onRetry: _load,
            )
          else if (_loading && _rows.isEmpty)
            const Center(child: CircularProgressIndicator())
          else
            _CodificationCard(rows: rows, total: _rows.length),
        ],
      ),
    );
  }
}

class _Toolbar extends StatelessWidget {
  const _Toolbar({
    required this.query,
    required this.loading,
    required this.total,
    required this.shown,
    required this.onQuery,
    required this.onRefresh,
  });

  final String query;
  final bool loading;
  final int total;
  final int shown;
  final ValueChanged<String> onQuery;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: TextField(
            onChanged: onQuery,
            decoration: InputDecoration(
              isDense: true,
              prefixIcon: const Icon(Icons.search, size: 18, color: AppColors.muted),
              hintText: 'Filtrer par référence, titre, type, statut…',
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(11),
                borderSide: const BorderSide(color: AppColors.border),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(11),
                borderSide: const BorderSide(color: AppColors.rdcBlue),
              ),
              filled: true,
              fillColor: Colors.white,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Text(
          '$shown / $total',
          style: const TextStyle(fontSize: 11, color: AppColors.muted),
        ),
        const SizedBox(width: 12),
        OutlinedButton.icon(
          onPressed: loading ? null : onRefresh,
          icon: const Icon(Icons.refresh, size: 16),
          label: const Text('Rafraîchir'),
        ),
      ],
    );
  }
}

class _CodificationCard extends StatelessWidget {
  const _CodificationCard({required this.rows, required this.total});

  final List<Map<String, dynamic>> rows;
  final int total;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.border),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0D0F1B2D),
            blurRadius: 24,
            offset: Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Références existantes et rattachements · $total norme(s)',
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: AppColors.text,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'Touchez une ligne pour lire la référence complète. '
            'Lecture seule : aucune décision ni code attribué ici.',
            style: TextStyle(fontSize: 11, color: AppColors.muted),
          ),
          const SizedBox(height: 12),
          const Row(
            children: [
              // Miroir des colonnes <table> du template web.
              Expanded(
                flex: 3,
                child: _ColumnHeader('Référence'),
              ),
              Expanded(flex: 5, child: _ColumnHeader('Titre')),
              Expanded(flex: 2, child: _ColumnHeader('Type')),
              Expanded(flex: 3, child: _ColumnHeader('Statut')),
              Expanded(flex: 3, child: _ColumnHeader('Groupe')),
            ],
          ),
          const SizedBox(height: 4),
          if (rows.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 24),
              child: Text(
                'Aucune norme enregistrée.',
                style: TextStyle(color: AppColors.muted),
              ),
            )
          else
            for (final row in rows) _Row(row),
        ],
      ),
    );
  }
}

class _ColumnHeader extends StatelessWidget {
  const _ColumnHeader(this.label);
  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Text(
        label.toUpperCase(),
        style: const TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.8,
          color: AppColors.subtle,
        ),
      ),
    );
  }
}

class _Row extends StatelessWidget {
  const _Row(this.row);
  final Map<String, dynamic> row;

  Color _statusColor(String? status) {
    switch (status) {
      case 'HOMOLOGATED':
      case 'PUBLISHED':
        return AppColors.success;
      case 'ARCHIVED':
      case 'RETIRED':
        return AppColors.muted;
      case 'DRAFT':
        return AppColors.warning;
      case 'REJECTED':
        return AppColors.danger;
      default:
        return AppColors.rdcBlue;
    }
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = _statusColor(row['status']?.toString());
    final box = MediaQuery.sizeOf(context);
    final compact = box.width < 720;
    final reference = Text(
      row['reference'] ?? '',
      style: const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w800,
        fontFamily: 'monospace',
        color: AppColors.text,
      ),
    );
    final title = Text(
      row['title'] ?? '',
      maxLines: 2,
      overflow: TextOverflow.ellipsis,
      style: const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w600,
        color: AppColors.text,
      ),
    );
    final type = Text(
      row['type_label'] ?? '',
      style: const TextStyle(fontSize: 11, color: AppColors.muted),
    );
    final status = Text(
      row['status_label'] ?? '',
      style: TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w700,
        color: statusColor,
      ),
    );
    final group = Text(
      [row['ctm'], row['wg']].whereType<String>().where((s) => s.isNotEmpty).join(' · '),
      maxLines: 2,
      overflow: TextOverflow.ellipsis,
      style: const TextStyle(fontSize: 11, color: AppColors.subtle),
    );
    return InkWell(
      onTap: () => showModalBottomSheet<void>(
        context: context,
        showDragHandle: true,
        builder: (_) => _DetailSheet(row),
      ),
      borderRadius: BorderRadius.circular(10),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
        child: compact
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(children: [Expanded(child: reference)]),
                  const SizedBox(height: 2),
                  title,
                  const SizedBox(height: 4),
                  Wrap(spacing: 10, runSpacing: 4, children: [type, status, group]),
                ],
              )
            : Row(
                children: [
                  Expanded(flex: 3, child: reference),
                  Expanded(flex: 5, child: title),
                  Expanded(flex: 2, child: type),
                  Expanded(flex: 3, child: status),
                  Expanded(flex: 3, child: group),
                ],
              ),
      ),
    );
  }
}

class _DetailSheet extends StatelessWidget {
  const _DetailSheet(this.row);
  final Map<String, dynamic> row;

  @override
  Widget build(BuildContext context) {
    final entries = <(String, String)>[
      ('Référence', row['reference'] ?? ''),
      ('Titre', row['title'] ?? ''),
      ('Type', row['type_label'] ?? ''),
      ('Statut', row['status_label'] ?? ''),
      ('CTM', row['ctm'] ?? '—'),
      ('Groupe de travail', row['wg'] ?? '—'),
    ];
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Pôle 2 · Codification',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.2,
              color: AppColors.rdcBlue,
            ),
          ),
          const SizedBox(height: 12),
          for (final (label, value) in entries) ...[
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 3),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 150,
                    child: Text(
                      label,
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppColors.muted,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Text(
                      value,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: AppColors.text,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _Banner extends StatelessWidget {
  const _Banner({
    required this.icon,
    required this.text,
    required this.color,
    this.onRetry,
  });
  final IconData icon;
  final String text;
  final Color color;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 18, color: color),
        const SizedBox(width: 8),
        Expanded(
          child: Text(text, style: TextStyle(fontSize: 13, color: color)),
        ),
        if (onRetry != null)
          TextButton(onPressed: onRetry, child: const Text('Réessayer')),
      ],
    );
  }
}

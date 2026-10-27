import 'package:flutter/material.dart';

import '../../../core/api/api_client.dart';
import 'expert_theme.dart';

class ExpertHistoryTab extends StatefulWidget {
  const ExpertHistoryTab({super.key, this.docId, this.docTitle});

  final String? docId;
  final String? docTitle;

  @override
  State<ExpertHistoryTab> createState() => _ExpertHistoryTabState();
}

class _ExpertHistoryTabState extends State<ExpertHistoryTab> {
  List<Map<String, dynamic>> _versions = [];
  List<Map<String, dynamic>> _segments = [];
  bool _loading = true;
  bool _loadingDiff = false;
  int? _source;
  int? _target;
  String? _error;
  String? _diffError;
  int _diffRequest = 0;

  @override
  void initState() {
    super.initState();
    _loadVersions();
  }

  @override
  void didUpdateWidget(covariant ExpertHistoryTab oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.docId != widget.docId) {
      _diffRequest++;
      _versions = [];
      _segments = [];
      _source = null;
      _target = null;
      _error = null;
      _diffError = null;
      _loadingDiff = false;
      _loadVersions();
    }
  }

  Future<void> _loadVersions() async {
    final id = widget.docId;
    if (id == null) {
      _diffRequest++;
      _versions = [];
      _segments = [];
      _source = null;
      _target = null;
      _error = null;
      _diffError = null;
      _loading = false;
      _loadingDiff = false;
      return;
    }
    _diffRequest++;
    setState(() {
      _loading = true;
      _loadingDiff = false;
      _error = null;
      _diffError = null;
    });
    try {
      final resp = await ApiClient.dio.get('/api/v1/norms/$id/versions/');
      final data = resp.data;
      final raw = data is List
          ? data
          : (data is Map ? (data['results'] as List? ?? []) : const []);
      final versions =
          raw.map((e) => Map<String, dynamic>.from(e as Map)).toList()..sort(
            (a, b) => (b['version_number'] as num? ?? 0).compareTo(
              a['version_number'] as num? ?? 0,
            ),
          );
      if (!mounted) return;
      setState(() {
        _versions = versions;
        _segments = [];
        _loading = false;
        if (versions.isEmpty) {
          _source = null;
          _target = null;
        } else {
          _target = (versions.first['version_number'] as num).toInt();
          _source = versions.length > 1
              ? (versions[1]['version_number'] as num).toInt()
              : _target;
        }
      });
      if (versions.length > 1) {
        await _loadDiff();
      }
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _versions = [];
        _segments = [];
        _source = null;
        _target = null;
        _loading = false;
        _loadingDiff = false;
        _error = "Impossible de charger l'historique.";
      });
    }
  }

  Future<void> _loadDiff() async {
    final id = widget.docId;
    final source = _source;
    final target = _target;
    if (id == null ||
        source == null ||
        target == null ||
        _versions.length < 2 ||
        source == target) {
      if (mounted) {
        setState(() {
          _segments = [];
          _diffError = null;
          _loadingDiff = false;
        });
      }
      return;
    }
    final request = ++_diffRequest;
    setState(() {
      _loadingDiff = true;
      _segments = [];
      _diffError = null;
    });
    try {
      final resp = await ApiClient.dio.get(
        '/api/v1/norms/$id/diff/',
        queryParameters: {'v1': source, 'v2': target},
      );
      if (!mounted || request != _diffRequest) return;
      final data = resp.data;
      final raw = data is Map
          ? (data['diff_segments'] as List? ?? [])
          : const [];
      setState(() {
        _segments = raw
            .map((e) => Map<String, dynamic>.from(e as Map))
            .toList();
        _loadingDiff = false;
      });
    } catch (_) {
      if (!mounted || request != _diffRequest) return;
      setState(() {
        _segments = [];
        _diffError = 'Erreur lors du chargement des différences.';
        _loadingDiff = false;
      });
    }
  }

  String _date(String? raw) {
    final date = raw == null ? null : DateTime.tryParse(raw)?.toLocal();
    if (date == null) return '-';
    final day = date.day.toString().padLeft(2, '0');
    final month = date.month.toString().padLeft(2, '0');
    final hour = date.hour.toString().padLeft(2, '0');
    final minute = date.minute.toString().padLeft(2, '0');
    return '$day/$month/${date.year} $hour:$minute';
  }

  String _authorName(Map<String, dynamic> version) {
    final name = (version['author_name'] as String? ?? '').trim();
    if (name.isNotEmpty) return name;
    final email = (version['author_email'] as String? ?? '').trim();
    if (email.isNotEmpty) return email;
    final author = version['version_author'];
    if (author is Map) {
      final username = (author['username'] as String? ?? '').trim();
      if (username.isNotEmpty) return username;
    }
    return 'Inconnu';
  }

  String _authorFirstName(Map<String, dynamic> version) {
    final parts = _authorName(version).split(RegExp(r'\s+'));
    return parts.first;
  }

  String _versionLabel(Map<String, dynamic> version) {
    final number = (version['version_number'] as num? ?? 0).toInt();
    return 'v$number (${_authorFirstName(version)})';
  }

  int? _versionNumber(Map<String, dynamic>? version) {
    if (version == null) return null;
    return (version['version_number'] as num? ?? 0).toInt();
  }

  Future<void> _restore(int versionNumber, ExpertPalette p) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: p.card,
        title: Text(
          'Restaurer la version v$versionNumber ?',
          style: TextStyle(color: p.title, fontSize: 16),
        ),
        content: Text(
          'Cette action créera une nouvelle version copiée de la v$versionNumber.',
          style: TextStyle(color: p.muted, fontSize: 12),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text('Annuler', style: TextStyle(color: p.muted)),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: FilledButton.styleFrom(backgroundColor: p.blueDeep),
            child: const Text('Restaurer'),
          ),
        ],
      ),
    );
    if (confirmed != true || widget.docId == null) return;
    try {
      await ApiClient.dio.post(
        '/api/v1/norms/${widget.docId}/rollback-version/',
        data: {'version_number': versionNumber},
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('La version v$versionNumber a été restaurée.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      await _loadVersions();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Restauration impossible.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    if (widget.docId == null) return _noDocument(p);
    return LayoutBuilder(
      builder: (context, constraints) {
        final stacked = constraints.maxWidth < 900;
        final padding = EdgeInsets.all(constraints.maxWidth < 560 ? 16 : 24);
        if (stacked) {
          return SingleChildScrollView(
            padding: padding,
            child: Column(
              children: [
                SizedBox(height: 460, child: _timelineCard(p)),
                const SizedBox(height: 24),
                SizedBox(height: 560, child: _diffCard(p)),
              ],
            ),
          );
        }
        return Padding(
          padding: padding,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(width: 384, child: _timelineCard(p)),
              const SizedBox(width: 24),
              Expanded(child: _diffCard(p)),
            ],
          ),
        );
      },
    );
  }

  Widget _noDocument(ExpertPalette p) {
    return Center(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 440),
        margin: const EdgeInsets.all(24),
        padding: const EdgeInsets.all(24),
        decoration: _panelDecoration(p),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.history_toggle_off, size: 32, color: p.subtle),
            const SizedBox(height: 12),
            Text(
              'Sélectionnez un document pour afficher son historique.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: p.muted,
              ),
            ),
          ],
        ),
      ),
    );
  }

  BoxDecoration _panelDecoration(ExpertPalette p, {bool timeline = false}) {
    final borderColor = p.isDark
        ? Colors.white.withValues(alpha: 0.10)
        : (timeline ? p.blue.withValues(alpha: 0.18) : p.border);
    final color = p.isDark
        ? Color.alphaBlend(
            p.blue.withValues(alpha: timeline ? 0.025 : 0.01),
            p.card,
          )
        : (timeline ? const Color(0xFFF8FAFC) : Colors.white);
    return BoxDecoration(
      color: color,
      borderRadius: BorderRadius.circular(12),
      border: Border.all(color: borderColor),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withValues(alpha: p.isDark ? 0.20 : 0.05),
          blurRadius: 18,
          offset: const Offset(0, 8),
        ),
      ],
    );
  }

  Widget _timelineCard(ExpertPalette p) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: _panelDecoration(p, timeline: true),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _panelHeader(
            p,
            icon: Icons.history,
            title: 'HISTORIQUE DES MODIFICATIONS',
            iconColor: p.blue,
          ),
          const SizedBox(height: 16),
          Expanded(child: _timelineBody(p)),
        ],
      ),
    );
  }

  Widget _timelineBody(ExpertPalette p) {
    if (_loading) {
      return Center(
        child: CircularProgressIndicator(color: p.blue, strokeWidth: 2),
      );
    }
    if (_error != null) {
      return Center(
        child: Text(
          _error!,
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 11.5, color: p.red),
        ),
      );
    }
    if (_versions.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.info_outline, size: 22, color: p.subtle),
            const SizedBox(height: 8),
            Text(
              "Aucun historique d'édition enregistré.",
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 11.5, color: p.muted),
            ),
          ],
        ),
      );
    }
    return SingleChildScrollView(
      padding: const EdgeInsets.only(right: 4),
      child: Stack(
        children: [
          Positioned(
            left: 17,
            top: 10,
            bottom: 10,
            child: Container(
              width: 2,
              color: p.isDark
                  ? Colors.white.withValues(alpha: 0.05)
                  : p.borderStrong,
            ),
          ),
          Column(
            children: [
              for (final version in _versions) _timelineEntry(p, version),
            ],
          ),
        ],
      ),
    );
  }

  Widget _timelineEntry(ExpertPalette p, Map<String, dynamic> version) {
    final number = _versionNumber(version) ?? 0;
    final summary = (version['summary'] as String? ?? '').trim();
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 36,
            child: Padding(
              padding: const EdgeInsets.only(top: 7),
              child: Align(
                alignment: Alignment.topCenter,
                child: _timelineDot(p, number),
              ),
            ),
          ),
          Expanded(
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: p.isDark
                    ? Colors.white.withValues(alpha: 0.02)
                    : Colors.black.withValues(alpha: 0.025),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: p.border),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 6,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: p.surface,
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(color: p.border),
                        ),
                        child: Text(
                          'v$number',
                          style: TextStyle(
                            fontSize: 9.5,
                            fontFamily: 'monospace',
                            fontWeight: FontWeight.w700,
                            color: p.isDark ? p.text : p.muted,
                          ),
                        ),
                      ),
                      const Spacer(),
                      Text(
                        _date(version['created_at'] as String?),
                        style: TextStyle(
                          fontSize: 9.5,
                          fontFamily: 'monospace',
                          color: p.muted,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 9),
                  Text(
                    summary.isEmpty ? '"Aucun résumé fourni."' : '"$summary"',
                    maxLines: 3,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 11.5,
                      height: 1.45,
                      fontWeight: FontWeight.w600,
                      color: p.text,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(Icons.person_outline, size: 12, color: p.subtle),
                      const SizedBox(width: 4),
                      Expanded(
                        child: Text(
                          _authorName(version),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            color: p.muted,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 9),
                  Divider(height: 1, color: p.border),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      InkWell(
                        onTap: () {
                          final other = _versions.firstWhere(
                            (item) => _versionNumber(item) != number,
                            orElse: () => version,
                          );
                          setState(() {
                            _source = number;
                            _target = _versionNumber(other);
                            _segments = [];
                            _diffError = null;
                          });
                          _loadDiff();
                        },
                        child: Text(
                          'Comparer',
                          style: TextStyle(
                            fontSize: 10.5,
                            fontWeight: FontWeight.w700,
                            color: p.blue,
                          ),
                        ),
                      ),
                      const Spacer(),
                      InkWell(
                        onTap: () => _restore(number, p),
                        child: Row(
                          children: [
                            Icon(Icons.rotate_left, size: 12, color: p.amber),
                            const SizedBox(width: 4),
                            Text(
                              'Restaurer',
                              style: TextStyle(
                                fontSize: 10.5,
                                fontWeight: FontWeight.w700,
                                color: p.amber,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _timelineDot(ExpertPalette p, int number) {
    final selectedSource = _source == number;
    final selectedTarget = _target == number;
    final active = selectedSource || selectedTarget;
    final filled = selectedTarget && !selectedSource;
    return Transform.scale(
      scale: active ? 1.08 : 1,
      child: Container(
        width: 18,
        height: 18,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: filled
              ? p.blue
              : (p.isDark ? const Color(0xFF020204) : Colors.white),
          border: Border.all(
            color: active
                ? p.blue
                : (p.isDark
                      ? Colors.white.withValues(alpha: 0.20)
                      : p.borderStrong),
            width: 2,
          ),
          boxShadow: active
              ? [
                  BoxShadow(
                    color: p.blue.withValues(alpha: 0.45),
                    blurRadius: 8,
                  ),
                ]
              : null,
        ),
        child: filled
            ? Center(
                child: Container(
                  width: 3,
                  height: 3,
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                  ),
                ),
              )
            : null,
      ),
    );
  }

  Widget _diffCard(ExpertPalette p) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: _panelDecoration(p),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _diffHeader(p),
          const SizedBox(height: 16),
          _legend(p),
          const SizedBox(height: 16),
          Expanded(
            child: Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: p.isDark ? const Color(0xFF050507) : Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: p.border),
              ),
              child: _diffBody(p),
            ),
          ),
        ],
      ),
    );
  }

  Widget _diffHeader(ExpertPalette p) {
    return Container(
      padding: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: p.border)),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final title = Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.compare_arrows, size: 18, color: p.muted),
              const SizedBox(width: 8),
              SizedBox(
                width: 120,
                child: Text(
                  'ANALYSE DES DIFFÉRENCES',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 12,
                    height: 1.25,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.5,
                    color: p.title,
                  ),
                ),
              ),
            ],
          );
          final controls = _diffControls(p);
          if (constraints.maxWidth < 600) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                title,
                const SizedBox(height: 10),
                Align(alignment: Alignment.centerRight, child: controls),
              ],
            );
          }
          return Row(
            children: [
              Expanded(child: title),
              const SizedBox(width: 12),
              controls,
            ],
          );
        },
      ),
    );
  }

  Widget _diffControls(ExpertPalette p) {
    return Wrap(
      alignment: WrapAlignment.end,
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: 6,
      runSpacing: 6,
      children: [
        _versionControl(p, 'SOURCE', true),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 2),
          child: Text('→', style: TextStyle(fontSize: 12, color: p.subtle)),
        ),
        _versionControl(p, 'CIBLE', false),
      ],
    );
  }

  Widget _versionControl(ExpertPalette p, String label, bool source) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          '$label :',
          style: TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.2,
            color: p.muted,
          ),
        ),
        const SizedBox(width: 6),
        _versionPicker(p, source),
      ],
    );
  }

  Widget _versionPicker(ExpertPalette p, bool source) {
    final value = source ? _source : _target;
    final validValue =
        _versions.any((version) => _versionNumber(version) == value)
        ? value
        : null;
    return Container(
      width: 120,
      height: 30,
      padding: const EdgeInsets.only(left: 8, right: 4),
      decoration: BoxDecoration(
        color: p.field,
        borderRadius: BorderRadius.circular(7),
        border: Border.all(color: p.border),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<int>(
          value: validValue,
          isExpanded: true,
          isDense: true,
          itemHeight: 48,
          dropdownColor: p.surface,
          focusColor: Colors.transparent,
          icon: Icon(Icons.expand_more, size: 14, color: p.subtle),
          style: TextStyle(
            fontSize: 10.5,
            fontFamily: 'monospace',
            color: p.text,
          ),
          items: [
            for (final version in _versions)
              DropdownMenuItem<int>(
                value: _versionNumber(version),
                child: Text(
                  _versionLabel(version),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
          ],
          onChanged: _versions.isEmpty
              ? null
              : (selected) {
                  if (selected == null) return;
                  setState(() {
                    if (source) {
                      _source = selected;
                    } else {
                      _target = selected;
                    }
                    _segments = [];
                    _diffError = null;
                  });
                  _loadDiff();
                },
        ),
      ),
    );
  }

  Widget _legend(ExpertPalette p) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: p.isDark
            ? Colors.white.withValues(alpha: 0.02)
            : p.blueSoft.withValues(alpha: 0.55),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: p.isDark
              ? Colors.white.withValues(alpha: 0.05)
              : p.blue.withValues(alpha: 0.18),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 1),
            child: Icon(Icons.help_outline, size: 16, color: p.blue),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text.rich(
              TextSpan(
                style: TextStyle(fontSize: 11, height: 1.55, color: p.muted),
                children: [
                  TextSpan(
                    text: 'Légende : ',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: p.isDark ? p.text : const Color(0xFF334155),
                    ),
                  ),
                  const TextSpan(
                    text:
                        'Le texte inchangé reste en gris neutre. Les mots ou paragraphes supprimés apparaissent en ',
                  ),
                  WidgetSpan(
                    alignment: PlaceholderAlignment.middle,
                    child: _legendBadge(
                      p,
                      'rouge barré',
                      p.red,
                      lineThrough: true,
                    ),
                  ),
                  const TextSpan(
                    text: '. Les ajouts de rédaction apparaissent en ',
                  ),
                  WidgetSpan(
                    alignment: PlaceholderAlignment.middle,
                    child: _legendBadge(p, 'bleu', p.blue),
                  ),
                  const TextSpan(text: '.'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _diffBody(ExpertPalette p) {
    if (_loading) {
      return Center(
        child: CircularProgressIndicator(color: p.blue, strokeWidth: 2),
      );
    }
    if (_versions.length < 2) {
      return _emptyState(
        p,
        icon: Icons.info_outline,
        message: 'Pas assez de versions enregistrées pour comparer.',
      );
    }
    if (_source == null || _target == null) {
      return _emptyState(
        p,
        icon: Icons.info_outline,
        message: 'Sélectionnez une version pour afficher les différences.',
      );
    }
    if (_source == _target) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 40,
              height: 40,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: p.surface,
                border: Border.all(color: p.border),
              ),
              child: Text(
                'v$_source',
                style: TextStyle(
                  fontSize: 10.5,
                  fontFamily: 'monospace',
                  fontWeight: FontWeight.w700,
                  color: p.muted,
                ),
              ),
            ),
            const SizedBox(height: 10),
            Text(
              'Vous comparez la version v$_source avec elle-même.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: p.title,
              ),
            ),
          ],
        ),
      );
    }
    if (_loadingDiff) {
      return Center(
        child: CircularProgressIndicator(color: p.blue, strokeWidth: 2),
      );
    }
    if (_diffError != null) {
      return Center(
        child: Text(
          _diffError!,
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 11.5, color: p.red),
        ),
      );
    }
    if (_segments.isEmpty) {
      return Center(
        child: Text(
          'Aucune différence significative détectée.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 11.5, color: p.subtle),
        ),
      );
    }
    final spans = <TextSpan>[];
    for (final segment in _segments) {
      final type = segment['type'] as String? ?? 'equal';
      final text = segment['text'] as String? ?? '';
      if (text.isEmpty) continue;
      if (RegExp(r'^\s+$').hasMatch(text)) {
        spans.add(TextSpan(text: text));
      } else if (type == 'delete') {
        spans.add(
          TextSpan(
            text: text,
            style: TextStyle(
              color: p.red,
              backgroundColor: p.red.withValues(alpha: 0.14),
              decoration: TextDecoration.lineThrough,
              decorationColor: p.red,
            ),
          ),
        );
      } else if (type == 'insert') {
        spans.add(
          TextSpan(
            text: text,
            style: TextStyle(
              color: p.isDark ? const Color(0xFF60A5FA) : p.blueDeep,
              backgroundColor: p.blue.withValues(alpha: 0.15),
              fontWeight: FontWeight.w600,
            ),
          ),
        );
      } else {
        spans.add(
          TextSpan(
            text: text,
            style: TextStyle(color: p.text),
          ),
        );
      }
    }
    return SingleChildScrollView(
      child: SelectableText.rich(
        TextSpan(
          style: TextStyle(fontSize: 12.5, height: 1.7, color: p.text),
          children: spans,
        ),
      ),
    );
  }

  Widget _emptyState(
    ExpertPalette p, {
    required IconData icon,
    required String message,
  }) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 24, color: p.subtle),
          const SizedBox(height: 10),
          Text(
            message,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: p.muted,
            ),
          ),
        ],
      ),
    );
  }

  Widget _panelHeader(
    ExpertPalette p, {
    required IconData icon,
    required String title,
    required Color iconColor,
  }) {
    return Container(
      padding: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: p.border)),
      ),
      child: Row(
        children: [
          Icon(icon, size: 18, color: iconColor),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              title,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.55,
                color: p.title,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _legendBadge(
    ExpertPalette p,
    String text,
    Color color, {
    bool lineThrough = false,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 9.5,
          fontWeight: FontWeight.w700,
          color: color,
          decoration: lineThrough ? TextDecoration.lineThrough : null,
        ),
      ),
    );
  }
}

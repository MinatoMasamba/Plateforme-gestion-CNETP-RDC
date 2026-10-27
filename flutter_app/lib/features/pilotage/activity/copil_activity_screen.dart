import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api/api_client.dart';
import '../theme/copil_theme.dart';
import '../console/widgets/copil_instruction_drawer.dart';

class CopilActivityScreen extends ConsumerStatefulWidget {
  const CopilActivityScreen({super.key, this.scId});
  final int? scId;
  @override
  ConsumerState<CopilActivityScreen> createState() =>
      _CopilActivityScreenState();
}

class _CopilActivityScreenState extends ConsumerState<CopilActivityScreen> {
  Map<String, dynamic>? _data;
  String? _error;
  bool _loading = true;
  DateTime _end = DateTime.now();
  DateTime _start = DateTime.now().subtract(const Duration(days: 27));
  String _normTab = 'waiting';
  String _view = 'Vue globale';

  @override
  void initState() {
    super.initState();
    _load();
  }

  String iso(DateTime value) => value.toIso8601String().split('T').first;

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final path = widget.scId == null
          ? 'activity'
          : 'subcommission/${widget.scId}';
      final response = await ApiClient.dio.get(
        '/api/v1/mobile/pilotage/$path/',
        queryParameters: {'debut': iso(_start), 'fin': iso(_end)},
      );
      if (mounted) {
        setState(() => _data = Map<String, dynamic>.from(response.data as Map));
      }
    } catch (_) {
      if (mounted) {
        setState(
          () => _error = 'Impossible de charger les activités. Réessayez.',
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _pick(bool start) async {
    final date = await showDatePicker(
      context: context,
      initialDate: start ? _start : _end,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
    );
    if (date != null && mounted) {
      setState(() {
        if (start) {
          _start = date;
        } else {
          _end = date;
        }
      });
    }
  }

  void _openSc(Map row) => Navigator.of(context).push(
    MaterialPageRoute<void>(
      builder: (_) => CopilActivityScreen(scId: row['id'] as int),
    ),
  );

  @override
  Widget build(BuildContext context) {
    final dark = ref.watch(copilDarkProvider);
    final p = dark ? CopilPalette.dark : CopilPalette.light;
    final data = _data ?? {};
    final detail = widget.scId != null;
    Widget card(Widget child) => Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: p.card,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: p.border),
      ),
      child: child,
    );
    Widget heading(String text) => Padding(
      padding: const EdgeInsets.only(top: 24, bottom: 12),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.w700,
          color: p.title,
        ),
      ),
    );
    Widget line(String title, String subtitle) => ListTile(
      contentPadding: EdgeInsets.zero,
      title: Text(
        title,
        style: TextStyle(color: p.title, fontWeight: FontWeight.w600),
      ),
      subtitle: Text(subtitle, style: TextStyle(color: p.muted)),
    );
    final rows = data['subcommissions'] as List? ?? [];
    return CopilTheme(
      palette: p,
      child: Scaffold(
        backgroundColor: p.bg,
        appBar: AppBar(
          backgroundColor: p.card,
          foregroundColor: p.title,
          title: const Text(
            'PILOTAGE CNE-ITP',
            style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800),
          ),
          actions: [
            IconButton(
              tooltip: 'Changer le thème',
              onPressed: () =>
                  ref.read(copilDarkProvider.notifier).state = !dark,
              icon: Icon(
                dark ? Icons.light_mode_outlined : Icons.dark_mode_outlined,
              ),
            ),
          ],
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
            ? Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(_error!),
                    OutlinedButton(
                      onPressed: _load,
                      child: const Text('Réessayer'),
                    ),
                  ],
                ),
              )
            : SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 1240),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          detail
                              ? 'Pilotage › Activités › ${data['code']}'
                              : 'Pilotage › Activités › $_view',
                          style: TextStyle(fontSize: 12, color: p.muted),
                        ),
                        const SizedBox(height: 20),
                        Text(
                          detail
                              ? 'Activité · ${data['name']}'
                              : 'Supervision des sous-commissions',
                          style: TextStyle(
                            fontSize: 30,
                            fontWeight: FontWeight.w700,
                            color: p.title,
                          ),
                        ),
                        const SizedBox(height: 10),
                        Text(
                          'Consultez l’organisation courante et les activités réellement enregistrées.',
                          style: TextStyle(color: p.muted),
                        ),
                        if (detail)
                          Align(
                            alignment: Alignment.centerRight,
                            child: OutlinedButton(
                              onPressed: () =>
                                  showCopilInstruction(context, global: false),
                              child: const Text('Donner une instruction'),
                            ),
                          ),
                        const SizedBox(height: 24),
                        card(
                          Wrap(
                            spacing: 12,
                            runSpacing: 12,
                            crossAxisAlignment: WrapCrossAlignment.center,
                            children: [
                              Text(
                                'PÉRIODE ANALYSÉE',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700,
                                  color: p.muted,
                                ),
                              ),
                              OutlinedButton(
                                onPressed: () => _pick(true),
                                child: Text('Début : ${iso(_start)}'),
                              ),
                              OutlinedButton(
                                onPressed: () => _pick(false),
                                child: Text('Fin : ${iso(_end)}'),
                              ),
                              FilledButton(
                                onPressed: _load,
                                child: const Text('Actualiser'),
                              ),
                            ],
                          ),
                        ),
                        if (!detail) ...[
                          const SizedBox(height: 20),
                          Wrap(
                            spacing: 8,
                            children: [
                              for (final view in [
                                'Vue globale',
                                'Sous-commissions',
                              ])
                                ChoiceChip(
                                  label: Text(view),
                                  selected: _view == view,
                                  onSelected: (_) =>
                                      setState(() => _view = view),
                                ),
                            ],
                          ),
                          if (_view == 'Vue globale') ...[
                            heading('Vue globale'),
                            card(
                              Wrap(
                                spacing: 48,
                                runSpacing: 20,
                                children: [
                                  Text(
                                    '${rows.length}\nSous-commissions',
                                    style: TextStyle(
                                      fontSize: 20,
                                      color: p.title,
                                    ),
                                  ),
                                  Text(
                                    '${data['group_count']}\nGroupes de travail du rapport',
                                    style: TextStyle(
                                      fontSize: 20,
                                      color: p.title,
                                    ),
                                  ),
                                  Text(
                                    '${((data['metrics'] as Map?)?['production'] as Map?)?['sources'] ?? 0}\nTâches suivies sur la période',
                                    style: TextStyle(
                                      fontSize: 20,
                                      color: p.title,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            heading('Indicateurs de suivi'),
                            Wrap(
                              spacing: 12,
                              runSpacing: 12,
                              children: [
                                for (final entry in {
                                  'advancement': 'AVANCEMENT',
                                  'production': 'PRODUCTION',
                                  'quality': 'QUALITÉ',
                                  'engagement': 'ENGAGEMENT',
                                  'completeness': 'COMPLÉTUDE',
                                }.entries)
                                  SizedBox(
                                    width: 210,
                                    child: card(
                                      Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            entry.value,
                                            style: TextStyle(
                                              fontSize: 12,
                                              color: p.muted,
                                            ),
                                          ),
                                          const SizedBox(height: 12),
                                          Text(
                                            '${((data['metrics'] as Map?)?[entry.key] as Map?)?['value'] ?? 'Non configuré'}',
                                            style: TextStyle(
                                              fontSize: 18,
                                              color: p.title,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                          ],
                          heading('Sous-commissions'),
                          for (final row in rows)
                            Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: card(
                                ListTile(
                                  title: Text(
                                    '${row['code']}',
                                    style: TextStyle(
                                      color: p.blue,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                  subtitle: Text(
                                    '${row['name']}',
                                    style: TextStyle(color: p.text),
                                  ),
                                  trailing: const Icon(Icons.arrow_forward),
                                  onTap: () => _openSc(row as Map),
                                ),
                              ),
                            ),
                        ] else ...[
                          heading('Structure de coordination'),
                          Wrap(
                            spacing: 12,
                            runSpacing: 12,
                            children: [
                              for (final row
                                  in data['coordination'] as List? ?? [])
                                SizedBox(
                                  width: 320,
                                  child: card(
                                    line(
                                      '${row['title']}',
                                      '${row['holder']}'.isEmpty
                                          ? 'Titulaire à confirmer'
                                          : '${row['holder']}',
                                    ),
                                  ),
                                ),
                            ],
                          ),
                          heading('Normes de la sous-commission'),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: [
                              for (final tab in {
                                'waiting': 'En attente',
                                'working': 'En plein travail',
                                'produced': 'Produites',
                                'unconfirmed': 'Non rattachées',
                              }.entries)
                                ChoiceChip(
                                  label: Text(
                                    '${tab.value} · ${((data['norms'] as Map?)?[tab.key] as List? ?? []).length}',
                                  ),
                                  selected: _normTab == tab.key,
                                  onSelected: (_) =>
                                      setState(() => _normTab = tab.key),
                                ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          card(
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                if (((data['norms'] as Map?)?[_normTab]
                                            as List? ??
                                        [])
                                    .isEmpty)
                                  Text(
                                    'Aucune norme rattachée de façon confirmée.',
                                    style: TextStyle(color: p.muted),
                                  ),
                                for (final norm
                                    in (data['norms'] as Map?)?[_normTab]
                                            as List? ??
                                        [])
                                  line('${norm['title']}', '${norm['status']}'),
                              ],
                            ),
                          ),
                          heading('Groupes de travail'),
                          for (final group in data['groups'] as List? ?? [])
                            Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: card(
                                ExpansionTile(
                                  title: Text(
                                    '${group['code']} — ${group['name']}',
                                    style: TextStyle(
                                      color: p.title,
                                      fontSize: 14,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                  subtitle: Text(
                                    'Avancement : ${(group['metrics']['advancement'] as Map)['value'] ?? 'Non configuré'}',
                                    style: TextStyle(color: p.muted),
                                  ),
                                  children: [
                                    for (final task
                                        in group['tasks'] as List? ?? [])
                                      line(
                                        '${task['title']}',
                                        '${task['status']}',
                                      ),
                                    if ((group['tasks'] as List? ?? []).isEmpty)
                                      line(
                                        'Aucune tâche suivie',
                                        'Les activités apparaîtront après leur enregistrement.',
                                      ),
                                  ],
                                ),
                              ),
                            ),
                        ],
                        const SizedBox(height: 40),
                      ],
                    ),
                  ),
                ),
              ),
      ),
    );
  }
}

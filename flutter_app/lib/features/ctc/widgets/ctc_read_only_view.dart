import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../../core/api/api_client.dart';
import '../../../theme/app_colors.dart';

class CtcReadOnlyView extends StatefulWidget {
  const CtcReadOnlyView({super.key, required this.view});

  final String view;

  @override
  State<CtcReadOnlyView> createState() => _CtcReadOnlyViewState();
}

class _CtcReadOnlyViewState extends State<CtcReadOnlyView> {
  List<Map<String, dynamic>>? _rows;
  String? _error;
  String _query = '';
  String? _referential;
  Map<String, int> _summary = const {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _error = null);
    try {
      final response = await ApiClient.dio.get(
        '/api/v1/mobile/ctc/${widget.view}/',
      );
      final data = response.data as Map<String, dynamic>;
      if (!mounted) return;
      setState(() {
        _rows = (data['results'] as List? ?? [])
            .whereType<Map<String, dynamic>>()
            .toList();
        _summary = {
          for (final key in [
            'count',
            'complete',
            'incomplete',
            'without_login',
          ])
            key: (data[key] as num?)?.toInt() ?? 0,
        };
        final referential = data['referential'];
        _referential = referential is Map
            ? '${referential['code'] ?? ''} · ${referential['status'] ?? ''}'
            : null;
      });
    } on DioException catch (error) {
      if (!mounted) return;
      final data = error.response?.data;
      setState(
        () => _error = data is Map
            ? (data['detail']?.toString() ?? 'Données indisponibles.')
            : 'Données indisponibles.',
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final experts = widget.view == 'experts';
    final rows = _rows?.where((row) {
      if (_query.isEmpty) return true;
      return row.values.any(
        (value) => value.toString().toLowerCase().contains(_query),
      );
    }).toList();
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 26, 24, 48),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1120),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'SUPERVISION · COORDINATION DU SECRÉTARIAT TECHNIQUE',
                style: TextStyle(
                  color: AppColors.rdcBlue,
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  letterSpacing: .6,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                experts ? 'Experts et affectations' : 'Traçabilité',
                style: const TextStyle(
                  fontSize: 27,
                  fontWeight: FontWeight.w800,
                  color: AppColors.text,
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'Consultation en lecture seule des données enregistrées.',
                style: TextStyle(color: AppColors.muted),
              ),
              if (_referential != null) ...[
                const SizedBox(height: 8),
                Text(
                  'Référentiel : $_referential',
                  style: const TextStyle(color: AppColors.muted, fontSize: 12),
                ),
              ],
              const SizedBox(height: 22),
              if (_error != null) ...[
                Text(_error!, style: const TextStyle(color: Colors.red)),
                TextButton(onPressed: _load, child: const Text('Réessayer')),
              ] else if (rows == null)
                const Center(child: CircularProgressIndicator())
              else ...[
                if (experts) ...[
                  LayoutBuilder(
                    builder: (context, constraints) {
                      final columns = constraints.maxWidth >= 760 ? 4 : 2;
                      final width = constraints.maxWidth / columns;
                      final items = [
                        ('Experts enregistrés', _summary['count'] ?? 0),
                        ('Profils complets', _summary['complete'] ?? 0),
                        ('Profils à compléter', _summary['incomplete'] ?? 0),
                        (
                          'Sans connexion connue',
                          _summary['without_login'] ?? 0,
                        ),
                      ];
                      return Wrap(
                        runSpacing: 8,
                        children: [
                          for (final item in items)
                            SizedBox(
                              width: width,
                              child: Card(
                                color: Colors.white,
                                child: Padding(
                                  padding: const EdgeInsets.all(12),
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        '${item.$2}',
                                        style: const TextStyle(
                                          fontSize: 25,
                                          fontWeight: FontWeight.w800,
                                          color: AppColors.text,
                                        ),
                                      ),
                                      Text(
                                        item.$1,
                                        style: const TextStyle(
                                          fontSize: 11,
                                          color: AppColors.muted,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ),
                        ],
                      );
                    },
                  ),
                  const SizedBox(height: 18),
                ],
                TextField(
                  decoration: InputDecoration(
                    labelText: experts
                        ? 'Rechercher un expert'
                        : 'Rechercher une action',
                    prefixIcon: const Icon(Icons.search),
                    border: const OutlineInputBorder(),
                  ),
                  onChanged: (value) =>
                      setState(() => _query = value.toLowerCase().trim()),
                ),
                const SizedBox(height: 16),
                Text(
                  '${rows.length} résultat(s)',
                  style: const TextStyle(color: AppColors.muted),
                ),
                const SizedBox(height: 12),
                if (rows.isEmpty)
                  const Text('Aucune donnée enregistrée pour cette recherche.')
                else
                  for (final row in rows) ...[
                    SizedBox(
                      width: double.infinity,
                      child: Card(
                        color: Colors.white,
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: experts
                                ? [
                                    Text(
                                      '${row['name'] ?? ''}',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                    const SizedBox(height: 5),
                                    Text(
                                      '${row['structure'] ?? 'Structure non renseignée'}',
                                    ),
                                    Text(
                                      '${row['sc_code'] ?? 'SC non renseignée'} · ${row['sc_name'] ?? ''}',
                                    ),
                                    Text(
                                      '${row['affectation_label'] ?? ''}',
                                      style: const TextStyle(
                                        color: AppColors.muted,
                                      ),
                                    ),
                                  ]
                                : [
                                    Text(
                                      '${row['action'] ?? ''} · ${row['object'] ?? ''}',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                    const SizedBox(height: 5),
                                    Text(
                                      '${row['actor'] ?? ''} · ${row['timestamp'] ?? ''}',
                                    ),
                                    if ('${row['reference'] ?? ''}'.isNotEmpty)
                                      Text('${row['reference']}'),
                                    if ('${row['title'] ?? ''}'.isNotEmpty)
                                      Text('${row['title']}'),
                                  ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                  ],
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class CtcInstructionsView extends StatefulWidget {
  const CtcInstructionsView({super.key});

  @override
  State<CtcInstructionsView> createState() => _CtcInstructionsViewState();
}

class _CtcInstructionsViewState extends State<CtcInstructionsView> {
  late Future<Map<String, dynamic>> _future = _fetch();

  Future<Map<String, dynamic>> _fetch() async {
    final response = await ApiClient.dio.get(
      '/api/v1/mobile/ctc/instructions/',
    );
    return response.data as Map<String, dynamic>;
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<Map<String, dynamic>>(
    future: _future,
    builder: (context, snapshot) {
      final data = snapshot.data;
      final ctms = (data?['ctms'] as List? ?? [])
          .whereType<Map<String, dynamic>>()
          .toList();
      final general = data?['general'];
      return SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(24, 26, 24, 48),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1120),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'TRAVAIL · COORDINATION DU SECRÉTARIAT TECHNIQUE',
                  style: TextStyle(
                    color: AppColors.rdcBlue,
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Instructions',
                  style: TextStyle(
                    fontSize: 27,
                    fontWeight: FontWeight.w800,
                    color: AppColors.text,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Directives de production adressées aux sous-commissions (CTM).',
                  style: TextStyle(color: AppColors.muted),
                ),
                const SizedBox(height: 22),
                if (snapshot.hasError) ...[
                  const Text('Les instructions sont indisponibles.'),
                  TextButton(
                    onPressed: () => setState(() => _future = _fetch()),
                    child: const Text('Réessayer'),
                  ),
                ] else if (data == null)
                  const Center(child: CircularProgressIndicator())
                else ...[
                  const Text(
                    'INSTRUCTION GÉNÉRALE',
                    style: TextStyle(
                      color: AppColors.rdcBlue,
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 8),
                  if (general is Map<String, dynamic>)
                    _InstructionCard(general)
                  else
                    const Text('Aucune instruction générale enregistrée.'),
                  const SizedBox(height: 24),
                  Text(
                    'Sous-commissions (CTM) · ${ctms.length}',
                    style: const TextStyle(
                      fontSize: 19,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 14),
                  if (ctms.isEmpty)
                    const Text('Aucune sous-commission enregistrée.'),
                  for (final ctm in ctms) ...[
                    SizedBox(
                      width: double.infinity,
                      child: Card(
                        color: Colors.white,
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'CTM ${ctm['number'] ?? ''}',
                                style: const TextStyle(
                                  color: AppColors.muted,
                                  fontSize: 11,
                                ),
                              ),
                              const SizedBox(height: 5),
                              Text(
                                '${ctm['name'] ?? ''}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              const Divider(),
                              if (ctm['last_instruction']
                                  is Map<String, dynamic>)
                                _InstructionCard(ctm['last_instruction'])
                              else
                                const Text('Aucune instruction reçue.'),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                  ],
                ],
              ],
            ),
          ),
        ),
      );
    },
  );
}

class _InstructionCard extends StatelessWidget {
  const _InstructionCard(this.instruction);

  final Map<String, dynamic> instruction;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        '${instruction['objet'] ?? ''}',
        style: const TextStyle(fontWeight: FontWeight.w800),
      ),
      if ('${instruction['message'] ?? ''}'.isNotEmpty) ...[
        const SizedBox(height: 5),
        Text('${instruction['message']}'),
      ],
      const SizedBox(height: 7),
      Text(
        [
          instruction['portee'],
          instruction['statut'],
          if (instruction['echeance'] != null)
            'Échéance : ${instruction['echeance']}',
          if (instruction['nb_normes'] != null)
            '${instruction['nb_normes']} normes attendues',
        ].where((value) => value != null && '$value'.isNotEmpty).join(' · '),
        style: const TextStyle(color: AppColors.muted, fontSize: 12),
      ),
    ],
  );
}

class CtcNormsView extends StatefulWidget {
  const CtcNormsView({super.key, required this.view});

  final String view;

  @override
  State<CtcNormsView> createState() => _CtcNormsViewState();
}

class _CtcNormsViewState extends State<CtcNormsView> {
  late Future<List<Map<String, dynamic>>> _future = _fetch();
  String _query = '';

  Future<List<Map<String, dynamic>>> _fetch() async {
    final response = await ApiClient.dio.get(
      '/api/v1/mobile/ctc/${widget.view}/',
    );
    final data = response.data as Map<String, dynamic>;
    return (data['results'] as List? ?? [])
        .whereType<Map<String, dynamic>>()
        .toList();
  }

  @override
  Widget build(
    BuildContext context,
  ) => FutureBuilder<List<Map<String, dynamic>>>(
    future: _future,
    builder: (context, snapshot) {
      final archives = widget.view == 'archives';
      final rows = snapshot.data?.where((row) {
        if (_query.isEmpty) return true;
        return '${row['reference']} ${row['title']}'.toLowerCase().contains(
          _query,
        );
      }).toList();
      return SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(24, 26, 24, 48),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1120),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  archives
                      ? 'SYSTÈME · COORDINATION DU SECRÉTARIAT TECHNIQUE'
                      : 'SUPERVISION · COORDINATION DU SECRÉTARIAT TECHNIQUE',
                  style: const TextStyle(
                    color: AppColors.rdcBlue,
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  archives ? 'Archives' : 'Homologations',
                  style: const TextStyle(
                    fontSize: 27,
                    fontWeight: FontWeight.w800,
                    color: AppColors.text,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  archives
                      ? 'Recherche dans les normes réellement archivées.'
                      : 'Normes homologuées ou publiées en lecture seule.',
                  style: const TextStyle(color: AppColors.muted),
                ),
                const SizedBox(height: 22),
                if (snapshot.hasError) ...[
                  const Text('Les normes sont indisponibles.'),
                  TextButton(
                    onPressed: () => setState(() => _future = _fetch()),
                    child: const Text('Réessayer'),
                  ),
                ] else if (rows == null)
                  const Center(child: CircularProgressIndicator())
                else ...[
                  TextField(
                    decoration: const InputDecoration(
                      labelText: 'Référence ou titre',
                      prefixIcon: Icon(Icons.search),
                      border: OutlineInputBorder(),
                    ),
                    onChanged: (value) =>
                        setState(() => _query = value.trim().toLowerCase()),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    '${rows.length} norme(s)',
                    style: const TextStyle(color: AppColors.muted),
                  ),
                  const SizedBox(height: 12),
                  if (rows.isEmpty)
                    Text(
                      archives
                          ? 'Aucune norme archivée enregistrée.'
                          : 'Aucune norme homologuée ou publiée enregistrée.',
                    ),
                  for (final row in rows) ...[
                    SizedBox(
                      width: double.infinity,
                      child: Card(
                        color: Colors.white,
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${row['reference'] ?? ''}',
                                style: const TextStyle(
                                  color: AppColors.rdcBlue,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '${row['title'] ?? ''}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                '${row['status'] ?? ''}',
                                style: const TextStyle(color: AppColors.muted),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                  ],
                ],
              ],
            ),
          ),
        ),
      );
    },
  );
}

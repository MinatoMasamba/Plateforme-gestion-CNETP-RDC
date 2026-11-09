import 'package:flutter/material.dart';

class ReportCoverEditor extends StatelessWidget {
  const ReportCoverEditor({
    super.key,
    required this.cover,
    required this.onChanged,
    required this.preview,
    this.readOnly = false,
  });
  final Map<String, dynamic> cover;
  final VoidCallback onChanged;
  final VoidCallback preview;
  final bool readOnly;
  static const labels = {
    'organization': 'Organisme',
    'department': 'Service ou département',
    'title': 'Titre sur la couverture',
    'subtitle': 'Sous-titre',
    'recipient': 'À l’attention de',
    'subject': 'Objet',
    'issuer': 'Émetteur',
    'date': 'Date à afficher',
    'reference': 'Référence à afficher',
    'footer': 'Pied de couverture',
    'brand': 'Signature du corps du rapport',
  };
  static const limits = {
    'organization': 180,
    'department': 180,
    'title': 250,
    'subtitle': 180,
    'recipient': 200,
    'subject': 200,
    'issuer': 150,
    'date': 150,
    'reference': 150,
    'brand': 80,
    'footer': 150,
  };
  @override
  Widget build(BuildContext context) => Material(
    color: Colors.transparent,
    child: ExpansionTile(
      title: const Text('Page zéro · couverture bleue'),
      subtitle: const Text(
        'Le même dessin de couverture est utilisé pour les exports PDF et Word.',
      ),
      children: [
        const Text(
          'Personnalisez les rubriques et les quatre indicateurs. Les champs laissés vides reprennent les valeurs par défaut du rapport lors de l’export. Dans Word, cette couverture est un visuel : modifiez ses rubriques ici avant de télécharger.',
        ),
        const SizedBox(height: 12),
        for (final entry in labels.entries)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: TextFormField(
              initialValue: '${cover[entry.key] ?? ''}',
              readOnly: readOnly,
              maxLength: limits[entry.key],
              decoration: InputDecoration(
                labelText: entry.value,
                border: const OutlineInputBorder(),
              ),
              onChanged: (value) {
                cover[entry.key] = value;
                onChanged();
              },
            ),
          ),
        for (var i = 0; i < 4; i++) ...[
          Text(
            'Indicateur ${i + 1}',
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  initialValue: _stat(i, 'value'),
                  readOnly: readOnly,
                  maxLength: 20,
                  decoration: const InputDecoration(
                    labelText: 'Valeur',
                    border: OutlineInputBorder(),
                  ),
                  onChanged: (v) => _setStat(i, 'value', v),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextFormField(
                  initialValue: _stat(i, 'label'),
                  readOnly: readOnly,
                  maxLength: 60,
                  decoration: const InputDecoration(
                    labelText: 'Libellé',
                    border: OutlineInputBorder(),
                  ),
                  onChanged: (v) => _setStat(i, 'label', v),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
        ],
        OutlinedButton.icon(
          onPressed: preview,
          icon: const Icon(Icons.visibility_outlined),
          label: const Text('Voir la page de couverture'),
        ),
        const SizedBox(height: 12),
      ],
    ),
  );
  String _stat(int i, String key) {
    final stats = cover['stats'] as List? ?? [];
    return i < stats.length ? '${stats[i][key] ?? ''}' : '';
  }

  void _setStat(int i, String key, String value) {
    final stats =
        cover.putIfAbsent('stats', () => <Map<String, String>>[]) as List;
    while (stats.length <= i) {
      stats.add({'value': '', 'label': ''});
    }
    stats[i][key] = value;
    onChanged();
  }
}

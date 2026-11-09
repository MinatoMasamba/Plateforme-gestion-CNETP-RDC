import 'package:flutter/material.dart';

class ReportTableBlock {
  ReportTableBlock(this.start, this.end, this.rows);
  final int start, end;
  final List<List<String>> rows;
  String get text => '${rows.map((r) => r.join(' | ')).join('\n')}\n';
}

List<ReportTableBlock> reportTables(String text) {
  final tables = <ReportTableBlock>[];
  var offset = 0, start = 0;
  var rows = <List<String>>[];
  void flush() {
    if (rows.length > 1) {
      tables.add(ReportTableBlock(start, offset, rows));
    }
    rows = [];
  }

  for (final line in text.split('\n')) {
    if (line.contains(' | ')) {
      if (rows.isEmpty) start = offset;
      rows.add(line.split(' | ').map((v) => v.trim()).toList());
    } else {
      flush();
    }
    offset += line.length + 1;
  }
  flush();
  return tables;
}

Future<List<ReportTableBlock>?> editReportTables(
  BuildContext context,
  String text,
) => showDialog<List<ReportTableBlock>>(
  context: context,
  builder: (context) => _TableDialog(tables: reportTables(text)),
);

class _TableDialog extends StatefulWidget {
  const _TableDialog({required this.tables});
  final List<ReportTableBlock> tables;
  @override
  State<_TableDialog> createState() => _TableDialogState();
}

class _TableDialogState extends State<_TableDialog> {
  int _selected = 0;
  String? _error;
  @override
  Widget build(BuildContext context) {
    if (widget.tables.isEmpty) {
      return const AlertDialog(
        content: Text('Aucun tableau dans cette section.'),
      );
    }
    final table = widget.tables[_selected];
    final columns = table.rows.fold<int>(
      0,
      (n, row) => n > row.length ? n : row.length,
    );
    for (final row in table.rows) {
      while (row.length < columns) {
        row.add('');
      }
    }
    return AlertDialog(
      title: const Text('Modifier les tableaux du modèle'),
      content: SizedBox(
        width: 800,
        height: 460,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (widget.tables.length > 1)
              DropdownButton<int>(
                value: _selected,
                isExpanded: true,
                items: List.generate(
                  widget.tables.length,
                  (i) => DropdownMenuItem(
                    value: i,
                    child: Text('Tableau ${i + 1}'),
                  ),
                ),
                onChanged: (i) => setState(() => _selected = i!),
              ),
            const Text(
              'Renseignez les cellules. La première ligne contient les en-têtes.',
            ),
            const SizedBox(height: 12),
            Expanded(
              child: SingleChildScrollView(
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Column(
                    children: [
                      for (var r = 0; r < table.rows.length; r++)
                        Container(
                          key: ObjectKey(table.rows[r]),
                          margin: const EdgeInsets.only(bottom: 8),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              for (var c = 0; c < columns; c++)
                                SizedBox(
                                  width: 190,
                                  child: Padding(
                                    padding: const EdgeInsets.only(right: 8),
                                    child: TextFormField(
                                      initialValue: table.rows[r][c],
                                      minLines: 1,
                                      maxLines: 4,
                                      maxLength: 4000,
                                      decoration: InputDecoration(
                                        labelText: r == 0
                                            ? 'En-tête ${c + 1}'
                                            : 'Ligne $r · colonne ${c + 1}',
                                        border: const OutlineInputBorder(),
                                        filled: r == 0,
                                      ),
                                      onChanged: (v) => table.rows[r][c] = v,
                                    ),
                                  ),
                                ),
                              if (r > 0)
                                IconButton(
                                  tooltip: 'Retirer la ligne $r',
                                  onPressed: table.rows.length <= 2
                                      ? null
                                      : () => setState(
                                          () => table.rows.removeAt(r),
                                        ),
                                  icon: const Icon(Icons.remove_circle_outline),
                                ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
            if (_error != null)
              Text(_error!, style: const TextStyle(color: Colors.red)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: [
                TextButton.icon(
                  onPressed: table.rows.length >= 200
                      ? null
                      : () => setState(
                          () => table.rows.add(List.filled(columns, '')),
                        ),
                  icon: const Icon(Icons.add),
                  label: const Text('Ajouter une ligne'),
                ),
                TextButton.icon(
                  onPressed: columns >= 12
                      ? null
                      : () => setState(() {
                          for (final row in table.rows) {
                            row.add('');
                          }
                        }),
                  icon: const Icon(Icons.view_column_outlined),
                  label: const Text('Ajouter une colonne'),
                ),
              ],
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Annuler'),
        ),
        FilledButton(
          onPressed: () {
            if (widget.tables.any(
              (t) => t.rows.any(
                (r) => r.any((c) => c.contains('\n') || c.contains(' | ')),
              ),
            )) {
              setState(
                () => _error =
                    'Utilisez une seule ligne par cellule et / pour séparer plusieurs valeurs.',
              );
              return;
            }
            Navigator.pop(context, widget.tables);
          },
          child: const Text('Appliquer les tableaux'),
        ),
      ],
    );
  }
}

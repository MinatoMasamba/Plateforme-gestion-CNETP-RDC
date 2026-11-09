import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

/// Coordinates are normalized to the original page, independent of screen size.
class ReportFixedEditor extends StatefulWidget {
  const ReportFixedEditor({
    super.key,
    required this.api,
    required this.source,
    required this.fields,
    required this.onChanged,
    this.readOnly = false,
    this.startPage = 0,
  });
  final Dio api;
  final Map<String, dynamic> source;
  final List<Map<String, dynamic>> fields;
  final VoidCallback onChanged;
  final bool readOnly;
  final int startPage;
  @override
  State<ReportFixedEditor> createState() => _ReportFixedEditorState();
}

class _ReportFixedEditorState extends State<ReportFixedEditor> {
  int _page = 0;
  @override
  void initState() {
    super.initState();
    _page = widget.startPage;
  }

  final _images = <String, Future<Uint8List>>{};
  Future<Uint8List> _image() =>
      _images.putIfAbsent('${widget.source['id']}:$_page', () async {
        final result = await widget.api.get<List<int>>(
          '/api/v1/st/reports/sources/${widget.source['id']}/',
          queryParameters: {'page': _page},
          options: Options(responseType: ResponseType.bytes),
        );
        return Uint8List.fromList(result.data!);
      });

  Future<void> _edit(Map<String, dynamic> field, {bool adding = false}) async {
    if (widget.readOnly) return;
    final text = TextEditingController(text: '${field['text']}');
    var size = (field['size'] as num).toDouble();
    var height = (field['height'] as num).toDouble();
    var width = (field['width'] as num).toDouble();
    final result = await showDialog<String>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, update) => AlertDialog(
          title: Text(adding ? 'Ajouter un champ' : 'Modifier le champ'),
          content: SizedBox(
            width: 480,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: text,
                    maxLines: 5,
                    maxLength: 4000,
                    autofocus: true,
                    decoration: const InputDecoration(
                      labelText: 'Texte à inscrire dans le modèle',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const Text('Taille du texte'),
                  Slider(
                    value: size,
                    min: .005,
                    max: .1,
                    onChanged: (v) => update(() => size = v),
                  ),
                  const Text('Largeur du champ'),
                  Slider(
                    value: width,
                    min: .02,
                    max: 1 - (field['x'] as num).toDouble(),
                    onChanged: (v) => update(() => width = v),
                  ),
                  const Text('Hauteur du champ'),
                  Slider(
                    value: height.clamp(
                      .01,
                      1 - (field['y'] as num).toDouble(),
                    ),
                    min: .01,
                    max: 1 - (field['y'] as num).toDouble(),
                    onChanged: (v) => update(() => height = v),
                  ),
                  const Text(
                    'Le texte est ajouté sur une copie. Placez le champ dans une zone libre du modèle.',
                  ),
                ],
              ),
            ),
          ),
          actions: [
            if (!adding)
              TextButton(
                onPressed: () => Navigator.pop(context, 'delete'),
                child: const Text('Supprimer le champ'),
              ),
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Annuler'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, 'save'),
              child: const Text('Appliquer'),
            ),
          ],
        ),
      ),
    );
    if (!mounted) {
      text.dispose();
      return;
    }
    setState(() {
      if (result == 'save') {
        field.addAll({'text': text.text, 'size': size, 'height': height});
        if (adding) widget.fields.add(field);
      } else if (result == 'delete') {
        widget.fields.remove(field);
      }
    });
    text.dispose();
    if (result != null) widget.onChanged();
  }

  @override
  Widget build(BuildContext context) {
    final pages = widget.source['pages'] as List;
    if (_page >= pages.length || _page < widget.startPage) {
      _page = widget.startPage;
    }
    final meta = pages[_page] as Map;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Présentation conservée',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        const Text(
          'Cliquez dans une zone libre de la page pour ajouter un champ. Cliquez sur un champ pour le modifier.',
        ),
        const Text(
          'Le PDF conserve le fond original. L’export Word de ce mode contient des pages rendues ; choisissez la rédaction libre pour obtenir du texte Word modifiable.',
        ),
        Row(
          children: [
            IconButton(
              tooltip: 'Page précédente',
              onPressed: _page > widget.startPage
                  ? () => setState(() => _page--)
                  : null,
              icon: const Icon(Icons.chevron_left),
            ),
            Text('Page ${_page + 1} / ${pages.length}'),
            IconButton(
              tooltip: 'Page suivante',
              onPressed: _page + 1 < pages.length
                  ? () => setState(() => _page++)
                  : null,
              icon: const Icon(Icons.chevron_right),
            ),
          ],
        ),
        FutureBuilder<Uint8List>(
          future: _image(),
          builder: (context, snapshot) {
            if (snapshot.hasError) {
              return Column(
                children: [
                  const Text('Impossible de charger cette page.'),
                  TextButton(
                    onPressed: () => setState(
                      () => _images.remove('${widget.source['id']}:$_page'),
                    ),
                    child: const Text('Réessayer'),
                  ),
                ],
              );
            }
            if (!snapshot.hasData) return const LinearProgressIndicator();
            return LayoutBuilder(
              builder: (context, constraints) {
                final width = constraints.maxWidth.clamp(0.0, 900.0);
                final height =
                    width * (meta['height'] as num) / (meta['width'] as num);
                return SizedBox(
                  width: width,
                  height: height,
                  child: GestureDetector(
                    onTapUp: widget.readOnly
                        ? null
                        : (event) {
                            if (widget.fields.length >= 300) return;
                            final x = (event.localPosition.dx / width).clamp(
                              0.0,
                              .58,
                            );
                            final y = (event.localPosition.dy / height).clamp(
                              0.0,
                              .85,
                            );
                            _edit({
                              'page': _page,
                              'x': x,
                              'y': y,
                              'width': .4,
                              'height': .1,
                              'text': '',
                              'size': .02,
                            }, adding: true);
                          },
                    child: Stack(
                      children: [
                        Positioned.fill(
                          child: Image.memory(snapshot.data!, fit: BoxFit.fill),
                        ),
                        for (final field in widget.fields.where(
                          (f) => f['page'] == _page,
                        ))
                          Positioned(
                            left: (field['x'] as num) * width,
                            top: (field['y'] as num) * height,
                            width: (field['width'] as num) * width,
                            height: (field['height'] as num) * height,
                            child: GestureDetector(
                              onTap: () => _edit(field),
                              child: Container(
                                decoration: BoxDecoration(
                                  border: Border.all(
                                    color: Colors.blue.withValues(alpha: .5),
                                  ),
                                  color: Colors.blue.withValues(alpha: .04),
                                ),
                                child: Text(
                                  '${field['text']}',
                                  style: TextStyle(
                                    fontFamily: 'Arial',
                                    fontSize: (field['size'] as num) * width,
                                    color: Colors.black,
                                    height: 1.2,
                                  ),
                                ),
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                );
              },
            );
          },
        ),
      ],
    );
  }
}

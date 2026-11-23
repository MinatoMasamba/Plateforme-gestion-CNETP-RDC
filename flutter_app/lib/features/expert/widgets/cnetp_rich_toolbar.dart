import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_quill/flutter_quill.dart' as quill;

import '../../../core/rich_text/cnetp_markdown.dart';
import 'expert_theme.dart';

/// Styles Quill alignés sur la palette CNE-ITP (éditeur PC et lecture mobile).
quill.DefaultStyles cnetpQuillStyles(ExpertPalette p, {bool compact = false}) {
  final body = TextStyle(
    color: p.text,
    fontSize: ExpertType.body,
    height: ExpertType.bodyHeight,
  );
  quill.DefaultTextBlockStyle block(
    TextStyle style, {
    double top = 0,
    double bottom = 10,
    BoxDecoration? decoration,
  }) => quill.DefaultTextBlockStyle(
    style,
    quill.HorizontalSpacing.zero,
    quill.VerticalSpacing(top, bottom),
    quill.VerticalSpacing.zero,
    decoration,
  );
  TextStyle heading(double size) => TextStyle(
    color: p.title,
    fontSize: size,
    fontWeight: FontWeight.w800,
    height: 1.3,
  );
  return quill.DefaultStyles(
    paragraph: block(body),
    h1: block(heading(compact ? 20 : 24), top: 12, bottom: 8),
    h2: block(heading(compact ? 17 : 20), top: 10, bottom: 6),
    h3: block(heading(compact ? 15 : 17), top: 8, bottom: 4),
    lists: quill.DefaultListBlockStyle(
      body,
      quill.HorizontalSpacing.zero,
      const quill.VerticalSpacing(0, 6),
      quill.VerticalSpacing.zero,
      null,
      null,
    ),
    quote: block(
      body.copyWith(color: p.muted, fontStyle: FontStyle.italic),
      decoration: BoxDecoration(
        border: Border(left: BorderSide(color: p.blue, width: 4)),
      ),
    ),
    sizeSmall: const TextStyle(fontSize: 12),
    sizeLarge: const TextStyle(fontSize: 18),
    sizeHuge: const TextStyle(fontSize: 22),
    link: TextStyle(
      color: p.blue,
      decoration: TextDecoration.underline,
      decorationColor: p.blue,
    ),
  );
}

/// Ajuste les couleurs autorisées au thème (bleu nuit illisible sur fond sombre).
TextStyle Function(quill.Attribute) cnetpStyleBuilder(ExpertPalette p) =>
    (attribute) {
      if (attribute.key == quill.Attribute.color.key &&
          '${attribute.value}'.toLowerCase() == cnetpColors['nuit'] &&
          p.isDark) {
        return TextStyle(color: p.title);
      }
      if (attribute.key == quill.Attribute.background.key &&
          attribute.value != null) {
        return const TextStyle(color: Color(0xFF0A2540));
      }
      return const TextStyle();
    };

/// Ouvre le dialogue de lien ; renvoie `''` pour retirer le lien.
Future<String?> cnetpAskLink(BuildContext context, {String? initial}) {
  return showDialog<String>(
    context: context,
    builder: (context) => _LinkDialog(initial: initial),
  );
}

class _LinkDialog extends StatefulWidget {
  const _LinkDialog({this.initial});
  final String? initial;

  @override
  State<_LinkDialog> createState() => _LinkDialogState();
}

class _LinkDialogState extends State<_LinkDialog> {
  late final _url = TextEditingController(text: widget.initial ?? 'https://');
  String? _error;

  void _submit() {
    final value = _url.text.trim();
    if (!cnetpIsSafeUrl(value)) {
      setState(
        () => _error =
            'Adresse invalide : utilisez http://, https:// ou mailto:.',
      );
      return;
    }
    Navigator.pop(context, value);
  }

  @override
  void dispose() {
    _url.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Insérer un lien'),
      content: SizedBox(
        width: 420,
        child: TextField(
          key: const ValueKey('rich-link-url'),
          controller: _url,
          autofocus: true,
          keyboardType: TextInputType.url,
          decoration: InputDecoration(
            labelText: 'Adresse du lien',
            errorText: _error,
            border: const OutlineInputBorder(),
          ),
          onSubmitted: (_) => _submit(),
        ),
      ),
      actions: [
        if (widget.initial != null)
          TextButton(
            onPressed: () => Navigator.pop(context, ''),
            child: const Text('Retirer le lien'),
          ),
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Annuler'),
        ),
        FilledButton(
          key: const ValueKey('rich-link-apply'),
          onPressed: _submit,
          child: const Text('Appliquer'),
        ),
      ],
    );
  }
}

/// Actions de mise en forme communes à la barre fixe, au menu contextuel
/// et aux raccourcis clavier.
class CnetpFormatter {
  CnetpFormatter(this.controller);
  final quill.QuillController controller;

  Map<String, quill.Attribute> get _attrs =>
      controller.getSelectionStyle().attributes;

  bool has(quill.Attribute attribute) =>
      _attrs[attribute.key]?.value == attribute.value;

  dynamic value(String key) => _attrs[key]?.value;

  void toggle(quill.Attribute attribute) {
    controller.formatSelection(
      has(attribute) ? quill.Attribute.clone(attribute, null) : attribute,
    );
  }

  void setInline(quill.Attribute base, Object? value) {
    controller.formatSelection(quill.Attribute.clone(base, value));
  }

  String get blockStyle {
    final header = value(quill.Attribute.header.key);
    if (header is int) return 'h$header';
    if (value(quill.Attribute.blockQuote.key) == true) return 'quote';
    return 'p';
  }

  void setBlockStyle(String style) {
    controller.formatSelection(quill.Attribute.header);
    controller.formatSelection(
      quill.Attribute.clone(quill.Attribute.blockQuote, null),
    );
    switch (style) {
      case 'h1':
        controller.formatSelection(quill.Attribute.h1);
      case 'h2':
        controller.formatSelection(quill.Attribute.h2);
      case 'h3':
        controller.formatSelection(quill.Attribute.h3);
      case 'quote':
        controller.formatSelection(
          quill.Attribute.clone(quill.Attribute.list, null),
        );
        controller.formatSelection(quill.Attribute.blockQuote);
    }
  }

  void toggleList(quill.Attribute list) {
    if (!has(list)) {
      controller.formatSelection(
        quill.Attribute.clone(quill.Attribute.blockQuote, null),
      );
    }
    toggle(list);
  }

  void clear() {
    for (final attribute in <quill.Attribute>[
      quill.Attribute.bold,
      quill.Attribute.italic,
      quill.Attribute.underline,
      quill.Attribute.size,
      quill.Attribute.color,
      quill.Attribute.background,
      quill.Attribute.link,
    ]) {
      controller.formatSelection(quill.Attribute.clone(attribute, null));
    }
  }

  Future<void> editLink(BuildContext context) async {
    final current = value(quill.Attribute.link.key);
    final url = await cnetpAskLink(
      context,
      initial: current is String ? current : null,
    );
    if (url == null) return;
    setInline(quill.Attribute.link, url.isEmpty ? null : url);
  }
}

class _LinkIntent extends Intent {
  const _LinkIntent();
}

/// Raccourci Ctrl+K (lien) ; Ctrl+B/I/U sont gérés nativement par Quill.
Map<ShortcutActivator, Intent> cnetpShortcuts() => const {
  SingleActivator(LogicalKeyboardKey.keyK, control: true): _LinkIntent(),
  SingleActivator(LogicalKeyboardKey.keyK, meta: true): _LinkIntent(),
};

Map<Type, Action<Intent>> cnetpActions(
  BuildContext context,
  CnetpFormatter formatter,
) => {
  _LinkIntent: CallbackAction<_LinkIntent>(
    onInvoke: (_) => formatter.editLink(context),
  ),
};

/// Menu contextuel de sélection : actions système + mise en forme rapide.
Widget cnetpContextMenu(
  BuildContext context,
  quill.QuillRawEditorState state,
  CnetpFormatter formatter, {
  VoidCallback? onShare,
}) {
  final selection = formatter.controller.selection;
  final items = [...state.contextMenuButtonItems];
  if (!formatter.controller.readOnly && !selection.isCollapsed) {
    void run(VoidCallback action) {
      state.hideToolbar();
      action();
    }

    items.addAll([
      ContextMenuButtonItem(
        label: 'Gras',
        onPressed: () => run(() => formatter.toggle(quill.Attribute.bold)),
      ),
      ContextMenuButtonItem(
        label: 'Italique',
        onPressed: () => run(() => formatter.toggle(quill.Attribute.italic)),
      ),
      ContextMenuButtonItem(
        label: 'Souligné',
        onPressed: () => run(() => formatter.toggle(quill.Attribute.underline)),
      ),
      ContextMenuButtonItem(
        label: 'Surligner',
        onPressed: () => run(
          () => formatter.setInline(
            quill.Attribute.background,
            formatter.value(quill.Attribute.background.key) == null
                ? cnetpHighlight
                : null,
          ),
        ),
      ),
      ContextMenuButtonItem(
        label: 'Lien…',
        onPressed: () => run(() => formatter.editLink(context)),
      ),
    ]);
  }
  if (onShare != null && !selection.isCollapsed) {
    items.add(
      ContextMenuButtonItem(
        label: 'Partager l’extrait',
        onPressed: () {
          state.hideToolbar();
          onShare();
        },
      ),
    );
  }
  return AdaptiveTextSelectionToolbar.buttonItems(
    anchors: state.contextMenuAnchors,
    buttonItems: items,
  );
}

/// Barre d’outils fixe de l’éditeur PC.
class CnetpRichToolbar extends StatelessWidget {
  const CnetpRichToolbar({super.key, required this.formatter});
  final CnetpFormatter formatter;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return ListenableBuilder(
      listenable: formatter.controller,
      builder: (context, _) {
        final enabled = !formatter.controller.readOnly;
        Widget toggle(
          String key,
          IconData icon,
          String tooltip,
          quill.Attribute attribute, {
          VoidCallback? onPressed,
          bool? isActive,
        }) {
          final active = isActive ?? formatter.has(attribute);
          return IconButton(
            key: ValueKey('rich-$key'),
            tooltip: tooltip,
            isSelected: active,
            onPressed: enabled
                ? (onPressed ?? () => formatter.toggle(attribute))
                : null,
            style: IconButton.styleFrom(
              backgroundColor: active ? p.blue.withValues(alpha: .16) : null,
              foregroundColor: active ? p.blue : p.text,
              minimumSize: const Size(36, 36),
            ),
            icon: Icon(icon, size: 18),
          );
        }

        final size = formatter.value(quill.Attribute.size.key);
        final color = '${formatter.value(quill.Attribute.color.key) ?? ''}'
            .toLowerCase();
        final highlighted =
            '${formatter.value(quill.Attribute.background.key) ?? ''}'
                .toLowerCase() ==
            cnetpHighlight;
        Widget divider() => Container(
          width: 1,
          height: 24,
          margin: const EdgeInsets.symmetric(horizontal: 4),
          color: p.border,
        );

        return Container(
          key: const ValueKey('rich-toolbar'),
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: p.surface,
            border: Border(bottom: BorderSide(color: p.border)),
            borderRadius: const BorderRadius.vertical(top: Radius.circular(10)),
          ),
          child: Wrap(
            crossAxisAlignment: WrapCrossAlignment.center,
            spacing: 2,
            runSpacing: 2,
            children: [
              _Menu<String>(
                key: const ValueKey('rich-style'),
                tooltip: 'Style de paragraphe',
                enabled: enabled,
                value: formatter.blockStyle,
                width: 132,
                options: const {
                  'p': 'Paragraphe',
                  'h1': 'Titre 1',
                  'h2': 'Titre 2',
                  'h3': 'Titre 3',
                  'quote': 'Citation',
                },
                onSelected: formatter.setBlockStyle,
              ),
              _Menu<String>(
                key: const ValueKey('rich-size'),
                tooltip: 'Taille du texte',
                enabled: enabled,
                value: size is String && cnetpSizes.containsValue(size)
                    ? size
                    : '',
                width: 112,
                options: const {
                  '': 'Normal',
                  'small': 'Petit',
                  'large': 'Grand',
                  'huge': 'Très grand',
                },
                onSelected: (value) => formatter.setInline(
                  quill.Attribute.size,
                  value.isEmpty ? null : value,
                ),
              ),
              divider(),
              toggle(
                'bold',
                Icons.format_bold,
                'Gras (Ctrl+B)',
                quill.Attribute.bold,
              ),
              toggle(
                'italic',
                Icons.format_italic,
                'Italique (Ctrl+I)',
                quill.Attribute.italic,
              ),
              toggle(
                'underline',
                Icons.format_underlined,
                'Souligné (Ctrl+U)',
                quill.Attribute.underline,
              ),
              PopupMenuButton<String>(
                key: const ValueKey('rich-color'),
                tooltip: 'Couleur du texte',
                enabled: enabled,
                onSelected: (value) => formatter.setInline(
                  quill.Attribute.color,
                  value.isEmpty ? null : value,
                ),
                itemBuilder: (context) => [
                  const PopupMenuItem(value: '', child: Text('Automatique')),
                  for (final entry in const {
                    'bleu': 'Bleu CNE-ITP',
                    'rouge': 'Rouge',
                    'nuit': 'Bleu nuit',
                  }.entries)
                    PopupMenuItem(
                      value: cnetpColors[entry.key],
                      child: Row(
                        children: [
                          Icon(
                            Icons.circle,
                            size: 14,
                            color: _hex(cnetpColors[entry.key]!),
                          ),
                          const SizedBox(width: 8),
                          Text(entry.value),
                        ],
                      ),
                    ),
                ],
                child: Padding(
                  padding: const EdgeInsets.all(8),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.format_color_text, size: 18, color: p.text),
                      Container(
                        width: 18,
                        height: 3,
                        color: cnetpColors.containsValue(color)
                            ? _hex(color)
                            : p.text,
                      ),
                    ],
                  ),
                ),
              ),
              IconButton(
                key: const ValueKey('rich-highlight'),
                tooltip: 'Surligner en jaune',
                isSelected: highlighted,
                onPressed: enabled
                    ? () => formatter.setInline(
                        quill.Attribute.background,
                        highlighted ? null : cnetpHighlight,
                      )
                    : null,
                style: IconButton.styleFrom(
                  backgroundColor: highlighted ? const Color(0xFFFFF24B) : null,
                  foregroundColor: highlighted
                      ? const Color(0xFF0A2540)
                      : p.text,
                  minimumSize: const Size(36, 36),
                ),
                icon: const Icon(Icons.border_color_outlined, size: 18),
              ),
              divider(),
              toggle(
                'bullet',
                Icons.format_list_bulleted,
                'Liste à puces',
                quill.Attribute.ul,
                onPressed: () => formatter.toggleList(quill.Attribute.ul),
              ),
              toggle(
                'ordered',
                Icons.format_list_numbered,
                'Liste numérotée',
                quill.Attribute.ol,
                onPressed: () => formatter.toggleList(quill.Attribute.ol),
              ),
              toggle(
                'quote',
                Icons.format_quote,
                'Citation',
                quill.Attribute.blockQuote,
                onPressed: () => formatter.setBlockStyle(
                  formatter.blockStyle == 'quote' ? 'p' : 'quote',
                ),
              ),
              toggle(
                'link',
                Icons.link,
                'Lien (Ctrl+K)',
                quill.Attribute.link,
                isActive: formatter.value(quill.Attribute.link.key) != null,
                onPressed: () => formatter.editLink(context),
              ),
              divider(),
              IconButton(
                key: const ValueKey('rich-clear'),
                tooltip: 'Effacer la mise en forme',
                onPressed: enabled ? formatter.clear : null,
                style: IconButton.styleFrom(minimumSize: const Size(36, 36)),
                icon: Icon(Icons.format_clear, size: 18, color: p.text),
              ),
            ],
          ),
        );
      },
    );
  }
}

Color _hex(String value) =>
    Color(int.parse('FF${value.replaceFirst('#', '')}', radix: 16));

class _Menu<T> extends StatelessWidget {
  const _Menu({
    super.key,
    required this.tooltip,
    required this.enabled,
    required this.value,
    required this.options,
    required this.onSelected,
    required this.width,
  });

  final String tooltip;
  final bool enabled;
  final T value;
  final Map<T, String> options;
  final ValueChanged<T> onSelected;
  final double width;

  @override
  Widget build(BuildContext context) {
    final p = ExpertTheme.of(context);
    return PopupMenuButton<T>(
      tooltip: tooltip,
      enabled: enabled,
      initialValue: value,
      onSelected: onSelected,
      itemBuilder: (context) => [
        for (final entry in options.entries)
          PopupMenuItem(value: entry.key, child: Text(entry.value)),
      ],
      child: Container(
        width: width,
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          border: Border.all(color: p.border),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Expanded(
              child: Text(
                options[value] ?? options.values.first,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: p.text,
                  fontSize: ExpertType.meta,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            Icon(Icons.arrow_drop_down, size: 18, color: p.muted),
          ],
        ),
      ),
    );
  }
}

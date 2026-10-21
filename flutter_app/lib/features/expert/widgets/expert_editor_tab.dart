import 'package:flutter/material.dart';

/// Palette sombre propre à l'espace Expert (comme le template /app/).
class ExpertColors {
  static const bg = Color(0xFF020204);
  static const surface = Color(0xFF0B0B10);
  static const card = Color(0xFF0F0F16);
  static const border = Color(0x14FFFFFF);
  static const text = Color(0xFFE5EEF8);
  static const muted = Color(0xFF94A3B8);
  static const subtle = Color(0xFF64748B);
  static const blue = Color(0xFF3B82F6);
  static const blueDeep = Color(0xFF2563EB);
  static const amber = Color(0xFFF59E0B);
  static const green = Color(0xFF34D399);
  static const red = Color(0xFFF87171);
  static const teal = Color(0xFF2DD4BF);
}

/// Éditeur de normes — refonte fidèle de `module-editor` (app.html).
class ExpertEditorTab extends StatefulWidget {
  const ExpertEditorTab({
    super.key,
    required this.doc,
    required this.loading,
    required this.onSave,
  });

  final Map<String, dynamic>? doc;
  final bool loading;
  final VoidCallback onSave;

  @override
  State<ExpertEditorTab> createState() => _ExpertEditorTabState();
}

class _ExpertEditorTabState extends State<ExpertEditorTab> {
  late TextEditingController _text;
  final _comment = TextEditingController();

  @override
  void initState() {
    super.initState();
    _text = TextEditingController(text: _content());
  }

  @override
  void didUpdateWidget(covariant ExpertEditorTab oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.doc != widget.doc) {
      _text.text = _content();
    }
  }

  String _content() {
    final v = widget.doc?['latest_version'];
    if (v is Map && v['content'] is String) return v['content'] as String;
    return '';
  }

  @override
  void dispose() {
    _text.dispose();
    _comment.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.loading && widget.doc == null) {
      return const Center(child: CircularProgressIndicator());
    }
    final doc = widget.doc;
    if (doc == null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: const [
            Icon(Icons.description_outlined, size: 44, color: ExpertColors.subtle),
            SizedBox(height: 12),
            Text('Aucun document sélectionné',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: ExpertColors.text)),
            SizedBox(height: 6),
            Text('Sélectionnez un document dans la barre latérale pour commencer l\'édition.',
                style: TextStyle(fontSize: 12, color: ExpertColors.muted)),
          ],
        ),
      );
    }

    final code = doc['reference_number'] as String? ?? '—';
    final family = doc['standard_family'] as String? ?? doc['norm_type'] as String? ?? 'NCD';
    final title = doc['title'] as String? ?? '';
    final desc = doc['description'] as String? ?? '';
    final ctm = doc['ctm_name'] as String? ?? 'Non assigné';

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _documentHeader(code, family, title, desc, ctm),
          const SizedBox(height: 18),
          LayoutBuilder(
            builder: (context, c) {
              final wide = c.maxWidth >= 1000;
              final left = Expanded(
                flex: 2,
                child: Column(
                  children: [
                    _textCard(),
                    const SizedBox(height: 16),
                    _scrutinCard(),
                    const SizedBox(height: 16),
                    _versionCard(),
                  ],
                ),
              );
              final right = SizedBox(
                width: wide ? 340 : double.infinity,
                child: Column(
                  children: [
                    _aiCard(),
                    const SizedBox(height: 16),
                    _shareCard(),
                  ],
                ),
              );
              return wide
                  ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [left, const SizedBox(width: 16), right])
                  : Column(children: [left, const SizedBox(height: 16), right]);
            },
          ),
        ],
      ),
    );
  }

  Widget _documentHeader(String code, String family, String title, String desc, String ctm) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            _badge(code, ExpertColors.blue, ExpertColors.blue.withValues(alpha: 0.12), mono: true),
            const SizedBox(width: 8),
            _badge(family, ExpertColors.muted, ExpertColors.surface),
            const SizedBox(width: 10),
            const Text('• Dernière modification aujourd\'hui',
                style: TextStyle(fontSize: 11, color: ExpertColors.subtle)),
          ],
        ),
        const SizedBox(height: 10),
        Text(title,
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: ExpertColors.text)),
        if (desc.isNotEmpty) ...[
          const SizedBox(height: 6),
          Text(desc, style: const TextStyle(fontSize: 12, height: 1.5, color: ExpertColors.muted)),
        ],
        const SizedBox(height: 14),
        Row(
          children: [
            Expanded(
              child: _panel(
                child: Row(
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('SOUS-COMMISSION (CTM)',
                            style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: ExpertColors.blue, letterSpacing: 0.5)),
                        const SizedBox(height: 4),
                        Text(ctm,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: ExpertColors.text)),
                        const SizedBox(height: 4),
                        const Text('Voir Groupes (WGs) →',
                            style: TextStyle(fontSize: 9, color: ExpertColors.blue)),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(width: 12),
            _panel(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: const [
                  Text('ÉDITEUR ACTIF', style: TextStyle(fontSize: 9, color: ExpertColors.subtle, letterSpacing: 0.5)),
                  SizedBox(height: 4),
                  Text('Expert Rédacteur', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: ExpertColors.text)),
                  SizedBox(height: 2),
                  Text('Expert Rédacteur', style: TextStyle(fontSize: 9, color: ExpertColors.subtle)),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _textCard() {
    final chars = _text.text.length;
    final words = _text.text.trim().isEmpty ? 0 : _text.text.trim().split(RegExp(r'\s+')).length;
    return _panel(
      padding: EdgeInsets.zero,
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: ExpertColors.border))),
            child: Row(
              children: [
                const Text('FORMAT : TEXTE BRUT / CLAUSES ISO',
                    style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: ExpertColors.muted, letterSpacing: 0.6)),
                const Spacer(),
                Text('$chars caractères • $words mots',
                    style: const TextStyle(fontSize: 10, fontFamily: 'monospace', color: ExpertColors.subtle)),
              ],
            ),
          ),
          SizedBox(
            height: 300,
            child: TextField(
              controller: _text,
              maxLines: null,
              expands: true,
              onChanged: (_) => setState(() {}),
              style: const TextStyle(fontSize: 13, height: 1.7, color: ExpertColors.text),
              decoration: const InputDecoration(
                hintText: 'Écrivez le standard ici…',
                hintStyle: TextStyle(color: ExpertColors.subtle),
                border: InputBorder.none,
                contentPadding: EdgeInsets.all(16),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _scrutinCard() {
    return _panel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _iconTile(Icons.how_to_vote_outlined, ExpertColors.blue),
              const SizedBox(width: 10),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('SCRUTIN & ÉVALUATION THÉMATIQUE',
                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: ExpertColors.text, letterSpacing: 0.4)),
                    SizedBox(height: 2),
                    Text('Co-gouvernance scientifique (Consensus minimum requis : 75 %)',
                        style: TextStyle(fontSize: 10, color: ExpertColors.subtle)),
                  ],
                ),
              ),
              const Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text('TAUX DE VALIDATION', style: TextStyle(fontSize: 8, color: ExpertColors.subtle, letterSpacing: 0.4)),
                  SizedBox(height: 2),
                  Text('0%', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: ExpertColors.blue)),
                ],
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: const [
              Text('POUR (0)', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: ExpertColors.blue)),
              Spacer(),
              Text('CONTRE (0)', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: ExpertColors.red)),
              Spacer(),
              Text('ABS (0)', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: ExpertColors.subtle)),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(999),
            child: Container(height: 6, color: const Color(0xFF1E293B)),
          ),
          const SizedBox(height: 10),
          const Row(
            children: [
              Icon(Icons.people_outline, size: 13, color: ExpertColors.subtle),
              SizedBox(width: 5),
              Text("0 expert a émargé l'avis", style: TextStyle(fontSize: 10, color: ExpertColors.subtle)),
              Spacer(),
              Text('AVIS PARTIEL', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: ExpertColors.amber)),
            ],
          ),
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: ExpertColors.surface,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: ExpertColors.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: const [
                    Expanded(
                      child: Text("Exprimer votre voix d'expert permanent",
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: ExpertColors.text)),
                    ),
                    Text('Non voté',
                        style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: ExpertColors.amber)),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    _voteButton('POUR', Icons.thumb_up_outlined, ExpertColors.blue),
                    const SizedBox(width: 8),
                    _voteButton('CONTRE', Icons.thumb_down_outlined, ExpertColors.red),
                    const SizedBox(width: 8),
                    _voteButton('ABS.', Icons.remove, ExpertColors.muted),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _versionCard() {
    return _panel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('JOURNAL DES VERSIONS / COMMENTAIRE',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: ExpertColors.muted)),
          const SizedBox(height: 4),
          const Text('Détaillez brièvement votre modification pour conserver un historique exploitable.',
              style: TextStyle(fontSize: 10, color: ExpertColors.subtle)),
          const SizedBox(height: 10),
          TextField(
            controller: _comment,
            style: const TextStyle(fontSize: 12, color: ExpertColors.text),
            decoration: InputDecoration(
              hintText: 'Ex: Mise en conformité de la note 2…',
              hintStyle: const TextStyle(fontSize: 12, color: ExpertColors.subtle),
              filled: true,
              fillColor: ExpertColors.surface,
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(9),
                borderSide: const BorderSide(color: ExpertColors.border),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(9),
                borderSide: const BorderSide(color: ExpertColors.border),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              TextButton.icon(
                onPressed: () => _text.text = _content(),
                icon: const Icon(Icons.rotate_left, size: 15, color: ExpertColors.muted),
                label: const Text('Réinitialiser', style: TextStyle(fontSize: 11, color: ExpertColors.muted)),
              ),
              const Spacer(),
              FilledButton.icon(
                onPressed: widget.onSave,
                style: FilledButton.styleFrom(backgroundColor: ExpertColors.blueDeep),
                icon: const Icon(Icons.save_outlined, size: 15),
                label: const Text('Sauvegarder la version', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700)),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _aiCard() {
    return _panel(
      accent: ExpertColors.blue,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _iconTile(Icons.auto_awesome_outlined, ExpertColors.blue),
              const SizedBox(width: 10),
              const Expanded(
                child: Text('CONSEIL RÉGLEMENTAIRE IA',
                    style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: ExpertColors.text, letterSpacing: 0.4)),
              ),
              const Icon(Icons.close, size: 15, color: ExpertColors.subtle),
            ],
          ),
          const SizedBox(height: 10),
          const Text("L'IA intégrée évalue la rédaction par rapport aux exigences de certification ISO.",
              style: TextStyle(fontSize: 11, height: 1.5, color: ExpertColors.muted)),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: () {},
              style: FilledButton.styleFrom(backgroundColor: ExpertColors.blueDeep),
              icon: const Icon(Icons.auto_awesome, size: 15),
              label: const Text('Analyser & optimiser le texte', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _shareCard() {
    return _panel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _iconTile(Icons.share_outlined, ExpertColors.blue),
              const SizedBox(width: 10),
              const Expanded(
                child: Text('PARTAGER & DÉBATTRE',
                    style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: ExpertColors.text, letterSpacing: 0.4)),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text('Surlignez du texte à gauche pour préremplir l\'extrait à envoyer vers le chat.',
              style: TextStyle(fontSize: 10.5, height: 1.5, color: ExpertColors.muted)),
          const SizedBox(height: 12),
          const Text('EXTRAIT DE CLAUSE SÉLECTIONNÉ',
              style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: ExpertColors.subtle, letterSpacing: 0.5)),
          const SizedBox(height: 6),
          _inputPlaceholder('Sélectionnez du texte dans l\'éditeur…', maxLines: 3),
          const SizedBox(height: 10),
          const Text('EXPERT DESTINATAIRE',
              style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: ExpertColors.subtle, letterSpacing: 0.5)),
          const SizedBox(height: 6),
          _inputPlaceholder('— Sélectionner l\'expert —'),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () {},
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: ExpertColors.border),
                foregroundColor: ExpertColors.text,
              ),
              icon: const Icon(Icons.chat_bubble_outline, size: 15),
              label: const Text('Partager à l\'expert & Ouvrir le Chat', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _inputPlaceholder(String hint, {int maxLines = 1}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
      decoration: BoxDecoration(
        color: ExpertColors.surface,
        borderRadius: BorderRadius.circular(9),
        border: Border.all(color: ExpertColors.border),
      ),
      child: Text(hint,
          maxLines: maxLines,
          style: const TextStyle(fontSize: 11, color: ExpertColors.subtle)),
    );
  }

  Widget _voteButton(String label, IconData icon, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 9),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.10),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: color.withValues(alpha: 0.3)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 13, color: color),
            const SizedBox(width: 5),
            Text(label, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: color)),
          ],
        ),
      ),
    );
  }

  Widget _badge(String text, Color color, Color bg, {bool mono = false}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(6)),
      child: Text(text,
          style: TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w700,
            color: color,
            fontFamily: mono ? 'monospace' : null,
          )),
    );
  }

  Widget _iconTile(IconData icon, Color color) {
    return Container(
      width: 30,
      height: 30,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(icon, size: 15, color: color),
    );
  }

  Widget _panel({required Widget child, EdgeInsets? padding, Color? accent}) {
    return Container(
      padding: padding ?? const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: ExpertColors.card,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: accent?.withValues(alpha: 0.25) ?? ExpertColors.border),
      ),
      child: child,
    );
  }
}

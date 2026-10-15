# Charte graphique appliquée à la page A4 — CTC / Lecteur normatif

Source : `/home/minato/Documents/CHARTE GRAPHIQUE FINALE (OLGA)pdf.pdf`
(« Charte graphique du Gouvernement de la République Démocratique du Congo »)

## Règles extraites de la charte

### Architecture de marque État (p.8 et p.11)
1. **Bloc-armoirie** — toujours disposé **à gauche** de la composition.
2. **Ligne d'État** — barre **verticale** tricolore, symbole de la Nation.
   - Hauteur **= hauteur du Bloc-armoirie**.
   - Les **3 couleurs sont réparties à égalité** (aucune ne prend plus de place).
   - Ordre **de haut en bas : Bleu, Jaune, Rouge**.
   - Largeur = `X` ; zone de sécurité = `4X`.
3. **Intitulé officiel** — à droite, renseigne la structure émettrice.

### Typographie (p.14 et p.24)
- **Copper Hewitt (semi-bold)** — imposée pour l'intitulé officiel.
  (non installée localement → pile de repli `Copper Hewitt → Copperplate → Georgia serif`)

### Palette officielle (p.26 — « Les couleurs principales »)
| Couleur | Web | Pantone | CMJN | RVB |
|---|---|---|---|---|
| Bleu  | **#0095c9** | 801C | C100 M0 J0 N0 | R0 V159 B227 |
| Jaune | **#fff24b** | 803C | C0 M0 J100 N0 | R255 V237 B0 |
| Rouge | **#db3832** | 485C | C0 M100 J100 N0 | R227 V6 B19 |

## Application dans `templates/ctc/app/norme_read.html`

- **Bandeau supérieur** : Bloc-armoirie (`logo-cnetp.png`) + **Ligne d'État verticale** (3 segments **égaux** Bleu/Jaune/Rouge, hauteur = armoirie) + **intitulé officiel** en `Copper Hewitt` (3 lignes : RDC / CTC-CNE-ITP / Lecteur normatif).
- **Feuille A4** (`210mm × 297mm`, fond `#F4F6F9` autour) : bandeau d'État centré, **Ligne d'État horizontale** (3 parts égales), titre H1 en `Copper Hewitt`, cartouche de métadonnées, sections H2, corps Inter aéré.
- **Boutons** aux accents bleu institutionnel `#0095c9`.
- **Pied de page réglementaire** : **fixe en bas**, séparateur fin, mention d'usage + copyright « © 2026 Gouvernement de la RDC », **QR de traçabilité** (`/ctc/norme/<id>/qr/`).
- **Impression** : `@page { size: A4 }`, seule la feuille sort (bandeau/pied fixes masqués).

## Vérifications
- Palette `#0095c9 / #fff24b / #db3832` présente, plus aucun ancien code.
- Test E2E `test_ctc_norme_read_a4` : **PASSED**.
- Capture : `reports/e2e/ctc_norme_read_a4.png`.

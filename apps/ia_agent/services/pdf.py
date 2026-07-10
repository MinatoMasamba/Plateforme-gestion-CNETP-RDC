from graphviz import Digraph

def generer_diagramme_cnetp():
    # Initialisation du diagramme orienté (de haut en bas)
    dot = Digraph(name="Organigramme CNETP", format="pdf")
    dot.attr(rankdir='TB', splines='ortho', nodesep='0.8', ranksep='1.2')
    
    # Configuration globale de l'apparence des nœuds (Police Helvetica, bords arrondis)
    dot.attr('node', shape='box', style='filled, rounded', fontname='Helvetica-Bold', fontcolor='white', penwidth='0', margin='0.3')
    dot.attr('edge', color='#475569', penwidth='2', arrowhead='vee')

    # --- PALETTE DE COULEURS RDC ---
    BLEU_ETAT = '#007FFF'
    BLEU_FONCE = '#0f2d59'
    JAUNE_OR = '#f7d618'
    ROUGE = '#CE1126'
    GRIS = '#64748b'

    # --- CRÉATION DES NŒUDS DU DIAGRAMME ---
    
    # 1. Sommet : Le Ministère [cite: 496]
    dot.node('MINISTRE', 'Ministre des ITP\nHaute Coordination Générale', fillcolor=BLEU_ETAT, fontsize='14')

    # 2. Niveau Stratégique : Comité de Pilotage [cite: 511]
    dot.node('COPIL', 'Comité de Pilotage Élargi\n(27 Experts)\nOrientation, Arbitrage & Validation', fillcolor=BLEU_FONCE, fontsize='13')

    # 3. Niveau Opérationnel : Cellule Technique [cite: 541]
    dot.node('CTC', 'Cellule Technique de Coordination\n(20 Experts)\nGestion Journalière & Ingénierie Doc.', fillcolor=JAUNE_OR, fontcolor='black', fontsize='12')

    # 4. Niveau Exécutif : Les Groupes de Travail (WG) [cite: 564]
    # Nous créons un nœud parent pour regrouper les WG
    dot.node('WG_MAIN', 'LES 8 SOUS-COMMISSIONS\nGroupes de Travail (153 Experts)\nProduction Technique Exclusive', fillcolor=ROUGE, fontsize='12')

    # Création des 8 Sous-commissions pour montrer l'arborescence [cite: 570, 577, 586, 597, 605, 614, 624, 633]
    dot.attr('node', shape='rect', style='filled, rounded', fillcolor='#f8fafc', fontcolor='#334155', fontname='Helvetica', penwidth='1', color=ROUGE, fontsize='10')
    dot.node('WG1', 'SC 1: Géotechnique\n(19 experts)')
    dot.node('WG2', 'SC 2: Ouvrages d\'art\n(19 experts)')
    dot.node('WG3', 'SC 3: Bâtiments\n(19 experts)')
    dot.node('WG4', 'SC 4: Aéroports\n(19 experts)')
    dot.node('WG5', 'SC 5: Routes & Ports\n(19 experts)')
    dot.node('WG6', 'SC 6: Ressources Eau\n(19 experts)')
    dot.node('WG7', 'SC 7: Assainissement\n(19 experts)')
    dot.node('WG8', 'SC 8: Matériaux\n(20 experts)')

    # --- CRÉATION DES FLÈCHES DE CONNEXION (LES LIENS) ---
    dot.edge('MINISTRE', 'COPIL', label=' Délègue', fontname='Helvetica', fontsize='9', fontcolor=GRIS)
    dot.edge('COPIL', 'CTC', label=' Supervise', fontname='Helvetica', fontsize='9', fontcolor=GRIS)
    dot.edge('CTC', 'WG_MAIN', label=' Coordonne', fontname='Helvetica', fontsize='9', fontcolor=GRIS)

    # Relier le nœud principal des WG aux 8 groupes spécifiques
    # On utilise un nœud invisible pour forcer un bel alignement horizontal
    with dot.subgraph() as sous_groupes:
        sous_groupes.attr(rank='same')
        sous_groupes.edge('WG_MAIN', 'WG1', color=ROUGE)
        sous_groupes.edge('WG_MAIN', 'WG2', color=ROUGE)
        sous_groupes.edge('WG_MAIN', 'WG3', color=ROUGE)
        sous_groupes.edge('WG_MAIN', 'WG4', color=ROUGE)
        sous_groupes.edge('WG_MAIN', 'WG5', color=ROUGE)
        sous_groupes.edge('WG_MAIN', 'WG6', color=ROUGE)
        sous_groupes.edge('WG_MAIN', 'WG7', color=ROUGE)
        sous_groupes.edge('WG_MAIN', 'WG8', color=ROUGE)

    # --- GÉNÉRATION DU PDF ---
    # render(nom_du_fichier, format, view=True pour ouvrir automatiquement)
    dot.render('Diagramme_Arbre_CNETP', view=False)
    print("Le diagramme hiérarchique a été généré avec succès en PDF !")

if __name__ == '__main__':
    generer_diagramme_cnetp()
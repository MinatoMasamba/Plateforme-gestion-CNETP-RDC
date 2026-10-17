"""Organigramme du rapport de réorganisation adopté le 15 octobre 2026."""

import json
from pathlib import Path

from graphviz import Digraph


def generer_diagramme_cnetp():
    catalogue = json.loads(
        Path(__file__).resolve().parents[2]
        .joinpath('governance/rapport_adopte_2026_reference.json')
        .read_text(encoding='utf-8')
    )
    dot = Digraph(name='Organigramme CNE-ITP', format='pdf')
    dot.attr(rankdir='TB', splines='ortho', nodesep='0.8', ranksep='1.2')
    dot.attr('node', shape='box', style='filled,rounded', fontname='Helvetica-Bold',
             fontcolor='white', penwidth='0', margin='0.3')
    dot.attr('edge', color='#475569', penwidth='2', arrowhead='vee')
    dot.node('COPIL', 'Comité de pilotage\n22 postes · organe non permanent\nOrientation, arbitrage et validation', fillcolor='#0f2d59')
    dot.node('ST', 'Coordination du Secrétariat technique\n24 postes permanents\nGestion et suivi des travaux de normalisation', fillcolor='#f7d618', fontcolor='black')
    dot.node('SC', '7 sous-commissions techniques\n35 groupes de travail', fillcolor='#CE1126')
    dot.edge('COPIL', 'ST', label='Oriente et supervise')
    dot.edge('ST', 'SC', label='Coordonne les travaux')
    dot.attr('node', shape='rect', style='filled,rounded', fillcolor='#f8fafc',
             fontcolor='#334155', fontname='Helvetica', penwidth='1', color='#CE1126', fontsize='10')
    for item in sorted(catalogue['sc'], key=lambda sc: sc['tome']):
        node = item['code']
        dot.node(node, f"Tome {item['tome']} · {item['name']}\n5 groupes de travail")
        dot.edge('SC', node, color='#CE1126')
    dot.render('Diagramme_Arbre_CNETP', view=False)
    print('Le diagramme hiérarchique a été généré en PDF.')


if __name__ == '__main__':
    generer_diagramme_cnetp()

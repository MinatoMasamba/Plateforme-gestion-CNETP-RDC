"""Catalogue explicite des rapports ; les libellés sont des modèles, pas des actes officiels."""

FAMILIES = {
    'norme': 'Norme individuelle',
    'collectif': 'Production collective',
    'experts': 'Experts et formation',
    'finance': 'Finances et besoins',
    'gouvernance': 'Gouvernance et arbitrage',
    'ministere': 'Ministère et transfert',
}

COMMON = ('objet', 'realisations', 'difficultes', 'prochaines_actions', 'decision_attendue')
LABELS = {
    'objet': 'Objet et périmètre', 'realisations': 'Travaux réalisés et preuves',
    'difficultes': 'Difficultés et réserves', 'prochaines_actions': 'Prochaines actions et échéances',
    'decision_attendue': 'Décision sollicitée', 'origine': 'Origine et émetteur',
    'pieces_recues': 'Pièces reçues et lisibilité', 'anomalies': 'Anomalies et pièces manquantes',
    'versions': 'Versions et modifications', 'observations': 'Observations et traitement',
    'examens': 'Examens attendus et résultats', 'consultation': 'Consultation et conclusions',
    'transmission': 'Bordereau et destinataire', 'normes': 'Normes, étapes et livrables',
    'groupes': 'Sous-commissions, GT et responsables', 'activite': 'Activité effective et méthode',
    'participants': 'Participants et présences vérifiées', 'evaluations': 'Exercices et évaluations',
    'incidents': 'Incidents, diagnostic et résolution', 'sauvegardes': 'Sauvegardes et restaurations vérifiées',
    'equipements': 'Équipements, quantités et état', 'communications': 'Messages, envois et accusés',
    'institutions': 'Institutions consultées et réponses', 'partenariats': 'Partenaires et contributions',
    'arm': 'Dossiers ARM et périmètre confirmé', 'ressources': 'Ressources, besoins et justificatifs',
    'budget': 'Crédits, engagements, liquidations, ordonnancements et paiements',
    'options': 'Options et effets comparés', 'decisions': 'Décisions, responsables et preuves',
    'formation': 'Formations, acquis et besoins de suivi', 'transfert': 'État de transfert et réserves',
    'articles': 'Articles et clauses examinés', 'methodes': 'Méthodes, hypothèses et résultats',
    'cartes': 'Cartes, sources et anomalies', 'risques': 'Risques et mesures proposées',
}

# code: (famille, intitulé, champs propres). Tous conservent les cinq sections communes.
TYPES = {
    'N1': ('norme', 'Réception et recevabilité', ('origine', 'pieces_recues', 'anomalies')),
    'N2': ('norme', 'Conformité documentaire et versions', ('versions', 'observations', 'anomalies')),
    'N3': ('norme', 'Examens spécialisés CTC', ('examens', 'observations', 'consultation')),
    'N4': ('norme', 'Transmission au COPIL', ('versions', 'examens', 'consultation', 'transmission')),
    'M1': ('collectif', 'Avancement de plusieurs normes', ('normes', 'groupes')),
    'M2': ('collectif', 'Production des sous-commissions', ('groupes', 'normes')),
    'M3': ('experts', 'Activité des experts', ('activite', 'groupes')),
    'F1': ('finance', 'Besoins financiers d’une norme', ('ressources', 'budget')),
    'F2': ('finance', 'Financement de plusieurs normes', ('normes', 'ressources', 'budget')),
    'F3': ('finance', 'Exécution budgétaire', ('budget', 'ressources')),
    'F4': ('finance', 'Demande de ressources au Ministère', ('normes', 'budget', 'risques')),
    'C1': ('gouvernance', 'Arbitrage sur une norme', ('articles', 'observations', 'options')),
    'C2': ('gouvernance', 'Production normative générale', ('normes', 'groupes', 'ressources')),
    'C3': ('gouvernance', 'Suivi des décisions du COPIL', ('decisions', 'transmission')),
    'ITP-01': ('ministere', 'Étape institutionnelle', ('groupes', 'normes', 'risques')),
    'ITP-02': ('ministere', 'Production et résultats', ('normes', 'groupes', 'decisions')),
    'ITP-03': ('ministere', 'Besoins et financement', ('budget', 'ressources', 'risques')),
    'ITP-04': ('ministere', 'Mise en service et transfert', ('formation', 'incidents', 'sauvegardes', 'transfert')),
    'P1': ('norme', 'Contrôle documentaire et anomalies', ('pieces_recues', 'anomalies')),
    'P2': ('norme', 'Gestion des versions', ('versions', 'observations')),
    'P3': ('norme', 'Inventaire documentaire', ('pieces_recues', 'versions')),
    'P4': ('experts', 'Formation et compétences', ('participants', 'formation', 'evaluations')),
    'P5': ('experts', 'Assistance et incidents', ('incidents', 'formation')),
    'P6': ('experts', 'Exploitation technique', ('sauvegardes', 'incidents', 'equipements')),
    'P7': ('finance', 'Logistique et moyens', ('equipements', 'ressources', 'budget')),
    'P8': ('collectif', 'Communication et séances', ('communications', 'participants', 'decisions')),
    'P9': ('gouvernance', 'Relations extérieures et ARM', ('institutions', 'partenariats', 'arm')),
    'S-ISO': ('norme', 'Veille et conformité internationale', ('articles', 'observations')),
    'S-JUR': ('norme', 'Contrôle de légistique', ('articles', 'observations')),
    'S-ENV': ('norme', 'Examen environnemental', ('risques', 'observations')),
    'S-ECO': ('norme', 'Examen économique', ('methodes', 'ressources')),
    'S-PLAN': ('norme', 'Méthodologie et chronogramme', ('methodes', 'prochaines_actions')),
    'S-SCI': ('norme', 'Vérification scientifique', ('methodes', 'articles')),
    'S-ENQ': ('norme', 'Enquête publique', ('consultation', 'observations')),
    'S-FEC': ('norme', 'Consultation industrielle', ('consultation', 'institutions')),
    'S-SIG': ('norme', 'Contrôle géospatial', ('cartes', 'anomalies')),
    'S-GAF': ('finance', 'Exécution budgétaire du GAF', ('budget', 'ressources')),
}


def fields_for(code):
    return tuple(dict.fromkeys((*COMMON, *TYPES[code][2])))

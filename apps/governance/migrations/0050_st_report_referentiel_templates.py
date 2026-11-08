from django.db import migrations


def seed_referentiel(apps, schema_editor):
    Template = apps.get_model('governance', 'STReportTemplate')
    definitions = [
        # 3. Coordination centrale
        ('r-c01', 'R-C01 · Bilan CTC', ['Références et états CTC', 'Examens clos', 'Décisions ouvertes', 'Mandats et échéances', 'Besoins chiffrés']),
        ('r-c02', 'R-C02 · Transmission COPIL', ['Choix demandé', 'Options soutenues par les pièces', 'Pièces justificatives', 'Mandats et procès-verbaux']),
        ('r-c03', 'R-C03 · Besoins de la coordination', ['Besoins chiffrés', 'Références et sources', 'Échéances et conséquences']),
        ('r-c04', 'R-C04 · Retards et arbitrages opérationnels', ['Dossier et date d’entrée', 'Échéance', 'Dernier événement', 'Motif du retard', 'Action attendue', 'Responsable']),
        ('r-c05', 'R-C05 · Réception et transmissions', ['Bordereaux et dates', 'Pièces reçues et émetteur', 'Journal et destinataire']),
        ('r-c06', 'R-C06 · Liaison interservices', ['Courriers', 'Dossier et référence', 'Échéance', 'Pièces de réponse', 'Accusés vérifiés']),
        # 4. Pôle 1 – analyse documentaire
        ('r-d01', 'R-D01 · Conformité globale', ['Normes contrôlées', 'Anomalies par gravité', 'Corrections ouvertes', 'Versions validées']),
        ('r-d02', 'R-D02 · Recevabilité et écarts', ['Référence, titre et origine', 'Présence des pièces', 'Gabarit, unités et articles', 'Annexes']),
        ('r-d03', 'R-D03 · Historique des versions', ['Identifiant, auteur et date', 'Modifications', 'Version précédente', 'Décision, état et justificatif']),
        ('r-d04', 'R-D04 · Inventaire et classement', ['Chemin Drive, nom et type', 'Version et accès', 'Statut et dates', 'Copies antérieures']),
        # 5. Pôle 2 – appui technique et formation
        ('r-t01', 'R-T01 · Exploitation et formation', ['Disponibilité et incidents', 'Formation et capacité', 'Sauvegardes', 'Besoins matériels']),
        ('r-t02', 'R-T02 · Formation évaluée', ['Programme et séances', 'Liste de présence', 'Exercices et notes', 'Profils et besoins d’appui']),
        ('r-t03', 'R-T03 · Incidents utilisateurs', ['Ticket, usager et pôle autorisé', 'Module et erreur', 'Diagnostic et action', 'Résultat et escalade']),
        ('r-t04', 'R-T04 · Sauvegarde et restauration', ['Instance et horaire', 'Sauvegarde, résultat et intégrité', 'Restauration de test', 'Logs']),
        # 6. Pôle 3 – logistique et communication
        ('r-l01', 'R-L01 · Besoins logistiques', ['Activité et date', 'Participants', 'Matériels, coûts et disponibilités', 'Justificatifs']),
        ('r-l02', 'R-L02 · Inventaire et service fait', ['Article et quantités demandée, existante, livrée', 'Devis et facture', 'Réception']),
        ('r-l03', 'R-L03 · Communications', ['Campagne et destinataires', 'Canal et message', 'Envoi et erreurs', 'Confirmations vérifiées']),
        ('r-l04', 'R-L04 · Séances et présence', ['Convocation', 'Présence vérifiée', 'Décisions', 'Responsable d’action et échéance']),
        # 7. Pôle 4 – relations extérieures
        ('r-e01', 'R-E01 · Consultations externes', ['Organismes et objet', 'Contributions et état', 'Réserves', 'Décisions attendues']),
        ('r-e02', 'R-E02 · Correspondances', ['Référence courrier et institution', 'Date et objet', 'Pièces', 'Échéance et réponse']),
        ('r-e03', 'R-E03 · Contributions partenaires', ['Partenaire et domaine', 'Contribution et preuves', 'Convention', 'Valorisation et statut']),
        ('r-e04', 'R-E04 · Suivi administratif ARM', ['Dossier et origine', 'Dates et pièces', 'Observations', 'Statut — périmètre à confirmer']),
        # 8. Pôle 5 – coordination des sous-commissions
        ('r-s01', 'R-S01 · Bilan des 7 SC', ['Mandats et SC', 'Tomes, GT et normes', 'Jalons et retards', 'Actions demandées']),
        ('r-s02', 'R-S02 · Fiche par SC', ['Membres et postes confirmés', 'Réunions', 'Normes confiées', 'Décisions', 'Vacances de postes']),
        ('r-s03', 'R-S03 · Production par GT', ['GT et animateur', 'Livrable et versions', 'Échéance', 'Tâches et observations']),
        ('r-s04', 'R-S04 · Portefeuille multi-normes', ['Dossiers par état et étape', 'SC, auteur et échéance', 'Preuves', 'Évolution']),
        # 9. Rapports spécialisés : sous-rôles CTC
        ('r-x01', 'R-X01 · Harmonie internationale', ['Référentiel et édition', 'Clauses comparées', 'Divergences', 'Avis, date et source']),
        ('r-x02', 'R-X02 · Légistique', ['Articles et base juridique', 'Observation et version', 'Décision', 'Réserve']),
        ('r-x03', 'R-X03 · Environnement', ['Impact et mesures', 'Document source', 'Risques', 'Avis et réserves']),
        ('r-x04', 'R-X04 · Économie', ['Hypothèses', 'Coûts et effets attendus', 'Méthode', 'Réserves']),
        ('r-x05', 'R-X05 · Chronogramme', ['Jalons et dépendances', 'Responsable', 'Échéance', 'Avis et statut']),
        ('r-x06', 'R-X06 · Contrôle scientifique', ['Hypothèses et protocole', 'Essais et calcul', 'Avis indépendant']),
        ('r-x07', 'R-X07 · Consultation industrielle', ['Parties consultées', 'Commentaires et réponses', 'Conclusion et date']),
        ('r-x08', 'R-X08 · Enquête publique', ['Période et contributions', 'Thèmes et réponses', 'Preuves', 'Décisions']),
        ('r-x09', 'R-X09 · Géospatial', ['Cartes et source', 'Échelle et coordonnées', 'Contrôles et écarts']),
        ('r-x10', 'R-X10 · Exécution budgétaire', ['Crédits confirmés', 'Engagement', 'Liquidation', 'Ordonnancement', 'Paiement et pièces']),
        # 17. COPIL
        ('c1-copil', 'C1 · Note d’arbitrage', ['Article et version', 'Problème constaté', 'Solutions A/B et avis', 'Implications', 'Choix demandé']),
        ('c2-copil', 'C2 · Bilan de production', ['Normes par étape', 'Nouvelles avancées', 'Retards et anomalies', 'Coûts', 'Décisions', 'Date d’arrêté de la base']),
        ('c3-copil', 'C3 · Suivi des décisions COPIL', ['Référence PV ou instruction', 'Action et responsable', 'Échéance', 'Pièce', 'État']),
        # 18. Ministère ITP
        ('itp-01', 'ITP-01 · Réorganisation et avancement', ['Actes et postes confirmés', 'Rapprochement anciennes CTM / nouvelles SC', 'Déploiement testé']),
        ('itp-02', 'ITP-02 · Résultats normatifs', ['Portefeuille', 'Jalons franchis', 'Décisions du COPIL', 'Publication effective prouvée']),
        ('itp-03', 'ITP-03 · Besoins et financement', ['Montants par livrable', 'Devis et crédits écrits', 'Écarts et conséquences', 'Arbitrage demandé']),
        ('itp-04', 'ITP-04 · Formation et transfert', ['Participants et résultats', 'Comptes et tests de sécurité', 'Sauvegarde et restauration', 'Incidents et réserves']),
        # 14 à 16. Finances
        ('f1-besoin', 'F1 · Ligne de besoin financier', ['Référence et étape', 'Activité et livrable', 'Quantité et unité', 'Coût unitaire', 'Montant demandé', 'Financement confirmé', 'Montant restant à couvrir', 'Échéance', 'Justificatifs', 'Validation']),
        ('f2-execution', 'F2 · Exécution financière', ['Crédit disponible', 'Engagement', 'Liquidation', 'Ordonnancement', 'Paiement', 'Pièces justificatives']),
        ('f3-consolide', 'F3 · Demandes financières consolidées', ['Norme ou coût mutualisé', 'Données requises', 'Consolidation pôles et GAF', 'Décision possible']),
    ]
    for code, name, sections in definitions:
        Template.objects.get_or_create(system_code=code, defaults={'name': name, 'sections': [{'title': title, 'content': ''} for title in sections]})


class Migration(migrations.Migration):
    dependencies = [('governance', '0049_stnotificationread')]
    operations = [migrations.RunPython(seed_referentiel, migrations.RunPython.noop)]

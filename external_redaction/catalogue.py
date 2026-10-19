"""Catalogue prospectif de 20 projets NCD (statut BROUILLON).

Source institutionnelle : rapport adopté de la CNE-ITP du 15 octobre 2026
(catalogue prospectif, pages 29 à 31). Les codes NCD sont des références
provisoires de projet, pas des numéros d'homologation.

Chaque entrée est une base de travail destinée aux experts : le corps suit la
structure documentaire obligatoire (avant-propos, domaine d'application,
références, termes, principes, exigences, contrôles, conditions RDC, points
d'examen, bibliographie) et marque explicitement les données à compléter.

Aucune valeur technique, formule, seuil ou obligation réglementaire n'est
inventée : les passages non documentés portent le marqueur
« [À COMPLÉTER PAR LES EXPERTS] ».
"""

# Numéros des sous-commissions unifiées (CTM) :
# 1 = SC-BAT, 2 = SC-ENV, 3 = SC-GF, 4 = SC-IT, 5 = SC-OH, 6 = SC-SOCLE, 7 = SC-VRD

SOURCE = "Rapport adopté de la CNE-ITP du 15 octobre 2026"

_NOTE = "[À COMPLÉTER PAR LES EXPERTS]"

CATALOGUE = [
    # ── SC-SOCLE ─────────────────────────────────────────────────────────────
    {
        "code": "NCD 001",
        "title": "Vocabulaire technique unifié et symboles graphiques pour le BTP en RDC",
        "sc_number": 6,
        "wg_name": "Normalisation Appliquée",
        "category": "Matériaux & Essais / Socle commun",
        "iso_reference": "ISO 80000 (série)",
        "description": (
            "Unifier la terminologie, les grandeurs, les unités et les symboles "
            "graphiques utilisés dans les documents techniques du bâtiment et des "
            "travaux publics en RDC, afin de rendre les études, les cahiers des "
            "charges et les rapports d'essai interopérables."
        ),
        "tags": "vocabulaire, symboles graphiques, unités SI, terminologie BTP, normalisation",
        "content": (
            "AVANT-PROPOS\n"
            "La présente norme est élaborée par la sous-commission Matériaux & Essais / Socle commun de "
            "la CNE-ITP. Elle vise à doter les acteurs du bâtiment et des travaux publics d'un vocabulaire "
            "technique et de symboles graphiques unifiés afin de lever les ambiguïtés contractuelles et "
            "techniques entre les maîtres d'ouvrage, les bureaux d'études, les entreprises et les "
            "laboratoires. Elle s'appuie sur la série ISO 80000.\n\n"
            "INTRODUCTION\n"
            "La cohérence des termes, des grandeurs et des symboles est une condition de la qualité et de "
            "l'interopérabilité des documents techniques. Le présent document définit les règles communes "
            "de terminologie, de grandeurs, d'unités et de symboles graphiques applicables aux études, "
            "aux cahiers des charges et aux rapports d'essai.\n\n"
            "1. Domaine d'application\n"
            "La présente norme s'applique aux documents techniques produits et échangés dans le cadre des "
            "projets d'infrastructures et de bâtiment en RDC : études, spécifications, rapports d'essai, "
            "plans et pièces écrites. Elle ne définit pas elle-même les exigences de performance des "
            "ouvrages.\n\n"
            "2. Références normatives\n"
            "ISO 80000 (série) — Grandeurs et unités.\n\n"
            "3. Termes et définitions\n"
            "Grandeur, unité, symbole, définition, terme, vocabulaire, système d'unités.\n\n"
            "4. Grandeurs et unités\n"
            "Adopter les grandeurs et les unités du Système international ; exprimer chaque grandeur avec "
            "son unité et son symbole normalisé ; harmoniser la graphie des symboles dans l'ensemble des "
            "documents.\n\n"
            "5. Symboles graphiques\n"
            "Fixer les règles de représentation des symboles graphiques utilisés sur les plans "
            "(matériaux, équipements, réseaux, ouvrages) conformément aux référentiels de dessin "
            "technique en vigueur.\n\n"
            "6. Règles de rédaction des définitions\n"
            "Rédiger des définitions claires, non contradictoires et fondées sur les références "
            "internationales ; distinguer les définitions normalisées des usages propres au contexte "
            "congolais.\n\n"
            "7. Vérification de la cohérence\n"
            "Contrôle documentaire de cohérence : revue croisée des termes et des symboles, vérification "
            "de la conformité aux références retenues.\n\n"
            "8. Conditions d'application en RDC\n"
            "Prise en compte des usages linguistiques (français et langues nationales), des pratiques de "
            "rédaction existantes et des documents déjà produits par les administrations et les bureaux "
            "d'études.\n\n"
            "9. Documentation et traçabilité\n"
            "Glossaire normalisé, tableaux de symboles, registre des équivalences terminologiques.\n\n"
            "10. Annexes\n"
            "Glossaire normalisé, tableaux de symboles graphiques.\n\n"
            "11. Bibliographie\n"
            "ISO 80000 (série) — Grandeurs et unités."
        ),
    },
    {
        "code": "NCD 002",
        "title": "Spécifications techniques des ciments courants fabriqués ou importés en RDC",
        "sc_number": 6,
        "wg_name": "Matériaux de Construction Locaux",
        "category": "Matériaux & Essais / Socle commun",
        "iso_reference": "EN 197-1",
        "description": (
            "Définir les spécifications des ciments courants mis sur le marché en RDC "
            "(fabriqués localement ou importés), leurs classes de résistance et les "
            "critères de conformité, en vue d'une adoption/adaptation du référentiel EN 197."
        ),
        "tags": "ciment, liants hydrauliques, EN 197, conformité, matériaux",
        "content": (
            "AVANT-PROPOS\n"
            "La présente norme est élaborée par la sous-commission Matériaux & Essais / Socle commun de "
            "la CNE-ITP. Le ciment est un intrant stratégique du bâtiment et des travaux publics ; les "
            "ciments disponibles en RDC proviennent de fabrications locales et d'importations aux "
            "désignations variées. Le présent document établit un référentiel national de spécifications "
            "sur la base de l'EN 197-1, sans reproduire le texte protégé par le droit d'auteur.\n\n"
            "INTRODUCTION\n"
            "Le présent document a pour objet l'identification et la vérification des ciments courants : "
            "composition normalisée, désignation, classes de résistance et critères mécaniques, physiques "
            "et chimiques.\n\n"
            "1. Domaine d'application\n"
            "La présente norme s'applique aux ciments courants fabriqués ou importés en RDC. Elle couvre "
            "leur composition, leur désignation, leurs exigences de performance et leurs critères de "
            "conformité.\n\n"
            "2. Références normatives\n"
            "EN 197-1 — Ciment — Composition, spécifications et critères de conformité des ciments "
            "courants.\n\n"
            "3. Termes et définitions\n"
            "Ciment courant, constituant principal, addition, classe de résistance, prise, stabilité, "
            "conformité.\n\n"
            "4. Composition et désignation\n"
            "Les ciments sont classés selon leur composition et désignés de façon normalisée et lisible. "
            "Les types et leurs désignations sont repris de l'EN 197-1.\n\n"
            "5. Exigences physiques, mécaniques et chimiques\n"
            "Les exigences de finesse, de temps de prise, de stabilité et de résistance à la compression, "
            "ainsi que les classes de résistance, sont reprises de l'EN 197-1.\n\n"
            "6. Méthodes d'essai\n"
            "Les essais de résistance à la compression, de temps de prise et de stabilité sont réalisés "
            "selon les méthodes d'essai normalisées associées à l'EN 197-1.\n\n"
            "7. Critères de conformité\n"
            "Conformité des lots, échantillonnage, marquage et documents d'accompagnement conformément "
            "aux règles de l'EN 197-1.\n\n"
            "8. Conditions d'application en RDC\n"
            "Climat tropical humide (stockage et conservation), disponibilité des laboratoires d'essai, "
            "traçabilité des importations et contrôle aux points d'entrée.\n\n"
            "9. Documentation et traçabilité\n"
            "Certificats de conformité, rapports d'essai, traçabilité des lots et des importations.\n\n"
            "10. Annexes\n"
            "Tableaux de composition et de classes de résistance.\n\n"
            "11. Bibliographie\n"
            "EN 197-1 (série EN 197)."
        ),
    },
    {
        "code": "NCD 005",
        "title": "Guide d'assurance qualité et d'accréditation des laboratoires d'essais géotechniques et de matériaux",
        "sc_number": 6,
        "wg_name": "Essais et Métrologie",
        "category": "Matériaux & Essais / Socle commun",
        "iso_reference": "ISO/IEC 17025:2017",
        "description": (
            "Fournir un guide pour l'assurance qualité et l'accréditation des "
            "laboratoires d'essais géotechniques et de matériaux en RDC, sur la base "
            "de l'ISO/IEC 17025, afin de fiabiliser les résultats d'essai."
        ),
        "tags": "assurance qualité, accréditation, laboratoires, ISO/IEC 17025, essais",
        "content": (
            "AVANT-PROPOS\n"
            "Le présent guide est élaboré par la sous-commission Matériaux & Essais / Socle commun de la "
            "CNE-ITP. La fiabilité des résultats d'essai conditionne la sécurité des ouvrages. Ce guide "
            "accompagne les laboratoires congolais vers des pratiques conformes à l'ISO/IEC 17025:2017 "
            "(Exigences générales concernant la compétence des laboratoires d'étalonnages et d'essais).\n\n"
            "INTRODUCTION\n"
            "Le présent document vise à harmoniser l'assurance qualité des laboratoires d'essais "
            "géotechniques et de matériaux et à faciliter leur démarche d'accréditation.\n\n"
            "1. Domaine d'application\n"
            "Le guide s'applique aux laboratoires d'essais géotechniques et de matériaux de construction "
            "opérant en RDC. Il est informatif : il oriente sans se substituer aux exigences "
            "d'accréditation elles-mêmes.\n\n"
            "2. Références normatives\n"
            "ISO/IEC 17025:2017 — Exigences générales concernant la compétence des laboratoires "
            "d'étalonnages et d'essais.\n\n"
            "3. Termes et définitions\n"
            "Essai, étalonnage, accréditation, traçabilité métrologique, incertitude de mesure, essai "
            "d'aptitude, validation de méthode.\n\n"
            "4. Exigences de structure et de ressources\n"
            "Structurer le système de management ; garantir la compétence du personnel ; maîtriser les "
            "locaux et les équipements ; assurer la traçabilité métrologique.\n\n"
            "5. Exigences de processus\n"
            "Valider les méthodes d'essai ; maîtriser les échantillons ; assurer la validité des "
            "résultats ; établir des rapports d'essai complets et traçables.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "Participation à des essais d'aptitude et à des comparaisons inter-laboratoires ; audits "
            "internes ; revues de direction.\n\n"
            "7. Critères de conformité\n"
            "Respect des exigences de l'ISO/IEC 17025 et validité démontrée des résultats d'essai.\n\n"
            "8. Conditions d'application en RDC\n"
            "Capacités locales de métrologie, disponibilité des matériaux de référence, alimentation et "
            "maintenance des équipements, financement de l'accréditation.\n\n"
            "9. Documentation et traçabilité\n"
            "Manuel qualité, procédures techniques, enregistrements et archives.\n\n"
            "10. Annexes\n"
            "Modèles de fiches, listes de contrôle.\n\n"
            "11. Bibliographie\n"
            "ISO/IEC 17025:2017."
        ),
    },

    # ── SC-IT ────────────────────────────────────────────────────────────────
    {
        "code": "NCD 101",
        "title": "Catalogue national de dimensionnement des structures de chaussées souples et semi-rigides",
        "sc_number": 4,
        "wg_name": "Ingénierie Routière",
        "category": "Infrastructures de transport",
        "iso_reference": "AASHTO (Guide for Design of Pavement Structures)",
        "description": (
            "Élaborer un catalogue national de structures de chaussées souples et "
            "semi-rigides adapté au trafic, aux sols et aux matériaux disponibles en "
            "RDC, en s'appuyant sur les méthodes AASHTO et les guides techniques pertinents."
        ),
        "tags": "chaussées, dimensionnement, AASHTO, routier, structures",
        "content": (
            "AVANT-PROPOS\n"
            "Le dimensionnement des chaussées est aujourd'hui réalisé de façon hétérogène. Ce projet vise "
            "un catalogue national de structures types, fondé sur les méthodes reconnues (AASHTO) et "
            "adapté aux réalités congolaises.\n\n"
            "INTRODUCTION\n"
            "Le problème traité est la définition de structures de chaussées fiables et économiques en "
            "fonction du trafic, de la portance des sols et des matériaux disponibles.\n\n"
            "1. Domaine d'application\n"
            "Chaussées souples et semi-rigides des routes neuves et réhabilitées en RDC. Sont exclus les "
            "revêtements aéronautiques et les chaussées rigides en béton (le cas échéant traités à part).\n\n"
            "2. Références normatives\n"
            "- AASHTO, Guide for Design of Pavement Structures (édition à vérifier) et méthode de "
            "dimensionnement AASHTO 1993.\n"
            "- [À COMPLÉTER PAR LES EXPERTS] : guides techniques d'application et catalogue des "
            "structures existant.\n\n"
            "3. Termes et définitions\n"
            "Trafic cumulé équivalent, essieu de référence, portance (CBR), couche de forme, assise, "
            "couche de roulement — définitions de travail.\n\n"
            "4. Principes généraux\n"
            "Classer le trafic en niveaux ; déterminer la portance d'assise ; proposer des structures "
            "types ; définir les hypothèses de dimensionnement et leurs limites.\n\n"
            "5. Exigences techniques\n"
            "[À COMPLÉTER PAR LES EXPERTS] : niveaux de trafic, coefficients et abaques. Les valeurs de "
            "dimensionnement doivent être reprises de sources autorisées ou calibrées localement, jamais "
            "inventées.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "[À COMPLÉTER PAR LES EXPERTS] : essais de portance (CBR, déflexion), contrôle de compactage, "
            "critères de réception.\n\n"
            "7. Conditions particulières d'application en RDC\n"
            "Sols latéritiques, saisonnalité des pluies, disponibilité des granulats, trafic réel et "
            "surcharges.\n\n"
            "8. Points soumis à l'examen des experts\n"
            "- Édition de la méthode AASHTO à retenir ;\n"
            "- niveaux de trafic et classes de portance propres à la RDC ;\n"
            "- matériaux de substitution disponibles.\n\n"
            "9. Annexes\n"
            "[À COMPLÉTER PAR LES EXPERTS] : catalogue de structures types.\n\n"
            "10. Bibliographie\n"
            "- AASHTO, Guide for Design of Pavement Structures.\n"
            "- [À COMPLÉTER PAR LES EXPERTS]."
        ),
    },
    {
        "code": "NCD 102",
        "title": "Règles de calcul, d'inspection et de maintenance des ponts routiers métalliques et en béton",
        "sc_number": 4,
        "wg_name": "Ponts et ouvrages d'art",
        "category": "Infrastructures de transport",
        "iso_reference": "Eurocodes EN 1990 à EN 1999",
        "description": (
            "Définir des règles de calcul, d'inspection et de maintenance des ponts "
            "routiers métalliques et en béton, en s'appuyant sur les Eurocodes "
            "structuraux et les parties applicables aux ponts."
        ),
        "tags": "ponts, ouvrages d'art, Eurocodes, inspection, maintenance",
        "content": (
            "AVANT-PROPOS\n"
            "Les ponts routiers constituent des ouvrages à enjeux de sécurité majeurs. Ce projet vise à "
            "disposer de règles nationales de calcul, d'inspection et de maintenance fondées sur les "
            "Eurocodes, sans reproduire leur texte protégé.\n\n"
            "INTRODUCTION\n"
            "Le problème traité est l'absence de référentiel national unifié pour la conception et "
            "l'entretien des ponts, ainsi que le vieillissement du patrimoine d'ouvrages.\n\n"
            "1. Domaine d'application\n"
            "Ponts routiers métalliques et en béton, en construction neuve comme en inspection et "
            "maintenance. Exclusions et limites à préciser par le GT.\n\n"
            "2. Références normatives\n"
            "- EN 1990 à EN 1999 (Eurocodes structuraux), notamment les parties applicables aux ponts "
            "(actions, béton, acier, géotechnique).\n"
            "- [À COMPLÉTER PAR LES EXPERTS] : annexes nationales et guides d'inspection.\n\n"
            "3. Termes et définitions\n"
            "État limite, action, combinaison d'actions, inspection, auscultation, maintenance — "
            "définitions de travail.\n\n"
            "4. Principes généraux\n"
            "Adopter la philosophie des états limites ; définir les actions et combinaisons ; fixer un "
            "cadre d'inspection périodique et de maintenance préventive.\n\n"
            "5. Exigences techniques\n"
            "[À COMPLÉTER PAR LES EXPERTS] : paramètres de calcul, coefficients partiels, classes "
            "d'inspection. Aucun coefficient ou seuil ne doit être inventé.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "[À COMPLÉTER PAR LES EXPERTS] : méthodes d'inspection visuelle et instrumentée, essais sur "
            "matériaux, critères de classement des désordres.\n\n"
            "7. Conditions particulières d'application en RDC\n"
            "Surcharges réelles, environnement agressif, disponibilité des équipements d'inspection, "
            "compétences locales.\n\n"
            "8. Points soumis à l'examen des experts\n"
            "- Choix des annexes nationales des Eurocodes ;\n"
            "- classement du patrimoine d'ouvrages ;\n"
            "- fréquence et modalités d'inspection.\n\n"
            "9. Annexes\n"
            "[À COMPLÉTER PAR LES EXPERTS] : fiches d'inspection, catalogue des désordres.\n\n"
            "10. Bibliographie\n"
            "- EN 1990 à EN 1999 (Eurocodes).\n"
            "- [À COMPLÉTER PAR LES EXPERTS]."
        ),
    },
    {
        "code": "NCD 103",
        "title": "Normes de conception géométrique des routes en zones de fortes pentes et reliefs difficiles",
        "sc_number": 4,
        "wg_name": "Ingénierie Routière",
        "category": "Infrastructures de transport",
        "iso_reference": "Guides de conception géométrique routière",
        "description": (
            "Fixer des règles de conception géométrique des routes en zones de fortes "
            "pentes et reliefs difficiles, adaptées au contexte congolais et aux "
            "guides de conception géométrique routière reconnus."
        ),
        "tags": "conception géométrique, routes, fortes pentes, relief, tracé",
        "content": (
            "AVANT-PROPOS\n"
            "Les zones de relief exigent des règles de tracé spécifiques (rayons, déclivités, visibilité). "
            "Ce projet adapte les guides de conception géométrique routière aux contraintes congolaises.\n\n"
            "INTRODUCTION\n"
            "Le problème traité est la sécurité et la constructibilité des routes en terrain difficile, où "
            "les paramètres géométriques usuels sont mal adaptés.\n\n"
            "1. Domaine d'application\n"
            "Conception géométrique des routes neuves et réhabilitées en zones de fortes pentes et reliefs "
            "difficiles en RDC. Limites à préciser.\n\n"
            "2. Références normatives\n"
            "- Guides de conception géométrique routière (à identifier précisément par le GT).\n"
            "- [À COMPLÉTER PAR LES EXPERTS] : recommandations sur la visibilité et le tracé en plan et "
            "profil en long.\n\n"
            "3. Termes et définitions\n"
            "Rayon en plan, déclivité, rampe, visibilité d'arrêt, profil en long, terrassement — "
            "définitions de travail.\n\n"
            "4. Principes généraux\n"
            "Adapter les paramètres géométriques aux vitesses de référence ; maîtriser les déclivités et "
            "les distances de visibilité ; intégrer les ouvrages de soutènement et de drainage.\n\n"
            "5. Exigences techniques\n"
            "[À COMPLÉTER PAR LES EXPERTS] : valeurs limites de déclivité, rayons minimaux, largeurs, "
            "pentes transversales. Aucune valeur ne doit être inventée.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "[À COMPLÉTER PAR LES EXPERTS] : vérification de la conformité du tracé, contrôle des pentes "
            "et de la visibilité.\n\n"
            "7. Conditions particulières d'application en RDC\n"
            "Reliefs accidentés de l'Est, pluviométrie, géologie et stabilité des versants, matériaux de "
            "terrassement.\n\n"
            "8. Points soumis à l'examen des experts\n"
            "- Références géométriques à retenir ;\n"
            "- catégories de routes concernées ;\n"
            "- articulation avec la prévention de l'érosion.\n\n"
            "9. Annexes\n"
            "[À COMPLÉTER PAR LES EXPERTS] : tableaux de paramètres géométriques.\n\n"
            "10. Bibliographie\n"
            "- Guides de conception géométrique routière.\n"
            "- [À COMPLÉTER PAR LES EXPERTS]."
        ),
    },

    # ── SC-GF ────────────────────────────────────────────────────────────────
    {
        "code": "NCD 201",
        "title": "Prescriptions pour l'exécution des campagnes de reconnaissance géotechnique des sols in situ",
        "sc_number": 3,
        "wg_name": "Reconnaissance des sols et investigations in situ",
        "category": "Géotechnique & Fondations",
        "iso_reference": "ISO 22475-1",
        "description": (
            "Définir les prescriptions d'exécution des campagnes de reconnaissance "
            "géotechnique in situ (sondages, prélèvements, essais), sur la base de "
            "l'ISO 22475 et des références pertinentes."
        ),
        "tags": "reconnaissance géotechnique, in situ, sondages, ISO 22475, prélèvements",
        "content": (
            "AVANT-PROPOS\n"
            "La qualité des études géotechniques dépend de la fiabilité de la reconnaissance. Ce projet "
            "fixe les prescriptions d'exécution des campagnes in situ, en s'appuyant sur l'ISO 22475.\n\n"
            "INTRODUCTION\n"
            "Le problème traité est l'hétérogénéité des pratiques de sondage et de prélèvement, source "
            "d'erreurs de dimensionnement.\n\n"
            "1. Domaine d'application\n"
            "Campagnes de reconnaissance géotechnique des sols in situ en RDC : sondages, prélèvements, "
            "essais en place. Limites à préciser.\n\n"
            "2. Références normatives\n"
            "- ISO 22475-1, Reconnaissance et essais géotechniques — Méthodes de prélèvement et mesurages "
            "piézométriques (édition à vérifier).\n"
            "- [À COMPLÉTER PAR LES EXPERTS] : essais in situ (pénétromètre, pressiomètre, etc.).\n\n"
            "3. Termes et définitions\n"
            "Sondage, carottage, prélèvement remanié/intact, essai in situ, piézométrie — définitions "
            "de travail.\n\n"
            "4. Principes généraux\n"
            "Programmer la campagne en fonction de l'ouvrage ; qualifier les échantillons ; assurer la "
            "traçabilité des prélèvements et des essais.\n\n"
            "5. Exigences techniques\n"
            "[À COMPLÉTER PAR LES EXPERTS] : profondeurs, espacement, nombre de points, méthodes "
            "d'essai. Aucun paramètre chiffré ne doit être inventé.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "[À COMPLÉTER PAR LES EXPERTS] : procès-verbaux de sondage, conservation des échantillons, "
            "validation des résultats.\n\n"
            "7. Conditions particulières d'application en RDC\n"
            "Sols latéritiques, accès difficiles, disponibilité des appareils de sondage, conditions "
            "climatiques.\n\n"
            "8. Points soumis à l'examen des experts\n"
            "- Édition de l'ISO 22475 à retenir ;\n"
            "- densité minimale de reconnaissance selon les ouvrages ;\n"
            "- essais in situ prioritaires.\n\n"
            "9. Annexes\n"
            "[À COMPLÉTER PAR LES EXPERTS] : modèles de fiches de sondage.\n\n"
            "10. Bibliographie\n"
            "- ISO 22475 (série).\n"
            "- [À COMPLÉTER PAR LES EXPERTS]."
        ),
    },
    {
        "code": "NCD 202",
        "title": "Manuel technique de prévention et de lutte contre l'érosion ravinante en milieu urbain",
        "sc_number": 3,
        "wg_name": "Stabilité & Érosions",
        "category": "Géotechnique & Fondations",
        "iso_reference": "Guides de traitement des risques géotechniques",
        "description": (
            "Fournir un manuel technique de prévention et de lutte contre l'érosion "
            "ravinante en milieu urbain, combinant mesures de stabilisation et de "
            "gestion des eaux, adapté aux villes congolaises."
        ),
        "tags": "érosion ravinante, milieu urbain, stabilisation, gestion des eaux, ravins",
        "content": (
            "AVANT-PROPOS\n"
            "L'érosion ravinante affecte gravement plusieurs villes congolaises. Ce manuel vise à "
            "structurer la prévention et le traitement des ravins, en mobilisant les documents "
            "scientifiques et guides disponibles.\n\n"
            "INTRODUCTION\n"
            "Le problème traité est la formation et la progression des ravins en milieu urbain, liées au "
            "ruissellement non maîtrisé et aux pratiques d'occupation des sols.\n\n"
            "1. Domaine d'application\n"
            "Prévention et traitement de l'érosion ravinante en milieu urbain et périurbain en RDC. "
            "Limites à préciser.\n\n"
            "2. Références normatives\n"
            "- Documents scientifiques et guides de traitement des risques géotechniques (à sélectionner).\n"
            "- [À COMPLÉTER PAR LES EXPERTS] : guides de gestion des eaux pluviales et de stabilisation.\n\n"
            "3. Termes et définitions\n"
            "Érosion ravinante, ravin, bassin versant urbain, ruissellement, ouvrage de stabilisation — "
            "définitions de travail.\n\n"
            "4. Principes généraux\n"
            "Agir d'abord sur les causes (gestion des eaux amont), puis stabiliser les versants et "
            "protéger les fonds de ravin ; intégrer les mesures d'urbanisme.\n\n"
            "5. Exigences techniques\n"
            "[À COMPLÉTER PAR LES EXPERTS] : techniques de stabilisation (végétale, mécanique, génie "
            "civil), dimensionnement des exutoires. Aucune valeur ne doit être inventée.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "[À COMPLÉTER PAR LES EXPERTS] : suivi topographique, inspections, indicateurs d'efficacité.\n\n"
            "7. Conditions particulières d'application en RDC\n"
            "Pluviométrie intense, sols érodables, occupation non planifiée, contraintes foncières et "
            "budgétaires.\n\n"
            "8. Points soumis à l'examen des experts\n"
            "- Cartographie des zones à risque ;\n"
            "- priorisation des interventions ;\n"
            "- techniques adaptées aux moyens locaux.\n\n"
            "9. Annexes\n"
            "[À COMPLÉTER PAR LES EXPERTS] : fiches techniques de stabilisation.\n\n"
            "10. Bibliographie\n"
            "- [À COMPLÉTER PAR LES EXPERTS]."
        ),
    },
    {
        "code": "NCD 203",
        "title": "Règles de dimensionnement et d'exécution des fondations superficielles et profondes",
        "sc_number": 3,
        "wg_name": "Fondations",
        "category": "Géotechnique & Fondations",
        "iso_reference": "Eurocode 7 (EN 1997)",
        "description": (
            "Définir des règles de dimensionnement et d'exécution des fondations "
            "superficielles et profondes, sur la base de l'Eurocode 7 (EN 1997) et "
            "des pratiques géotechniques reconnues."
        ),
        "tags": "fondations, superficielles, profondes, Eurocode 7, portance",
        "content": (
            "AVANT-PROPOS\n"
            "Le dimensionnement des fondations conditionne la sécurité des ouvrages. Ce projet définit des "
            "règles de dimensionnement et d'exécution, sur la base de l'Eurocode 7.\n\n"
            "INTRODUCTION\n"
            "Le problème traité est l'absence de référentiel national pour le calcul de la portance, des "
            "tassements et de l'exécution des fondations.\n\n"
            "1. Domaine d'application\n"
            "Fondations superficielles (semelles, radiers) et profondes (pieux) des ouvrages courants en "
            "RDC. Limites à préciser.\n\n"
            "2. Références normatives\n"
            "- EN 1997 (Eurocode 7), Calcul géotechnique (parties et édition à vérifier).\n"
            "- [À COMPLÉTER PAR LES EXPERTS] : normes d'exécution des pieux et essais associés.\n\n"
            "3. Termes et définitions\n"
            "Capacité portante, tassement, semelle, radier, pieu, frottement latéral, pointe — "
            "définitions de travail.\n\n"
            "4. Principes généraux\n"
            "Vérifier les états limites (portance, tassement, glissement) ; associer reconnaissance et "
            "dimensionnement ; prescrire les contrôles d'exécution.\n\n"
            "5. Exigences techniques\n"
            "[À COMPLÉTER PAR LES EXPERTS] : méthodes de calcul, coefficients partiels, paramètres de "
            "sol. Aucun coefficient ou seuil ne doit être inventé.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "[À COMPLÉTER PAR LES EXPERTS] : essais de pieux, contrôle des tassements, réception des "
            "fouilles.\n\n"
            "7. Conditions particulières d'application en RDC\n"
            "Sols latéritiques, nappe phréatique, disponibilité des essais in situ et du matériel.\n\n"
            "8. Points soumis à l'examen des experts\n"
            "- Annexes nationales de l'Eurocode 7 ;\n"
            "- méthodes d'essai disponibles localement ;\n"
            "- typologie des pieux usuels.\n\n"
            "9. Annexes\n"
            "[À COMPLÉTER PAR LES EXPERTS] : abaques et modèles de notes de calcul.\n\n"
            "10. Bibliographie\n"
            "- EN 1997 (Eurocode 7).\n"
            "- [À COMPLÉTER PAR LES EXPERTS]."
        ),
    },

    # ── SC-OH ────────────────────────────────────────────────────────────────
    {
        "code": "NCD 301",
        "title": "Guide méthodologique d'estimation des débits de crue et d'hydrologie statistique pour les infrastructures",
        "sc_number": 5,
        "wg_name": "Gestion des Eaux Pluviales",
        "category": "Ouvrages hydrauliques",
        "iso_reference": "Guides OMM (hydrologie)",
        "description": (
            "Fournir une méthodologie d'estimation des débits de crue et d'hydrologie "
            "statistique pour le dimensionnement des infrastructures, en s'appuyant "
            "sur les guides de l'Organisation météorologique mondiale."
        ),
        "tags": "hydrologie, débits de crue, statistique, OMM, dimensionnement",
        "content": (
            "AVANT-PROPOS\n"
            "Le dimensionnement des ouvrages hydrauliques repose sur l'estimation des crues. Ce guide "
            "propose une méthodologie d'hydrologie statistique adaptée aux données disponibles en RDC.\n\n"
            "INTRODUCTION\n"
            "Le problème traité est l'insuffisance et l'hétérogénéité des données hydrométriques et des "
            "méthodes d'estimation des crues.\n\n"
            "1. Domaine d'application\n"
            "Estimation des débits de crue pour le dimensionnement des ouvrages hydrauliques et des "
            "infrastructures en RDC. Limites à préciser.\n\n"
            "2. Références normatives\n"
            "- Guides de l'Organisation météorologique mondiale (OMM) sur l'estimation des crues et "
            "l'hydrologie statistique (références précises à identifier).\n"
            "- [À COMPLÉTER PAR LES EXPERTS] : manuels nationaux d'hydrologie.\n\n"
            "3. Termes et définitions\n"
            "Débit de crue, période de retour, pluie de projet, bassin versant, hydrométrie — "
            "définitions de travail.\n\n"
            "4. Principes généraux\n"
            "Choisir la méthode selon la disponibilité des données ; traiter l'incertitude ; documenter "
            "les hypothèses ; utiliser des données réellement observées.\n\n"
            "5. Exigences techniques\n"
            "[À COMPLÉTER PAR LES EXPERTS] : méthodes statistiques (ajustement de lois, régionalisation), "
            "choix des périodes de retour. Aucun paramètre ou coefficient ne doit être inventé.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "[À COMPLÉTER PAR LES EXPERTS] : validation croisée, comparaison avec des bassins jaugés.\n\n"
            "7. Conditions particulières d'application en RDC\n"
            "Réseau hydrométrique limité, pluviométrie, occupation des bassins versants.\n\n"
            "8. Points soumis à l'examen des experts\n"
            "- Sélection des guides OMM ;\n"
            "- périodes de retour à retenir par type d'ouvrage ;\n"
            "- stratégie de collecte de données.\n\n"
            "9. Annexes\n"
            "[À COMPLÉTER PAR LES EXPERTS] : exemples de calcul.\n\n"
            "10. Bibliographie\n"
            "- Guides OMM (hydrologie).\n"
            "- [À COMPLÉTER PAR LES EXPERTS]."
        ),
    },
    {
        "code": "NCD 303",
        "title": "Normes de dimensionnement hydraulique des caniveaux, dalots et réseaux de drainage pluvial urbain",
        "sc_number": 5,
        "wg_name": "Gestion des Eaux Pluviales",
        "category": "Ouvrages hydrauliques",
        "iso_reference": "Guides techniques de calcul hydraulique",
        "description": (
            "Définir des normes de dimensionnement hydraulique des caniveaux, dalots "
            "et réseaux de drainage pluvial urbain, adaptées au contexte congolais."
        ),
        "tags": "drainage pluvial, caniveaux, dalots, dimensionnement hydraulique, urbain",
        "content": (
            "AVANT-PROPOS\n"
            "Le drainage pluvial urbain est un enjeu majeur face aux inondations. Ce projet fixe des "
            "règles de dimensionnement des caniveaux, dalots et réseaux de drainage.\n\n"
            "INTRODUCTION\n"
            "Le problème traité est le sous-dimensionnement fréquent des ouvrages de drainage et "
            "l'absence de référentiel national.\n\n"
            "1. Domaine d'application\n"
            "Caniveaux, dalots et réseaux de drainage pluvial urbain en RDC. Limites à préciser.\n\n"
            "2. Références normatives\n"
            "- Guides techniques de calcul hydraulique (à identifier et valider par le GT).\n"
            "- [À COMPLÉTER PAR LES EXPERTS] : référentiels d'hydrologie urbaine et de drainage.\n\n"
            "3. Termes et définitions\n"
            "Débit de pointe, section hydraulique, caniveau, dalot, exutoire, temps de concentration — "
            "définitions de travail.\n\n"
            "4. Principes généraux\n"
            "Dimensionner en fonction des débits de pointe ; assurer la continuité hydraulique jusqu'aux "
            "exutoires ; prévoir l'entretien et l'auto-curage.\n\n"
            "5. Exigences techniques\n"
            "[À COMPLÉTER PAR LES EXPERTS] : formules de dimensionnement et leurs limites, vitesses "
            "admissibles, gabarits. Aucune valeur ne doit être inventée.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "[À COMPLÉTER PAR LES EXPERTS] : vérification des sections, essais de réception, suivi des "
            "points de débordement.\n\n"
            "7. Conditions particulières d'application en RDC\n"
            "Pluviométrie intense, urbanisation rapide, encombrement des exutoires, entretien.\n\n"
            "8. Points soumis à l'examen des experts\n"
            "- Choix des formules et des périodes de retour ;\n"
            "- gabarits normalisés ;\n"
            "- articulation avec la voirie.\n\n"
            "9. Annexes\n"
            "[À COMPLÉTER PAR LES EXPERTS] : abaques de dimensionnement.\n\n"
            "10. Bibliographie\n"
            "- [À COMPLÉTER PAR LES EXPERTS]."
        ),
    },
    {
        "code": "NCD 304",
        "title": "Prescriptions techniques pour la construction et la protection sanitaire des forages d'eau potable",
        "sc_number": 5,
        "wg_name": "Forages et Captage",
        "category": "Ouvrages hydrauliques",
        "iso_reference": "Lignes directrices OMS (eau de boisson)",
        "description": (
            "Définir des prescriptions techniques pour la construction et la "
            "protection sanitaire des forages d'eau potable, en s'appuyant sur les "
            "lignes directrices de l'OMS et les référentiels de captage."
        ),
        "tags": "forages, eau potable, protection sanitaire, OMS, captage",
        "content": (
            "AVANT-PROPOS\n"
            "Les forages constituent une source majeure d'eau potable. Ce projet fixe les prescriptions "
            "de construction et de protection sanitaire, sur la base des lignes directrices de l'OMS.\n\n"
            "INTRODUCTION\n"
            "Le problème traité est la contamination des forages et la qualité hétérogène des ouvrages de "
            "captage.\n\n"
            "1. Domaine d'application\n"
            "Construction et protection sanitaire des forages d'eau potable en RDC. Limites à préciser.\n\n"
            "2. Références normatives\n"
            "- OMS, Guidelines for drinking-water quality (édition à vérifier).\n"
            "- [À COMPLÉTER PAR LES EXPERTS] : référentiels de cimentation, tubage et protection des "
            "têtes de forage.\n\n"
            "3. Termes et définitions\n"
            "Forage, aquifère, tubage, crépine, cimentation annulaire, périmètre de protection — "
            "définitions de travail.\n\n"
            "4. Principes généraux\n"
            "Assurer l'étanchéité sanitaire du forage ; prévenir la contamination de la nappe ; prévoir "
            "les périmètres de protection ; contrôler la qualité de l'eau.\n\n"
            "5. Exigences techniques\n"
            "[À COMPLÉTER PAR LES EXPERTS] : profondeurs, diamètres, matériaux, exigences de cimentation "
            "et de désinfection. Aucune valeur ne doit être inventée.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "[À COMPLÉTER PAR LES EXPERTS] : essais de pompage, analyses de qualité d'eau, inspection des "
            "ouvrages.\n\n"
            "7. Conditions particulières d'application en RDC\n"
            "Hydrogéologie, profondeur des nappes, matériel de foration disponible, assainissement.\n\n"
            "8. Points soumis à l'examen des experts\n"
            "- Édition des lignes directrices OMS ;\n"
            "- normes de qualité d'eau à retenir ;\n"
            "- périmètres de protection.\n\n"
            "9. Annexes\n"
            "[À COMPLÉTER PAR LES EXPERTS] : modèles de fiches de forage.\n\n"
            "10. Bibliographie\n"
            "- OMS, Guidelines for drinking-water quality.\n"
            "- [À COMPLÉTER PAR LES EXPERTS]."
        ),
    },

    # ── SC-VRD ───────────────────────────────────────────────────────────────
    {
        "code": "NCD 402",
        "title": "Normes d'installation des réseaux électriques basse tension et de protection contre la foudre",
        "sc_number": 7,
        "wg_name": "Installations électriques, courants forts et éclairage public",
        "category": "Réseaux divers, équipements & fluides",
        "iso_reference": "IEC 60364",
        "description": (
            "Définir des normes d'installation des réseaux électriques basse tension "
            "et de protection contre la foudre, sur la base de l'IEC 60364 et des "
            "référentiels de protection contre la foudre."
        ),
        "tags": "électricité basse tension, IEC 60364, protection foudre, installations, ERP",
        "content": (
            "AVANT-PROPOS\n"
            "Les installations électriques basse tension et la protection contre la foudre engagent la "
            "sécurité des personnes et des biens. Ce projet définit des règles d'installation adaptées.\n\n"
            "INTRODUCTION\n"
            "Le problème traité est la sécurité électrique et la protection contre la foudre dans un "
            "contexte climatique et réglementaire à préciser.\n\n"
            "1. Domaine d'application\n"
            "Installations électriques basse tension et protection contre la foudre des bâtiments et "
            "équipements en RDC. Limites à préciser.\n\n"
            "2. Références normatives\n"
            "- IEC 60364 (série), Installations électriques à basse tension (référence vérifiée ; parties "
            "et éditions à préciser).\n"
            "- [À COMPLÉTER PAR LES EXPERTS] : référentiels de protection contre la foudre (série IEC 62305 "
            "à confirmer).\n\n"
            "3. Termes et définitions\n"
            "Basse tension, schéma de liaison à la terre, dispositif de protection, parafoudre, prise de "
            "terre — définitions de travail.\n\n"
            "4. Principes généraux\n"
            "Assurer la protection des personnes contre les contacts indirects ; définir les schémas de "
            "liaison à la terre ; prescrire la protection contre la foudre et les surtensions.\n\n"
            "5. Exigences techniques\n"
            "[À COMPLÉTER PAR LES EXPERTS] : sections, dispositifs de protection, règles de mise à la "
            "terre. Aucune valeur ne doit être inventée.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "[À COMPLÉTER PAR LES EXPERTS] : essais de continuité, mesure de terre, essais d'isolement, "
            "réception.\n\n"
            "7. Conditions particulières d'application en RDC\n"
            "Orages fréquents, qualité des réseaux, disponibilité des matériels, habilitations.\n\n"
            "8. Points soumis à l'examen des experts\n"
            "- Parties de l'IEC 60364 à retenir ;\n"
            "- référentiel foudre applicable ;\n"
            "- schémas de liaison à la terre recommandés.\n\n"
            "9. Annexes\n"
            "[À COMPLÉTER PAR LES EXPERTS] : tableaux et schémas types.\n\n"
            "10. Bibliographie\n"
            "- IEC 60364 (série).\n"
            "- [À COMPLÉTER PAR LES EXPERTS]."
        ),
    },
    {
        "code": "NCD 403",
        "title": "Prescriptions de sécurité incendie et de câblage dans les Établissements Recevant du Public (ERP)",
        "sc_number": 7,
        "wg_name": "Courants faibles, sécurité électronique et automatismes",
        "category": "Réseaux divers, équipements & fluides",
        "iso_reference": "ISO/IEC 11801",
        "description": (
            "Définir des prescriptions de sécurité incendie et de câblage dans les ERP, "
            "en s'appuyant sur l'ISO/IEC 11801 et les normes de sécurité incendie "
            "pertinentes à déterminer."
        ),
        "tags": "sécurité incendie, ERP, câblage, ISO/IEC 11801, courants faibles",
        "content": (
            "AVANT-PROPOS\n"
            "La sécurité incendie et la qualité du câblage dans les ERP sont essentielles pour la "
            "protection des occupants. Ce projet définit des prescriptions à adapter au contexte congolais.\n\n"
            "INTRODUCTION\n"
            "Le problème traité est l'absence de référentiel national pour la sécurité incendie et le "
            "câblage des établissements recevant du public.\n\n"
            "1. Domaine d'application\n"
            "Sécurité incendie et câblage (courants faibles) dans les ERP en RDC. Limites à préciser.\n\n"
            "2. Références normatives\n"
            "- ISO/IEC 11801, Technologies de l'information — Câblage générique des locaux d'utilisateurs "
            "(édition à vérifier).\n"
            "- [À COMPLÉTER PAR LES EXPERTS] : normes de sécurité incendie pertinentes (à déterminer).\n\n"
            "3. Termes et définitions\n"
            "ERP, compartimentage, désenfumage, évacuation, câblage structuré, SSI — définitions de "
            "travail.\n\n"
            "4. Principes généraux\n"
            "Garantir l'évacuation et l'intervention des secours ; limiter la propagation du feu et des "
            "fumées ; fiabiliser les systèmes de sécurité et le câblage.\n\n"
            "5. Exigences techniques\n"
            "[À COMPLÉTER PAR LES EXPERTS] : classement des ERP, moyens de secours, exigences de câblage. "
            "Aucune valeur ne doit être inventée.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "[À COMPLÉTER PAR LES EXPERTS] : essais des équipements de sécurité, vérification du câblage, "
            "réception.\n\n"
            "7. Conditions particulières d'application en RDC\n"
            "Parc immobilier existant, disponibilité des équipements, services de secours, réglementation "
            "nationale.\n\n"
            "8. Points soumis à l'examen des experts\n"
            "- Classification des ERP ;\n"
            "- normes de sécurité incendie à adopter ;\n"
            "- exigences de câblage et de supervision.\n\n"
            "9. Annexes\n"
            "[À COMPLÉTER PAR LES EXPERTS] : grilles d'évaluation.\n\n"
            "10. Bibliographie\n"
            "- ISO/IEC 11801.\n"
            "- [À COMPLÉTER PAR LES EXPERTS]."
        ),
    },

    # ── SC-ENV ───────────────────────────────────────────────────────────────
    {
        "code": "NCD 501",
        "title": "Directives nationales pour la réalisation des Études d'Impact Environnemental et Social (EIES) des projets ITP",
        "sc_number": 2,
        "wg_name": "Évaluations environnementales et sociales (EES)",
        "category": "Environnement, santé & sécurité",
        "iso_reference": "ISO 14001",
        "description": (
            "Établir des directives nationales pour la réalisation des EIES des "
            "projets d'infrastructures et de travaux publics, en s'appuyant sur "
            "l'ISO 14001 et la réglementation nationale applicable."
        ),
        "tags": "EIES, environnement, social, ISO 14001, impacts, ITP",
        "content": (
            "AVANT-PROPOS\n"
            "Les EIES conditionnent la durabilité des projets. Ce projet définit des directives "
            "nationales pour leur réalisation, en lien avec la réglementation congolaise.\n\n"
            "INTRODUCTION\n"
            "Le problème traité est l'hétérogénéité des EIES et leur faible prise en compte des enjeux "
            "locaux.\n\n"
            "1. Domaine d'application\n"
            "Réalisation des EIES des projets d'infrastructures et de travaux publics (ITP) en RDC. "
            "Limites à préciser.\n\n"
            "2. Références normatives\n"
            "- ISO 14001, Systèmes de management environnemental (édition à vérifier).\n"
            "- [À COMPLÉTER PAR LES EXPERTS] : textes réglementaires nationaux sur les EIES.\n\n"
            "3. Termes et définitions\n"
            "EIES, impact environnemental et social, mesure d'atténuation, consultation publique, "
            "suivi — définitions de travail.\n\n"
            "4. Principes généraux\n"
            "Définir le contenu minimal de l'EIES ; associer les parties prenantes ; prévoir le suivi et "
            "le contrôle des mesures.\n\n"
            "5. Exigences techniques\n"
            "[À COMPLÉTER PAR LES EXPERTS] : contenu du rapport, méthodes d'évaluation des impacts, "
            "seuils de déclenchement. Aucune valeur réglementaire ne doit être inventée.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "[À COMPLÉTER PAR LES EXPERTS] : revue des rapports, indicateurs de suivi.\n\n"
            "7. Conditions particulières d'application en RDC\n"
            "Cadre institutionnel, capacités des bureaux d'études, participation des communautés.\n\n"
            "8. Points soumis à l'examen des experts\n"
            "- Articulation avec la réglementation nationale ;\n"
            "- contenu minimal de l'EIES ;\n"
            "- mécanismes de consultation publique.\n\n"
            "9. Annexes\n"
            "[À COMPLÉTER PAR LES EXPERTS] : canevas de rapport.\n\n"
            "10. Bibliographie\n"
            "- ISO 14001.\n"
            "- [À COMPLÉTER PAR LES EXPERTS]."
        ),
    },
    {
        "code": "NCD 502",
        "title": "Code de bonne pratique d'hygiène, de santé et de sécurité au travail (SST) sur les chantiers de construction",
        "sc_number": 2,
        "wg_name": "Hygiène, santé et sécurité au travail (SST)",
        "category": "Environnement, santé & sécurité",
        "iso_reference": "ISO 45001:2018",
        "description": (
            "Établir un code de bonne pratique SST pour les chantiers de construction "
            "en RDC, sur la base de l'ISO 45001 et des règles d'hygiène et de "
            "sécurité reconnues."
        ),
        "tags": "SST, hygiène, santé, sécurité, chantiers, ISO 45001",
        "content": (
            "AVANT-PROPOS\n"
            "Les chantiers de construction concentrent des risques d'accidents et de maladies "
            "professionnelles. Ce code fixe des règles d'hygiène, de santé et de sécurité adaptées.\n\n"
            "INTRODUCTION\n"
            "Le problème traité est la faiblesse de la prévention des risques sur les chantiers "
            "congolais.\n\n"
            "1. Domaine d'application\n"
            "Chantiers de construction et d'infrastructures en RDC. Limites à préciser.\n\n"
            "2. Références normatives\n"
            "- ISO 45001:2018, Systèmes de management de la santé et de la sécurité au travail — Exigences "
            "et lignes directrices pour leur utilisation (référence vérifiée).\n"
            "- [À COMPLÉTER PAR LES EXPERTS] : réglementation nationale du travail et de la sécurité.\n\n"
            "3. Termes et définitions\n"
            "Danger, risque, équipement de protection individuelle, analyse des risques, accident du "
            "travail — définitions de travail.\n\n"
            "4. Principes généraux\n"
            "Identifier et évaluer les risques ; hiérarchiser les mesures de prévention ; former le "
            "personnel ; assurer le suivi des incidents.\n\n"
            "5. Exigences techniques\n"
            "[À COMPLÉTER PAR LES EXPERTS] : protections collectives et individuelles, organisation du "
            "chantier, premiers secours. Aucune valeur ne doit être inventée.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "[À COMPLÉTER PAR LES EXPERTS] : inspections de chantier, registres, indicateurs de "
            "sinistralité.\n\n"
            "7. Conditions particulières d'application en RDC\n"
            "Saisonnalité, disponibilité des EPI, taille des entreprises, économie informelle.\n\n"
            "8. Points soumis à l'examen des experts\n"
            "- Articulation avec l'ISO 45001 et la réglementation nationale ;\n"
            "- obligations selon la taille du chantier ;\n"
            "- mécanismes de contrôle.\n\n"
            "9. Annexes\n"
            "[À COMPLÉTER PAR LES EXPERTS] : check-lists de prévention.\n\n"
            "10. Bibliographie\n"
            "- ISO 45001:2018.\n"
            "- [À COMPLÉTER PAR LES EXPERTS]."
        ),
    },
    {
        "code": "NCD 503",
        "title": "Règlement de gestion, de tri et de mise en décharge des déchets inertes et gravats du BTP",
        "sc_number": 2,
        "wg_name": "Déchets Solides & CET",
        "category": "Environnement, santé & sécurité",
        "iso_reference": "Famille ISO 59000",
        "description": (
            "Définir un règlement de gestion, de tri et de mise en décharge des "
            "déchets inertes et gravats du BTP, en s'appuyant sur la famille "
            "ISO 59000 et la réglementation nationale."
        ),
        "tags": "déchets BTP, gravats, tri, décharge, économie circulaire, ISO 59000",
        "content": (
            "AVANT-PROPOS\n"
            "Les déchets inertes et gravats du BTP sont rarement gérés de façon structurée. Ce règlement "
            "vise à organiser leur tri, leur valorisation et leur mise en décharge.\n\n"
            "INTRODUCTION\n"
            "Le problème traité est l'abandon anarchique des gravats et l'absence de filière de gestion "
            "des déchets inertes.\n\n"
            "1. Domaine d'application\n"
            "Gestion, tri et mise en décharge des déchets inertes et gravats issus des chantiers de BTP "
            "en RDC. Limites à préciser.\n\n"
            "2. Références normatives\n"
            "- Famille ISO 59000 (économie circulaire ; références précises à vérifier).\n"
            "- [À COMPLÉTER PAR LES EXPERTS] : réglementation nationale sur les déchets.\n\n"
            "3. Termes et définitions\n"
            "Déchet inerte, gravat, valorisation, recyclage, installation de stockage — définitions de "
            "travail.\n\n"
            "4. Principes généraux\n"
            "Prévenir et réduire les déchets ; trier à la source ; favoriser la valorisation ; encadrer "
            "la mise en décharge des résidus.\n\n"
            "5. Exigences techniques\n"
            "[À COMPLÉTER PAR LES EXPERTS] : catégories de déchets, conditions de stockage, traçabilité. "
            "Aucune valeur ne doit être inventée.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "[À COMPLÉTER PAR LES EXPERTS] : bordereaux de suivi, contrôles des sites de dépôt.\n\n"
            "7. Conditions particulières d'application en RDC\n"
            "Filières de valorisation limitées, occupation urbaine, capacités de contrôle.\n\n"
            "8. Points soumis à l'examen des experts\n"
            "- Références de la famille ISO 59000 ;\n"
            "- obligations des producteurs de déchets ;\n"
            "- sites de dépôt autorisés.\n\n"
            "9. Annexes\n"
            "[À COMPLÉTER PAR LES EXPERTS] : bordereaux types.\n\n"
            "10. Bibliographie\n"
            "- Famille ISO 59000.\n"
            "- [À COMPLÉTER PAR LES EXPERTS]."
        ),
    },

    # ── SC-BAT ───────────────────────────────────────────────────────────────
    {
        "code": "NCD 601",
        "title": "Règles simplifiées de calcul et de construction parasismique et anticyclonique pour l'habitat",
        "sc_number": 1,
        "wg_name": "Structures et Sécurité",
        "category": "Bâtiments courants & spéciaux",
        "iso_reference": "Eurocodes structuraux",
        "description": (
            "Définir des règles simplifiées de calcul et de construction parasismique "
            "et anticyclonique pour l'habitat en RDC, sur la base des Eurocodes "
            "structuraux et des données locales."
        ),
        "tags": "parasismique, anticyclonique, habitat, Eurocodes, structures",
        "content": (
            "AVANT-PROPOS\n"
            "La présente règle est élaborée par la sous-commission Bâtiments courants et spéciaux de la "
            "CNE-ITP afin de fournir aux concepteurs et constructeurs d'habitations des dispositions "
            "simplifiées de calcul et de construction destinées à réduire la vulnérabilité des bâtiments "
            "aux séismes et aux vents forts. Elle s'appuie sur les Eurocodes structuraux et s'inscrit "
            "dans le programme d'adoption et d'adaptation des référentiels internationaux aux réalités "
            "congolaises.\n\n"
            "INTRODUCTION\n"
            "L'habitat courant constitue l'essentiel du patrimoine bâti. Sa sécurité face aux actions "
            "sismiques et climatiques dépend largement du respect de règles de conception simples : "
            "régularité de la structure, continuité des chaînages, qualité des liaisons et des "
            "matériaux. Le présent document propose des règles de calcul simplifiées et des dispositions "
            "constructives applicables aux constructions de faible et moyenne hauteur.\n\n"
            "1. Domaine d'application\n"
            "La présente règle s'applique aux bâtiments d'habitation courants, en maçonnerie porteuse, "
            "en béton armé ou en structures mixtes, de faible ou moyenne hauteur. Elle couvre la "
            "conception, le dimensionnement simplifié et la mise en œuvre des éléments de "
            "contreventement. Elle ne s'applique pas aux ouvrages exceptionnels, aux bâtiments de grande "
            "hauteur ni aux structures exigeant un calcul dynamique détaillé, qui relèvent des normes "
            "d'ingénierie complètes.\n\n"
            "2. Références normatives\n"
            "EN 1990 — Bases de calcul des structures ; EN 1991-1-1 — Actions générales, densités, poids "
            "propres et charges d'exploitation ; EN 1991-1-4 — Actions du vent ; EN 1998-1 — Calcul des "
            "structures pour leur résistance aux séismes ; EN 1992 et EN 1996 — Béton et maçonnerie.\n\n"
            "3. Termes et définitions\n"
            "Séisme, accélération de calcul au sol, spectre de réponse, zone sismique, action du vent, "
            "pression dynamique, contreventement, chaînage, ductilité, régularité en plan et en "
            "élévation.\n\n"
            "4. Exigences générales\n"
            "Concevoir des structures simples, symétriques et régulières en plan et en élévation ; "
            "assurer une liaison continue des éléments porteurs par des chaînages horizontaux et "
            "verticaux ; garantir un cheminement clair des efforts horizontaux jusqu'aux fondations ; "
            "employer des matériaux de qualité contrôlée et homogène.\n\n"
            "5. Exigences spécifiques\n"
            "Dispositions constructives : chaînages en béton armé au niveau des soubassements, des "
            "planchers et en tête de murs ; liaison des murs de refend avec les façades ; limitation des "
            "porte-à-faux ; ancrage et contreventement de la toiture. Les valeurs de calcul "
            "(coefficients partiels, paramètres de zone, spectres) sont reprises de l'EN 1998-1 et des "
            "annexes nationales applicables, à adopter et adapter au contexte congolais.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "Contrôle des matériaux en cours de chantier ; vérification de la position et de la "
            "continuité des chaînages ; contrôle du ferraillage et de la mise en œuvre des nœuds ; "
            "réception des éléments de contreventement.\n\n"
            "7. Critères de conformité\n"
            "Respect des dispositions constructives prescrites ; conformité des résultats d'essais de "
            "matériaux ; absence de défaut de liaison entre éléments ; respect des tolérances "
            "d'exécution.\n\n"
            "8. Conditions d'application en RDC\n"
            "Sols et fondations adaptés ; disponibilité des matériaux et des compétences ; contraintes "
            "climatiques ; établissement progressif d'un zonage sismique et climatique national à partir "
            "des données disponibles.\n\n"
            "9. Documentation et traçabilité\n"
            "Plans d'exécution, notes de calcul simplifiées, procès-verbaux d'essais, fiches de contrôle "
            "de mise en œuvre.\n\n"
            "10. Annexes\n"
            "Schémas types de chaînage, tableaux de dispositions constructives minimales, exemples "
            "d'application.\n\n"
            "11. Bibliographie\n"
            "Eurocodes structuraux (EN 1990, EN 1991, EN 1998, EN 1992, EN 1996)."
        ),
    },
    {
        "code": "NCD 602",
        "title": "Normes d'accessibilité universelle pour les personnes à mobilité réduite (PMR) dans les bâtiments publics",
        "sc_number": 1,
        "wg_name": "Structures et Sécurité",
        "category": "Bâtiments courants & spéciaux",
        "iso_reference": "ISO 21542",
        "description": (
            "Définir des normes d'accessibilité universelle pour les PMR dans les "
            "bâtiments publics, sur la base de l'ISO 21542 dont l'édition et "
            "l'applicabilité restent à vérifier."
        ),
        "tags": "accessibilité, PMR, bâtiments publics, ISO 21542, universel",
        "content": (
            "AVANT-PROPOS\n"
            "La présente norme définit les exigences d'accessibilité universelle des bâtiments publics "
            "afin de garantir à toute personne, notamment aux personnes à mobilité réduite, un accès et "
            "une utilisation autonomes des espaces et des services. Elle s'appuie sur l'ISO 21542 et "
            "vise son application au contexte congolais.\n\n"
            "INTRODUCTION\n"
            "L'accessibilité constitue une condition d'équité et de sécurité. Le présent document "
            "précise les cheminements, les dimensions, les pentes et les équipements à mettre en œuvre "
            "pour l'accessibilité des bâtiments publics, qu'ils soient neufs ou existants.\n\n"
            "1. Domaine d'application\n"
            "Bâtiments recevant du public : accès extérieurs, halls, circulations horizontales et "
            "verticales, portes, escaliers, ascenseurs, sanitaires et signalétique. Application aux "
            "constructions neuves comme aux travaux de réhabilitation.\n\n"
            "2. Références normatives\n"
            "ISO 21542 — Construction immobilière, accessibilité et facilité d'utilisation de "
            "l'environnement bâti.\n\n"
            "3. Termes et définitions\n"
            "Personne à mobilité réduite, accessibilité universelle, cheminement accessible, pente, "
            "palier de repos, main courante, contraste visuel, bande podotactile, aire de manœuvre.\n\n"
            "4. Exigences générales\n"
            "Garantir un cheminement continu, sécurisé et repérable depuis la voirie jusqu'aux espaces "
            "desservis ; prévoir des largeurs, pentes et paliers compatibles avec l'usage d'un fauteuil "
            "roulant ; assurer la détectabilité et la signalétique.\n\n"
            "5. Exigences spécifiques\n"
            "Cheminements de largeur suffisante, pentes douces avec paliers de repos, portes à largeur "
            "utile adaptée, commandes et sanitaires accessibles, mains courantes, éclairage et contraste "
            "adaptés. Les valeurs dimensionnelles sont reprises de l'ISO 21542.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "Vérification géométrique des cheminements et des pentes ; contrôle des largeurs et des "
            "aires de manœuvre ; essais de fonctionnement des équipements ; audits d'accessibilité.\n\n"
            "7. Critères de conformité\n"
            "Respect des dimensions et pentes prescrites ; fonctionnement des équipements ; continuité "
            "du cheminement ; présence et lisibilité de la signalétique.\n\n"
            "8. Conditions d'application en RDC\n"
            "Parc immobilier existant, adaptation progressive, matériaux et entretien, climat.\n\n"
            "9. Documentation et traçabilité\n"
            "Plans d'accessibilité, fiches de contrôle, rapports d'audit.\n\n"
            "10. Annexes\n"
            "Schémas de dimensions types, grilles de contrôle d'accessibilité.\n\n"
            "11. Bibliographie\n"
            "ISO 21542."
        ),
    },
    {
        "code": "NCD 604",
        "title": "Guide d'introduction progressive des processus numériques et de la maquette BIM dans la commande publique",
        "sc_number": 1,
        "wg_name": "Transition numérique et BIM (Building Information Modeling)",
        "category": "Bâtiments courants & spéciaux",
        "iso_reference": "ISO 19650 (série)",
        "description": (
            "Guider l'introduction progressive des processus numériques et de la "
            "maquette BIM dans la commande publique en RDC, sur la base de la "
            "série ISO 19650."
        ),
        "tags": "BIM, numérique, commande publique, ISO 19650, maquette",
        "content": (
            "AVANT-PROPOS\n"
            "Le présent guide accompagne l'introduction progressive du BIM et des processus numériques "
            "dans la commande publique congolaise. Il s'appuie sur la série ISO 19650 et définit les "
            "étapes, les rôles et les exigences d'information à mettre en place.\n\n"
            "INTRODUCTION\n"
            "La transition numérique de la commande publique repose sur la structuration de "
            "l'information et la collaboration autour d'un environnement commun de données. Le présent "
            "guide fournit un cadre progressif adapté aux capacités des maîtres d'ouvrage et des acteurs "
            "de la construction.\n\n"
            "1. Domaine d'application\n"
            "Processus de production et de gestion de l'information des projets de bâtiments et "
            "d'infrastructures commandés par les personnes publiques, de la phase d'étude jusqu'à "
            "l'exploitation.\n\n"
            "2. Références normatives\n"
            "ISO 19650-1 — Concepts et principes ; ISO 19650-2 — Phase de réalisation des actifs ; "
            "ISO 19650-3 — Phase d'exploitation des actifs ; ISO 19650-5 — Approche de la sécurité de "
            "l'information.\n\n"
            "3. Termes et définitions\n"
            "BIM, maquette numérique, environnement commun de données, exigences d'information "
            "organisationnelles et de projet, plan d'exécution BIM, niveau de développement, format IFC.\n\n"
            "4. Exigences générales\n"
            "Définir les exigences d'information avant la consultation ; organiser un environnement "
            "commun de données unique ; répartir les rôles et responsabilités entre les parties ; "
            "prévoir le contrôle et la remise des livrables.\n\n"
            "5. Exigences spécifiques\n"
            "Mise en place progressive par niveaux de maturité ; adoption de formats ouverts (IFC) ; "
            "gestion des statuts et des versions de l'information ; prise en compte de la sécurité de "
            "l'information.\n\n"
            "6. Méthodes de contrôle et de vérification\n"
            "Vérification des livrables numériques ; contrôle de conformité des échanges d'information ; "
            "revues périodiques de l'environnement commun de données.\n\n"
            "7. Critères de conformité\n"
            "Respect des exigences d'information ; validité des échanges ; traçabilité des versions et "
            "des statuts.\n\n"
            "8. Conditions d'application en RDC\n"
            "Infrastructure numérique, compétences disponibles, maturité des acteurs, accompagnement des "
            "petites structures.\n\n"
            "9. Documentation et traçabilité\n"
            "Exigences d'information, plans d'exécution BIM, procès-verbaux de réception des livrables.\n\n"
            "10. Annexes\n"
            "Feuille de route de déploiement, gabarits d'exigences d'information.\n\n"
            "11. Bibliographie\n"
            "ISO 19650 (série)."
        ),
    },
]


def catalogue_count():
    return len(CATALOGUE)

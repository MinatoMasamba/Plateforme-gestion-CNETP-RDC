# ARCHITECTURE API : GOUVERNANCE (apps/governance)

## 📌 Rôle Hybride
Définit le plan structurel (Arborescence CTM > WG > Affectation). L'interface React dépend de ces tables pour savoir comment router l'utilisateur et quel document l'utilisateur a le droit d'ouvrir sur l'écran d'accueil.

---

## 1. Cartographie Exhaustive des 8 Comités Techniques Miroirs (CTMs) & 24 Groupes de Travail (WGs)

Le script de peuplement initial (`Seed / Fixtures`) de la base de données Django doit enregistrer précisément l'arborescence suivante :

### ⚖️ CTM 1 : Géotechnique et Risques Naturels (19 Experts)
* **Alignement National & International :** Miroir **ISO/TC 182** & **ARSO/TC 83**
* **Groupes de Travail :**
  * **WG 1.1 :** Reconnaissance & Essais (Standardisation des essais in-situ/laboratoire : CBR, Proctor, pressiomètre).
  * **WG 1.2 :** Sols Tropicaux & Ferrallitiques (Spécifications propres aux sols latéritiques et sables fins de RDC).
  * **WG 1.3 :** Stabilité & Érosions (Modélisation de la stabilité des versants et protocoles antiérosifs).

### ⚖️ CTM 2 : Structures et Ouvrages d'Art (20 Experts)
* **Alignement National & International :** Miroir **ISO/TC 71** (Béton), **ISO/TC 167** (Acier) & **Eurocodes 2, 3, 4**
* **Groupes de Travail :**
  * **WG 2.1 :** Calcul Structural / Eurocodes (Adaptation des coefficients de pondération des charges d'exploitation de la RDC).
  * **WG 2.2 :** Génie Parasismique & Dynamique (Règles de construction sismiques pour le Graben Est : Goma, Bukavu).
  * **WG 2.3 :** Infrastructures Hydrauliques Lourdes (Règles de l'art pour les grands barrages, digues de protection et portiques).

### ⚖️ CTM 3 : Bâtiment, Urbanisme et Transition Numérique (20 Experts)
* **Alignement National & International :** Miroir **ISO/TC 59** (Bâtiments) & **ARSO/TC 12**
* **Groupes de Travail :**
  * **WG 3.1 :** Sécurité & Habitabilité (Sécurité incendie dans les IGH, ventilation, accessibilité universelle PMR).
  * **WG 3.2 :** BIM & Numérisation (Normalisation pour l'obligation de la maquette BIM ISO 19650 dans les marchés publics).
  * **WG 3.3 :** Performance Énergétique (Isolation thermique et ventilation naturelle en climat tropical).

### ⚖️ CTM 4 : Infrastructures Aéroportuaires (19 Experts)
* **Alignement National & International :** Miroir **ISO/TC 20** & Liaison Technique **OACI** (Organisation de l'Aviation Civile Internationale)
* **Groupes de Travail :**
  * **WG 4.1 :** Génie Civil Aéroportuaire (Structure, portance méthode ACN-PCN et enrobés spécifiques pour pistes/taxiways).
  * **WG 4.2 :** Sécurité & Éco-Infrastructures (Balisage d'approche, barrières de sécurité, servitudes et gestion environnementale).

### ⚖️ CTM 5 : Infrastructures de Transport Linéaire et Maritimes (20 Experts)
* **Alignement National & International :** Miroir **ISO/TC 269** (Rail), **ISO/TC 224** (Maritime) & **ARSO/TC 83-2**
* **Groupes de Travail :**
  * **WG 5.1 :** Ingénierie Routière (Chaussées asphaltées, pavées et routes en terre).
  * **WG 5.2 :** Superstructures Ferroviaires (Écartements des voies, caractéristiques du ballast, traverses et rails).
  * **WG 5.3 :** Génie Maritime & Portuaire (Quais, terminaux à conteneurs, ducs-d'albe et défenses).

### ⚖️ CTM 6 : Ingénierie Hydraulique et Distribution (19 Experts)
* **Alignement National & International :** Miroir **ISO/TC 224** & **ARSO/TC 41**
* **Groupes de Travail :**
  * **WG 6.1 :** Adduction Urbaine & Matériaux (Spécifications des conduites en fonte ductile, PEHD, stations de pompage et compteurs).
  * **WG 6.2 :** Hydraulique Rurale & Forages (Protocoles de captage des sources et forages ruraux).
  * **WG 6.3 :** Hydraulique Agricole (Périmètres irrigués, canaux de dérivation, maîtrise de l'eau).

### ⚖️ CTM 7 : Génie Sanitaire, Économie Circulaire et Assainissement (20 Experts)
* **Alignement National & International :** Miroir **ISO/TC 275** (Boues) & **ARSO/TC 40**
* **Groupes de Travail :**
  * **WG 7.1 :** Hydrologie Urbaine / Pluvial (Pente et pose des grands collecteurs, caniveaux pour prévenir les inondations).
  * **WG 7.2 :** Eaux Usées & Épuration (Égouts collectifs, fosses septiques, traitement des boues de vidange).
  * **WG 7.3 :** Déchets Solides & Valorisation (Décharges contrôlées, déchetteries, Centres d'Enfouissement CET).

### ⚖️ CTM 8 : Sciences des Matériaux, Métrologie et Valorisation Locale (20 Experts)
* **Alignement National & International :** Miroir **ISO/TC 165** (Bois), **ARSO/TC 11** & **OCC/BTC** (Contrôles unifiés)
* **Groupes de Travail :**
  * **WG 8.1 :** Matériaux Locaux Bio-sourcés (Normalisation du Bloc de Terre Comprimée (BTC), argiles, bois d'œuvre).
  * **WG 8.2 :** Métrologie & Protocoles d'Essais (Méthodes d'essais non destructifs avec l'OCC et le BTC).
  * **WG 8.3 :** Procédures de Certification (Critères techniques requis pour les visas de conformité).

---

## 2. `CTMViewSet` et `WGViewSet`

**Vue:** `apps.governance.views.CTMViewSet`

### `GET /api/v1/governance/my_comitees/`
* **Rôle :** Méthode hautement optimisée pour dire à l'application React "Dans quels comités l'expert connecté a-t-il le droit d'agir ?"
* **Opération Django :**
```python
@action(detail=False, methods=['get'])
def my_comitees(self, request):
    expert = request.user.expert
    # Récupérer les CTM via la table de jointure Affectation
    affectations = Affectation.objects.filter(expert=expert)
    # Serialize...
```
* **Résultat exploité par React :** Cette liste est mise dans le Store Global (Context / Redux) par la couche `useAuth.ts` au boot. Cela permet de bloquer au niveau du frontend les routes inaccessibles comme mécanisme de confort (complétant la sécurité du serveur).

## 3. Validation Sécurisée Côté Backend (Les Postes Limités)

### `POST /api/v1/governance/affectations/`
* **Rôle :** Quand le Secrétaire depuis l'écran "ExpertsModule" choisit d'affecter un ingénieur en tant que `PRESIDENT_WG`.
* **Règle Serveur Strictes :**
  Un poste comme Président est unique. Si l'Interface React (désynchronisée) essaie d'envoyer l'affectation, le backend DOIT surcharger le `Serializer.validate()` :
```python
def validate(self, data):
    if data['role_type'] == 'PRESIDENT_WG':
        if Affectation.objects.filter(wg=data['wg'], role_type='PRESIDENT_WG').exists():
            raise serializers.ValidationError("Ce groupe de travail possède déjà un Président.")
    return data
```
Le backend bloque, et renvoie `400 Bad Request`. React intercepte l'erreur dans `djangoFetch` et affiche l'alerte à l'utilisateur.

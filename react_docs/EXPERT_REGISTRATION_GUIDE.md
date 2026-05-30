# 📋 Guide d'Inscription des Experts CNETP

## Vue d'ensemble

L'inscription des experts CNETP se fait via un **endpoint public spécifique** accessible par QR Code. Les experts doivent :

1. ✅ Créer un compte utilisateur
2. ✅ Sélectionner une ou plusieurs **Sous-Commissions Techniques (CTM)**
3. ✅ Uploader leur **Curriculum Vitae (CV)**

---

## 🔗 Endpoints d'Inscription

### 1. GET - Récupérer les Structures
```
GET /api/v1/expert-registration/structures/
```

**Description**: Liste toutes les structures d'origine disponibles.

**Réponse (200)**:
```json
[
  {
    "id": 1,
    "name": "Secrétariat Général aux ITP",
    "acronym": "SG-ITP",
    "category": "ADMIN",
    "description": "...",
    "email": "contact@sg-itp.cd",
    "phone": "+243812345678",
    "website": "https://sg-itp.cd",
    "contact_person": "Jean Dupont",
    "expert_count": 12
  },
  ...
]
```

---

### 2. GET - Récupérer les CTM
```
GET /api/v1/expert-registration/ctm/
```

**Description**: Liste tous les Comités Techniques Miroirs (sous-commissions) disponibles.

**Réponse (200)**:
```json
[
  {
    "id": 1,
    "number": 1,
    "name": "Géotechnique et Risques Naturels",
    "description": "Reconnaissance des sols, géomécanique, fondations, stabilité des talus..."
  },
  {
    "id": 2,
    "number": 2,
    "name": "Ouvrages d'Art",
    "description": "Ponts, viaducs, barrages, calcul mécanique des structures..."
  },
  ...
]
```

---

### 3. POST - Inscription d'un Expert
```
POST /api/v1/expert-registration/public_register/
```

**Description**: Crée un nouvel expert et son compte utilisateur.

**Content-Type**: `multipart/form-data` (pour l'upload du CV)

**Body (FormData)**:
```
email                  = "expert@company.cd"
password               = "SecurePassword123!"
password_confirm       = "SecurePassword123!"
first_name             = "Jean"
last_name              = "Dupont"
phone                  = "+243812345678"
structure_id           = 1
specialties            = "Géotechnique, Fondations, Stabilité des sols"
ctm_ids[]              = 1
ctm_ids[]              = 2
cv                     = <binary file - PDF/DOC>
```

**JSON Alternatif (sans fichier)**:
```json
{
  "email": "expert@company.cd",
  "password": "SecurePassword123!",
  "password_confirm": "SecurePassword123!",
  "first_name": "Jean",
  "last_name": "Dupont",
  "phone": "+243812345678",
  "structure_id": 1,
  "specialties": "Géotechnique, Fondations",
  "ctm_ids": [1, 2]
}
```

**Réponse (201 - Succès)**:
```json
{
  "message": "Expert inscrit avec succès. Un email de confirmation sera envoyé.",
  "expert": {
    "id": 42,
    "email": "expert@company.cd",
    "first_name": "Jean",
    "last_name": "Dupont",
    "status": "PENDING",
    "inscription_date": "2026-05-25T12:30:45.123456Z",
    "ctm_ids": [1, 2]
  }
}
```

**Réponse (400 - Erreur)**:
```json
{
  "email": ["Cet email est déjà utilisé."],
  "password": ["Les mots de passe ne correspondent pas."],
  "ctm_ids": ["Vous devez sélectionner au moins un CTM."],
  "cv": ["Le fichier CV ne doit pas dépasser 5MB."]
}
```

---

## 📱 Flux d'Inscription Complet

```
1. Expert scanne QR Code
         ↓
2. Accès à la page d'inscription web
         ↓
3. Frontend récupère :
   - GET /api/v1/expert-registration/structures/
   - GET /api/v1/expert-registration/ctm/
         ↓
4. Expert remplit le formulaire :
   ✓ Email & Mot de passe
   ✓ Nom & Prénom
   ✓ Numéro de téléphone
   ✓ Structure d'origine (dropdown)
   ✓ Sélectionne 1+ CTM (checkboxes)
   ✓ Upload CV (PDF/DOC)
         ↓
5. Frontend envoie :
   POST /api/v1/expert-registration/public_register/
         ↓
6. Django crée :
   ✓ Utilisateur (User)
   ✓ Profil Expert
   ✓ Associations CTM (M2M)
   ✓ Sauvegarde CV
         ↓
7. Réponse de confirmation
   ✓ Email de validation envoyé
   ✓ Status = PENDING (en attente de validation)
```

---

## 📋 Validations

### Email
- ✅ Format valide
- ✅ Unique en base de données
- ❌ Erreur si doublon

### Mot de passe
- ✅ Minimum 8 caractères
- ✅ Confirmation identique
- ❌ Erreur si différent

### Structure
- ✅ ID doit exister
- ✅ Structure active

### CTM (Sous-Commissions)
- ✅ Au moins 1 CTM requis
- ✅ Chaque ID doit exister
- ✅ IDs doivent être valides

### CV (Fichier)
- ✅ Optionnel
- ✅ Formats acceptés: PDF, DOC, DOCX, TXT
- ✅ Taille max: 5 MB
- ❌ Erreur si format invalide

---

## 🎯 Exemples cURL

### 1. Récupérer les structures
```bash
curl -X GET "http://localhost:8000/api/v1/expert-registration/structures/" \
  -H "Content-Type: application/json"
```

### 2. Récupérer les CTM
```bash
curl -X GET "http://localhost:8000/api/v1/expert-registration/ctm/" \
  -H "Content-Type: application/json"
```

### 3. S'inscrire (sans fichier)
```bash
curl -X POST "http://localhost:8000/api/v1/expert-registration/public_register/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jean.dupont@company.cd",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!",
    "first_name": "Jean",
    "last_name": "Dupont",
    "phone": "+243812345678",
    "structure_id": 1,
    "specialties": "Géotechnique",
    "ctm_ids": [1, 2]
  }'
```

### 4. S'inscrire (avec fichier CV)
```bash
curl -X POST "http://localhost:8000/api/v1/expert-registration/public_register/" \
  -F "email=jean.dupont@company.cd" \
  -F "password=SecurePassword123!" \
  -F "password_confirm=SecurePassword123!" \
  -F "first_name=Jean" \
  -F "last_name=Dupont" \
  -F "phone=+243812345678" \
  -F "structure_id=1" \
  -F "specialties=Géotechnique, Fondations" \
  -F "ctm_ids=1" \
  -F "ctm_ids=2" \
  -F "cv=@/path/to/cv.pdf"
```

---

## 🔐 Sécurité

✅ **Authentification**:
- Endpoint public (`AllowAny`)
- Pas de token requis pour s'inscrire
- Authentification via login après inscription

✅ **Validation des données**:
- Vérification des formats
- Validation des références (structure, CTM)
- Vérification d'unicité (email)

✅ **Fichiers**:
- Upload safe avec validations
- Extensions autorisées uniquement
- Taille limitée

✅ **Statut initial**:
- Experts créés avec status = `PENDING`
- Pas actifs automatiquement
- Attente de validation administrative

---

## 📊 Données stockées

Lors de l'inscription, les données suivantes sont stockées :

**Utilisateur (User)**:
- `email` ✅
- `username` (généré automatiquement)
- `password` (hashé)
- `first_name` ✅
- `last_name` ✅
- `phone` ✅
- `is_expert` = True

**Expert (Expert)**:
- `user` (FK vers User)
- `structure` (FK vers Structure)
- `specialties` (domaines de compétence)
- `cv` (fichier uploadé)
- `status` = "PENDING"
- `inscription_date` (auto)
- `ctm_choices` (M2M vers CTM)

---

## ✅ Checklist Frontend

Lorsque vous implémentez le formulaire d'inscription côté React :

- [ ] Récupérer structures via `/expert-registration/structures/`
- [ ] Récupérer CTM via `/expert-registration/ctm/`
- [ ] Afficher dropdown pour structures
- [ ] Afficher checkboxes pour CTM (multi-select)
- [ ] Champ file upload pour CV
- [ ] Validation email format
- [ ] Validation passwords match
- [ ] Validation au moins 1 CTM sélectionné
- [ ] Upload FormData pour fichier
- [ ] Afficher messages d'erreur du serveur
- [ ] Message de succès après inscription
- [ ] Rediriger vers login après succès

---

## 🚀 Génération QR Code

Générez le QR code pointant vers l'URL d'inscription :

```bash
cd /home/minato/project
source mon_env/bin/activate

# Générer QR code
python manage.py generer_qr_expert --url "http://localhost:8000/inscription-expert/"

# Production
python manage.py generer_qr_expert --url "https://normes.cnetp.cd/inscription-expert/"
```

Le QR code sera généré dans `/media/qrcodes/qr_inscription_expert.png`

---

## 📞 Support

Pour des questions sur l'API :
- Consultez `/api/v1/docs/swagger/` (Swagger UI)
- Voir `/api/v1/schema/` (OpenAPI spec)

---

**Version**: 1.0  
**Date**: 25 mai 2026  
**Statut**: ✅ Production-Ready

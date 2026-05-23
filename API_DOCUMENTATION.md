# 🔐 API REST CNETP - Documentation d'Authentification

## 📍 Base URL

```
http://localhost:8000/api/v1/
```

## 🛣️ Routes Principales d'Authentification

### 1. **Inscription (Register)**
- **Endpoint**: `POST /auth/register/`
- **Authentification**: Non requise
- **Description**: Créer un nouveau compte utilisateur

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jean_dupont",
    "email": "jean@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "Jean",
    "last_name": "Dupont",
    "phone": "+243812345678",
    "province": "Kinshasa"
  }'
```

**Réponse Succès (201)**:
```json
{
  "id": 1,
  "username": "jean_dupont",
  "email": "jean@example.com",
  "first_name": "Jean",
  "last_name": "Dupont",
  "phone": "+243812345678",
  "province": "Kinshasa",
  "is_expert": false,
  "is_ctc_staff": false,
  "is_minister": false,
  "date_joined": "2026-05-19T19:00:00Z"
}
```

**Note importante:** L'endpoint `POST /auth/register/` permet uniquement la création de comptes "simple user" (`is_expert: false`). Les inscriptions d'experts ne sont pas autorisées via cet endpoint. Pour l'inscription d'un expert utilisez `POST /experts/inscription/`.

---

### 2. **Login**
- **Endpoint**: `POST /auth/login/`
- **Authentification**: Non requise
- **Description**: Se connecter et recevoir un token de session

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jean_dupont",
    "password": "SecurePass123!"
  }'
```

**Réponse Succès (200)**:
```json
{
  "id": 1,
  "username": "jean_dupont",
  "email": "jean@example.com",
  "first_name": "Jean",
  "last_name": "Dupont",
  "phone": "+243812345678",
  "province": "Kinshasa",
  "is_expert": true,
  "is_ctc_staff": false,
  "is_minister": false,
  "message": "Connecté avec succès"
}
```

**Erreur (401)**:
```json
{
  "non_field_errors": ["Identifiants invalides"]
}
```

---

### 3. **Profil Utilisateur Actuel**
- **Endpoint**: `GET /auth/me/`
- **Authentification**: **Requise** (Session Cookie)
- **Description**: Récupérer le profil de l'utilisateur connecté

```bash
curl -X GET http://localhost:8000/api/v1/auth/me/ \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_SESSION_ID"
```

**Réponse (200)**:
```json
{
  "id": 1,
  "username": "jean_dupont",
  "email": "jean@example.com",
  "first_name": "Jean",
  "last_name": "Dupont",
  "phone": "+243812345678",
  "province": "Kinshasa",
  "is_expert": true,
  "is_ctc_staff": false,
  "is_minister": false,
  "date_joined": "2026-05-19T19:00:00Z",
  "last_login": "2026-05-19T19:05:00Z"
}
```

---

### 4. **Mettre à Jour le Profil**
- **Endpoint**: `PATCH /auth/profile/`
- **Authentification**: **Requise**
- **Description**: Mettre à jour les informations du profil

```bash
curl -X PATCH http://localhost:8000/api/v1/auth/profile/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_SESSION_ID" \
  -d '{
    "first_name": "Jean",
    "last_name": "Dupont",
    "phone": "+243987654321",
    "province": "Kinshasa"
  }'
```

---

### 5. **Changer le Mot de Passe**
- **Endpoint**: `POST /auth/change-password/`
- **Authentification**: **Requise**
- **Description**: Changer le mot de passe avec l'ancien password

```bash
curl -X POST http://localhost:8000/api/v1/auth/change-password/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_SESSION_ID" \
  -d '{
    "old_password": "SecurePass123!",
    "new_password": "NewSecurePass456!",
    "new_password2": "NewSecurePass456!"
  }'
```

---

### 6. **Logout**
- **Endpoint**: `POST /auth/logout/`
- **Authentification**: **Requise**
- **Description**: Se déconnecter et invalider la session

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout/ \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_SESSION_ID"
```

---

## 👥 Gestion des Experts

### 1. **Inscription d'un Expert (Formulaire Complet)**
- **Endpoint**: `POST /experts/inscription/`
- **Authentification**: Non requise
- **Description**: Formulaire d'inscription complet pour expert + utilisateur

```bash
curl -X POST http://localhost:8000/api/v1/experts/inscription/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "marie_ingenieur",
    "email": "marie@example.com",
    "first_name": "Marie",
    "last_name": "Ingénieur",
    "phone": "+243821234567",
    "province": "Kinshasa",
    "password": "ExpertPass123!",
    "password2": "ExpertPass123!",
    "structure_id": 1,
    "specialties": "Géotechnique, Reconnaissance des sols",
    "appointment_decree_number": "2026/001",
    "appointment_date": "2026-01-15"
  }'
```

---

### 2. **Lister les Experts**
- **Endpoint**: `GET /experts/`
- **Authentification**: **Requise**
- **Description**: Récupérer la liste de tous les experts avec pagination

```bash
curl -X GET "http://localhost:8000/api/v1/experts/?page=1&status=ACTIVE" \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_SESSION_ID"
```

**Filtres disponibles**:
- `status`: PENDING, ACTIVE, INACTIVE
- `structure`: ID ou nom de la structure
- `search`: Recherche par nom, email, username

---

### 3. **Détails d'un Expert**
- **Endpoint**: `GET /experts/{id}/`
- **Authentification**: **Requise**

```bash
curl -X GET http://localhost:8000/api/v1/experts/1/ \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_SESSION_ID"
```

---

### 4. **Mon Profil Expert**
- **Endpoint**: `GET /experts/my_profile/`
- **Authentification**: **Requise**

```bash
curl -X GET http://localhost:8000/api/v1/experts/my_profile/ \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_SESSION_ID"
```

---

### 5. **Activer un Expert (CTC uniquement)**
- **Endpoint**: `POST /experts/{id}/activate/`
- **Authentification**: **Requise** (CTC Staff)

```bash
curl -X POST http://localhost:8000/api/v1/experts/1/activate/ \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_CTC_SESSION_ID"
```

---

## 🏛️ Gouvernance (CTM/WG)

### 1. **Lister les CTM**
- **Endpoint**: `GET /ctm/`
- **Authentification**: **Requise**

```bash
curl -X GET "http://localhost:8000/api/v1/ctm/?ordering=number" \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_SESSION_ID"
```

---

### 2. **Détails d'un CTM avec ses WG et Experts**
- **Endpoint**: `GET /ctm/{id}/`

```bash
curl -X GET http://localhost:8000/api/v1/ctm/1/ \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_SESSION_ID"
```

---

### 3. **Lister les Groupes de Travail (WG)**
- **Endpoint**: `GET /wg/`

```bash
curl -X GET "http://localhost:8000/api/v1/wg/?ctm=1&ordering=number" \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_SESSION_ID"
```

---

### 4. **Affectations (Expert → CTM/WG)**
- **Endpoint**: `GET /affectations/`

```bash
curl -X GET "http://localhost:8000/api/v1/affectations/?expert_id=1" \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_SESSION_ID"
```

**Créer une affectation** (CTC uniquement):
```bash
curl -X POST http://localhost:8000/api/v1/affectations/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_CTC_SESSION_ID" \
  -d '{
    "expert": 1,
    "ctm": 1,
    "wg": 3,
    "role": "MEMBER"
  }'
```

---

## 🏢 Structures

### 1. **Lister les Structures**
- **Endpoint**: `GET /structures/`
- **Authentification**: **Requise**

```bash
curl -X GET "http://localhost:8000/api/v1/structures/?category=ADMINISTRATIVE" \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_SESSION_ID"
```

---

### 2. **Experts d'une Structure**
- **Endpoint**: `GET /structures/{id}/experts/`

```bash
curl -X GET http://localhost:8000/api/v1/structures/1/experts/ \
  -H "Accept: application/json" \
  -b "sessionid=YOUR_SESSION_ID"
```

---

## 🔑 Codes de Statut

| Code | Signification |
|------|--------------|
| 200 | ✅ OK - Succès |
| 201 | ✅ Created - Ressource créée |
| 204 | ✅ No Content - Succès sans contenu |
| 400 | ❌ Bad Request - Données invalides |
| 401 | ❌ Unauthorized - Authentification requise |
| 403 | ❌ Forbidden - Permis­sion insuffisante |
| 404 | ❌ Not Found - Ressource inexistante |
| 500 | ❌ Server Error - Erreur serveur |

---

## 🔒 Sécurité & Authentification

### Session Cookie
La plupart des endpoints utilisent l'authentification par **Session Django**:

1. Après `POST /auth/login/`, vous recevez un `sessionid` cookie
2. Utilisez ce cookie dans toutes les requêtes suivantes:
   ```bash
   curl ... -b "sessionid=xyz123..."
   ```

### Cookies automatiques avec curl
```bash
curl -c cookies.txt -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

curl -b cookies.txt http://localhost:8000/api/v1/auth/me/
```

---

## 📚 Documentation Interactive

Accédez à la documentation Swagger :
```
http://localhost:8000/api/v1/schema/swagger/
```

Ou ReDoc :
```
http://localhost:8000/api/v1/schema/redoc/
```

---

## 🧪 Exemples de Workflow Complet

### Workflow: Inscription + Login + Devenir Expert

```bash
#!/bin/bash

# 1. Créer un nouvel utilisateur
curl -c cookies.txt -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_expert",
    "email": "expert@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "Expert",
    "last_name": "Novice",
    "phone": "+243812345678",
    "province": "Kinshasa"
  }'

# 2. Se connecter
curl -b cookies.txt -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_expert",
    "password": "SecurePass123!"
  }'

# 3. Consulter les structures disponibles
curl -b cookies.txt http://localhost:8000/api/v1/structures/

# 4. Devenir expert (si possible par endpoint dédié)
curl -b cookies.txt -X POST http://localhost:8000/api/v1/experts/inscription/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_expert",
    "email": "expert@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "Expert",
    "last_name": "Novice",
    "phone": "+243812345678",
    "province": "Kinshasa",
    "structure_id": 1,
    "specialties": "Structures et Ouvrages"
  }'

# 5. Consulter mon profil
curl -b cookies.txt http://localhost:8000/api/v1/experts/my_profile/

# 6. Me déconnecter
curl -b cookies.txt -X POST http://localhost:8000/api/v1/auth/logout/
```

---

## 📞 Erreurs Courantes

### "Identifiants invalides"
```json
{"non_field_errors": ["Identifiants invalides"]}
```
→ Vérifier le username/password

### "Informations d'authentification non fournies"
```json
{"detail": "Informations d'authentification non fournies."}
```
→ Ajouter le header `-b "sessionid=..."`

### "Ce nom d'utilisateur existe déjà"
```json
{"username": ["Ce nom d'utilisateur existe déjà."]}
```
→ Choisir un autre username

---

**Documentation mise à jour** : 19 Mai 2026  
**API Version** : v1  
**Environnement** : Développement

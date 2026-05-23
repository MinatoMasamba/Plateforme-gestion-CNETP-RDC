# 🎯 Résumé des Endpoints API CNETP

## 🔐 AUTHENTIFICATION (/auth/)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| POST | `/auth/register/` | ❌ | Créer un nouvel utilisateur |
| POST | `/auth/login/` | ❌ | Se connecter |
| POST | `/auth/logout/` | ✅ | Se déconnecter |
| GET | `/auth/me/` | ✅ | Profil utilisateur actuel |
| PATCH | `/auth/profile/` | ✅ | Mettre à jour le profil |
| POST | `/auth/change-password/` | ✅ | Changer le mot de passe |

---

## 👥 EXPERTS (/experts/)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| POST | `/experts/inscription/` | ❌ | Inscription expert complète |
| GET | `/experts/` | ✅ | Lister tous les experts |
| GET | `/experts/{id}/` | ✅ | Détails d'un expert |
| GET | `/experts/my_profile/` | ✅ | Mon profil expert |
| POST | `/experts/{id}/activate/` | 🔐 | Activer un expert (CTC) |
| POST | `/experts/{id}/deactivate/` | 🔐 | Désactiver un expert (CTC) |
| GET | `/experts/{id}/affectations/` | ✅ | Affectations de l'expert |

---

## 🏢 STRUCTURES (/structures/)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/structures/` | ✅ | Lister toutes les structures |
| GET | `/structures/{id}/` | ✅ | Détails d'une structure |
| GET | `/structures/{id}/experts/` | ✅ | Experts d'une structure |

---

## 🏛️ COMITÉS TECHNIQUES (CTM) (/ctm/)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/ctm/` | ✅ | Lister les CTM |
| GET | `/ctm/{id}/` | ✅ | Détails d'un CTM |
| POST | `/ctm/` | 🔐 | Créer un CTM (CTC) |
| PUT | `/ctm/{id}/` | 🔐 | Mettre à jour un CTM (CTC) |
| DELETE | `/ctm/{id}/` | 🔐 | Supprimer un CTM (CTC) |
| GET | `/ctm/{id}/experts/` | ✅ | Experts du CTM |
| GET | `/ctm/{id}/working_groups/` | ✅ | WG du CTM |
| GET | `/ctm/{id}/roles/` | ✅ | Rôles du CTM |

---

## 👨‍💼 GROUPES DE TRAVAIL (WG) (/wg/)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/wg/` | ✅ | Lister les WG |
| GET | `/wg/{id}/` | ✅ | Détails d'un WG |
| POST | `/wg/` | 🔐 | Créer un WG (CTC) |
| PUT | `/wg/{id}/` | 🔐 | Mettre à jour un WG (CTC) |
| DELETE | `/wg/{id}/` | 🔐 | Supprimer un WG (CTC) |
| GET | `/wg/{id}/experts/` | ✅ | Experts du WG |

---

## 🔗 AFFECTATIONS (Expert → CTM/WG) (/affectations/)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/affectations/` | ✅ | Lister les affectations |
| POST | `/affectations/` | 🔐 | Créer une affectation (CTC) |
| GET | `/affectations/{id}/` | ✅ | Détails affectation |
| PUT | `/affectations/{id}/` | 🔐 | Mettre à jour (CTC) |
| DELETE | `/affectations/{id}/` | 🔐 | Supprimer (CTC) |
| GET | `/affectations/by_expert/` | ✅ | Affectations d'un expert |
| GET | `/affectations/by_ctm/` | ✅ | Affectations d'un CTM |
| GET | `/affectations/by_wg/` | ✅ | Affectations d'un WG |
| POST | `/affectations/bulk_create/` | 🔐 | Créer en masse (CTC) |

---

## 👔 RÔLES CTM (/roles-ctm/)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/roles-ctm/` | ✅ | Lister les rôles CTM |
| POST | `/roles-ctm/` | 🔐 | Attribuer un rôle (CTC) |
| GET | `/roles-ctm/{id}/` | ✅ | Détails du rôle |
| PUT | `/roles-ctm/{id}/` | 🔐 | Mettre à jour le rôle (CTC) |

---

## 🤝 COMITÉ DE PILOTAGE (/comite-pilotage/)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/comite-pilotage/` | ✅ | Lister les membres |
| POST | `/comite-pilotage/` | 🔐 | Ajouter un membre (CTC) |
| GET | `/comite-pilotage/active_members/` | ✅ | Membres actifs |

---

## 👤 UTILISATEURS (/users/)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/users/` | ✅ | Lister les utilisateurs |
| GET | `/users/{id}/` | ✅ | Détails d'un utilisateur |

---

## 📊 FILTRES DISPONIBLES

### Experts
```
?status=ACTIVE&structure=1&search=jean
```

### CTM
```
?number=1&name=Géotechnique
```

### Affectations
```
?expert_id=1&ctm_id=1&wg_id=3&role=PRESIDENT
```

---

## 🔐 Authentification

- ✅ = Endpoint public (connecté)
- ❌ = Endpoint public (anonyme)
- 🔐 = Endpoint restreint (CTC/Ministre)

**Authentification**: Session Cookie (par défaut)

```bash
# Login
curl -c cookies.txt -X POST http://localhost:8000/api/v1/auth/login/ ...

# Utiliser le cookie
curl -b cookies.txt http://localhost:8000/api/v1/experts/ ...
```

---

## 📚 Documentation Interactive

- **Swagger UI** : http://localhost:8000/api/v1/schema/swagger/
- **ReDoc** : http://localhost:8000/api/v1/schema/redoc/
- **OpenAPI Schema** : http://localhost:8000/api/v1/schema/

---

## ⚡ Cas d'Usage Rapides

### 1️⃣ M'inscrire et me connecter
```bash
POST /auth/register/ → POST /auth/login/ → GET /auth/me/
```

### 2️⃣ Devenir expert
```bash
POST /experts/inscription/ → (attendre validation CTC) → GET /experts/my_profile/
```

### 3️⃣ Consulter les CTM/WG
```bash
GET /ctm/ → GET /ctm/{id}/working_groups/ → GET /wg/{id}/experts/
```

### 4️⃣ Voir mon affectation
```bash
GET /experts/my_profile/ → GET /experts/{id}/affectations/
```

### 5️⃣ Gérer les experts (CTC)
```bash
GET /experts/?status=PENDING → POST /experts/{id}/activate/
```

---

**Mis à jour** : 19 Mai 2026  
**Version API** : v1  
**Statut** : 🟢 Actif

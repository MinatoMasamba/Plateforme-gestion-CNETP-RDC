# 🚀 Guide de Démarrage - Plateforme CNETP

## ✅ Problème Résolu: Écran Blanc

L'écran blanc du React a été causé par **deux problèmes majeurs**:

### 1️⃣ **Routes API Incompatibles**
- ❌ React appelait `/api/documents` et `/api/collaborators`
- ✅ Django expose l'API sur `/api/v1/documents` et `/api/v1/collaborators`
- **Solution**: Configuration Vite proxy + API bridge

### 2️⃣ **Serveurs Non Lancés**
- ✅ Maintenant les deux serveurs sont prêts

---

## 🎯 Démarrage Rapide

### Option 1: Démarrage Manuel (Recommandé)

**Terminal 1 - Backend Django:**
```bash
cd /home/minato/project
source mon_env/bin/activate
python3 manage.py runserver 127.0.0.1:8000
```

**Terminal 2 - Frontend React/Vite:**
```bash
cd /home/minato/project/frontend
npm run dev
```

**Accès:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Documentation API: http://localhost:8000/api/v1/schema/swagger/

---

### Option 2: Script Automatisé
```bash
cd /home/minato/project
bash run_dev.sh
```

---

## 🔌 Endpoints API Configurés

### Collaborateurs (Experts)
```bash
curl http://127.0.0.1:8000/api/v1/collaborators/
```
**Réponse:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "name": "Expert1 CNETP",
      "email": "expert1@cnetp.cd",
      "role": "active",
      "isActive": true
    }
  ]
}
```

### Documents
```bash
curl http://127.0.0.1:8000/api/v1/documents/
```

---

## 🔐 Identifiants de Test

**Admin User:**
- Username: `admin`
- Password: `admin123`
- Email: `admin@test.com`

---

## 📋 Configuration Appliquée

### ✅ Fichiers Modifiés

1. **`frontend/vite.config.ts`**
   - Ajout proxy pour rediriger `/api/*` vers Django

2. **`config/settings.py`**
   - Ajout port 5173 à `CORS_ALLOWED_ORIGINS`

3. **`api/v1/api_bridge_views.py`** (NEW)
   - API bridge pour mapper `/api/` vers `/api/v1/`

4. **`api/v1/urls.py`**
   - Routes pour `DocumentsAPIView` et `CollaboratorsAPIView`

---

## 🧪 Test de Vérification

```bash
# Vérifier Django (en cours d'exécution)
curl -s http://127.0.0.1:8000/api/v1/collaborators/ | python3 -m json.tool

# Vérifier Vite Frontend (en cours d'exécution)
curl -s http://127.0.0.1:5173/ | head -c 100
```

---

## 🐛 Dépannage

### "Port already in use"
```bash
ps aux | grep "python.*runserver"
kill <PID>
```

### Erreur CORS
- Vérifier que port 5173 est dans `CORS_ALLOWED_ORIGINS`
- Relancer Django après modification

### API retourne 500
- Vérifier les logs Django en console
- Vérifier les modèles utilisés

---

## 📚 Architecture

```
localhost:5173 (Vite Dev Server)
    ↓ proxy /api/* 
    ↓ 
localhost:8000 (Django)
    ↓ URL routing
    ↓
/api/v1/collaborators/
/api/v1/documents/
```

---

**Dernière mise à jour:** 2026-05-25

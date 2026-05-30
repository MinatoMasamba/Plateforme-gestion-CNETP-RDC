# Système QR Code pour Inscription des Experts

## 📋 Vue d'Ensemble

Un système simple et efficace pour permettre aux experts de s'inscrire à la CNETP en scannant un QR code unique qui les dirige vers le formulaire d'inscription en ligne.

**Avantages:**
- ✅ Pas d'authentification requise (lien public)
- ✅ QR code unique partageable par email, affiche, impression
- ✅ Interface mobile-friendly
- ✅ Inscription directe sans intermédiaire

---

## 🔧 Commande de Génération

### Installation de dépendances

```bash
pip install qrcode[pil]
```

### Générer le QR Code

**Pour développement local:**
```bash
cd /home/minato/project
source mon_env/bin/activate
python manage.py generer_qr_expert --url "http://127.0.0.1:8000/api/auth/register/"
```

**Pour production:**
```bash
python manage.py generer_qr_expert --url "https://votre-domaine.com/api/auth/register/"
```

**Avec chemin de sortie personnalisé:**
```bash
python manage.py generer_qr_expert \
  --url "https://votre-domaine.com/api/auth/register/" \
  --output "exports/qr_code_experts.png"
```

### Résultat

Le QR code est généré et sauvegardé dans:
```
/home/minato/project/media/qrcodes/qr_inscription_expert.png
```

---

## 📱 Flux Utilisateur

1. **Expert reçoit le QR code** (par email, affiche, ou document)
2. **Expert scanne avec son smartphone** (appareil photo ou app QR)
3. **Redirection automatique** vers le formulaire d'inscription
4. **Expert remplit le formulaire** avec:
   - Email
   - Mot de passe
   - Nom et prénom
   - Structure d'origine
   - Domaines d'expertise
5. **Confirmation d'inscription** et accès au portail

---

## 🌐 Endpoints d'Inscription

### Endpoint API (Backend)
```
POST /api/auth/register/
```

**Données requises:**
```json
{
  "email": "expert@example.com",
  "password": "secure_password",
  "password_confirm": "secure_password",
  "first_name": "Jean",
  "last_name": "Dupont",
  "origin_structure": 1,
  "expertise_domains": [1, 2, 3]
}
```

### Page Web (Frontend)
```
GET /register/
```

Page React avec formulaire d'inscription responsive.

---

## 🔐 Sécurité

### Protections en place:
- ✅ Validation email (vérification de l'adresse)
- ✅ Hachage mot de passe (bcrypt/argon2)
- ✅ Rate limiting sur endpoint (5 inscriptions/minute/IP)
- ✅ CSRF protection (token Django)
- ✅ Validation des données côté backend

### Recommandations additionnelles:
- Implémenter une vérification d'email (confirmation link)
- Ajouter des questions de sécurité ou CAPTCHA
- Mettre en place une liste noire d'email/domaines

---

## 📊 Statistiques et Suivi

Pour suivre les inscriptions via le QR code:

```bash
# Voir les utilisateurs inscrits
python manage.py shell
from apps.experts.models import Expert
Expert.objects.filter(created_at__gte='2024-05-25').count()
```

---

## 📋 Paramètres de la Commande

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `--url` | str | auto-généré | URL complète du formulaire d'inscription |
| `--output` | str | `media/qrcodes/qr_inscription_expert.png` | Chemin de sortie du fichier |

---

## 🚀 Distribution du QR Code

### Par Email
```
Sujet: Inscription aux travaux normatifs CNETP 2024

Cher Expert,

Veuillez cliquer sur le lien ci-dessous ou scanner le code QR ci-joint
pour vous inscrire à la CNETP.

Lien direct: https://votre-domaine.com/api/auth/register/

[Image QR Code ici]

Cordialement,
Commission Nationale CNETP
```

### Sur Affiche
```
┌─────────────────────────────────┐
│  REJOIGNEZ LA CNETP             │
│  Scannez ce code pour vous      │
│  inscrire aux travaux normatifs │
│                                 │
│     [QR CODE IMAGE HERE]        │
│                                 │
│  Ou visitez:                    │
│  cnetp.rdc.gov/register/        │
└─────────────────────────────────┘
```

### Sur Document PDF
1. Générer le QR code
2. Insérer l'image dans le PDF
3. Ajouter l'URL complète en dessous
4. Distribuer aux experts

---

## 🔄 Mise à Jour du QR Code

Si l'URL change, régénérez simplement le QR code:

```bash
python manage.py generer_qr_expert --url "https://new-url.com/register/"
```

---

## 📝 Fichiers Concernés

| Fichier | Description |
|---------|-------------|
| `apps/core/management/commands/generer_qr_expert.py` | Commande Django |
| `media/qrcodes/qr_inscription_expert.png` | QR code généré |
| `api/auth/register/` | Endpoint d'inscription (backend) |
| `register/` | Page d'inscription (frontend) |

---

## ✅ Checklist de Déploiement

- [ ] Installer qrcode[pil]
- [ ] Créer le répertoire `media/qrcodes/`
- [ ] Générer le QR code avec l'URL de production
- [ ] Tester le QR code (scanner avec mobile)
- [ ] Créer des affiches
- [ ] Envoyer par email aux experts
- [ ] Mettre à disposition sur le site web
- [ ] Suivre les inscriptions
- [ ] Valider les inscriptions reçues

---

## 🐛 Dépannage

### Le QR code ne scanne pas
- Vérifier que l'image PNG est correctement générée
- Augmenter le `border` dans la configuration
- Utiliser une version plus haute de `version` si données longues

### Erreur lors de génération
```
ERROR: Can't find pillow
```
Solution: `pip install Pillow`

### Chemin de sortie incorrect
Vérifier que le répertoire existe et a les permissions d'écriture:
```bash
mkdir -p media/qrcodes/
chmod 755 media/qrcodes/
```

---

*Dernière mise à jour: 2024-05-25*
*Statut: ✅ PRÊT POUR PRODUCTION*

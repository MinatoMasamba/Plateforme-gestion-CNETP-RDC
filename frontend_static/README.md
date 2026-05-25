# CNETP - Frontend Statique (HTML/CSS/JS/Tailwind)

## Vue d'ensemble

Cette version statique de l'application CNETP a été convertie à partir de React vers une version HTML/CSS/JavaScript/Tailwind pure, tout en conservant l'intégration complète avec l'API Django backend.

### Architecture

```
frontend_static/
├── index.html              # Point d'entrée principal
├── css/
│   └── styles.css         # Styles personnalisés
└── js/
    ├── api.js             # Wrapper API pour communication avec Django
    ├── app.js             # Logique applicative et gestion d'état
    └── components/
        ├── messaging.js   # Widget de messagerie
        ├── history.js     # Module Historique des versions
        ├── experts.js     # Module Experts & Groupes
        ├── meetings.js    # Module Réunions & Votes
        ├── financial.js   # Module Cotisations & Indemnités
        ├── validation.js  # Module Bibliothèque Publique
        └── legistique.js  # Module Bureau Légistique
```

## Modules Disponibles

### 1. **Éditeur de Normes**
- Affichage des documents
- Modification du contenu
- Sauvegarde des versions avec commentaires
- Intégration API: `/api/documents`, `/api/documents/{id}/versions`

### 2. **Historique des Versions**
- Consultation de l'historique des versions
- Restauration à une version antérieure
- Affichage des métadonnées (auteur, date, commentaire)
- Intégration API: `/api/documents/{id}/versions`, `/api/documents/{id}/rollback`

### 3. **Experts & Groupes de Travail**
- Liste des groupes de travail (WG)
- Annuaire des experts CNETP
- Chat avec les experts via widget de messagerie
- Intégration API: `/api/experts`, `/api/working-groups`

### 4. **Réunions & Votes**
- Calendrier des réunions à venir
- Votes en cours avec options (Pour/Contre/Abstention)
- Statuts et dates limites
- Intégration API: `/api/meetings`, `/api/votes`

### 5. **Cotisations & Indemnités**
- Suivi des cotisations membres
- Détails des indemnités versées
- Statuts de paiement
- Intégration API: `/api/contributions`, `/api/allowances`

### 6. **Bibliothèque Publique**
- Normes publiées
- Consultation des documents
- Statuts de publication
- Intégration API: `/api/public-norms`

### 7. **Bureau Légistique**
- Dossiers en traitement
- Statuts des analyses juridiques
- Historique des décisions
- Intégration API: `/api/legistique-files`

### 8. **Widget de Messagerie**
- Chat sécurisé en temps réel
- Discussions par expert
- Notifications
- Accessible depuis le bouton flottant en bas-droite

## Installation

### Prérequis
- Un serveur web (Apache, Nginx, etc.)
- Python/Django backend fonctionnant avec les APIs configurées

### Étapes de déploiement

#### Option 1 : Copie directe
```bash
# Copier le dossier frontend_static vers votre serveur
cp -r frontend_static /var/www/html/cnetp
```

#### Option 2 : Avec Docker
```bash
docker run -d -p 80:80 -v /path/to/frontend_static:/usr/share/nginx/html nginx:latest
```

#### Option 3 : Intégration Django (servir depuis les statics)
```bash
# Dans votre settings.py Django
STATIC_URL = '/static/'
STATIC_ROOT = '/path/to/frontend_static'

# Puis collectez les statics
python manage.py collectstatic
```

## Configuration des APIs

Les APIs pointent par défaut vers le même domaine (chemins relatifs). Pour modifier les URLs :

Éditez `js/api.js` et modifiez la variable `baseUrl` :

```javascript
const API = {
    baseUrl: 'https://api.votredomaine.com', // ou '' pour relatif
    // ...
}
```

## Utilisation

1. Ouvrez `index.html` dans un navigateur (ou accédez via votre serveur web)
2. L'application charge automatiquement les documents et données depuis l'API
3. Naviguez entre les modules via les onglets en haut
4. Cliquez sur les documents dans la barre latérale pour les éditer
5. Utilisez le widget de messagerie (bouton bleu en bas-droite) pour communiquer

## État Global (Gestion d'État)

L'application utilise un objet `state` global pour gérer l'état, remplaçant les `useState` de React :

```javascript
const state = {
    isLoading: boolean,
    isDarkMode: boolean,
    activeTab: string,
    selectedDocId: string,
    documents: Array,
    collaborators: Array,
    experts: Array,
    workingGroups: Array,
    activeCollaborator: Object,
    userProfile: Object
};
```

## Rendu Réactif

Chaque interaction déclenche un rendu des composants affectés :

```javascript
// Exemple : changement d'onglet
window.setActiveTab = (tabId) => {
    state.activeTab = tabId;     // Mise à jour état
    renderTabs();               // Re-render des onglets
    renderViewport();           // Re-render du contenu
};
```

## Appels API

Tous les appels API sont encapsulés dans `js/api.js` :

```javascript
// Exemple : récupérer des documents
const docs = await API.fetchDocs();

// Exemple : sauvegarder une version
const result = await API.saveVersion(docId, {
    content: 'nouveau contenu',
    author: 'Nom Auteur',
    email: 'email@example.com',
    comment: 'Mise à jour importante'
});
```

## Dépendances

- **Tailwind CSS** : Livré via CDN (https://cdn.tailwindcss.com)
- **Lucide Icons** : Livré via CDN (https://unpkg.com/lucide@latest)
- **Aucune dépendance npm requise**

## Personnalisation

### Ajouter un nouveau module

1. Créez `js/components/monmodule.js` :
```javascript
const MonModule = {
    render(container) {
        container.innerHTML = `<div>Contenu du module</div>`;
        initLucide();
    }
};
```

2. Ajoutez à `index.html` :
```html
<script src="js/components/monmodule.js"></script>
```

3. Ajoutez à la liste des tabs dans `app.js` :
```javascript
{ id: 'monmodule', label: 'Mon Module', icon: 'icon-name' }
```

4. Gérez dans le switch `renderViewport()` :
```javascript
case 'monmodule':
    MonModule.render(container);
    break;
```

### Modifier les couleurs

Éditez la config Tailwind dans `index.html` :

```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                custom: {
                    primary: '#your-color',
                    secondary: '#your-color'
                }
            }
        }
    }
};
```

## Déploiement sur Serveur

### Apache
```apache
<VirtualHost *:80>
    ServerName cnetp.votredomaine.com
    DocumentRoot /var/www/html/frontend_static
    
    <Directory /var/www/html/frontend_static>
        AllowOverride All
        Require all granted
    </Directory>
    
    # Redirection vers index.html pour SPA
    <IfModule mod_rewrite.c>
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /index.html [L]
    </IfModule>
</VirtualHost>
```

### Nginx
```nginx
server {
    listen 80;
    server_name cnetp.votredomaine.com;
    
    root /usr/share/nginx/html/frontend_static;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Dépannage

### Les API ne répondent pas
- Vérifiez les CORS dans votre backend Django
- Assurez-vous que le backend est accessible depuis le frontend
- Vérifiez que `baseUrl` dans `api.js` est correct

### Les icônes n'apparaissent pas
- Vérifiez que Lucide CDN est chargé
- Ouvrez la console (F12) pour les erreurs

### Le thème n'est pas appliqué
- Rafraîchissez la page (Ctrl+F5)
- Vérifiez que Tailwind CDN est accessible

## Performance

- **Pas de build nécessaire** : Servez directement les fichiers
- **CDN pour dépendances** : Tailwind et Lucide depuis CDN
- **State management minimaliste** : Objet JS pur, aucune overhead
- **Rendu efficace** : Mise à jour du DOM ciblée

## Sécurité

- Les APIs doivent être derrière HTTPS en production
- Configurez les CORS correctement
- Validez/échappez les données côté serveur
- Utilisez des tokens JWT pour l'authentification

## Support et Maintenance

Pour toute question ou issue :
1. Consultez la documentation du backend Django
2. Vérifiez la console du navigateur (F12) pour les erreurs
3. Testez les endpoints API directement avec curl/Postman

## Licence

© 2026 CNETP RDC - Tous droits réservés

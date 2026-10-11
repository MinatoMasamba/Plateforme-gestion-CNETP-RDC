# App de génération de brouillons IA (DeepSeek)

> Note : le dossier conserve l'ancien nom interne `gemini_drafts` (label Django,
> table `gemini_drafts`) pour ne pas casser les migrations et les données
> existantes. Le moteur IA a été migré vers **DeepSeek**.

## Installation / démarrage rapide

1. Ajouter `apps.gemini_drafts` à `INSTALLED_APPS` dans `settings.py`.
2. Configurer les variables DeepSeek dans vos settings (ou votre `.env`) :

```py
# settings.py
DEEPSEEK_API_KEY = 'your_api_key'
DEEPSEEK_MODEL = 'deepseek-chat'          # ou 'deepseek-reasoner'
DEEPSEEK_BASE_URL = 'https://api.deepseek.com'
DEEPSEEK_MAX_TOKENS = 8192
```

3. Faire les migrations :

```bash
python manage.py migrate
```

4. Inclure les URLs dans votre `urls.py` principal :

```py
from django.urls import path, include

urlpatterns = [
    # ...
    path('drafts/', include('apps.gemini_drafts.urls')),
]
```

5. Requête d'exemple :

```bash
curl -X POST http://localhost:8000/drafts/generate/ \
  -H "Content-Type: application/json" \
  -d '{"domain":"energie","type":"guide","content":"...","data":{}}'
```

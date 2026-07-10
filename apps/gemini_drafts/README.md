# gemini_drafts Django app

Installation and quick start:

1. Copier ce dossier dans votre projet Django (par exemple `apps/gemini_drafts`).
2. Ajouter `gemini_drafts` à `INSTALLED_APPS` dans `settings.py`.
3. Configurer les variables dans vos settings Django:

```py
# settings.py
GEMINI_API_URL = 'https://api.example.com/v1/generate'
GEMINI_API_KEY = 'your_api_key'
```

4. Faire les migrations:

```bash
python manage.py makemigrations gemini_drafts
python manage.py migrate
```

5. Inclure les URLs dans votre `urls.py` principal:

```py
from django.urls import path, include

urlpatterns = [
    # ...
    path('gemini/', include('apps.gemini_drafts.urls')),
]
```

6. Requête d'exemple:

```bash
curl -X POST http://localhost:8000/gemini/generate/ \
  -H "Content-Type: application/json" \
  -d '{"ctm":"CTM-Ex","wg":"WG1","domain":"energie","type":"guide","data":{"context":"..."}}'
```

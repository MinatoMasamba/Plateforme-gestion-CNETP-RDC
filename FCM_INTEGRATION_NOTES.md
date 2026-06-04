Intégration FCM (Firebase Cloud Messaging) — Notes d'implémentation

1. Installer la dépendance : `firebase-admin` (ajoutée à requirements.txt)

2. Fournir les credentials :
   - Soit via fichier JSON `GOOGLE_APPLICATION_CREDENTIALS`/`FIREBASE_CREDENTIALS_PATH` dans l'environnement
   - Soit en plaçant le JSON dans la variable d'environnement `FIREBASE_CREDENTIALS_JSON` (stringified)

3. Utilisation dans la tâche : `apps/mobileapp/tasks.dispatch_notification` utilise `firebase_admin.messaging.send` pour chaque token.

4. Bonnes pratiques :
   - Utiliser le token `token.token` stocké dans PushToken.model
   - Gérer les erreurs et mettre à jour NotificationLog (FAILED/BOUNCED)
   - Implémenter retries et backoff côté Celery (task annotations) si nécessaire

5. Tests :
   - Mock firebase_admin.messaging.send dans les tests
   - Vérifier création de NotificationLog et statuts

6. Remarques :
   - APNs (iOS) peut être géré via Firebase pour simplifier; sinon utiliser `apns2` ou d'autres libs.
   - `docker-compose.yml` doit exposer credentials au container celery (mount file ou变量)

# Plan Flutter CNETP — Application et Secretariat technique

## Constat

Le projet ne contient pas encore d'application Flutter. Le dossier `mobile/` correspond a Django. L'interface `/app` actuelle est une interface web/PWA compilee, et le Secretariat technique est actuellement servi par des templates Django.

L'objectif est de construire une application Flutter unique avec deux espaces :

- l'application generale CNETP ;
- le Secretariat technique / CTC.

## 1. Stabiliser le backend mobile

Flutter doit consommer des endpoints JSON dedies, et non les pages HTML Django.

Endpoints a ajouter ou normaliser :

- `GET /api/v1/mobile/app/bootstrap/`
- `GET /api/v1/mobile/dashboard/`
- `GET /api/v1/mobile/norms/`
- `GET /api/v1/mobile/tasks/`
- `GET /api/v1/mobile/ctc/dashboard/`
- `GET /api/v1/mobile/ctc/dossiers/`
- `GET /api/v1/mobile/ctc/dossiers/{id}/`
- `POST /api/v1/mobile/ctc/dossiers/{id}/reception/`
- `POST /api/v1/mobile/ctc/dossiers/{id}/indexation/`
- `POST /api/v1/mobile/ctc/dossiers/{id}/validation-entree/`
- `POST /api/v1/mobile/ctc/reviews/{id}/decision/`
- `POST /api/v1/mobile/ctc/industriel/{id}/decision/`
- `POST /api/v1/mobile/ctc/dossiers/{id}/transmettre-pilotage/`

Chaque action doit etre controlee cote serveur selon le role CTC et retourner l'etat actuel du dossier.

```json
{
  "ok": true,
  "status": "APPROVED",
  "current_stage": "INDUSTRIAL",
  "message": "Action enregistree",
  "updated_at": "..."
}
```

## 2. Creer le projet Flutter

Structure recommandee :

```text
flutter_app/
  lib/
    core/
      api/
      auth/
      theme/
      routing/
      storage/
      notifications/
    features/
      auth/
      dashboard/
      norms/
      experts/
      meetings/
      messaging/
      notifications/
      profile/
      secretariat_ctc/
        dashboard/
        dossiers/
        reviews/
        industrial/
        transmission/
```

Technologies recommandees :

- Flutter ;
- `Dio` pour les appels API ;
- `Riverpod` pour l'etat ;
- `go_router` pour la navigation ;
- `freezed` et `json_serializable` pour les modeles ;
- `flutter_secure_storage` pour les tokens ;
- Firebase Cloud Messaging pour les notifications ;
- `file_picker` pour les documents.

## 3. Authentification

Implementer :

- connexion utilisateur et expert ;
- activation expert par token ;
- confirmation email ;
- JWT access/refresh ;
- renouvellement automatique du token ;
- deconnexion et fermeture de session ;
- enregistrement du `device_id` ;
- redirection selon `user_type` et les roles CTC.

## 4. Application generale

Construire les ecrans suivants :

1. Connexion et inscription.
2. Tableau de bord.
3. Liste et detail des normes.
4. Historique des versions.
5. Taches personnelles.
6. Notifications.
7. Profil et preferences.
8. Reunions et votes.
9. Messagerie.
10. Bibliotheque publique.

Le theme sombre et clair doit utiliser les memes tokens visuels que l'interface web.

## 5. Secretariat technique / CTC

Ordre de construction :

1. Tableau de bord CTC adapte au role.
2. File des dossiers.
3. Detail du dossier avec timeline.
4. Reception et indexation.
5. Validation d'entree.
6. File des examens assignes.
7. Formulaire d'acceptation ou de refus.
8. Consultation industrielle FEC.
9. Transmission au Pilotage.
10. Historique des decisions et notifications.

Un dossier ne doit avancer que si le serveur confirme l'etape precedente.

## 6. Notifications

Flutter doit gerer :

- notification en premier plan et en arriere-plan ;
- ouverture vers le dossier concerne ;
- marquage comme lu ;
- compteur non lu ;
- preferences par categorie ;
- fallback vers les notifications in-app si le push est indisponible.

Le backend contient deja une base de notifications, des preferences, des tokens push et des taches email/push a stabiliser.

## 7. Tests

Scenarios obligatoires :

- inscription publique et confirmation email ;
- activation expert ;
- connexion et renouvellement JWT ;
- reception complete d'un dossier CTC ;
- acceptation d'un examen ;
- refus avec commentaire ;
- blocage si une validation manque ;
- transmission au Pilotage ;
- accuse de reception President/Rapporteur ;
- notification in-app et push ;
- lecture hors connexion.

## 8. Ordre de livraison

1. Stabiliser les APIs Flutter et les permissions.
2. Corriger les fixtures de tests Django existantes.
3. Creer le socle Flutter.
4. Livrer Auth, Dashboard et Notifications.
5. Livrer Normes et Taches.
6. Livrer le Secretariat CTC.
7. Ajouter Reunions, Messagerie et Paiements.
8. Executer une recette complete sur un dossier reel de bout en bout.

## Point bloquant actuel

La logique CTC existe cote serveur web, mais Flutter ne doit pas dependre des routes HTML `/ctc/...`. La prochaine etape technique est donc de creer les endpoints mobiles CTC, leurs serializers, leurs permissions et leurs tests avant de commencer les ecrans Flutter.

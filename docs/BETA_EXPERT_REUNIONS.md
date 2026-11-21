# Bêta Expert — réunions

## Livraison du 18 novembre 2026

Flutter présente les réunions accessibles avec les filtres « Cette semaine »,
« Aujourd’hui » et « Toutes ». Les horaires sont convertis dans le fuseau de
l’appareil. Le lien externe est enregistré sur la réunion serveur en mode
EXTERNE ; il reste ouvert dans l’application de visioconférence ou le navigateur.
Les réunions annulées ou terminées ne proposent plus de bouton de connexion.

L’export privé `/api/v1/reunions/{id}/calendrier/` produit un fichier ICS avec
alarmes J-1 et H-1. Leur exécution dépend de l’agenda dans lequel l’expert importe
le fichier ; ce ne sont pas des notifications push CNE-ITP. Après un changement
d’horaire, télécharger et importer la nouvelle invitation.

L’expert invité peut signaler son absence via `excuser/`, puis émarger via
`checkin_presence/` à partir de quinze minutes avant l’horaire. Un clic sur un
lien Meet ne constitue pas une preuve de présence effective dans Meet.

La lecture des réunions, présences, votes et PV est limitée côté API aux invités
et gestionnaires autorisés. Le vote exige une invitation et une présence ; une
réunion annulée ou terminée refuse le vote. Les historiques sont conservés.

## Actions selon les droits

Flutter utilise les capacités renvoyées par le serveur, sans déduire un droit
de gestion du simple rôle Expert ou d'une adhésion à la SC.

- Invité : rejoindre la visioconférence, consulter les documents, signaler son
  absence, émarger à l'ouverture, voter après émargement et consulter le PV.
- Gestionnaire autorisé : préparer la séance, renseigner le lien Meet, les
  documents et la question du vote, gérer les présences, clôturer et rédiger le PV.
- Validateur autorisé : valider un PV complété après clôture. La validation
  verrouille le brouillon ; elle ne découle pas de la création de la réunion.

Les actions non autorisées sont masquées. L'API refuse également les appels
directs. Les révisions protègent la préparation et le PV contre les écrasements
concurrents ; la question ne change plus après un vote.

## Compléments implémentés

- Notifications d'invitation créées lors de l'ajout d'un participant explicite,
  puis alertes pour changement d'horaire, lien, documents ou ordre du jour et
  annulation. Pas d'alerte supplémentaire lors d'une sauvegarde inchangée.
  L'expédition attend la validation de la transaction et revérifie l'invitation,
  l'horaire et l'état de la séance. Une notification historique reste consultable.
- Filtre « Réunions » dans les notifications Flutter. L'ouverture marque l'alerte
  comme lue et affiche la séance concernée. Le compteur se rafraîchit chaque
  minute lorsque l'application est visible, et à son retour au premier plan.
- Rappels serveur J-1/H-1 recalculés chaque minute, dédupliqués par invitation,
  horaire et échéance ; les réunions annulées/reportées et les personnes excusées
  sont exclues. Le dispatcher vérifie à nouveau l’invitation et l’horaire.
- Ressources personnelles synchronisées par compte et norme, avec révision et
  réponse 409 en cas de conflit. Les liens locaux existants restent récupérables.
- Routes mobiles Expert dédiées pour les réunions, ressources et activité.
- Création de projet reliée à l’API existante ; compteur d’activité Flutter relié
  au service de battements avec visibilité et interaction observées.
- Notifications de réunion reliées à la séance sélectionnée dans Flutter.
- Finances filtrées côté serveur : structure du compte et indemnités personnelles.
- Espaces Flutter CTC/Pilotage bloqués, y compris par lien direct ; les interfaces
  Django ne sont pas désactivées.
- Faux collaborateur et faux poste de rapporteur retirés de la barre latérale.

## Activation et dépendances externes

Appliquer les migrations `norms.0014_expertresource` et
`meetings.0007_meetingreminder` et
`meetings.0008_processusverbaux_revision_reunion_document_links_and_more`
et `mobileapp.0005_meeting_change_notifications` sur le serveur cible. Les données existantes
ne sont pas réécrites. La recette utilise uniquement la base isolée `/tmp`.

Les rappels automatiques nécessitent Celery Worker et Beat avec le broker
configuré. Sans ordonnanceur actif, la présence du code ne produit pas de rappel.
La livraison push effective exige les identifiants Firebase et les jetons des
appareils ; les emails dépendent du serveur SMTP et des préférences du compte.
Ces services externes ne sont pas validés par les tests sans réseau.

## Restant avant ouverture générale

- Recette visuelle des autres onglets et des formulaires de gestion. La liste
  Réunions et la participation d'un invité ont été capturées sur 1440 et 390 px
  le 20 novembre, avec thèmes clair/sombre pour la liste. Les captures corrigées
  sont dans `reports/expert_beta/reunions_corrige_*`.
- Recette avec comptes réels et invitations explicitement vérifiées.
- Activation et test de livraison des notifications sur le serveur cible.
- Installation et parcours réels sur un appareil Android après compilation de
  la cible Android ajoutée. La version Windows est reportée à la demande de
  l'utilisateur.

## Distribution directe et journal Android

L'ajout des fichiers utilise l'App Store existant de Django, sans nouvelle page
de téléchargement. `/admin/appstore/appreleasefile/` calcule taille et empreinte
SHA-256 lors d'un upload et expose le lien direct
`/app-store/telecharger/<id>/`. L'expert doit être connecté et autorisé à la bêta.

Le serveur peut importer un APK Flutter réel avec
`manage.py import_expert_builds --release-version <version> --apk <fichier> --tester <courriel> --publish`.
`--all-active-experts` ouvre explicitement la bêta aux comptes experts actifs.
Un fichier publié n'est pas écrasé ; une mise à jour reçoit un nouveau numéro.
`APPSTORE_PACKAGES_ROOT` permet de choisir un stockage privé, par exemple un
sous-dossier de `external_redaction/releases/`, sans servir ce dossier par Nginx.

Flutter transmet les erreurs techniques et requêtes lentes via l'endpoint JWT
`POST /api/v1/mobile/diagnostics/`. Aucun en-tête, corps de requête ou paramètre
URL n'est journalisé. Les mots de passe, jetons et courriels sont masqués.
La file mémoire est limitée à 20 événements ; l'échec du journal ne crée pas
de boucle réseau. Le serveur limite chaque compte à 20 événements/minute et
100/jour. Le journal privé est `.client_diagnostics/flutter_errors.txt`
(`CLIENT_DIAGNOSTICS_DIR` configurable), avec rotation à 5 Mo et quatre archives.
Les incidents sont consultables dans `/admin/mobileapp/clientdiagnostic/`.
Appliquer `mobileapp.0006_client_diagnostic` avant de distribuer le nouveau client.

L'icône Android et l'icône Windows proviennent exactement du fichier utilisé par
l'en-tête : `flutter_app/assets/img/logo-cnetp.png`. La clé de signature bêta est
privée dans `.private_build/`, avec configuration dans `android/key.properties`.
Ces éléments ne sont ni versionnés, ni téléversés avec l'APK ; les conserver
pour pouvoir signer les mises à jour.

Le benchmark `flutter_app/tool/benchmark_proxy.dart` mesure la latence en direct
et via le proxy local vers un même serveur HTTPS. Il ne valide pas un relais
distant distinct ni le débit de gros fichiers. Rapport :
`reports/expert_beta/proxy_benchmark.json`.

L’intégration automatique Google Calendar/Meet et l’import des présences Meet
ne sont pas inclus. Le secrétariat renseigne le lien externe existant.

### Distribution allégée vérifiée le 21 novembre 2026

La version `1.0.0-beta.1+3` est publiée dans l’App Store distant :
https://workalldomain.pythonanywhere.com/app-store/telecharger/2/
Un seul APK ARM 32/64 bits pèse 17 688 631 octets (17,7 Mo), contre 57,7 Mo
précédemment, soit une réduction de 69,4 %. Les bibliothèques natives sont
compressées et extraites à l’installation ; la signature bêta est conservée.
Le téléchargement distant a été vérifié par SHA-256. Aucun test d’installation
sur téléphone physique n’a été effectué.

La campagne autorisée couvre 153 comptes actifs. Gmail a accepté les envois
pour 150 adresses distinctes, correspondant à 152 comptes ; les destinataires
groupés sont en copie cachée. Aucun avis d’échec n’était reçu lors du contrôle
immédiat, ce qui ne prouve pas la livraison finale. Pour le compte au domaine
email invalide, l’envoi WhatsApp réel a échoué avec le code Twilio 63015
(numéro non inscrit au Sandbox). Aucun SMS n’a été envoyé.
Le bilan sans coordonnées est dans
`reports/expert_beta/apk_notification_summary.json` ; les coordonnées et reçus
du fournisseur restent privés dans `.private_build/`.

Les routes serveur de diagnostic et les nouvelles capacités Réunions restent
absentes du serveur distant (404) : les changements backend locaux exigent
encore un déploiement. La campagne signale cette limite aux experts.

## Mise à jour du serveur après publication Git

Depuis le checkout du serveur, avec son environnement virtuel activé et après
sauvegarde de la base, récupérer `main`, puis appliquer les migrations avant
de recharger l’application PythonAnywhere :

```bash
git pull --ff-only origin main
python manage.py migrate --noinput
python manage.py check
python manage.py collectstatic --noinput
```

Les migrations à inclure sont `norms.0014`, `meetings.0007` et `0008`, ainsi que
`mobileapp.0005` et `0006`. Le rechargement de l’application web doit suivre
ces commandes. Aucun nouvel APK n’est requis pour activer ces routes dans
l’APK allégé déjà publié.

Vérifier ensuite avec une session autorisée :

- `GET /api/v1/mobile/expert/meetings/capabilities/` : 200 avec les capacités ;
- `GET /api/v1/mobile/expert/meetings/` : 200 avec les seules réunions accessibles ;
- `OPTIONS /api/v1/mobile/diagnostics/` : 200 ;
- `/admin/mobileapp/clientdiagnostic/` : liste accessible à l’administration.

Ces contrôles de disponibilité ne prouvent pas la livraison push, email ou
des rappels : ces derniers exigent les services décrits plus haut.

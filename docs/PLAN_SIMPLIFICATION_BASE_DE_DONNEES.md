# Plan d’examen et de simplification des données

## Objectif

Réduire les informations jugées superflues autour des experts, des adhésions et des nominations, sans perdre les données nécessaires aux droits, aux décisions et à la traçabilité.

## Constat initial

- `apps/experts/models.py` : `Expert.status` décrit l’état du profil expert (en attente, actif, inactif, suspendu ou rejeté). Le modèle conserve également les dates et auteurs d’acceptation ou de rejet.
- `apps/governance/models.py` : `PilotageMembreship` et `CTCMembership` enregistrent l’appartenance d’un expert à un organe et son rôle. Ces adhésions ne possèdent pas de champ de statut distinct dans ces modèles.
- `apps/governance/phoenix_models.py` : `MandatOrganisation.status` décrit le cycle d’un mandat (proposé, en cours, terminé). Des contraintes et validations dépendent notamment de l’état « en cours ».
- `apps/core/models.py` : `BaseModel` fournit `created_at`, `updated_at`, `created_by` et `updated_by` à de nombreux modèles. Le champ « mis à jour » sert à la traçabilité ; il n’est pas nécessairement utile à afficher partout.

## Étapes proposées

1. **Identifier l’écran ou la table visée.** Relever les colonnes effectivement affichées, les filtres et les formulaires concernés. Confirmer si « database » désigne une interface de consultation ou le schéma physique de la base.
2. **Inventorier les usages de chaque champ candidat.** Vérifier les permissions, validations, notifications, exports, API, filtres, tris et migrations qui utilisent les statuts d’expert, d’adhésion ou de nomination et les dates de modification.
3. **Classer les éléments.** Pour chaque champ : conserver et afficher, conserver mais masquer dans l’interface, ou supprimer après analyse des dépendances. Privilégier le masquage des colonnes techniques et de traçabilité si seul l’écran paraît chargé.
4. **Valider les règles métier.** Confirmer quelles étapes du cycle d’adhésion ou de nomination doivent rester visibles, et quelles informations sont obligatoires pour établir une nomination et attribuer des droits.
5. **Mettre en œuvre la simplification retenue.** Adapter d’abord l’interface, les filtres et les exports concernés. Si une suppression en base est décidée, prévoir une migration Django et traiter les données existantes ainsi que les références dans le code.
6. **Vérifier le résultat.** Tester les parcours d’inscription, d’affectation, de nomination et de contrôle des droits concernés, ainsi que les migrations si le schéma change.

## Décisions à prendre avant modification

- Quel écran, export ou ensemble de tables est concerné ?
- Faut-il uniquement alléger l’affichage, ou aussi supprimer des colonnes en base ?
- Quels statuts précis sont considérés comme inutiles ?
- Les dates « mis à jour » doivent-elles être masquées partout ou seulement sur certaines vues ?

La simplification destructive des colonnes reste conditionnée à ces confirmations.

## Mise en œuvre du suivi de profil (21 octobre 2026)

- Une migration additive `experts.0008` crée `ProfileUpdate` et son journal `ProfileUpdateEvent`. Les fiches anciennes sans ligne de suivi sont comptées `NOT_STARTED` : cela signifie **absence de preuve de soumission dans la nouvelle procédure**, et non absence d’activité historique.
- Les transitions sont contrôlées par `apps/experts/profile_updates.py` ; seul le secrétariat peut ouvrir l’examen et certifier `COMPLETE`. Le compte actif, les nominations et les affectations restent indépendants.
- Le formulaire de choix d’organisation permet une soumission explicite ; le formulaire historique enregistre seulement un début de mise à jour. L’API privée `POST /api/v1/experts/{id}/profile-update/` expose les transitions et `GET` expose les critères manquants. L’administration Django permet de filtrer le suivi et de consulter les transitions.
- La commande `python manage.py suivi_profils` présente les indicateurs séparément. Les commandes existantes de notification et d’import conservent leur rôle : elles n’attribuent jamais `COMPLETE` et leurs filtres `ACTIVE` concernent l’état administratif de l’expert.
- Sur la base présente **avant migration** : 149 experts (148 `ACTIVE`, 1 `PENDING`), 39 CV, 2 choix SC appartenant à 1 expert et 399 affectations SC. Sur une copie après migration : 149 profils `NOT_STARTED`, 0 `COMPLETE`. Ces chiffres ne sont pas ceux de l’ancienne copie citée dans `prompt_test_2e2`.
- La migration a été exécutée sur une copie SQLite sous `/tmp/opencode/profile_migration_test.sqlite3`. Pour appliquer à la base courante, effectuer une sauvegarde puis exécuter `python manage.py migrate experts 0008` ; la base courante n’a pas été migrée ici.

À préciser ultérieurement : le modèle d’affectation migrée n’a pas de valeur `APPROVED` ; ne pas compter `MIGRATED` comme une validation administrative. Les autres écrans et exports restent à harmoniser avec cette distinction.

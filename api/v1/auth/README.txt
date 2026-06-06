Module: auth
============
Gestion de l'authentification et des utilisateurs.

Contenu:
- serializers.py : Serializers pour l'inscription, la connexion, le profil utilisateur et le changement de mot de passe.
- views.py       : AuthViewSet (register, login, logout, me, profile, change-password) et UserListViewSet.

Endpoints principaux:
  POST   /api/v1/auth/register/
  POST   /api/v1/auth/login/
  POST   /api/v1/auth/logout/
  GET    /api/v1/auth/me/
  PATCH  /api/v1/auth/profile/
  POST   /api/v1/auth/change-password/
  GET    /api/v1/users/
  GET    /api/v1/users/{id}/

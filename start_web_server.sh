#!/bin/bash
# Lance un simple serveur HTTP Python pour servir les fichiers statiques.
# Nécessite Python 3.

# Assurez-vous d'être dans le bon répertoire pour servir les fichiers
cd frontend_static

echo "Démarrage du serveur HTTP sur http://localhost:8000/"
python3 -m http.server 8000

🎯 OBJECTIF GLOBAL

Créer une bibliothèque Python nommée ghostapi qui permet de :

👉 Transformer automatiquement des fonctions Python en API REST
👉 Ajouter une authentification complète (JWT + rôles) en une ligne (via authdrop intégré)

⚡ EXPÉRIENCE UTILISATEUR FINALE
from ghostapi import expose

def get_users():
    return [{"name": "Donaldo"}]

def create_user(name: str):
    return {"name": name}

expose(auth=True)

👉 Résultat :

API REST auto

Auth complète

Swagger docs

Validation auto

🧱 STRUCTURE DU PROJET
ghostapi/
│
├── ghostapi/
│   ├── __init__.py
│   ├── core.py
│   ├── inspector.py
│   ├── router.py
│   ├── wrapper.py
│   ├── config.py
│   ├── utils.py
│
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── core.py
│   │   ├── security.py
│   │   ├── models.py
│   │   ├── middleware.py
│   │   ├── roles.py
│   │   ├── exceptions.py
│
├── tests/
│   ├── test_basic.py
│   ├── test_auth.py
│   ├── test_routes.py
│
├── examples/
│   ├── simple.py
│   ├── auth_example.py
│
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
🧠 MODULES À IMPLÉMENTER
🔹 core.py

Fonction principale :

def expose(auth: bool = False, host="127.0.0.1", port=8000):

Responsabilités :

scanner les fonctions utilisateur

générer routes

activer auth si demandé

lancer serveur

🔹 inspector.py

utiliser inspect

récupérer toutes les fonctions du module principal

ignorer fonctions privées

🔹 router.py

mapper fonctions → routes FastAPI

déterminer méthode HTTP :

nom fonction	méthode
get_*	GET
create_*	POST
update_*	PUT
delete_*	DELETE
🔹 wrapper.py

convertir fonctions Python en endpoints HTTP

gérer :

arguments

retour JSON

erreurs

🔹 config.py

stocker config globale

options :

auth

debug

rate limit (prévu)

🔹 utils.py

helpers communs

🔐 MODULE AUTH (authdrop intégré)
🔹 auth/core.py
def enable_auth(app, secret, expire):
🔹 auth/security.py

JWT encode/decode (python-jose)

bcrypt password hashing (passlib)

🔹 auth/models.py

User model :

id
email
password
role
🔹 auth/middleware.py

vérifier token

injecter user dans request

🔹 auth/roles.py
def require_role(role):
🔹 auth/exceptions.py

erreurs auth propres

⚙️ DÉPENDANCES

Dans pyproject.toml :

[project]
name = "ghostapi"
version = "0.1.0"
description = "Turn Python functions into APIs instantly with built-in auth"
requires-python = ">=3.8"

dependencies = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "python-jose",
    "passlib[bcrypt]"
]
🧪 TESTS AUTOMATIQUES (TRÈS IMPORTANT)

Créer tests avec :

pytest

🔹 test_basic.py

vérifier que API démarre

vérifier route simple

🔹 test_routes.py

GET fonctionne

POST fonctionne

🔹 test_auth.py

register

login

accès protégé

🤖 AUTO-TEST & AUTO-AMÉLIORATION

👉 Kilo doit :

exécuter tests automatiquement

corriger erreurs si tests échouent

boucler jusqu’à succès

📘 README.md

Doit inclure :

🚀 Installation
pip install ghostapi
⚡ Exemple
from ghostapi import expose

def hello():
    return "Hello"

expose()
🔐 Auth
expose(auth=True)
📚 Features

auto API

auto docs

auth intégrée

validation auto

📦 BUILD & PUBLICATION

Commande :

python -m build
twine upload dist/*
💣 FEATURES AVANCÉES (OPTIONNEL MAIS PRÉVU)

cache auto

rate limiting

websocket auto

versioning API

🧼 QUALITÉ CODE

type hints partout

docstrings

architecture propre

modularité forte

🚀 OBJECTIF FINAL

Une lib :

installable via pip

utilisable en 1 ligne

stable

testée

documentée

extensible

💥 BONUS OBLIGATOIRE

Ajouter CLI :

ghostapi run
🧠 INSTRUCTIONS IMPORTANTES POUR Kilo

ne pas générer code cassé

tester chaque module

corriger automatiquement

optimiser lisibilité

éviter duplication
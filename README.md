# 🎯 GhostAPI

Transformez vos fonctions Python en API REST instantanément, avec authentification intégrée.

## 🚀 Installation

```bash
pip install ghostapi
```

## ⚡ Exemple Rapide

```python
from ghostapi import expose

def get_users():
    return [{"name": "Donaldo"}]

def create_user(name: str):
    return {"name": name}

expose(auth=True)
```

Résultat :
- API REST automatique
- Auth complète (JWT + rôles)
- Documentation Swagger
- Validation automatique

## 📖 Documentation

### Utilisation de Base

```python
from ghostapi import expose

def hello():
    return {"message": "Hello World"}

def get_users():
    return [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]

def create_user(name: str, email: str):
    return {"name": name, "email": email, "id": 100}

# Démarre le serveur sur http://127.0.0.1:8000
expose()
```

Cela crée automatiquement :
- `GET /hello` → `{"message": "Hello World"}`
- `GET /users` → `[{"id": 1, "name": "John"}, ...]`
- `POST /user` → Crée un utilisateur

### Avec Authentification

```python
from ghostapi import expose

def get_secret_data():
    return {"secret": "data"}

# Active l'authentification JWT
expose(auth=True)
```

### API Personnalisée

```python
from ghostapi import create_api, add_routes

app = create_api(
    auth=True,
    title="Mon API",
    version="1.0.0"
)

def my_function():
    return {"data": "test"}

add_routes(app, {"my_function": my_function})
```

## 🔐 Authentification

### S'inscrire

```bash
POST /api/auth/register
{
    "email": "user@example.com",
    "password": "password123",
    "role": "user"
}
```

### Se Connecter

```bash
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password123
```

Réponse :
```json
{
    "access_token": "eyJ...",
    "token_type": "bearer"
}
```

### Accéder aux Routes Protégées

```bash
GET /protected-endpoint
Authorization: Bearer <access_token>
```

### Vérifier l'Utilisateur Connecté

```bash
GET /api/auth/me
Authorization: Bearer <access_token>
```

## 🎭 Rôles

GhostAPI supporte la hiérarchie de rôles :
- `admin` : Accès total
- `moderator` : Accès modéré
- `user` : Accès utilisateur
- `guest` : Accès limité

```python
from ghostapi.auth import require_role

# Utilisation avec FastAPI
@app.get("/admin")
async def admin_endpoint(user = Depends(require_role("admin"))):
    return {"message": "Admin only"}
```

## 📚 Fonctionnalités

- ✅ Transformation automatique de fonctions Python en API REST
- ✅ Authentification JWT intégrée
- ✅ Contrôle d'accès basé sur les rôles
- ✅ Documentation Swagger automatique
- ✅ Validation des paramètres automatique
- ✅ Support GET, POST, PUT, DELETE, PATCH
- ✅ CLI pour lancer le serveur

## 🔧 Configuration

```python
expose(
    auth=True,              # Activer l'authentification
    host="0.0.0.0",       # Adresse du serveur
    port=8000,             # Port du serveur
    debug=True,             # Mode debug
    cors_origins=["*"],   # Origins autorisées pour CORS
)
```

### Variable d'environnement pour le secret JWT

Pour plus de sécurité, définissez la variable d'environnement `GHOSTAPI_SECRET`:

```bash
# Linux/Mac
export GHOSTAPI_SECRET="votre-secret-securise"

# Windows
set GHOSTAPI_SECRET=votre-secret-securise
```

Ou en Python:
```python
import os
os.environ["GHOSTAPI_SECRET"] = "votre-secret-securise"

from ghostapi import expose
```

## 🖥️ CLI

```bash
# Lancer le serveur
ghostapi run

# Avec options
ghostapi run --host 0.0.0.0 --port 8080 --reload --debug
```

## 📁 Structure du Projet

```
ghostapi/
├── ghostapi/
│   ├── __init__.py       # Point d'entrée
│   ├── core.py           # Fonction expose()
│   ├── inspector.py      # Découverte de fonctions
│   ├── router.py         # Mapping vers routes FastAPI
│   ├── wrapper.py        # Conversion fonctions vers endpoints
│   ├── config.py         # Configuration globale
│   ├── utils.py          # Utilitaires
│   ├── cli.py            # Interface CLI
│   └── auth/            # Module d'authentification
│       ├── core.py
│       ├── security.py
│       ├── models.py
│       ├── middleware.py
│       ├── roles.py
│       └── exceptions.py
├── tests/                # Tests automatisés
├── examples/            # Exemples d'utilisation
├── pyproject.toml       # Configuration du package
└── README.md
```

## 🧪 Tests

```bash
# Installer les dépendances de test
pip install pytest

# Lancer les tests
pytest tests/
```
## 📝 License

MIT License

---

Fait par ZoubStack

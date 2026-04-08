# Guide complet GhostAPI

## Table des matières

1. [Installation](#installation)
2. [Démarrage rapide](#démarrage-rapide)
3. [Configuration](#configuration)
4. [Authentification](#authentification)
5. [Fonctionnalités avancées](#fonctionnalités-avancées)
6. [Tests intégrés](#tests-intégrés)
7. [Exemples](#exemples)
8. [API Reference](#api-reference)

---

## Installation

### Prérequis

- Python 3.8+
- pip

### Installer ghostapi

```bash
pip install ghostapi
```

Ou installer depuis les sources :

```bash
git clone https://github.com/ghostapi/ghostapi.git
cd ghostapi
pip install -e .
```

---

## Démarrage rapide

### Premier exemple

Créez un fichier `main.py` :

```python
from ghostapi import expose

def hello():
    """Retourne un message de greeting."""
    return {"message": "Hello World"}

def get_users():
    """Retourne la liste des utilisateurs."""
    return [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]

def create_user(name: str, email: str):
    """Crée un nouvel utilisateur."""
    return {"id": 3, "name": name, "email": email}

# Lance le serveur
expose()
```

Lancez le serveur :

```bash
python main.py
```

Accédez à :
- **API** : http://127.0.0.1:8000
- **Docs** : http://127.0.0.1:8000/docs

### Sans lancer le serveur (pour les tests)

```python
from ghostapi import create_api, add_routes

def get_users():
    return [{"name": "Alice"}]

# Crée l'API sans lancer le serveur
app = create_api()
add_routes(app, {"get_users": get_users})

# Maintenant vous pouvez tester avec FastAPI TestClient
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.get("/users")
print(response.json())
```

---

## Configuration

### Paramètres de `expose()`

```python
expose(
    auth: bool = False,           # Activer l'authentification
    host: str = "127.0.0.1",     # Adresse du serveur
    port: int = 8000,            # Port du serveur
    debug: bool = False,         # Mode debug
    title: str = "GhostAPI",    # Titre de l'API
    description: str = "...",     # Description
    version: str = "1.0.0",     # Version
    secret: Optional[str] = None, # Clé secrète JWT
    expire_minutes: int = 30,    # Expiration token
    cors_origins: List[str] = None,  # Origins CORS autorisées
    rate_limit: int = 60,       # Requêtes/minute (0=désactivé)
    storage_backend: str = "memory",  # "memory", "file", "buffered", "async_file"
    storage_file: str = "data.json",   # Fichier pour storage
    cache_enabled: bool = False,      # Activer le cache
    cache_ttl: int = 300,            # TTL du cache
    health_check: bool = True,       # Health endpoints
    hooks: Optional[Hooks] = None,    # Hooks personnalisés
    auto_test: bool = False          # Tests automatiques
)
```

### Variables d'environnement

```bash
# Obligatoire en production
export GHOSTAPI_SECRET="votre-clé-secrète-très-longue"

# Optionnel
export GHOSTAPI_DEBUG=true
```

---

## Authentification

### Activer l'authentification

```python
from ghostapi import expose

def get_data():
    return {"data": "secret"}

# Active JWT auth
expose(auth=True)
```

### Inscription

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "Password123", "role": "user"}'
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -d "username=user@example.com&password=Password123"
```

Réponse :
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Accès aux routes protégées

```bash
curl -X GET http://127.0.0.1:8000/data \
  -H "Authorization: Bearer VOTRE_TOKEN"
```

### Rôles

Trois rôles disponibles :
- `user` - Utilisateur standard
- `moderator` - Modérateur
- `admin` - Administrateur

La hiérarchie : admin > moderator > user > guest

### Route /me

```bash
curl -X GET http://127.0.0.1:8000/api/auth/me \
  -H "Authorization: Bearer VOTRE_TOKEN"
```

Réponse :
```json
{
  "id": "uuid-utilisateur",
  "email": "user@example.com",
  "role": "user"
}
```

---

## Fonctionnalités avancées

### Stockage persistant

```python
# Utiliser un fichier JSON au lieu de la mémoire
expose(storage_backend="file", storage_file="mes_donnees.json")

# Avec buffering (meilleures performances)
expose(storage_backend="buffered", storage_file="data.json")

# Async I/O
expose(storage_backend="async_file", storage_file="data.json")
```

### Rate Limiting

```python
# Limiter à 100 requêtes par minute
expose(rate_limit=100)

# Désactiver
expose(rate_limit=0)
```

### CORS

```python
# Autoriser des origins spécifiques
expose(cors_origins=["https://mon-site.com", "https://app.mon-site.com"])
```

### Cache Intégré

```python
# Activer le cache
expose(
    cache_enabled=True,
    cache_ttl=300  # 5 minutes
)
```

### Health Check

```python
# Activer les endpoints de health
expose(health_check=True)

# Endpoints disponibles:
# GET /health      - Status global
# GET /health/ready - Readiness (Kubernetes)
# GET /health/live  - Liveness (Kubernetes)
```

### Hooks Personnalisés

```python
from ghostapi.hooks import Hooks

def log_request(request):
    print(f"Requête: {request.method} {request.url}")

def before_response(response):
    response.headers["X-API-Version"] = "1.0.0"
    return response

hooks = Hooks(
    before_request=log_request,
    before_response=before_response
)

expose(hooks=hooks)
```

### Décorateurs

```python
from ghostapi.decorators import cache, rate_limit, require_auth

@cache(ttl=60)
def get_data():
    return expensive_computation()

@rate_limit(max_calls=10, period=60)
def api_call():
    return {"result": "ok"}

@require_auth(role="admin")
def admin_function():
    return {"secret": "data"}
```

---

## Tests Intégrés

### Tests Automatiques

Les tests s'exécutent automatiquement en mode debug :

```python
expose(debug=True)
# Affiche les résultats des tests au démarrage
```

Ou explicitement :

```python
expose(auto_test=True)
```

### Tests Programmatiques

```python
from ghostapi.testing import ContinuousTester

tester = ContinuousTester()

def my_function(name: str, age: int):
    return {"name": name, "age": age}

result = tester.test_function(my_function)
print(result)
# {'valid': True, 'tests_passed': True, ...}
```

### Validation de Fonction

```python
from ghostapi.testing import TestGenerator

def create_user(name: str, email: str):
    return {"name": name, "email": email}

generator = TestGenerator()
test_cases = generator.generate_tests(create_user)

for test_case in test_cases:
    print(f"{test_case.name}: {test_case.input_params}")
```

---

## Exemples

### Exemple complet avec auth

```python
from ghostapi import expose
from ghostapi.auth import require_role

def get_public_data():
    """Données publiques - pas de auth requise."""
    return {"message": "Bienvenue!"}

def get_private_data():
    """Données privées - auth requise."""
    return {"secret": "information sensibles"}

def get_admin_data():
    """Données admin - rôle admin requis."""
    return {"admin_only": "zone protégée"}

# Avec authentification
expose(
    auth=True,
    title="Mon API",
    version="1.0.0",
    cache_enabled=True,
    health_check=True
)
```

### Exemple avec Cache

```python
from ghostapi import expose
from ghostapi.decorators import cache

@cache(ttl=60)
def get_weather():
    """Données mises en cache pendant 60 secondes."""
    return fetch_weather_from_api()

expose(cache_enabled=True)
```

### Exemple avec Stockage Bufferisé

```python
from ghostapi import expose

def save_data(key: str, value: str):
    """Sauvegarde avec buffering pour de meilleures performances."""
    from ghostapi.storage import get_storage
    storage = get_storage()
    storage.set(key, {"value": value})
    return {"saved": True}

expose(storage_backend="buffered")
```

---

## API Reference

### Fonctions principales

| Fonction | Description |
|----------|-------------|
| `expose()` | Lance le serveur API |
| `create_api()` | Crée l'API sans lancer le serveur |
| `get_app()` | Retourne l'application FastAPI |
| `add_routes()` | Ajoute des routes à une app existante |

### Module Auth

| Fonction | Description |
|----------|-------------|
| `enable_auth()` | Active l'authentification |
| `require_role()` | Exige un rôle spécifique |
| `has_role()` | Vérifie le rôle |
| `get_current_user()` | Retourne l'utilisateur actuel |

### Module Storage

| Fonction | Description |
|----------|-------------|
| `get_storage()` | Retourne le storage actuel |
| `set_storage()` | Définit un storage personnalisé |
| `init_storage()` | Initialise le storage |

### Module Cache

| Fonction | Description |
|----------|-------------|
| `get_cache()` | Retourne le cache |
| `init_cache()` | Initialise le cache |
| `cached()` | Décorateur de cache |
| `clear_cache()` | Vide le cache |

### Module Health

| Fonction | Description |
|----------|-------------|
| `add_health_check()` | Ajoute les endpoints de health |
| `get_health_check()` | Retourne le gestionnaire |

### Module Hooks

| Fonction | Description |
|----------|-------------|
| `Hooks` | Classe de configuration des hooks |
| `add_hooks()` | Ajoute les hooks à l'app |

### Module Testing

| Fonction | Description |
|----------|-------------|
| `ContinuousTester` | Testeur automatique |
| `TestGenerator` | Générateur de tests |
| `run_auto_tests()` | Exécute les tests |

---

## Dépannage

### Erreur "No app created"

Assurez-vous d'appeler `create_api()` ou `expose()` avant `get_app()`.

### Erreur d'authentification

Vérifiez que :
1. Le token n'est pas expiré
2. Le token est correctement formaté (Bearer)
3. La route nécessite bien l'authentification

### Warnings de sécurité

Si vous voyez :
```
⚠️ SECURITY WARNING: You are using the default secret key!
```

Définissez la variable d'environnement :
```bash
export GHOSTAPI_SECRET="votre-cle-secrete"
```

---

## Prochaines étapes

- Consultez les tests pour plus d'exemples
- Regardez les examples dans le dossier `examples/`
- Contribuez au projet sur GitHub

# API Reference GhostAPI

## Table des matières

1. [Fonctions principales](#fonctions-principales)
2. [Auth API](#auth-api)
3. [Storage API](#storage-api)
4. [Cache API](#cache-api)
5. [Health API](#health-api)
6. [Hooks API](#hooks-api)
7. [Decorators API](#decorators-api)
8. [Testing API](#testing-api)
9. [Models](#models)
10. [Exceptions](#exceptions)

---

## Fonctions principales

### `expose()`

Lance le serveur API et expose les fonctions du module appelant.

```python
from ghostapi import expose

def hello():
    return "Hello"

expose()
```

**Paramètres :**

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `auth` | `bool` | `False` | Activer l'authentification |
| `host` | `str` | `"127.0.0.1"` | Adresse du serveur |
| `port` | `int` | `8000` | Port du serveur |
| `debug` | `bool` | `False` | Mode debug |
| `title` | `str` | `"GhostAPI"` | Titre de l'API |
| `description` | `str` | `...` | Description |
| `version` | `str` | `"1.0.0"` | Version |
| `secret` | `Optional[str]` | `None` | Clé JWT |
| `expire_minutes` | `int` | `30` | Expiration token |
| `cors_origins` | `Optional[List[str]]` | `None` | Origins CORS |
| `rate_limit` | `int` | `60` | Requêtes/min |
| `storage_backend` | `str` | `"memory"` | "memory", "file", "buffered", "async_file" |
| `storage_file` | `str` | `"ghostapi_data.json"` | Fichier data |
| `cache_enabled` | `bool` | `False` | Activer le cache |
| `cache_ttl` | `int` | `300` | TTL du cache (secondes) |
| `health_check` | `bool` | `True` | Activer health endpoints |
| `hooks` | `Optional[Hooks]` | `None` | Hooks personnalisés |
| `auto_test` | `bool` | `False` | Tests automatiques |

**Retourne :** `FastAPI`

---

### `create_api()`

Crée l'application FastAPI sans lancer le serveur.

```python
from ghostapi import create_api

app = create_api(auth=True)
```

**Paramètres :** Même que `expose()`

**Retourne :** `FastAPI`

---

### `get_app()`

Retourne l'application FastAPI actuelle.

```python
from ghostapi import get_app

app = get_app()
```

**Retourne :** `Optional[FastAPI]`

---

### `add_routes()`

Ajoute des routes à une application existante.

```python
from ghostapi import create_api, add_routes

def get_users():
    return [{"name": "Alice"}]

app = create_api()
add_routes(app, {"get_users": get_users})
```

**Paramètres :**

| Paramètre | Type | Description |
|-----------|------|-------------|
| `app` | `FastAPI` | Application FastAPI |
| `functions` | `Optional[Dict[str, Callable]]` | Fonctions à exposer |
| `module` | `Optional[Any]` | Module à scanner |
| `auth_required` | `bool` | Auth requise |

---

## Auth API

### `enable_auth()`

Active l'authentification sur une application.

```python
from fastapi import FastAPI
from ghostapi.auth import enable_auth

app = FastAPI()
enable_auth(app)
```

**Paramètres :**

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `app` | `FastAPI` | - | Application FastAPI |
| `secret` | `str` | `DEFAULT_SECRET` | Clé JWT |
| `expire_minutes` | `int` | `30` | Expiration |
| `excluded_paths` | `Optional[List[str]]` | `None` | Chemins exclus |

---

### `require_role()`

Crée une dépendance qui exige un rôle.

```python
from fastapi import FastAPI, Depends
from ghostapi.auth import require_role

app = FastAPI()

@app.get("/admin")
async def admin_page(user = Depends(require_role("admin"))):
    return {"message": "Bienvenue Admin!"}
```

**Paramètre :** `role: str`

**Retourne :** `RequireRole`

---

### `has_role()`

Vérifie si un utilisateur a un rôle.

```python
from ghostapi.auth import has_role

# Vérification simple
if has_role("user", "admin"):  # False
    print("Admin!")

if has_role("admin", "user"):  # True (hiérarchie)
    print("Admin peut accéder!")
```

**Paramètres :**

| Paramètre | Type | Description |
|-----------|------|-------------|
| `user_role` | `Optional[str]` | Rôle de l'utilisateur |
| `required_role` | `str` | Rôle requis |

**Retourne :** `bool`

---

### `get_current_user()`

Extrait l'utilisateur actuel de la requête.

```python
from fastapi import Request
from ghostapi.auth import get_current_user

def get_user(request: Request):
    user = get_current_user(request)
    if user:
        return user["email"]
    return "Guest"
```

**Paramètre :** `request: Request`

**Retourne :** `Optional[dict]`

---

## Storage API

### `get_storage()`

Retourne le storage actuel.

```python
from ghostapi.storage import get_storage

storage = get_storage()
users = storage.get_all()
```

**Retourne :** `StorageBackend`

---

### `set_storage()`

Définit un storage personnalisé.

```python
from ghostapi.storage import set_storage, InMemoryStorage

storage = InMemoryStorage()
set_storage(storage)
```

**Paramètre :** `storage: StorageBackend`

---

### `init_storage()`

Initialise le storage.

```python
from ghostapi.storage import init_storage

# Memory
init_storage(backend="memory")

# File
init_storage(backend="file", file_path="data.json")

# Buffered (write-behind)
init_storage(backend="buffered", file_path="data.json")

# Async file
init_storage(backend="async_file", file_path="data.json")
```

**Paramètres :**

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `backend` | `str` | `"memory"` | "memory", "file", "buffered", "async_file" |
| `file_path` | `str` | `"ghostapi_data.json"` | Chemin fichier |
| `force` | `bool` | `False` | Forcer réinit |

**Retourne :** `StorageBackend`

---

### Classes de Storage

```python
from ghostapi.storage import (
    StorageBackend,
    InMemoryStorage,
    FileStorage,
    BufferedFileStorage,
    AsyncFileStorage
)
```

- **InMemoryStorage** : Stockage en mémoire (volatile)
- **FileStorage** : Stockage persistant JSON
- **BufferedFileStorage** : Stockage avec buffer d'écriture (meilleures performances)
- **AsyncFileStorage** : Stockage async avec aiofiles

---

## Cache API

### `get_cache()`

Retourne le cache actuel.

```python
from ghostapi.cache import get_cache

cache = get_cache()
value = cache.get("key")
```

**Retourne :** `InMemoryCache`

---

### `init_cache()`

Initialise le cache.

```python
from ghostapi.cache import init_cache

init_cache(default_ttl=300)  # TTL de 5 minutes
```

**Paramètres :**

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `default_ttl` | `int` | `300` | TTL par défaut en secondes |

---

### `cached()` - Décorateur

Décorateur pour cacher les résultats de fonction.

```python
from ghostapi.cache import cached

@cached(ttl=60)
def get_expensive_data():
    return expensive_computation()
```

**Paramètres :**

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `ttl` | `int` | `300` | TTL en secondes |
| `key_prefix` | `Optional[str]` | `None` | Préfixe pour la clé |

---

### `clear_cache()`

Vide le cache.

```python
from ghostapi.cache import clear_cache

count = clear_cache()
print(f"Removed {count} entries")
```

**Retourne :** `int` - Nombre d'entrées supprimées

---

### `get_cache_stats()`

Retourne les statistiques du cache.

```python
from ghostapi.cache import get_cache_stats

stats = get_cache_stats()
print(stats)
# {'total_entries': 10, 'default_ttl': 300, 'expired_cleaned': 2}
```

---

### `add_cache_middleware()`

Ajoute le middleware de cache HTTP.

```python
from ghostapi.cache import add_cache_middleware

add_cache_middleware(
    app,
    ttl=300,
    excluded_paths=["/docs"],
    methods=["GET"]
)
```

---

## Health API

### `add_health_check()`

Ajoute les endpoints de health check.

```python
from ghostapi.health import add_health_check

add_health_check(app)
```

**Paramètres :**

| Paramètre | Type | Description |
|-----------|------|-------------|
| `app` | `FastAPI` | Application FastAPI |

**Endpoints ajoutés :**

- `GET /health` - Status global
- `GET /health/ready` - Readiness check (Kubernetes)
- `GET /health/live` - Liveness check (Kubernetes)

---

### `get_health_check()`

Retourne le gestionnaire de health check.

```python
from ghostapi.health import get_health_check

health = get_health_check()
health.register_check("custom", lambda: True)

status = health.get_status()
```

---

## Hooks API

### `Hooks`

Classe pour configurer les hooks.

```python
from ghostapi.hooks import Hooks

def log_request(request):
    print(f"Request: {request.method} {request.url}")

def before_response(response):
    response.headers["X-Custom"] = "value"
    return response

hooks = Hooks(
    before_request=log_request,
    before_response=before_response,
    on_error=handle_error
)
```

**Paramètres :**

| Paramètre | Type | Description |
|-----------|------|-------------|
| `before_request` | `Optional[Callable]` | Exécuté avant chaque requête |
| `after_request` | `Optional[Callable]` | Exécuté après chaque requête |
| `before_response` | `Optional[Callable]` | Modifie la réponse |
| `after_response` | `Optional[Callable]` | Après l'envoi de la réponse |
| `on_error` | `Optional[Callable]` | En cas d'erreur |
| `on_auth_success` | `Optional[Callable]` | Après authentification réussie |

---

### `add_hooks()`

Ajoute les hooks à l'application.

```python
from ghostapi.hooks import add_hooks, Hooks

hooks = Hooks(before_request=log_request)
add_hooks(app, hooks)
```

---

## Decorators API

### `@cache`

Décorateur pour cacher les résultats.

```python
from ghostapi.decorators import cache

@cache(ttl=60)
def get_data():
    return {"data": "expensive"}
```

---

### `@rate_limit`

Décorateur pour limiter les appels.

```python
from ghostapi.decorators import rate_limit

@rate_limit(max_calls=10, period=60)
def api_call():
    return {"result": "ok"}
```

---

### `@require_auth`

Décorateur pour exiger l'authentification.

```python
from ghostapi.decorators import require_auth

@require_auth()
def protected():
    return {"secret": "data"}

@require_auth(role="admin")
def admin_only():
    return {"admin": "data"}
```

---

### `@retry`

Décorateur pour réessayer en cas d'erreur.

```python
from ghostapi.decorators import retry

@retry(max_attempts=3, delay=1.0)
def unreliable_call():
    return fetch_data()
```

---

### `@timeout`

Décorateur pour ajouter un timeout.

```python
from ghostapi.decorators import timeout

@timeout(seconds=30.0)
def slow_operation():
    return long_computation()
```

---

### `@validate_params`

Décorateur pour valider les paramètres.

```python
from ghostapi.decorators import validate_params

@validate_params(
    age=lambda x: x >= 0,
    email=lambda x: '@' in x
)
def create_user(name: str, age: int, email: str):
    return {"name": name, "age": age, "email": email}
```

---

## Testing API

### `ContinuousTester`

Testeur automatique pour les fonctions.

```python
from ghostapi.testing import ContinuousTester

tester = ContinuousTester()

def my_function(name: str, age: int):
    return {"name": name, "age": age}

result = tester.test_function(my_function)
print(result)
# {'valid': True, 'tests_passed': True, ...}
```

---

### `TestGenerator`

Génère des cas de test depuis les signatures.

```python
from ghostapi.testing import TestGenerator

def calculate(a: int, b: int):
    return a + b

generator = TestGenerator()
test_cases = generator.generate_tests(calculate)
```

---

### `run_auto_tests()`

Exécute des tests sur les fonctions.

```python
from ghostapi.testing import run_auto_tests

def get_data():
    return {"data": "test"}

results = run_auto_tests({"get_data": get_data})
print(results)
# {'total': 1, 'passed': 1, 'failed': 0, ...}
```

---

### `auto_test` - Paramètre

Active les tests automatiques avec `expose()`.

```python
from ghostapi import expose

# Les tests s'exécutent au démarrage
expose(debug=True)  # Inclut auto-tests
# ou
expose(auto_test=True)  # Tests uniquement
```

---

## Models

### `UserCreate`

```python
from ghostapi.auth.models import UserCreate

user = UserCreate(
    email="user@example.com",
    password="Password123",
    role="user"
)
```

**Champs :**

| Champ | Type | Description |
|-------|------|-------------|
| `email` | `EmailStr` | Email valide |
| `password` | `str` | Min 8 chars, majuscule, minuscule, chiffre |
| `role` | `str` | "user", "moderator", ou "admin" |

---

### `UserResponse`

```python
from ghostapi.auth.models import UserResponse

user = UserResponse(
    id="uuid",
    email="user@example.com",
    role="user"
)
```

---

### `Token`

```python
from ghostapi.auth.models import Token

token = Token(
    access_token="eyJ...",
    token_type="bearer"
)
```

---

## Exceptions

### `AuthenticationError`

Erreur d'authentification générale.

```python
from ghostapi.auth.exceptions import AuthenticationError

raise AuthenticationError("Invalid credentials")
```

---

### `InvalidCredentialsError`

Identifiants invalides.

```python
from ghostapi.auth.exceptions import InvalidCredentialsError

raise InvalidCredentialsError()
```

---

### `UserAlreadyExistsError`

Utilisateur déjà existant.

```python
from ghostapi.auth.exceptions import UserAlreadyExistsError

raise UserAlreadyExistsError("email@example.com")
```

---

### `UserNotFoundError`

Utilisateur non trouvé.

```python
from ghostapi.auth.exceptions import UserNotFoundError

raise UserNotFoundError()
```

---

### `InvalidTokenError`

Token JWT invalide.

```python
from ghostapi.auth.exceptions import InvalidTokenError

raise InvalidTokenError("Token expired")
```

---

### `AuthorizationError`

Erreur d'autorisation (permissions insuffisantes).

```python
from ghostapi.auth.exceptions import AuthorizationError

raise AuthorizationError("Admin required")
```

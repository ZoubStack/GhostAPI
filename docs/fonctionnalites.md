# Fonctionnalités de GhostAPI

GhostAPI est un framework Python qui permet de transformer instantanément des fonctions Python en API REST complètes, avec authentification et sécurité intégrées.

---

## 🚀 Transformation Automatique de Fonctions en API

### Découverte Automatique
- Analyse automatique du module appelant pour détecter les fonctions publiques
- Pas besoin de configuration complexe : il suffit d'importer et d'exposer

### Mapping des Méthodes HTTP
| Préfixe de fonction | Méthode HTTP | Exemple |
|-------------------|--------------|---------|
| `get_` | GET | `get_users()` → `/users` (GET) |
| `create_` | POST | `create_user()` → `/user` (POST) |
| `update_` | PUT | `update_user()` → `/user` (PUT) |
| `delete_` | DELETE | `delete_user()` → `/user` (DELETE) |
| `patch_` | PATCH | `patch_user()` → `/user` (PATCH) |
| (par défaut) | GET | `hello()` → `/hello` (GET) |

### Conversion des Noms
- Les underscore sont convertis en tirets : `get_all_users()` → `/all-users`
- Les noms de fonctions sont convertis en kebab-case

---

## 🔐 Authentification JWT

### Inscription Utilisateur
```
POST /api/auth/register
{
    "email": "user@example.com",
    "password": "password123",
    "role": "user"
}
```

### Connexion
```
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

### Accès aux Routes Protégées
```
GET /protected-endpoint
Authorization: Bearer <access_token>
```

### Vérification de l'Utilisateur
```
GET /api/auth/me
Authorization: Bearer <access_token>
```

### Configuration
- Secret JWT configurable (variable d'environnement `GHOSTAPI_SECRET`)
- Expiration du token configurable (par défaut 30 minutes)
- Hachage des mots de passe avec bcrypt

---

## 🎭 Contrôle d'Accès Basé sur les Rôles (RBAC)

### Hiérarchie des Rôles
```
admin     → admin, moderator, user, guest
moderator → moderator, user, guest
user      → user, guest
guest     → guest
```

### Utilisation
```python
from ghostapi.auth import require_role
from fastapi import Depends

@app.get("/admin")
async def admin_endpoint(user = Depends(require_role("admin"))):
    return {"message": "Admin only"}
```

### Décorateur pour Plusieurs Rôles
```python
from ghostapi.auth.roles import require_roles

@require_roles("admin", "moderator")
async def protected_endpoint():
    return {"message": "Protected"}
```

---

## 📚 Documentation Automatique

### Swagger UI
- URL : `/docs`
- Interface interactive pour tester les endpoints

### ReDoc
- URL : `/redoc`
- Documentation au format OpenAPI alternatif

### Schéma OpenAPI
- URL : `/openapi.json`
- Schema JSON complet de l'API

---

## ✅ Validation Automatique

### Modèles Pydantic
- Génération automatique des modèles de requête depuis les paramètres de fonction
- Validation des types Python (str, int, float, bool, list, dict)
- Support des valeurs par défaut

### Exemple
```python
def create_user(name: str, email: str, age: int = 18):
    return {"name": name, "email": email, "age": age}
```

Génère automatiquement un modèle de validation :
```python
class CreateUserRequest(BaseModel):
    name: str
    email: str
    age: int = 18
```

---

## ⚡ CLI (Interface en Ligne de Commande)

### Commandes Disponibles
```bash
# Lancer le serveur
ghostapi run

# Avec options
ghostapi run --host 0.0.0.0 --port 8080 --reload --debug
```

### Options
| Option | Description | Défaut |
|--------|-------------|--------|
| `--host` | Adresse du serveur | `127.0.0.1` |
| `--port` | Port du serveur | `8000` |
| `--reload` | Rechargement automatique | `false` |
| `--debug` | Mode debug | `false` |

---

## 🚦 Rate Limiting (Limitation de Débit)

### Configuration
- Par défaut : 60 requêtes/minute par IP
- Personnalisable via le paramètre `rate_limit`

### Chemins Exclus
- `/docs` - Documentation Swagger
- `/openapi.json` - Schema OpenAPI
- `/redoc` - Documentation ReDoc
- `/api/auth` - Routes d'authentification

### Réponse en Cas de Dépassement
```json
{
    "detail": "Rate limit exceeded. Please try again later."
}
```
Code HTTP : `429 Too Many Requests`

---

## 💾 Stockage Pluggable

### InMemoryStorage (Par Défaut)
- Stockage en mémoire (volatile)
- Idéal pour le développement et les tests

### FileStorage
- Stockage persistant dans un fichier JSON
- Sanitization automatique des chemins (protection contre les path traversal attacks)

### Configuration
```python
expose(
    storage_backend="file",      # "memory" ou "file"
    storage_file="data.json"      # Nom du fichier
)
```

### API de Stockage
```python
from ghostapi.storage import (
    get_storage,
    set_storage,
    init_storage,
    StorageBackend,
    InMemoryStorage,
    FileStorage
)
```

---

## 🔒 Headers de Sécurité

### Headers Automatiques
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection`
- `Strict-Transport-Security` (si HTTPS)

### Personnalisation
```python
from ghostapi.security_headers import add_security_headers
add_security_headers(app)
```

---

## 🌐 CORS (Cross-Origin Resource Sharing)

### Configuration
```python
expose(
    cors_origins=["*"]  # Liste des origines autorisées
)
```

### Options
- `"*"` : Toutes les origines
- Liste spécifique : `["https://example.com", "https://api.example.com"]`

---

## 📝 Logging

### Configuration du Niveau
```python
expose(debug=True)  # Niveau DEBUG
expose(debug=False)  # Niveau INFO
```

### Gestion des Exceptions
- Gestion centralisée des erreurs HTTP
- Messages d'erreur structurés

---

## ⚙️ API de Configuration

### Fonction Principale : `expose()`
```python
from ghostapi import expose

def my_function():
    return {"data": "test"}

expose(
    auth=True,                 # Activer l'authentification
    host="0.0.0.0",           # Adresse du serveur
    port=8000,                 # Port du serveur
    debug=True,                # Mode debug
    title="Mon API",          # Titre de l'API
    version="1.0.0",           # Version de l'API
    cors_origins=["*"],       # Origines CORS
    rate_limit=60,            # Limite de requêtes/minute
    storage_backend="memory", # Backend de stockage
    secret="my-secret",       # Secret JWT
    expire_minutes=30         # Expiration du token
)
```

### Création Manuelle d'API
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

### Récupération de l'App
```python
from ghostapi import get_app

app = get_app()
```

---

## 🧪 Points d'Entrée Exportés

### Fonctions Principales
```python
from ghostapi import (
    expose,           # Transformer et démarrer
    create_api,       # Créer sans démarrer
    get_app,          # Récupérer l'app
    add_routes        # Ajouter des routes
)
```

### Authentification
```python
from ghostapi.auth import (
    enable_auth,      # Activer l'auth
    require_role,    # Exiger un rôle
    has_role,        # Vérifier un rôle
    get_current_user # Utilisateur actuel
)
```

### Stockage
```python
from ghostapi import (
    get_storage,
    set_storage,
    init_storage,
    StorageBackend,
    InMemoryStorage,
    FileStorage
)
```

---

## 🚀 Nouvelles Fonctionnalités Implémentées

### 1. Système de Cache Intégré

GhostAPI intègre désormais un système de cache performant :

```python
expose(
    cache_enabled=True,
    cache_ttl=300,  # 5 minutes
)
```

#### Décorateur @cached
```python
from ghostapi.decorators import cache

@cache(ttl=60)
def get_expensive_data():
    return expensive_computation()
```

#### CacheMiddleware
- Cache au niveau HTTP
- Exclusion de chemins configurable
- Méthodes HTTP configurables

---

### 2. Tests Automatiques Intégrés

 Système de tests qui s'exécutent automatiquement :

```python
# Les tests s'exécutent au démarrage
expose(debug=True)
# ou
expose(auto_test=True)
```

#### TestGenerator
```python
from ghostapi.testing import TestGenerator

generator = TestGenerator()
test_cases = generator.generate_tests(my_function)
```

#### ContinuousTester
```python
from ghostapi.testing import ContinuousTester

tester = ContinuousTester()
result = tester.test_function(my_function)
```

---

### 3. Health Check Endpoints

Endpoints de monitoring pour Kubernetes :

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Status global |
| `GET /health/ready` | Readiness check |
| `GET /health/live` | Liveness check |

```python
expose(health_check=True)
```

---

### 4. Hooks Personnalisables

```python
from ghostapi.hooks import Hooks

def log_request(request):
    print(f"Requête: {request.method} {request.url}")

hooks = Hooks(
    before_request=log_request,
    before_response=modify_response,
    on_error=handle_error
)

expose(hooks=hooks)
```

---

### 5. Décorateurs

```python
from ghostapi.decorators import cache, rate_limit, require_auth, retry, timeout, validate_params

@cache(ttl=60)
def get_data():
    return data

@rate_limit(max_calls=10, period=60)
def api_call():
    return data

@require_auth(role="admin")
def admin_function():
    return sensitive_data

@retry(max_attempts=3)
def unreliable_call():
    return fetch_data()

@timeout(seconds=30)
def slow_operation():
    return long_task()
```

---

### 6. Stockage Amélioré

#### BufferedFileStorage
- Write-behind pour de meilleures performances
- Buffer configurable
- Écriture atomique

#### AsyncFileStorage
- I/O asynchrone avec aiofiles
- Fallback automatique

```python
expose(
    storage_backend="buffered",  # ou "async_file"
    storage_file="data.json"
)
```

---

### 7. Messages d'Erreur Améliorés

#### Erreurs de Paramètres en Français
```
Le paramètre 'age' doit être un entier, reçu : 'abc'
```

#### Types Non Supportés
```
Type 'complex' non supporté pour la génération automatique du modèle.
Types supportés: str, int, float, bool, list, dict, Optional[T], List[T], Union[T, ...]

Pour utiliser ce type, utilisez un Pydantic model explicite:
```

---

## 📦 Dépendances

- **fastapi** - Framework web moderne
- **uvicorn** - Serveur ASGI
- **pydantic** - Validation des données
- **python-jose** - Tokens JWT
- **passlib** - Hachage de mots de passe

---

*Document généré pour GhostAPI v0.1.0*

---

## 🧙‍♂️ CLI Interactive Generator

### Mode Interactif
Lancez le générateur interactif pour créer des fonctions API :

```bash
ghostapi new --interactive
# ou
ghostapi new -i
```

Cela vous guidera à travers :
- Nom de la fonction
- Route path
- Méthode HTTP (GET, POST, PUT, DELETE)
- Niveau d'authentification
- Rate limiting
- Mise en cache

### Mode Commandes
Utilisez des arguments directs :

```bash
ghostapi new create_user --route=/users/create --method=POST --auth=user --rate-limit=10 --cache=300
```

#### Options
| Option | Description |
|--------|-------------|
| `--name` | Nom de la fonction |
| `--route` | Chemin de la route |
| `--method` | Méthode HTTP (GET, POST, PUT, DELETE) |
| `--auth` | Niveau d'authentification (user, admin, ou rôle personnalisé) |
| `--rate-limit` | Limite de requêtes par minute |
| `--cache` | TTL du cache en secondes |

---

## 🔄 Hot Reload pour Fonctions Individuelles

Rechargez des fonctions spécifiques sans redémarrer le serveur complet.

### FunctionWatcher
```python
from ghostapi.hotreload import FunctionWatcher

watcher = FunctionWatcher(
    callback=lambda mod, func: print(f"🔄 Rechargé: {mod}.{func}")
)

# Surveiller une fonction
watcher.watch_function("my_module", "my_function")

# Surveiller un module entier
watcher.watch_module("my_module")

# Démarrer la surveillance
watcher.start(poll_interval=1.0)

# Arrêter
watcher.stop()
```

### Context Manager
```python
from ghostapi.hotreload import FunctionReloader

with FunctionReloader("my_module", "my_function") as reloader:
    # La fonction se rechargera automatiquement
    result = my_function()
```

### Décorateur @hot_reload
```python
from ghostapi.hotreload import hot_reload

@hot_reload("my_module")
def my_function():
    return "Données"
```

### Integration FastAPI
```python
from ghostapi.hotreload import setup_hot_reload
from ghostapi import expose

app = expose(hot_reload_module="my_module")
watcher = setup_hot_reload(app, "my_module")
```

---

## 🔐 OAuth2 / Social Login

Support pour Google, GitHub et Discord.

### Configuration
```python
from ghostapi.auth.oauth import OAuthConfig, setup_oauth

oauth_config = OAuthConfig(
    google_client_id="your-google-client-id",
    google_client_secret="your-google-client-secret",
    github_client_id="your-github-client-id",
    github_client_secret="your-github-client-secret",
    discord_client_id="your-discord-client-id",
    discord_client_secret="your-discord-client-secret"
)

router = setup_oauth(app, oauth_config)
```

### Variables d'Environnement
```bash
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
DISCORD_CLIENT_ID=...
DISCORD_CLIENT_SECRET=...
OAUTH_CALLBACK_URL=/api/auth/oauth/callback
```

---

## 📋 Audit Logs Automatiques

Journalisation de tous les accès aux routes sécurisées.

### Configuration
```python
from ghostapi.auth.audit import AuditLogger, create_audit_middleware

audit = AuditLogger(
    storage_path="data/audit_logs.json",
    max_entries=10000,
    retention_days=90
)

# Ajouter le middleware
app.add_middleware(create_audit_middleware(audit))
```

### Types d'Actions
- `LOGIN`, `LOGOUT`, `LOGIN_FAILED`
- `TOKEN_REFRESH`, `TOKEN_REVOKED`
- `ACCESS_DENIED`, `ACCESS_GRANTED`
- `DATA_READ`, `DATA_WRITE`, `DATA_DELETE`

---

## 🚫 Token Blacklist / Revocation

Révocation de tokens JWT avant expiration.

```python
from ghostapi.auth.token_blacklist import get_token_blacklist

blacklist = get_token_blacklist()

# Révoquer un token
blacklist.revoke_token(
    jti="token-id",
    user_id="user-456",
    expires_at=datetime.utcnow() + timedelta(hours=1),
    reason="logout"
)

# Vérifier si révoqué
if blacklist.is_revoked("token-id"):
    raise HTTPException(status_code=401)

# Révoquer tous les tokens d'un utilisateur
blacklist.revoke_all_user_tokens("user-456", reason="password_change")
```

---

## 💾 Caching Distribué (Redis/Memcached)

Cache distribué pour les endpoints exposés publiquement.

### Redis
```python
from ghostapi.distributed_cache import RedisCache

cache = RedisCache(
    host="localhost",
    port=6379,
    password="secret",
    db=0,
    prefix="ghostapi:"
)
```

### Memcached
```python
from ghostapi.distributed_cache import MemcachedCache

cache = MemcachedCache(
    servers=["localhost:11211"],
    prefix="ghostapi_"
)
```

### Factory
```python
from ghostapi.distributed_cache import create_distributed_cache, CacheBackend

cache = create_distributed_cache(
    backend=CacheBackend.REDIS,
    host="localhost",
    port=6379
)
```

---

## ⚡ Rate Limit Avancé (Par User/Token/Rôle)

Limitation de débit par utilisateur, token ou rôle.

### Configuration
```python
from ghostapi.rate_limit_advanced import AdvancedRateLimiter, RateLimitScope

limiter = AdvancedRateLimiter()
limiter.add_rule("default", max_calls=60, period=60)
limiter.add_rule("premium", max_calls=1000, period=60, scope=RateLimitScope.USER)
```

### Rate Limit par Rôle
```python
from ghostapi.rate_limit_advanced import RoleRateLimiter

role_limiter = RoleRateLimiter()
role_limiter.set_limit("admin", 1000, 60)
role_limiter.set_limit("user", 100, 60)
role_limiter.set_limit("guest", 10, 60)
```

---

## 🔄 File d'Attente de Tâches Asynchrones

Support Celery et RQ pour les tâches en arrière-plan.

### Utilisation Simple
```python
from ghostapi.tasks import task, AsyncRunner

@task
def generate_report(data):
    # Traite en arrière-plan
    return create_report(data)

# Lancer la tâche
job = generate_report.delay(data)
```

### Async Runner
```python
from ghostapi.tasks import AsyncRunner

runner = AsyncRunner()

# Enqueue une tâche
job = runner.enqueue(generate_report, data)

# Obtenir le résultat
result = runner.get_result(job.id)

# Attendre le résultat
result = runner.wait_for_result(job.id, timeout=30)
```

---

## 📊 Monitoring / Prometheus

Monitoring des performances avec export Prometheus.

### Configuration
```python
from ghostapi.monitoring import setup_monitoring

app = setup_monitoring(app)
```

### Endpoints
- `GET /metrics` - Métriques Prometheus
- `GET /profile` - Rapport de profiling

### Métriques Disponibles
```
ghostapi_requests_total{method="GET", endpoint="/users", status="200"}
ghostapi_request_duration_seconds{method="GET", endpoint="/users"}
```

---

## ⏱️ Profiling Automatique

Mesure automatique du temps d'exécution des fonctions.

### Utilisation
```python
from ghostapi.monitoring import PerformanceProfiler

profiler = PerformanceProfiler()
profiler.start()

# Avec décorateur
@profiler.profile()
def expensive_function():
    return compute()

# Avec context manager
from ghostapi.monitoring import profile_block

with profile_block("database_query"):
    result = db.query()

# Obtenir le rapport
report = profiler.get_report()
print(profiler.export_report())

---

---

## 🌍 Internationalisation (i18n)

Support multi-langue pour les messages d'erreurs et les docstrings Swagger.

### Langues Supportées
- 🇫🇷 Français (fr)
- 🇬🇧 Anglais (en)
- 🇪🇸 Espagnol (es)

### Détection Automatique

La langue est automatiquement détectée depuis l'en-tête `Accept-Language` :

```python
from ghostapi.i18n import I18nMiddleware, get_i18n_manager

# Middleware de détection automatique
app.add_middleware(I18nMiddleware)
```

### Utilisation des Messages d'Erreur

```python
from ghostapi.i18n import (
    get_error_message,
    field_required,
    invalid_email,
    invalid_credentials
)

# Message simple
msg = get_error_message("field_required", field="email")

# Fonctions utilitaires
msg = field_required("username")
msg = invalid_email("email")
msg = invalid_credentials()
```

### Messages d'Erreur Traduits

| Clé | Français | Anglais | Espagnol |
|-----|----------|---------|----------|
| `field_required` | Le champ '{field}' est requis. | Field '{field}' is required. | El campo '{field}' es requerido. |
| `invalid_email` | doit être une adresse email valide | must be a valid email address | debe ser una dirección de correo válida |
| `invalid_credentials` | Email ou mot de passe invalide. | Invalid email or password. | Email o contraseña inválidos. |
| `access_denied` | Accès refusé. | Access denied. | Acceso denegado. |
| `rate_limit_exceeded` | Limite de requêtes dépassée. | Rate limit exceeded. | Límite de solicitudes excedido. |

### Docstrings pour Swagger

```python
from ghostapi.i18n import get_docstring

# Obtenir une docstring traduite
title = get_docstring("Authentication")  # "Authentification"
label = get_docstring("Login")          # "Connexion"
```

### Décorateur @translated_docstring

```python
from ghostapi.i18n import translated_docstring

@translated_docstring("Description")
def my_endpoint():
    '''This will be translated'''
    pass
```

### Configuration Manuelle

```python
from ghostapi.i18n import set_language, Language

# Définir une langue spécifique
set_language(Language.FRENCH)

# Obtenir le manager
from ghostapi.i18n import get_i18n_manager
manager = get_i18n_manager()
manager.set_language(Language.SPANISH)
```

### Messages Personnalisés

```python
manager = get_i18n_manager()
manager.add_custom_message(
    Language.FRENCH,
    "welcome_message",
    "Bienvenue sur notre API!"
)
```

---

## 🔌 Système de Plugins / Extensibilité

GhostAPI dispose d'un système de plugins puissant pour étendre les fonctionnalités.

### Architecture des Plugins

```python
from ghostapi.plugins import (
    Plugin,
    PluginMetadata,
    StoragePlugin,
    ValidationPlugin,
    DecoratorPlugin,
    PluginRegistry,
    register_plugin,
    get_plugin_registry
)
```

### Création d'un Plugin

```python
from ghostapi.plugins import Plugin, PluginMetadata

class MyCustomPlugin(Plugin):
    def __init__(self, config=None):
        super().__init__(config)
    
    def get_metadata(self):
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            author="Your Name",
            description="Description du plugin"
        )
    
    def on_load(self, app):
        print("Plugin chargé!")
    
    def on_unload(self):
        print("Plugin déchargé!")

# Enregistrer le plugin
register_plugin(MyCustomPlugin())
```

### Plugins de Stockage Personnalisés

Créez vos propres stratégies de stockage :

```python
from ghostapi.plugins import StoragePlugin, PluginMetadata

class CustomStoragePlugin(StoragePlugin):
    def __init__(self, config=None):
        super().__init__(config)
        self._data = {}
    
    def get_metadata(self):
        return PluginMetadata("custom_storage", "1.0.0", "author")
    
    def on_load(self, app):
        pass
    
    def on_unload(self):
        pass
    
    def get(self, key):
        return self._data.get(key)
    
    def set(self, key, value):
        self._data[key] = value
    
    def delete(self, key):
        return self._data.pop(key, None) is not None
    
    def clear(self):
        self._data.clear()
    
    def get_all(self):
        return self._data.copy()
```

### Plugins de Validation Personnalisés

Ajoutez vos propres types de validation :

```python
from ghostapi.plugins import ValidationPlugin, PluginMetadata

class PhoneValidationPlugin(ValidationPlugin):
    def get_metadata(self):
        return PluginMetadata("phone_validation", "1.0.0", "author")
    
    def on_load(self, app):
        pass
    
    def on_unload(self):
        pass
    
    def validate(self, value):
        import re
        pattern = r'^\+?[1-9]\d{1,14}

### Générateur de Tests Basé sur les Types

Génère automatiquement des tests unitaires pour toutes les fonctions publiques basées sur les annotations de type.

```python
from ghostapi.test_generator import AutoTestGenerator, TypeTestGenerator

# Générateur automatique
generator = AutoTestGenerator()

# Définir une fonction avec des annotations de type
def add(x: int, y: int) -> int:
    return x + y

# Générer des cas de test
test_cases = generator.generate_tests(add, max_cases=10)

# Exécuter les tests
results = generator.run_tests(add, test_cases)
print(f"Tests réussis: {results['passed']}/{results['total']}")
```

### Générateur de Code de Test Pytest

Génère du code pytest prêt à l'emploi.

```python
# Générer le code du test
code = generator.generate_test_code(add)
print(code)
```

Génère :
```python
import pytest

def test_add():
    result = add(0, 1)
    assert isinstance(result, int)
    assert result == 1

def test_add_negative():
    result = add(-1, -1)
    assert isinstance(result, int)
```

### Générateur de Données Fictives (Mock Data)

Génère automatiquement des données fictives pour tester Swagger/ReDoc.

```python
from ghostapi.test_generator import MockDataGenerator

generator = MockDataGenerator()

# Définir un schéma
schema = {
    "id": "int",
    "name": "str",
    "email": "str",
    "age": "int",
    "active": "bool"
}

# Générer un objet
data = generator.generate_for_schema(schema)
print(data)
# {'id': 0, 'name': 'test', 'email': 'test@example.com', 'age': 18, 'active': True}

# Générer une liste d'objets
users = generator.generate_list(schema, count=5)
```

### Instance Globale

Des instances globales sont disponibles pour une utilisation facile :

```python
from ghostapi.test_generator import get_test_generator, get_mock_generator

# Instance globale du générateur de tests
test_gen = get_test_generator()

# Instance globale du générateur de mock
mock_gen = get_mock_generator()
```

### Types Supportés

| Type | Valeurs générées |
|------|------------------|
| `int` | 0, 1, -1, 42 |
| `str` | "test", "hello", "example" |
| `bool` | True, False |
| `float` | 0.0, 1.5, -1.0 |
| `list` | [], [1, 2, 3] |
| `dict` | {}, {"key": "value"} |
```

        return bool(re.match(pattern, str(value)))
    
    def get_error_message(self, field_name, value):
        return f"Le champ '{field_name}' doit être un numéro de téléphone valide."
```

### Plugins de Décorateurs Personnalisés

Créez des décorateurs réutilisables :

```python
from ghostapi.plugins import DecoratorPlugin, PluginMetadata

class CacheDecoratorPlugin(DecoratorPlugin):
    def get_metadata(self):
        return PluginMetadata("cache_decorator", "1.0.0", "author")
    
    def on_load(self, app):
        pass
    
    def on_unload(self):
        pass
    
    def create_decorator(self, ttl=300):
        cache = {}
        
        def decorator(func):
            def wrapper(*args, **kwargs):
                import time
                key = str(args)
                
                if key in cache:
                    cached_time, cached_value = cache[key]
                    if time.time() - cached_time < ttl:
                        return cached_value
                
                result = func(*args, **kwargs)
                cache[key] = (time.time(), result)
                return result
            
            return wrapper
        return decorator
```

### Enregistrement et Gestion des Plugins

```python
from ghostapi.plugins import get_plugin_registry

registry = get_plugin_registry()

# Lister tous les plugins
plugins = registry.list_plugins()

# Activer/Désactiver un plugin
registry.disable_plugin("my_plugin")
registry.enable_plugin("my_plugin")

# Supprimer un plugin
registry.unregister("my_plugin")
```

---

## 🔧 Middleware Personnalisable

Injectez votre propre middleware global pour le logging, les métriques, ou la sécurité.

### Enregistrer du Middleware Personnalisé

```python
from ghostapi.plugins import add_custom_middleware, get_middleware_registry

# Créer un middleware ASGI
async def logging_middleware(scope, receive, send):
    print(f"Requête: {scope['method']} {scope['path']}")
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [[b"content-type", b"application/json"]],
    })
    await send({
        "type": "http.response.body",
        "body": b'{"message": "OK"}',
    })

# L'ajouter à l'application
add_custom_middleware(logging_middleware, position="first")

# Ou utiliser le registre
registry = get_middleware_registry()
registry.add_middleware(logging_middleware, position="last")
```

### Middleware de Métriques Personnalisé

```python
async def metrics_middleware(scope, receive, send):
    import time
    start_time = time.time()
    
    # Traiter la requête
    await receive()
    
    # Calculer la durée
    duration = time.time() - start_time
    print(f"Durée: {duration:.3f}s")
    
    await send({...})

add_custom_middleware(metrics_middleware)
```

### Middleware de Sécurité Personnalisé

```python
async def security_middleware(scope, receive, send):
    # Vérifier les headers de sécurité
    headers = dict(scope.get("headers", []))
    
    # Ajouter des headers de sécurité
    response_headers = [
        [b"X-Content-Type-Options", b"nosniff"],
        [b"X-Frame-Options", b"DENY"],
        [b"X-XSS-Protection", b"1; mode=block"],
    ]
    
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": response_headers,
    })

add_custom_middleware(security_middleware)
```

### Gestion du Middleware

```python
registry = get_middleware_registry()

# Obtenir tout le middleware
all_middleware = registry.get_middleware()

# Supprimer du middleware
registry.remove_middleware(logging_middleware)

# Tout effacer
registry.clear()
```

---

## 🧪 Tests / QA Automatiques

Génération automatique de tests unitaires et de données fictives pour tester votre API.

### Générateur de Tests Basé sur les Types

Génère automatiquement des tests unitaires pour toutes les fonctions publiques basées sur les annotations de type.

```python
from ghostapi.test_generator import AutoTestGenerator, TypeTestGenerator

# Générateur automatique
generator = AutoTestGenerator()

# Définir une fonction avec des annotations de type
def add(x: int, y: int) -> int:
    return x + y

# Générer des cas de test
test_cases = generator.generate_tests(add, max_cases=10)

# Exécuter les tests
results = generator.run_tests(add, test_cases)
print(f"Tests réussis: {results['passed']}/{results['total']}")
```

### Générateur de Code de Test Pytest

Génère du code pytest prêt à l'emploi.

```python
# Générer le code du test
code = generator.generate_test_code(add)
print(code)
```

Génère :
```python
import pytest

def test_add():
    result = add(0, 1)
    assert isinstance(result, int)
    assert result == 1

def test_add_negative():
    result = add(-1, -1)
    assert isinstance(result, int)
```

### Générateur de Données Fictives (Mock Data)

Génère automatiquement des données fictives pour tester Swagger/ReDoc.

```python
from ghostapi.test_generator import MockDataGenerator

generator = MockDataGenerator()

# Définir un schéma
schema = {
    "id": "int",
    "name": "str",
    "email": "str",
    "age": "int",
    "active": "bool"
}

# Générer un objet
data = generator.generate_for_schema(schema)
print(data)
# {'id': 0, 'name': 'test', 'email': 'test@example.com', 'age': 18, 'active': True}

# Générer une liste d'objets
users = generator.generate_list(schema, count=5)
```

### Instance Globale

Des instances globales sont disponibles pour une utilisation facile :

```python
from ghostapi.test_generator import get_test_generator, get_mock_generator

# Instance globale du générateur de tests
test_gen = get_test_generator()

# Instance globale du générateur de mock
mock_gen = get_mock_generator()
```

### Types Supportés

| Type | Valeurs générées |
|------|------------------|
| `int` | 0, 1, -1, 42 |
| `str` | "test", "hello", "example" |
| `bool` | True, False |
| `float` | 0.0, 1.5, -1.0 |
| `list` | [], [1, 2, 3] |
| `dict` | {}, {"key": "value"} |
```

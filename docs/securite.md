# Guide de sécurité GhostAPI

## Table des matières

1. [Aperçu](#aperçu)
2. [Configuration production](#configuration-production)
3. [Authentification](#authentification)
4. [Protection des données](#protection-des-données)
5. [Headers de sécurité](#headers-de-sécurité)
6. [Rate limiting](#rate-limiting)
7. [Cache sécurisé](#cache-sécurisé)
8. [Bonnes pratiques](#bonnes-pratiques)

---

## Aperçu

GhostAPI intègre plusieurs fonctionnalités de sécurité :

- ✅ Authentification JWT
- ✅ Hachage bcrypt
- ✅ Validation des données
- ✅ Rate limiting
- ✅ Security headers
- ✅ Cache sécurisé avec TTL
- ✅ Masquage des erreurs en production

---

## Configuration production

### 1. Clé secrète

**Obligatoire** : Définissez une clé secrète robuste.

```python
import os
os.environ["GHOSTAPI_SECRET"] = "votre-cle-secrete-très-longue-et-complexe-12345"
```

Ou via variable d'environnement :

```bash
export GHOSTAPI_SECRET="votre-cle-secrete-très-longue-et-complexe-12345"
```

### 2. Mode debug

Désactivez le mode debug en production :

```python
expose(debug=False)  # Production
expose(debug=True)   # Développement uniquement
```

### 3. Configuration minimale recommandée

```python
expose(
    auth=True,
    debug=False,
    secret=os.environ.get("GHOSTAPI_SECRET"),
    rate_limit=60,  # Limite les abus
    cors_origins=["https://votre-site.com"],
    cache_enabled=True,  # Cache pour réduire la charge
    health_check=True    # Monitoring
)
```

---

## Authentification

### Mot de passe

Le mot de passe doit contenir :
- Minimum 8 caractères
- Au moins une majuscule
- Au moins une minuscule
- Au moins un chiffre

```python
# Valide
"Password123"

# Invalide
"password"     # Pas de majuscule
"PASSWORD"     # Pas de minuscule
"Pass123"      # Trop court
"password123"  # Pas de majuscule
```

### Rôles

Trois rôles disponibles avec hiérarchie :

```
admin → moderator → user → guest
```

- **admin** : Accès total
- **moderator** : Modération
- **user** : Accès standard
- **guest** : Accès limité

### Token JWT

Les tokens expirent après 30 minutes par défaut.

```python
# Personnaliser l'expiration
expose(auth=True, expire_minutes=60)  # 1 heure
```

---

## Protection des données

### Stockage

**En mémoire** (défaut) : Les données sont perdues au redémarrage.

```python
expose(storage_backend="memory")
```

**Fichier** : Les données persistent.

```python
expose(storage_backend="file", storage_file="data.json")
```

**Bufferisé** : Meilleures performances pour les écritures fréquentes.

```python
expose(storage_backend="buffered", storage_file="data.json")
```

⚠️ **Attention** : Le fichier de données contient les mots de passe hachés. Protégez-le !

### Hachage

Les mots de passe sont hachés avec bcrypt (12 rounds).

```python
from ghostapi.auth.security import get_password_hash, verify_password

# Hachage
hashed = get_password_hash("Password123")

# Vérification
verify_password("Password123", hashed)  # True
```

---

## Headers de sécurité

GhostAPI ajoute automatiquement ces headers :

| Header | Valeur | Protection |
|--------|--------|------------|
| `X-Content-Type-Options` | `nosniff` | MIME sniffing |
| `X-Frame-Options` | `DENY` | Clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS |
| `Strict-Transport-Security` | `max-age=31536000` | HSTS |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Vie privée |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` | Permissions |

---

## Rate limiting

Le rate limiting limite le nombre de requêtes par IP.

```python
# 60 requêtes par minute (défaut)
expose(rate_limit=60)

# Plus strict
expose(rate_limit=30)

# Désactiver
expose(rate_limit=0)
```

### Réponses

Quand la limite est dépassée :

```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

---

## Cache sécurisé

### Configuration

Le cache intégré permet de réduire la charge sur les ressources sensibles.

```python
expose(
    cache_enabled=True,
    cache_ttl=300  # 5 minutes
)
```

### Cache avec Décorateur

```python
from ghostapi.decorators import cache

@cache(ttl=60)
def get_expensive_data():
    # Ne sera appelé qu'une fois par minute
    return fetch_sensitive_data()
```

### Sécurité du Cache

- TTL (Time To Live) pour expirer les données
- Pas de cache des données sensibles par défaut
- CacheMiddleware pour HTTP avec exclusion des routes sensibles

```python
from ghostapi.cache import add_cache_middleware

add_cache_middleware(
    app,
    ttl=300,
    excluded_paths=["/admin", "/api/auth"],
    methods=["GET"]  # Seulement GET
)
```

---

## Bonnes pratiques

### 1. Toujours utiliser HTTPS

En production, utilisez toujours HTTPS.

```bash
# Avec uvicorn
uvicorn main:app --host 0.0.0.0 --port 443 --ssl-keyfile key.pem --ssl-certfile cert.pem
```

### 2. CORS

Configurez CORS strictement :

```python
# ✓ Bon : Origines spécifiques
expose(cors_origins=["https://votre-site.com"])

# ✗ Éviter : Toutes les origines
expose(cors_origins=["*"])
```

### 3. Logging

Surveillez les logs en production :

```python
# Les erreurs sont logged automatiquement
# Utilisez un outil comme ELK ou Datadog
```

### 4. Rotation des tokens

Les tokens expirent automatiquement. Vérifiez régulièrement les logs d'authentification.

### 5. Validation des entrées

Ne faites pas confiance aux entrées utilisateur :

```python
from fastapi import HTTPException

def create_user(name: str, email: str):
    if len(name) > 100:
        raise HTTPException(400, "Name too long")
    if len(email) > 254:
        raise HTTPException(400, "Email too long")
    # ...
```

### 6. Limiter les données sensibles

Ne retournez jamais de mots de passe dans les réponses :

```python
# ✓ Bon
return {"id": 1, "email": "user@example.com"}

# ✗ Mauvais
return {"id": 1, "password": "..."}
```

### 7. Monitoring avec Health Check

Utilisez les endpoints de health pour le monitoring :

```python
expose(health_check=True)

# GET /health      - Status global
# GET /health/ready - Readiness (Kubernetes)
# GET /health/live  - Liveness (Kubernetes)
```

---

## Checklist sécurité

Avant de mettre en production :

- [ ] Clé secrète définie via `GHOSTAPI_SECRET`
- [ ] `debug=False`
- [ ] CORS configuré avec vos domaines
- [ ] Rate limiting activé
- [ ] HTTPS activé
- [ ] Logs surveillés
- [ ] Données sensibles protégés
- [ ] Health check activé pour monitoring
- [ ] Tests de sécurité passés

---

## Troubleshooting

### Avertissements de sécurité

Si vous voyez :
```
⚠️ SECURITY WARNING: You are using the default secret key!
```

**Action** : Définissez immédiatement une clé secrète.

### Erreurs d'authentification

1. Vérifiez le token n'est pas expiré
2. Vérifiez le format `Bearer <token>`
3. Vérifiez la route nécessite l'auth

### Rate limit

Si vous atteignez la limite :
- Attendez 1 minute
- Augmentez la limite si nécessaire
- Investiguer les abus potentiels

### Cache

Si le cache ne fonctionne pas :
- Vérifiez que `cache_enabled=True`
- Vérifiez le TTL configuré
- Utilisez `clear_cache()` pour vider

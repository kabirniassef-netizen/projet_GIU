# 📡 Documentation API Avancée

## Authentification

### 1. Obtenir un Token (À implémenter)

**Endpoint:** `POST /api/token/`

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Réponse:**
```json
{
  "token": "abc123def456..."
}
```

### 2. Utiliser le Token

Ajouter le header à chaque requête:
```
Authorization: Token abc123def456...
```

## Format des Réponses

### Succès (200-201)
```json
{
  "id": 1,
  "field": "value",
  "timestamp": "2026-06-30T12:00:00Z"
}
```

### Erreur (400)
```json
{
  "error": "Description de l'erreur"
}
```

### Non Autorisé (401)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Exemples d'Utilisation

### 1. Créer un Incident

```bash
curl -X POST http://localhost:8000/api/incidents/incidents/ \
  -H "Authorization: Token votre_token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Accident près du marché",
    "description": "Collision observée vers 14 h, circulation ralentie.",
    "category": 13,
    "address": "Route nationale, près du marché central",
    "region": "Dakar",
    "department": "Dakar",
    "commune": "Dakar"
  }'
```

Un citoyen connecté peut envoyer le formulaire depuis le bouton « Signaler un incident ». Il est redirigé vers la connexion ou la création d’un compte si nécessaire. Choisissez la catégorie « Accident de la route », indiquez le point de repère précis dans `address` et renseignez la région, le département et la commune. Une photo est facultative et limitée à 5 Mio. Utilisez `GET /api/incidents/categories/` pour récupérer les identifiants de catégories ; les identifiants peuvent varier entre les bases. Pour joindre une photo via l’API, envoyez les champs en `multipart/form-data`.

Un citoyen sans compte peut aussi signaler depuis son téléphone sur `/signaler/`, sans fournir de coordonnées personnelles. Le formulaire demande la région, le département et la commune pour localiser l’incident; une photo est facultative. L’endpoint public `POST /api/incidents/public/` accepte également une adresse dans le champ `address`. Les catégories sont consultables sans authentification avec `GET /api/incidents/categories/`. Les signalements publics sont limités à 20 envois par heure et par adresse IP.

```bash
curl -X POST http://localhost:8000/api/incidents/public/ \
  -F "title=Accident près du marché" \
  -F "description=Collision observée, circulation ralentie." \
  -F "category=13" \
  -F "address=Route nationale, près du marché central" \
  -F "region=Dakar" \
  -F "department=Dakar" \
  -F "commune=Dakar"
```

### 2. Lister les Incidents

```bash
curl http://localhost:8000/api/incidents/incidents/ \
  -H "Authorization: Token votre_token"
```

Avec filtrage par statut:
```bash
curl "http://localhost:8000/api/incidents/incidents/by_status/?status=created" \
  -H "Authorization: Token votre_token"
```

### 3. Mettre à jour le Statut d'un Incident

```bash
curl -X POST http://localhost:8000/api/incidents/incidents/1/update_status/ \
  -H "Authorization: Token votre_token" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "validated",
    "comment": "Incident validé et planifié"
  }'
```

### 4. Créer une Intervention

```bash
curl -X POST http://localhost:8000/api/interventions/interventions/ \
  -H "Authorization: Token votre_token" \
  -H "Content-Type: application/json" \
  -d '{
    "incident": 1,
    "assigned_to": 2,
    "scheduled_date": "2026-07-01T10:00:00Z",
    "estimated_duration": 120,
    "priority": "high",
    "notes": "Prévoir de la macadam"
  }'
```

### 5. Consulter le Dashboard

```bash
curl http://localhost:8000/api/reports/reports/global_statistics/ \
  -H "Authorization: Token votre_token"
```

Réponse:
```json
{
  "total_incidents": 12,
  "resolved_incidents": 8,
  "pending_incidents": 2,
  "total_interventions": 10,
  "completed_interventions": 8,
  "total_assets": 150,
  "operational_assets": 145,
  "avg_resolution_time": 24.5,
  "asset_availability_rate": 96.67
}
```

### 6. Notifications personnelles

Lister les notifications de l’utilisateur connecté :

```bash
curl http://localhost:8000/api/notifications/ \
  -H "Authorization: Token votre_token"
```

Marquer une notification comme lue :

```bash
curl -X PATCH http://localhost:8000/api/notifications/1/ \
  -H "Authorization: Token votre_token" \
  -H "Content-Type: application/json" \
  -d '{"is_read": true}'
```

Chaque utilisateur ne peut consulter et modifier que ses propres notifications. Les signalements utilisent une adresse composée de la région, du département et de la commune (sans coordonnées GPS) ; les coordonnées des actifs doivent respecter les bornes GPS. Les photos d’incident sont limitées à 5 Mio. Les changements de statut suivent des transitions autorisées et sont historisés avec leur auteur.

## Pagination

Les listes sont paginées par défaut (50 items par page):

```bash
curl "http://localhost:8000/api/incidents/incidents/?page=2" \
  -H "Authorization: Token votre_token"
```

## Recherche et Filtrage

```bash
# Filtrer par statut
curl "http://localhost:8000/api/incidents/incidents/?status=resolved"

# Rechercher par titre
curl "http://localhost:8000/api/incidents/incidents/?search=lampadaire"

# Ordonner les résultats
curl "http://localhost:8000/api/incidents/incidents/?ordering=-created_at"
```

## Cas d'Utilisation Courants

### Workflow Complet: Citoyen → Résolution

```bash
# 1. Citoyen crée un incident
INCIDENT_ID=$(curl -X POST http://localhost:8000/api/incidents/incidents/ \
  -H "Authorization: Token citoyen_token" \
  -H "Content-Type: application/json" \
  -d '{...}' | jq '.id')

# 2. Manager valide
curl -X POST http://localhost:8000/api/incidents/incidents/$INCIDENT_ID/update_status/ \
  -H "Authorization: Token manager_token" \
  -H "Content-Type: application/json" \
  -d '{"status": "validated"}'

# 3. Manager crée une intervention
curl -X POST http://localhost:8000/api/interventions/interventions/ \
  -H "Authorization: Token manager_token" \
  -H "Content-Type: application/json" \
  -d '{...}'

# 4. Agent met à jour
curl -X POST http://localhost:8000/api/interventions/interventions/1/update_status/ \
  -H "Authorization: Token agent_token" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "comment": "Réparé"}'

# 5. Citoyen vérifie via API
curl http://localhost:8000/api/incidents/incidents/$INCIDENT_ID/ \
  -H "Authorization: Token citoyen_token"
```

## Gestion des Erreurs

### Validations Communes

**Champ obligatoire manquant:**
```json
{
  "title": ["This field may not be blank."]
}
```

**Valeur de champ invalide:**
```json
{
  "category": ["Invalid pk - object does not exist."]
}
```

**Pas d'autorisation:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

## Bonnes Pratiques

1. **Toujours utiliser HTTPS en production**
2. **Ne pas exposer les tokens en URL**
3. **Implémenter la cache pour les statistiques**
4. **Valider les entrées côté client**
5. **Limiter le rate limiting si nécessaire**
6. **Utiliser les filtres pour optimiser les requêtes**
7. **Logger les erreurs d'API**
8. **Tester avec des outils comme Postman**

## Rate Limiting (À implémenter)

Actuellement pas de limite de taux, à ajouter en production:
```python
# À ajouter dans settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

## Webhooks (À implémenter)

Système de notifications pour les changements d'état:
```python
# POST à une URL externe quand un incident change de statut
POST https://votre-app.com/webhook/incident-updated
{
  "event": "incident.updated",
  "incident_id": 1,
  "old_status": "created",
  "new_status": "validated",
  "timestamp": "2026-06-30T12:00:00Z"
}
```

---

**Dernière mise à jour:** 2026-06-30  
**Version API:** 1.0.0

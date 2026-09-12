# 📡 Documentation API Avancée

## Authentification

### 1. Obtenir un Token

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
    "title": "Nid-de-poule rue de la Paix",
    "description": "Grande dégradation de la chaussée",
    "category": "road",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "address": "Rue de la Paix, 75000 Paris",
    "priority": "high"
  }'
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

---

**Dernière mise à jour:** 2026-06-30  
**Version API:** 1.0.0

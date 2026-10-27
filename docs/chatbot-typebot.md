# Chatbot de signalement (Typebot open source)

Le chatbot permet aux citoyens de **signaler un incident** et de **suivre un signalement**
par conversation, depuis une bulle affichée sur l'accueil, `/signaler/` et `/suivi/`.

On utilise la version open source de Typebot, **auto-hébergée** avec Docker
(`deploy/typebot/`) : aucune donnée ne passe par typebot.io. Typebot comprend deux
applications : l'**éditeur** (builder, port 8080) où l'on construit le bot, et le
**lecteur** (viewer, port 8081) qui l'exécute et que la bulle du site interroge.

## 1. Lancer Typebot

```bash
cd deploy/typebot
cp .env.example .env      # PowerShell : Copy-Item .env.example .env
# compléter .env : mots de passe, ENCRYPTION_SECRET, ADMIN_EMAIL, identifiants SMTP Brevo
docker compose up -d
```

- Éditeur : http://localhost:8080 — se connecter avec `ADMIN_EMAIL` ; le lien de
  connexion arrive par e-mail (d'où le SMTP). Les identifiants SMTP se trouvent dans
  Brevo → *SMTP & API* → onglet *SMTP*.
- Lecteur : http://127.0.0.1:8081
- Arrêt : `docker compose down` (les données restent dans le volume `typebot-db-data`).

## 2. Côté application

| Variable           | Rôle                                                                 |
|--------------------|----------------------------------------------------------------------|
| `TYPEBOT_ID`       | Identifiant public du bot (Share → Embed). Vide = pas de bulle.      |
| `TYPEBOT_API_HOST` | Adresse du lecteur (viewer), `http://127.0.0.1:8081` en local.       |
| `CHATBOT_API_KEY`  | Clé secrète que le bot envoie dans l'en-tête `X-Chatbot-Key`.        |
| `CHATBOT_THROTTLE_RATE` | Quota du bot, `300/hour` par défaut.                            |

Générer une clé : `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

Pourquoi une clé : les requêtes HTTP du bot partent toutes du viewer, donc d'une même
adresse IP. Sans clé, tous les citoyens passant par le bot se partageraient
la limite anonyme de 20 requêtes par heure.

Sur Render, renseigner `TYPEBOT_ID`, `TYPEBOT_API_HOST` et `CHATBOT_API_KEY` dans
*Environment*, puis redéployer.

## 3. Créer le bot dans l'éditeur

Dans l'éditeur (http://localhost:8080), créer un bot vide, puis les variables :
`choix`, `liste_categories`, `liste_ids`, `categorie`, `categorie_id`, `titre`, `description`, `region`,
`departement`, `commune`, `adresse`, `code`, `reponse`.

Pour chaque bloc **HTTP request**, ajouter l'en-tête `X-Chatbot-Key` avec la valeur de
`CHATBOT_API_KEY`. URL de base de l'API :

- en local : `http://giu-api:8000` (le viewer tourne dans Docker et `giu-api` y désigne la
  machine ; ajouter `giu-api` à `ALLOWED_HOSTS` dans le `.env` de Django, et garder
  `SSRF_ALLOWED_HOSTS=giu-api` dans `deploy/typebot/.env`). Ne pas utiliser
  `host.docker.internal` : Typebot refuse son adresse IPv6 privée ;
- en production : `https://giu-signalements.onrender.com`.

### Accueil

1. Texte : « Bonjour ! En cas de blessé ou de danger immédiat, appelez d'abord les secours. »
2. Boutons → `choix` : **Signaler un incident** / **Suivre un signalement**.

### Branche « Signaler un incident »

1. HTTP request `GET /api/incidents/categories/`. Dans *Save in variables*, deux entrées :
   `liste_categories` ← `data.results.map(c => c.name_display)` et
   `liste_ids` ← `data.results.map(c => c.id)`.
2. Bloc Boutons avec *Dynamic items* = `liste_categories` ; le choix est enregistré dans
   `categorie`.
3. Set variable `categorie_id`, type *Map item with same index* : élément `categorie`,
   liste de départ `liste_categories`, liste cible `liste_ids`.
4. Questions texte → `titre` (court), `description`, `region`, `departement`, `commune`,
   `adresse` (facultatif).
5. HTTP request `POST /api/incidents/public/`, corps JSON :

   ```json
   {
     "title": "{{titre}}",
     "description": "{{description}}",
     "category": {{categorie_id}},
     "region": "{{region}}",
     "department": "{{departement}}",
     "commune": "{{commune}}",
     "address": "{{adresse}}"
   }
   ```

   Enregistrer `data.tracking_code` dans `code`.
6. Condition : si `code` est vide → « Le signalement n'a pas pu être enregistré, réessayez
   ou utilisez le formulaire /signaler/ ». Sinon → « Merci ! Votre code de suivi est
   **{{code}}**. Conservez-le pour suivre le traitement. »

La photo n'est pas gérée par le bot : renvoyer vers `/signaler/` si le citoyen veut en joindre une.

### Branche « Suivre un signalement »

1. Question texte → `code` (« Entrez votre code, par exemple GIU-AB12CD34 »).
2. HTTP request `GET /api/incidents/track/{{code}}/` ; enregistrer `data.status_display`
   dans `reponse`.
3. Condition : `reponse` vide → « Code introuvable, vérifiez-le. » Sinon →
   « Votre signalement est actuellement : **{{reponse}}**. Détails : /suivi/?code={{code}} ».

## 4. Publier

Cliquer sur **Publish**, puis *Share* → copier l'identifiant public dans `TYPEBOT_ID`.

## 5. Mise en production

Render (offre gratuite) ne convient pas bien à Typebot : il faut trois services qui
tournent en continu. Le plus simple est un petit serveur (VPS) avec Docker :

1. Copier `deploy/typebot/` sur le serveur et lancer `docker compose up -d`.
2. Mettre un reverse proxy HTTPS (Caddy, Nginx…) devant, par exemple
   `bot-admin.mondomaine.sn` → 8080 et `bot.mondomaine.sn` → 8081.
3. Dans `.env` : `NEXTAUTH_URL=https://bot-admin.mondomaine.sn`,
   `NEXT_PUBLIC_VIEWER_URL=https://bot.mondomaine.sn`, puis remplacer `latest` par une
   version précise des images dans `docker-compose.yml`.
4. Sur Render : `TYPEBOT_API_HOST=https://bot.mondomaine.sn`.

## Variante n8n

Les mêmes appels (`categories`, `public`, `track`) avec l'en-tête `X-Chatbot-Key` se
font avec des nœuds *HTTP Request* n8n, déclenchés par exemple par un *Telegram Trigger*
pour un bot Telegram. La bulle du site reste alors désactivée (`TYPEBOT_ID` vide).

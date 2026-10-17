# État du projet GIU

Le dépôt contient le backend Django, les API, l'interface web et les applications
métier. Ce fichier décrit l'état de préparation observé, pas une certification
de production.

## Environnement local

- Utiliser Python 3.12 ou plus récent et créer `.venv`.
- Installer les dépendances avec `pip install -r requirements.txt`.
- Copier `.env.example` vers `.env`; la configuration locale utilise SQLite.
- Appliquer les migrations avec `python manage.py migrate`.
- Charger les données de démonstration avec `python load_test_data.py`.
- Démarrer le serveur avec `python manage.py runserver`.

Les comptes de démonstration sont réservés au développement. Le script refuse
de les charger quand `DEBUG=False` et ne modifie plus un compte `admin` existant.

## État des validations

- Environnement `.venv` et dépendances: installés et vérifiés.
- Configuration Django locale: `manage.py check` sans erreur.
- Migrations: appliquées à SQLite; la sauvegarde antérieure est conservée dans
  `backups/db-before-migration-20261013.sqlite3`.
- Données de démonstration: chargées.
- Tests: 37 tests API, rôles, parcours métier, admin et notifications réussis.
- `verify_setup.py`: 10/10 vérifications réussies.
- `check --deploy`: exécutée avec des valeurs temporaires; deux avertissements
  HSTS restent à décider selon le domaine et ses sous-domaines (`W005`, `W021`).
  Cela ne vaut pas déploiement ni validation des vrais secrets.
- E-mail/WhatsApp: scénarios testés; l'envoi réel reste à configurer et valider
  auprès des fournisseurs.
- Déploiement: non réalisé.

## Avant une mise en production

1. Générer une `SECRET_KEY` dédiée et définir `DEBUG=False`.
2. Configurer `ALLOWED_HOSTS`, CORS, CSRF, PostgreSQL, SMTP et, si nécessaire,
   WhatsApp à partir de secrets fournis par l'environnement de déploiement.
3. Déployer derrière HTTPS avec un serveur WSGI et un reverse proxy.
4. Configurer les fichiers statiques, sauvegardes, journalisation et supervision.
5. Exécuter `python manage.py check --deploy` et une recette sur l'environnement
   cible avant toute mise en service.

Le dossier racine du dépôt est la version de référence. Le dossier imbriqué
`projet_GIU/` contient son propre dépôt Git et des fichiers qui diffèrent; il
est conservé en attendant une décision sur la préservation de cet historique.

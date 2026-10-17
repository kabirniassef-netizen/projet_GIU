# Explication des diagrammes et de l'architecture du projet

Ce document explique à quoi sert chaque diagramme et comment le lire.

## 1. Diagramme de cas d'utilisation

Cette vue répond à la question : « qui a le droit de faire quoi ? » Les ronds (Citoyen, Agent, Gestionnaire, Décideur, Admin) représentent les acteurs, c'est-à-dire les types d'utilisateurs. Les rectangles (Signaler un incident, Valider, etc.) représentent les actions possibles.

Une ligne pleine entre un acteur et une action signifie que cet acteur peut déclencher cette action. Par exemple, le Citoyen peut signaler et suivre un incident, tandis que le Gestionnaire peut le valider. Ce diagramme décrit les permissions, pas la technique : il aide à définir ce que chaque rôle peut faire dans l'interface.

Les flèches en pointillés vers « Notification » montrent que certaines actions (signaler, valider, créer une intervention...) déclenchent aussi une notification.

## 2. Diagramme de classes

Cette vue répond à la question : « quelles sont les données et comment sont-elles reliées ? » Chaque classe correspond généralement à un modèle Django et à une table ; ses attributs correspondent aux champs.

Un Incident a un `created_by` (qui pointe vers User) et un `status` : c'est l'objet central. Une relation Incident → Intervention avec la cardinalité « 0..1 » signifie qu'un incident peut avoir au plus une intervention. Une relation UrbanAsset → AssetHistory « 1 vers plusieurs » signifie qu'un actif urbain peut avoir plusieurs entrées d'historique. Chaque Notification pointe vers un User destinataire.

Ce diagramme donne une vue de la structure des modèles et de leurs relations `ForeignKey`.

## 3. Diagramme de séquence

Cette vue montre l'ordre chronologique des échanges pour un scénario précis, ici le parcours complet d'un signalement. Chaque flèche horizontale représente un appel (requête HTTP ou événement interne) et le temps s'écoule de haut en bas.

Le citoyen envoie `POST /api/incidents` ; l'API crée l'incident et répond « 201 Créé ». L'API déclenche ensuite une notification vers les gestionnaires. Le gestionnaire valide l'incident, ce qui déclenche une notification au citoyen, puis crée une intervention et l'assigne à un agent, qui est notifié. L'agent prend en charge puis clôture l'intervention, avec les notifications correspondantes. Les indicateurs des rapports sont recalculés en arrière-plan.

Ce diagramme aide à ordonner les appels API et à repérer quand déclencher les notifications, par exemple avec un signal `post_save` lorsque cela convient.

## 4. Diagramme d'architecture

Cette vue décrit les couches techniques, du navigateur jusqu'au stockage des données.

- **Client (navigateur)** : les templates Django, HTML, CSS et JavaScript que l'utilisateur manipule.
- **Présentation** : les pages Django (accueil, connexion, tableau de bord) renvoient du HTML ; l'API REST (`/api/...`) renvoie du JSON.
- **Applications métier** : `users`, `incidents`, `assets`, `interventions` et `reports` regroupent leurs modèles, vues et sérialiseurs. Les relations entre données sont représentées notamment par des clés étrangères.
- **Notifications** : ce module centralise les notifications déclenchées par les incidents et les interventions (courriel et notifications dans l'application).
- **Base de données** : PostgreSQL stocke les données applicatives.

Le flux principal va de la présentation aux applications métier, puis à la base de données. Cette séparation aide à faire évoluer l'API et les pages sans les confondre.
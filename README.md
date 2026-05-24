Projet Final MongoDB : Plateforme E-Commerce Big Data 
Présentation du Projet
Ce projet a été réalisé dans le cadre du Master 1 IABD (Intelligence Artificielle et Big Data). L'objectif est de concevoir, implémenter et optimiser le backend d'une plateforme e-commerce à forte volumétrie (type Amazon) en utilisant MongoDB
.
Le projet couvre l'intégralité du cycle de vie de la donnée :
Modélisation NoSQL : Choix stratégiques entre Embedding et Referencing
.
Génération Massive : Simulation de millions de documents via Python Faker
.
Analytique Avancée : Pipelines d'agrégation complexes pour le pilotage métier
.
Optimisation : Stratégies d'indexation et analyse des plans d'exécution
.
Préparation IA : Création d'une matrice Utilisateur-Produit et moteur de recommandation
.

--------------------------------------------------------------------------------
🛠️ Technologies utilisées
Base de données : MongoDB (via un conteneur Docker)
.
Langage : Python 3.x.
Librairies : pymongo, faker, tabulate, pprint.
Outils : MongoDB Compass (Profiling), Git (Versionnage).

--------------------------------------------------------------------------------
📂 Structure du projet
.
├── docker-compose.yml     # Configuration de l'infrastructure Docker
├── Master1.py             # Script de peuplement massif (Step 2)
├── queries.py             # Requêtes métier, indexation et IA (Step 3, 4, 5)
├── requirements.txt       # Dépendances Python
└── Rapport_Projet.pdf     # Rapport final 

🚀 Installation et Lancement
1. Cloner le dépôt
git clone <votre-lien-depot-git>
cd projet-mongodb-iabd
2. Lancer l'environnement Docker
Le projet utilise Docker pour garantir la portabilité de l'environnement
.
docker-compose up -d
3. Installer les dépendances Python
Il est recommandé d'utiliser un environnement virtuel.
pip install -r requirements.txt
4. Générer les données (Step 2)
Ce script va insérer plus de 2 millions de commandes et 500 000 produits dans votre base locale
.
python Master1.py
5. Exécuter les analyses et l'IA (Step 3, 4, 5)
Lancer les pipelines d'agrégation et le système de recommandation.
python queries.py

📈 Fonctionnalités Clés
Analyse de Performance (Optimisation)
Le projet démontre le passage d'un COLLSCAN (lent) à un IXSCAN (rapide) grâce à la mise en place d'index simples, composés et textuels
. Les statistiques de performance (executionStats) sont détaillées dans le rapport PDF
.
Cas d'usage IA
User-Item Matrix : Génération d'une collection ia_user_item_matrix pour les algorithmes de filtrage collaboratif
.
Recommandation : Moteur basé sur la co-occurrence d'achats (Market Basket Analysis)
.

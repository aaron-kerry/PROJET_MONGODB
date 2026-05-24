from pymongo import MongoClient
from faker import Faker
import random
import datetime


fake = Faker()

# Connexion à l'instance Docker locale
client = MongoClient("mongodb://localhost:27017/")
db = client["ecommerce_bigdata"]

# 1. SCHÉMA UTILISATEURS
schema_utilisateurs = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["nom", "email", "motDePasse", "adresses"],
        "properties": {
            "nom": {"bsonType": "string"},
            "email": {"bsonType": "string", "pattern": "^.+@.+$"},
            "adresses": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["ville", "pays"],
                    "properties": {
                        "rue": {"bsonType": "string"},
                        "ville": {"bsonType": "string"},
                        "pays": {"bsonType": "string"}
                    }
                }
            },
            "panier_actuel": {"bsonType": "array"},
            "historique_navigation": {"bsonType": "array"}
        }
    }
}

# 2. SCHÉMA PRODUITS
schema_produits = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["nom", "prix", "stock", "categorie"],
        "properties": {
            "nom": {"bsonType": "string"},
            "description": {"bsonType": "string"},
            "prix": {"bsonType": "double"},
            "stock": {"bsonType": "int", "minimum": 0},
            "categorie": {"bsonType": "string"},
            "caracteristiques": {"bsonType": "object"},
            "avis_recents": {"bsonType": "array", "maxItems": 5}
        }
    }
}

# 3. SCHÉMA COMMANDES
schema_commandes = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["client_id", "date", "lignes_commande", "montant_total"],
        "properties": {
            "client_id": {"bsonType": "objectId"},
            "date": {"bsonType": "date"},
            "montant_total": {"bsonType": "double"},
            "lignes_commande": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["produit_id", "nom_snapshot", "prix_achat"],
                    "properties": {
                        "produit_id": {"bsonType": "objectId"},
                        "nom_snapshot": {"bsonType": "string"},
                        "prix_achat": {"bsonType": "double"},
                        "quantite": {"bsonType": "int", "minimum": 1}
                    }
                }
            },
            "etat_livraison": {"enum": ["En cours", "Livré", "Annulé"]}
        }
    }
}

# 4. SCHÉMA AVIS
schema_avis = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["produit_id", "client_id", "note"],
        "properties": {
            "produit_id": {"bsonType": "objectId"},
            "client_id": {"bsonType": "objectId"},
            "note": {"bsonType": "int", "minimum": 1, "maximum": 5},
            "commentaire": {"bsonType": "string"},
            "date": {"bsonType": "date"}
        }
    }
}



# Création des collections avec validation
collections = {
    "utilisateurs": schema_utilisateurs,
    "produits": schema_produits,
    "commandes": schema_commandes,
    "avis": schema_avis
}

for name, schema in collections.items():
    db.create_collection(name, validator=schema)
    print(f"Collection '{name}' configurée avec validation.")

#Configuration des volumes
NB_USERS = 1000000
NB_PRODS = 5000000
NB_COMMANDES = 2000000
NB_AVIS = 1000000
BATCH_SIZE = 5000

def generate_data():
    print("Lancement de la génération massive...")

    prod_ids = [p["_id"] for p in db.produits.find({}, {"_id": 1})]
    user_ids = [u["_id"] for u in db.utilisateurs.find({}, {"_id": 1})]

    # 1. PRODUITS
    prod_ids = []
    categories = ["Électronique", "Mode", "Maison", "Sport", "Livres"]

    for i in range(0, NB_PRODS, BATCH_SIZE):
        batch = []
        for _ in range(BATCH_SIZE):
            p = {
                "nom": fake.catch_phrase(),
                "description": fake.text(max_nb_chars=200),
                "prix": round(random.uniform(10.0, 2000.0), 2),
                "stock": random.randint(0, 1000),
                "categorie": random.choice(categories),
                "caracteristiques": {"marque": fake.company(), "poids": f"{random.randint(1,10)}kg"},
                "avis_recents": []
            }
            batch.append(p)
        res = db.produits.insert_many(batch)
        prod_ids.extend(res.inserted_ids)
        if len(prod_ids) % 50000 == 0:
            print(f"Produits : {len(prod_ids)} insérés")

    # 2. UTILISATEURS
    user_ids = []
    for i in range(0, NB_USERS, BATCH_SIZE):
        batch = []
        for _ in range(BATCH_SIZE):
            u = {
                "nom": fake.name(),
                "email": fake.unique.email(),
                "motDePasse": "hash_secu_123",
                "adresses": [
                    {"rue": fake.street_address(), "ville": fake.city(), "pays": fake.country()}
                    for _ in range(random.randint(1, 2))
                ],
                "panier_actuel": [],
                "historique_navigation": [random.choice(prod_ids[:1000]) for _ in range(5)]
            }
            batch.append(u)
        res = db.utilisateurs.insert_many(batch)
        user_ids.extend(res.inserted_ids)
    print("Utilisateurs terminés.")

    # 3. AVIS
    print("Génération des avis...")
    for i in range(0, NB_AVIS, BATCH_SIZE):
        batch = []
        for _ in range(BATCH_SIZE):
            batch.append({
                "produit_id": random.choice(prod_ids),
                "client_id": random.choice(user_ids),
                "note": random.randint(1, 5),
                "commentaire": fake.sentence(),
                "date": datetime.datetime.combine(fake.date_this_year(), datetime.datetime.min.time())
            })
        db.avis.insert_many(batch)
        if (i + BATCH_SIZE) % 50000 == 0:
            print(f"Avis : {i + BATCH_SIZE} insérés")

    # 4. COMMANDES
    print("Génération des commandes...")
    for i in range(0, NB_COMMANDES, BATCH_SIZE):
        batch = []
        for _ in range(BATCH_SIZE):
            p_ref = db.produits.find_one({"_id": random.choice(prod_ids)})
            batch.append({
                "client_id": random.choice(user_ids),
                "date": datetime.datetime.combine(fake.date_this_year(), datetime.datetime.min.time()),
                "montant_total": p_ref["prix"],
                "lignes_commande": [{
                    "produit_id": p_ref["_id"],
                    "nom_snapshot": p_ref["nom"],
                    "prix_achat": p_ref["prix"],
                    "quantite": 1
                }],
                "etat_livraison": random.choice(["Livré", "En cours", "Annulé"])
            })
        db.commandes.insert_many(batch)
        if (i + BATCH_SIZE) % 50000 == 0:
            print(f"Commandes : {i + BATCH_SIZE} insérées")

    print("--- Peuplement massif terminé avec succès ! ---")

# Lancement
generate_data()

# SCRIPT DE TEST RAPIDE POUR L'ÉTAPE 5
def add_test_data_for_ia(nb_new_orders=5000):
    print(f"Insertion de {nb_new_orders} commandes multi-articles pour tester l'IA...")
    
    # On récupère quelques produits existants pour créer des liens
    prods = list(db.produits.find({}, {"nom": 1, "prix": 1}).limit(1000))
    users = list(db.utilisateurs.find({}, {"_id": 1}).limit(500))

    new_orders = []
    for _ in range(nb_new_orders):
        # On force 3 articles par commande pour garantir la co-occurrence
        articles_choisis = random.sample(prods, 3)
        panier = []
        total = 0
        for art in articles_choisis:
            panier.append({
                "produit_id": art["_id"],
                "nom_snapshot": art["nom"],
                "prix_achat": art["prix"],
                "quantite": 1
            })
            total += art["prix"]
        
        new_orders.append({
            "client_id": random.choice(users)["_id"],
            "date": datetime.now(),
            "lignes_commande": panier,
            "montant_total": round(total, 2),
            "etat_livraison": "Livré"
        })
    
    db.commandes.insert_many(new_orders)
    print("Données de test IA ajoutées.")
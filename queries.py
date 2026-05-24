from pymongo import MongoClient
from datetime import datetime, timedelta
from tabulate import tabulate
from pprint import pprint

# Connexion à l'instance Docker locale
client = MongoClient("mongodb://localhost:27017/")
db = client["ecommerce_bigdata"]

# Utilitaire pour la lisibilité des mois
MOIS_FR = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
    7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
}

# 1. ANALYTIQUE DES VENTES : CA mensuel par catégorie (Année écoulée) 
def get_monthly_revenue():
    print("\n" + "═"*80)
    print("ANALYTIQUE : CHIFFRE D'AFFAIRES MENSUEL PAR CATÉGORIE")
    print("═"*80)
    
    un_an_depuis = datetime.now() - timedelta(days=365)
    pipeline = [
        {"$match": {"date": {"$gte": un_an_depuis}}},
        {"$unwind": "$lignes_commande"},
        {"$group": {
            "_id": {
                "mois": {"$month": "$date"},
                "cat": "$lignes_commande.nom_snapshot" 
            },
            "ca": {"$sum": "$lignes_commande.prix_achat"}
        }},
        {"$sort": {"_id.mois": 1, "ca": -1}},
        {"$limit": 10}
    ]
    
    results = list(db.commandes.aggregate(pipeline))
    table = [[MOIS_FR[r['_id']['mois']], r['_id']['cat'], f"{r['ca']:,.2f} fr"] for r in results]
    print(tabulate(table, headers=["Mois", "Catégorie", "Chiffre d'Affaires"], tablefmt="pretty"))


# 2. COMPORTEMENT UTILISATEUR : Top 100 Clients 
def get_top_100_clients():
    print("\n" + "═"*80)
    print("TOP 5 DES CLIENTS LES PLUS DÉPENSIERS")
    print("═"*80)
    
    pipeline = [
        {"$group": {
            "_id": "$client_id",
            "total": {"$sum": "$montant_total"},
            "panier_moyen": {"$avg": "$montant_total"},
            "nb_cmd": {"$sum": 1}
        }},
        {"$sort": {"total": -1}},
        {"$limit": 5},
        {"$lookup": { 
            "from": "utilisateurs",
            "localField": "_id",
            "foreignField": "_id",
            "as": "user_info"
        }},
        {"$unwind": "$user_info"}
    ]
    
    results = list(db.commandes.aggregate(pipeline))
    table = [[r['user_info']['nom'], r['nb_cmd'], f"{r['panier_moyen']:,.2f} €", f"{r['total']:,.2f} €"] for r in results]
    print(tabulate(table, headers=["Nom Client", "Nb Commandes", "Panier Moyen", "Total Dépensé"], tablefmt="fancy_grid"))


# 3. GESTION DES STOCKS : Alerte Stock < 5 & Ventes >= 10/mois 
def get_stock_alerts():
    print("\n" + "═"*80)
    print("ALERTES RÉAPPROVISIONNEMENT (Forte Demande / Stock Faible)")
    print("═"*80)
    
    un_mois_depuis = datetime.now() - timedelta(days=30)
    
    pipeline = [
        {"$match": {"stock": {"$lt": 5}}}, 
        {"$lookup": {
            "from": "commandes",
            "localField": "_id",
            "foreignField": "lignes_commande.produit_id",
            "as": "ventes"
        }},
        {"$project": {
            "nom": 1, "stock": 1,
            "nb_ventes": {
                "$size": {
                    "$filter": {
                        "input": "$ventes", 
                        "as": "c", 
                        "cond": {"$gte": ["$$c.date", un_mois_depuis]}
                    }
                }
            }
        }},
        {"$match": {"nb_ventes": {"$gte": 10}}},
        {"$sort": {"nb_ventes": -1}}
    ]
    
    results = list(db.produits.aggregate(pipeline))
    if not results:
        print("Aucun produit ne nécessite de réapprovisionnement urgent.")
    else:
        table = [[r['nom'], r['stock'], r['nb_ventes']] for r in results]
        print(tabulate(table, headers=["Produit", "Stock Restant", "Ventes (30j)"], tablefmt="simple"))


# 4. RECHERCHE TEXTUELLE (SIMULATION SANS INDEX VIA REGEX) 
def search_products_no_index(keyword):
    print("\n" + "═"*80)
    print(f"RÉSULTATS DE RECHERCHE POUR : '{keyword}' (Mode sans index)")
    print("═"*80)
    
    query = {
        "$or": [
            {"nom": {"$regex": keyword, "$options": "i"}},
            {"description": {"$regex": keyword, "$options": "i"}}
        ]
    }
    
    results = list(db.produits.find(query).limit(5))
    table = [[r['nom'], r['categorie'], f"{r['prix']:.2f} €"] for r in results]
    
    if not results:
        print(f" Aucun produit trouvé pour '{keyword}'.")
    else:
        print(tabulate(table, headers=["Nom du Produit", "Catégorie", "Prix"], tablefmt="presto"))

# 5. IA : GÉNÉRATION DE LA MATRICE UTILISATEUR-PRODUIT
def create_user_item_matrix():
    print("\n" + "═"*80)
    print("IA : GÉNÉRATION DE LA MATRICE UTILISATEUR-PRODUIT")
    print("═"*80)

    # Ce pipeline transforme les commandes brutes en une structure 
    # exploitable par des algorithmes de filtrage collaboratif 
    pipeline = [
        {"$unwind": "$lignes_commande"},
        {"$group": {
            "_id": "$client_id",
            # On regroupe les IDs de produits uniques achetés par le client
            "produits_achetes": {"$addToSet": "$lignes_commande.produit_id"},
            "total_articles": {"$sum": 1}
        }},
        # Matérialise le résultat dans une collection physique pour la vélocité 
        {"$out": "ia_user_item_matrix"} 
    ]
    
    db.commandes.aggregate(pipeline)
    print(" Collection 'ia_user_item_matrix' créée avec succès.")

# 6. IA : RECOMMANDATIONS DE PRODUITS (Market Basket Analysis)
def get_recommendations(target_product_id):
    print("\n" + "═"*80)
    print(f"RECOMMANDATIONS pour les acheteurs du produit : {target_product_id}")
    print("═"*80)

    pipeline = [
        # 1. On cible toutes les commandes contenant le produit en question
        {"$match": {"lignes_commande.produit_id": target_product_id}},
        # 2. On déplie le panier pour analyser les co-occurrences 
        {"$unwind": "$lignes_commande"},
        # 3. On exclut le produit cible pour ne pas se le recommander lui-même
        {"$match": {"lignes_commande.produit_id": {"$ne": target_product_id}}},
        # 4. On compte combien de fois chaque "autre" produit apparaît
        {"$group": {
            "_id": "$lignes_commande.produit_id",
            "count": {"$sum": 1}
        }},
        # 5. Tri par popularité (fréquence d'achat simultané) 
        {"$sort": {"count": -1}},
        {"$limit": 3},
        # 6. Jointure pour récupérer les noms des produits recommandés
        {"$lookup": {
            "from": "produits",
            "localField": "_id",
            "foreignField": "_id",
            "as": "info"
        }},
        {"$unwind": "$info"}
    ]
    
    results = list(db.commandes.aggregate(pipeline))
    table = [[r['info']['nom'], r['count']] for r in results]
    
    if not table:
        print("Aucune co-occurrence trouvée (Le produit a peut-être toujours été acheté seul).")
    else:
        print(tabulate(table, headers=["Produit Recommandé", "Nb d'achats simultanés"], tablefmt="fancy_grid"))

# --- BLOC D'EXÉCUTION PRINCIPAL  ---
if __name__ == "__main__":
    print("=== DÉMARRAGE DES TESTS GLOBAUX (PROJET MONGODB M1) ===")
    
    # 1. Rappel des tests métier (Étape 3)
    get_stock_alerts()
    
    # 2. Génération de la matrice IA
    create_user_item_matrix()
    
    # 3. Audit de la matrice 
    nb_users_ia = db.ia_user_item_matrix.count_documents({})
    print(f"Audit : {nb_users_ia} profils clients générés pour l'IA.")

    # 4. Test intelligent du moteur de recommandation
   
    candidat_ia = db.ia_user_item_matrix.find_one({"total_articles": {"$gt": 1}})
    
    if candidat_ia and len(candidat_ia['produits_achetes']) > 0:
      
        target_id = candidat_ia['produits_achetes']
        get_recommendations(target_id)
    else:
        print("❌ Échec du test : Aucune commande multi-articles trouvée en base.")
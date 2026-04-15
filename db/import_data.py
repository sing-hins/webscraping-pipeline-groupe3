import json
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

# Connexion à PostgreSQL (host="db" est le nom du conteneur)
conn = psycopg2.connect(
    host="db",
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    database=os.getenv("POSTGRES_DB", "commodities_db"),
    port=os.getenv("POSTGRES_PORT", "5432")
)

cursor = conn.cursor()

# Vérifier/créer la table (au cas où)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS commodities (
        id SERIAL PRIMARY KEY,
        date DATE NOT NULL,
        annee INTEGER,
        mois INTEGER,
        matiere VARCHAR(50) NOT NULL,
        categorie VARCHAR(50),
        unite VARCHAR(20),
        prix DECIMAL(12,4),
        source TEXT,
        scraped_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW()
    )
""")
conn.commit()
print("✅ Table vérifiée/créée")

# Charger les données JSON
json_path = "clean_data.json"

if not os.path.exists(json_path):
    print(f"❌ Fichier {json_path} non trouvé !")
    print("Recherche d'autres fichiers JSON...")
    
    import glob
    json_files = glob.glob("*.json")
    if json_files:
        json_path = json_files[0]
        print(f"✅ Utilisation de {json_path}")
    else:
        print("❌ Aucun fichier JSON trouvé !")
        exit(1)

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"📊 Chargement de {len(data)} lignes...")

# Compter avant
cursor.execute("SELECT COUNT(*) FROM commodities")
avant = cursor.fetchone()[0]
print(f"📌 Avant import : {avant} lignes")

# Insérer les données
count = 0
for item in data:
    try:
        cursor.execute("""
            INSERT INTO commodities (date, annee, mois, matiere, categorie, unite, prix, source, scraped_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            item.get("date"),
            item.get("annee"),
            item.get("mois"),
            item.get("matiere"),
            item.get("categorie"),
            item.get("unite"),
            item.get("prix"),
            item.get("source"),
            item.get("scraped_at", datetime.now().isoformat())
        ))
        count += 1
    except Exception as e:
        print(f"⚠️ Erreur sur une ligne: {e}")

conn.commit()

# Compter après
cursor.execute("SELECT COUNT(*) FROM commodities")
apres = cursor.fetchone()[0]
print(f"✅ Import terminé : {count} lignes insérées")
print(f"📌 Après import : {apres} lignes")

cursor.close()
conn.close()
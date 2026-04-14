import sys
import os
import pandas as pd
from datetime import datetime

# Ajouter le parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import get_session, Commodity, init_db

# ─────────────────────────────────────────────────────────
# INSERTION DES DONNÉES NETTOYÉES
# ─────────────────────────────────────────────────────────
def load_csv_to_db(csv_path="scraper/commodities_data.csv"):
    """
    Charge le CSV nettoyé et l'insère dans PostgreSQL
    """
    print(f"Chargement de {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"  → {len(df)} lignes à insérer")

    # Nettoyer les colonnes
    df = df.rename(columns={
        "date": "date",
        "annee": "annee",
        "mois": "mois",
        "matiere": "matiere",
        "categorie": "categorie",
        "unite": "unite",
        "prix": "prix",
        "source": "source",
        "scraped_at": "scraped_at"
    })

    # Convertir les dates
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["scraped_at"] = pd.to_datetime(df["scraped_at"])

    session = get_session()
    
    try:
        # Supprimer les anciennes données (optionnel)
        print("Suppression des anciennes données...")
        session.query(Commodity).delete()
        
        # Insérer les nouvelles
        print("Insertion des nouvelles données...")
        for _, row in df.iterrows():
            commodity = Commodity(
                date=row["date"],
                annee=row["annee"],
                mois=row["mois"],
                matiere=row["matiere"],
                categorie=row["categorie"],
                unite=row["unite"],
                prix=row["prix"],
                source=row["source"],
                scraped_at=row["scraped_at"]
            )
            session.add(commodity)
        
        session.commit()
        print(f"[OK] {len(df)} lignes insérées dans la base")
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        session.close()


# ─────────────────────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 1. Initialiser la base (créer les tables)
    init_db()
    
    # 2. Charger les données depuis le CSV
    load_csv_to_db()
    
    print("\n[OK] Base de données prête !")
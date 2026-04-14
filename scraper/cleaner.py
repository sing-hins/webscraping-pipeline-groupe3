import json
import logging
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# CHARGEMENT
# ─────────────────────────────────────────────────────────
def load_raw_data(filepath="raw_data.json"):
    """Charge le fichier JSON brut produit par scraper.py"""
    log.info(f"Chargement de {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    log.info(f"  → {len(df)} lignes brutes chargées")
    return df

# ─────────────────────────────────────────────────────────
# NETTOYAGE
# ─────────────────────────────────────────────────────────
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Nettoyage des données...")
    initial = len(df)

    # 1. Renommer les colonnes proprement
    df.columns = [c.strip().lower() for c in df.columns]

    # 2. Conversion de la date
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    avant = len(df)
    df = df.dropna(subset=["date"])
    log.info(f"  Dates invalides supprimées : {avant - len(df)}")

    # 3. Conversion du prix en float (déjà fait par scraper mais sécurité)
    if df["prix"].dtype == "object":
        df["prix"] = (
            df["prix"]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
    df["prix"] = pd.to_numeric(df["prix"], errors="coerce")

    avant = len(df)
    df = df.dropna(subset=["prix"])
    log.info(f"  Prix invalides supprimés   : {avant - len(df)}")

    # 4. Supprimer les prix aberrants (négatifs ou nuls)
    avant = len(df)
    df = df[df["prix"] > 0]
    log.info(f"  Prix <= 0 supprimés        : {avant - len(df)}")

    # 5. Supprimer les doublons
    avant = len(df)
    df = df.drop_duplicates(subset=["date", "matiere"])
    log.info(f"  Doublons supprimés         : {avant - len(df)}")

    # 6. Standardiser les noms de matières (minuscules, underscore)
    df["matiere"] = df["matiere"].str.lower().str.replace(" ", "_")

    # 7. Standardiser les catégories
    df["categorie"] = df["categorie"].str.lower().str.strip()

    # 8. Conversion scraped_at
    if "scraped_at" in df.columns:
        df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce")

    # 9. Trier par catégorie, matière, date
    df = df.sort_values(
        ["categorie", "matiere", "date"]
    ).reset_index(drop=True)

    # 10. Ajouter colonne année et mois (utile pour le dashboard)
    df["annee"] = df["date"].dt.year
    df["mois"]  = df["date"].dt.month

    # 11. Garder uniquement les colonnes utiles
    colonnes_utiles = [
        "date", "annee", "mois",
        "matiere", "categorie", "unite",
        "prix", "source", "scraped_at"
    ]
    df = df[[col for col in colonnes_utiles if col in df.columns]]

    log.info(f"  Lignes finales : {len(df)} (sur {initial} initiales)")
    return df

# ─────────────────────────────────────────────────────────
# STATISTIQUES PAR MATIÈRE
# ─────────────────────────────────────────────────────────
def generate_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Génère un résumé statistique par matière"""
    stats = df.groupby(["categorie", "matiere", "unite"])["prix"].agg(
        nb_observations="count",
        prix_min="min",
        prix_max="max",
        prix_moyen="mean",
        prix_median="median",
        ecart_type="std",
        date_debut=lambda x: df.loc[x.index, "date"].min().strftime("%Y-%m-%d"),
        date_fin=lambda x: df.loc[x.index, "date"].max().strftime("%Y-%m-%d"),
    ).reset_index()

    stats["prix_moyen"]  = stats["prix_moyen"].round(4)
    stats["prix_median"] = stats["prix_median"].round(4)
    stats["ecart_type"]  = stats["ecart_type"].round(4)
    return stats

# ─────────────────────────────────────────────────────────
# SAUVEGARDE
# ─────────────────────────────────────────────────────────
def save_outputs(df: pd.DataFrame, stats: pd.DataFrame):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # CSV principal — format long (date | matiere | prix ...)
    csv_path = f"commodities_data_{timestamp}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    log.info(f"  CSV sauvé : {csv_path}")

    # CSV stable sans timestamp (pour l'API et la DB)
    df.to_csv("commodities_data.csv", index=False, encoding="utf-8-sig")
    log.info(f"  CSV sauvé : commodities_data.csv")

    # CSV statistiques
    stats.to_csv("commodities_stats.csv", index=False, encoding="utf-8-sig")
    log.info(f"  Stats sauvées : commodities_stats.csv")

    # JSON nettoyé (pour l'API)
    df_export = df.copy()
    df_export["date"] = df_export["date"].astype(str)
    if "scraped_at" in df_export.columns:
        df_export["scraped_at"] = df_export["scraped_at"].astype(str)
    df_export.to_json("clean_data.json", orient="records", force_ascii=False, indent=2)
    log.info(f"  JSON nettoyé : clean_data.json")

# ─────────────────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────────────────
def run_cleaner(filepath="raw_data.json"):
    """
    Pipeline complet : charge → nettoie → stats → sauvegarde
    Retourne le DataFrame nettoyé
    """
    log.info("="*50)
    log.info("DEMARRAGE DU NETTOYAGE")
    log.info("="*50)

    df    = load_raw_data(filepath)
    df    = clean_data(df)
    stats = generate_stats(df)

    log.info("\nResume par categorie :")
    for cat, grp in df.groupby("categorie"):
        log.info(
            f"  {cat:15s} : {grp['matiere'].nunique()} matieres, "
            f"{len(grp)} observations"
        )

    log.info("\nApercu des stats :")
    log.info("\n" + stats[["matiere", "prix_min", "prix_max", "prix_moyen",
                            "nb_observations"]].to_string(index=False))

    save_outputs(df, stats)

    log.info("\nNETTOYAGE TERMINE [OK]")
    log.info("="*50)

    return df

# ─────────────────────────────────────────────────────────
# POINT D'ENTREE
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_cleaner()
import pytest
import pandas as pd
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scraper'))
from cleaner import clean_data, generate_stats


# ── Fixture : DataFrame de test ────────────────────────
@pytest.fixture
def sample_df():
    return pd.DataFrame([
        {"date": "2020-01-01", "matiere": "gold",     "categorie": "metals",
         "unite": "USD/oz",  "prix": "1500.5",  "source": "macrotrends.net",
         "scraped_at": "2024-01-01"},
        {"date": "2020-02-01", "matiere": "gold",     "categorie": "metals",
         "unite": "USD/oz",  "prix": "1550.0",  "source": "macrotrends.net",
         "scraped_at": "2024-01-01"},
        {"date": "2020-01-01", "matiere": "crude_oil","categorie": "energy",
         "unite": "USD/bbl", "prix": "$60.25",  "source": "macrotrends.net",
         "scraped_at": "2024-01-01"},
        # Doublon — doit être supprimé
        {"date": "2020-01-01", "matiere": "gold",     "categorie": "metals",
         "unite": "USD/oz",  "prix": "1500.5",  "source": "macrotrends.net",
         "scraped_at": "2024-01-01"},
        # Prix invalide — doit être supprimé
        {"date": "2020-03-01", "matiere": "silver",   "categorie": "metals",
         "unite": "USD/oz",  "prix": "N/A",     "source": "macrotrends.net",
         "scraped_at": "2024-01-01"},
        # Prix négatif — doit être supprimé
        {"date": "2020-04-01", "matiere": "silver",   "categorie": "metals",
         "unite": "USD/oz",  "prix": "-5.0",    "source": "macrotrends.net",
         "scraped_at": "2024-01-01"},
    ])


def test_clean_supprime_doublons(sample_df):
    """Vérifie que les doublons date+matière sont supprimés"""
    df_clean = clean_data(sample_df)
    assert df_clean.duplicated(subset=["date", "matiere"]).sum() == 0


def test_clean_supprime_prix_invalides(sample_df):
    """Vérifie que les prix non numériques sont supprimés"""
    df_clean = clean_data(sample_df)
    assert df_clean["prix"].isna().sum() == 0


def test_clean_supprime_prix_negatifs(sample_df):
    """Vérifie que les prix négatifs ou nuls sont supprimés"""
    df_clean = clean_data(sample_df)
    assert (df_clean["prix"] <= 0).sum() == 0


def test_clean_colonnes_presentes(sample_df):
    """Vérifie que les colonnes obligatoires sont présentes"""
    df_clean = clean_data(sample_df)
    colonnes_requises = ["date", "annee", "mois", "matiere",
                         "categorie", "prix", "unite"]
    for col in colonnes_requises:
        assert col in df_clean.columns, f"Colonne manquante : {col}"


def test_clean_types_corrects(sample_df):
    """Vérifie les types de données après nettoyage"""
    df_clean = clean_data(sample_df)
    assert pd.api.types.is_datetime64_any_dtype(df_clean["date"])
    assert pd.api.types.is_float_dtype(df_clean["prix"])
    assert pd.api.types.is_integer_dtype(df_clean["annee"])


def test_stats_colonnes(sample_df):
    """Vérifie que generate_stats produit les bonnes colonnes"""
    df_clean = clean_data(sample_df)
    stats    = generate_stats(df_clean)
    for col in ["matiere", "prix_min", "prix_max", "prix_moyen", "nb_observations"]:
        assert col in stats.columns, f"Colonne stats manquante : {col}"

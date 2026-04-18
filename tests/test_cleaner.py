# tests/test_cleaner.py
import json
import os
import sys
import pandas as pd
from datetime import datetime

# Ajouter le dossier parent au chemin
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─────────────────────────────────────────────────────────
# TEST 1 : Vérification du chargement des données
# ─────────────────────────────────────────────────────────
def test_load_raw_data():
    """Test que le chargement du fichier raw_data.json fonctionne"""
    
    from scraper.cleaner import load_raw_data
    
    df = load_raw_data("scraper/raw_data.json")
    
    assert df is not None
    assert len(df) > 0
    assert len(df) >= 50, f"Moins de 50 lignes: {len(df)}"
    
    # Vérifier les colonnes essentielles
    required_columns = ["date", "matiere", "prix", "categorie", "unite"]
    for col in required_columns:
        assert col in df.columns, f"Colonne manquante: {col}"
    
    print(f"✅ Test 1 passé: {len(df)} lignes chargées")


# ─────────────────────────────────────────────────────────
# TEST 2 : Vérification du nettoyage (suppression des prix <= 0)
# ─────────────────────────────────────────────────────────
def test_clean_data_removes_negative_prices():
    """Test que les prix négatifs ou nuls sont supprimés"""
    
    from scraper.cleaner import clean_data
    
    # Créer un DataFrame de test
    test_df = pd.DataFrame({
        'date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04'],
        'prix': [100, -50, 0, 200],
        'matiere': ['gold', 'gold', 'gold', 'gold'],
        'categorie': ['metals', 'metals', 'metals', 'metals'],
        'unite': ['USD/oz', 'USD/oz', 'USD/oz', 'USD/oz'],
        'source': ['test', 'test', 'test', 'test']
    })
    
    df_clean = clean_data(test_df)
    
    # Vérifier que les prix négatifs et nuls ont été supprimés
    assert len(df_clean) == 2, f"Attendu 2 lignes, obtenu {len(df_clean)}"
    assert all(df_clean['prix'] > 0), "Il reste des prix négatifs ou nuls"
    
    print("✅ Test 2 passé: suppression des prix négatifs et nuls")


# ─────────────────────────────────────────────────────────
# TEST 3 : Vérification de la conversion des dates
# ─────────────────────────────────────────────────────────
def test_clean_data_converts_dates():
    """Test que les dates sont correctement converties"""
    
    from scraper.cleaner import clean_data
    
    test_df = pd.DataFrame({
        'date': ['2024-01-15', '2024-02-20', 'invalid_date', '2024-03-10'],
        'prix': [100, 150, 200, 250],
        'matiere': ['gold', 'gold', 'gold', 'gold'],
        'categorie': ['metals', 'metals', 'metals', 'metals'],
        'unite': ['USD/oz', 'USD/oz', 'USD/oz', 'USD/oz'],
        'source': ['test', 'test', 'test', 'test']
    })
    
    df_clean = clean_data(test_df)
    
    # Les dates invalides doivent être supprimées
    assert len(df_clean) == 3, f"Attendu 3 lignes, obtenu {len(df_clean)}"
    
    # Vérifier que les dates sont bien au format datetime
    assert pd.api.types.is_datetime64_any_dtype(df_clean['date']), "Les dates ne sont pas au format datetime"
    
    # Vérifier les colonnes année et mois
    assert 'annee' in df_clean.columns, "Colonne 'annee' manquante"
    assert 'mois' in df_clean.columns, "Colonne 'mois' manquante"
    
    print("✅ Test 3 passé: conversion des dates OK")


# ─────────────────────────────────────────────────────────
# TEST 4 : Vérification de la suppression des doublons
# ─────────────────────────────────────────────────────────
def test_clean_data_removes_duplicates():
    """Test que les doublons (même date et même matière) sont supprimés"""
    
    from scraper.cleaner import clean_data
    
    test_df = pd.DataFrame({
        'date': ['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-02'],
        'prix': [100, 100, 150, 150],
        'matiere': ['gold', 'gold', 'gold', 'silver'],
        'categorie': ['metals', 'metals', 'metals', 'metals'],
        'unite': ['USD/oz', 'USD/oz', 'USD/oz', 'USD/oz'],
        'source': ['test', 'test', 'test', 'test']
    })
    
    df_clean = clean_data(test_df)
    
    # Le doublon gold/2024-01-01 doit être supprimé
    # On doit avoir 3 lignes: gold 2024-01-01 (1 seule), gold 2024-01-02, silver 2024-01-02
    assert len(df_clean) == 3, f"Attendu 3 lignes après dédoublonnage, obtenu {len(df_clean)}"
    
    print("✅ Test 4 passé: suppression des doublons")


# ─────────────────────────────────────────────────────────
# TEST 5 : Vérification de la génération des statistiques
# ─────────────────────────────────────────────────────────
def test_generate_stats():
    """Test que les statistiques par matière sont correctement générées"""
    
    from scraper.cleaner import generate_stats
    
    test_df = pd.DataFrame({
        'date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-01', '2024-01-02'],
        'prix': [100, 110, 120, 50, 60],
        'matiere': ['gold', 'gold', 'gold', 'silver', 'silver'],
        'categorie': ['metals', 'metals', 'metals', 'metals', 'metals'],
        'unite': ['USD/oz', 'USD/oz', 'USD/oz', 'USD/oz', 'USD/oz'],
        'source': ['test', 'test', 'test', 'test', 'test']
    })
    
    stats = generate_stats(test_df)
    
    # Vérifier les statistiques pour gold
    gold_stats = stats[stats['matiere'] == 'gold']
    assert len(gold_stats) == 1
    assert gold_stats['prix_min'].values[0] == 100
    assert gold_stats['prix_max'].values[0] == 120
    assert gold_stats['prix_moyen'].values[0] == 110
    assert gold_stats['nb_observations'].values[0] == 3
    
    # Vérifier les statistiques pour silver
    silver_stats = stats[stats['matiere'] == 'silver']
    assert len(silver_stats) == 1
    assert silver_stats['prix_min'].values[0] == 50
    assert silver_stats['prix_max'].values[0] == 60
    assert silver_stats['prix_moyen'].values[0] == 55
    assert silver_stats['nb_observations'].values[0] == 2
    
    # Vérifier les colonnes attendues
    expected_columns = ['categorie', 'matiere', 'unite', 'nb_observations', 
                        'prix_min', 'prix_max', 'prix_moyen', 'prix_median', 'ecart_type']
    for col in expected_columns:
        assert col in stats.columns, f"Colonne manquante dans les stats: {col}"
    
    print("✅ Test 5 passé: génération des statistiques OK")


# ─────────────────────────────────────────────────────────
# TEST 6 : Vérification du pipeline complet (optionnel)
# ─────────────────────────────────────────────────────────
def test_full_cleaner_pipeline():
    """Test que le pipeline complet fonctionne (basé sur les fichiers existants)"""
    
    from scraper.cleaner import load_raw_data, clean_data, generate_stats
    
    # Charger les données réelles
    df = load_raw_data("scraper/raw_data.json")
    assert len(df) > 0
    
    # Nettoyer
    df_clean = clean_data(df)
    assert len(df_clean) > 0
    assert len(df_clean) <= len(df)
    
    # Générer les stats
    stats = generate_stats(df_clean)
    assert len(stats) > 0
    assert len(stats) == df_clean['matiere'].nunique()
    
    # Vérifier les catégories
    categories = set(df_clean['categorie'].unique())
    expected_categories = {'metals', 'energy', 'commodities'}
    assert categories == expected_categories, f"Catégories trouvées: {categories}"
    
    print(f"✅ Test 6 passé: pipeline complet - {len(df_clean)} lignes, {len(stats)} matières")


# ─────────────────────────────────────────────────────────
# EXÉCUTION PRINCIPALE
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🧪 EXÉCUTION DES TESTS UNITAIRE DU CLEANER")
    print("="*50 + "\n")
    
    tests = [
        ("Chargement des données", test_load_raw_data),
        ("Suppression prix négatifs/nuls", test_clean_data_removes_negative_prices),
        ("Conversion des dates", test_clean_data_converts_dates),
        ("Suppression des doublons", test_clean_data_removes_duplicates),
        ("Génération des statistiques", test_generate_stats),
        ("Pipeline complet", test_full_cleaner_pipeline),
    ]
    
    passed = 0
    failed = 0
    
    for name, test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {name}: Erreur inattendue - {e}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"📊 RÉSULTAT: {passed} passed, {failed} failed")
    print("="*50)
    
    sys.exit(1 if failed > 0 else 0)
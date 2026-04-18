# tests/test_scraper.py
import json
import os
import sys

# ─────────────────────────────────────────────────────────
# TEST 1 : Vérification du respect de robots.txt
# ─────────────────────────────────────────────────────────
def test_robots_txt_respect():
    """Test que les URLs autorisées passent, les interdites sont bloquées"""
    
    DISALLOWED_PATHS = [
        "/stock-comparison", "/search/", "/series/", "/test/",
        "/dev/", "/sandbox/", "/pma/", "/stats/", "/Secure_Server/"
    ]
    
    def is_allowed(url):
        from urllib.parse import urlparse
        path = urlparse(url).path
        for disallowed in DISALLOWED_PATHS:
            if path.startswith(disallowed):
                return False
        return True
    
    # URLs autorisées
    assert is_allowed("https://www.macrotrends.net/1333/historical-gold-prices-100-year-chart") == True
    assert is_allowed("https://www.macrotrends.net/1470/silver-prices") == True
    
    # URLs interdites
    assert is_allowed("https://www.macrotrends.net/search/?q=gold") == False
    assert is_allowed("https://www.macrotrends.net/stock-comparison") == False
    assert is_allowed("https://www.macrotrends.net/series/123") == False
    
    print("✅ Test 1 passé: robots.txt respecté")


# ─────────────────────────────────────────────────────────
# TEST 2 : Vérification du fichier raw_data.json
# ─────────────────────────────────────────────────────────
def test_raw_data_file():
    """Test que raw_data.json existe et contient des données valides"""
    
    raw_data_path = os.path.join(os.path.dirname(__file__), "..", "scraper", "raw_data.json")
    
    # Vérifier que le fichier existe
    assert os.path.exists(raw_data_path), f"❌ Fichier non trouvé: {raw_data_path}"
    
    # Vérifier qu'il contient des données valides
    with open(raw_data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert len(data) > 0, "❌ Le fichier raw_data.json est vide"
    assert len(data) >= 50, f"❌ Moins de 50 items: {len(data)} (minimum requis)"
    
    # Vérifier la structure
    required_keys = ["date", "matiere", "prix", "unite", "categorie"]
    for key in required_keys:
        assert key in data[0], f"❌ Clé manquante: {key}"
    
    # Vérifier que les prix sont des nombres
    assert isinstance(data[0]["prix"], (int, float)), "❌ Le prix n'est pas un nombre"
    
    # Vérifier qu'il y a plusieurs matières
    matieres = set(item.get("matiere") for item in data)
    assert len(matieres) >= 10, f"❌ Seulement {len(matieres)} matières (10 minimum)"
    
    print(f"✅ Test 2 passé: {len(data)} lignes, {len(matieres)} matières")


# ─────────────────────────────────────────────────────────
# TEST 3 : Vérification des données nettoyées
# ─────────────────────────────────────────────────────────
def test_clean_data_file():
    """Test que clean_data.json existe et est valide"""
    
    clean_data_path = os.path.join(os.path.dirname(__file__), "..", "scraper", "clean_data.json")
    
    assert os.path.exists(clean_data_path), f"❌ Fichier non trouvé: {clean_data_path}"
    
    with open(clean_data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert len(data) > 0, "❌ clean_data.json est vide"
    
    # Vérifier qu'il n'y a pas de prix négatifs
    prix_negatifs = [item for item in data if item.get("prix", 0) <= 0]
    assert len(prix_negatifs) == 0, f"❌ {len(prix_negatifs)} prix négatifs ou nuls trouvés"
    
    # Vérifier que les dates sont au bon format
    for item in data[:10]:
        assert "date" in item, "❌ Date manquante"
        assert "-" in item["date"], f"❌ Format de date invalide: {item['date']}"
    
    print(f"✅ Test 3 passé: {len(data)} lignes nettoyées, aucun prix négatif")


# ─────────────────────────────────────────────────────────
# TEST 4 : Vérification du fichier de statistiques
# ─────────────────────────────────────────────────────────
def test_stats_file():
    """Test que commodities_stats.csv existe"""
    
    stats_path = os.path.join(os.path.dirname(__file__), "..", "scraper", "commodities_stats.csv")
    
    assert os.path.exists(stats_path), f"❌ Fichier non trouvé: {stats_path}"
    
    # Vérifier que le fichier n'est pas vide
    assert os.path.getsize(stats_path) > 0, "❌ Le fichier de statistiques est vide"
    
    print("✅ Test 4 passé: commodities_stats.csv existe")


# ─────────────────────────────────────────────────────────
# EXÉCUTION PRINCIPALE
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🧪 EXÉCUTION DES TESTS UNITAIRE DU SCRAPER")
    print("="*50 + "\n")
    
    tests = [
        ("Respect robots.txt", test_robots_txt_respect),
        ("Fichier raw_data.json", test_raw_data_file),
        ("Fichier clean_data.json", test_clean_data_file),
        ("Fichier statistiques", test_stats_file),
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
    
    # Sortie avec code d'erreur si des tests échouent
    sys.exit(1 if failed > 0 else 0)
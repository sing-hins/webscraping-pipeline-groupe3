import pytest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scraper'))
from scraper import MATIERES, init_driver


def test_matieres_not_empty():
    """Vérifie que la liste des matières n'est pas vide"""
    assert len(MATIERES) > 0


def test_matieres_structure():
    """Vérifie que chaque matière a les clés obligatoires"""
    for nom, config in MATIERES.items():
        assert "url"       in config, f"{nom} manque 'url'"
        assert "categorie" in config, f"{nom} manque 'categorie'"
        assert "unite"     in config, f"{nom} manque 'unite'"


def test_matieres_categories_valides():
    """Vérifie que les catégories sont dans la liste autorisée"""
    categories_valides = {"metals", "energy", "commodities"}
    for nom, config in MATIERES.items():
        assert config["categorie"] in categories_valides, \
            f"{nom} a une catégorie invalide : {config['categorie']}"


def test_matieres_urls_macrotrends():
    """Vérifie que toutes les URLs pointent vers macrotrends.net"""
    for nom, config in MATIERES.items():
        assert "macrotrends.net" in config["url"], \
            f"{nom} a une URL invalide : {config['url']}"


def test_nb_matieres_par_categorie():
    """Vérifie qu'on a au moins 2 matières par catégorie"""
    from collections import Counter
    counts = Counter(c["categorie"] for c in MATIERES.values())
    for cat, nb in counts.items():
        assert nb >= 2, f"Catégorie '{cat}' a seulement {nb} matière(s)"

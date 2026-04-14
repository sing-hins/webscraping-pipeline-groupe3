# Pipeline Web Scraping - Commodities

## 🎯 Objectif
Scraping automatique des prix des matières premières (métaux, énergie, commodités agricoles) depuis Macrotrends.

## 📊 Données collectées
- **12 matières** : gold, silver, copper, platinum, crude_oil, natural_gas, brent_crude, corn, wheat, coffee, cocoa, sugar
- **5 815 lignes** après nettoyage
- **Période** : Données mensuelles historiques
- **Sources** : macrotrends.net

## ✅ Ce qui est fait (Data Engineering)

| Fichier | Description | Status |
|---------|-------------|--------|
| `scraper/scraper.py` | Scraping Selenium avec respect robots.txt | ✅ |
| `scraper/cleaner.py` | Nettoyage pandas (doublons, NaN, formats) | ✅ |
| `commodities_data.csv` | Données nettoyées prêtes pour API/DB | ✅ |

## 🚀 Pour les développeurs backend (API + DB)

### Récupérer les données
Les données nettoyées sont dans `scraper/commodities_data.csv`

### Structure des données
| Colonne | Type | Description |
|---------|------|-------------|
| date | date | Prix mensuel |
| matiere | string | gold, silver, etc. |
| categorie | string | metals, energy, commodities |
| prix | float | Prix en USD |
| unite | string | USD/oz, USD/barrel, etc. |

### Modèle de base de données suggéré
```sql
CREATE TABLE commodities (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    matiere VARCHAR(50) NOT NULL,
    categorie VARCHAR(50) NOT NULL,
    prix FLOAT NOT NULL,
    unite VARCHAR(20),
    source TEXT,
    scraped_at TIMESTAMP
);
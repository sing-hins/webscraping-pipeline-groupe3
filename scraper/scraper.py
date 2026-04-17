import time
import json
import logging
import sys
import io
from datetime import datetime
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, JavascriptException

# ─────────────────────────────────────────────────────────
# FORCER L'UTF-8 POUR LA CONSOLE WINDOWS
# ─────────────────────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ─────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper.log", encoding='utf-8')
    ]
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# CONFIGURATION RESPECTANT ROBOTS.TXT
# ─────────────────────────────────────────────────────────
CRAWL_DELAY = 2  # secondes entre les requêtes (respect éthique)
USER_AGENT = "ENSEA Educational Project / AS Data Science"
MAX_RETRIES = 2

# Liste des chemins interdits par robots.txt
DISALLOWED_PATHS = [
    "/stock-comparison",
    "/search/",
    "/series/",
    "/test/",
    "/dev/",
    "/sandbox/",
    "/pma/",
    "/stats/",
    "/Secure_Server/"
]

def is_allowed_by_robots(url):
    """Vérifie si l'URL est autorisée par robots.txt"""
    parsed = urlparse(url)
    path = parsed.path
    
    for disallowed in DISALLOWED_PATHS:
        if path.startswith(disallowed):
            return False
    return True

# ─────────────────────────────────────────────────────────
# LISTE DES MATIÈRES À SCRAPER
# ─────────────────────────────────────────────────────────
MATIERES = {
    # METALS
    "gold": {
        "url": "https://www.macrotrends.net/1333/historical-gold-prices-100-year-chart",
        "categorie": "metals",
        "unite": "USD/oz"
    },
    "silver": {
        "url": "https://www.macrotrends.net/1470/historical-silver-prices-100-year-chart",
        "categorie": "metals",
        "unite": "USD/oz"
    },
    "copper": {
        "url": "https://www.macrotrends.net/1476/copper-prices-historical-chart-data",
        "categorie": "metals",
        "unite": "USD/lb"
    },
    "platinum": {
        "url": "https://www.macrotrends.net/2540/platinum-price-history",
        "categorie": "metals",
        "unite": "USD/oz"
    },
    # ENERGY
    "crude_oil": {
        "url": "https://www.macrotrends.net/1369/crude-oil-price-history-chart",
        "categorie": "energy",
        "unite": "USD/barrel"
    },
    "natural_gas": {
        "url": "https://www.macrotrends.net/2478/natural-gas-price-history",
        "categorie": "energy",
        "unite": "USD/MMBtu"
    },
    "brent_crude": {
        "url": "https://www.macrotrends.net/2480/brent-crude-oil-prices-10-year-daily-chart",
        "categorie": "energy",
        "unite": "USD/barrel"
    },
    # COMMODITIES
    "corn": {
        "url": "https://www.macrotrends.net/2532/corn-prices-historical-chart-data",
        "categorie": "commodities",
        "unite": "USD/bushel"
    },
    "wheat": {
        "url": "https://www.macrotrends.net/2534/wheat-prices-historical-chart",
        "categorie": "commodities",
        "unite": "USD/bushel"
    },
    "coffee": {
        "url": "https://www.macrotrends.net/2535/coffee-prices-historical-chart",
        "categorie": "commodities",
        "unite": "USD/lb"
    },
    "cocoa": {
        "url": "https://www.macrotrends.net/2536/cocoa-prices-historical-chart",
        "categorie": "commodities",
        "unite": "USD/kg"
    },
    "sugar": {
        "url": "https://www.macrotrends.net/2537/sugar-prices-historical-chart",
        "categorie": "commodities",
        "unite": "USD/lb"
    },
}

# ─────────────────────────────────────────────────────────
# INITIALISATION DU NAVIGATEUR
# ─────────────────────────────────────────────────────────
from selenium.webdriver.chrome.service import Service

def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(f"user-agent={USER_AGENT}")
    
    # ----- AJOUT POUR DOCKER -----
    # Indiquer le chemin de Chromium (installé dans l'image)
    options.binary_location = "/usr/bin/chromium"
    # Indiquer le chemin du chromedriver
    service = Service(executable_path="/usr/bin/chromedriver")
    # -----------------------------
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver
# ─────────────────────────────────────────────────────────
# SUPPRIMER LES OVERLAYS (VERSION CORRIGÉE)
# ─────────────────────────────────────────────────────────
def remove_overlays(driver):
    """Supprime les popups et overlays sans erreur JS"""
    try:
        # Version avec chaîne continue (pas de saut de ligne)
        driver.execute_script("""
            var selectors = ['.fc-dialog-overlay', '.fc-consent-root', '#onetrust-accept-btn-handler', '.modal', '.popup', '.overlay'];
            for (var i = 0; i < selectors.length; i++) {
                var elements = document.querySelectorAll(selectors[i]);
                for (var j = 0; j < elements.length; j++) {
                    elements[j].remove();
                }
            }
        """)
        return True
    except JavascriptException as e:
        log.warning(f"  [WARN] Erreur overlay (non bloquante): {str(e)[:100]}")
        return False

def click_table_tab(driver):
    """Clique sur l'onglet du tableau si présent"""
    try:
        driver.execute_script("""
            var tabs = document.querySelectorAll('div.tab.tab2');
            if (tabs.length > 0) {
                tabs[0].click();
            }
        """)
        return True
    except JavascriptException as e:
        log.warning(f"  [WARN] Onglet tableau non trouvé: {str(e)[:100]}")
        return False

# ─────────────────────────────────────────────────────────
# SCRAPER UNE PAGE (AVEC RETRY)
# ─────────────────────────────────────────────────────────
def scrape_page(driver, nom, config, retry=0):
    url = config["url"]
    categorie = config["categorie"]
    unite = config["unite"]

    # Vérifier robots.txt
    if not is_allowed_by_robots(url):
        log.warning(f"  [SKIP] {nom} - URL non autorisée par robots.txt")
        return []

    log.info(f"Scraping : {nom} ({categorie}) — {url}")

    try:
        driver.get(url)
        time.sleep(CRAWL_DELAY)

        # Supprimer les overlays
        remove_overlays(driver)
        time.sleep(1)

        # Cliquer sur l'onglet tableau
        click_table_tab(driver)
        time.sleep(2)

        # Attendre que le tableau soit chargé
        wait = WebDriverWait(driver, 25)
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#tableContainer1 tbody tr, table tbody tr")
            )
        )
        time.sleep(2)

        # Essayer plusieurs sélecteurs pour le tableau
        table_selectors = ["#tableContainer1 tbody tr", "table tbody tr", ".dataTable tbody tr"]
        rows = []
        for selector in table_selectors:
            rows = driver.find_elements(By.CSS_SELECTOR, selector)
            if rows:
                break

        if not rows:
            log.warning(f"  [WARN] Aucune ligne trouvée pour {nom}")
            return []

        data = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 2:
                date_str = cols[0].text.strip()
                prix_str = cols[1].text.strip().replace("$", "").replace(",", "").replace(" ", "")
                if date_str and prix_str:
                    try:
                        prix = float(prix_str)
                        data.append({
                            "date": date_str,
                            "matiere": nom,
                            "prix": prix,
                            "unite": unite,
                            "categorie": categorie,
                            "source": url,
                            "scraped_at": datetime.now().isoformat()
                        })
                    except ValueError:
                        continue

        log.info(f"  [OK] {len(data)} lignes extraites pour {nom}")
        return data

    except TimeoutException:
        log.error(f"  [TIMEOUT] {nom} - délai dépassé")
        if retry < MAX_RETRIES:
            log.info(f"  [RETRY] {nom} - tentative {retry + 2}/{MAX_RETRIES + 1}")
            time.sleep(5)
            return scrape_page(driver, nom, config, retry + 1)
        return []
        
    except Exception as e:
        log.error(f"  [ERROR] {nom} : {str(e)[:200]}")
        if retry < MAX_RETRIES:
            log.info(f"  [RETRY] {nom} - tentative {retry + 2}/{MAX_RETRIES + 1}")
            time.sleep(5)
            return scrape_page(driver, nom, config, retry + 1)
        return []

# ─────────────────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────────────────
def run_scraper(matieres=None):
    """
    Lance le scraping de toutes les matières.
    Retourne une liste de dicts et sauvegarde raw_data.json
    """
    if matieres is None:
        matieres = MATIERES

    log.info("=" * 50)
    log.info("DEBUT DU SCRAPING - Macrotrends")
    log.info(f"User-Agent: {USER_AGENT}")
    log.info(f"Crawl delay: {CRAWL_DELAY}s")
    log.info("=" * 50)

    driver = init_driver()
    all_data = []
    errors = []
    success = []

    try:
        for nom, config in matieres.items():
            result = scrape_page(driver, nom, config)
            
            if result:
                all_data.extend(result)
                success.append(nom)
            else:
                errors.append(nom)
            
            # Délai entre chaque page (respect éthique)
            time.sleep(CRAWL_DELAY)

    finally:
        driver.quit()
        log.info("Navigateur ferme.")

    # Sauvegarde raw_data.json
    with open("raw_data.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    log.info("=" * 50)
    log.info("SCRAPING TERMINE")
    log.info(f"  Total lignes  : {len(all_data)}")
    log.info(f"  Matieres OK   : {len(success)}/{len(matieres)}")
    if success:
        log.info(f"  Succes : {success}")
    if errors:
        log.warning(f"  Erreurs : {errors}")
    log.info(f"  Fichier sauve : raw_data.json")
    log.info("=" * 50)

    return all_data


# ─────────────────────────────────────────────────────────
# POINT D'ENTREE
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_scraper()

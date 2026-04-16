import os
import sys
import logging
from datetime import datetime
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# CONFIGURATION CELERY + REDIS
# ─────────────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "webscraping_tasks",
    broker  = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
)

celery_app.conf.update(
    task_serializer        = "json",
    result_serializer      = "json",
    accept_content         = ["json"],
    timezone               = "Africa/Abidjan",
    enable_utc             = True,
    task_track_started     = True,
    result_expires         = 3600,  # résultats conservés 1h

    # ── CELERY BEAT — Planification automatique ──────────
    beat_schedule = {

        # Scraping complet toutes les semaines (lundi 6h)
        "scraping-hebdomadaire": {
            "task":     "celery_tasks.scrape_task",
            "schedule": crontab(hour=6, minute=0, day_of_week=1),
            "args":     (),
        },

        # Scraping mensuel le 1er du mois à 5h
        "scraping-mensuel": {
            "task":     "celery_tasks.scrape_task",
            "schedule": crontab(hour=5, minute=0, day_of_month=1),
            "args":     (),
        },

        # Nettoyage seul toutes les nuits à 2h
        "nettoyage-quotidien": {
            "task":     "celery_tasks.clean_task",
            "schedule": crontab(hour=2, minute=0),
            "args":     (),
        },
    }
)

# ─────────────────────────────────────────────────────────
# TÂCHE : SCRAPING COMPLET
# ─────────────────────────────────────────────────────────
@celery_app.task(bind=True, name="celery_tasks.scrape_task",
                 max_retries=3, default_retry_delay=60)
def scrape_task(self):
    """Scrape toutes les matières et nettoie les données"""
    log.info(f"[Task {self.request.id}] Démarrage scraping...")

    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scraper'))
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'db'))
        from scraper  import run_scraper
        from cleaner  import run_cleaner
        from init_db  import run_init
        from models   import ScrapingLog
        from init_db  import get_engine, get_session

        session   = get_session(get_engine())
        log_entry = ScrapingLog(
            status   = "running",
            task_id  = self.request.id
        )
        session.add(log_entry)
        session.commit()

        # Étape 1 : Scraping
        self.update_state(state="PROGRESS",
                          meta={"step": "scraping", "progress": 30})
        raw_data = run_scraper()

        # Étape 2 : Nettoyage
        self.update_state(state="PROGRESS",
                          meta={"step": "cleaning", "progress": 60})
        df = run_cleaner()

        # Étape 3 : Insertion en base
        self.update_state(state="PROGRESS",
                          meta={"step": "inserting", "progress": 90})
        run_init()

        # Log succès
        log_entry.status      = "success"
        log_entry.nb_lignes   = len(df)
        log_entry.finished_at = datetime.utcnow()
        session.commit()
        session.close()

        result = {
            "status":   "success",
            "nb_lignes": len(df),
            "task_id":  self.request.id,
            "finished": str(datetime.utcnow())
        }
        log.info(f"[Task {self.request.id}] Terminé — {len(df)} lignes")
        return result

    except Exception as e:
        log.error(f"[Task {self.request.id}] Erreur : {e}")
        try:
            log_entry.status  = "error"
            log_entry.erreurs = str(e)[:500]
            session.commit()
            session.close()
        except:
            pass
        raise self.retry(exc=e)


# ─────────────────────────────────────────────────────────
# TÂCHE : NETTOYAGE SEUL
# ─────────────────────────────────────────────────────────
@celery_app.task(bind=True, name="celery_tasks.clean_task")
def clean_task(self):
    """Nettoyage et réinsertion sans re-scraper"""
    log.info(f"[Task {self.request.id}] Démarrage nettoyage...")
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scraper'))
        from cleaner import run_cleaner
        df = run_cleaner()
        log.info(f"[Task {self.request.id}] Nettoyage OK — {len(df)} lignes")
        return {"status": "success", "nb_lignes": len(df)}
    except Exception as e:
        log.error(f"[Task {self.request.id}] Erreur nettoyage : {e}")
        return {"status": "error", "message": str(e)}

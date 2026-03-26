cat > tasks/celery_tasks.py << 'EOF'
from celery import Celery
import os

# Création de l'objet Celery — c'est lui que Docker cherche
celery = Celery(
    "observatoire",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    timezone="Africa/Abidjan",
    beat_schedule={
        "scraping-automatique": {
            "task": "tasks.celery_tasks.scraper_prices",
            "schedule": 21600.0,  # toutes les 6 heures
        },
    }
)

@celery.task
def scraper_prices():
    """Tâche principale de scraping — sera complétée par le Data Engineer"""
    print("Scraping en cours...")
    return {"status": "ok", "message": "Scraping lancé"}
EOF

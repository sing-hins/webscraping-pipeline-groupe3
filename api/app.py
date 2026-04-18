import os
import logging
from flask import Flask, jsonify, request, abort, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from prometheus_flask_exporter import PrometheusMetrics

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'db'))
from models import Commodity, ScrapingLog

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# APP FLASK
# ─────────────────────────────────────────────────────────

app = Flask(__name__)
metrics = PrometheusMetrics(app)
CORS(app)

# ─────────────────────────────────────────────────────────
# DB SESSION
# ─────────────────────────────────────────────────────────
def get_session():
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_host = os.getenv("POSTGRES_HOST", "db")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "commodities_db")
    
    url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(url, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()

# ─────────────────────────────────────────────────────────
# SWAGGER UI
# ─────────────────────────────────────────────────────────
SWAGGER_URL = "/api/docs"
API_URL = "/static/swagger.yaml"
swaggerui_bp = get_swaggerui_blueprint(SWAGGER_URL, API_URL)
app.register_blueprint(swaggerui_bp, url_prefix=SWAGGER_URL)

# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────
def paginate(query, page, limit):
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    return items, total

def success(data, total=None, page=None, limit=None):
    resp = {"status": "success", "data": data}
    if total is not None:
        resp["pagination"] = {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    return jsonify(resp), 200

def error(message, code=400):
    return jsonify({"status": "error", "message": message}), code

# ─────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "projet": "ENSEA WebScraping Pipeline",
        "version": "1.0.0",
        "endpoints": [
            "GET  /data",
            "GET  /data/<id>",
            "GET  /data/search?query=gold&categorie=metals",
            "GET  /data/categories",
            "GET  /data/matieres",
            "GET  /stats",
            "POST /scrape",
            "POST /scrape/async",
            "GET  /scrape/status/<task_id>",
            "GET  /logs",
            "GET  /api/docs",
            "GET  /export/csv",
            "GET  /export/csv/filtered"
        ]
    }), 200

@app.route("/data", methods=["GET"])
def get_all_data():
    session = get_session()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    categorie = request.args.get("categorie")
    matiere = request.args.get("matiere")
    annee = request.args.get("annee")

    if page < 1 or limit < 1 or limit > 500:
        return error("page >= 1 et limit entre 1 et 500")

    query = session.query(Commodity).order_by(
        Commodity.categorie, Commodity.matiere, Commodity.date
    )

    if categorie:
        query = query.filter(Commodity.categorie == categorie.lower())
    if matiere:
        query = query.filter(Commodity.matiere == matiere.lower())
    if annee:
        query = query.filter(Commodity.annee == int(annee))

    items, total = paginate(query, page, limit)
    session.close()
    return success([i.to_dict() for i in items], total, page, limit)

@app.route("/data/<int:item_id>", methods=["GET"])
def get_by_id(item_id):
    session = get_session()
    item = session.query(Commodity).get(item_id)
    session.close()
    if not item:
        return error(f"ID {item_id} introuvable", 404)
    return success(item.to_dict())

@app.route("/data/search", methods=["GET"])
def search():
    session = get_session()
    query_str = request.args.get("query", "").strip().lower()
    categorie = request.args.get("categorie")
    matiere = request.args.get("matiere")
    annee_min = request.args.get("annee_min")
    annee_max = request.args.get("annee_max")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    query = session.query(Commodity)

    if query_str:
        query = query.filter(
            or_(
                Commodity.matiere.ilike(f"%{query_str}%"),
                Commodity.categorie.ilike(f"%{query_str}%"),
            )
        )
    if categorie:
        query = query.filter(Commodity.categorie == categorie.lower())
    if matiere:
        query = query.filter(Commodity.matiere == matiere.lower())
    if annee_min:
        query = query.filter(Commodity.annee >= int(annee_min))
    if annee_max:
        query = query.filter(Commodity.annee <= int(annee_max))

    query = query.order_by(Commodity.matiere, Commodity.date)
    items, total = paginate(query, page, limit)
    session.close()
    return success([i.to_dict() for i in items], total, page, limit)

@app.route("/data/categories", methods=["GET"])
def get_categories():
    session = get_session()
    cats = session.query(Commodity.categorie).distinct().all()
    session.close()
    return success([c[0] for c in cats])

@app.route("/data/matieres", methods=["GET"])
def get_matieres():
    session = get_session()
    rows = session.query(
        Commodity.matiere, Commodity.categorie, Commodity.unite
    ).distinct().order_by(Commodity.categorie, Commodity.matiere).all()
    session.close()
    return success([
        {"matiere": r[0], "categorie": r[1], "unite": r[2]}
        for r in rows
    ])

@app.route("/stats", methods=["GET"])
def get_stats():
    from sqlalchemy import func
    session = get_session()
    rows = session.query(
        Commodity.matiere,
        Commodity.categorie,
        Commodity.unite,
        func.count(Commodity.id).label("nb"),
        func.min(Commodity.prix).label("prix_min"),
        func.max(Commodity.prix).label("prix_max"),
        func.avg(Commodity.prix).label("prix_moyen"),
        func.min(Commodity.date).label("date_debut"),
        func.max(Commodity.date).label("date_fin"),
    ).group_by(
        Commodity.matiere, Commodity.categorie, Commodity.unite
    ).order_by(Commodity.categorie, Commodity.matiere).all()

    session.close()
    return success([{
        "matiere": r.matiere,
        "categorie": r.categorie,
        "unite": r.unite,
        "nb_obs": r.nb,
        "prix_min": round(r.prix_min, 4),
        "prix_max": round(r.prix_max, 4),
        "prix_moyen": round(r.prix_moyen, 4),
        "date_debut": str(r.date_debut),
        "date_fin": str(r.date_fin),
    } for r in rows])

@app.route("/scrape", methods=["POST"])
def scrape_sync():
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scraper'))
    from scraper import run_scraper
    from cleaner import run_cleaner

    session = get_session()
    log_entry = ScrapingLog(status="running")
    session.add(log_entry)
    session.commit()

    try:
        run_scraper()
        df = run_cleaner()
        nb = len(df)

        log_entry.status = "success"
        log_entry.nb_lignes = nb
        log_entry.finished_at = __import__("datetime").datetime.utcnow()
        session.commit()

        return jsonify({
            "status": "success",
            "nb_lignes": nb,
            "message": "Scraping et nettoyage terminés"
        }), 200

    except Exception as e:
        log_entry.status = "error"
        log_entry.erreurs = str(e)[:500]
        session.commit()
        return error(f"Erreur scraping : {e}", 500)

    finally:
        session.close()

@app.route("/scrape/async", methods=["POST"])
def scrape_async():
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tasks'))
    from celery_tasks import scrape_task

    task = scrape_task.delay()
    return jsonify({
        "status": "accepted",
        "task_id": task.id,
        "message": "Scraping lancé en arrière-plan",
        "check": f"/scrape/status/{task.id}"
    }), 202

@app.route("/scrape/status/<task_id>", methods=["GET"])
def scrape_status(task_id):
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tasks'))
    from celery_tasks import celery_app

    task = celery_app.AsyncResult(task_id)
    return jsonify({
        "task_id": task_id,
        "status": task.status,
        "result": str(task.result) if task.ready() else None
    }), 200

@app.route("/logs", methods=["GET"])
def get_logs():
    session = get_session()
    logs = session.query(ScrapingLog).order_by(
        ScrapingLog.started_at.desc()
    ).limit(50).all()
    session.close()
    return success([l.to_dict() for l in logs])

@app.route("/export/csv", methods=["GET"])
def export_csv():
    import io
    import csv
    session = get_session()
    data = session.query(Commodity).all()
    session.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "date", "annee", "mois", "matiere", "categorie", "unite", "prix", "source", "scraped_at"])
    
    for item in data:
        writer.writerow([
            item.id, item.date, item.annee, item.mois, item.matiere,
            item.categorie, item.unite, item.prix, item.source, item.scraped_at
        ])
    
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=commodities_export.csv'
    }

@app.route("/export/csv/filtered", methods=["GET"])
def export_csv_filtered():
    import io
    import csv
    matiere = request.args.get("matiere")
    categorie = request.args.get("categorie")
    annee = request.args.get("annee")
    
    session = get_session()
    query = session.query(Commodity)
    
    if matiere:
        query = query.filter(Commodity.matiere == matiere)
    if categorie:
        query = query.filter(Commodity.categorie == categorie)
    if annee:
        query = query.filter(Commodity.annee == int(annee))
    
    data = query.all()
    session.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "date", "annee", "mois", "matiere", "categorie", "unite", "prix", "source", "scraped_at"])
    
    for item in data:
        writer.writerow([
            item.id, item.date, item.annee, item.mois, item.matiere,
            item.categorie, item.unite, item.prix, item.source, item.scraped_at
        ])
    
    filename = "commodities"
    if matiere:
        filename += f"_{matiere}"
    if categorie:
        filename += f"_{categorie}"
    if annee:
        filename += f"_{annee}"
    filename += ".csv"
    
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename={filename}'
    }

# ─────────────────────────────────────────────────────────
# GESTION DES ERREURS
# ─────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return error("Endpoint introuvable", 404)

@app.errorhandler(500)
def server_error(e):
    return error("Erreur serveur interne", 500)

# ─────────────────────────────────────────────────────────
# LANCEMENT
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )
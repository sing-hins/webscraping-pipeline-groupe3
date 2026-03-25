# db/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Création de l'objet db qui sera partagé dans toute l'application
db = SQLAlchemy()

class CacaoPrice(db.Model):
    """
    Table des prix du cacao.
    Stocke à la fois les prix locaux (FCFA/kg) 
    et les prix mondiaux (USD/tonne)
    """
    __tablename__ = "cacao_prices"

    # Identifiant unique auto-généré
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Date de la cotation
    date = db.Column(db.Date, nullable=False)
    
    # Prix numérique (ex: 1200.0)
    prix = db.Column(db.Float, nullable=False)
    
    # Devise : "FCFA" pour local, "USD" pour mondial
    devise = db.Column(db.String(10), nullable=False)
    
    # Unité : "kg" pour local, "tonne" pour mondial
    unite = db.Column(db.String(20), nullable=False)
    
    # Type : "local" (Côte d'Ivoire) ou "mondial" (marché international)
    type_prix = db.Column(db.String(20), nullable=False)
    
    # Site source des données
    source = db.Column(db.String(100), nullable=False)
    
    # Date d'insertion automatique en base
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convertit l'objet en dictionnaire pour l'API JSON"""
        return {
            "id": self.id,
            "date": self.date.strftime("%Y-%m-%d"),
            "prix": self.prix,
            "devise": self.devise,
            "unite": self.unite,
            "type_prix": self.type_prix,
            "source": self.source,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

    def __repr__(self):
        return f"<CacaoPrice {self.date} - {self.prix} {self.devise}/{self.unite}>"


class CafePrice(db.Model):
    """
    Table des prix du café.
    """
    __tablename__ = "cafe_prices"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False)
    prix = db.Column(db.Float, nullable=False)
    devise = db.Column(db.String(10), nullable=False)
    unite = db.Column(db.String(20), nullable=False)
    type_prix = db.Column(db.String(20), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convertit l'objet en dictionnaire pour l'API JSON"""
        return {
            "id": self.id,
            "date": self.date.strftime("%Y-%m-%d"),
            "prix": self.prix,
            "devise": self.devise,
            "unite": self.unite,
            "type_prix": self.type_prix,
            "source": self.source,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

    def __repr__(self):
        return f"<CafePrice {self.date} - {self.prix} {self.devise}/{self.unite}>"


class ScrapingLog(db.Model):
    """
    Table de logs des scrapings effectués.
    Permet de savoir quand le scraping a tourné, 
    combien d'items ont été collectés, et s'il y a eu des erreurs.
    """
    __tablename__ = "scraping_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Date du début de scrapping
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Date du fin de scrapping
    finished_at = db.Column(db.DateTime, nullable=True)
    
    # Statut : "success", "error", "running"
    statut = db.Column(db.String(20), default="running")
    
    # Nombre d'items récupérés
    items_collectes = db.Column(db.Integer, default=0)
    
    # Message d'erreur si problème
    message = db.Column(db.Text, nullable=True)
    
    # Source scrapée
    source = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "started_at": self.started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": self.finished_at.strftime("%Y-%m-%d %H:%M:%S") if self.finished_at else None,
            "statut": self.statut,
            "items_collectes": self.items_collectes,
            "message": self.message,
            "source": self.source
        }

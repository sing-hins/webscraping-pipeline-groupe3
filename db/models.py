import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Base de données
Base = declarative_base()

# ─────────────────────────────────────────────────────────
# MODÈLE COMMODITY
# ─────────────────────────────────────────────────────────
class Commodity(Base):
    __tablename__ = "commodities"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    annee = Column(Integer)
    mois = Column(Integer)
    matiere = Column(String(50), nullable=False)
    categorie = Column(String(50), nullable=False)
    unite = Column(String(20))
    prix = Column(Float, nullable=False)
    source = Column(String(500))
    scraped_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)

    # Index composites pour les requêtes fréquentes
    __table_args__ = (
        Index("idx_commodities_date", "date"),
        Index("idx_commodities_matiere", "matiere"),
        Index("idx_commodities_categorie", "categorie"),
        Index("idx_commodities_date_matiere", "date", "matiere"),
    )

    def to_dict(self):
        """Convertit l'objet en dictionnaire pour l'API"""
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "annee": self.annee,
            "mois": self.mois,
            "matiere": self.matiere,
            "categorie": self.categorie,
            "unite": self.unite,
            "prix": self.prix,
            "source": self.source,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ─────────────────────────────────────────────────────────
# CONNEXION À LA BASE
# ─────────────────────────────────────────────────────────
def get_db_url():
    """Construit l'URL de connexion PostgreSQL depuis .env"""
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "commodities_db")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def get_engine():
    """Crée et retourne le moteur SQLAlchemy"""
    return create_engine(get_db_url(), echo=False)


def get_session():
    """Crée et retourne une session de base de données"""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def init_db():
    """Initialise la base de données (crée les tables)"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("[OK] Base de données initialisée")


def drop_db():
    """Supprime toutes les tables (utile pour les tests)"""
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    print("[WARN] Toutes les tables ont été supprimées")


# ─────────────────────────────────────────────────────────
# POINT D'ENTRÉE POUR L'INITIALISATION
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
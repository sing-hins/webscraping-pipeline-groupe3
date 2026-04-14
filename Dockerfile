# ================================
# IMAGE DE BASE
# Python 3.11 version légère
# ================================
FROM python:3.11-slim

# ================================
# VARIABLES D'ENVIRONNEMENT
# ================================
# Empêche Python de créer des fichiers .pyc
ENV PYTHONDONTWRITEBYTECODE=1

# Affiche les logs Python immédiatement (pas de buffer)
ENV PYTHONUNBUFFERED=1

# Dossier de travail dans le conteneur
WORKDIR /app

# ================================
# INSTALLATION DES DÉPENDANCES SYSTÈME
# ================================
# Nécessaire pour psycopg2 (connexion PostgreSQL)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ================================
# INSTALLATION DES DÉPENDANCES PYTHON
# ================================
# On copie d'abord SEULEMENT requirements.txt
# (optimisation : Docker met en cache cette couche)
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ================================
# COPIE DU CODE SOURCE
# ================================
COPY . .

# ================================
# PORT EXPOSÉ
# ================================
# Flask tourne sur le port 5000
EXPOSE 5000

# ================================
# COMMANDE DE DÉMARRAGE
# ================================
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

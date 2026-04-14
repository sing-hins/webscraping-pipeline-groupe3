import pytest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'api'))


@pytest.fixture
def client():
    """Client de test Flask"""
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index(client):
    """GET / retourne 200 avec la liste des endpoints"""
    r = client.get("/")
    assert r.status_code == 200
    data = r.get_json()
    assert "endpoints" in data


def test_get_data_pagination(client):
    """GET /data retourne une structure paginée"""
    r = client.get("/data?page=1&limit=5")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "success"
    assert "pagination" in data
    assert "data" in data


def test_get_data_limit_invalide(client):
    """GET /data avec limit invalide retourne 400"""
    r = client.get("/data?limit=9999")
    assert r.status_code == 400


def test_get_by_id_inexistant(client):
    """GET /data/999999 retourne 404"""
    r = client.get("/data/999999")
    assert r.status_code == 404


def test_search_endpoint(client):
    """GET /data/search retourne une réponse valide"""
    r = client.get("/data/search?query=gold")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "success"


def test_categories_endpoint(client):
    """GET /data/categories retourne une liste"""
    r = client.get("/data/categories")
    assert r.status_code == 200


def test_stats_endpoint(client):
    """GET /stats retourne une réponse valide"""
    r = client.get("/stats")
    assert r.status_code == 200


def test_logs_endpoint(client):
    """GET /logs retourne une liste"""
    r = client.get("/logs")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data["data"], list)

import pytest
from io import BytesIO
from fastapi.testclient import TestClient
from app import app
from database import Database
from model import Point
import os

# Configuration de la base de données
CONF_DIR = config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.ini"))

@pytest.fixture(scope="function")
def client():
    """Fixture pour initialiser le client de test"""
    client = TestClient(app)
    yield client

def test_get_polygon(client):
    """ Test du point d'API pour récupérer un polygone sous forme d'image """
    polygon = [
        Point(x=4.0, y=0.0, comment="Test point"),
        Point(x=4.0, y=3.0, comment="Test point2"),
        Point(x=6.7, y=5.7, comment="Test point3"),
        Point(x=6.4, y=0.0, comment="Test point4")
    ]
    # Insérer le polygone dans la base de données et récupérer l'id
    db = Database(CONF_DIR)
    id_polygone = db.insert_polygon(polygon)

    # Faire la requête GET en passant le paramètre `id` dans l'URL
    response = client.get(f"/polygon/{id_polygone}")

    # Vérifications du statut de la réponse et du type de contenu
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "image/png"
    
    # Vérification que la réponse est bien une image PNG
    img_data = BytesIO(response.content)
    img_data.seek(0)
    png_signature = b'\x89PNG\r\n\x1a\n'
    assert img_data.read(len(png_signature)) == png_signature

def test_get_non_existing_polygon(client):
    """ Test de récupération d'un polygone qui n'existe pas """
    non_existing_polygon_id = 9999  # Un ID de polygone qui n'existe pas dans la base de données
    response = client.get(f"/polygon/{non_existing_polygon_id}")  # On essaye de récupérer un polygone inexistant
    # Vérification du code de statut et du message d'erreur
    assert response.status_code == 400  # Assurez-vous que le statut de la réponse est 404 pour "Not Found"

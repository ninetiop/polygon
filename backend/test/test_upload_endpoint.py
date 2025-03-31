import sys
import os
import io
import time
import pytest
from fastapi.testclient import TestClient
from database import Database, PolygonORM
from app import app

CONF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.ini"))

app.should_exit = False

# Création d'une fixture pour la configuration de la base de données et le client de test
@pytest.fixture(scope="module")
def db():
    db = Database(CONF_DIR)
    # Supprime les polygones existants avant les tests
    db.session.query(PolygonORM).delete()
    db.session.commit()
    yield db
    # Nettoyage après les tests
    db.session.query(PolygonORM).delete()
    db.session.commit()

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture
def valid_csv():
    return "x,y,comment\n4.0,0.0,\n4.0,3.0,\n6.7,5.7,was 6.5 before version 2.3.0\n6.7,0.0," 

@pytest.fixture
def invalid_csvs():
    return [
        "4,0\n4,3\n6.7,5.7\n6.7,0",  # No columns
        "a,b,c\n4,0\n4,3\n6.7,5.7\n6.7,0,",  # Bad columns
        "x,y,comment\n2.0,4.0,2.2\n1.0,2.1,\n1.2,0",  # Passing third float instead comment
        "x,y,comment\n2.0,4.0,hello world,4.5\n1.0,2.1,\n1.2,2.3,",  # Passing too much values 
        "x,y,comment\n2.0,\n1.0,2.1,\n1.2,2.3,",  # Passing not enough values 
    ]

@pytest.fixture
def text_file_content():
    return "Hello, World!"  # Mauvais format (fichier texte)

# Test de l'upload d'un CSV valide
def test_upload_valid_csv(client, valid_csv):
    files = {"csv_file": ("test.csv", valid_csv, "text/csv")}
    response = client.post("/upload", files=files)
    assert response.status_code == 200
    assert "CSV uploaded successfully" in response.text

# Test de l'upload de CSV invalide
@pytest.mark.parametrize("invalid_csv", ["4,0\n4,3\n6.7,5.7\n6.7,0", 
                                         "a,b,c\n4,0\n4,3\n6.7,5.7\n6.7,0,", 
                                         "x,y,comment\n2.0,4.0,2.2\n1.0,2.1,\n1.2,0", 
                                         "x,y,comment\n2.0,4.0,hello world,4.5\n1.0,2.1,\n1.2,2.3,", 
                                         "x,y,comment\n2.0,\n1.0,2.1,\n1.2,2.3,"]
)
def test_upload_invalid_csv(client, invalid_csv):
    file_obj = io.BytesIO(invalid_csv.encode('utf-8'))
    files = {"csv_file": ("test.csv", file_obj, "text/csv")}
    response = client.post("/upload", files=files)
    assert response.status_code == 400
    time.sleep(0.5)

# Test de l'upload de fichier avec une extension incorrecte (txt)
def test_upload_no_csv(client, text_file_content):
    files = {"csv_file": ("test.txt", text_file_content, "text/plain")}
    response = client.post("/upload", files=files)
    assert response.status_code == 400
    assert "The file is not in CSV format" in response.text

# Test de l'upload de deux fois le même CSV, vérification que la DB reste inchangée
def test_upload_duplicate_csv(client, valid_csv, db):
    # Premier envoi du CSV
    files = {"csv_file": ("test.csv", valid_csv, "text/csv")}
    response = client.post("/upload", files=files)
    assert response.status_code == 200
    assert "CSV uploaded successfully" in response.text

    # Récupérer l'ID du polygone créé
    first_polygon_id = db.session.query(PolygonORM.id).first()[0]

    # Envoi du même fichier CSV une deuxième fois
    response = client.post("/upload", files=files)
    assert response.status_code == 200
    assert "CSV uploaded successfully" in response.text

    # Vérifier que l'ID du polygone est le même (la DB ne devrait pas changer)
    second_polygon_id = db.session.query(PolygonORM.id).first()[0]
    assert first_polygon_id == second_polygon_id  # L'ID du polygone devrait être le même

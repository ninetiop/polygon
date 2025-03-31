import pytest
import os
from database import Database, PolygonORM, PointORM
from model import Point


# Configuration de la base de données
CONF_DIR = config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.ini"))

# Test de la connexion à la base de données
def test_connection():
    db = Database(CONF_DIR)
    is_connect = db.connect()
    assert is_connect is True

# Test de l'insertion d'un polygone dans la base de données
def test_insert_polygon():
    db = Database(CONF_DIR)
    points = [
        Point(x=1.5, y=2.5, comment="Test point"),
        Point(x=1.0, y=3.0, comment="Test point2")
    ]
    db.insert_polygon(points)
    nb_pts_db = len(db.get_all_rows(PointORM))  # Utilise get_all_rows pour vérifier les points
    assert nb_pts_db == 2
    # Tester l'insertion de points en double
    points = [
        Point(x=1.0, y=6.0, comment="Test point3"),
        Point(x=1.5, y=2.5, comment="Test point")
    ]
    db.insert_polygon(points)
    nb_pts_db = len(db.get_all_rows(PointORM))
    assert nb_pts_db == 3

# Test de la récupération de tous les points dans la base de données
def test_get_points():
    db = Database(CONF_DIR)
    points = [
        Point(x=1.5, y=2.5, comment="Test point"),
        Point(x=1.0, y=3.0, comment="Test point2")
    ]
    db.insert_polygon(points)

    # Utilise la méthode get_all_rows pour vérifier le nombre de points
    all_points = db.get_all_rows(PointORM)
    assert len(all_points) == 2  # Vérifie que deux points ont été insérés

# Test de la méthode is_polygon_exist
def test_is_polygon_exist():
    db = Database(CONF_DIR)
    # Insérer un polygone avec des points
    points_1 = [
        Point(x=1.5, y=2.5, comment="Test point 1"),
        Point(x=1.0, y=3.0, comment="Test point 2")
    ]
    db.insert_polygon(points_1)

    # Vérifier si le polygone existe
    existing_polygon_id = db.is_polygon_exist(points_1)
    assert existing_polygon_id is not None
    assert isinstance(existing_polygon_id, int)

    # Insérer un autre polygone avec des points différents
    points_2 = [
        Point(x=4.5, y=5.5, comment="Test point 3"),
        Point(x=6.0, y=7.0, comment="Test point 4")
    ]
    db.insert_polygon(points_2)

    # Vérifier que le deuxième polygone existe
    existing_polygon_id_2 = db.is_polygon_exist(points_2)
    assert existing_polygon_id_2 is not None
    assert existing_polygon_id != existing_polygon_id_2

    # Tester un polygone qui n'existe pas
    points_3 = [Point(x=9.5, y=10.5, comment="Test point 5")]
    existing_polygon_id_3 = db.is_polygon_exist(points_3)
    assert existing_polygon_id_3 is None
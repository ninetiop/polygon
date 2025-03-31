import numpy as np
import shapely
import random
import matplotlib.pyplot as plt
import io
import os
from matplotlib.patches import Polygon
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from logger_manager import log
from database import Database
from model import Point

CONF_DIR = config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.ini"))

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"], 
)
db = Database(CONF_DIR)

@app.get("/polygon/{id}")
async def get_polygon(id: int):
    """ Endpoint retourner l'image du polygone """
    try:
        log.info(f"Get polygon with ID {id}")

        # Récupérer les points associés au polygone
        polygons_points = db.get_points(id=id)  
        if not polygons_points:  
            log.error(f"No polygon found for ID {id} in DB")
            raise HTTPException(status_code=400, detail="No polygon found in DB")

        # Extraire les coordonnées X et Y
        x_values = [point.x for point in polygons_points]
        y_values = [point.y for point in polygons_points]

        if not x_values or not y_values:  # Vérification de sécurité
            raise HTTPException(status_code=400, detail="Invalid polygon data")

        # Calcul de l'aire du polygone
        area = shapely.Polygon([(p.x, p.y) for p in polygons_points]).area

        # Configuration de l'affichage
        plt.clf()
        plt.ioff()
        plt.xlim(min(x_values) - 1, max(x_values) + 1)
        plt.ylim(min(y_values) - 1, max(y_values) + 1)

        # Ajout du polygone avec une couleur fixe
        polygon = Polygon([(p.x, p.y) for p in polygons_points], closed=True, fill=False, 
                          edgecolor="blue", linewidth=2, label=f"Polygon {id}, Area = {area:.2f} px²")
        plt.gca().add_patch(polygon)
        plt.legend(loc="upper right")

        # Sauvegarde de l'image en mémoire
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png')
        img_bytes.seek(0)

        return StreamingResponse(img_bytes, media_type="image/png")

    except HTTPException as http_exc:
        log.error(f"HTTPException {http_exc.status_code}: {http_exc.detail}")
        raise http_exc

    except Exception as exc:
        log.error(f"Unexpected error: {exc}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the polygon.")

@app.post("/upload")
async def upload_csv(csv_file: UploadFile):
    """Endpoint pour uploader un fichier CSV contenant des points et créer un polygone."""
    try:
        log.info(f"Uploading {csv_file.filename}...")      

        # Vérification du format du fichier (doit être un CSV)
        if not csv_file.filename.endswith(".csv"):
            log.error("The file is not in CSV format")
            raise HTTPException(status_code=400, detail="The file is not in CSV format")

        # Lecture et décodage du fichier en UTF-8
        content = await csv_file.read()
        content_str = content.decode('utf-8')
        string_io = io.StringIO(content_str)

        try:
            # Lecture des données CSV en utilisant NumPy
            data = np.genfromtxt(string_io, delimiter=',', dtype=None, names=True, encoding='utf-8')

            # Création des objets `Point` à partir des données CSV
            points = [
                Point(x=float(x), y=float(y), comment=comment)
                for x, y, comment in zip(data['x'], data['y'], data['comment'])
            ]

            # Vérification que le polygone contient au moins 3 points
            if len(points) < 3:
                raise HTTPException(status_code=400, detail="A polygon must have at least 3 points.")

            # Insertion du polygone dans la base de données et récupération de son ID
            id_polygon = db.insert_polygon(points)

            log.info(f"{csv_file.filename} uploaded successfully!") 

        except ValueError:
            # Gestion d'une erreur due à un format CSV mal structuré
            log.error("ValueError: CSV is malformed")
            raise HTTPException(status_code=400, detail="CSV is malformed.")

        # Retourner une réponse avec l'ID du polygone inséré et la liste des points
        return {
            "message": "CSV uploaded successfully",
            "id": id_polygon,
            "points": [{"x": p.x, "y": p.y, "comment": p.comment} for p in points]
        }

    except HTTPException as http_exc:
        # Gestion des erreurs HTTP spécifiques
        log.error(f"HTTPException {http_exc.status_code}: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as db_exc:
        # Gestion des erreurs liées à la base de données
        log.error(f"Database error: {str(db_exc)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_exc)}")

    except Exception as exc:
        # Gestion des erreurs générales
        log.error(f"Unhandled exception: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"Error processing the CSV file: {str(exc)}")
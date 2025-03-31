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
    try:
        log.info(f"Get polygon with ID {id}")
        # Si un ID est fourni
        if id is not None:
            polygons_points = db.get_points(id=id)  # Récupère uniquement les points pour ce polygone
            if not polygons_points:  # Vérifier si des points sont trouvés
                log.error("No polygon ID found in DB")
                raise HTTPException(status_code=400, detail="No polygon ID found in DB")
        else:
            log.error("No polygon ID provided, returning empty response.")
            raise HTTPException(status_code=400, detail="No polygon ID provided")

        # Construction du dictionnaire des polygones
        polygons_dict = {}
        for point in polygons_points:
            if point.polygon_id not in polygons_dict:
                polygons_dict[point.polygon_id] = []
            polygons_dict[point.polygon_id].append((point.x, point.y))

        # Création du graphique
        plt.clf()
        plt.ioff()
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'brown', 'cyan', 'magenta']
        x_values = [point.x for point in polygons_points]
        y_values = [point.y for point in polygons_points]
        x_min, x_max = min(x_values), max(x_values)
        y_min, y_max = min(y_values), max(y_values)

        for polygon_id, polygon_points in polygons_dict.items():
            area = shapely.Polygon(polygon_points).area
            color = random.choice(colors)
            polygon = Polygon(polygon_points, closed=True, fill=False, edgecolor=color, linewidth=2,
                              label=f"Polygon {polygon_id}, Area = {area:.2f} px²")
            plt.gca().add_patch(polygon)

        plt.xlim(x_min - 1, x_max + 1)
        plt.ylim(y_min - 1, y_max + 1)
        plt.legend(loc="upper right")

        # Sauvegarder l'image en mémoire
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png')
        img_bytes.seek(0)

        # Retourner l'image comme réponse
        return StreamingResponse(img_bytes, media_type="image/png")

    except HTTPException as http_exc:
        log.error(f"HTTPException {http_exc.status_code} due to reason: {http_exc.detail}")
        raise http_exc

    except Exception as exc:
        log.error(f"Error: {exc}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the polygon.")


@app.post("/upload")
async def upload_csv(csv_file: UploadFile):
    try:
        log.info(f"Uploading {csv_file.filename}... ")      
        if not csv_file.filename.endswith(".csv"):
            log.error("The file is not in CSV format")
            raise HTTPException(status_code=400, detail="The file is not in CSV format")
        content = await csv_file.read()
        content_str = content.decode('utf-8')
        string_io = io.StringIO(content_str)
        try:
            data = np.genfromtxt(string_io, delimiter=',', dtype=None, names=True, encoding='utf-8')
            points = [
                Point(x=float(x), y=float(y), comment=comment)
                for x, y, comment in zip(data['x'], data['y'], data['comment'])
            ]
            if len(points) < 3:
                raise HTTPException(status_code=400, detail="A polygon must have at least 3 points.")
            id_polygon = db.insert_polygon(points)
            log.info(f"{csv_file.filename} uploaded successfully!") 
        except ValueError as value_error:
            log.error(f"ValueError due to reason: CSV is malformed")
            raise HTTPException(status_code=400, detail=f"CSV is malformed.")
        return {"message": "CSV uploaded successfully", "id": id_polygon, "points": [{"x": p.x, "y": p.y, "comment": p.comment} for p in points]}  
    except HTTPException as http_exc:
        log.error(f"HTTPException {http_exc.status_code} due to reason: {http_exc.detail}")
        raise http_exc
    except SQLAlchemyError as db_exc:
        log.error(f"Database error: {str(db_exc)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_exc)}")
    except Exception as exc:
        log.error(f"Unhandled exception: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"Error processing the CSV file: {str(exc)}")

from sqlalchemy import create_engine, text, ForeignKey, Column, Integer, Float, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from configparser import ConfigParser
from typing import List, Union, Optional
from sqlalchemy.exc import SQLAlchemyError
from model import Point
from logger_manager import log

Base = declarative_base()

class PolygonORM(Base):
    __tablename__ = "polygons"
    id = Column(Integer, primary_key=True, autoincrement=True)
    points = relationship("PointORM", back_populates="polygon", cascade="all, delete-orphan")


class PointORM(Base):
    __tablename__ = "points"
    id = Column(Integer, primary_key=True, autoincrement=True)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    comment = Column(String, nullable=True)
    polygon_id = Column(Integer, ForeignKey('polygons.id'), nullable=False)
    polygon = relationship("PolygonORM", back_populates="points") 


class Database:
    def __init__(self, config_file: str = "config.ini"):
        self.config_file = config_file
        self.connect()

    def get_all_rows(self, model):
        """ Récupérer toutes les lignes d'une table donnée (ex: PointORM ou PolygonORM) """
        try:
            rows = self.session.query(model).all()
            return rows
        except Exception as e:
            self.session.rollback()
            print(f"Error while fetching rows: {e}")
            return []

    def read_db_config(self) -> str:
        """Read and return the database connection URL from the ini file"""
        config = ConfigParser()
        config.read(self.config_file)
        db = config["postgresql"]
        return f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['dbname']}"

    def connect(self) -> bool:
        """Establish a database connection and return True if successful, False otherwise."""
        try:
            DATABASE_URL = self.read_db_config()
            self.engine = create_engine(DATABASE_URL)
            self.SessionLocal = sessionmaker(bind=self.engine)
            self.session = self.SessionLocal()
            log.info("✅ Database connection established.")
            return True
        except SQLAlchemyError as e:
            log.error(f"❌ Error while connecting to the database: {e}")
            return False

    def close(self):
        """Close the session and connection."""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()
        log.info("✅ Connection closed.")

    def init_db(self):
        """Initialize the database and create tables."""
        Base.metadata.create_all(bind=self.engine)

    def is_polygon_exist(self, points: List[Point]) -> Optional[int]:
        """Check if a polygon with the same points already exists in the database, and return its ID if it exists."""
        try:
            session_db = self.SessionLocal()

            # Ordonnancer les points par leurs coordonnées x puis y pour éviter les erreurs de comparaison d'ordre
            sorted_points = sorted(points, key=lambda p: (p.x, p.y))  # Trie les points par x puis y
            point_placeholders = ",".join([f"({p.x}, {p.y})" for p in sorted_points])

            # Vérifier si tous les points existent dans la base de données et sont associés à un même polygone
            query = text(f"""
                SELECT p.polygon_id, COUNT(DISTINCT p.polygon_id)
                FROM points p
                WHERE (p.x, p.y) IN ({point_placeholders})
                GROUP BY p.polygon_id
            """)

            result = session_db.execute(query).fetchall()

            # Si on trouve des résultats
            if result:
                # Vérifier si tous les points sont associés au même polygon_id
                for polygon_id, polygon_count in result:
                    # Si plus d'un polygone existe pour ces points, ce n'est pas le même polygone
                    if polygon_count > 1:
                        log.warning(f"Points {point_placeholders} are associated with multiple polygons.")
                        return None  # Plusieurs polygones pour les mêmes points, pas le même polygone

                    # Si un seul polygone est trouvé, retourner son ID
                    if polygon_count == 1:
                        return polygon_id  # Retourner l'ID du polygone existant

            return None  # Aucun polygone avec ces points n'existe

        except SQLAlchemyError as e:
            log.error(f"❌ Error checking if polygon exists: {e}")
            raise SQLAlchemyError
        finally:
            session_db.close()


    def insert_polygon(self, points: List[Point]) -> int:
        """Create a new polygon and insert its points in a single transaction."""
        try:
            # Vérifier si un polygone avec ces points existe déjà et récupérer l'ID si c'est le cas
            existing_polygon_id = self.is_polygon_exist(points)
            if existing_polygon_id:
                log.warning(f"Polygon with the same points already exists, ID: {existing_polygon_id}")
                return existing_polygon_id  # Retourner l'ID du polygone existant

            # Si aucun polygone n'existe, on crée un nouveau polygone
            session_db = self.SessionLocal()
            with session_db.begin():
                new_polygon = PolygonORM()
                session_db.add(new_polygon)
                session_db.flush()
                for p in points:
                    p.polygon_id = new_polygon.id
                rows_inserted = self.__insert_points(points, session_db)
                if rows_inserted == 0:
                    log.warning("All points already exist, database is unchanged.")
            self.session.commit()
            return new_polygon.id  # Retourner l'ID du nouveau polygone créé

        except (SQLAlchemyError, ValueError) as e:
            log.error(f"❌ Error inserting polygon and points: {e}")
            raise SQLAlchemyError
        finally:
            self.session.close()

    def get_points(self, id: Union[int, None] = None) -> List[Point]:
        """Retrieve all points from the database or points for a specific polygon."""
        if id is None:
            # Si l'id est None, récupérer tous les points
            points = self.session.query(PointORM).all()
        else:
            # Sinon, récupérer les points pour un polygone spécifique
            points = self.session.query(PointORM).filter(PointORM.polygon_id == id).all()
        # Convertir les résultats en objets Point et les retourner
        return [Point(x=p.x, y=p.y, comment=p.comment, polygon_id=p.polygon_id) for p in points]

    def __insert_points(self, points: List[Point], session_db: Session) -> int:
        """Insert points without duplicates."""
        row_inserted = 0
        for p in points:
            new_point = PointORM(**p.model_dump())
            session_db.add(new_point)
            row_inserted += 1
        return row_inserted
-- Se connecter à la base de données postgres pour pouvoir supprimer polygone
\c postgres;

-- Supprimer la base de données polygone si elle existe
DROP DATABASE IF EXISTS polygone;

-- Créer la nouvelle base de données
CREATE DATABASE polygone;

-- Se connecter à la base polygone
\c polygone;

-- Créer les tables
CREATE TABLE IF NOT EXISTS polygons (
    id SERIAL PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS points (
    id SERIAL PRIMARY KEY,
    x FLOAT NOT NULL,
    y FLOAT NOT NULL,
    comment TEXT,
    polygon_id INT,
    FOREIGN KEY (polygon_id) REFERENCES polygons(id) ON DELETE CASCADE
);

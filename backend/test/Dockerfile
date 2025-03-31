# Utiliser une image Python officielle
FROM python:3.12

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires depuis le projet principal
COPY ../requirements.txt .
COPY ../ ./

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Définir la commande par défaut pour exécuter les tests
CMD ["pytest", "-v", "-s", "--color=yes", "--maxfail=5", "--disable-warnings"]
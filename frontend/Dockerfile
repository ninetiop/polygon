# Utiliser l'image officielle Nginx comme base
FROM nginx:alpine

# Copier tous les fichiers dans le dossier d'index de Nginx
COPY . /usr/share/nginx/html

# Exposer le port 80
EXPOSE 80

# Démarrer Nginx au démarrage
CMD ["nginx", "-g", "daemon off;"]

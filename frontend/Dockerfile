# --- Stage 1: Build the static assets ---
# Utiliser une image Node pour effectuer le build
FROM node:20-alpine as build-stage

WORKDIR /app

# Copier les fichiers de configuration et installer les dépendances
COPY package*.json ./
# Installer les dépendances de production
RUN npm install --production=false

# Copier le code source
COPY . .

# Construire l'application (les assets se trouvent généralement dans /app/dist)
RUN npm run build

# --- Stage 2: Serve the assets using Nginx ---
# Utiliser une image Nginx alpine, très légère, pour la production
FROM nginx:stable-alpine as production-stage

# Copier les fichiers construits depuis la stage de build vers le répertoire par défaut de Nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Exposer le port par défaut de Nginx
EXPOSE 80

# La commande par défaut de Nginx est utilisée
CMD ["nginx", "-g", "daemon off;"]
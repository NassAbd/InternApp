FROM node:20-alpine

# Dossier de travail
WORKDIR /app

# Copier package.json et package-lock.json pour profiter du cache Docker
COPY package*.json ./

# Installer les dépendances
RUN npm ci --frozen-lockfile

# Copier le reste du code
COPY . .

# Exposer le port Vite
EXPOSE 5173

# Lancer le dev server
CMD ["npm", "run", "dev"]

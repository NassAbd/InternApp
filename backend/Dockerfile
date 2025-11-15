# Utilise l'image de base Playwright (inclut Python et les dépendances du navigateur)
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers de dépendances en premier pour profiter de la mise en cache
# S'assurer que 'requirements.txt' existe dans le dossier 'backend/'
COPY requirements.txt .

# Installer les dépendances Python, y compris Gunicorn et Uvicorn
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code de l'application
COPY . .

# Définir une variable d'environnement pour Gunicorn/Playwright (optionnel mais utile)
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright/

# Le port que Gunicorn va écouter (doit correspondre à la config dans Gunicorn/UvicornWorker)
EXPOSE 8000

# Commande de production: Lancer Gunicorn avec des workers Uvicorn.
# Utilise généralement 2 * NBR_COEURS + 1 workers. Ici, 4 est un bon point de départ.
CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
# --- IMPORTS DE BASE (nécessaires pour la configuration) ---
import asyncio
import platform
import json
import os

# --- IMPORTS DE L'APPLICATION (après la config de l'event loop) ---
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from scrapers import airbus, ariane, cnes, thales # Déplacé
# -------------------------------------------------------------------

app = FastAPI()

# Autoriser le frontend React (vite = 5173)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS_FILE = "jobs.json"

# --- Utils (Synchrones pour l'I/O de fichier) ---
def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return []
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_jobs(jobs):
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)


# Mapping nom -> module scraper
SCRAPERS = {
    "airbus": airbus,
    "ariane": ariane,
    "cnes": cnes,
    "thales": thales,
}


# --- Routes ---
@app.get("/jobs")
def get_jobs():
    return load_jobs()

@app.get("/modules")
def get_modules():
    return list(SCRAPERS.keys())


@app.post("/scrape")
async def scrape_jobs():  # Route asynchrone
    return await _scrape_modules(list(SCRAPERS.keys()))


@app.post("/scrape_modules")
async def scrape_selected_modules(modules: list[str] = Body(..., embed=True)):  # Route asynchrone
    """
    Exemple de body JSON attendu :
    {
        "modules": ["airbus", "thales"]
    }
    """
    return await _scrape_modules(modules)


# --- Fonction utilitaire commune ASYNCHRONE ---
async def _scrape_modules(modules: list[str]):  # Fonction asynchrone
    jobs = load_jobs()
    existing_links = {j["link"] for j in jobs}
    
    tasks = []
    scraped_modules_names = []
    
    # 1. Préparer les tâches asynchrones (Coroutines)
    for module in modules:
        scraper = SCRAPERS.get(module)
        if scraper and hasattr(scraper, "fetch_jobs"):
            # Ajouter l'appel de la coroutine (la fonction fetch_jobs)
            tasks.append(scraper.fetch_jobs())
            scraped_modules_names.append(module)
        else:
            print(f"Module {module} inconnu ou sans fetch_jobs.")

    # 2. Exécuter toutes les tâches en parallèle et attendre les résultats
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 3. Traiter les résultats
    new_jobs = []
    failed_scrapers = []
    
    for module, result in zip(scraped_modules_names, results):
        if isinstance(result, Exception):
            # Le scraper a échoué (exception levée)
            print(f"Erreur scraper {module}: {result}")
            failed_scrapers.append(module)
        else:
            # Succès : 'result' est site_jobs
            site_jobs = result
            for job in site_jobs:
                if job["link"] not in existing_links:
                    job["new"] = True
                    new_jobs.append(job)
                    existing_links.add(job["link"])
                else:
                    print(f"Doublon trouvé: {job['link']}")

    # 4. Finalisation et sauvegarde
    for job in jobs:
        job["new"] = False

    jobs = new_jobs + jobs
    save_jobs(jobs)

    return {
        "added": len(new_jobs),
        "total": len(jobs),
        "failed_scrapers": failed_scrapers,
    }
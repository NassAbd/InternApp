from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body
import json
import os
from scrapers import airbus, ariane, cnes, thales

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

# --- Utils ---
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
def scrape_jobs():
    return _scrape_modules(list(SCRAPERS.keys()))


@app.post("/scrape_modules")
def scrape_selected_modules(modules: list[str] = Body(..., embed=True)):
    """
    Exemple de body JSON attendu :
    {
        "modules": ["airbus", "thales"]
    }
    """
    return _scrape_modules(modules)


# --- Fonction utilitaire commune ---
def _scrape_modules(modules: list[str]):
    jobs = load_jobs()
    new_jobs = []
    failed_scrapers = []

    # Construire un set des liens déjà présents
    existing_links = {j["link"] for j in jobs}

    for module in modules:
        scraper = SCRAPERS.get(module)
        if not scraper:
            failed_scrapers.append(module)  # module inconnu
            continue

        try:
            site_jobs = scraper.fetch_jobs()
            for job in site_jobs:
                if job["link"] not in existing_links:
                    job["new"] = True
                    new_jobs.append(job)
                    existing_links.add(job["link"])
                else:
                    print(f"Doublon trouvé: {job['link']}")
        except Exception as e:
            print(f"Erreur scraper {module}: {e}")
            failed_scrapers.append(module)

    # Marquer les anciens jobs comme non-nouveaux
    for job in jobs:
        job["new"] = False

    jobs = new_jobs + jobs
    save_jobs(jobs)

    return {
        "added": len(new_jobs),
        "total": len(jobs),
        "failed_scrapers": failed_scrapers,
    }

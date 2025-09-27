from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    allow_origins=origins,          # Autorise uniquement ces origines
    allow_credentials=True,
    allow_methods=["*"],            # GET, POST, PUT, DELETE...
    allow_headers=["*"],            # Autorise tous les headers
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


# --- Routes ---
@app.get("/jobs")
def get_jobs():
    return load_jobs()


@app.post("/scrape")
def scrape_jobs():
    jobs = load_jobs()

    new_jobs = []
    failed_scrapers = []

    for scraper in [airbus, ariane, cnes, thales]:
        try:
            site_jobs = scraper.fetch_jobs()
            for job in site_jobs:
                # éviter les doublons par lien
                if not any(j["link"] == job["link"] for j in jobs):
                    job["new"] = True
                    new_jobs.append(job)
                else:
                    print(f"Doublon trouvé: {job['link']}")
        except Exception as e:
            print(f"Erreur scraper {scraper.__name__}: {e}")
            failed_scrapers.append(scraper.__name__)

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

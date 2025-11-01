# --- BASE IMPORTS ---
import asyncio
import platform
import json
import os
import math

# --- APP IMPORTS ---
from fastapi import FastAPI, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from scrapers import airbus, ariane, cnes, thales
# -------------------

app = FastAPI()

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


SCRAPERS = {
    "airbus": airbus,
    "ariane": ariane,
    "cnes": cnes,
    "thales": thales,
}


# --- Routes ---
@app.get("/jobs")
def get_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    modules: str = Query(None),
    search: str = Query(None),
):
    all_jobs = load_jobs()

    filterable_modules = sorted(list(set(job.get("module") for job in all_jobs if job.get("module"))))

    # Filter by modules
    filtered_jobs = all_jobs
    if modules:
        selected_modules = {name.strip().lower() for name in modules.split(",")}
        filtered_jobs = [
            job for job in filtered_jobs
            if job.get("module") and job["module"].lower() in selected_modules
        ]

    # Filter by search
    if search:
        search_term = search.lower()
        filtered_jobs = [
            job for job in filtered_jobs
            if search_term in str(job.get("title", "")).lower() or \
               search_term in str(job.get("company", "")).lower() or \
               search_term in str(job.get("location", "")).lower()
        ]

    # Pagination
    total_items = len(filtered_jobs)
    total_pages = math.ceil(total_items / size)

    start_index = (page - 1) * size
    end_index = start_index + size

    paginated_jobs = filtered_jobs[start_index:end_index]

    return {
        "page": page,
        "size": size,
        "total_items": total_items,
        "total_pages": total_pages,
        "jobs": paginated_jobs,
        "filterable_modules": filterable_modules,
    }


@app.get("/modules")
def get_modules():
    return list(SCRAPERS.keys())


@app.post("/scrape")
async def scrape_jobs():
    return await _scrape_modules(list(SCRAPERS.keys()))


@app.post("/scrape_modules")
async def scrape_selected_modules(modules: list[str] = Body(..., embed=True)):
    """
    Example of expected JSON body :
    {
        "modules": ["airbus", "thales"]
    }
    """
    return await _scrape_modules(modules)


# --- ASYNC common function ---
async def _scrape_modules(modules: list[str]):
    jobs = load_jobs()
    existing_links = {j["link"] for j in jobs}
    
    tasks = []
    scraped_modules_names = []
    
    # Prepare async tasks
    for module in modules:
        scraper = SCRAPERS.get(module)
        if scraper and hasattr(scraper, "fetch_jobs"):
            # Add coroutine call (fetch_jobs function)
            tasks.append(scraper.fetch_jobs())
            scraped_modules_names.append(module)
        else:
            print(f"Module {module} unknown or without fetch_jobs.")

    # Execute tasks in parallel and wait for results
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    new_jobs = []
    failed_scrapers = []
    
    for module, result in zip(scraped_modules_names, results):
        if isinstance(result, Exception):
            # The scraper failed (exception raised)
            print(f"Error scraper {module}: {result}")
            failed_scrapers.append(module)
        else:
            # Success : 'result' is site_jobs
            site_jobs = result
            for job in site_jobs:
                if job["link"] not in existing_links:
                    job["new"] = True
                    new_jobs.append(job)
                    existing_links.add(job["link"])
                else:
                    print(f"Duplicate found: {job['link']}")

    # Finalize and save
    for job in jobs:
        job["new"] = False

    jobs = new_jobs + jobs
    save_jobs(jobs)

    return {
        "added": len(new_jobs),
        "total": len(jobs),
        "failed_scrapers": failed_scrapers,
    }
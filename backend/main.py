# --- BASE IMPORTS ---
import asyncio
import json
import os
import math

# --- APP IMPORTS ---
from fastapi import FastAPI, Body, Query, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from config import ACTIVE_SCRAPERS, JSON_OUTPUT_PATH
from tagging_service import TaggingService
from profile_manager import ProfileManager
from scoring_engine import ScoringEngine
from cv_parser import CVParser
# -------------------

app = FastAPI()

# Initialize services
tagging_service = TaggingService()
profile_manager = ProfileManager()
scoring_engine = ScoringEngine()
cv_parser = CVParser()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS_FILE = JSON_OUTPUT_PATH

# --- Utils ---
def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return []
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    
    # Ensure all jobs have tags field for backward compatibility
    for job in jobs:
        if "tags" not in job:
            job_title = job.get("title", "")
            job_description = job.get("description", "")
            job["tags"] = tagging_service.tagJob(job_title, job_description)
    
    return jobs


def save_jobs(jobs):
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)


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
    return list(ACTIVE_SCRAPERS.keys())


# --- Profile Management Endpoints ---
@app.get("/profile")
def get_profile():
    """
    Load user profile data.
    
    Returns:
        User profile containing tags, location, and groq_api_key
        
    Raises:
        HTTPException: If profile cannot be loaded or is corrupted
    """
    try:
        profile = profile_manager.loadProfile()
        return profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/profile")
def save_profile(profile_data: dict = Body(...)):
    """
    Save user profile updates.
    
    Args:
        profile_data: Dictionary containing profile fields (tags, location, groq_api_key)
        
    Returns:
        Updated profile data
        
    Raises:
        HTTPException: If profile data is invalid or cannot be saved
    """
    try:
        profile_manager.saveProfile(profile_data)
        # Return the saved profile to confirm what was actually stored
        return profile_manager.loadProfile()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IOError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/profile/parse-cv")
async def parse_cv(
    file: UploadFile = File(...),
    api_key: str = Form(...),
    merge_with_existing: bool = Form(True)
):
    """
    Parse uploaded CV file and extract relevant tags using Groq API.
    
    Args:
        file: PDF file upload
        api_key: Groq API key for LLM analysis
        merge_with_existing: Whether to merge with existing profile tags
        
    Returns:
        Dictionary containing extracted tags and updated profile
        
    Raises:
        HTTPException: If file processing or API call fails
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    if not api_key.strip():
        raise HTTPException(status_code=400, detail="Groq API key is required")
    
    try:
        # Read file content
        pdf_content = await file.read()
        
        if len(pdf_content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Parse CV and extract tags
        extracted_tags, cv_text = cv_parser.parseCV(pdf_content, api_key.strip())
        
        # Load current profile
        current_profile = profile_manager.loadProfile()
        
        # Merge tags if requested
        if merge_with_existing:
            existing_tags = current_profile.get("tags", [])
            final_tags = cv_parser.mergeTags(existing_tags, extracted_tags)
        else:
            final_tags = extracted_tags
        
        # Update profile with new tags and API key
        updated_profile = current_profile.copy()
        updated_profile["tags"] = final_tags
        updated_profile["groq_api_key"] = api_key.strip()
        
        # Save updated profile
        profile_manager.saveProfile(updated_profile)
        
        return {
            "success": True,
            "extracted_tags": extracted_tags,
            "final_tags": final_tags,
            "profile": updated_profile,
            "cv_preview": cv_text[:500] + "..." if len(cv_text) > 500 else cv_text
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=502, detail=f"API connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/jobs/for-you")
def get_personalized_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    modules: str = Query(None),
    search: str = Query(None),
):
    """
    Get personalized job feed with relevance scores.
    
    Args:
        page: Page number for pagination
        size: Number of jobs per page
        modules: Comma-separated list of modules to filter by
        search: Search term to filter jobs by title, company, or location
        
    Returns:
        Paginated personalized jobs with match_score and matching_tags
        
    Raises:
        HTTPException: If profile cannot be loaded or jobs cannot be processed
    """
    try:
        # Load user profile
        user_profile = profile_manager.loadProfile()
        
        # Check if user has any preferences set
        if not user_profile.get("tags") and not user_profile.get("location"):
            return {
                "page": page,
                "size": size,
                "total_items": 0,
                "total_pages": 0,
                "jobs": [],
                "filterable_modules": [],
                "message": "No preferences set. Please configure your profile to see personalized recommendations."
            }
        
        # Load all jobs
        all_jobs = load_jobs()
        
        # Apply module filtering before scoring (same as regular /jobs endpoint)
        filtered_jobs = all_jobs
        if modules:
            selected_modules = {name.strip().lower() for name in modules.split(",")}
            filtered_jobs = [
                job for job in filtered_jobs
                if job.get("module") and job["module"].lower() in selected_modules
            ]
        
        # Apply search filtering before scoring (same as regular /jobs endpoint)
        if search:
            search_term = search.lower()
            filtered_jobs = [
                job for job in filtered_jobs
                if search_term in str(job.get("title", "")).lower() or \
                   search_term in str(job.get("company", "")).lower() or \
                   search_term in str(job.get("location", "")).lower()
            ]
        
        # Score and filter jobs using ScoringEngine
        scored_jobs = scoring_engine.scoreJobs(user_profile, filtered_jobs)
        
        # Get filterable modules from all jobs (for UI consistency)
        filterable_modules = sorted(list(set(job.get("module") for job in all_jobs if job.get("module"))))
        
        # Pagination
        total_items = len(scored_jobs)
        total_pages = math.ceil(total_items / size) if total_items > 0 else 0
        
        start_index = (page - 1) * size
        end_index = start_index + size
        
        paginated_jobs = scored_jobs[start_index:end_index]
        
        return {
            "page": page,
            "size": size,
            "total_items": total_items,
            "total_pages": total_pages,
            "jobs": paginated_jobs,
            "filterable_modules": filterable_modules,
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Profile error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/scrape")
async def scrape_jobs():
    return await _scrape_modules(list(ACTIVE_SCRAPERS.keys()))


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
        scraper = ACTIVE_SCRAPERS.get(module)
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
                    # Add tags to the job using TaggingService
                    job_title = job.get("title", "")
                    job_description = job.get("description", "")  # Some scrapers might have description
                    job["tags"] = tagging_service.tagJob(job_title, job_description)
                    
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
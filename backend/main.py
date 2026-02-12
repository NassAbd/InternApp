# --- BASE IMPORTS ---
import asyncio
import json
import os
import math

# --- APP IMPORTS ---
from fastapi import FastAPI, Body, Query, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from config import ACTIVE_SCRAPERS
from tagging_service import TaggingService
from scoring_engine import ScoringEngine
from cv_parser import CVParser
from maintenance_service import MaintenanceService
from database import get_db, init_db
from repositories.job_repository import JobRepository
from repositories.profile_repository import ProfileRepository
from repositories.application_repository import ApplicationRepository
import inspect
import traceback
# -------------------

app = FastAPI()

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database tables on application startup."""
    init_db()
    print("✅ Database initialized")

# Initialize services
tagging_service = TaggingService()
scoring_engine = ScoringEngine()
cv_parser = CVParser()
maintenance_service = MaintenanceService()

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

# --- Utils removed - now using database repositories ---


# --- Routes ---
@app.get("/jobs")
def get_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    modules: str = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
):
    job_repo = JobRepository(db)
    all_jobs = [job.to_dict() for job in job_repo.get_all_jobs()]

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
def get_profile(db: Session = Depends(get_db)):
    """
    Load user profile data.
    
    Returns:
        User profile containing tags, location, and groq_api_key
        
    Raises:
        HTTPException: If profile cannot be loaded or is corrupted
    """
    try:
        profile_repo = ProfileRepository(db)
        profile = profile_repo.get_profile()
        return profile.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/profile")
def save_profile(profile_data: dict = Body(...), db: Session = Depends(get_db)):
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
        profile_repo = ProfileRepository(db)
        profile = profile_repo.save_profile(profile_data)
        return profile.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IOError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/profile")
def reset_profile(db: Session = Depends(get_db)):
    """
    Reset user profile to default/empty state.
    
    Returns:
        Default empty profile
        
    Raises:
        HTTPException: If profile cannot be reset
    """
    try:
        profile_repo = ProfileRepository(db)
        # Create default empty profile
        default_profile = {
            "tags": [],
            "location": None,
            "groq_api_key": None,
            "use_for_scraper_fix": False,
        }
        
        # Save the default profile (this will overwrite existing profile)
        profile = profile_repo.save_profile(default_profile)
        return profile.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset profile: {str(e)}")


@app.post("/profile/parse-cv")
async def parse_cv(
    file: UploadFile = File(...),
    api_key: str = Form(None),
    merge_with_existing: bool = Form(True),
    db: Session = Depends(get_db),
):
    """
    Parse uploaded CV file and extract relevant tags using Groq API.
    
    Args:
        file: PDF file upload
        api_key: Groq API key for LLM analysis (optional if stored in profile)
        merge_with_existing: Whether to merge with existing profile tags
        
    Returns:
        Dictionary containing extracted tags and updated profile
        
    Raises:
        HTTPException: If file processing or API call fails
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Determine API key to use
    final_api_key = api_key
    if not final_api_key or not final_api_key.strip():
        # Try to load from profile
        try:
            profile_repo = ProfileRepository(db)
            profile = profile_repo.get_profile()
            final_api_key = profile.groq_api_key
        except Exception:
            pass
            
    if not final_api_key or not final_api_key.strip():
        raise HTTPException(status_code=400, detail="Groq API key is required. Please enter it in Profile Manager.")
    
    try:
        # Read file content
        pdf_content = await file.read()
        
        if len(pdf_content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Parse CV and extract tags
        extracted_tags, cv_text = cv_parser.parseCV(pdf_content, final_api_key.strip())
        
        # Load current profile
        profile_repo = ProfileRepository(db)
        current_profile = profile_repo.get_profile()
        
        # Merge tags if requested
        if merge_with_existing:
            existing_tags = current_profile.tags or []
            final_tags = cv_parser.mergeTags(existing_tags, extracted_tags)
        else:
            final_tags = extracted_tags
        
        # Update profile with new tags and API key (only if provided explicitly)
        updated_profile_data = {
            "tags": final_tags,
            "location": current_profile.location,
            "groq_api_key": api_key.strip() if api_key and api_key.strip() else current_profile.groq_api_key,
            "use_for_scraper_fix": current_profile.use_for_scraper_fix,
        }
        
        # Save updated profile
        updated_profile = profile_repo.save_profile(updated_profile_data)
        
        return {
            "success": True,
            "extracted_tags": extracted_tags,
            "final_tags": final_tags,
            "profile": updated_profile.to_dict(),
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
    db: Session = Depends(get_db),
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
        profile_repo = ProfileRepository(db)
        user_profile_model = profile_repo.get_profile()
        user_profile = user_profile_model.to_dict()
        
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
        job_repo = JobRepository(db)
        all_jobs = [job.to_dict() for job in job_repo.get_all_jobs()]
        
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


# --- Application Tracking Endpoints ---
@app.post("/applications")
def track_application(job_data: dict = Body(...), db: Session = Depends(get_db)):
    """
    Add a job to the application tracking list.
    
    Args:
        job_data: Dictionary containing complete job information
        
    Returns:
        Created application with tracking metadata
        
    Raises:
        HTTPException: If job data is invalid or tracking fails
    """
    try:
        app_repo = ApplicationRepository(db)
        application = app_repo.add_application(job_data)
        return {
            "success": True,
            "data": application.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/applications")
def get_tracked_applications(db: Session = Depends(get_db)):
    """
    Retrieve all tracked applications sorted by last update.
    
    Returns:
        List of tracked applications with metadata
        
    Raises:
        HTTPException: If applications cannot be retrieved
    """
    try:
        app_repo = ApplicationRepository(db)
        applications = app_repo.get_applications()
        return {
            "success": True,
            "data": [app.to_dict() for app in applications]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.patch("/applications/{job_id}")
def update_application(job_id: str, updates: dict = Body(...), db: Session = Depends(get_db)):
    """
    Update an existing tracked application.
    
    Args:
        job_id: Application ID to update
        updates: Dictionary containing fields to update (status, notes)
        
    Returns:
        Updated application data
        
    Raises:
        HTTPException: If application not found or update data is invalid
    """
    try:
        app_repo = ApplicationRepository(db)
        application = app_repo.update_application(job_id, updates)
        if not application:
            raise HTTPException(status_code=404, detail=f"Application with ID {job_id} not found")
        return {
            "success": True,
            "data": application.to_dict()
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/applications/{job_id}")
def remove_application(job_id: str, db: Session = Depends(get_db)):
    """
    Remove an application from tracking.
    
    Args:
        job_id: Application ID to remove
        
    Returns:
        Success status
        
    Raises:
        HTTPException: If application not found or removal fails
    """
    try:
        app_repo = ApplicationRepository(db)
        removed = app_repo.remove_application(job_id)
        if not removed:
            raise HTTPException(status_code=404, detail=f"Application with ID {job_id} not found")
        
        return {
            "success": True,
            "message": "Application removed successfully"
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/scrape")
async def scrape_jobs(db: Session = Depends(get_db)):
    return await _scrape_modules(list(ACTIVE_SCRAPERS.keys()), db)


@app.post("/scrape_modules")
async def scrape_selected_modules(modules: list[str] = Body(..., embed=True), db: Session = Depends(get_db)):
    """
    Example of expected JSON body :
    {
        "modules": ["airbus", "thales"]
    }
    """
    return await _scrape_modules(modules, db)


# --- ASYNC common function ---
async def _scrape_modules(modules: list[str], db: Session):
    job_repo = JobRepository(db)
    all_jobs = job_repo.get_all_jobs()
    existing_links = {job.link for job in all_jobs}
    
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
    new_jobs_count = 0
    failed_scrapers = []
    
    for module, result in zip(scraped_modules_names, results):
        if isinstance(result, Exception):
            # The scraper failed (exception raised)
            print(f"Error scraper {module}: {result}")
            
            failure_info = {
                "module": module,
                "error": str(result),
                "diagnosis": None
            }
            
            # Try to diagnose if we have an API key and usage is enabled
            try:
                profile_repo = ProfileRepository(db)
                profile = profile_repo.get_profile()
                api_key = profile.groq_api_key
                use_for_fix = profile.use_for_scraper_fix
                
                if api_key and use_for_fix:
                    scraper_module = ACTIVE_SCRAPERS.get(module)
                    if scraper_module:
                        try:
                            # If it's a module
                            source_code = inspect.getsource(scraper_module)
                        except TypeError:
                            # Fallback if it's a class instance
                            source_code = inspect.getsource(scraper_module.__class__)
                            
                        error_log = "".join(traceback.format_exception(type(result), result, result.__traceback__))
                        
                        diagnosis = maintenance_service.diagnose_failure(
                            module_name=module,
                            error_log=error_log,
                            source_code=source_code,
                            api_key=api_key
                        )
                        failure_info["diagnosis"] = diagnosis
            except Exception as e:
                print(f"Diagnosis failed for {module}: {e}")
                
            failed_scrapers.append(failure_info)
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
                    
                    # Add to database
                    job_repo.add_job(job)
                    new_jobs_count += 1
                    existing_links.add(job["link"])
                else:
                    print(f"Duplicate found: {job['link']}")

    # Mark all existing jobs as not new (bulk operation)
    job_repo.mark_all_as_not_new()
    
    # Get total count
    total_jobs = len(job_repo.get_all_jobs())

    return {
        "added": new_jobs_count,
        "total": total_jobs,
        "failed_scrapers": failed_scrapers,
    }
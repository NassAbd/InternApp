# --- BASE IMPORTS ---
import asyncio
import json
import os
import math

# --- APP IMPORTS ---
# --- APP IMPORTS ---
from fastapi import FastAPI, Body, Query, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from config import ACTIVE_SCRAPERS, JSON_OUTPUT_PATH
from tagging_service import TaggingService
from profile_manager import ProfileManager
from scoring_engine import ScoringEngine
from cv_parser import CVParser
from application_manager import ApplicationManager
from maintenance_service import MaintenanceService
from database import SessionLocal
from repositories.job_repository import JobRepository
from sqlalchemy.exc import OperationalError
from database import engine
from models import Base
import inspect
import traceback
# -------------------

app = FastAPI()

@app.on_event("startup")
def on_startup():
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("Database tables created/verified.")
    except Exception as e:
        print(f"Error initializing database: {e}")


# Initialize services
tagging_service = TaggingService()
profile_manager = ProfileManager()
scoring_engine = ScoringEngine()
cv_parser = CVParser()
application_manager = ApplicationManager()
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


# --- Routes ---

@app.get("/jobs")
def get_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    modules: str = Query(None),
    search: str = Query(None),
):
    session = SessionLocal()
    try:
        repo = JobRepository(session)
        
        module_list = [m.strip().lower() for m in modules.split(",")] if modules else None
        
        # Get jobs from DB
        try:
            jobs_models, total_items = repo.get_jobs(
                skip=(page - 1) * size,
                limit=size,
                modules=module_list,
                search=search
            )
        except OperationalError:
             # Database likely missing or tables not created
            jobs_models, total_items = [], 0
        
        # Convert to dicts
        jobs_list = [job.to_dict() for job in jobs_models]
        
        # Get modules list from config
        filterable_modules = sorted(list(ACTIVE_SCRAPERS.keys()))
        
        total_pages = math.ceil(total_items / size)

        return {
            "page": page,
            "size": size,
            "total_items": total_items,
            "total_pages": total_pages,
            "jobs": jobs_list,
            "filterable_modules": filterable_modules,
        }
    finally:
        session.close()


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
        if "OperationalError" in str(e) or "no such table" in str(e):
            # Return default profile if DB is uninitialized/broken
            return {
                "tags": [],
                "location": None,
                "groq_api_key": None
            }
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if "no such table" in str(e) or "OperationalError" in str(e):
             return {
                "tags": [],
                "location": None,
                "groq_api_key": None
            }
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


@app.delete("/profile")
def reset_profile():
    """
    Reset user profile to default/empty state.
    
    Returns:
        Default empty profile
        
    Raises:
        HTTPException: If profile cannot be reset
    """
    try:
        # Create default empty profile
        default_profile = {
            "tags": [],
            "location": None,
            "groq_api_key": None
        }
        
        # Save the default profile (this will overwrite existing profile)
        profile_manager.saveProfile(default_profile)
        
        # Return the reset profile
        return profile_manager.loadProfile()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset profile: {str(e)}")


@app.post("/profile/parse-cv")
async def parse_cv(
    file: UploadFile = File(...),
    api_key: str = Form(None),
    merge_with_existing: bool = Form(True)
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
            profile = profile_manager.loadProfile()
            final_api_key = profile.get("groq_api_key")
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
        current_profile = profile_manager.loadProfile()
        
        # Merge tags if requested
        if merge_with_existing:
            existing_tags = current_profile.get("tags", [])
            final_tags = cv_parser.mergeTags(existing_tags, extracted_tags)
        else:
            final_tags = extracted_tags
        
        # Update profile with new tags and API key (only if provided explicitly)
        updated_profile = current_profile.copy()
        updated_profile["tags"] = final_tags
        if api_key and api_key.strip():
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
             # Return empty or standard list. 
             # For simpler logic, we can return standardized empty struct or call get_jobs?
             # Existing logic returned clean empty structure with message.
            return {
                "page": page,
                "size": size,
                "total_items": 0,
                "total_pages": 0,
                "jobs": [],
                "filterable_modules": [],
                "message": "No preferences set. Please configure your profile to see personalized recommendations."
            }
        
        session = SessionLocal()
        try:
            repo = JobRepository(session)
            
            module_list = [m.strip().lower() for m in modules.split(",")] if modules else None
            
            # Fetch ALL matching jobs (limit 10000) for scoring
            # We must fetch all because scoring needs to sort the entire set.
            try:
                jobs_models, _ = repo.get_jobs(
                    skip=0, 
                    limit=10000, 
                    modules=module_list, 
                    search=search
                )
            except OperationalError:
                jobs_models = []

            
            # Convert to dicts
            filtered_jobs = [job.to_dict() for job in jobs_models]
            
            # Score and filter jobs using ScoringEngine
            scored_jobs = scoring_engine.scoreJobs(user_profile, filtered_jobs)
            
            # Get filterable modules
            filterable_modules = sorted(list(ACTIVE_SCRAPERS.keys()))
            
            # Pagination in memory
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
        finally:
            session.close()
        
    except ValueError as e:
        if "OperationalError" in str(e) or "no such table" in str(e):
             return {
                "page": page,
                "size": size,
                "total_items": 0,
                "total_pages": 0,
                "jobs": [],
                "filterable_modules": [],
            }
        raise HTTPException(status_code=400, detail=f"Profile error: {str(e)}")
    except Exception as e:
        if "no such table" in str(e) or "OperationalError" in str(e):
             return {
                "page": page,
                "size": size,
                "total_items": 0,
                "total_pages": 0,
                "jobs": [],
                "filterable_modules": [],
            }
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# --- Application Tracking Endpoints ---
@app.post("/applications")
def track_application(job_data: dict = Body(...)):
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
        application = application_manager.add_application(job_data)
        return {
            "success": True,
            "data": application
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Check for operational DB errors in the exception chain or string
        if "no such table" in str(e) or "OperationalError" in str(e):
             raise HTTPException(status_code=503, detail="Database unavailable. Please try again later.")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



@app.get("/applications")
def get_tracked_applications():
    """
    Retrieve all tracked applications sorted by last update.
    
    Returns:
        List of tracked applications with metadata
        
    Raises:
        HTTPException: If applications cannot be retrieved
    """
    try:
        applications = application_manager.get_applications()
        return {
            "success": True,
            "data": applications
        }
    except Exception as e:
        if "no such table" in str(e) or "OperationalError" in str(e) or isinstance(e, OperationalError):
             # Return empty list for graceful frontend handling
             return {
                 "success": True,
                 "data": []
             }
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.patch("/applications/{job_id}")
def update_application(job_id: str, updates: dict = Body(...)):
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
        application = application_manager.update_application(job_id, updates)
        return {
            "success": True,
            "data": application
        }
    except ValueError as e:
        # Check if it's a "not found" error
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if "no such table" in str(e) or "OperationalError" in str(e):
             raise HTTPException(status_code=503, detail="Database unavailable.")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/applications/{job_id}")
def remove_application(job_id: str):
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
        removed = application_manager.remove_application(job_id)
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
        if "no such table" in str(e) or "OperationalError" in str(e):
             raise HTTPException(status_code=503, detail="Database unavailable.")
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
    # We used to load all jobs here to check duplicates relative to 'jobs'.
    # Now we will check against DB for each scraped job.
    
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
    session = SessionLocal()
    repo = JobRepository(session)
    
    new_jobs_count = 0
    failed_scrapers = []
    
    try:
        try:
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
                        profile = profile_manager.loadProfile()
                        api_key = profile.get("groq_api_key")
                        use_for_fix = profile.get("use_for_scraper_fix", False)
                        
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
                    
                    # 1. Collect potential new jobs and existing IDs for this module
                    module_new_jobs = []
                    module_existing_ids = []
                    
                    for job in site_jobs:
                        # Check if exists in DB (Read is fine, minimal I/O compared to Write)
                        # Optimization: We could pre-fetch all links if list is huge, 
                        # but for <100 jobs/module, row-by-row check is acceptable provided we don't WRITE.
                        existing_job = repo.get_job_by_link(job["link"])
                        
                        if not existing_job:
                            # Add tags to the job using TaggingService
                            job_title = job.get("title", "")
                            job_description = job.get("description", "")
                            job["tags"] = tagging_service.tagJob(job_title, job_description)
                            job["is_new"] = True
                            
                            # Add to batch list
                            module_new_jobs.append(job)
                        else:
                            # User Request: If found, mark as old (is_new = False)
                            module_existing_ids.append(existing_job.id)
                    
                    # 2. Batch Operations
                    if module_new_jobs:
                        repo.create_jobs_batch(module_new_jobs)
                        new_jobs_count += len(module_new_jobs)
                    
                    if module_existing_ids:
                        repo.mark_jobs_as_old(module_existing_ids)

            # Get total count
            _, total_count = repo.get_jobs(limit=1) 
            
            return {
                "added": new_jobs_count,
                "total": total_count,
                "failed_scrapers": failed_scrapers,
            }

        except OperationalError as e:
            print(f"Database error during scrape: {e}")
            return {
                "added": new_jobs_count,
                "total": 0,
                "failed_scrapers": failed_scrapers + [{"module": "general", "error": f"Database unavailable: {str(e)}"}],
            }
    finally:
        session.close()
"""
ApplicationManager - Core application management logic for job tracking.

This module provides functionality to add, update, remove, and query tracked job applications.
Integrates with StorageManager for data persistence and provides business logic for application tracking.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


class ApplicationManager:
    """Manages job application tracking operations via Database."""
    
    def __init__(self):
        """
        Initialize ApplicationManager.
        Uses on-demand database sessions.
        """
        from database import SessionLocal
        self.SessionLocal = SessionLocal
    
    def _serialize_application(self, app_model) -> Dict[str, Any]:
        """Convert SQLAlchemy application model to dictionary."""
        import json
        
        # Serialize Job
        job_dict = {
            "link": app_model.job.link,
            "title": app_model.job.title,
            "company": app_model.job.company,
            "location": app_model.job.location,
            "tags": json.loads(app_model.job.tags) if app_model.job.tags else [],
            "new": app_model.job.is_new
        }
        
        # Serialize Application
        return {
            "id": app_model.id,
            "status": app_model.status,
            "date_added": app_model.date_added.isoformat().replace('+00:00', 'Z') if app_model.date_added else None,
            "last_update": app_model.last_update.isoformat().replace('+00:00', 'Z') if app_model.last_update else None,
            "notes": app_model.notes,
            "job": job_dict
        }

    def add_application(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a job to the tracking list."""
        from repositories.job_repository import JobRepository
        from repositories.application_repository import ApplicationRepository
        
        session = self.SessionLocal()
        try:
            # 1. Ensure Job exists
            job_repo = JobRepository(session)
            job_obj = job_repo.upsert_job(job_data)
            
            # 2. Create Application
            app_repo = ApplicationRepository(session)
            app_obj = app_repo.add_application(job_obj)
            
            return self._serialize_application(app_obj)
        except Exception as e:
            raise ValueError(f"Error adding application: {e}")
        finally:
            session.close()
    
    def get_applications(self) -> List[Dict[str, Any]]:
        """Retrieve all tracked applications."""
        from repositories.application_repository import ApplicationRepository
        
        session = self.SessionLocal()
        try:
            app_repo = ApplicationRepository(session)
            apps = app_repo.get_all_applications()
            return [self._serialize_application(app) for app in apps]
        except Exception as e:
            raise ValueError(f"Error getting applications: {e}")
        finally:
            session.close()
    
    def update_application(self, job_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing application."""
        from repositories.application_repository import ApplicationRepository
        
        session = self.SessionLocal()
        try:
            app_repo = ApplicationRepository(session)
            updated_app = app_repo.update_application(job_id, updates)
            
            if not updated_app:
                raise ValueError(f"Application with ID {job_id} not found")
                
            return self._serialize_application(updated_app)
        except Exception as e:
            raise ValueError(f"Error updating application: {e}")
        finally:
            session.close()
    
    def remove_application(self, job_id: str) -> bool:
        """Remove an application from tracking."""
        from repositories.application_repository import ApplicationRepository
        
        session = self.SessionLocal()
        try:
            app_repo = ApplicationRepository(session)
            return app_repo.delete_application(job_id)
        except Exception as e:
            raise ValueError(f"Error removing application: {e}")
        finally:
            session.close()
    
    def is_job_tracked(self, job_id: str) -> bool:
        """
        Check if a job is currently being tracked.
        Note: The legacy version used job_id (application id) but semantically we often want to check by job link.
        However, keeping signature consistent.
        """
        from repositories.application_repository import ApplicationRepository
        session = self.SessionLocal()
        try:
            app_repo = ApplicationRepository(session)
            return app_repo.get_application(job_id) is not None
        finally:
            session.close()
    
    def get_application_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific application by ID."""
        from repositories.application_repository import ApplicationRepository
        
        session = self.SessionLocal()
        try:
            app_repo = ApplicationRepository(session)
            app = app_repo.get_application(job_id)
            return self._serialize_application(app) if app else None
        finally:
            session.close()
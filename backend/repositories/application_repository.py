"""
ApplicationRepository - Data access layer for UserApplication model.

Provides methods to manage user's tracked job applications.
"""

from sqlalchemy.orm import Session, joinedload
from models import UserApplication, Job, ApplicationStatus
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import hashlib


class ApplicationRepository:
    """Repository for UserApplication database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize ApplicationRepository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def _generate_application_id(self, job_link: str) -> str:
        """
        Generate application ID from job link (MD5 hash for compatibility).
        
        Args:
            job_link: Job URL
            
        Returns:
            MD5 hash string
        """
        return hashlib.md5(job_link.encode('utf-8')).hexdigest()
    
    def add_application(self, job_data: Dict[str, Any]) -> UserApplication:
        """
        Add a job to application tracking.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            Created UserApplication instance
            
        Raises:
            ValueError: If job data is invalid
        """
        if not job_data.get("link"):
            raise ValueError("Job must have a 'link' field")
        
        # Generate application ID
        app_id = self._generate_application_id(job_data["link"])
        
        # Check if application already exists
        existing_app = self.get_by_id(app_id)
        if existing_app:
            return existing_app
        
        # Find or create job
        from repositories.job_repository import JobRepository
        job_repo = JobRepository(self.db)
        job = job_repo.get_job_by_link(job_data["link"])
        
        if not job:
            # Create job if it doesn't exist
            job = job_repo.add_job(job_data)
        
        # Create application
        current_time = datetime.now(timezone.utc)
        application = UserApplication(
            id=app_id,
            job_id=job.id,
            status=ApplicationStatus.INTERESTED,
            date_added=current_time,
            last_update=current_time,
        )
        
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        
        return application
    
    def get_applications(self) -> List[UserApplication]:
        """
        Retrieve all tracked applications sorted by last_update.
        
        Returns:
            List of UserApplication instances with job data loaded
        """
        return (
            self.db.query(UserApplication)
            .options(joinedload(UserApplication.job))
            .order_by(UserApplication.last_update.desc())
            .all()
        )
    
    def get_by_id(self, app_id: str) -> Optional[UserApplication]:
        """
        Get a specific application by ID.
        
        Args:
            app_id: Application ID
            
        Returns:
            UserApplication instance if found, None otherwise
        """
        return (
            self.db.query(UserApplication)
            .options(joinedload(UserApplication.job))
            .filter(UserApplication.id == app_id)
            .first()
        )
    
    def update_application(self, app_id: str, updates: Dict[str, Any]) -> Optional[UserApplication]:
        """
        Update an existing application.
        
        Args:
            app_id: Application ID to update
            updates: Dictionary containing fields to update (status, notes)
            
        Returns:
            Updated UserApplication instance if found, None otherwise
            
        Raises:
            ValueError: If updates contain invalid data
        """
        application = self.get_by_id(app_id)
        if not application:
            return None
        
        # Update status if provided
        if "status" in updates:
            status_value = updates["status"]
            # Handle both string and enum values
            if isinstance(status_value, str):
                try:
                    application.status = ApplicationStatus(status_value)
                except ValueError:
                    raise ValueError(f"Invalid status: {status_value}")
            else:
                application.status = status_value
        
        # Update notes if provided
        if "notes" in updates:
            application.notes = updates["notes"]
        
        # Update timestamp
        application.last_update = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(application)
        
        return application
    
    def remove_application(self, app_id: str) -> bool:
        """
        Remove an application from tracking.
        
        Args:
            app_id: Application ID to remove
            
        Returns:
            True if application was removed, False if not found
        """
        application = self.get_by_id(app_id)
        if not application:
            return False
        
        self.db.delete(application)
        self.db.commit()
        
        return True
    
    def is_job_tracked(self, job_id: str) -> bool:
        """
        Check if a job is currently being tracked.
        
        Args:
            job_id: Application ID to check
            
        Returns:
            True if job is tracked, False otherwise
        """
        return self.get_by_id(job_id) is not None

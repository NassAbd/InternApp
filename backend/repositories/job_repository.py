"""
JobRepository - Data access layer for Job model.

Provides methods to manage job postings in the database.
"""

from sqlalchemy.orm import Session
from models import Job
from typing import List, Optional, Dict, Any


class JobRepository:
    """Repository for Job database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize JobRepository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def add_job(self, job_data: Dict[str, Any]) -> Job:
        """
        Add a new job to the database.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            Created Job model instance
            
        Raises:
            ValueError: If job with same link already exists
        """
        # Check if job already exists
        existing_job = self.get_job_by_link(job_data.get("link"))
        if existing_job:
            # Return existing job (idempotent)
            return existing_job
        
        # Create new job
        job = Job(
            link=job_data["link"],
            module=job_data["module"],
            company=job_data["company"],
            title=job_data["title"],
            location=job_data.get("location"),
            tags=job_data.get("tags", []),
            new=job_data.get("new", True),
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        return job
    
    def get_all_jobs(self) -> List[Job]:
        """
        Retrieve all jobs from database.
        
        Returns:
            List of all Job instances
        """
        return self.db.query(Job).all()
    
    def get_job_by_link(self, link: str) -> Optional[Job]:
        """
        Find a job by its URL.
        
        Args:
            link: Job URL
            
        Returns:
            Job instance if found, None otherwise
        """
        return self.db.query(Job).filter(Job.link == link).first()
    
    def get_job_by_id(self, job_id: int) -> Optional[Job]:
        """
        Find a job by its database ID.
        
        Args:
            job_id: Job database ID
            
        Returns:
            Job instance if found, None otherwise
        """
        return self.db.query(Job).filter(Job.id == job_id).first()
    
    def update_job(self, link: str, updates: Dict[str, Any]) -> Optional[Job]:
        """
        Update an existing job.
        
        Args:
            link: Job URL to identify the job
            updates: Dictionary of fields to update
            
        Returns:
            Updated Job instance if found, None otherwise
        """
        job = self.get_job_by_link(link)
        if not job:
            return None
        
        # Update allowed fields
        for key, value in updates.items():
            if hasattr(job, key):
                setattr(job, key, value)
        
        self.db.commit()
        self.db.refresh(job)
        
        return job
    
    def mark_all_as_not_new(self) -> int:
        """
        Mark all jobs as not new (bulk update).
        
        Returns:
            Number of jobs updated
        """
        result = self.db.query(Job).filter(Job.new).update({"new": False})
        self.db.commit()
        
        return result
    
    def delete_job(self, link: str) -> bool:
        """
        Delete a job from the database.
        
        Args:
            link: Job URL
            
        Returns:
            True if job was deleted, False if not found
        """
        job = self.get_job_by_link(link)
        if not job:
            return False
        
        self.db.delete(job)
        self.db.commit()
        
        return True

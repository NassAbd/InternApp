from sqlalchemy.orm import Session
from models import Job
from typing import Dict, Any, Optional, List, Tuple


class JobRepository:
    """Repository for managing Job database operations."""
    def __init__(self, db: Session):

        self.db = db

    def get_job_by_link(self, link: str) -> Optional[Job]:
        return self.db.query(Job).filter(Job.link == link).first()
    
    def get_job_by_id(self, job_id: int) -> Optional[Job]:
        return self.db.query(Job).filter(Job.id == job_id).first()

    def create_job(self, job_data: Dict[str, Any]) -> Job:
        """Create a new job record."""
        tags = job_data.get("tags")
        if isinstance(tags, list):
            import json
            tags = json.dumps(tags)
            
        new_job = Job(
            link=job_data["link"],
            title=job_data.get("title"),
            company=job_data.get("company"),
            location=job_data.get("location"),
            tags=tags,
            is_new=job_data.get("is_new", True),
            module=job_data.get("module")
        )
        self.db.add(new_job)
        self.db.commit()
        self.db.refresh(new_job)
        return new_job

    def create_jobs_batch(self, jobs_data: List[Dict[str, Any]]) -> int:
        """
        Create multiple job records in a single transaction.
        Returns the number of jobs created.
        """
        if not jobs_data:
            return 0
            
        import json
        new_jobs = []
        for job_data in jobs_data:
            tags = job_data.get("tags")
            if isinstance(tags, list):
                tags = json.dumps(tags)
                
            new_job = Job(
                link=job_data["link"],
                title=job_data.get("title"),
                company=job_data.get("company"),
                location=job_data.get("location"),
                tags=tags,
                is_new=job_data.get("is_new", True),
                module=job_data.get("module")
            )
            self.db.add(new_job)
        
        self.db.commit()
        return len(new_jobs)

    def mark_jobs_as_old(self, job_ids: List[int]) -> int:
        """
        Mark multiple jobs as not new (is_new=False).
        Returns the number of jobs updated.
        """
        if not job_ids:
            return 0
            
        updated_count = self.db.query(Job).filter(Job.id.in_(job_ids)).update(
            {Job.is_new: False}, 
            synchronize_session=False
        )
        self.db.commit()
        return updated_count



    def upsert_job(self, job_data: Dict[str, Any]) -> Job:
        """Get existing job by link or create new one. DOES NOT update existing."""
        existing_job = self.get_job_by_link(job_data["link"])
        if existing_job:
            if not existing_job.module and job_data.get("module"):
                existing_job.module = job_data.get("module")
                self.db.commit()
            return existing_job
        return self.create_job(job_data)
        
    def get_jobs(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        modules: Optional[List[str]] = None, 
        search: Optional[str] = None
    ) -> tuple[list[Job], int]:
        """
        Get jobs with optional filtering and pagination.
        Returns: (list_of_jobs, total_count)
        """

        # Order by ID desc (effectively date desc) or date_scraped desc
        query = self.db.query(Job).order_by(Job.date_scraped.desc())

        
        if modules:
            query = query.filter(Job.module.in_(modules))
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Job.title.ilike(search_term)) | 
                (Job.company.ilike(search_term)) | 
                (Job.location.ilike(search_term))
            )
            
        total = query.count()
        
        jobs = query.offset(skip).limit(limit).all()
        
        return jobs, total

    def get_all_jobs_no_pagination(self) -> list[Job]:
        """Get all jobs (useful for batch processing/scoring if dataset is small)."""
        return self.db.query(Job).all()

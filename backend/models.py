"""
SQLAlchemy models for InternApp database.

This module defines the database schema using SQLAlchemy ORM:
- Job: Job postings from various scrapers
- UserProfile: User preferences and settings (singleton)
- UserApplication: User's tracked job applications
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class ApplicationStatus(str, enum.Enum):
    """Enumeration of possible application statuses."""
    INTERESTED = "Interested"
    APPLIED = "Applied"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    REJECTED = "Rejected"


class Job(Base):
    """
    Job posting model.
    
    Represents job opportunities scraped from various sources.
    Each job is uniquely identified by its link URL.
    """
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    link = Column(String, unique=True, nullable=False, index=True)
    module = Column(String, nullable=False, index=True)  # Scraper source (e.g., "airbus", "cnes")
    company = Column(String, nullable=False)
    title = Column(String, nullable=False)
    location = Column(String, nullable=True)
    tags = Column(JSON, nullable=False, default=list)  # List of tags as JSON array
    new = Column(Boolean, nullable=False, default=True)  # Flag for newly scraped jobs
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship to applications
    applications = relationship("UserApplication", back_populates="job", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "link": self.link,
            "module": self.module,
            "company": self.company,
            "title": self.title,
            "location": self.location,
            "tags": self.tags or [],
            "new": self.new,
        }


class UserProfile(Base):
    """
    User profile model (singleton).
    
    Stores user preferences, settings, and API keys.
    There should only be one UserProfile record (id=1).
    """
    __tablename__ = "user_profile"
    
    id = Column(Integer, primary_key=True, default=1)  # Singleton - always id=1
    tags = Column(JSON, nullable=False, default=list)  # User interest tags
    location = Column(String, nullable=True)  # Preferred location
    groq_api_key = Column(String, nullable=True)  # API key for LLM features
    use_for_scraper_fix = Column(Boolean, nullable=False, default=False)  # Enable AI diagnostics
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "tags": self.tags or [],
            "location": self.location,
            "groq_api_key": self.groq_api_key,
            "use_for_scraper_fix": self.use_for_scraper_fix,
        }


class UserApplication(Base):
    """
    User application tracking model.
    
    Represents a job that the user is tracking through the application process.
    Links to a Job record and stores application-specific metadata.
    """
    __tablename__ = "user_applications"
    
    id = Column(String, primary_key=True)  # MD5 hash of job link (for compatibility)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    status = Column(SQLEnum(ApplicationStatus), nullable=False, default=ApplicationStatus.INTERESTED)
    date_added = Column(DateTime(timezone=True), nullable=False)
    last_update = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationship to job
    job = relationship("Job", back_populates="applications")
    
    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "job": self.job.to_dict() if self.job else None,
            "status": self.status.value if isinstance(self.status, ApplicationStatus) else self.status,
            "date_added": self.date_added.isoformat().replace('+00:00', 'Z') if self.date_added else None,
            "last_update": self.last_update.isoformat().replace('+00:00', 'Z') if self.last_update else None,
            "notes": self.notes,
        }

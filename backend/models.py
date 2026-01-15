from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    link = Column(String, unique=True, index=True)
    title = Column(String)
    company = Column(String)
    location = Column(String)
    tags = Column(String)  # Storing as JSON string or comma-separated
    is_new = Column(Boolean, default=True)
    date_scraped = Column(DateTime(timezone=True), server_default=func.now())
    module = Column(String)

    # Relationship
    applications = relationship("UserApplication", back_populates="job")

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "link": self.link,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "tags": json.loads(self.tags) if self.tags else [],
            "is_new": self.is_new,
            "new": self.is_new, # For compatibility with frontend expecting 'new'
            "date_scraped": self.date_scraped.isoformat() if self.date_scraped else None,
            "module": self.module
        }

class UserProfile(Base):
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, index=True)
    tags = Column(String)  # JSON string
    location_preference = Column(String, nullable=True)
    groq_api_key = Column(String, nullable=True)
    use_for_scraper_fix = Column(Boolean, default=False)

class UserApplication(Base):
    __tablename__ = "applications"

    id = Column(String, primary_key=True, index=True) # MD5 Hash of link
    job_id = Column(Integer, ForeignKey("jobs.id"))
    status = Column(String) # Enum values handled at app level
    date_added = Column(DateTime)
    last_update = Column(DateTime)
    notes = Column(String, nullable=True)

    # Relationship
    job = relationship("Job", back_populates="applications")

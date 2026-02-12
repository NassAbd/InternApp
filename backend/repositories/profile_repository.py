"""
ProfileRepository - Data access layer for UserProfile model.

Provides methods to manage user profile (singleton pattern).
"""

from sqlalchemy.orm import Session
from models import UserProfile
from typing import Dict, Any, List, Optional


class ProfileRepository:
    """Repository for UserProfile database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize ProfileRepository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_profile(self) -> UserProfile:
        """
        Get user profile (creates default if doesn't exist).
        
        Returns:
            UserProfile instance
        """
        profile = self.db.query(UserProfile).filter(UserProfile.id == 1).first()
        
        if not profile:
            # Create default profile
            profile = UserProfile(
                id=1,
                tags=[],
                location=None,
                groq_api_key=None,
                use_for_scraper_fix=False,
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        
        return profile
    
    def save_profile(self, profile_data: Dict[str, Any]) -> UserProfile:
        """
        Save/update user profile.
        
        Args:
            profile_data: Dictionary containing profile fields
            
        Returns:
            Updated UserProfile instance
        """
        profile = self.get_profile()
        
        # Update fields if provided
        if "tags" in profile_data:
            profile.tags = profile_data["tags"]
        if "location" in profile_data:
            profile.location = profile_data["location"]
        if "groq_api_key" in profile_data:
            profile.groq_api_key = profile_data["groq_api_key"]
        if "use_for_scraper_fix" in profile_data:
            profile.use_for_scraper_fix = profile_data["use_for_scraper_fix"]
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    def update_tags(self, tags: List[str]) -> UserProfile:
        """
        Update user interest tags.
        
        Args:
            tags: List of tag strings
            
        Returns:
            Updated UserProfile instance
        """
        profile = self.get_profile()
        profile.tags = tags
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    def update_location(self, location: Optional[str]) -> UserProfile:
        """
        Update user location preference.
        
        Args:
            location: Location string or None
            
        Returns:
            Updated UserProfile instance
        """
        profile = self.get_profile()
        profile.location = location
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    def update_groq_api_key(self, api_key: Optional[str]) -> UserProfile:
        """
        Update Groq API key.
        
        Args:
            api_key: API key string or None
            
        Returns:
            Updated UserProfile instance
        """
        profile = self.get_profile()
        profile.groq_api_key = api_key
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile

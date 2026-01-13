from sqlalchemy.orm import Session
from models import UserProfile
from typing import Dict, Any, List
import json

class ProfileRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_profile(self) -> UserProfile:
        """Get the single user profile or create it if missing."""
        profile = self.db.query(UserProfile).first()
        if not profile:
            # Create default profile
            profile = UserProfile(
                tags=json.dumps([]),
                location_preference=None,
                groq_api_key=None,
                use_for_scraper_fix=False
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        return profile

    def update_profile(self, updates: Dict[str, Any]) -> UserProfile:
        profile = self.get_profile()
        
        if "tags" in updates:
            tags = updates["tags"]
            if isinstance(tags, list):
                profile.tags = json.dumps(tags)
            else:
                profile.tags = tags # Assume already stringified if not list
                
        if "location" in updates: # Mapping 'location' key from frontend to 'location_preference'
            profile.location_preference = updates["location"]
            
        if "location_preference" in updates:
            profile.location_preference = updates["location_preference"]
            
        if "groq_api_key" in updates:
            profile.groq_api_key = updates["groq_api_key"]
            
        if "use_for_scraper_fix" in updates:
            profile.use_for_scraper_fix = updates["use_for_scraper_fix"]
            
        self.db.commit()
        self.db.refresh(profile)
        return profile

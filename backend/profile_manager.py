"""
ProfileManager - Manages user profile data including tags, location preferences, and API keys.

This module provides functionality to load, save, and update user profiles stored in JSON format.
Handles file system operations with proper error handling and data validation.
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class ProfileManager:
    """Manages user profile data and persistence operations via Database."""
    
    def __init__(self):
        """
        Initialize ProfileManager.
        Uses on-demand database sessions for operations.
        """
        from database import SessionLocal
        self.SessionLocal = SessionLocal
    
    def loadProfile(self) -> Dict[str, Any]:
        """
        Load user profile from Database.
        
        Returns:
            Dict containing user profile data with keys: tags, location, groq_api_key
        """
        from repositories.profile_repository import ProfileRepository
        import json
        
        session = self.SessionLocal()
        try:
            repo = ProfileRepository(session)
            profile_model = repo.get_profile()
            
            # Serialize to dict to maintain contract with main.py
            return {
                "tags": json.loads(profile_model.tags) if profile_model.tags else [],
                "location": profile_model.location_preference,
                "groq_api_key": profile_model.groq_api_key,
                "use_for_scraper_fix": profile_model.use_for_scraper_fix
            }
        except Exception as e:
            raise ValueError(f"Error loading profile: {e}")
        finally:
            session.close()
    
    def saveProfile(self, profile_data: Dict[str, Any]) -> None:
        """
        Save user profile data to Database.
        
        Args:
            profile_data: Dictionary containing profile data
        """
        from repositories.profile_repository import ProfileRepository
        
        session = self.SessionLocal()
        try:
            repo = ProfileRepository(session)
            repo.update_profile(profile_data)
        except Exception as e:
            raise IOError(f"Error saving profile: {e}")
        finally:
            session.close()
    
    def updateTags(self, tags: List[str]) -> Dict[str, Any]:
        """Update user interest tags in the profile."""
        if not isinstance(tags, list):
            raise ValueError("Tags must be a list")
            
        cleaned_tags = [str(tag).strip() for tag in tags if str(tag).strip()]
        
        # Use saveProfile logic which uses repository
        self.saveProfile({"tags": cleaned_tags})
        return self.loadProfile()
    
    def setLocationPreference(self, location: Optional[str]) -> Dict[str, Any]:
        """Set user location preference in the profile."""
        loc_val = location.strip() if location else None
        self.saveProfile({"location": loc_val})
        return self.loadProfile()
    
    def setGroqApiKey(self, api_key: Optional[str]) -> Dict[str, Any]:
        """Set Groq API key in the profile."""
        key_val = api_key.strip() if api_key else None
        self.saveProfile({"groq_api_key": key_val})
        return self.loadProfile()
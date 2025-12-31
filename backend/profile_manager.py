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
    """Manages user profile data and persistence operations."""
    
    def __init__(self, profile_path: str = "user_profile.json"):
        """
        Initialize ProfileManager with specified profile file path.
        
        Args:
            profile_path: Path to the user profile JSON file
        """
        self.profile_path = Path(profile_path)
        self._default_profile = {
            "tags": [],
            "location": None,
            "groq_api_key": None
        }
    
    def loadProfile(self) -> Dict[str, Any]:
        """
        Load user profile from JSON file or create default profile if file doesn't exist.
        
        Returns:
            Dict containing user profile data with keys: tags, location, groq_api_key
            
        Raises:
            ValueError: If profile file is corrupted or contains invalid data
        """
        try:
            if not self.profile_path.exists():
                # Create default profile file if it doesn't exist
                self.saveProfile(self._default_profile)
                return self._default_profile.copy()
            
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            # Validate profile structure and provide defaults for missing keys
            validated_profile = self._validate_profile(profile_data)
            return validated_profile
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Profile file is corrupted: {e}")
        except Exception as e:
            raise ValueError(f"Error loading profile: {e}")
    
    def saveProfile(self, profile: Dict[str, Any]) -> None:
        """
        Save user profile data to JSON file with proper error handling.
        
        Args:
            profile: Dictionary containing profile data
            
        Raises:
            ValueError: If profile data is invalid
            IOError: If file cannot be written
        """
        try:
            # Validate profile before saving
            validated_profile = self._validate_profile(profile)
            
            # Ensure directory exists
            self.profile_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write profile data
            with open(self.profile_path, 'w', encoding='utf-8') as f:
                json.dump(validated_profile, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise IOError(f"Error saving profile: {e}")
    
    def updateTags(self, tags: List[str]) -> Dict[str, Any]:
        """
        Update user interest tags in the profile.
        
        Args:
            tags: List of tag strings representing user interests
            
        Returns:
            Updated profile dictionary
            
        Raises:
            ValueError: If tags parameter is invalid
        """
        if not isinstance(tags, list):
            raise ValueError("Tags must be a list")
        
        # Validate and clean tags
        cleaned_tags = [str(tag).strip() for tag in tags if str(tag).strip()]
        
        profile = self.loadProfile()
        profile["tags"] = cleaned_tags
        self.saveProfile(profile)
        
        return profile
    
    def setLocationPreference(self, location: Optional[str]) -> Dict[str, Any]:
        """
        Set user location preference in the profile.
        
        Args:
            location: Location string or None to clear preference
            
        Returns:
            Updated profile dictionary
        """
        profile = self.loadProfile()
        profile["location"] = location.strip() if location else None
        self.saveProfile(profile)
        
        return profile
    
    def setGroqApiKey(self, api_key: Optional[str]) -> Dict[str, Any]:
        """
        Set Groq API key in the profile (for CV parsing functionality).
        
        Args:
            api_key: API key string or None to clear
            
        Returns:
            Updated profile dictionary
        """
        profile = self.loadProfile()
        profile["groq_api_key"] = api_key.strip() if api_key else None
        self.saveProfile(profile)
        
        return profile
    
    def _validate_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize profile data structure.
        
        Args:
            profile: Raw profile data dictionary
            
        Returns:
            Validated and normalized profile dictionary
            
        Raises:
            ValueError: If profile structure is invalid
        """
        if not isinstance(profile, dict):
            raise ValueError("Profile must be a dictionary")
        
        # Create validated profile with defaults
        validated = self._default_profile.copy()
        
        # Validate tags
        if "tags" in profile:
            if isinstance(profile["tags"], list):
                validated["tags"] = [str(tag).strip() for tag in profile["tags"] if str(tag).strip()]
            else:
                raise ValueError("Tags must be a list")
        
        # Validate location
        if "location" in profile:
            if profile["location"] is None or isinstance(profile["location"], str):
                validated["location"] = profile["location"]
            else:
                raise ValueError("Location must be a string or None")
        
        # Validate groq_api_key
        if "groq_api_key" in profile:
            if profile["groq_api_key"] is None or isinstance(profile["groq_api_key"], str):
                validated["groq_api_key"] = profile["groq_api_key"]
            else:
                raise ValueError("Groq API key must be a string or None")
        
        return validated
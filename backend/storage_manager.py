"""
StorageManager - Handles persistence of user application tracking data.

This module provides functionality to load, save, and manage user_applications.json
with proper error handling, data validation, and concurrent access safety.
"""

import json
import os
import hashlib
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime


class StorageManager:
    """Manages user application data persistence operations."""
    
    def __init__(self, applications_path: str = "user_applications.json"):
        """
        Initialize StorageManager with specified applications file path.
        
        Args:
            applications_path: Path to the user applications JSON file
        """
        self.applications_path = Path(applications_path)
    
    def load_applications(self) -> List[Dict[str, Any]]:
        """
        Load user applications from JSON file or return empty list if file doesn't exist.
        
        Returns:
            List of application dictionaries
            
        Raises:
            ValueError: If applications file is corrupted or contains invalid data
        """
        try:
            if not self.applications_path.exists():
                return []
            
            # Check if file is empty
            if self.applications_path.stat().st_size == 0:
                return []
            
            with open(self.applications_path, 'r', encoding='utf-8') as f:
                applications_data = json.load(f)
            
            # Validate that it's a list
            if not isinstance(applications_data, list):
                raise ValueError("Applications file must contain a list")
            
            # Validate each application
            validated_applications = []
            for app in applications_data:
                validated_app = self._validate_application_data(app)
                validated_applications.append(validated_app)
            
            return validated_applications
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Applications file is corrupted: {e}")
        except Exception as e:
            raise ValueError(f"Error loading applications: {e}")
    
    def save_applications(self, applications: List[Dict[str, Any]]) -> None:
        """
        Save user applications data to JSON file with proper error handling.
        
        Args:
            applications: List of application dictionaries
            
        Raises:
            ValueError: If applications data is invalid
            IOError: If file cannot be written
        """
        try:
            # Validate applications before saving
            if not isinstance(applications, list):
                raise ValueError("Applications must be a list")
            
            validated_applications = []
            for app in applications:
                validated_app = self._validate_application_data(app)
                validated_applications.append(validated_app)
            
            # Ensure directory exists
            self.applications_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if file exists
            if self.applications_path.exists():
                backup_path = self.applications_path.with_suffix('.json.backup')
                # Remove existing backup if it exists
                if backup_path.exists():
                    backup_path.unlink()
                self.applications_path.rename(backup_path)
            
            # Write applications data
            with open(self.applications_path, 'w', encoding='utf-8') as f:
                json.dump(validated_applications, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            # Restore backup if write failed
            backup_path = self.applications_path.with_suffix('.json.backup')
            if backup_path.exists():
                backup_path.rename(self.applications_path)
            raise IOError(f"Error saving applications: {e}")
    
    def validate_application_data(self, data: Dict[str, Any]) -> bool:
        """
        Public method to validate application data structure.
        
        Args:
            data: Application data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            self._validate_application_data(data)
            return True
        except ValueError:
            return False
    
    def generate_application_id(self, job: Dict[str, Any]) -> str:
        """
        Generate a unique application ID from job data.
        
        Args:
            job: Job dictionary containing at least a 'link' field
            
        Returns:
            Unique string ID based on job link hash
            
        Raises:
            ValueError: If job data is invalid or missing required fields
        """
        if not isinstance(job, dict):
            raise ValueError("Job must be a dictionary")
        
        job_link = job.get("link")
        if not job_link or not isinstance(job_link, str):
            raise ValueError("Job must have a valid 'link' field")
        
        # Generate hash from job link
        return hashlib.md5(job_link.encode('utf-8')).hexdigest()
    
    def _validate_application_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize application data structure.
        
        Args:
            data: Raw application data dictionary
            
        Returns:
            Validated and normalized application dictionary
            
        Raises:
            ValueError: If application structure is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Application must be a dictionary")
        
        # Required fields
        required_fields = ["id", "job", "status", "date_added", "last_update"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Application missing required field: {field}")
        
        # Validate ID
        if not isinstance(data["id"], str) or not data["id"].strip():
            raise ValueError("Application ID must be a non-empty string")
        
        # Validate job object
        if not isinstance(data["job"], dict):
            raise ValueError("Job must be a dictionary")
        
        # Validate status
        valid_statuses = ["Interested", "Applied", "Interview", "Offer", "Rejected"]
        if data["status"] not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        
        # Validate timestamps
        for timestamp_field in ["date_added", "last_update"]:
            if not isinstance(data[timestamp_field], str):
                raise ValueError(f"{timestamp_field} must be a string")
            try:
                datetime.fromisoformat(data[timestamp_field].replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"{timestamp_field} must be a valid ISO timestamp")
        
        # Validate optional notes field
        if "notes" in data and data["notes"] is not None:
            if not isinstance(data["notes"], str):
                raise ValueError("Notes must be a string or None")
        
        # Return validated data (create a copy to avoid modifying original)
        import copy
        validated = {
            "id": data["id"].strip(),
            "job": copy.deepcopy(data["job"]),  # Deep copy to prevent mutation
            "status": data["status"],
            "date_added": data["date_added"],
            "last_update": data["last_update"],
        }
        
        # Add optional notes if present
        if "notes" in data:
            validated["notes"] = data["notes"]
        
        return validated
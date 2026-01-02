"""
ApplicationManager - Core application management logic for job tracking.

This module provides functionality to add, update, remove, and query tracked job applications.
Integrates with StorageManager for data persistence and provides business logic for application tracking.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from storage_manager import StorageManager


class ApplicationManager:
    """Manages job application tracking operations."""
    
    def __init__(self, storage_manager: Optional[StorageManager] = None):
        """
        Initialize ApplicationManager with storage manager.
        
        Args:
            storage_manager: StorageManager instance for data persistence
        """
        self.storage_manager = storage_manager or StorageManager()
    
    def add_application(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a job to the tracking list.
        
        Args:
            job_data: Job dictionary containing job information
            
        Returns:
            Created application dictionary
            
        Raises:
            ValueError: If job data is invalid or job is already tracked
        """
        if not isinstance(job_data, dict):
            raise ValueError("Job data must be a dictionary")
        
        # Generate application ID
        app_id = self.storage_manager.generate_application_id(job_data)
        
        # Load existing applications
        applications = self.storage_manager.load_applications()
        
        # Check if job is already tracked (idempotence)
        for app in applications:
            if app["id"] == app_id:
                # Return existing application without modification
                return app
        
        # Create new application
        current_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        new_application = {
            "id": app_id,
            "job": job_data.copy(),  # Create a copy to avoid modifying original
            "status": "Interested",  # Default status
            "date_added": current_time,
            "last_update": current_time,
        }
        
        # Add to applications list
        applications.append(new_application)
        
        # Save to storage
        self.storage_manager.save_applications(applications)
        
        return new_application
    
    def get_applications(self) -> List[Dict[str, Any]]:
        """
        Retrieve all tracked applications sorted by last_update.
        
        Returns:
            List of application dictionaries sorted by last_update (newest first)
        """
        applications = self.storage_manager.load_applications()
        
        # Sort by last_update timestamp (newest first)
        applications.sort(key=lambda app: app["last_update"], reverse=True)
        
        return applications
    
    def update_application(self, job_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing application.
        
        Args:
            job_id: Application ID to update
            updates: Dictionary containing fields to update (status, notes)
            
        Returns:
            Updated application dictionary
            
        Raises:
            ValueError: If job_id is invalid or application not found
            ValueError: If updates contain invalid data
        """
        if not isinstance(job_id, str) or not job_id.strip():
            raise ValueError("Job ID must be a non-empty string")
        
        if not isinstance(updates, dict):
            raise ValueError("Updates must be a dictionary")
        
        # Load applications
        applications = self.storage_manager.load_applications()
        
        # Find application to update
        app_index = None
        for i, app in enumerate(applications):
            if app["id"] == job_id:
                app_index = i
                break
        
        if app_index is None:
            raise ValueError(f"Application with ID {job_id} not found")
        
        # Validate and apply updates
        application = applications[app_index].copy()
        
        # Update status if provided
        if "status" in updates:
            valid_statuses = ["Interested", "Applied", "Interview", "Offer", "Rejected"]
            if updates["status"] not in valid_statuses:
                raise ValueError(f"Status must be one of: {valid_statuses}")
            application["status"] = updates["status"]
        
        # Update notes if provided
        if "notes" in updates:
            if updates["notes"] is not None and not isinstance(updates["notes"], str):
                raise ValueError("Notes must be a string or None")
            application["notes"] = updates["notes"]
        
        # Update timestamp
        application["last_update"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        # Replace in applications list
        applications[app_index] = application
        
        # Save to storage
        self.storage_manager.save_applications(applications)
        
        return application
    
    def remove_application(self, job_id: str) -> bool:
        """
        Remove an application from tracking.
        
        Args:
            job_id: Application ID to remove
            
        Returns:
            True if application was removed, False if not found
            
        Raises:
            ValueError: If job_id is invalid
        """
        if not isinstance(job_id, str) or not job_id.strip():
            raise ValueError("Job ID must be a non-empty string")
        
        # Load applications
        applications = self.storage_manager.load_applications()
        
        # Find and remove application
        original_length = len(applications)
        applications = [app for app in applications if app["id"] != job_id]
        
        # Check if anything was removed
        if len(applications) == original_length:
            return False
        
        # Save updated applications
        self.storage_manager.save_applications(applications)
        
        return True
    
    def is_job_tracked(self, job_id: str) -> bool:
        """
        Check if a job is currently being tracked.
        
        Args:
            job_id: Job ID to check
            
        Returns:
            True if job is tracked, False otherwise
        """
        if not isinstance(job_id, str) or not job_id.strip():
            return False
        
        applications = self.storage_manager.load_applications()
        
        for app in applications:
            if app["id"] == job_id:
                return True
        
        return False
    
    def get_application_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific application by ID.
        
        Args:
            job_id: Application ID to retrieve
            
        Returns:
            Application dictionary if found, None otherwise
        """
        if not isinstance(job_id, str) or not job_id.strip():
            return None
        
        applications = self.storage_manager.load_applications()
        
        for app in applications:
            if app["id"] == job_id:
                return app
        
        return None
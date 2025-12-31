"""
ScoringEngine - Calculates relevance scores for jobs based on user profiles.

This module provides functionality to score jobs based on user preferences,
filter out irrelevant jobs, and sort results by relevance score.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ScoredJob:
    """Data structure for a job with calculated relevance score."""
    job_data: Dict[str, Any]
    match_score: int
    matching_tags: List[str]


class ScoringEngine:
    """Engine for calculating job relevance scores based on user profiles."""
    
    # Scoring weights
    TAG_MATCH_POINTS = 10
    LOCATION_MATCH_POINTS = 5
    NEW_JOB_BONUS_POINTS = 2
    
    def __init__(self):
        """Initialize ScoringEngine with default scoring parameters."""
        pass
    
    def scoreJobs(self, user_profile: Dict[str, Any], jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score all jobs based on user profile and return filtered, sorted results.
        
        Args:
            user_profile: User profile containing tags, location, etc.
            jobs: List of job dictionaries to score
            
        Returns:
            List of jobs with match_score and matching_tags, filtered and sorted by relevance
        """
        if not jobs:
            return []
        
        # Early exit if user has no preferences
        user_tags = user_profile.get("tags", [])
        user_location = user_profile.get("location")
        
        if not user_tags and not user_location:
            # Only return jobs with new bonus
            new_jobs = []
            for job in jobs:
                if job.get("new", False):
                    enhanced_job = job.copy()
                    enhanced_job["match_score"] = self.NEW_JOB_BONUS_POINTS
                    enhanced_job["matching_tags"] = []
                    new_jobs.append(enhanced_job)
            return self.filterAndSort(new_jobs)
        
        # Pre-process user preferences for efficiency
        user_tags_lower = set(tag.lower() for tag in user_tags) if user_tags else set()
        user_location_lower = user_location.lower() if user_location else None
        
        # Score each job
        scored_jobs = []
        for job in jobs:
            score, matching_tags = self._calculateScoreOptimized(job, user_tags_lower, user_location_lower)
            
            if score > 0:  # Only include jobs with positive scores
                # Create enhanced job object with scoring information
                enhanced_job = job.copy()
                enhanced_job["match_score"] = score
                enhanced_job["matching_tags"] = matching_tags
                scored_jobs.append(enhanced_job)
        
        # Sort by score (highest first) and return
        return self.filterAndSort(scored_jobs)
    
    def _calculateScoreOptimized(self, job: Dict[str, Any], user_tags_lower: set, user_location_lower: Optional[str]) -> tuple[int, List[str]]:
        """
        Optimized score calculation with pre-processed user preferences.
        
        Args:
            job: Job dictionary containing title, location, tags, etc.
            user_tags_lower: Pre-processed set of lowercase user tags
            user_location_lower: Pre-processed lowercase user location
            
        Returns:
            Tuple of (score, matching_tags)
        """
        score = 0
        matching_tags = []
        
        # Score based on tag matches
        job_tags = job.get("tags", [])
        if job_tags and user_tags_lower:
            job_tags_lower = set(tag.lower() for tag in job_tags)
            matched_tags = user_tags_lower.intersection(job_tags_lower)
            
            if matched_tags:
                score += len(matched_tags) * self.TAG_MATCH_POINTS
                matching_tags = list(matched_tags)
        
        # Score based on location match
        if user_location_lower and job.get("location"):
            job_location = job["location"].lower()
            if user_location_lower in job_location or job_location in user_location_lower:
                score += self.LOCATION_MATCH_POINTS
        
        # Bonus for new jobs
        if job.get("new", False):
            score += self.NEW_JOB_BONUS_POINTS
        
        return score, matching_tags
    
    def calculateScore(self, job: Dict[str, Any], user_profile: Dict[str, Any]) -> tuple[int, List[str]]:
        """
        Calculate relevance score for a single job based on user profile.
        
        Args:
            job: Job dictionary containing title, location, tags, etc.
            user_profile: User profile with preferences
            
        Returns:
            Tuple of (score, matching_tags)
        """
        score = 0
        matching_tags = []
        
        # Get user preferences
        user_tags = set(tag.lower() for tag in user_profile.get("tags", []))
        user_location = user_profile.get("location", "").lower() if user_profile.get("location") else None
        
        # Score based on tag matches
        job_tags = job.get("tags", [])
        if job_tags and user_tags:
            job_tags_lower = set(tag.lower() for tag in job_tags)
            matched_tags = user_tags.intersection(job_tags_lower)
            
            if matched_tags:
                score += len(matched_tags) * self.TAG_MATCH_POINTS
                matching_tags = list(matched_tags)
        
        # Score based on location match
        if user_location and job.get("location"):
            job_location = job["location"].lower()
            if user_location in job_location or job_location in user_location:
                score += self.LOCATION_MATCH_POINTS
        
        # Bonus for new jobs
        if job.get("new", False):
            score += self.NEW_JOB_BONUS_POINTS
        
        return score, matching_tags
    
    def filterAndSort(self, scored_jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out zero-score jobs and sort by relevance score.
        
        Args:
            scored_jobs: List of jobs with match_score field
            
        Returns:
            Filtered and sorted list of jobs
        """
        # Filter out jobs with zero or negative scores
        filtered_jobs = [job for job in scored_jobs if job.get("match_score", 0) > 0]
        
        # Sort by match_score (descending), then by new status, then by title
        filtered_jobs.sort(key=lambda job: (
            -job.get("match_score", 0),  # Higher scores first
            -int(job.get("new", False)),  # New jobs first within same score
            job.get("title", "").lower()  # Alphabetical by title as tiebreaker
        ))
        
        return filtered_jobs
    
    def getScoreBreakdown(self, job: Dict[str, Any], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed breakdown of how a job's score was calculated.
        
        Args:
            job: Job dictionary
            user_profile: User profile
            
        Returns:
            Dictionary with score breakdown details
        """
        breakdown = {
            "total_score": 0,
            "tag_matches": [],
            "tag_score": 0,
            "location_match": False,
            "location_score": 0,
            "new_job_bonus": False,
            "new_job_score": 0
        }
        
        user_tags = set(tag.lower() for tag in user_profile.get("tags", []))
        user_location = user_profile.get("location", "").lower() if user_profile.get("location") else None
        
        # Tag scoring breakdown
        job_tags = job.get("tags", [])
        if job_tags and user_tags:
            job_tags_lower = set(tag.lower() for tag in job_tags)
            matched_tags = user_tags.intersection(job_tags_lower)
            
            if matched_tags:
                breakdown["tag_matches"] = list(matched_tags)
                breakdown["tag_score"] = len(matched_tags) * self.TAG_MATCH_POINTS
        
        # Location scoring breakdown
        if user_location and job.get("location"):
            job_location = job["location"].lower()
            if user_location in job_location or job_location in user_location:
                breakdown["location_match"] = True
                breakdown["location_score"] = self.LOCATION_MATCH_POINTS
        
        # New job bonus breakdown
        if job.get("new", False):
            breakdown["new_job_bonus"] = True
            breakdown["new_job_score"] = self.NEW_JOB_BONUS_POINTS
        
        # Calculate total
        breakdown["total_score"] = (
            breakdown["tag_score"] + 
            breakdown["location_score"] + 
            breakdown["new_job_score"]
        )
        
        return breakdown
    
    def updateScoringWeights(self, tag_points: Optional[int] = None, 
                           location_points: Optional[int] = None, 
                           new_job_points: Optional[int] = None) -> None:
        """
        Update scoring weights for different factors.
        
        Args:
            tag_points: Points awarded per matching tag
            location_points: Points awarded for location match
            new_job_points: Bonus points for new jobs
        """
        if tag_points is not None:
            self.TAG_MATCH_POINTS = max(0, tag_points)
        if location_points is not None:
            self.LOCATION_MATCH_POINTS = max(0, location_points)
        if new_job_points is not None:
            self.NEW_JOB_BONUS_POINTS = max(0, new_job_points)
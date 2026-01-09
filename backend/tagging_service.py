"""
TaggingService - Automatically categorizes jobs using predefined keyword dictionaries.

This module provides functionality to analyze job titles and descriptions, 
clean text content, and assign relevant category tags based on keyword matching.
"""

import re
from typing import Dict, List, Set


class TaggingService:
    """Service for automatically tagging jobs with relevant categories."""
    
    def __init__(self):
        """Initialize TaggingService with predefined category dictionaries."""
        self._category_keywords = {
            "aerospace": [
                "satellite", "space", "espace", "rocket", "fusée", "aviation", "aircraft", "avion", "aeronautical",
                "aéronautique", "aerospace", "flight", "vol", "propulsion", "orbital", "launcher", "lanceur", 
                "spacecraft", "avionics", "avionique", "aerodynamics", "aérodynamique", "turbine", "engine", 
                "moteur", "cabin", "cabine", "cockpit", "payload", "charge utile", "constellation", "uav", "drone"
            ],
            "software": [
                "python", "javascript", "react", "api", "web", "frontend", "backend", "database", "sql", 
                "programming", "programmation", "developer", "développeur", "software", "logiciel", "code", 
                "application", "system", "système", "algorithm", "algorithme", "data", "données", "analytics", 
                "machine learning", "ai", "ia", "artificial intelligence", "intelligence artificielle", 
                "cloud", "devops", "git", "agile", "embedded", "embarqué", "cyber", "cybersecurity", "cybersécurité"
            ],
            "engineering": [
                "mechanical", "mécanique", "electrical", "électrique", "systems", "systèmes", "design", "conception",
                "manufacturing", "fabrication", "production", "quality", "qualité", "process", "processus", 
                "industrial", "industriel", "automation", "automatisme", "robotics", "robotique", "control", 
                "commande", "simulation", "modeling", "modélisation", "cad", "cao", "solidworks", "catia", 
                "matlab", "testing", "essais", "test", "validation", "integration", "intégration", "hardware", "matériel"
            ],
            "research": [
                "research", "recherche", "development", "développement", "innovation", "r&d", "technology", 
                "technologie", "science", "analysis", "analyse", "study", "étude", "investigation", 
                "experiment", "expérimentation", "prototype", "feasibility", "faisabilité", "optimization", 
                "optimisation", "improvement", "amélioration", "advanced", "avancé", "cutting-edge", "état de l'art"
            ],
            "management": [
                "project", "projet", "manager", "management", "gestion", "lead", "leader", "coordinator", 
                "coordinateur", "planning", "planification", "strategy", "stratégie", "business", "affaires", 
                "operations", "opérations", "team", "équipe", "leadership", "supervision", "organization", 
                "organisation", "administration", "budget", "resource", "ressource", "stakeholder", "partie prenante", 
                "pmo", "supply chain", "achats", "procurement"
            ]
        }   

        
        # Common stop words to remove during text cleaning
        self._stop_words = {
            "le", "la", "les", "un", "une", "des", "du", "de", "et", "ou", "mais",
            "pour", "avec", "dans", "sur", "par", "sans", "sous", "entre", "vers",
            "the", "a", "an", "and", "or", "but", "for", "with", "in", "on", "by",
            "without", "under", "between", "to", "from", "at", "of", "is", "are",
            "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may", "might", "can", "must"
        }
    
    def tagJob(self, job_title: str, job_description: str = "") -> List[str]:
        """
        Analyze job title and description to assign relevant category tags.
        
        Args:
            job_title: The job title to analyze
            job_description: Optional job description for additional context
            
        Returns:
            List of category tags that match the job content
        """
        if not job_title:
            return []
        
        # Clean and prepare text for analysis
        cleaned_title = self.cleanTitle(job_title)
        cleaned_description = self.cleanTitle(job_description) if job_description else ""
        
        # Combine title and description for comprehensive matching
        combined_text = f"{cleaned_title} {cleaned_description}".strip()
        
        # Find matching categories
        matching_tags = self.matchKeywords(combined_text, self._category_keywords)
        
        return sorted(list(matching_tags))
    
    def cleanTitle(self, text: str) -> str:
        """
        Clean and normalize text for keyword matching.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned and normalized text string
        """
        if not text:
            return ""
        
        # Convert to lowercase
        cleaned = text.lower()
        
        # Remove special characters and extra whitespace
        cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove stop words
        words = cleaned.split()
        filtered_words = [word for word in words if word not in self._stop_words and len(word) > 2]
        
        return ' '.join(filtered_words)
    
    def matchKeywords(self, text: str, categories: Dict[str, List[str]]) -> Set[str]:
        """
        Find matching categories based on keyword presence in text.
        
        Args:
            text: Cleaned text to analyze
            categories: Dictionary mapping category names to keyword lists
            
        Returns:
            Set of category names that have matching keywords
        """
        if not text:
            return set()
        
        matching_categories = set()
        text_words = set(text.split())
        
        for category, keywords in categories.items():
            # Check if any keyword from this category appears in the text
            category_keywords = set(keyword.lower() for keyword in keywords)
            
            # Look for exact word matches and partial matches
            for keyword in category_keywords:
                if keyword in text_words or keyword in text:
                    matching_categories.add(category)
                    break
        
        return matching_categories
    


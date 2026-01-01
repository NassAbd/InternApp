"""
CVParser - Extracts relevant tags from uploaded CV using LLM analysis.

This module provides functionality to parse PDF CV files and extract relevant
tags using the Groq API, mapping the results to predefined categories.
"""

import io
import json
import requests
from typing import Dict, List, Any, Optional, Tuple
from PyPDF2 import PdfReader


class CVParser:
    """Parser for extracting tags from CV files using LLM analysis."""
    
    def __init__(self):
        """Initialize CVParser with predefined categories."""
        # Define the same categories as TaggingService for consistency
        self.predefined_categories = {
            "aerospace": [
                "Space systems, Satellite engineering, Orbital mechanics, Rocket propulsion, Launchers",
                "Aeronautics, Aircraft design, Avionics, Flight dynamics, Aerodynamics",
                "Espace, Systèmes spatiaux, Propulsion, Lanceurs, Satellite, Avionique, Aéronautique"
            ],
            "software": [
                "Software engineering, Fullstack development, Cloud computing, DevOps, Embedded systems",
                "Programming languages (Python, C++, Java, JS), Web frameworks, API design, Architecture",
                "Développement logiciel, Systèmes embarqués, Programmation, Cloud, Architecture logicielle"
            ],
            "engineering": [
                "Mechanical engineering, Structural analysis, Thermal control, Materials science",
                "Electrical engineering, Power systems, Industrial automation, Manufacturing processes",
                "Génie mécanique, Analyse structurale, Thermique, Matériaux, Automatisme, Génie électrique"
            ],
            "electronics": [
                "RF engineering, Signal processing, Hardware design, FPGA, PCB, Radar systems",
                "Telecommunications, Microelectronics, Circuit design, Instrumentation",
                "Électronique, Traitement du signal, RF, Radar, Systèmes matériels, Télécoms"
            ],
            "data": [
                "Data science, Machine Learning, Artificial Intelligence, Big Data, Data Analysis",
                "Statistics, Computer Vision, Natural Language Processing, Database management",
                "Science des données, Apprentissage automatique, IA, Statistiques, Analyse de données"
            ],
            "management": [
                "Project management, PMO, Product ownership, Agile/Scrum, Team leadership, Strategy",
                "Business administration, Coordination, Supervision, Operations management",
                "Gestion de projet, Direction, Management d'équipe, Stratégie, Coordination"
            ],
            "operations_supply": [
                "Supply chain, Logistics, Procurement, Quality assurance (QA), Lean manufacturing",
                "Production planning, Maintenance (MRO), Assembly & Integration (AIT/AIV)",
                "Chaîne logistique, Achats, Qualité, Production, Maintenance, Intégration et Tests"
            ],
            "research": [
                "R&D, Academic research, Scientific computing, Innovation, Laboratory testing",
                "Fundamental research, Applied physics, Mathematics, PhD/Thèse",
                "Recherche et Développement, Innovation, Recherche scientifique, Laboratoire"
            ],
            "design": [
                "System design, CAD/CAO (Catia, SolidWorks), UI/UX design, Graphic design",
                "Product design, Creative direction, Technical drawing",
                "Conception de systèmes, CAO, Design industriel, Interface utilisateur"
            ],
            "security": [
                "Cybersecurity, Network security, Information assurance, Cryptography",
                "System safety, Risk analysis, Critical infrastructure protection",
                "Cybersécurité, Sécurité des réseaux, Sûreté de fonctionnement, Analyse de risques"
            ],
            "finance": [
                "Financial analysis, Controlling, Accounting, Auditing, Budgeting, Economics",
                "Finance d'entreprise, Contrôle de gestion, Audit, Comptabilité, Budget"
            ],
            "marketing": [
                "Corporate communication, Digital marketing, Sales, Business development, Content strategy",
                "Public relations, Market analysis, Event planning",
                "Communication, Ventes, Marketing digital, Commerce, Développement commercial"
            ]
        }
    
    def parseCV(self, pdf_content: bytes, api_key: str) -> Tuple[List[str], str]:
        """
        Parse CV content and extract relevant tags using Groq API.
        
        Args:
            pdf_content: PDF file content as bytes
            api_key: Groq API key for LLM analysis
            
        Returns:
            Tuple of (extracted_tags, raw_cv_text)
            
        Raises:
            ValueError: If PDF cannot be parsed or API key is invalid
            ConnectionError: If Groq API request fails
        """
        try:
            # Extract text from PDF
            cv_text = self._extract_text_from_pdf(pdf_content)
            
            if not cv_text.strip():
                raise ValueError("No text could be extracted from the PDF file")
            
            # Extract tags using Groq API
            extracted_tags = self._extract_tags_with_groq(cv_text, api_key)
            
            return extracted_tags, cv_text
            
        except Exception as e:
            if isinstance(e, (ValueError, ConnectionError)):
                raise
            else:
                raise ValueError(f"Error parsing CV: {str(e)}")
    
    def _extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        Extract text content from PDF bytes.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If PDF cannot be read
        """
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PdfReader(pdf_file)
            
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            return text_content.strip()
            
        except Exception as e:
            raise ValueError(f"Cannot read PDF file: {str(e)}")
    
    def _extract_tags_with_groq(self, cv_text: str, api_key: str) -> List[str]:
        """
        Use Groq API to analyze CV text and extract relevant tags.
        
        Args:
            cv_text: Extracted CV text content
            api_key: Groq API key
            
        Returns:
            List of extracted category tags
            
        Raises:
            ConnectionError: If API request fails
            ValueError: If API response is invalid
        """
        # Prepare the prompt for Groq API
        categories_list = ", ".join(self.predefined_categories.keys())
        
        prompt = f"""
        Analyze the following CV/resume text and identify the person's skills, experience, and interests.
        Based on the content, select the most relevant categories from this predefined list: {categories_list}
        
        Return ONLY a JSON array of category names that match the person's background. 
        For example: ["software", "engineering", "data"]
        
        Do not include categories that are not clearly supported by the CV content.
        Do not add any explanation or additional text.
        
        CV Text:
        {cv_text[:4000]}  # Limit text to avoid token limits
        """
        
        try:
            # Make request to Groq API
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "model": "llama-3.3-70b-versatile",  # Use a reliable model
                "temperature": 0.1,  # Low temperature for consistent results
                "max_tokens": 100  # Short response expected
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 401:
                raise ConnectionError("Invalid Groq API key")
            elif response.status_code != 200:
                raise ConnectionError(f"Groq API request failed: {response.status_code} - {response.text}")
            
            # Parse response
            response_data = response.json()
            
            if "choices" not in response_data or not response_data["choices"]:
                raise ValueError("Invalid response from Groq API")
            
            content = response_data["choices"][0]["message"]["content"].strip()
            
            # Parse JSON response
            try:
                extracted_categories = json.loads(content)
                
                if not isinstance(extracted_categories, list):
                    raise ValueError("API response is not a list")
                
                # Validate categories against predefined list
                valid_categories = []
                for category in extracted_categories:
                    if isinstance(category, str) and category.lower() in self.predefined_categories:
                        valid_categories.append(category.lower())
                
                return valid_categories
                
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract categories manually
                return self._fallback_category_extraction(content)
                
        except requests.RequestException as e:
            raise ConnectionError(f"Network error contacting Groq API: {str(e)}")
        except Exception as e:
            if isinstance(e, (ConnectionError, ValueError)):
                raise
            else:
                raise ConnectionError(f"Unexpected error with Groq API: {str(e)}")
    
    def _fallback_category_extraction(self, response_text: str) -> List[str]:
        """
        Fallback method to extract categories if JSON parsing fails.
        
        Args:
            response_text: Raw response text from API
            
        Returns:
            List of extracted categories
        """
        valid_categories = []
        response_lower = response_text.lower()
        
        for category in self.predefined_categories.keys():
            if category in response_lower:
                valid_categories.append(category)
        
        return valid_categories
    
    def mergeTags(self, existing_tags: List[str], new_tags: List[str]) -> List[str]:
        """
        Merge CV-extracted tags with existing user tags.
        
        Args:
            existing_tags: Current user profile tags
            new_tags: Tags extracted from CV
            
        Returns:
            Combined list of unique tags
        """
        # Combine and deduplicate tags
        all_tags = set()
        
        # Add existing tags
        for tag in existing_tags:
            if isinstance(tag, str) and tag.strip():
                all_tags.add(tag.strip().lower())
        
        # Add new tags
        for tag in new_tags:
            if isinstance(tag, str) and tag.strip():
                all_tags.add(tag.strip().lower())
        
        return sorted(list(all_tags))
    
    def getAvailableCategories(self) -> Dict[str, List[str]]:
        """
        Get the predefined categories and their keywords.
        
        Returns:
            Dictionary of categories and their associated keywords
        """
        return self.predefined_categories.copy()
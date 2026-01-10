import json
import requests
from typing import Optional, Dict, Any

class MaintenanceService:
    """Service for diagnosing scraper failures using LLM."""

    def diagnose_failure(self, module_name: str, error_log: str, source_code: str, api_key: str) -> Dict[str, Any]:
        """
        Analyze scraper failure and provide explanation and fix suggestions.

        Args:
            module_name: Name of the failed scraper module
            error_log: The exception message or traceback
            source_code: The source code of the scraper
            api_key: Groq API key

        Returns:
            Dictionary containing 'explanation' and 'suggested_fix'
        """
        prompt = f"""
            Role: Expert Python Developer specialized in Playwright web scraping.

            Context: The scraper module '{module_name}' crashed. 
            Note: The 'ValueError' triggers in the code are intentional; they are 'data guards' designed to fail fast when page structures change or selectors return null/empty values.

            Error Log:
            {error_log}

            Source Code (Context):
            {source_code[:10000]}

            Task:
            1. Identify the specific field or logic that triggered the intentional crash based on the Error Log.
            2. Analyze if the failure is due to a DOM change (selector no longer valid), a timeout, or a data format mismatch.
            3. Provide ONLY the specific modified function or code block that was failing. DO NOT rewrite the entire file.

            Constraints:
            - Maintain the 'Value Error' guard logic in your fix.
            - Focus on updating selectors, waiting logic, or data cleaning.
            - Ensure the fix is surgical and ready to be integrated.

            Return ONLY a JSON object:
            {{
                "explanation": "Brief and technical explanation of why the guard was triggered.",
                "suggested_fix": "Python code block containing only the corrected function/method."
            }}
            """

        try:
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
                "model": "llama-3.3-70b-versatile",
                "temperature": 0.1,
                "max_tokens": 1000,
                "response_format": {"type": "json_object"}
            }

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                return {
                    "explanation": f"Failed to get diagnosis from AI (Status: {response.status_code})",
                    "suggested_fix": None
                }

            response_data = response.json()
            content = response_data["choices"][0]["message"]["content"]
            
            return json.loads(content)

        except Exception as e:
            return {
                "explanation": f"Internal error during diagnosis: {str(e)}",
                "suggested_fix": None
            }

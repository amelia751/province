"""Gemini AI service for tax content relevance detection."""

import logging
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for using Gemini AI to determine tax content relevance."""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-flash-latest')
        
        # System prompt for tax relevance detection
        self.tax_relevance_prompt = """
You are an expert tax analyst. Your job is to determine if content from IRS sources is relevant to tax calculations and rules.

RELEVANT content includes:
- Tax rates, brackets, and thresholds
- Standard deductions and itemized deduction limits
- Tax credits (Child Tax Credit, EITC, etc.)
- Filing status requirements
- Income limits for various tax benefits
- Tax year changes and inflation adjustments
- Form changes that affect calculations
- Revenue procedures with numerical tax data
- Business tax rules and depreciation schedules
- Estate and gift tax exemptions

NOT RELEVANT content includes:
- General tax tips and advice
- Procedural announcements (office closures, etc.)
- Enforcement actions and penalties
- Audit procedures and compliance
- General educational content
- Press releases about IRS operations
- Personnel announcements
- Technology updates
- Customer service information

Respond with ONLY a valid JSON object (no markdown formatting):
{
    "relevant": true,
    "confidence": 0.95,
    "reason": "Brief explanation of why this is or is not relevant",
    "key_topics": ["list", "of", "key", "tax", "topics", "found"]
}

Content to analyze:
"""
    
    def is_tax_relevant(self, title: str, content: str, url: str = "") -> Dict[str, Any]:
        """
        Determine if content is relevant to tax calculations using Gemini AI.
        
        Args:
            title: Title of the content
            content: Main content text
            url: URL of the content (optional)
            
        Returns:
            Dict with relevance analysis
        """
        try:
            # Prepare the content for analysis
            analysis_text = f"""
Title: {title}
URL: {url}
Content: {content[:2000]}...  # Limit content to avoid token limits
"""
            
            # Generate response from Gemini
            response = self.model.generate_content(
                self.tax_relevance_prompt + analysis_text,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent results
                    max_output_tokens=500
                )
            )
            
            # Parse the JSON response
            import json
            import re
            try:
                # Clean the response text - remove markdown code blocks
                response_text = response.text.strip()
                
                # Remove ```json and ``` markers if present
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                response_text = response_text.strip()
                
                result = json.loads(response_text)
                
                # Validate the response structure
                if not all(key in result for key in ['relevant', 'confidence', 'reason']):
                    logger.warning(f"Invalid Gemini response structure: {result}")
                    return self._fallback_analysis(title, content)
                
                # Ensure confidence is a float between 0 and 1
                result['confidence'] = max(0.0, min(1.0, float(result.get('confidence', 0.5))))
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON response: {e}")
                logger.error(f"Raw response: {response.text}")
                return self._fallback_analysis(title, content)
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._fallback_analysis(title, content)
    
    def _fallback_analysis(self, title: str, content: str) -> Dict[str, Any]:
        """
        Fallback keyword-based analysis when Gemini fails.
        
        Args:
            title: Title of the content
            content: Main content text
            
        Returns:
            Dict with basic relevance analysis
        """
        # Fallback keywords for tax relevance
        tax_keywords = [
            'tax rate', 'tax bracket', 'standard deduction', 'itemized deduction',
            'child tax credit', 'earned income tax credit', 'eitc', 'ctc',
            'inflation adjustment', 'revenue procedure', 'rev proc',
            'filing status', 'income limit', 'tax year', 'form 1040',
            'schedule', 'withholding', 'estimated tax', 'business tax',
            'depreciation', 'estate tax', 'gift tax', 'alternative minimum tax',
            'amt', 'tax threshold', 'exemption', 'credit', 'deduction'
        ]
        
        text_lower = (title + " " + content).lower()
        matched_keywords = [kw for kw in tax_keywords if kw in text_lower]
        
        # Simple relevance scoring
        relevance_score = len(matched_keywords) / len(tax_keywords)
        is_relevant = relevance_score > 0.1 or len(matched_keywords) >= 2
        
        return {
            'relevant': is_relevant,
            'confidence': min(0.8, relevance_score * 2),  # Cap at 0.8 for fallback
            'reason': f"Fallback analysis: Found {len(matched_keywords)} tax-related keywords",
            'key_topics': matched_keywords[:5],  # Limit to top 5
            'fallback': True
        }
    
    def extract_tax_data(self, content: str) -> Dict[str, Any]:
        """
        Extract structured tax data from content using Gemini AI.
        
        Args:
            content: Content to extract data from
            
        Returns:
            Dict with extracted tax data
        """
        extraction_prompt = """
Extract structured tax data from the following content. Look for:
- Tax rates and percentages
- Dollar amounts and thresholds
- Income limits
- Deduction amounts
- Credit amounts
- Tax year information
- Filing status information

Return a JSON object with the extracted data:
{
    "tax_year": 2024,
    "standard_deductions": {"single": 14600, "married_filing_jointly": 29200},
    "tax_brackets": [{"rate": 10, "min": 0, "max": 11000, "filing_status": "single"}],
    "credits": {"child_tax_credit": 2000},
    "other_amounts": {"key": "value"},
    "confidence": 0.0-1.0
}

Content:
"""
        
        try:
            response = self.model.generate_content(
                extraction_prompt + content[:3000],  # Limit content
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1000
                )
            )
            
            import json
            result = json.loads(response.text.strip())
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract tax data with Gemini: {e}")
            return {"confidence": 0.0, "error": str(e)}


# Global instance
_gemini_service = None

def get_gemini_service() -> GeminiService:
    """Get or create the global Gemini service instance."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service

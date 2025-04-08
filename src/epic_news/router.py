"""
Request routing module for Epic News application.
This module contains classes for routing user requests to the appropriate crew.
"""

import re
from typing import Dict, Optional, Tuple, List, Any

class KeywordMatcher:
    """Class for matching keywords in user requests."""
    
    def __init__(self, keywords: List[str], crew_type: str):
        """
        Initialize a KeywordMatcher.
        
        Args:
            keywords: List of keywords to match
            crew_type: The crew type to return if any keyword matches
        """
        self.keywords = keywords
        self.crew_type = crew_type
    
    def matches(self, text: str) -> bool:
        """
        Check if any keyword matches the given text.
        
        Args:
            text: The text to check for keyword matches
            
        Returns:
            True if any keyword matches, False otherwise
        """
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)


class RequestRouter:
    """Class for routing user requests to the appropriate crew."""
    
    def __init__(self):
        """Initialize the RequestRouter with keyword matchers."""
        self.matchers = [
            KeywordMatcher(
                ["poeme", "poem", "poetry", "verse", "stanza"], 
                "POEM"
            ),
            KeywordMatcher(
                ["recette", "recipe", "cooking", "cuisine", "food"], 
                "COOKING"
            ),
            KeywordMatcher(
                ["news", "actualité", "information", "article", "report"], 
                "NEWS"
            ),
            KeywordMatcher(
                ["book", "livre", "library", "bibliothèque", "roman", "novel", "author", "auteur"], 
                "LIBRARY"
            ),
            KeywordMatcher(
                ["meeting", "prep", "réunion", "préparation", "agenda", "minutes"], 
                "MEETING_PREP"
            ),
            KeywordMatcher(
                ["lead", "score", "scoring", "prospect", "qualification"], 
                "LEAD_SCORING"
            ),
            KeywordMatcher(
                ["contact", "find contact", "sales contact", "buyer", "decision maker"], 
                "CONTACT_FINDER"
            ),
            KeywordMatcher(
                ["holiday", "vacation", "trip", "travel", "weekend", "vacances", "voyage", "séjour"], 
                "HOLIDAY_PLANNER"
            )
        ]
    
    def extract_book_title(self, request: str) -> Optional[str]:
        """
        Extract a book title from a request.
        
        Args:
            request: The user request
            
        Returns:
            The book title if found, None otherwise
        """
        book_match = re.search(r"['\"](.+?)['\"]", request)
        if book_match:
            return book_match.group(1)
        return None
    
    def extract_company(self, request: str) -> Optional[str]:
        """
        Extract a company name from a request.
        
        Args:
            request: The user request
            
        Returns:
            The company name if found, None otherwise
        """
        company_match = re.search(r"with\s+([A-Z][a-zA-Z\s]+)", request)
        if company_match:
            return company_match.group(1).strip()
        
        # Try alternative pattern
        company_match = re.search(r"for\s+([A-Z][a-zA-Z\s]+)", request)
        if company_match:
            return company_match.group(1).strip()
        
        return None
    
    def extract_product(self, request: str) -> Optional[str]:
        """
        Extract a product name from a request.
        
        Args:
            request: The user request
            
        Returns:
            The product name if found, None otherwise
        """
        product_match = re.search(r"selling\s+([A-Za-z0-9\s]+)", request)
        if product_match:
            return product_match.group(1).strip()
        return None
    
    def extract_destination(self, request: str) -> Optional[str]:
        """
        Extract a destination from a request.
        
        Args:
            request: The user request
            
        Returns:
            The destination if found, None otherwise
        """
        destination_match = re.search(r"(?:to|in|at|for)\s+([A-Za-z\s]+?)(?:\s+for|\s+with|\s+during|\.|$)", request)
        if destination_match:
            return destination_match.group(1).strip()
        return None
    
    def extract_duration(self, request: str) -> Optional[str]:
        """
        Extract a duration from a request.
        
        Args:
            request: The user request
            
        Returns:
            The duration if found, None otherwise
        """
        duration_match = re.search(r"for\s+a\s+([a-zA-Z0-9\s]+)(?:\s+trip|\s+vacation|\s+holiday)?", request, re.IGNORECASE)
        if duration_match:
            return duration_match.group(1).strip()
        return None
    
    def route(self, request: str, topic: str = "") -> Dict[str, Any]:
        """
        Route a user request to the appropriate crew.
        
        Args:
            request: The user request
            topic: The current topic, if any
            
        Returns:
            A dictionary containing the crew type and any extracted parameters
        """
        result = {
            "crew_type": "",
            "topic": topic or request,
            "parameters": {}
        }
        
        # First check if we can extract a book title
        if any(matcher.matches(request) for matcher in self.matchers if matcher.crew_type == "LIBRARY"):
            book_title = self.extract_book_title(request)
            if book_title:
                result["crew_type"] = "LIBRARY"
                result["topic"] = book_title
                return result
        
        # Check for meeting prep
        if any(matcher.matches(request) for matcher in self.matchers if matcher.crew_type == "MEETING_PREP"):
            company = self.extract_company(request)
            result["crew_type"] = "MEETING_PREP"
            if company:
                result["parameters"]["company"] = company
                if not result["topic"]:
                    result["topic"] = f"Meeting with {company}"
            return result
        
        # Check for contact finder
        if any(matcher.matches(request) for matcher in self.matchers if matcher.crew_type == "CONTACT_FINDER"):
            company = self.extract_company(request)
            product = self.extract_product(request)
            result["crew_type"] = "CONTACT_FINDER"
            if company:
                result["parameters"]["company"] = company
            if product:
                result["parameters"]["our_product"] = product
            if company and not result["topic"]:
                result["topic"] = f"Contact Finder for {company}"
            return result
        
        # Check for holiday planner
        if any(matcher.matches(request) for matcher in self.matchers if matcher.crew_type == "HOLIDAY_PLANNER"):
            destination = self.extract_destination(request) or topic
            duration = self.extract_duration(request)
            result["crew_type"] = "HOLIDAY_PLANNER"
            if destination:
                result["parameters"]["destination"] = destination
                if not result["topic"]:
                    result["topic"] = destination
            if duration:
                result["parameters"]["duration"] = duration
            return result
        
        # Check for lead scoring
        if any(matcher.matches(request) for matcher in self.matchers if matcher.crew_type == "LEAD_SCORING"):
            result["crew_type"] = "LEAD_SCORING"
            if not result["topic"]:
                result["topic"] = "Lead Scoring"
            return result
        
        # Check for other crew types
        for matcher in self.matchers:
            if matcher.matches(request):
                result["crew_type"] = matcher.crew_type
                return result
        
        # If no match found, return UNKNOWN
        result["crew_type"] = "UNKNOWN"
        return result

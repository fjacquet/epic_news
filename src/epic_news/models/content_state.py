"""
Content state model for Epic News application.
This module defines the ContentState class which stores all state information
for the application during execution.
"""

import datetime
from pydantic import BaseModel, Field

class ContentState(BaseModel):
    # Basic request information
    user_request: str = "Create a Poem on Paris in the night"
    topic: str = ""  # Will be extracted from user_request if not provided
    selected_crew: str = ""  # Default crew type
 
    # Holiday planner parameters
    duration: str = ""  # Duration of the holiday
    current_year: str = str(datetime.datetime.now().year)  # Current year
    destination: str = "Paris, FR"  # Destination of the holiday
    family: str = ""  # Family details
    origin: str = ""  # Origin of the holiday
    special_needs: str = ""  # Special needs of the holiday
    categories:  dict = Field(default_factory=lambda: {
        "CONTACT_FINDER": "CONTACT_FINDER",
        "COOKING": "COOKING",
        "HOLIDAY_PLANNER": "HOLIDAY_PLANNER",
        "LEAD_SCORING": "LEAD_SCORING",
        "LIBRARY": "LIBRARY",
        "MEETING_PREP": "MEETING_PREP",
        "NEWS": "NEWS",
        "OPEN_SOURCE_INTELLIGENCE": "OPEN_SOURCE_INTELLIGENCE",
        "POEM": "POEM",
        "UNKNOWN": "UNKNOWN",
    })
    # Output file path
    output_file: str = ""

    # Email settings
    sendto: str = "fred.jacquet@gmail.com"
    email_sent: bool = False
    error_message: str = ""
    
    # Additional parameters
    sentence_count: int = 5

    # Company and product parameters (used by both ContactFinder and MeetingPrep)
    company: str = ""
    our_product: str = ""

    # Meeting prep specific parameters
    participants: list = [
        "John Doe <john.doe@pictet.com> - CEO",
        "Jane Smith <jane.smith@pictet.com> - CTO",
        "Bob Johnson <bob.johnson@pictet.com> - Sales Director"
    ]
    context: str = ""
    objective: str = ""
    prior_interactions: str = ""
    
    # Content storage for different crew types
    content: dict = Field(default_factory=lambda: {
        "news": "",
        "poem": "",
        "recipe": "",
        "post_report": "",
        "book_summary": "",
        "meeting_prep": "",
        "lead_score": "",
        "contact_info": "",
        "osfindings": "",
        "holiday_plan": ""
    })
    
    # Dynamic property access for content types
    def __getattr__(self, name):
        """Dynamic getter for content properties"""
        if name in self.content:
            return self.content.get(name, "")
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name, value):
        """Dynamic setter for content properties"""
        if name in getattr(self, "content", {}):
            self.content[name] = value
        else:
            super().__setattr__(name, value)

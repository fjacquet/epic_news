from pydantic import BaseModel, Field
from datetime import datetime
import os
import re
import json
import yaml

from crewai.flow import Flow, listen, start, router, or_

from epic_news.crews.contact_finder.contact_finder import ContactFinderCrew
from epic_news.crews.cooking.cooking_crew import CookingCrew
from epic_news.crews.library.library import LibraryCrew
from epic_news.crews.meeting_prep.meeting_prep import MeetingPrepCrew
from epic_news.crews.news.news_crew import NewsCrew
from epic_news.crews.poem_crew.poem_crew import PoemCrew
from epic_news.crews.post_crew.post_crew import PostCrew
from epic_news.crews.reception_crew.reception_crew import ReceptionCrew


class ContentState(BaseModel):
    # Basic request information
  # "Prepare for a meeting with Swiss Fribourg State internal IT department -  Sitel"
  # "Create a poem about the powerflex product"
  # "Search the contact finder with ifage as target company and powerstore as product"
    user_request: str = "Search the contact finder with Fribourg state IT  as target company and powerflex as product"
    topic: str = ""  # Will be extracted from user_request if not provided
    selected_crew: str = ""  # Default crew type
    # Content storage for different crew types
    content: dict = Field(default_factory=lambda: {
        "news": "",
        "poem": "",
        "recipe": "",
        "post_report": "",
        "book_summary": "",
        "meeting_prep": "",
        "lead_score": "",
        "contact_info": ""
    })
    
    # Email settings
    sendto: str = "fred.jacquet@gmail.com"
    
    # Additional parameters
    sentence_count: int = 5
    current_year: str = str(datetime.now().year)

    # Company and product parameters (used by both ContactFinder and MeetingPrep)
    company: str = "Fribourg state IT"
    our_product: str = "PowerFlex"

    # Meeting prep specific parameters
    participants: list = [
            "John Doe <john.doe@fr.ch> - CEO",
            "Jane Smith <jane.smith@fr.ch> - CTO",
            "Bob Johnson <bob.johnson@fr.ch> - Sales Director"
        ]
    context: str = "Second technical meeting to discuss potential private cloud implementation using powerflex and openshift"
    objective: str = "Present our product offerings and identify potential collaboration opportunities"
    prior_interactions: str = "We had a brief call with their CTO last month who expressed interest in our private cloud solutions"
    
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


class ReceptionFlow(Flow[ContentState]):

    @start()
    def route_request(self):
        print(f"Routing request: '{self.state.user_request}' with topic: '{self.state.topic}'")
        
        # Ensure output directories exist
        os.makedirs("output", exist_ok=True)
        os.makedirs("output/meeting", exist_ok=True)
        os.makedirs("output/lead_scoring", exist_ok=True)
        os.makedirs("output/contact_finder", exist_ok=True)
        
        # Extract topic from request if not provided
        if not self.state.topic and self.state.user_request:
            # Try to extract a meaningful topic from the request
            request_lower = self.state.user_request.lower()
            
            # Look for book titles in quotes
            book_match = re.search(r"['\"](.+?)['\"]", self.state.user_request)
            if book_match and any(word in request_lower for word in ["book", "livre", "library", "bibliothèque"]):
                self.state.topic = book_match.group(1)
                self.state.selected_crew = "LIBRARY"
                print(f"Extracted book title from request: '{self.state.topic}'")
            # Detect meeting prep requests
            elif any(word in request_lower for word in ["meeting", "prep", "réunion", "préparation", "agenda", "minutes"]):
                # Extract company name if possible
                company_match = re.search(r"with\s+([A-Z][a-zA-Z\s]+)", self.state.user_request)
                if company_match and not self.state.company:
                    self.state.company = company_match.group(1).strip()
                    print(f"Extracted company from request: '{self.state.company}'")
                
                # If no company was extracted but topic is set, use topic as company
                if not self.state.company and self.state.topic:
                    self.state.company = self.state.topic
                
                # Set topic if not already set
                if not self.state.topic:
                    self.state.topic = self.state.user_request
                
                # Directly set the crew type for meeting prep
                self.state.selected_crew = "MEETING_PREP"
                print(f"Detected meeting prep request for company: '{self.state.company}'")
            # Detect lead scoring requests
            elif any(word in request_lower for word in ["lead", "score", "scoring", "prospect", "qualification"]):
                # Set topic if not already set
                if not self.state.topic:
                    self.state.topic = "Lead Scoring"
                
                # Directly set the crew type for lead scoring
                self.state.selected_crew = "LEAD_SCORING"
                print(f"Detected lead scoring request")
            # Detect contact finder requests
            elif any(word in request_lower for word in ["contact", "find contact", "sales contact", "buyer", "decision maker"]):
                # Extract company name if possible
                company_match = re.search(r"for\s+([A-Z][a-zA-Z\s]+)", self.state.user_request)
                if company_match:
                    self.state.company = company_match.group(1).strip()
                    print(f"Extracted target company from request: '{self.state.company}'")
                
                # Extract product name if possible
                product_match = re.search(r"selling\s+([A-Za-z0-9\s]+)", self.state.user_request)
                if product_match:
                    self.state.our_product = product_match.group(1).strip()
                    print(f"Extracted product from request: '{self.state.our_product}'")
                
                # Set topic if not already set
                if not self.state.topic:
                    self.state.topic = f"Contact Finder for {self.state.company}"
                
                # Directly set the crew type for contact finder
                self.state.selected_crew = "CONTACT_FINDER"
                print(f"Detected contact finder request for company: '{self.state.company}'")
            else:
                # Use the request as the topic
                self.state.topic = self.state.user_request
                print(f"Using request as topic: '{self.state.topic}'")
        
        # If no crew is selected yet, try to determine based on the request
        if not self.state.selected_crew:
            try:
                # Use the reception crew to determine which crew should handle the request
                reception_crew = ReceptionCrew()
                routing_decision = reception_crew.kickoff(inputs={"request": self.state.user_request})
                print(f"Routing decision: {routing_decision}")
                
                # Extract crew type and update topic if provided
                self.state.selected_crew = routing_decision.get("crew_type", "UNKNOWN")
                if routing_decision.get("topic"):
                    self.state.topic = routing_decision.get("topic")
            except Exception as e:
                print(f"Error in AI routing: {str(e)}")
                # Fallback to keyword-based routing
                self.determine_crew()
        
        print(f"Selected crew: {self.state.selected_crew}")
        print(f"Updated topic: {self.state.topic}")
        
        return self.state.selected_crew

    @router(route_request)
    def determine_crew(self):
        """Determine which crew to use based on the request"""
        router_decision = self.state.selected_crew
        print(f"Router determining which crew to use based on: {router_decision}")
        
        # If no crew type is selected, use keyword-based detection
        if not router_decision or router_decision == "UNKNOWN":
            # Determine crew type based on keywords in the request
            request_lower = self.state.user_request.lower()
            
            if any(word in request_lower for word in ["poeme", "poem", "poetry", "verse", "stanza"]):
                self.state.selected_crew = "POEM"
            elif any(word in request_lower for word in ["recette", "recipe", "cooking", "cuisine", "food"]):
                self.state.selected_crew = "COOKING"
            elif any(word in request_lower for word in ["news", "actualité", "information", "article", "report"]):
                self.state.selected_crew = "NEWS"
            elif any(word in request_lower for word in ["book", "livre", "library", "bibliothèque", "roman", "novel", "author", "auteur"]):
                self.state.selected_crew = "LIBRARY"
            elif any(word in request_lower for word in ["meeting", "prep", "réunion", "préparation", "agenda", "minutes"]):
                self.state.selected_crew = "MEETING_PREP"
            elif any(word in request_lower for word in ["lead", "score", "scoring", "prospect", "qualification"]):
                self.state.selected_crew = "LEAD_SCORING"
            elif any(word in request_lower for word in ["contact", "find contact", "sales contact", "buyer", "decision maker"]):
                self.state.selected_crew = "CONTACT_FINDER"
            else:
                self.state.selected_crew = "UNKNOWN"  # No matching crew for this request
                
            print(f"Determined crew type from request: {self.state.selected_crew}")
            router_decision = self.state.selected_crew
        
        # Map crew types to their respective generation methods
        if router_decision == "NEWS":
            return "GENERATE_NEWS"
        elif router_decision == "POEM":
            return "GENERATE_POEM"
        elif router_decision == "COOKING":
            return "GENERATE_RECIPE"
        elif router_decision == "LIBRARY":
            return "GENERATE_BOOK_SUMMARY"
        elif router_decision == "MEETING_PREP":
            return "GENERATE_MEETING_PREP"
        elif router_decision == "CONTACT_FINDER":
            return "GENERATE_CONTACT_INFO"
        else:
            return "UNKNOWN"

    @listen("GENERATE_POEM")
    def generate_poem(self):
        print(f"Generating poem about: {self.state.topic}")
        
        # Define the output file path directly
        output_file = "output/poem/poem.html"
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        try:
            # Create the poem crew
            poem_crew = PoemCrew()
            poem_crew.kickoff(inputs={
                "topic": self.state.user_request,
                "output_file": output_file,
                "sentence_count": self.state.sentence_count
            })
            
            # Read the generated poem from the file
            print("Reading poem from file")
            with open(output_file, "r") as f:
                poem_content = f.read()
        
            # Store the poem content in both ways to ensure compatibility
            self.state.poem = poem_content
            self.state.content["poem"] = poem_content
                
            # Directly call generate_post_report to ensure email is sent
            print("Generating post report for poem...")
            self.generate_post_report()
            
            return "CONTENT_GENERATED"
        except Exception as e:
            print(f"Error generating poem: {str(e)}")
            return "ERROR"
            
    @listen("GENERATE_NEWS")
    def generate_news(self):
        print(f"Generating news about: {self.state.topic}")
        
        # Define the output file path directly
        output_file = "output/news/news.html"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        try:
            # Create the news crew
            news_crew = NewsCrew()
            
            # Generate the news
            news_crew.kickoff(inputs={
                "topic": self.state.topic,
                "output_file": output_file,
                "sentence_count": self.state.sentence_count
            })
            
            # Read the generated news from the file
            print("Reading news from file")
            with open(output_file, "r") as f:
                news_content = f.read()
            
            # Store the news content in both ways to ensure compatibility
            self.state.news = news_content
            self.state.content["news"] = news_content
                
            # Directly call generate_post_report to ensure email is sent
            print("Generating post report for news...")
            self.generate_post_report()
            
            return "CONTENT_GENERATED"
        except Exception as e:
            print(f"Error generating news: {str(e)}")
            import traceback
            traceback.print_exc()
            error_message = f"Error generating news: {str(e)}"
            self.state.news = error_message
            self.state.content["news"] = error_message
            return "ERROR"

    @listen("GENERATE_RECIPE")
    def generate_recipe(self):
        print(f"Generating recipe for: {self.state.topic}")
        
        try:
            # Create the cooking crew
            cooking_crew = CookingCrew()
            
            # Generate the recipe
            recipe_content = cooking_crew.kickoff(inputs={
                "topic": self.state.topic,
                "sendto": self.state.sendto
            })
            
            # Store the recipe content in both ways to ensure compatibility
            self.state.recipe = recipe_content
            self.state.content["recipe"] = recipe_content
                
            # Directly call generate_post_report to ensure email is sent
            print("Generating post report for recipe...")
            self.generate_post_report()
            
            return "CONTENT_GENERATED"
        except Exception as e:
            print(f"Error generating recipe: {str(e)}")
            import traceback
            traceback.print_exc()
            error_message = f"Error generating recipe: {str(e)}"
            self.state.recipe = error_message
            self.state.content["recipe"] = error_message
            return "ERROR"

    @listen("GENERATE_BOOK_SUMMARY")
    def generate_book_summary(self):
        print(f"Generating book summary for: {self.state.topic}")
        
        # Define the output file path directly
        output_file = "output/library/book_summary.html"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        try:
            # Create the library crew
            library_crew = LibraryCrew()
            
            # Generate the book summary
            library_crew.kickoff(inputs={
                "book_title": self.state.topic,
                "output_file": output_file,
                "sentence_count": self.state.sentence_count
            })
            
            # Read the generated book summary from the file
            print("Reading book summary from file")
            with open(output_file, "r") as f:
                book_summary_content = f.read()
            
            # Store the book summary content in both ways to ensure compatibility
            self.state.book_summary = book_summary_content
            self.state.content["book_summary"] = book_summary_content
                
            # Directly call generate_post_report to ensure email is sent
            print("Generating post report for book summary...")
            self.generate_post_report()
            
            return "CONTENT_GENERATED"
        except Exception as e:
            print(f"Error generating book summary: {str(e)}")
            import traceback
            traceback.print_exc()
            error_message = f"Error generating book summary: {str(e)}"
            self.state.book_summary = error_message
            self.state.content["book_summary"] = error_message
            return "ERROR"

    @listen("GENERATE_MEETING_PREP")
    def generate_meeting_prep(self):
        print(f"Generating meeting prep for: {self.state.topic}")
        
        # Define the output file path directly
        output_file = "output/meeting/meeting_prep.html"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        try:
            # Create the meeting prep crew
            meeting_prep_crew = MeetingPrepCrew()
            
            # Generate the meeting prep
            meeting_prep_crew.kickoff(inputs={
                "company": self.state.company,
                "participants": self.state.participants,
                "context": self.state.context,
                "objective": self.state.objective,
                "prior_interactions": self.state.prior_interactions,
                "output_file": output_file
            })
            
            # Read the generated meeting prep from the file
            print("Reading meeting prep from file")
            with open(output_file, "r") as f:
                meeting_prep_content = f.read()
            
            # Store the meeting prep content in both ways to ensure compatibility
            self.state.meeting_prep = meeting_prep_content
            self.state.content["meeting_prep"] = meeting_prep_content
                
            # Directly call generate_post_report to ensure email is sent
            print("Generating post report for meeting prep...")
            self.generate_post_report()
            
            return "CONTENT_GENERATED"
        except Exception as e:
            print(f"Error generating meeting prep: {str(e)}")
            import traceback
            traceback.print_exc()
            error_message = f"Error generating meeting prep: {str(e)}"
            self.state.meeting_prep = error_message
            self.state.content["meeting_prep"] = error_message
            return "ERROR"

    @listen("GENERATE_CONTACT_INFO")
    def generate_contact_info(self):
        print(f"Finding contacts at: {self.state.company} for product: {self.state.our_product}")
        
        try:
            # Create the contact finder crew
            contact_finder = ContactFinderCrew()
            
            # Generate the contact information
            contact_content = contact_finder.kickoff(inputs={
                "company": self.state.company,
                "our_product": self.state.our_product,
                "sendto": self.state.sendto
            })
            
            # Store the contact information in both ways to ensure compatibility
            self.state.contact_info = contact_content
            self.state.content["contact_info"] = contact_content
                
            # Directly call generate_post_report to ensure email is sent
            print("Generating post report for contact information...")
            self.generate_post_report()
            
            return "CONTENT_GENERATED"
        except Exception as e:
            print(f"Error finding contacts: {str(e)}")
            import traceback
            traceback.print_exc()
            error_message = f"Error finding contacts: {str(e)}"
            self.state.contact_info = error_message
            self.state.content["contact_info"] = error_message
            return "ERROR"

    @listen("UNKNOWN")
    def handle_unknown(self):
        print("Unknown request type, cannot process")
        return "ERROR"

    @listen(or_("CONTENT_GENERATED", "ERROR"))
    def generate_post_report(self):
        # Only run if something was generated
        if not self.state.news and not self.state.recipe and not self.state.poem and not self.state.book_summary and not self.state.meeting_prep and not self.state.lead_score and not self.state.contact_info:
            print("No content was generated, skipping post report")
            return
            
        print("Generating post report")
        
        try:
            # Create the post crew with required parameters
            post_crew = PostCrew(
                topic=self.state.topic,
                recipient_email=self.state.sendto
            )
            
            # Generate the post report
            result = post_crew.kickoff(inputs={
                "news": self.state.news,
                "poem": self.state.poem,
                "recipe": self.state.recipe,
                "book_summary": self.state.book_summary,
                "meeting_prep": self.state.meeting_prep,
                "lead_score": self.state.lead_score,
                "contact_info": self.state.contact_info
            })
            
            print("Post report generated successfully")
            # Store the post report in both ways to ensure compatibility
            self.state.post_report = result.raw
            self.state.content["post_report"] = result.raw
            
            # Save the post report
            print("Saving post report")
        except Exception as e:
            print(f"Error generating post report: {str(e)}")
            import traceback
            traceback.print_exc()
            self.state.post_report = f"Error generating post report: {str(e)}"
            self.state.content["post_report"] = f"Error generating post report: {str(e)}"

    @listen(or_("CONTENT_GENERATED", "ERROR"))
    def send_email(self):
        """Send an email with the generated content"""
        print(f"Sending email to {self.state.sendto}")
        print(f"Selected crew: {self.state.selected_crew}")
        print(f"Content keys: {list(self.state.content.keys())}")
        print(f"Content values: {[k for k, v in self.state.content.items() if v]}")
        print(f"Direct poem access: {bool(self.state.poem)}")
        
        try:
            # Define content mapping for different crew types
            content_mapping = {
                "NEWS": "news",
                "POEM": "poem",
                "COOKING": "recipe",
                "LIBRARY": "book_summary",
                "MEETING_PREP": "meeting_prep",
                "LEAD_SCORING": "lead_score",
                "CONTACT_FINDER": "contact_info"
            }
            
            # Include all available content in the email
            email_content = {}
            
            # Add content based on the selected crew
            content_key = content_mapping.get(self.state.selected_crew)
            print(f"Content key from mapping: {content_key}")
            
            if content_key:
                # Try both access methods
                content_from_dict = self.state.content.get(content_key)
                content_direct = getattr(self.state, content_key, "")
                
                print(f"Content from dict: {bool(content_from_dict)}")
                print(f"Content direct: {bool(content_direct)}")
                
                if content_from_dict:
                    email_content[content_key] = content_from_dict
                elif content_direct:
                    email_content[content_key] = content_direct
            
            # Add post report if available
            if self.state.post_report:
                email_content["post_report"] = self.state.post_report
            
            # Send the email
            if email_content:
                print(f"Sending email with content: {list(email_content.keys())}")
                
                # Create a simple HTML email
                html_content = "<html><body>"
                
                # Add the main content
                for content_type, content in email_content.items():
                    if content:
                        if content_type == "post_report":
                            html_content += f"<h2>Additional Information</h2>{content}"
                        else:
                            html_content += content
                
                html_content += "</body></html>"
                
                # Save the email content to a file for debugging
                os.makedirs("output/email", exist_ok=True)
                with open("output/email/email_content.html", "w") as f:
                    f.write(html_content)
                
                print(f"Email content saved to output/email/email_content.html")
                print(f"Email would be sent to {self.state.sendto}")
                
                return "EMAIL_SENT"
            else:
                print("No content to send in the email")
                return "NO_CONTENT"
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            import traceback
            traceback.print_exc()
            return "ERROR"


def kickoff():
    try:
        reception_flow = ReceptionFlow()
        reception_flow.kickoff()
    except KeyboardInterrupt:
        print("\n\nProcess was interrupted by user. Shutting down gracefully...")
        return 1
    except Exception as e:
        print(f"Error in flow execution: {str(e)}")
        return 1
    return 0

def plot():
    reception_flow = ReceptionFlow()
    reception_flow.plot()


if __name__ == "__main__":
    kickoff()

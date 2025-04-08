import os
import datetime 
from pydantic import BaseModel, Field
import re

from crewai.flow import Flow, listen, start, router, or_

from epic_news.router import RequestRouter
from epic_news.crews.contact_finder.contact_finder import ContactFinderCrew
from epic_news.crews.cooking.cooking_crew import CookingCrew
from epic_news.crews.holiday_planner.holiday_planner import HolidayPlannerCrew
from epic_news.crews.library.library import LibraryCrew
from epic_news.crews.meeting_prep.meeting_prep import MeetingPrepCrew
from epic_news.crews.news.news_crew import NewsCrew
from epic_news.crews.poem_crew.poem_crew import PoemCrew
from epic_news.crews.post_crew.post_crew import PostCrew
from epic_news.crews.reception_crew.reception_crew import ReceptionCrew
from epic_news.utils.directory_utils import ensure_output_directories
from epic_news.models import ContentState

def init():
    # Initialize output directories
    ensure_output_directories()

class ReceptionFlow(Flow[ContentState]):

    @start()
    def route_request(self):
        """Route the request to the appropriate crew"""
        # Reset the email_sent flag to ensure we send an email each time
        self.state.email_sent = False
        
        print(f"Routing request: '{self.state.user_request}' with topic: '{self.state.topic}'")
        
        # Use the RequestRouter to route the request
        router = RequestRouter()
        routing_result = router.route(self.state.user_request, self.state.topic)
        
        # Update state with routing results
        self.state.selected_crew = routing_result["crew_type"]
        
        # Update topic if provided and not already set
        if routing_result["topic"] and (not self.state.topic or self.state.topic == self.state.user_request):
            self.state.topic = routing_result["topic"]
        
        # Update any additional parameters
        for param, value in routing_result.get("parameters", {}).items():
            if hasattr(self.state, param) and value:
                setattr(self.state, param, value)
        
        print(f"Selected crew: {self.state.selected_crew}")
        print(f"Updated topic: {self.state.topic}")
        
        return self.state.selected_crew

    @router(route_request)
    def determine_crew(self):
        """Determine which crew to use based on the request"""
        router_decision = self.state.selected_crew
        print(f"Router determining which crew to use based on: {router_decision}")
        
        # If no crew type is selected or it's UNKNOWN, try the reception crew
        if not router_decision or router_decision == "UNKNOWN":
            # Use the reception crew to determine which crew should handle the request
            routing_decision = ReceptionCrew().crew().kickoff(
                inputs={
                    "user_request": self.state.user_request, 
                    "topic": self.state.topic,
                }
            )
            print(f"Reception crew routing decision: {routing_decision}")

            # Extract crew type and update topic if provided
            if isinstance(routing_decision, dict) and "crew_type" in routing_decision:
                self.state.selected_crew = routing_decision["crew_type"]
                if "topic" in routing_decision and routing_decision["topic"]:
                    self.state.topic = routing_decision["topic"]
            else:
                print("Warning: Invalid routing decision format. Using default crew type.")
                # Default to NEWS if reception crew fails
                self.state.selected_crew = "NEWS"
        
        print(f"Final crew selection: {self.state.selected_crew}")
        
        # Map crew types to their respective generation methods
        crew_to_method_map = {
            "NEWS": "GENERATE_NEWS",
            "POEM": "GENERATE_POEM",
            "COOKING": "GENERATE_RECIPE",
            "LIBRARY": "GENERATE_BOOK_SUMMARY",
            "MEETING_PREP": "GENERATE_MEETING_PREP",
            "LEAD_SCORING": "GENERATE_LEAD_SCORE",
            "CONTACT_FINDER": "GENERATE_CONTACT_INFO",
            "HOLIDAY_PLANNER": "GENERATE_HOLIDAY_PLAN"
        }
        
        # Get the method name from the map, or default to "UNKNOWN"
        return crew_to_method_map.get(self.state.selected_crew, "UNKNOWN")

    @listen(determine_crew)
    def generate_poem(self):
        if self.state.selected_crew == "POEM":

            """Generate a poem based on the topic"""
            print(f"Generating poem about: {self.state.topic}")
            
            # Define the output file path
            self.state.output_file = "output/poem/poem.html"
            
            # Create and kickoff the poem crew
            result = PoemCrew().crew().kickoff(inputs={
                "topic": self.state.topic,
                "user_request": self.state.user_request,
                "sentence_count": self.state.sentence_count,
                "output_file": self.state.output_file
            })
                
           
    @listen(determine_crew)
    def generate_news(self):
        if self.state.selected_crew == "NEWS":
            
            """Generate news content based on the topic"""
            print(f"Generating news about: {self.state.topic}")
            
            # Define the output file path directly
            self.state.output_file = "output/news/news.html"
            

            # Generate the news
            NewsCrew().crew().kickoff(inputs={
                "topic": self.state.topic,
                "output_file": self.state.output_file,
                "sentence_count": self.state.sentence_count
            })
              

    @listen(determine_crew)
    def generate_recipe(self):
        if self.state.selected_crew == "COOKING":
            
            """Generate a recipe based on the topic"""
            print(f"Generating recipe for: {self.state.topic}")
            
            # Define the output file path directly
            self.state.output_file = "output/cooking/recipe.html"
            
            # try:
                
                
            # Generate the recipe
            CookingCrew().crew().kickoff(inputs={
                "topic": self.state.topic,
                "output_file": self.state.output_file,
                "sendto": self.state.sendto
            })
                
    @listen(determine_crew)
    def generate_book_summary(self):
        if self.state.selected_crew == "LIBRARY":
            
            """Generate a book summary based on the topic"""
            print(f"Generating book summary for: {self.state.topic}")
            
            # Define the output file path directly
            self.state.output_file  = "output/library/book_summary.html"

            
            # Generate the book summary
            return LibraryCrew().crew().kickoff(inputs={
                "topic": self.state.topic,
                "output_file": self.state.output_file,
                "sendto": self.state.sendto
            })
                
    @listen(determine_crew)
    def generate_meeting_prep(self):
        if self.state.selected_crew == "MEETING_PREP":
            
            """
            Generate meeting preparation content based on the company name
            """
            print(f"Generating meeting prep for company: {self.state.company}")
        
         # Ensure we have a company name
            if not self.state.company and self.state.topic:
                self.state.company = self.state.topic
                print(f"Using topic as company name: {self.state.company}")
            
            # Define the output file path
            self.state.output_file = f"output/meeting/meeting_preparation.html"

            # Generate the meeting prep
            return  MeetingPrepCrew().crew().kickoff(inputs={
                "company": self.state.company,
                "output_file": self.state.output_file,
                "sendto": self.state.sendto,
                "prior_interactions": self.state.prior_interactions,
                "context": self.state.context,
                "objective": self.state.objective,
                "participants": self.state.participants
            })


    @listen(determine_crew)
    def generate_contact_info(self):
        if self.state.selected_crew == "CONTACT_FINDER":
            """Generate contact information for a company"""
            print(f"Finding contacts at: {self.state.company} for product: {self.state.our_product}")
            
            self.state.output_file = "output/contact_finder/approach_strategy.html"

            inputs={
                "company": self.state.company,
                "our_product": self.state.our_product,
                "output_file": self.state.output_file,
                "sendto": self.state.sendto,
            }

            return ContactFinderCrew().crew().kickoff(inputs=inputs)
            

    @listen(determine_crew)
    def generate_holiday_plan(self):
        if self.state.selected_crew == "HOLIDAY_PLANNER":
            
            # """Generate a holiday plan based on the destination"""
            # print(f"Generating holiday plan for: {self.state.destination}")
            
            # # Extract parameters from the request if not already set
            # if not self.state.destination and self.state.topic:
            #     # Try to extract destination from the topic
            #     self.state.destination = self.state.topic
            #     print(f"Using topic as destination: {self.state.destination}")
            
            #     # Extract duration if not set
            #     if not self.state.duration and self.state.user_request:
            #         # Try to extract duration from the request
            #         duration_match = re.search(r"for\s+a\s+([a-zA-Z0-9\s]+)(?:\s+trip|\s+vacation|\s+holiday)?", self.state.user_request, re.IGNORECASE)
            #         if duration_match:
            #             self.state.duration = duration_match.group(1).strip()
            #             print(f"Extracted duration: {self.state.duration}")
            #         else:
            #             # Default to weekend if not specified
            #             self.state.duration = "weekend"
                
            #     # Set default family if not specified
            #     if not self.state.family:
            #         self.state.family = "family of 4 (2 adults, 2 children)"
                
            #     # Set default origin if not specified
            #     if not self.state.origin:
            #         self.state.origin = "Geneva, Switzerland"
                
            #     # Create output directory
            #   
            #     print(f"Parameters: Destination={self.state.destination}, Duration={self.state.duration}, Family={self.state.family}, Origin={self.state.origin}")
                
              
            #     # Create the holiday planner crew
            #     holiday_crew = HolidayPlannerCrew()
            
            self.state.output_file="output/holiday/destination.md"
            # Prepare inputs
            inputs = {
                "destination": self.state.destination,
                "duration": self.state.duration,
                "family": self.state.family,
                "origin": self.state.origin,
                "special_needs": self.state.special_needs,
                "output_file": self.state.output_file,
            }

            print(f"Starting HolidayPlannerCrew with inputs: {inputs}")

            # Run the crew
            return HolidayPlannerCrew().crew().kickoff(inputs=inputs)
                


    @listen(or_(generate_holiday_plan,generate_contact_info,generate_meeting_prep,generate_book_summary,generate_recipe,generate_poem,generate_news))
    def send_email(self):
        """Send an email with the generated content"""
        
        # Reset the email_sent flag to ensure we always send an email
        # self.state.email_sent = False
        
        # Check if we've already sent an email for this flow run
        if hasattr(self.state, 'email_sent') and self.state.email_sent:
            print("Email already sent, skipping")
            return
        else: 
            print(f"Sending email to {self.state.sendto}, crew_type: {self.state.selected_crew}, content : {self.state.output_file}")
            
            # Initialize PostCrew with the necessary inputs
            inputs = {
                'book_summary': self.state.book_summary,
                'contact_info': self.state.contact_info,
                'crew_type': self.state.selected_crew,
                'lead_score': self.state.lead_score,
                'meeting_prep': self.state.meeting_prep,
                'news': self.state.news,
                'output_file': self.state.output_file,
                'poem': self.state.poem,
                'recipe': self.state.recipe,
                'recipient_email': self.state.sendto,
                'topic': self.state.topic,
            }
            
            # Mark that we've sent an email
            self.state.email_sent = True
            
            # Execute the PostCrew to send the email
            return PostCrew().crew().kickoff(inputs=inputs)

def kickoff():
    reception_flow = ReceptionFlow()
    reception_flow.kickoff()
    

def plot():
    reception_flow = ReceptionFlow()
    reception_flow.plot()

if __name__ == "__main__":
    init()
    kickoff()
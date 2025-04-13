import os
import datetime
import select 
from pydantic import BaseModel, Field
import re   

from crewai.flow import Flow, listen, start, router, or_, and_ 
# from epic_news.router import RequestRouter
from epic_news.crews.capture_destination.capture_destination_crew import CaptureDestinationCrew
from epic_news.crews.capture_duration.capture_duration_crew import CaptureDurationCrew
from epic_news.crews.capture_needs.capture_needs_crew import CaptureNeedsCrew
from epic_news.crews.capture_origin.capture_origin_crew import CaptureOriginCrew
from epic_news.crews.capture_travelers.capture_travelers_crew import CaptureTravelersCrew
from epic_news.crews.capture_topic.capture_topic_crew import CaptureTopicCrew
from epic_news.crews.classify.classify_crew import ClassifyCrew
from epic_news.crews.contact_finder.contact_finder_crew import ContactFinderCrew
from epic_news.crews.cooking.cooking_crew import CookingCrew
from epic_news.crews.holiday_planner.holiday_planner_crew import HolidayPlannerCrew
from epic_news.crews.library.library_crew import LibraryCrew
from epic_news.crews.meeting_prep.meeting_prep_crew import MeetingPrepCrew
from epic_news.crews.news.news_crew import NewsCrew
from epic_news.crews.osint.osint_crew import OsintCrew
from epic_news.crews.poem.poem_crew import PoemCrew
from epic_news.crews.post.post_crew import PostCrew
from epic_news.crews.reception.reception_crew import ReceptionCrew
from epic_news.utils.directory_utils import ensure_output_directories
from epic_news.models import ContentState


def init():
    # Initialize output directories
    ensure_output_directories()


"""                                                                                      """ 
"""                                                                                      """ 
"""                     All the magic is here                                            """ 
"""                                                                                      """ 

user_request = (
    "find a restaurant for 4 adults and 4 children on a sunday at 20:00 "
    "near the sacre coeur of Paris in april. only find the restaurant."
    "all the rest is not needed"
)

"""                                                                                      """ 
"""                                                                                      """ 
"""                                                                                      """ 


class ReceptionFlow(Flow[ContentState]):

    @start("go_initialize")
    def initialize(self):
        # Reset the email_sent flag to ensure we send an email each time
        self.state.email_sent = False
        self.state.user_request = user_request
        return "initialize"
        
    @start("go_classify")
    def classify(self):
        """Classify the user request and route it to the appropriate crew"""

      
        self.state.user_request = user_request
        print(f"Routing request: '{self.state.user_request}' with topic: '{self.state.topic}'")
        # Define the output file path directly
        self.state.output_file = "output/classify/decision.md"

        # Prepare input data for classification
        inputs = {
            "user_request": self.state.user_request,
            "output_file": self.state.output_file,
            "categories": self.state.categories,
            "selected_crew": self.state.selected_crew
        }

        # Run the classification crew
        classify_crew = ClassifyCrew()
        result = classify_crew.crew().kickoff(inputs=inputs)
        
        # Extract the selected category from the result
        selected_category = classify_crew.parse_result(result, self.state.categories)
        # print(f"returned result: {selected_category}")
        # Update the state with the selected category
        self.state.selected_crew = selected_category

        return "classify"


    @start("go_find_destination")  
    def find_destination(self):
        self.state.user_request = user_request
 
        # Extract the destination from the user request
        find_destination = CaptureDestinationCrew()
        destination = find_destination.crew().kickoff(inputs={"user_request": self.state.user_request})
        self.state.destination = str(destination)
        return "find_destination"

    @start("go_find_origin")
    def find_origin(self):
        self.state.user_request = user_request

        # Extract the origin from the user request
        find_origin = CaptureOriginCrew()
        origin = find_origin.crew().kickoff(inputs={"user_request": user_request})
        self.state.origin = str(origin)
        return "find_origin"
 
    @start("go_find_needs")
    def find_needs(self):
        self.state.user_request = user_request

        # Extract the needs from the user request
        find_needs = CaptureNeedsCrew()
        needs = find_needs.crew().kickoff(inputs={"user_request": user_request})
        self.state.special_needs = str(needs)
        return "find_needs"
 
    @start("go_find_travelers")
    def find_travelers(self):
        self.state.user_request = user_request

        # Extract the travelers from the user request
        find_travelers = CaptureTravelersCrew()
        travelers = find_travelers.crew().kickoff(inputs={"user_request": user_request})
        self.state.family = str(travelers)
        return "find_travelers"

    @start("go_find_duration")
    def find_duration(self):
        self.state.user_request = user_request

        # Extract the duration from the user request
        find_duration = CaptureDurationCrew()
        duration = find_duration.crew().kickoff(inputs={"user_request": user_request})
        self.state.duration = str(duration)
        return "find_duration"

    @listen(and_("classify", "find_destination", "find_origin", "find_needs", "find_travelers", "find_duration"))
    def finalize_preparation (self):
        return "finalize_preparation"

    @router("finalize_preparation")
    def determine_crew(self):

        """Route based on relationship type to personalize greetings."""
        if self.state.selected_crew == "CONTACT_FINDER":
            return "go_contact_finder"
        elif self.state.selected_crew == "HOLIDAY_PLANNER":
            return "go_generate_holiday_plan"
        elif self.state.selected_crew == "MEETING_PREP":
            return "go_generate_meeting_prep"
        elif self.state.selected_crew == "LIBRARY":
            return "go_generate_book_summary"
        elif self.state.selected_crew == "COOKING":
            return "go_generate_recipe"       
        elif self.state.selected_crew == "POEM":
            return "go_generate_poem"
        elif self.state.selected_crew == "NEWS":
            return "go_generate_news"
        elif self.state.selected_crew == "LEAD_SCORING":
            return "go_generate_leads"
        elif self.state.selected_crew == "OPEN_SOURCE_INTELLIGENCE":
            return "go_generate_osint"
        else:
            return "go_unknown"

    @listen("go_unknown")
    def unknown_crew(self):
        print("I don't know how to do that sorry")


    @listen("go_generate_poem")
    def generate_poem(self):
        if self.state.selected_crew == "POEM":

            """Generate a poem based on the topic"""
            print(f"Generating poem about: {self.state.topic}")
            
            # Define the output file path
            self.state.output_file = "output/poem/poem.html"
            
            # Create and kickoff the poem crew
            PoemCrew().crew().kickoff(inputs={
                "topic": self.state.topic,
                "user_request": self.state.user_request,
                "sentence_count": self.state.sentence_count,
                "output_file": self.state.output_file
            })
            return "finish"
                
           
    @listen("go_generate_news")
    def generate_news(self):
        if self.state.selected_crew == "NEWS":
            
            """Generate news content based on the topic"""
            print(f"Generating news about: {self.state.topic}")
            
            # Define the output file path directly
            self.state.output_file = "output/news/report.html"
            

            # Generate the news
            NewsCrew().crew().kickoff(inputs={
                "topic": self.state.topic,
                "output_file": self.state.output_file,
                "sentence_count": self.state.sentence_count,
                "sendto": self.state.sendto,
                "current_year": self.state.current_year
            })
            return "finish"
              

    @listen("go_generate_recipe")
    def generate_recipe(self):
        if self.state.selected_crew == "COOKING":
            
            """Generate a recipe based on the topic"""
            print(f"Generating recipe for: {self.state.topic}")
            
            # Define the output file path directly
            self.state.output_file = "output/cooking/recipe.html"

            # Generate the recipe
            CookingCrew().crew().kickoff(inputs={
                "topic": self.state.topic,
                "output_file": self.state.output_file,
                "sendto": self.state.sendto
            })
            return "finish"
                
    @listen("go_generate_book_summary")
    def generate_book_summary(self):
        if self.state.selected_crew == "LIBRARY":
            
            """Generate a book summary based on the topic"""
            print(f"Generating book summary for: {self.state.topic}")
            
            # Define the output file path directly
            self.state.output_file  = "output/library/book_summary.html"

            
            # Generate the book summary
            LibraryCrew().crew().kickoff(inputs={
                "topic": self.state.topic,
                "output_file": self.state.output_file,
                "sendto": self.state.sendto
            })
            return "finish"
                
    @listen("go_generate_meeting_prep")
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
            return "finish"


    @listen("go_contact_finder")  
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

            ContactFinderCrew().crew().kickoff(inputs=inputs)
            return "finish"  
            

    @listen("go_generate_osint")
    def generate_osint(self):
        if self.state.selected_crew == "OPEN_SOURCE_INTELLIGENCE":
            """Generate contact information for a company"""
            print(f"Finding contacts at: {self.state.company} ")
            
            self.state.output_file = "output/osint/osfindings.html"

            inputs={
                "company": self.state.company,
                "output_file": self.state.output_file,
                "sendto": self.state.sendto,
            }

            OsintCrew().crew().kickoff(inputs=inputs)
            return "finish"
            

    @listen("go_generate_holiday_plan")
    def generate_holiday_plan(self):
        if self.state.selected_crew == "HOLIDAY_PLANNER":
            self.state.output_file="output/travel_guides/itinerary.html"
            inputs = {
                "destination": self.state.destination,
                "duration": self.state.duration,
                "family": self.state.family,
                "origin": self.state.origin,
                "special_needs": self.state.special_needs,
                "output_file": self.state.output_file,
            }
            print(f"Inputs: {inputs}")

            print(f"Starting HolidayPlannerCrew with inputs: {inputs}")

            # Run the crew
            HolidayPlannerCrew().crew().kickoff(inputs=inputs)
            return "finish"
    
    @listen(or_("generate_holiday_plan", "generate_meeting_prep", "generate_book_summary", "generate_recipe", "generate_poem", "generate_news", "generate_osint"))
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
                'osfindings': self.state.osfindings,
                'output_file': self.state.output_file,
                'poem': self.state.poem,
                'recipe': self.state.recipe,
                'recipient_email': self.state.sendto,
                'topic': self.state.topic,
            }
            
            # Mark that we've sent an email
            self.state.email_sent = True
            
            # Execute the PostCrew to send the email
            PostCrew().crew().kickoff(inputs=inputs)


def kickoff():
    reception_flow = ReceptionFlow()
    reception_flow.kickoff()
    

def plot():
    reception_flow = ReceptionFlow()
    reception_flow.plot()

if __name__ == "__main__":
    init()
    kickoff()
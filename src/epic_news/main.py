from crewai.flow import Flow, and_, listen, or_, router, start
from dotenv import load_dotenv

from epic_news.crews.classify.classify_crew import ClassifyCrew
from epic_news.crews.company_profiler.company_profiler_crew import CompanyProfilerCrew
from epic_news.crews.cooking.cooking_crew import CookingCrew
from epic_news.crews.cross_reference_report_crew.cross_reference_report_crew import CrossReferenceReportCrew
from epic_news.crews.find_contacts.find_contacts_crew import FindContactsCrew
from epic_news.crews.find_location.find_location_crew import FindLocationCrew
from epic_news.crews.geospatial_analysis.geospatial_analysis_crew import GeospatialAnalysisCrew
from epic_news.crews.holiday_planner.holiday_planner_crew import HolidayPlannerCrew
from epic_news.crews.hr_intelligence.hr_intelligence_crew import HRIntelligenceCrew
from epic_news.crews.information_extraction.information_extraction_crew import InformationExtractionCrew
from epic_news.crews.legal_analysis.legal_analysis_crew import LegalAnalysisCrew
from epic_news.crews.library.library_crew import LibraryCrew
from epic_news.crews.marketing_writers.marketing_writers_crew import MarketingWritersCrew
from epic_news.crews.meeting_prep.meeting_prep_crew import MeetingPrepCrew
from epic_news.crews.news.news_crew import NewsCrew
from epic_news.crews.poem.poem_crew import PoemCrew
from epic_news.crews.post.post_crew import PostCrew
from epic_news.crews.post_only.post_only_crew import PostOnlyCrew
from epic_news.crews.tech_stack.tech_stack_crew import TechStackCrew
from epic_news.crews.web_presence.web_presence_crew import WebPresenceCrew
from epic_news.models import ContentState
from epic_news.utils.directory_utils import ensure_output_directories

load_dotenv()


def init():
    # Initialize output directories
    ensure_output_directories()


"""                                                                                      """
"""                                                                                      """
"""                     All the magic is here                                            """
"""                                                                                      """

user_request = (
    "find osint  about the company ''"
    "PLEASE GIVE YOUR SOURCES !!!"
)

"""                                                                                      """
"""                                                                                      """
"""                                                                                      """


#
class ReceptionFlow(Flow[ContentState]):


    @start()
    def feed_user_request(self):
        # Reset the email_sent flag to ensure we send an email each time
        self.state.email_sent = False
        self.state.user_request = user_request
        # return "feed_user_request"

    @listen("feed_user_request")
    def extract_info(self):
        """Extract all necessary information from the user request in a single step."""
        print("🤖 Kicking off Information Extraction Crew...")
        # Instantiate and run the information extraction crew
        extraction_crew = InformationExtractionCrew()
        extracted_data = extraction_crew.crew().kickoff(
            inputs={"user_request": self.state.user_request}
        )

        # Update the state with the extracted information
        if extracted_data:
            self.state.extracted_info = extracted_data.pydantic
            print("✅ Information extraction complete.")
        else:
            print("⚠️ Information extraction failed or returned no data.")

        # return "extract_info"

    @listen("extract_info")
    def classify(self):
        """Classify the user request and route it to the appropriate crew"""
        topic = (
            self.state.extracted_info.main_subject_or_activity
            if self.state.extracted_info
            else ""
        )
        print(
            f"Routing request: '{self.state.user_request}' with topic: '{topic}'"
        )
        # Define the output file path directly
        self.state.output_file = "output/classify/decision.md"

        # Prepare input data for classification using the centralized method
        inputs = self.state.to_crew_inputs()

        # Instantiate and run the classification crew
        classify_crew = ClassifyCrew()
        classification_result = classify_crew.crew().kickoff(inputs=inputs)

        # Parse the result and update the state
        self.state.selected_crew = classify_crew.parse_result(
            classification_result, self.state.categories
        )
        print(f"✅ Classification complete. Selected crew: {self.state.selected_crew}")

        # return "classify"

    @router("classify")
    def determine_crew(self):
        """Route based on selected crew type using a map."""
        if self.state.selected_crew == "CONTACT_FINDER":
            return "go_generate_contact_info"
        elif self.state.selected_crew == "HOLIDAY_PLANNER":
            return "go_generate_holiday_plan"
        elif self.state.selected_crew == "POST_ONLY":
            return "go_generate_post_only"
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
        elif self.state.selected_crew == "LOCATION":
            return "go_find_location"
        elif self.state.selected_crew == "OPEN_SOURCE_INTELLIGENCE":
            return "go_generate_osint"
        elif self.state.selected_crew == "MARKETING_WRITERS":
            return "go_generate_marketing_content"
        else:
            return "go_unknown"

    @listen("go_generate_post_only")
    def generate_post_only(self):
        """Generate a post-only based on the topic"""
        self.state.output_file = "output/travel_guides/itinerary.html"
        print(f"Generating post-only about: {self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Create and kickoff the post-only crew
        self.state.post_report = PostOnlyCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_post_only"

    @listen("go_generate_poem")
    def generate_poem(self):
        """Generate a poem based on the topic"""
        self.state.output_file = "output/poem/poem.html"
        print(f"Generating poem about: {self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Generate the poem
        self.state.poem = PoemCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_poem"

    @listen("go_generate_news")
    def generate_news(self):
        """Generate news content based on the topic"""
        self.state.output_file = "output/news/report.html"
        print(f"Generating news about: {self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Generate the news
        self.state.news_report = NewsCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_news"

    @listen("go_find_location")
    def find_location(self):
        """Find a location based on the topic"""
        self.state.output_file = "output/location/location.html"
        print(f"Finding location for: {self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Generate the location
        self.state.location_report = FindLocationCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "find_location"

    @listen("go_generate_recipe")
    def generate_recipe(self):
        """Generate a recipe based on the topic"""
        self.state.output_file = "output/cooking/recipe.html"
        self.state.attachment_file = "output/cooking/paprika_recipe.yaml"
        print(f"Generating recipe for: {self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Generate the recipe
        self.state.recipe = CookingCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_recipe"

    @listen("go_generate_book_summary")
    def generate_book_summary(self):
        """Generate a book summary based on the topic"""
        self.state.output_file = "output/library/book_summary.html"
        self.state.attachment_file = "output/library/research_results.md"
        print(f"Generating book summary for: {self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Generate the book summary
        self.state.book_summary = LibraryCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_book_summary"

    @listen("go_generate_meeting_prep")
    def generate_meeting_prep(self):
        """
        Generate meeting preparation content based on the company name
        """
        self.state.output_file = "output/meeting/meeting_preparation.html"
        # Prepare inputs and handle company fallback
        current_inputs = self.state.to_crew_inputs()
        company = current_inputs.get('company')
        if not company:
            company = current_inputs.get('topic')
            current_inputs['company'] = company # Modify the dict before passing
            print(f"Using topic as company name: {company}")

        print(f"Generating meeting prep for company: {company}")

        # Generate the meeting prep
        self.state.meeting_prep_report = MeetingPrepCrew().crew().kickoff(inputs=current_inputs)
        # return "generate_meeting_prep"

    @listen("go_generate_contact_info")
    def generate_contact_info(self):
        """Generate contact information for a company"""
        self.state.output_file = "output/contact_finder/approach_strategy.html"
        company = self.state.to_crew_inputs().get('target_company')
        print(
            f"Finding contacts at: {company} for product: {self.state.to_crew_inputs().get('our_product', 'N/A')}"
        )

        self.state.contact_info_report = FindContactsCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_contact_info"

    @listen("go_generate_osint")
    def generate_osint(self):
        """Generate OSINT report for a company"""
        pass 
        # return "generate_osint"
        
        
        
    @listen("generate_osint")
    def generate_company_profile(self):
        """Generate company profile based on the company name"""
        # self.state.output_file = "output/osint/company_profile.html"
        print(f"Generating company profile for: {self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Get company name from state inputs

        self.state.company_profile = CompanyProfilerCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_company_profile"
            
    @listen("generate_osint")
    def generate_tech_stack(self):
        """Generate company profile based on the company name"""
        # self.state.output_file = "output/osint/tech_stack.html"
        print(f"Generating Tech Stack for: {self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Get company name from state inputs
        self.state.tech_stack = TechStackCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_company_profile"

    @listen("generate_osint")
    def generate_web_presence(self):
        """Generate company profile based on the company name"""
        # self.state.output_file = "output/osint/web_presence.html"
        print(f"Generating Web Presence for: {self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Get company name from state inputs
        company_name = self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'Unknown Company')
        self.state.web_presence_report = WebPresenceCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_company_profile"
        
    @listen("generate_osint")
    def generate_hr_intelligence(self):
        """Generate company profile based on the company name"""
        # self.state.output_file = "output/osint/hr_intelligence.html"
        print(f"Generating HR Intelligence for: {self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Get company name from state inputs
        company_name = self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'Unknown Company')
        self.state.hr_intelligence_report = HRIntelligenceCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_company_profile"        

    @listen("generate_osint")
    def generate_legal_analysis(self):
        """Generate company profile based on the company name"""
        # self.state.output_file = "output/osint/legal_analysis.html"
        print(f"Generating Legal Analysis for: {self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Get company name from state inputs
        company_name = self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'Unknown Company')
        self.state.legal_analysis_report = LegalAnalysisCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_company_profile"

    @listen("generate_osint")
    def generate_geospatial_analysis(self):
        """Generate company profile based on the company name"""
        # self.state.output_file = "output/osint/geospatial_analysis.html"
        print(f"Generating Geospatial Analysis for: {self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Get company name from state inputs
        company_name = self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'Unknown Company')
        self.state.geospatial_analysis = GeospatialAnalysisCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # retun "generate_company_profile"

    @listen(and_( "generate_company_profile", "generate_tech_stack", "generate_web_presence", "generate_hr_intelligence", "generate_legal_analysis", "generate_geospatial_analysis"))
    def generate_cross_reference_report(self):
        """Generate cross reference report based on the company name"""
        # self.state.output_file = "output/osint/cross_reference_report.html"
        print(f"Generating Cross Reference Report for: {self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Get company name from state inputs
        company_name = self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'Unknown Company')
        self.state.cross_reference_report = CrossReferenceReportCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_company_profile"

    @listen("go_generate_holiday_plan")
    def generate_holiday_plan(self):
        self.state.output_file = "output/travel_guides/itinerary.html"
        current_inputs = self.state.to_crew_inputs()

        if not current_inputs.get('destination'):
            print("⚠️ No destination found for holiday plan. Aborting.")
            return "error"  # Or another appropriate error state

        print(f"Starting HolidayPlannerCrew with inputs: {current_inputs}")

        # Run the crew
        self.state.holiday_plan = HolidayPlannerCrew().crew().kickoff(inputs=current_inputs)
        # return "generate_holiday_plan"

    @listen("go_generate_marketing_content")
    def generate_marketing_content(self):
        """Generate enhanced marketing content in French based on the original message"""
        self.state.output_file = "output/marketing/enhanced_message.html"
        print(f"Enhancing marketing message about: {self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Create and kickoff the marketing writers crew
        self.state.marketing_report = MarketingWritersCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_marketing_content"

    @listen(or_("find_location",
                "generate_book_summary", 
                "generate_contact_info", 
                "generate_holiday_plan",
                "generate_leads", 
                "generate_marketing_content",
                "generate_meeting_prep",
                "generate_news", 
                "generate_poem",
                "generate_post_only", 
                "generate_recipe"
                )
            )
    def join(self):
        """Join the crew"""
        return "done"

    @listen("join")
    def next_level(self):
        """Go to next level"""
        return "done"
    

    @listen(or_( 
                "generate_cross_reference_report", 
                "next_level"
                ))
    def send_email(self):
        if not self.state.email_sent:
            """Send an email with the generated content"""
            print(f"Sending email to: {self.state.sendto}")
            
            # Get topic from extracted_info if available, otherwise use a default
            topic = "Unknown Topic"
            if self.state.extracted_info:
                if hasattr(self.state.extracted_info, "main_subject_or_activity"):
                    topic = self.state.extracted_info.main_subject_or_activity
            
            # Create inputs dictionary with safely accessed values
            inputs = {
                "output_file": self.state.output_file,
                "recipient_email": self.state.sendto,
                "topic": topic,
                "attachment": self.state.attachment_file,
                "attachment_file": self.state.attachment_file,
            }

            print(f"Inputs: {inputs}")
            PostCrew().crew().kickoff(inputs=inputs)
            self.state.email_sent = True
            
            # Exit the program after sending the email
            print("Email sent successfully. Exiting program.")
            return "done"
    
    # @listen("send_email")
    # def go_unknown(self):
    #     """Go to unknown state"""
    #     self.state.email_sent = True


def kickoff():
    reception_flow = ReceptionFlow()
    reception_flow.kickoff()


def plot():
    reception_flow = ReceptionFlow()
    reception_flow.plot()


if __name__ == "__main__":
    init()
    kickoff()

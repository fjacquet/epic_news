#!/usr/bin/env python
from src.epic_news.main import ContentState, ReceptionFlow

def test_lead_scoring():
    """
    Test the lead scoring crew integration with proper parameters.
    """
    # Create a ContentState with lead scoring specific parameters
    state = ContentState(
        user_request="Score this lead for our AI product",
        topic="Lead Scoring Test",
        selected_crew="LEAD_SCORING",  # Directly set the crew type
        sendto="fred.jacquet@gmail.com",
        company="Our Tech Company",
        form_response="""Name: John Smith
        Company: Enterprise Solutions Inc.
        Position: CTO
        Email: john.smith@enterprise-solutions.com
        Phone: +1-555-123-4567
        Company Size: 1000-5000 employees
        Industry: Healthcare Technology

        Current Challenges: We're looking to implement AI solutions to improve our patient data analysis and predictive diagnostics. Our current systems are outdated and don't provide the insights we need.

        Budget Range: $100,000 - $250,000

        Timeline: Looking to implement within the next 6 months

        Additional Information: We've tried some off-the-shelf solutions but they don't integrate well with our existing infrastructure. We need something customizable and scalable.
        """,
        product_name="AI Analytics Platform",
        product_description="An advanced AI analytics platform that helps enterprises extract insights from their data, with particular strengths in healthcare, finance, and retail sectors. Our platform integrates with existing systems and provides customizable dashboards and predictive analytics capabilities.",
        icp_description="Enterprise clients with 1000+ employees in healthcare, finance, or retail sectors with a need for advanced data analytics and AI-driven insights."
    )
    
    # Initialize the ReceptionFlow with our state
    flow = ReceptionFlow()
    flow.state = state
    
    # Skip the routing and directly run the lead scoring process
    print("Starting lead scoring process...")
    print(f"Using company: {state.company}")
    print(f"Form response length: {len(state.form_response)} characters")
    
    # Directly call the generate_lead_score method
    result = flow.generate_lead_score()
    
    print(f"Process completed with result: {result}")
    print("Check the output/lead_scoring directory for the generated document")
    
    # Send email with the generated content
    email_result = flow.send_email()
    print(f"Email result: {email_result}")
    print(f"Email sent to: {state.sendto}")

if __name__ == "__main__":
    test_lead_scoring()

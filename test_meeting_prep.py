#!/usr/bin/env python
from src.epic_news.main import ContentState, ReceptionFlow

def test_meeting_prep():
    """
    Test the meeting prep crew integration with proper parameters.
    """
    # Create a ContentState with meeting prep specific parameters
    state = ContentState(
        user_request="Prepare for a meeting with Sitel",
        topic="Sitel",
        selected_crew="MEETING_PREP",  # Directly set the crew type
        sendto="fred.jacquet@gmail.com",
        company="Sitel",  # Ensure company name is set
        participants=[
            "John Doe <john.doe@acme.com> - CEO",
            "Jane Smith <jane.smith@acme.com> - CTO",
            "Bob Johnson <bob.johnson@acme.com> - Sales Director"
        ],
        context="Second technical meeting to discuss potential private cloud implementation using powerflex and openshift",
        objective="Present our product offerings and identify potential collaboration opportunities",
        prior_interactions="We had a brief call with their CTO last month who expressed interest in our private cloud solutions"
    )
    
    # Initialize the ReceptionFlow with our state
    flow = ReceptionFlow()
    flow.state = state
    
    # Skip the routing and directly run the meeting prep process
    print("Starting meeting preparation process...")
    print(f"Using company: {state.company}")
    print(f"Participants: {state.participants}")
    
    # Directly call the generate_meeting_prep method
    result = flow.generate_meeting_prep()
    
    print(f"Process completed with result: {result}")
    print("Check the output/meeting directory for the generated document")
    
    # Send email with the generated content
    email_result = flow.send_email()
    print(f"Email result: {email_result}")
    print(f"Email sent to: {state.sendto}")

if __name__ == "__main__":
    test_meeting_prep()

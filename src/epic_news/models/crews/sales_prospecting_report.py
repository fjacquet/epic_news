from __future__ import annotations

from pydantic import BaseModel, Field


class KeyContact(BaseModel):
    """
    Pydantic model for a key contact.
    """

    name: str = Field(..., description="Name of the key contact.")
    role: str = Field(..., description="Role of the key contact.")
    department: str = Field(..., description="Department of the key contact.")
    contact_info: str = Field(..., description="Contact information for the key contact.")


class SalesProspectingReport(BaseModel):
    """
    Pydantic model for the sales prospecting crew output.
    """

    company_overview: str = Field(..., description="An overview of the company.")
    key_contacts: list[KeyContact] = Field(..., description="A list of key contacts at the company.")
    approach_strategy: str = Field(..., description="The developed sales approach strategy.")
    remaining_information: str = Field(..., description="Further insights and remaining information.")

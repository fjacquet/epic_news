from pydantic import BaseModel, Field


class MarketingReport(BaseModel):
    """
    Pydantic model for the marketing writers crew output.
    """

    topic: str = Field(..., description="The topic of the marketing campaign.")
    market_analysis: str = Field(..., description="The analysis of the market provided by the specialist.")
    enhanced_message: str = Field(
        ..., description="The final enhanced marketing message from the copywriter."
    )

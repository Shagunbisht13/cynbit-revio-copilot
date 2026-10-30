"""Pydantic data models and schemas for Revio Review Intelligence Engine."""

from typing import List, Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator


SentimentType = Literal["positive", "neutral", "negative"]
CrisisCategory = Literal[
    "none",
    "health_safety",
    "legal_threat",
    "fraud_scam",
    "discrimination",
    "viral_reputation"
]
CrisisSeverity = Literal["low", "medium", "high"]
BrandVoiceTone = Literal["professional", "warm", "concise"]
ApprovalStatus = Literal["pending", "approved", "edited", "rejected"]


class AspectItem(BaseModel):
    """Extracted aspect with assigned sentiment and evidence span."""
    aspect: str = Field(description="Aspect category, e.g., service, staff, price, cleanliness, delivery, quality, ambiance")
    sentiment: SentimentType = Field(description="Sentiment specifically towards this aspect")
    evidence: Optional[str] = Field(default=None, description="Direct quote or snippet from review text")


class CrisisFlag(BaseModel):
    """Urgent risk detection classification with severity and escalation reason."""
    is_crisis: bool = Field(default=False, description="True if the review demands immediate operational or legal escalation")
    category: CrisisCategory = Field(default="none", description="Specific risk classification")
    severity: CrisisSeverity = Field(default="low", description="Severity tier: low, medium, high")
    reason: str = Field(default="No crisis triggers identified", description="Detailed explanation of why this was flagged")
    recommended_action: str = Field(default="Standard response workflow", description="Immediate mitigation or escalation step for staff")


class ReviewAnalysis(BaseModel):
    """Comprehensive analysis result for an individual customer review."""
    review_id: Optional[str] = Field(default=None, description="Unique identifier for the review")
    review_text: str = Field(description="Raw customer review text")
    overall_sentiment: SentimentType = Field(description="Dominant sentiment classification")
    sentiment_confidence: float = Field(ge=0.0, le=1.0, description="Model confidence score between 0.0 and 1.0")
    aspects: List[AspectItem] = Field(default_factory=list, description="Extracted aspect-level sentiments")
    crisis: CrisisFlag = Field(default_factory=CrisisFlag, description="Crisis detection assessment")
    draft_reply: str = Field(description="Drafted response adhering to brand voice and guardrails")
    brand_tone: BrandVoiceTone = Field(default="professional", description="Applied brand voice tone")
    engine_used: str = Field(default="offline-fallback", description="Engine that processed the review ('gemini-flash' or 'offline-fallback')")
    approval_status: ApprovalStatus = Field(default="pending", description="Human-in-the-loop review status")
    human_edited_reply: Optional[str] = Field(default=None, description="Human reviewer edited text if modified")
    location: Optional[str] = Field(default=None, description="Branch or business location")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Customer star rating if available")
    date: Optional[str] = Field(default=None, description="Date of review if available")

    @field_validator("overall_sentiment", mode="before")
    @classmethod
    def normalize_sentiment(cls, v):
        if isinstance(v, str):
            v_clean = v.strip().lower()
            if "pos" in v_clean:
                return "positive"
            if "neg" in v_clean:
                return "negative"
            if "neu" in v_clean:
                return "neutral"
        return v


class BatchAnalysisSummary(BaseModel):
    """Aggregated metrics across a collection of analyzed reviews."""
    total_reviews: int
    sentiment_counts: dict[str, int]
    crisis_count: int
    top_negative_aspects: List[tuple[str, int]]
    location_breakdown: dict[str, dict[str, Any]] = Field(default_factory=dict)
    executive_summary: str = Field(description="Auto-generated weekly insights paragraph")

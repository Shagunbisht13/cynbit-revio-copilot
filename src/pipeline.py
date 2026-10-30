"""Central analysis pipeline orchestrator for Cynbit Revio Review Intelligence Engine."""

import re
from typing import List, Optional, Dict, Any
from src.models import (
    ReviewAnalysis,
    BrandVoiceTone,
)
from src.llm_client import GeminiReviewClient, LLMConfigurationError, LLMExecutionError
from src.fallback import run_offline_analysis


FORBIDDEN_PROMISES = [
    r"\brefund\b",
    r"\bfree (stay|meal|service|room|procedure)\b",
    r"\bdiscount voucher\b",
    r"\bmonetary compensation\b",
    r"\bwe admit fault\b",
    r"\bwe accept liability\b",
]


class ReviewIntelligencePipeline:
    """Unified pipeline routing between Gemini Flash and deterministic offline fallback."""

    def __init__(self, api_key: Optional[str] = None, force_fallback: bool = False):
        self.force_fallback = force_fallback
        self.llm_client = None if force_fallback else GeminiReviewClient(api_key=api_key)

    @property
    def is_llm_active(self) -> bool:
        """Returns True if the pipeline is operating with a live Gemini model."""
        return (not self.force_fallback) and (self.llm_client is not None) and self.llm_client.is_configured()

    def enforce_guardrails(self, analysis: ReviewAnalysis) -> ReviewAnalysis:
        """Enforces brand safety and anti-hallucination guardrails on the drafted reply."""
        reply = analysis.draft_reply

        # Check for unapproved financial or liability promises
        violates_promise = any(re.search(pat, reply, re.IGNORECASE) for pat in FORBIDDEN_PROMISES)
        if violates_promise:
            # Sanitize forbidden promises by replacing with review commitment
            sanitized = re.sub(
                r"(we will refund|we promise a free stay|we offer a full discount|we admit fault)[^.]*\.",
                "our management will personally review your account details.",
                reply,
                flags=re.IGNORECASE
            )
            analysis.draft_reply = sanitized

        # Ensure crisis replies include private escalation channel
        if analysis.crisis.is_crisis and "escalations@cynbit-client.com" not in analysis.draft_reply:
            analysis.draft_reply += (
                " Please reach out directly to our leadership team at escalations@cynbit-client.com "
                "so we may address this with the utmost priority."
            )

        return analysis

    def process_review(
        self,
        review_text: str,
        brand_tone: BrandVoiceTone = "professional",
        location: str = "General",
        rating: Optional[int] = None,
        review_id: Optional[str] = None,
        date: Optional[str] = None,
    ) -> ReviewAnalysis:
        """Processes a single review through Gemini Flash or graceful offline fallback."""
        if not review_text or not review_text.strip():
            raise ValueError("Review text cannot be empty.")

        # If LLM is configured and not forced to offline
        if self.is_llm_active:
            try:
                analysis = self.llm_client.analyze_review(
                    review_text=review_text.strip(),
                    brand_tone=brand_tone,
                    location=location,
                    rating=rating,
                    review_id=review_id,
                    date=date,
                )
                return self.enforce_guardrails(analysis)
            except (LLMConfigurationError, LLMExecutionError):
                # Graceful degradation to offline engine
                pass

        # Offline fallback path
        analysis = run_offline_analysis(
            review_text=review_text.strip(),
            brand_tone=brand_tone,
            location=location,
            rating=rating,
            review_id=review_id,
            date=date,
        )
        return self.enforce_guardrails(analysis)

    def process_batch(
        self,
        reviews_data: List[Dict[str, Any]],
        brand_tone: BrandVoiceTone = "professional",
    ) -> List[ReviewAnalysis]:
        """Processes a collection of review dictionaries."""
        results: List[ReviewAnalysis] = []
        for item in reviews_data:
            analysis = self.process_review(
                review_text=item.get("review_text", ""),
                brand_tone=brand_tone,
                location=item.get("location", "General"),
                rating=int(item["rating"]) if item.get("rating") is not None and str(item["rating"]).isdigit() else None,
                review_id=item.get("review_id"),
                date=item.get("date"),
            )
            results.append(analysis)
        return results

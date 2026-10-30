"""Google Gemini Flash LLM client with structured JSON parsing and retry logic."""

import json
import os
import re
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from src.models import (
    ReviewAnalysis,
    AspectItem,
    CrisisFlag,
    BrandVoiceTone,
)
from src.prompts import SYSTEM_PROMPT, build_analysis_prompt

load_dotenv()


class LLMConfigurationError(Exception):
    """Raised when API key or model configuration is missing or invalid."""
    pass


class LLMExecutionError(Exception):
    """Raised when an unrecoverable error occurs during LLM execution."""
    pass


class GeminiReviewClient:
    """Client for performing review intelligence analysis using Google Gemini Flash."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.client = None

        if self.api_key and self.api_key.strip():
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key.strip())
            except Exception as e:
                self.client = None

    def is_configured(self) -> bool:
        """Returns True if the client has a valid API key and client initialized."""
        return self.client is not None and bool(self.api_key and self.api_key.strip())

    def _clean_json_response(self, raw_text: str) -> str:
        """Extracts and strips JSON payload from model response text."""
        cleaned = raw_text.strip()
        # Remove markdown codeblock syntax if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    def analyze_review(
        self,
        review_text: str,
        brand_tone: BrandVoiceTone = "professional",
        location: str = "General",
        rating: Optional[int] = None,
        review_id: Optional[str] = None,
        date: Optional[str] = None,
        max_retries: int = 2,
    ) -> ReviewAnalysis:
        """Invokes Gemini Flash model with retries and structured schema validation."""
        if not self.is_configured():
            raise LLMConfigurationError("GEMINI_API_KEY is not configured or client failed to initialize.")

        prompt = build_analysis_prompt(review_text, brand_tone=brand_tone, location=location)
        contents = f"{SYSTEM_PROMPT}\n\n{prompt}"

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                )

                if not response or not response.text:
                    raise LLMExecutionError("Empty response received from Gemini API.")

                cleaned_json = self._clean_json_response(response.text)
                parsed = json.loads(cleaned_json)

                # Validate crisis payload
                crisis_data = parsed.get("crisis", {})
                crisis_flag = CrisisFlag(
                    is_crisis=bool(crisis_data.get("is_crisis", False)),
                    category=crisis_data.get("category", "none"),
                    severity=crisis_data.get("severity", "low"),
                    reason=crisis_data.get("reason", "No crisis triggers identified"),
                    recommended_action=crisis_data.get("recommended_action", "Standard workflow"),
                )

                # Validate aspects
                aspects_list = []
                for a in parsed.get("aspects", []):
                    aspects_list.append(AspectItem(
                        aspect=a.get("aspect", "general"),
                        sentiment=a.get("sentiment", "neutral"),
                        evidence=a.get("evidence"),
                    ))

                return ReviewAnalysis(
                    review_id=review_id,
                    review_text=review_text,
                    overall_sentiment=parsed.get("overall_sentiment", "neutral"),
                    sentiment_confidence=float(parsed.get("sentiment_confidence", 0.90)),
                    aspects=aspects_list,
                    crisis=crisis_flag,
                    draft_reply=parsed.get("draft_reply", ""),
                    brand_tone=brand_tone,
                    engine_used=f"gemini-flash ({self.model_name})",
                    approval_status="pending",
                    location=location,
                    rating=rating,
                    date=date,
                )

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    time.sleep(1.0 * (2 ** attempt))  # Exponential backoff

        raise LLMExecutionError(f"Gemini API analysis failed after {max_retries + 1} attempts: {last_error}")

"""Unit tests for brand voice reply guardrails and anti-hallucination policies."""

import pytest
from src.models import ReviewAnalysis, CrisisFlag
from src.pipeline import ReviewIntelligencePipeline


def test_guardrail_prevents_unauthorized_refund():
    pipeline = ReviewIntelligencePipeline(force_fallback=True)
    
    # Analysis with a simulated hallucinated refund promise
    raw_analysis = ReviewAnalysis(
        review_text="Food was cold and late.",
        overall_sentiment="negative",
        sentiment_confidence=0.90,
        crisis=CrisisFlag(is_crisis=False),
        draft_reply="We apologize for this. We will refund your full bill immediately.",
        brand_tone="professional",
    )
    
    guarded = pipeline.enforce_guardrails(raw_analysis)
    assert "refund" not in guarded.draft_reply.lower()
    assert "personally review your account details" in guarded.draft_reply.lower()


def test_guardrail_crisis_includes_escalation_channel():
    pipeline = ReviewIntelligencePipeline(force_fallback=True)
    
    crisis_flag = CrisisFlag(
        is_crisis=True,
        category="health_safety",
        severity="high",
        reason="Food poisoning alert",
        recommended_action="Escalate to management",
    )
    
    raw_analysis = ReviewAnalysis(
        review_text="I was hospitalized with severe food poisoning.",
        overall_sentiment="negative",
        sentiment_confidence=0.99,
        crisis=crisis_flag,
        draft_reply="We are very sorry to hear this happened to you.",
        brand_tone="professional",
    )
    
    guarded = pipeline.enforce_guardrails(raw_analysis)
    assert "escalations@cynbit-client.com" in guarded.draft_reply

"""Unit tests for offline fallback end-to-end pipeline execution."""

import pytest
from src.fallback import run_offline_analysis, analyze_sentiment, extract_aspects


def test_sarcasm_detection():
    text = "Oh wonderful, 50 minutes of waiting just to get lukewarm soup and stale bread. Truly five-star efficiency!"
    sentiment, confidence = analyze_sentiment(text)
    assert sentiment == "negative"
    assert confidence >= 0.85


def test_aspect_extraction_multi():
    text = "The doctor was compassionate and clinical care was top notch, but the front desk billing took 45 minutes."
    aspects = extract_aspects(text)
    aspect_names = {a.aspect for a in aspects}
    assert "staff" in aspect_names or "service" in aspect_names or "price" in aspect_names


def test_offline_analysis_end_to_end():
    text = "Exceptional stay! Immaculate rooms and lavish breakfast spread. Staff greeted us warmly."
    analysis = run_offline_analysis(
        review_text=text,
        brand_tone="warm",
        location="Jaipur HQ",
        rating=5,
    )
    assert analysis.overall_sentiment == "positive"
    assert analysis.sentiment_confidence >= 0.70
    assert analysis.engine_used == "offline-fallback"
    assert analysis.crisis.is_crisis is False
    assert len(analysis.draft_reply) > 20
    assert analysis.approval_status == "pending"


def test_brand_tones_generated():
    text = "Great haircut and friendly conversation with stylist."
    warm = run_offline_analysis(text, brand_tone="warm")
    concise = run_offline_analysis(text, brand_tone="concise")
    prof = run_offline_analysis(text, brand_tone="professional")

    assert warm.draft_reply != concise.draft_reply
    assert len(concise.draft_reply) <= len(warm.draft_reply) + 20

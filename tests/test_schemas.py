"""Unit tests for Pydantic schema validation and normalization."""

import pytest
from pydantic import ValidationError
from src.models import AspectItem, CrisisFlag, ReviewAnalysis


def test_aspect_item_valid():
    item = AspectItem(aspect="service", sentiment="positive", evidence="fast and helpful")
    assert item.aspect == "service"
    assert item.sentiment == "positive"
    assert item.evidence == "fast and helpful"


def test_aspect_item_invalid_sentiment():
    with pytest.raises(ValidationError):
        AspectItem(aspect="service", sentiment="super_happy")


def test_crisis_flag_defaults():
    crisis = CrisisFlag()
    assert not crisis.is_crisis
    assert crisis.category == "none"
    assert crisis.severity == "low"


def test_review_analysis_normalization():
    analysis = ReviewAnalysis(
        review_text="Great experience and clean rooms.",
        overall_sentiment="POS",  # Should normalize to 'positive'
        sentiment_confidence=0.95,
        draft_reply="Thank you for your feedback!",
    )
    assert analysis.overall_sentiment == "positive"
    assert analysis.sentiment_confidence == 0.95
    assert analysis.approval_status == "pending"


def test_review_analysis_confidence_bounds():
    # Confidence must be between 0.0 and 1.0
    with pytest.raises(ValidationError):
        ReviewAnalysis(
            review_text="Test",
            overall_sentiment="neutral",
            sentiment_confidence=1.5,
            draft_reply="Test reply",
        )

    with pytest.raises(ValidationError):
        ReviewAnalysis(
            review_text="Test",
            overall_sentiment="neutral",
            sentiment_confidence=-0.1,
            draft_reply="Test reply",
        )

"""Unit tests for crisis and urgent review detection rules."""

import pytest
from src.fallback import detect_crisis


def test_crisis_health_safety_food_poisoning():
    text = "We had acute food poisoning after dinner and spent the night hospitalized in the ICU."
    crisis = detect_crisis(text)
    assert crisis.is_crisis is True
    assert crisis.category == "health_safety"
    assert crisis.severity == "high"
    assert "hospitalized" in crisis.reason or "food poisoning" in crisis.reason


def test_crisis_legal_threat():
    text = "Sending a legal notice through my lawyer to your Jaipur office under the consumer protection act."
    crisis = detect_crisis(text)
    assert crisis.is_crisis is True
    assert crisis.category == "legal_threat"
    assert crisis.severity == "high"


def test_crisis_discrimination():
    text = "Front desk staff used a racial slur and denied entry to my companion in a wheelchair."
    crisis = detect_crisis(text)
    assert crisis.is_crisis is True
    assert crisis.category == "discrimination"
    assert crisis.severity == "high"


def test_crisis_fraud_scam():
    text = "Total financial fraud! You forged my signature on an unauthorized charge."
    crisis = detect_crisis(text)
    assert crisis.is_crisis is True
    assert crisis.category == "fraud_scam"
    assert crisis.severity == "high"


def test_crisis_viral_reputation():
    text = "I filmed the entire video and it is already trending on Twitter with 150k views."
    crisis = detect_crisis(text)
    assert crisis.is_crisis is True
    assert crisis.category == "viral_reputation"
    assert crisis.severity == "high"


def test_non_crisis_standard_complaint():
    text = "The soup was lukewarm and it took 25 minutes for the waiter to bring the bill."
    crisis = detect_crisis(text)
    assert crisis.is_crisis is False
    assert crisis.category == "none"
    assert crisis.severity in ["low", "medium"]

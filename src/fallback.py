"""Offline fallback engine for Revio Review Intelligence Engine.

Provides deterministic, zero-dependency analysis when:
1. GEMINI_API_KEY is unset or unavailable.
2. Network timeouts or rate limits occur.
3. Offline benchmark testing is executed.
"""

import re
from typing import List, Tuple
from src.models import (
    ReviewAnalysis,
    AspectItem,
    CrisisFlag,
    SentimentType,
    CrisisCategory,
    CrisisSeverity,
    BrandVoiceTone,
)

# --- Crisis Trigger Dictionaries ---
CRISIS_PATTERNS = {
    "health_safety": [
        r"\bfood poison(ing)?\b",
        r"\bhospital(ized|ization)?\b",
        r"\bvomit(ing)?\b",
        r"\bgastroenteritis\b",
        r"\brusty nail\b",
        r"\bhealth (code|inspector)\b",
        r"\bmalpractice\b",
        r"\bnerve damage\b",
        r"\binjury\b",
        r"\bemergency room\b",
        r"\bbimar\b",
        r"\bpet kharab\b",
    ],
    "legal_threat": [
        r"\blawyer\b",
        r"\blegal notice\b",
        r"\bconsumer court\b",
        r"\bconsumer protection\b",
        r"\blawsuit\b",
        r"\bsue\b",
        r"\bmedical council\b",
        r"\bpolice\b",
        r"\bconsumer affairs\b",
        r"\bfir\b",
    ],
    "fraud_scam": [
        r"\bscam\b",
        r"\bforg(ed|ery)\b",
        r"\bfinancial fraud\b",
        r"\bunauthorized (charge|fee|transaction)\b",
        r"\bextort(ion)?\b",
        r"\bdouble-charged\b",
        r"\bdhokha\b",
        r"\bchori\b",
    ],
    "discrimination": [
        r"\bdiscriminat(ion|ed|ing)\b",
        r"\bracial slur\b",
        r"\bcaste(ist)?\b",
        r"\bwheelchair\b",
        r"\bdenied entry\b",
        r"\bharrass(ment|ed)?\b",
        r"\bada violation\b",
        r"\bassault(ed)?\b",
        r"\bbadtameez\b",
    ],
    "viral_reputation": [
        r"\bviral\b",
        r"\btrending\b",
        r"\bviews on (instagram|twitter|tiktok)\b",
        r"\blocal news\b",
        r"\bfilmed the (entire )?video\b",
        r"\bpress\b",
    ],
}

# --- Aspect Keywords Mapping ---
ASPECT_KEYWORDS = {
    "service": ["service", "wait", "waiting", "delayed", "delay", "queue", "check-in", "checkout", "booking", "appointment", "transit", "valet"],
    "staff": ["staff", "receptionist", "doctor", "surgeon", "manager", "bouncer", "nurse", "barista", "stylist", "attendant", "guard"],
    "price": ["price", "cost", "expensive", "overpriced", "fee", "bill", "billing", "charges", "charged", "rates", "inr"],
    "cleanliness": ["clean", "cleanliness", "dirty", "filthy", "stained", "dusty", "hygiene", "sterilized", "sanitization", "smell", "restroom"],
    "delivery": ["delivery", "dispatch", "shipping", "shipped", "tracking", "order", "packaging"],
    "quality": ["quality", "taste", "food", "soup", "coffee", "roti", "dish", "fabric", "stitching", "apparel", "cotton", "pasta"],
    "ambiance": ["ambiance", "atmosphere", "music", "view", "rooftop", "courtyard", "seating", "nook"],
}

# Lexicons
POSITIVE_WORDS = {
    "exceptional", "immaculate", "lavish", "warmly", "painless", "recommended",
    "perfection", "friendly", "delightful", "helpful", "wonderful", "flawless",
    "impressive", "speedy", "exquisite", "decent", "compassionate", "delicious",
    "best", "peaceful", "great", "quiet", "pleasant", "comfortable", "modern",
    "high quality", "attentive", "courteous", "proud", "love", "loved", "spotless", "stunning"
}

NEGATIVE_WORDS = {
    "poisoning", "hospitalized", "rusty", "violation", "refund", "scam",
    "unconsented", "malpractice", "discrimination", "slurs", "fraud",
    "assault", "lukewarm", "stale", "tore", "disorganized", "rude", "scratched",
    "malfunctioning", "overpriced", "ignored", "neglected", "burnt", "bitter",
    "stained", "dusty", "misleading", "cumbersome", "slow", "filthy", "cloudy", "awful", "terrible", "poor"
}

SARCASM_SIGNALS = [
    r"oh wonderful",
    r"truly five-star efficiency",
    r"what world-class hospitality",
    r"masterclass in fast fashion disguised",
    r"fantastic ambiance if you enjoy deafening",
]


def detect_crisis(text: str) -> CrisisFlag:
    """Evaluates text against high-risk operational and legal regex rules."""
    text_lower = text.lower()

    for category, patterns in CRISIS_PATTERNS.items():
        for pat in patterns:
            match = re.search(pat, text_lower)
            if match:
                matched_term = match.group(0)
                reason = f"Detected high-risk crisis indicator '{matched_term}' under category {category}."
                if category in ["health_safety", "legal_threat", "fraud_scam", "discrimination", "viral_reputation"]:
                    severity: CrisisSeverity = "high"
                else:
                    severity: CrisisSeverity = "medium"

                actions = {
                    "health_safety": "Halt suspected lots, brief safety officer, and provide direct manager escalation phone line.",
                    "legal_threat": "Notify legal counsel and preserve incident logs; do not admit fault in public reply.",
                    "fraud_scam": "Initiate urgent audit with accounts desk and reach out via phone.",
                    "discrimination": "Escalate to HR and executive management; initiate staff inquiry immediately.",
                    "viral_reputation": "Alert PR / communications lead and monitor social channels.",
                }

                return CrisisFlag(
                    is_crisis=True,
                    category=category,  # type: ignore
                    severity=severity,
                    reason=reason,
                    recommended_action=actions.get(category, "Urgent management intervention required."),
                )

    # Moderate severity checks
    if any(term in text_lower for term in ["scratched", "damaged", "missed train"]):
        return CrisisFlag(
            is_crisis=False,
            category="none",
            severity="medium",
            reason="Operational property damage or severe customer inconvenience.",
            recommended_action="Contact customer for private resolution.",
        )

    return CrisisFlag(
        is_crisis=False,
        category="none",
        severity="low",
        reason="Standard customer feedback without legal or health escalations.",
        recommended_action="Follow standard brand response workflow.",
    )


def extract_aspects(text: str) -> List[AspectItem]:
    """Extracts operational aspects and calculates localized sentiment."""
    text_lower = text.lower()
    extracted: List[AspectItem] = []

    for aspect, keywords in ASPECT_KEYWORDS.items():
        for kw in keywords:
            idx = text_lower.find(kw)
            if idx != -1:
                # Extract sentence window around keyword
                start = max(0, idx - 40)
                end = min(len(text), idx + 60)
                snippet = text[start:end].strip()

                # Localized sentiment heuristic
                pos_hits = sum(1 for w in POSITIVE_WORDS if w in snippet.lower())
                neg_hits = sum(1 for w in NEGATIVE_WORDS if w in snippet.lower())
                
                # Check sarcasm
                if any(re.search(p, text_lower) for p in SARCASM_SIGNALS):
                    aspect_sentiment: SentimentType = "negative"
                elif neg_hits > pos_hits:
                    aspect_sentiment = "negative"
                elif pos_hits > neg_hits:
                    aspect_sentiment = "positive"
                else:
                    aspect_sentiment = "neutral"

                extracted.append(AspectItem(
                    aspect=aspect,
                    sentiment=aspect_sentiment,
                    evidence=f"...{snippet}..."
                ))
                break  # Record aspect once

    return extracted


def analyze_sentiment(text: str) -> Tuple[SentimentType, float]:
    """Determines dominant overall sentiment with confidence estimate."""
    text_lower = text.lower()

    # Check for sarcasm triggers
    if any(re.search(p, text_lower) for p in SARCASM_SIGNALS):
        return "negative", 0.92

    pos_score = sum(1 for w in POSITIVE_WORDS if re.search(r"\b" + re.escape(w) + r"\b", text_lower))
    neg_score = sum(1 for w in NEGATIVE_WORDS if re.search(r"\b" + re.escape(w) + r"\b", text_lower))

    total = pos_score + neg_score
    if total == 0:
        return "neutral", 0.70

    if neg_score > pos_score:
        confidence = min(0.98, 0.65 + (neg_score / (total + 1)) * 0.35)
        return "negative", round(confidence, 2)
    elif pos_score > neg_score:
        confidence = min(0.98, 0.65 + (pos_score / (total + 1)) * 0.35)
        return "positive", round(confidence, 2)
    else:
        return "neutral", 0.75


def generate_fallback_reply(
    sentiment: SentimentType,
    crisis: CrisisFlag,
    aspects: List[AspectItem],
    brand_tone: BrandVoiceTone = "professional",
) -> str:
    """Generates guardrailed reply based on brand tone and crisis status."""
    if crisis.is_crisis:
        if brand_tone == "warm":
            return (
                "We are deeply concerned to read this and treat this matter with the highest seriousness. "
                "The health, safety, and comfort of every guest are paramount to our team. "
                "We would be grateful if you could connect directly with our management at "
                "escalations@cynbit-client.com so our leadership team can personally investigate and assist you."
            )
        elif brand_tone == "concise":
            return (
                "We take this report very seriously. Please contact our leadership directly at "
                "escalations@cynbit-client.com or call our office so we can investigate immediately."
            )
        else:  # professional
            return (
                "We acknowledge your feedback and treat these matters with absolute priority. "
                "To ensure a thorough and prompt investigation by senior management, please contact our "
                "escalation team directly at escalations@cynbit-client.com with your contact details."
            )

    aspect_names = [a.aspect for a in aspects]
    aspect_str = f" regarding our {', '.join(aspect_names[:2])}" if aspect_names else ""

    if sentiment == "positive":
        if brand_tone == "warm":
            return (
                f"Thank you so much for your wonderful words{aspect_str}! "
                "Our team is overjoyed to know you had such a lovely experience with us. "
                "We look forward to welcoming you back very soon!"
            )
        elif brand_tone == "concise":
            return f"Thank you for the fantastic review{aspect_str}! We appreciate your support and look forward to serving you again."
        else:  # professional
            return (
                f"Thank you for sharing your positive feedback{aspect_str}. "
                "We are pleased to hear our standards met your expectations and look forward to your next visit."
            )
    elif sentiment == "negative":
        if brand_tone == "warm":
            return (
                f"We are genuinely sorry that your experience{aspect_str} fell short of what you deserved. "
                "We take great pride in our service, and your feedback has been shared with our operations lead "
                "to ensure immediate improvements."
            )
        elif brand_tone == "concise":
            return (
                f"Thank you for bringing this to our attention. We apologize for the issues{aspect_str} "
                "and are reviewing this with our team to prevent recurrence."
            )
        else:  # professional
            return (
                f"Thank you for providing your candid feedback regarding your experience{aspect_str}. "
                "We hold ourselves to high service standards and sincerely regret falling short. "
                "Our management team is actively addressing these points with our staff."
            )
    else:  # neutral
        if brand_tone == "warm":
            return (
                "Thank you for taking the time to review us. We appreciate your balanced feedback "
                "and are always working hard to make your next experience even better."
            )
        elif brand_tone == "concise":
            return "Thank you for your feedback. We appreciate your insights as we continue refining our services."
        else:
            return (
                "Thank you for sharing your feedback. We value your input and will use it to continuously "
                "improve our service quality and operational standards."
            )


def run_offline_analysis(
    review_text: str,
    brand_tone: BrandVoiceTone = "professional",
    location: str = "General",
    rating: int = None,
    review_id: str = None,
    date: str = None,
) -> ReviewAnalysis:
    """Executes end-to-end analysis using offline rule-based heuristics."""
    sentiment, confidence = analyze_sentiment(review_text)
    crisis = detect_crisis(review_text)
    aspects = extract_aspects(review_text)
    reply = generate_fallback_reply(sentiment, crisis, aspects, brand_tone)

    return ReviewAnalysis(
        review_id=review_id,
        review_text=review_text,
        overall_sentiment=sentiment,
        sentiment_confidence=confidence,
        aspects=aspects,
        crisis=crisis,
        draft_reply=reply,
        brand_tone=brand_tone,
        engine_used="offline-fallback",
        approval_status="pending",
        location=location,
        rating=rating,
        date=date,
    )

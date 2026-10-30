"""Synthetic review dataset generator for Cynbit Revio Review Intelligence Engine.

Generates realistic SMB customer reviews reflecting typical Cynbit clients:
- Hospitality & Dining (Boutique Hotel & Bistro)
- Healthcare & Wellness (Dental & Wellness Clinic)
- Retail & Creative (Apparel & Design Studio)

Includes explicit edge cases:
- Sarcasm and mixed-sentiment feedback
- Multi-location data (Jaipur HQ, Jaipur West, Delhi NCR, Mumbai)
- Crisis situations (food safety, discrimination, legal threats, billing fraud)
"""

import csv
import os
from typing import List, Dict, Any

# 75 Synthetic Reviews for general dashboard and demonstration
REVIEWS_DATA: List[Dict[str, Any]] = [
    # --- Crisis: Health & Safety / Food Poisoning ---
    {
        "review_id": "REV-001",
        "review_text": "Severe food poisoning after eating the seafood platter yesterday! Three of us were hospitalized with acute gastroenteritis. Calling the municipal food health inspector immediately.",
        "rating": 1,
        "location": "Jaipur HQ",
        "date": "2026-10-24",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-002",
        "review_text": "Found a rusty nail embedded inside the bread basket at the rooftop diner. Manager just laughed it off! Absolute health code violation.",
        "rating": 1,
        "location": "Jaipur West",
        "date": "2026-10-25",
        "business_type": "Hospitality & Dining"
    },
    # --- Crisis: Legal Threats & Consumer Court ---
    {
        "review_id": "REV-003",
        "review_text": "You charged my credit card three times for an unconfirmed booking and refuse to refund. My lawyer is serving a legal notice to your registered Jaipur address on Monday under consumer protection laws.",
        "rating": 1,
        "location": "Jaipur HQ",
        "date": "2026-10-26",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-004",
        "review_text": "This dental clinic performed an unconsented procedure that caused nerve damage. Filing a medical malpractice lawsuit and reporting Dr. Sharma to the medical council.",
        "rating": 1,
        "location": "Delhi NCR",
        "date": "2026-10-27",
        "business_type": "Healthcare & Wellness"
    },
    # --- Crisis: Discrimination & Harassment ---
    {
        "review_id": "REV-005",
        "review_text": "Front desk staff explicitly denied entry to my wheelchair-bound cousin, claiming 'it ruins the aesthetic'. Pure discrimination and ADA violation.",
        "rating": 1,
        "location": "Mumbai",
        "date": "2026-10-28",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-006",
        "review_text": "The security guard made derogatory casteist slurs when we asked for directions. Management did nothing when we protested.",
        "rating": 1,
        "location": "Jaipur West",
        "date": "2026-10-29",
        "business_type": "Retail & Creative"
    },
    # --- Crisis: Fraud & Billing Scams ---
    {
        "review_id": "REV-007",
        "review_text": "Complete scam! They charged hidden fees amounting to 40% over the agreed estimate and forged my signature on the work receipt. Total financial fraud.",
        "rating": 1,
        "location": "Delhi NCR",
        "date": "2026-10-22",
        "business_type": "Retail & Creative"
    },
    # --- Crisis: Viral Reputation Risk ---
    {
        "review_id": "REV-008",
        "review_text": "I recorded the bouncer pushing an elderly guest down the front steps. Video has already hit 200k views on Instagram and Twitter. Local news has reached out.",
        "rating": 1,
        "location": "Mumbai",
        "date": "2026-10-23",
        "business_type": "Hospitality & Dining"
    },
    # --- Sarcasm & Mixed Sentiment Edge Cases ---
    {
        "review_id": "REV-009",
        "review_text": "Oh wonderful, 50 minutes of waiting just to get lukewarm soup and stale bread. Truly five-star efficiency from your kitchen team!",
        "rating": 2,
        "location": "Jaipur HQ",
        "date": "2026-10-20",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-010",
        "review_text": "Fantastic ambiance if you enjoy deafening club music while trying to consult a dentist. Ear plugs should be included in the bill.",
        "rating": 2,
        "location": "Delhi NCR",
        "date": "2026-10-18",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-011",
        "review_text": "Loved paying premium bespoke designer rates for shirts that tore on the very first dry clean. Absolute masterclass in fast fashion disguised as couture.",
        "rating": 2,
        "location": "Mumbai",
        "date": "2026-10-19",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-012",
        "review_text": "The doctor was compassionate and clinical care was top notch, but the front desk billing was disorganized, rude, and took 45 minutes to produce an invoice.",
        "rating": 3,
        "location": "Jaipur West",
        "date": "2026-10-21",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-013",
        "review_text": "Stunning heritage courtyard and delicious cocktails, yet the valet parking team scratched our car door and shrugged it off without an apology.",
        "rating": 3,
        "location": "Jaipur HQ",
        "date": "2026-10-17",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-014",
        "review_text": "Great fabrics and prompt tailoring delivery, but prices feel 30% higher than comparable boutiques in C-Scheme.",
        "rating": 3,
        "location": "Jaipur West",
        "date": "2026-10-16",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-015",
        "review_text": "Clean facilities and polite nurses. However, appointment was delayed by over an hour with zero prior notification.",
        "rating": 3,
        "location": "Delhi NCR",
        "date": "2026-10-15",
        "business_type": "Healthcare & Wellness"
    },
    # --- Positive Reviews across aspects ---
    {
        "review_id": "REV-016",
        "review_text": "Exceptional stay! The housekeeping team kept the room immaculate, breakfast spread was lavish, and staff greeted us warmly by name.",
        "rating": 5,
        "location": "Jaipur HQ",
        "date": "2026-10-22",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-017",
        "review_text": "Dr. Verma took time to explain each step of the root canal painless procedure. Transparent pricing with no surprise charges. Highly recommended!",
        "rating": 5,
        "location": "Jaipur West",
        "date": "2026-10-23",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-018",
        "review_text": "Handcrafted wedding sherwani tailored to perfection! Fitting was spot on on the first trial and delivery arrived two days early.",
        "rating": 5,
        "location": "Delhi NCR",
        "date": "2026-10-24",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-019",
        "review_text": "Best cold brew and sourdough sandwiches in Bandra. Fast Wi-Fi, friendly baristas, and reasonable pricing for the quality offered.",
        "rating": 5,
        "location": "Mumbai",
        "date": "2026-10-25",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-020",
        "review_text": "The entire boutique experience was delightful. Attentive stylists, curated collection, and very reasonable customization charges.",
        "rating": 5,
        "location": "Jaipur HQ",
        "date": "2026-10-26",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-021",
        "review_text": "Prompt online consultation, medication was delivered within 3 hours, and customer support was very helpful throughout.",
        "rating": 5,
        "location": "Delhi NCR",
        "date": "2026-10-27",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-022",
        "review_text": "Consistently great coffee and peaceful study nook. Staff always remembers my usual order with a smile.",
        "rating": 5,
        "location": "Mumbai",
        "date": "2026-10-28",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-023",
        "review_text": "Wonderful heritage ambiance for an anniversary dinner. Flawless live classical music and courteous table attendants.",
        "rating": 5,
        "location": "Jaipur HQ",
        "date": "2026-10-29",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-024",
        "review_text": "The hygiene standards are truly impressive. Sterilized dental equipment unsealed in front of patient. Puts one at complete ease.",
        "rating": 5,
        "location": "Jaipur West",
        "date": "2026-10-29",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-025",
        "review_text": "Speedy delivery, exquisite packaging, and premium cotton feel. Will definitely order festive wear again.",
        "rating": 5,
        "location": "Delhi NCR",
        "date": "2026-10-30",
        "business_type": "Retail & Creative"
    },
    # --- Standard Negative Reviews (Operational, non-crisis) ---
    {
        "review_id": "REV-026",
        "review_text": "Air conditioning was malfunctioning all night in room 304 during peak summer heat. Maintenance took three hours to send a portable fan.",
        "rating": 2,
        "location": "Jaipur HQ",
        "date": "2026-10-14",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-027",
        "review_text": "Overpriced menu for meager portion sizes. A small bowl of pasta cost 650 INR and arrived lukewarm.",
        "rating": 2,
        "location": "Mumbai",
        "date": "2026-10-13",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-028",
        "review_text": "The clinic receptionist was texting on her personal phone and completely ignored patients waiting in queue.",
        "rating": 2,
        "location": "Delhi NCR",
        "date": "2026-10-12",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-029",
        "review_text": "Ordered custom curtains with promised 5-day dispatch; took over 18 days with zero tracking updates provided.",
        "rating": 2,
        "location": "Jaipur West",
        "date": "2026-10-11",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-030",
        "review_text": "Restrooms near the main banquet hall were neglected and lacked hand soap or paper towels.",
        "rating": 2,
        "location": "Jaipur HQ",
        "date": "2026-10-10",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-031",
        "review_text": "Coffee tasted burnt and bitter. Barista refused to remake it and acted defensive.",
        "rating": 1,
        "location": "Mumbai",
        "date": "2026-10-09",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-032",
        "review_text": "Waiting room chairs were stained and dusty. Did not expect this from a private specialty clinic.",
        "rating": 2,
        "location": "Jaipur West",
        "date": "2026-10-08",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-033",
        "review_text": "Sizing charts on their website are completely misleading. The medium dress fits like an XS and returns process is cumbersome.",
        "rating": 2,
        "location": "Delhi NCR",
        "date": "2026-10-07",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-034",
        "review_text": "Slow service during weekday lunch hours. It took 40 minutes for two salads to arrive.",
        "rating": 2,
        "location": "Jaipur HQ",
        "date": "2026-10-06",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-035",
        "review_text": "Staff insisted on cash payment because their card swipe machine was 'down', but refused to issue a printed receipt.",
        "rating": 2,
        "location": "Mumbai",
        "date": "2026-10-05",
        "business_type": "Retail & Creative"
    },
    # --- Neutral / Average Reviews ---
    {
        "review_id": "REV-036",
        "review_text": "Decent hotel room for a brief business transit. Nothing extraordinary, average breakfast, standard amenities.",
        "rating": 3,
        "location": "Jaipur HQ",
        "date": "2026-10-04",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-037",
        "review_text": "Routine teeth cleaning done in 20 minutes. Dentist was fine, price was on par with other neighborhood clinics.",
        "rating": 3,
        "location": "Jaipur West",
        "date": "2026-10-03",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-038",
        "review_text": "Average retail boutique. Standard collection seen in most malls, pricing neither cheap nor exorbitant.",
        "rating": 3,
        "location": "Delhi NCR",
        "date": "2026-10-02",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-039",
        "review_text": "Cappuccino was acceptable, seating is somewhat cramped during rush hours. Might revisit if in the area.",
        "rating": 3,
        "location": "Mumbai",
        "date": "2026-10-01",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-040",
        "review_text": "Standard consultation experience. Waiting time was around 25 minutes, doctor answered basic questions.",
        "rating": 3,
        "location": "Delhi NCR",
        "date": "2026-09-30",
        "business_type": "Healthcare & Wellness"
    },
    # --- More Positive Reviews ---
    {
        "review_id": "REV-041",
        "review_text": "Incredible rooftop view overlooking the city palace lights! Cocktails were masterfully crafted and staff was attentive.",
        "rating": 5,
        "location": "Jaipur HQ",
        "date": "2026-09-29",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-042",
        "review_text": "Brilliant pediatric dental experience! My 6-year-old was completely comfortable thanks to the doctor's gentle approach.",
        "rating": 5,
        "location": "Jaipur West",
        "date": "2026-09-28",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-043",
        "review_text": "High quality linen shirts with meticulous stitching. Store staff offered styling advice without being pushy.",
        "rating": 5,
        "location": "Delhi NCR",
        "date": "2026-09-27",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-044",
        "review_text": "Quiet atmosphere ideal for remote work, delicious almond croissants, and fast courteous service.",
        "rating": 5,
        "location": "Mumbai",
        "date": "2026-09-26",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-045",
        "review_text": "Check-in was seamless. The receptionist even arranged complimentary late checkout for our flight schedule.",
        "rating": 5,
        "location": "Jaipur HQ",
        "date": "2026-09-25",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-046",
        "review_text": "Cleanest clinic I have visited in Jaipur. Modern x-ray tech and very transparent pricing sheet displayed in reception.",
        "rating": 5,
        "location": "Jaipur West",
        "date": "2026-09-24",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-047",
        "review_text": "Custom bridal lehenga was delivered exactly on agreed timeline. Intricate zardozi embroidery matched reference photos.",
        "rating": 5,
        "location": "Delhi NCR",
        "date": "2026-09-23",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-048",
        "review_text": "Affordable daily coffee subscription plan with top-tier single origin beans. The staff makes everyone feel like a regular.",
        "rating": 5,
        "location": "Mumbai",
        "date": "2026-09-22",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-049",
        "review_text": "Spotless room, plush mattress, and quiet air conditioning. Woke up refreshed for our morning business meetings.",
        "rating": 5,
        "location": "Jaipur HQ",
        "date": "2026-09-21",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-050",
        "review_text": "Thorough dental scaling without any discomfort. Highly professional doctors and courteous support staff.",
        "rating": 5,
        "location": "Jaipur West",
        "date": "2026-09-20",
        "business_type": "Healthcare & Wellness"
    },
    # --- Location-specific Operational Insights Reviews ---
    {
        "review_id": "REV-051",
        "review_text": "Valet service at Jaipur HQ took 30 minutes to retrieve our vehicle on Saturday evening, causing us to miss our train.",
        "rating": 1,
        "location": "Jaipur HQ",
        "date": "2026-09-19",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-052",
        "review_text": "Wi-Fi in Jaipur West rooms drops connection every 10 minutes. Unacceptable if you need to work remotely.",
        "rating": 2,
        "location": "Jaipur West",
        "date": "2026-09-18",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-053",
        "review_text": "Billing errors are frequent at the Delhi NCR boutique. They forgot to apply the promotional 20% discount code twice.",
        "rating": 2,
        "location": "Delhi NCR",
        "date": "2026-09-17",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-054",
        "review_text": "Delivery packaging for online orders in Mumbai was damaged, leaving the product box soaked in monsoon rain.",
        "rating": 2,
        "location": "Mumbai",
        "date": "2026-09-16",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-055",
        "review_text": "Cleanliness of swimming pool at Jaipur HQ was disappointing; cloudy water and leaves floating near the drain.",
        "rating": 2,
        "location": "Jaipur HQ",
        "date": "2026-09-15",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-056",
        "review_text": "Courteous dental assistants and quick painless filing. Very reasonable charges.",
        "rating": 4,
        "location": "Jaipur West",
        "date": "2026-09-14",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-057",
        "review_text": "Charming boutique layout in Delhi NCR. Pricing is a bit high, but craftsmanship justifies it.",
        "rating": 4,
        "location": "Delhi NCR",
        "date": "2026-09-13",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-058",
        "review_text": "Good matcha latte and cozy ambiance. Can get noisy on Sunday afternoons.",
        "rating": 4,
        "location": "Mumbai",
        "date": "2026-09-12",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-059",
        "review_text": "Buffet breakfast had extensive South Indian and Continental options. Service was swift.",
        "rating": 4,
        "location": "Jaipur HQ",
        "date": "2026-09-11",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-060",
        "review_text": "Modern clinic setup and digital prescriptions sent on WhatsApp. Easy appointment booking.",
        "rating": 4,
        "location": "Jaipur West",
        "date": "2026-09-10",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-061",
        "review_text": "Loved the bespoke tailoring fit. Only deduction is delivery was one day later than promised.",
        "rating": 4,
        "location": "Delhi NCR",
        "date": "2026-09-09",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-062",
        "review_text": "Great espresso and friendly team. Seating space is somewhat limited.",
        "rating": 4,
        "location": "Mumbai",
        "date": "2026-09-08",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-063",
        "review_text": "Room was clean and spacious. Reception staff was pleasant throughout our 3-night stay.",
        "rating": 4,
        "location": "Jaipur HQ",
        "date": "2026-09-07",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-064",
        "review_text": "Efficient dental hygiene checkup. Clinic followed proper sanitization protocols.",
        "rating": 4,
        "location": "Jaipur West",
        "date": "2026-09-06",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-065",
        "review_text": "Good collection of ethnic kurtas. Helpful sales associates helped pick sizes.",
        "rating": 4,
        "location": "Delhi NCR",
        "date": "2026-09-05",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-066",
        "review_text": "Smooth nitro cold brew and tasty avocado toast. Reliable Wi-Fi.",
        "rating": 4,
        "location": "Mumbai",
        "date": "2026-09-04",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-067",
        "review_text": "Hotel location is central and convenient. Clean sheets and towels provided daily.",
        "rating": 4,
        "location": "Jaipur HQ",
        "date": "2026-09-03",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-068",
        "review_text": "Dr. Gupta explained the orthodontic options clearly with transparent fee estimates.",
        "rating": 4,
        "location": "Jaipur West",
        "date": "2026-09-02",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-069",
        "review_text": "Tailored blazer fit comfortably right off the rack. Fabric quality is solid.",
        "rating": 4,
        "location": "Delhi NCR",
        "date": "2026-09-01",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-070",
        "review_text": "Cozy cafe ambiance with pleasant jazz music. Good pastry selection.",
        "rating": 4,
        "location": "Mumbai",
        "date": "2026-08-31",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-071",
        "review_text": "Rooftop dinner was memorable. Staff accommodated our dietary gluten-free request gracefully.",
        "rating": 5,
        "location": "Jaipur HQ",
        "date": "2026-08-30",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-072",
        "review_text": "Emergency toothache treated promptly on a Sunday morning. Very grateful to the on-call doctor.",
        "rating": 5,
        "location": "Jaipur West",
        "date": "2026-08-29",
        "business_type": "Healthcare & Wellness"
    },
    {
        "review_id": "REV-073",
        "review_text": "Prompt international shipping and high-end silk finish. Exceeded expectations.",
        "rating": 5,
        "location": "Delhi NCR",
        "date": "2026-08-28",
        "business_type": "Retail & Creative"
    },
    {
        "review_id": "REV-074",
        "review_text": "Consistent taste across visits. Friendly baristas and clean restrooms.",
        "rating": 5,
        "location": "Mumbai",
        "date": "2026-08-27",
        "business_type": "Hospitality & Dining"
    },
    {
        "review_id": "REV-075",
        "review_text": "Beautiful boutique property with courteous management. Will recommend to colleagues visiting Jaipur.",
        "rating": 5,
        "location": "Jaipur HQ",
        "date": "2026-08-26",
        "business_type": "Hospitality & Dining"
    }
]

# 25 Gold-labeled reviews specifically for the Evaluation Benchmark
LABELED_EVAL_DATA: List[Dict[str, Any]] = [
    {
        "review_id": "EVAL-001",
        "review_text": "Severe food poisoning after dining here! Two guests were rushed to the emergency room with severe vomiting. Filing a complaint with the food safety commissioner.",
        "true_sentiment": "negative",
        "true_aspects": "quality:negative, service:negative",
        "is_crisis": True,
        "crisis_category": "health_safety",
        "crisis_severity": "high",
        "location": "Jaipur HQ"
    },
    {
        "review_id": "EVAL-002",
        "review_text": "They double-charged my debit card and refused to provide an account statement. My legal counsel is sending a consumer court notice today.",
        "true_sentiment": "negative",
        "true_aspects": "price:negative, service:negative",
        "is_crisis": True,
        "crisis_category": "legal_threat",
        "crisis_severity": "high",
        "location": "Delhi NCR"
    },
    {
        "review_id": "EVAL-003",
        "review_text": "Front manager yelled racial slurs at my partner and refused service at the door. Blatant discrimination and harassment.",
        "true_sentiment": "negative",
        "true_aspects": "staff:negative, service:negative",
        "is_crisis": True,
        "crisis_category": "discrimination",
        "crisis_severity": "high",
        "location": "Mumbai"
    },
    {
        "review_id": "EVAL-004",
        "review_text": "Total scam. Charged hidden maintenance fee of 15000 INR not mentioned in quote. Forged invoice receipt.",
        "true_sentiment": "negative",
        "true_aspects": "price:negative",
        "is_crisis": True,
        "crisis_category": "fraud_scam",
        "crisis_severity": "high",
        "location": "Jaipur West"
    },
    {
        "review_id": "EVAL-005",
        "review_text": "Bouncer assaulted a paying customer at entrance. I filmed the entire video and it is already trending on Twitter with 100k views.",
        "true_sentiment": "negative",
        "true_aspects": "staff:negative, service:negative",
        "is_crisis": True,
        "crisis_category": "viral_reputation",
        "crisis_severity": "high",
        "location": "Jaipur HQ"
    },
    {
        "review_id": "EVAL-006",
        "review_text": "Oh fantastic, waiting an hour for cold dal and rubbery roti. What world-class hospitality!",
        "true_sentiment": "negative",
        "true_aspects": "service:negative, quality:negative",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Jaipur HQ"
    },
    {
        "review_id": "EVAL-007",
        "review_text": "The surgeon was skilled and polite, but the clinic reception took 50 minutes to bill and lost my prescription.",
        "true_sentiment": "neutral",
        "true_aspects": "staff:positive, service:negative",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Delhi NCR"
    },
    {
        "review_id": "EVAL-008",
        "review_text": "Loved the handwoven fabric and stylish cuts, but prices are double what other boutiques charge.",
        "true_sentiment": "neutral",
        "true_aspects": "quality:positive, price:negative",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Jaipur West"
    },
    {
        "review_id": "EVAL-009",
        "review_text": "Flawless check-in, spotless suite, and the staff brought complimentary festive sweets to our room. Incredible stay!",
        "true_sentiment": "positive",
        "true_aspects": "service:positive, cleanliness:positive, staff:positive",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Jaipur HQ"
    },
    {
        "review_id": "EVAL-010",
        "review_text": "Painless dental extraction and very clear post-op instructions. Fair pricing.",
        "true_sentiment": "positive",
        "true_aspects": "quality:positive, staff:positive, price:positive",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Jaipur West"
    },
    {
        "review_id": "EVAL-011",
        "review_text": "Wedding sherwani fitting was impeccable and delivered two days ahead of schedule.",
        "true_sentiment": "positive",
        "true_aspects": "quality:positive, delivery:positive",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Delhi NCR"
    },
    {
        "review_id": "EVAL-012",
        "review_text": "Great pour-over coffee and pleasant quiet workspace. Courteous baristas.",
        "true_sentiment": "positive",
        "true_aspects": "quality:positive, staff:positive",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Mumbai"
    },
    {
        "review_id": "EVAL-013",
        "review_text": "Air conditioning unit leaked water on the carpet all night. Receptionist seemed unbothered.",
        "true_sentiment": "negative",
        "true_aspects": "cleanliness:negative, staff:negative",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Jaipur HQ"
    },
    {
        "review_id": "EVAL-014",
        "review_text": "Wait time was 45 minutes past our confirmed booking time with no explanation from staff.",
        "true_sentiment": "negative",
        "true_aspects": "service:negative, staff:negative",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Delhi NCR"
    },
    {
        "review_id": "EVAL-015",
        "review_text": "Stitching unraveled after single wear. Store refused exchange claiming clearance sale policy.",
        "true_sentiment": "negative",
        "true_aspects": "quality:negative, service:negative",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Mumbai"
    },
    {
        "review_id": "EVAL-016",
        "review_text": "Restroom was filthy and had no soap or water. Completely unhygienic.",
        "true_sentiment": "negative",
        "true_aspects": "cleanliness:negative",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Jaipur West"
    },
    {
        "review_id": "EVAL-017",
        "review_text": "Standard hotel stay. Clean bed, ordinary breakfast, nothing to complain or rave about.",
        "true_sentiment": "neutral",
        "true_aspects": "cleanliness:positive, quality:neutral",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Jaipur HQ"
    },
    {
        "review_id": "EVAL-018",
        "review_text": "Routine checkup was satisfactory. Clinic was okay, normal pricing.",
        "true_sentiment": "neutral",
        "true_aspects": "quality:neutral, price:neutral",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Delhi NCR"
    },
    {
        "review_id": "EVAL-019",
        "review_text": "Attentive service and delicious biryani, but dining hall was crowded and noisy.",
        "true_sentiment": "positive",
        "true_aspects": "service:positive, quality:positive",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Jaipur HQ"
    },
    {
        "review_id": "EVAL-020",
        "review_text": "The delivery arrived late by 3 hours, but the packaging kept the food warm and fresh.",
        "true_sentiment": "neutral",
        "true_aspects": "delivery:negative, quality:positive",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Mumbai"
    },
    {
        "review_id": "EVAL-021",
        "review_text": "Doctor was patient, gentle with child scaling, and clinic had sterilized tools sealed in pouches.",
        "true_sentiment": "positive",
        "true_aspects": "staff:positive, cleanliness:positive, quality:positive",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Jaipur West"
    },
    {
        "review_id": "EVAL-022",
        "review_text": "The manager threatened to take my phone away when I tried to record an unhygienic kitchen. Calling consumer affairs and police right now.",
        "true_sentiment": "negative",
        "true_aspects": "staff:negative, cleanliness:negative",
        "is_crisis": True,
        "crisis_category": "legal_threat",
        "crisis_severity": "high",
        "location": "Delhi NCR"
    },
    {
        "review_id": "EVAL-023",
        "review_text": "Fast dispatch, beautiful gift box, and fabric feels luxurious. Highly pleased with purchase.",
        "true_sentiment": "positive",
        "true_aspects": "delivery:positive, quality:positive",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Mumbai"
    },
    {
        "review_id": "EVAL-024",
        "review_text": "Coffee was average, seating is fine. Basic neighborhood cafe.",
        "true_sentiment": "neutral",
        "true_aspects": "quality:neutral",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "low",
        "location": "Mumbai"
    },
    {
        "review_id": "EVAL-025",
        "review_text": "Unprofessional valet driver parked our luxury sedan on muddy curb and scratched alloy wheels. Management refuses to compensate.",
        "true_sentiment": "negative",
        "true_aspects": "service:negative, staff:negative",
        "is_crisis": False,
        "crisis_category": "none",
        "crisis_severity": "medium",
        "location": "Jaipur HQ"
    }
]


def export_csv(file_path: str, data: List[Dict[str, Any]]) -> None:
    """Exports dataset to a clean CSV file."""
    if not data:
        return
    keys = list(data[0].keys())
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"Exported {len(data)} records to: {file_path}")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sample_path = os.path.join(base_dir, "sample_reviews.csv")
    eval_path = os.path.join(base_dir, "labeled_eval_set.csv")
    
    export_csv(sample_path, REVIEWS_DATA)
    export_csv(eval_path, LABELED_EVAL_DATA)
    print("Synthetic datasets generated successfully.")


if __name__ == "__main__":
    main()

"""Evaluation and benchmarking harness for Revio Review Intelligence Engine."""

import csv
import os
import time
from typing import List, Dict, Any
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from src.pipeline import ReviewIntelligencePipeline
from src.models import ReviewAnalysis


def load_evaluation_dataset(csv_path: str = None) -> List[Dict[str, Any]]:
    """Loads gold-standard labeled evaluation dataset."""
    if csv_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(base_dir, "data", "labeled_eval_set.csv")

    records = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Cast boolean
            row["is_crisis"] = str(row.get("is_crisis", "")).strip().lower() in ["true", "1", "yes"]
            records.append(row)
    return records


def run_pipeline_evaluation(
    pipeline: ReviewIntelligencePipeline,
    eval_records: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Runs pipeline on labeled evaluation set and calculates precision, recall, accuracy, and F1."""
    if eval_records is None:
        eval_records = load_evaluation_dataset()

    true_sentiments: List[str] = []
    pred_sentiments: List[str] = []
    true_crisis: List[int] = []
    pred_crisis: List[int] = []
    comparisons: List[Dict[str, Any]] = []

    start_time = time.time()

    for item in eval_records:
        review_text = item["review_text"]
        true_sent = item["true_sentiment"].strip().lower()
        is_crisis_true = int(item["is_crisis"])

        analysis: ReviewAnalysis = pipeline.process_review(
            review_text=review_text,
            brand_tone="professional",
            location=item.get("location", "General"),
            review_id=item.get("review_id"),
        )

        pred_sent = analysis.overall_sentiment.strip().lower()
        is_crisis_pred = 1 if analysis.crisis.is_crisis else 0

        true_sentiments.append(true_sent)
        pred_sentiments.append(pred_sent)
        true_crisis.append(is_crisis_true)
        pred_crisis.append(is_crisis_pred)

        aspects_str = ", ".join([f"{a.aspect}:{a.sentiment}" for a in analysis.aspects]) or "none"

        comparisons.append({
            "review_id": item.get("review_id", ""),
            "review_text": review_text[:80] + ("..." if len(review_text) > 80 else ""),
            "true_sentiment": true_sent,
            "pred_sentiment": pred_sent,
            "sentiment_match": true_sent == pred_sent,
            "true_crisis": bool(is_crisis_true),
            "pred_crisis": bool(is_crisis_pred),
            "crisis_match": is_crisis_true == is_crisis_pred,
            "pred_category": analysis.crisis.category,
            "pred_severity": analysis.crisis.severity,
            "extracted_aspects": aspects_str,
            "draft_reply_sample": analysis.draft_reply[:100] + "...",
        })

    elapsed = time.time() - start_time
    avg_latency_ms = round((elapsed / len(eval_records)) * 1000, 1) if eval_records else 0

    # Calculate metrics using scikit-learn
    labels = ["positive", "neutral", "negative"]
    sentiment_acc = accuracy_score(true_sentiments, pred_sentiments)
    sentiment_macro_f1 = f1_score(true_sentiments, pred_sentiments, labels=labels, average="macro", zero_division=0)
    
    crisis_rec = recall_score(true_crisis, pred_crisis, zero_division=0)
    crisis_prec = precision_score(true_crisis, pred_crisis, zero_division=0)
    crisis_f1 = f1_score(true_crisis, pred_crisis, zero_division=0)

    return {
        "sample_size": len(eval_records),
        "engine_used": "Gemini Flash" if pipeline.is_llm_active else "Offline Fallback",
        "avg_latency_ms": avg_latency_ms,
        "sentiment_accuracy": round(float(sentiment_acc), 3),
        "sentiment_macro_f1": round(float(sentiment_macro_f1), 3),
        "crisis_recall": round(float(crisis_rec), 3),
        "crisis_precision": round(float(crisis_prec), 3),
        "crisis_f1": round(float(crisis_f1), 3),
        "comparisons": comparisons,
    }

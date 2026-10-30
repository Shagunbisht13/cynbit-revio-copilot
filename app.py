"""Revio Copilot — Smart AI Review Assistant & Crisis Guardian for Local Businesses
Developed for Cynbit Technologies (Revio Platform)
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.models import ReviewAnalysis
from src.pipeline import ReviewIntelligencePipeline
from src.insights import aggregate_batch_insights
from src.evaluation import run_pipeline_evaluation

# Page configuration
st.set_page_config(
    page_title="Revio Copilot | Smart AI Review Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling optimized for both Dark & Light Themes
st.markdown("""
<style>
    /* Gradient Brand Header */
    .main-header {
        font-family: 'Inter', -apple-system, sans-serif;
        font-weight: 800;
        font-size: 2.3rem;
        background: linear-gradient(90deg, #38BDF8, #818CF8, #C084FC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #94A3B8;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }
    /* Modern Translucent Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #F8FAFC;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 4px;
    }
    /* Universal Badges */
    .badge-positive {
        background-color: rgba(34, 197, 94, 0.2);
        color: #4ADE80;
        border: 1px solid rgba(74, 222, 128, 0.4);
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .badge-negative {
        background-color: rgba(239, 68, 68, 0.2);
        color: #F87171;
        border: 1px solid rgba(248, 113, 113, 0.4);
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .badge-neutral {
        background-color: rgba(148, 163, 184, 0.2);
        color: #CBD5E1;
        border: 1px solid rgba(203, 213, 225, 0.4);
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    /* Crisis Alert Box */
    .crisis-alert-box {
        background: rgba(225, 29, 72, 0.15);
        border-left: 5px solid #F43F5E;
        border-radius: 8px;
        padding: 16px 20px;
        margin-top: 12px;
        margin-bottom: 16px;
    }
    /* Executive Summary Callout */
    .insights-box {
        background: rgba(59, 130, 246, 0.12);
        border-left: 5px solid #60A5FA;
        border-radius: 8px;
        padding: 18px 22px;
        font-size: 1rem;
        line-height: 1.6;
        color: #E2E8F0;
        margin-bottom: 20px;
    }
    .aspect-chip {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)


# Session state initialization
if "pipeline_cache" not in st.session_state:
    st.session_state.pipeline_cache = {}
if "reviews_df" not in st.session_state:
    st.session_state.reviews_df = None
if "batch_analyses" not in st.session_state:
    st.session_state.batch_analyses = []
if "approval_states" not in st.session_state:
    st.session_state.approval_states = {}
if "eval_results" not in st.session_state:
    st.session_state.eval_results = None
if "review_text_content" not in st.session_state:
    st.session_state.review_text_content = ""


def get_pipeline(force_offline: bool = False) -> ReviewIntelligencePipeline:
    """Returns or caches the pipeline instance."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    cache_key = f"pipeline_offline_{force_offline}_has_key_{bool(api_key)}"
    if cache_key not in st.session_state.pipeline_cache:
        pipeline = ReviewIntelligencePipeline(api_key=api_key, force_fallback=force_offline)
        st.session_state.pipeline_cache[cache_key] = pipeline
    return st.session_state.pipeline_cache[cache_key]


# --- Sidebar Controls ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=56)
    st.title("Revio Copilot")
    st.caption("A Cynbit Technologies Innovation")
    st.markdown("---")

    st.subheader("⚙️ AI Mode")
    force_offline = st.checkbox(
        "Run in Offline Mode",
        value=False,
        help="Check this to run locally using built-in smart rules with zero internet API calls."
    )
    
    pipeline = get_pipeline(force_offline=force_offline)
    
    if pipeline.is_llm_active:
        st.success(f"🟢 **Live Cloud AI**: Gemini Flash (`{pipeline.llm_client.model_name}`)")
    else:
        st.info("🟡 **Offline Smart Rules Active** (Zero API keys required)")

    st.markdown("---")
    st.subheader("🎭 Reply Style (Tone)")
    tone_choice = st.selectbox(
        "How should the reply sound?",
        options=[
            ("professional", "Professional (Polite & Business-like)"),
            ("warm", "Warm (Friendly & Caring)"),
            ("concise", "Concise (Short & Quick)")
        ],
        format_func=lambda x: x[1],
        index=0,
    )
    brand_tone = tone_choice[0]

    st.markdown("---")
    st.subheader("📂 Customer Reviews Data")
    data_source = st.radio(
        "Reviews to use:",
        options=["Bundled Sample (75 real-world reviews)", "Upload Your Own CSV"],
        index=0
    )

    if data_source == "Upload Your Own CSV":
        uploaded_file = st.file_uploader("Upload CSV (must have review_text column)", type=["csv"])
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                if "review_text" not in df.columns:
                    st.error("Uploaded CSV must contain a 'review_text' column.")
                else:
                    st.session_state.reviews_df = df
                    st.success(f"Loaded {len(df)} custom reviews.")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
    else:
        sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_reviews.csv")
        if os.path.exists(sample_path) and st.session_state.reviews_df is None:
            st.session_state.reviews_df = pd.read_csv(sample_path)

    st.markdown("---")
    # Quick statistics in sidebar
    approved_count = sum(1 for v in st.session_state.approval_states.values() if v[0] == "approved")
    edited_count = sum(1 for v in st.session_state.approval_states.values() if v[0] == "edited")
    rejected_count = sum(1 for v in st.session_state.approval_states.values() if v[0] == "rejected")
    
    st.markdown("**Manager Approval Tracker:**")
    st.markdown(f"✅ Approved: `{approved_count}` &nbsp;|&nbsp; ✏️ Edited: `{edited_count}` &nbsp;|&nbsp; ❌ Rejected: `{rejected_count}`")

    if st.session_state.approval_states:
        export_records = []
        for rid, (status, text) in st.session_state.approval_states.items():
            export_records.append({
                "review_id": rid,
                "approval_status": status,
                "approved_or_edited_reply": text
            })
        export_csv_data = pd.DataFrame(export_records).to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Approved Replies (CSV)",
            data=export_csv_data,
            file_name="revio_approved_responses.csv",
            mime="text/csv",
            use_container_width=True
        )


# --- Main Application Header ---
st.markdown('<div class="main-header">🛡️ Revio Copilot</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Smart AI Review Assistant & Crisis Guardian — built for local businesses & multi-location brands.</div>',
    unsafe_allow_html=True
)

tab1, tab2, tab3 = st.tabs([
    "💬 1. Test Any Review",
    "📊 2. Store Dashboard & Insights",
    "🎯 3. AI Accuracy & Tests"
])


# ==============================================================================
# TAB 1: Live Analysis & Human-in-the-Loop
# ==============================================================================
with tab1:
    st.subheader("Test Any Review & Get a Safe Reply")
    st.write("Pick an example review or type your own. The AI checks what customers liked or disliked, spots urgent crises, and drafts a polite reply for you.")

    # Preset mapping
    presets_map = {
        "Choose an example review to test...": "",
        "🚨 Food Safety Crisis: Hospital visit & food poisoning": "Severe food poisoning after eating the seafood platter yesterday! Three of us were hospitalized with acute gastroenteritis. Calling municipal health inspectors.",
        "⚖️ Legal Notice Threat: Triple credit card charge": "You charged my credit card three times and refuse to refund. My lawyer is serving a legal notice to your Jaipur address on Monday under consumer protection laws.",
        "♿ Discrimination: Wheelchair user denied entry": "Front desk staff explicitly denied entry to my wheelchair-bound cousin, claiming it ruins the aesthetic. Pure discrimination.",
        "😏 Sarcastic Review: 'Loved waiting 50 mins for cold soup!'": "Oh wonderful, 50 minutes of waiting just to get lukewarm soup and stale bread. Truly five-star efficiency from your kitchen team!",
        "⚖️ Mixed Review: Great doctor, terrible billing desk": "The doctor was compassionate and clinical care was top notch, but the front desk billing took 45 minutes to produce an invoice.",
        "⭐ 5-Star Praise: Clean rooms, great staff & breakfast": "Exceptional stay! Immaculate rooms, lavish breakfast spread, and staff greeted us warmly by name.",
    }

    def on_preset_selected():
        picked = st.session_state.get("preset_dropdown", "")
        if picked in presets_map and presets_map[picked]:
            st.session_state.review_text_content = presets_map[picked]

    col_input1, col_input2 = st.columns([1, 2])
    with col_input1:
        st.selectbox(
            "📌 Quick Example Scenarios",
            options=list(presets_map.keys()),
            key="preset_dropdown",
            on_change=on_preset_selected
        )
        custom_loc = st.selectbox("Store Location", ["Jaipur HQ", "Jaipur West", "Delhi NCR", "Mumbai", "General"])
        custom_rating = st.slider("Star Rating (Optional)", min_value=1, max_value=5, value=3)

    with col_input2:
        review_input = st.text_area(
            "Customer Review Text",
            value=st.session_state.review_text_content,
            height=130,
            placeholder="Type or paste any customer review here (e.g. from Google Maps, Zomato, TripAdvisor)..."
        )
        analyze_btn = st.button("✨ Analyze Review & Write Reply", type="primary", use_container_width=True)

    if analyze_btn and review_input.strip():
        with st.spinner("AI is reading the review, checking for danger, and drafting a reply..."):
            analysis: ReviewAnalysis = pipeline.process_review(
                review_text=review_input.strip(),
                brand_tone=brand_tone,
                location=custom_loc,
                rating=custom_rating,
                review_id="LIVE-DEMO",
            )
            st.session_state["latest_analysis"] = analysis

    if "latest_analysis" in st.session_state:
        res: ReviewAnalysis = st.session_state["latest_analysis"]

        st.markdown("---")
        st.markdown("### 📋 What the AI Found:")

        # Top Metric Badges
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            sent_label = {"positive": "HAPPY 😊", "neutral": "NEUTRAL 😐", "negative": "UNHAPPY 😡"}.get(res.overall_sentiment, res.overall_sentiment.upper())
            sent_badge = f'<span class="badge-{res.overall_sentiment}">{sent_label} ({int(res.sentiment_confidence*100)}% sure)</span>'
            st.markdown(f"**Customer Sentiment:**<br>{sent_badge}", unsafe_allow_html=True)
            
        with m2:
            crisis_state = "🚨 YES — NEEDS ATTENTION" if res.crisis.is_crisis else "✅ NORMAL FEEDBACK"
            color = "#F43F5E" if res.crisis.is_crisis else "#4ADE80"
            st.markdown(f"**Urgent Crisis?**<br><span style='color:{color}; font-weight:800;'>{crisis_state}</span>", unsafe_allow_html=True)

        with m3:
            severity_label = {"high": "HIGH PRIORITY", "medium": "MEDIUM", "low": "LOW"}.get(res.crisis.severity, "LOW")
            st.markdown(f"**Urgency Level:**<br><span style='color:#F8FAFC; font-weight:700;'>{severity_label}</span>", unsafe_allow_html=True)

        with m4:
            st.markdown(f"**AI Engine Used:**<br><small style='color:#94A3B8;'>{res.engine_used}</small>", unsafe_allow_html=True)

        # Crisis Alert Box if flagged
        if res.crisis.is_crisis:
            st.markdown(f"""
            <div class="crisis-alert-box">
                <h4 style="margin:0 0 6px 0; color:#FDA4AF;">🚨 Urgent Issue: {res.crisis.category.replace('_', ' ').title()}</h4>
                <p style="margin:0 0 6px 0; color:#FEE2E2;"><strong>Why this was flagged:</strong> {res.crisis.reason}</p>
                <p style="margin:0; color:#FEE2E2;"><strong>What you should do:</strong> {res.crisis.recommended_action}</p>
            </div>
            """, unsafe_allow_html=True)

        # Aspect extraction display
        st.markdown("#### 🎯 Specific Topics Mentioned (Aspects):")
        if res.aspects:
            asp_cols = st.columns(min(len(res.aspects), 4))
            for i, asp in enumerate(res.aspects):
                with asp_cols[i % len(asp_cols)]:
                    b_class = f"badge-{asp.sentiment}"
                    st.markdown(f"""
                    <div class="aspect-chip">
                        <strong style="color:#F8FAFC;">{asp.aspect.title()}</strong>: <span class="{b_class}">{asp.sentiment.title()}</span><br>
                        <small style="color:#94A3B8;">"{asp.evidence or 'From review'}"</small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("General feedback — no specific operational areas (like food or pricing) singled out.")

        # Guardrailed Reply Drafting & Human-in-the-Loop Workflow
        st.markdown("#### ✍️ AI-Drafted Reply (Review & Approve):")
        st.caption(f"Tone: **{res.brand_tone.title()}** | Safe: AI will never promise unauthorized refunds or discounts without your approval.")

        current_approval = st.session_state.approval_states.get(res.review_id or "LIVE-DEMO", ("pending", res.draft_reply))
        status, current_text = current_approval

        draft_editor = st.text_area(
            "You can edit the reply below before approving:",
            value=current_text,
            height=120,
            key="draft_editor_box"
        )

        b_col1, b_col2, b_col3, b_col4 = st.columns([1, 1, 1, 2])
        with b_col1:
            if st.button("✅ Approve Reply", use_container_width=True, type="primary"):
                st.session_state.approval_states[res.review_id or "LIVE-DEMO"] = ("approved", draft_editor)
                st.success("Reply approved and marked ready to send!")
                st.rerun()

        with b_col2:
            if st.button("✏️ Save Edits", use_container_width=True):
                st.session_state.approval_states[res.review_id or "LIVE-DEMO"] = ("edited", draft_editor)
                st.info("Your custom edits have been saved.")
                st.rerun()

        with b_col3:
            if st.button("❌ Reject", use_container_width=True):
                st.session_state.approval_states[res.review_id or "LIVE-DEMO"] = ("rejected", draft_editor)
                st.warning("Draft rejected. Flagged for manual phone follow-up.")
                st.rerun()

        with b_col4:
            badge_color = {"pending": "#94A3B8", "approved": "#4ADE80", "edited": "#FBBF24", "rejected": "#F87171"}.get(status, "#94A3B8")
            st.markdown(f"<div style='padding-top:8px;'>Current Status: <b style='color:{badge_color}; text-transform:uppercase;'>{status}</b></div>", unsafe_allow_html=True)


# ==============================================================================
# TAB 2: Batch Operations & Multi-Location Dashboard
# ==============================================================================
with tab2:
    st.subheader("Business Owner Dashboard: All Store Locations")
    st.write("Track customer happiness across all your branches, spot recurring complaints, and read your automated weekly executive summary.")

    df = st.session_state.reviews_df

    if df is not None and not df.empty:
        col_ctrl1, col_ctrl2 = st.columns([3, 1])
        with col_ctrl1:
            st.write(f"Currently analyzing **{len(df)} customer reviews** across: *{', '.join(df['location'].dropna().unique())}*.")
        with col_ctrl2:
            process_batch_btn = st.button("⚡ Run Full Business Analysis", type="primary", use_container_width=True)

        if process_batch_btn or not st.session_state.batch_analyses:
            with st.spinner("Analyzing all reviews across branches..."):
                records = df.to_dict(orient="records")
                analyses = pipeline.process_batch(records, brand_tone=brand_tone)
                st.session_state.batch_analyses = analyses

        if st.session_state.batch_analyses:
            batch_list = st.session_state.batch_analyses
            insights = aggregate_batch_insights(batch_list)

            # Executive Insights Box
            st.markdown("### 📢 AI Weekly Summary for the Owner")
            st.markdown(f"""
            <div class="insights-box">
                {insights.executive_summary}
            </div>
            """, unsafe_allow_html=True)

            # High Level Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{insights.total_reviews}</div>
                    <div class="metric-label">Total Reviews Analyzed</div>
                </div>
                """, unsafe_allow_html=True)
            with m2:
                pos_count = insights.sentiment_counts.get("positive", 0)
                pos_pct = round((pos_count / insights.total_reviews) * 100, 1)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:#4ADE80;">{pos_pct}%</div>
                    <div class="metric-label">Happy Customers</div>
                </div>
                """, unsafe_allow_html=True)
            with m3:
                neg_count = insights.sentiment_counts.get("negative", 0)
                neg_pct = round((neg_count / insights.total_reviews) * 100, 1)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:#F87171;">{neg_pct}%</div>
                    <div class="metric-label">Unhappy Customers</div>
                </div>
                """, unsafe_allow_html=True)
            with m4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:#F43F5E;">{insights.crisis_count}</div>
                    <div class="metric-label">Urgent Issues Flagged</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Charts Row
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.markdown("#### Overall Customer Mood")
                sent_df = pd.DataFrame({
                    "Mood": ["Happy", "Neutral", "Unhappy"],
                    "Reviews": [
                        insights.sentiment_counts.get("positive", 0),
                        insights.sentiment_counts.get("neutral", 0),
                        insights.sentiment_counts.get("negative", 0)
                    ]
                })
                fig_sent = px.pie(
                    sent_df,
                    names="Mood",
                    values="Reviews",
                    color="Mood",
                    color_discrete_map={"Happy": "#22C55E", "Neutral": "#94A3B8", "Unhappy": "#EF4444"},
                    hole=0.45
                )
                fig_sent.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_sent, use_container_width=True)

            with chart_col2:
                st.markdown("#### Top Customer Complaints")
                if insights.top_negative_aspects:
                    aspect_df = pd.DataFrame(insights.top_negative_aspects, columns=["Area", "Complaints"])
                    aspect_df["Area"] = aspect_df["Area"].str.title()
                    fig_asp = px.bar(
                        aspect_df,
                        x="Complaints",
                        y="Area",
                        orientation="h",
                        color="Complaints",
                        color_continuous_scale="Reds"
                    )
                    fig_asp.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_asp, use_container_width=True)
                else:
                    st.info("No complaints found.")

            # Multi-Location Breakdown Table
            st.markdown("#### 🏢 Branch-by-Branch Comparison")
            loc_rows = []
            for loc, data in insights.location_breakdown.items():
                loc_rows.append({
                    "Store Location": loc,
                    "Total Reviews": data["total"],
                    "Happy Reviews": data["positive_count"],
                    "Unhappy Reviews": data["negative_count"],
                    "Complaint Rate": f"{data['negative_rate']}%",
                    "Urgent Issues": data["crisis_count"],
                    "Main Friction Point": data["primary_bottleneck"].title(),
                })
            st.dataframe(pd.DataFrame(loc_rows), use_container_width=True, hide_index=True)

            # Triage Table of Flagged Crisis Reviews
            st.markdown("#### 🚨 Urgent Reviews Requiring Manager Attention")
            crisis_items = [a for a in batch_list if a.crisis.is_crisis]
            if crisis_items:
                crisis_rows = []
                for c in crisis_items:
                    crisis_rows.append({
                        "ID": c.review_id or "N/A",
                        "Location": c.location or "General",
                        "Risk Type": c.crisis.category.replace('_', ' ').upper(),
                        "Urgency": c.crisis.severity.upper(),
                        "Review Text": c.review_text[:110] + ("..." if len(c.review_text) > 110 else ""),
                        "Why Flagged": c.crisis.reason,
                        "Recommended Action": c.crisis.recommended_action,
                    })
                st.dataframe(pd.DataFrame(crisis_rows), use_container_width=True, hide_index=True)
            else:
                st.success("No urgent complaints right now. All reviews are standard feedback.")
    else:
        st.warning("No review dataset currently loaded. Please load the bundled dataset from the sidebar or upload a CSV.")


# ==============================================================================
# TAB 3: Model Benchmark & Evaluation
# ==============================================================================
with tab3:
    st.subheader("AI Accuracy & Quality Scores")
    st.write(
        "Here we test the AI against a benchmark dataset of 25 reviews where human experts already labeled the true sentiment and crises. "
        "This proves how well the AI performs on real-world tricky reviews (including sarcasm and mixed opinions)."
    )

    eval_col1, eval_col2 = st.columns([3, 1])
    with eval_col1:
        st.info("Benchmark contains 25 verified reviews with subtle sarcasm, mixed opinions, and legal/health crises.")
    with eval_col2:
        run_eval_btn = st.button("🧪 Run Accuracy Test", type="primary", use_container_width=True)

    if run_eval_btn or st.session_state.eval_results is None:
        with st.spinner("Testing AI accuracy against expert-labeled reviews..."):
            eval_metrics = run_pipeline_evaluation(pipeline)
            st.session_state.eval_results = eval_metrics

    if st.session_state.eval_results:
        metrics = st.session_state.eval_results

        # Top Evaluation Metrics Cards
        em1, em2, em3, em4, em5 = st.columns(5)
        with em1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:#38BDF8;">{metrics['sentiment_accuracy']*100:.1f}%</div>
                <div class="metric-label">Overall Accuracy</div>
            </div>
            """, unsafe_allow_html=True)
        with em2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:#A78BFA;">{metrics['sentiment_macro_f1']:.3f}</div>
                <div class="metric-label">Mood F1 Score</div>
            </div>
            """, unsafe_allow_html=True)
        with em3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:#F43F5E;">{metrics['crisis_recall']*100:.1f}%</div>
                <div class="metric-label">Crisis Catch Rate</div>
            </div>
            """, unsafe_allow_html=True)
        with em4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:#FBBF24;">{metrics['crisis_precision']*100:.1f}%</div>
                <div class="metric-label">Crisis Precision</div>
            </div>
            """, unsafe_allow_html=True)
        with em5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics['avg_latency_ms']} ms</div>
                <div class="metric-label">Speed per Review</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"**Test Details:** AI Engine Tested: `{metrics['engine_used']}` | Total Test Cases: `{metrics['sample_size']} reviews`")

        # Side-by-side comparison table
        st.markdown("#### 🔬 Review-by-Review Predictions vs Expert Labels")
        comp_df = pd.DataFrame(metrics["comparisons"])
        
        st.dataframe(
            comp_df[[
                "review_id",
                "review_text",
                "true_sentiment",
                "pred_sentiment",
                "sentiment_match",
                "true_crisis",
                "pred_crisis",
                "crisis_match",
                "pred_category",
                "pred_severity",
                "extracted_aspects",
            ]],
            use_container_width=True,
            hide_index=True
        )


# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#94A3B8; font-size:0.85rem;">
    Revio Copilot — Smart AI Review Assistant & Crisis Guardian | Cynbit Technologies | Built for SMB Growth
</div>
""", unsafe_allow_html=True)

"""Cynbit Revio - Review Intelligence Engine (PoC)
Enterprise AI Reputation Management & Aspect Sentiment Platform
"""

import os
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.models import ReviewAnalysis, ApprovalStatus
from src.pipeline import ReviewIntelligencePipeline
from src.insights import aggregate_batch_insights
from src.evaluation import run_pipeline_evaluation, load_evaluation_dataset

# Page configuration
st.set_page_config(
    page_title="Revio | Review Intelligence Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for enterprise aesthetic
st.markdown("""
<style>
    .main-header {
        font-family: 'Inter', -apple-system, sans-serif;
        font-weight: 700;
        font-size: 2.2rem;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-positive {
        background-color: #DCFCE7;
        color: #15803D;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-negative {
        background-color: #FEE2E2;
        color: #B91C1C;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-neutral {
        background-color: #F1F5F9;
        color: #475569;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .crisis-alert-box {
        background-color: #FFF1F2;
        border-left: 5px solid #E11D48;
        padding: 14px 18px;
        border-radius: 6px;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    .insights-box {
        background-color: #EFF6FF;
        border-left: 5px solid #3B82F6;
        padding: 16px 20px;
        border-radius: 6px;
        font-size: 0.98rem;
        line-height: 1.6;
        color: #1E3A8A;
        margin-bottom: 20px;
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
    st.session_state.approval_states = {}  # review_id -> (status, edited_text)
if "eval_results" not in st.session_state:
    st.session_state.eval_results = None


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
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=64)
    st.title("Revio Engine")
    st.caption("A Cynbit Technologies Innovation")
    st.markdown("---")

    st.subheader("⚙️ Engine Configuration")
    force_offline = st.checkbox("Force Offline Fallback Mode", value=False, help="Disables LLM calls and utilizes rule-based NLP heuristics.")
    
    pipeline = get_pipeline(force_offline=force_offline)
    
    if pipeline.is_llm_active:
        st.success(f"🟢 **Live Engine**: Gemini Flash (`{pipeline.llm_client.model_name}`)")
    else:
        st.info("🟡 **Deterministic Offline Fallback** (Zero API dependencies)")

    st.markdown("---")
    st.subheader("🎭 Brand Voice Setting")
    brand_tone = st.selectbox(
        "Response Tone",
        options=["professional", "warm", "concise"],
        index=0,
        help="Select brand voice persona for generating automated response drafts."
    )

    st.markdown("---")
    st.subheader("📂 Review Dataset")
    data_source = st.radio(
        "Choose Data Source",
        options=["Bundled Synthetic Dataset (75 reviews)", "Upload Custom CSV"],
        index=0
    )

    if data_source == "Upload Custom CSV":
        uploaded_file = st.file_uploader("Upload CSV (must contain review_text)", type=["csv"])
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
    
    st.markdown(f"**Human Approval Tracker:**")
    st.markdown(f"✅ Approved: `{approved_count}` | ✏️ Edited: `{edited_count}` | ❌ Rejected: `{rejected_count}`")

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
            label="📥 Download Approvals Ledger (CSV)",
            data=export_csv_data,
            file_name="revio_approved_responses.csv",
            mime="text/csv",
            use_container_width=True
        )


# --- Main Application Header ---
st.markdown('<div class="main-header">🛡️ Revio Review Intelligence Engine</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Aspect-Based Sentiment Intelligence, Crisis Triage & Guardrailed Response Drafting for Cynbit SMBs.</div>',
    unsafe_allow_html=True
)

tab1, tab2, tab3 = st.tabs([
    "🔍 Live Analysis & Human-in-the-Loop",
    "📊 Batch Operations & Multi-Location Dashboard",
    "🧪 Model Benchmark & Evaluation"
])


# ==============================================================================
# TAB 1: Live Analysis & Human-in-the-Loop
# ==============================================================================
with tab1:
    st.subheader("Customer Feedback Intelligence Workbench")
    st.write("Analyze individual reviews in real-time, inspect granular aspect breakdown, identify crises, and approve brand-guarded replies.")

    # Input section: preset picker or manual entry
    col_input1, col_input2 = st.columns([1, 2])
    
    preset_reviews = [
        "Select a preset edge-case...",
        "Severe food poisoning after eating the seafood platter yesterday! Three of us were hospitalized with acute gastroenteritis.",
        "You charged my credit card three times and refuse to refund. My lawyer is serving a legal notice to your Jaipur address on Monday.",
        "Front desk staff explicitly denied entry to my wheelchair-bound cousin, claiming it ruins the aesthetic.",
        "Oh wonderful, 50 minutes of waiting just to get lukewarm soup and stale bread. Truly five-star efficiency from your kitchen team!",
        "The doctor was compassionate and clinical care was top notch, but the front desk billing took 45 minutes to produce an invoice.",
        "Exceptional stay! Immaculate rooms, lavish breakfast spread, and staff greeted us warmly by name.",
    ]
    
    with col_input1:
        selected_preset = st.selectbox("Quick-Load Preconfigured Scenarios", preset_reviews)
        custom_loc = st.selectbox("Location", ["Jaipur HQ", "Jaipur West", "Delhi NCR", "Mumbai", "General"])
        custom_rating = st.slider("Star Rating (Optional)", min_value=1, max_value=5, value=3)

    initial_text = ""
    if selected_preset != "Select a preset edge-case...":
        initial_text = selected_preset

    with col_input2:
        review_input = st.text_area(
            "Review Text to Analyze",
            value=initial_text,
            height=140,
            placeholder="Paste raw customer review text here (e.g. Google Maps, TripAdvisor, Yelp)..."
        )
        analyze_btn = st.button("🚀 Run Comprehensive Intelligence Analysis", type="primary")

    if analyze_btn and review_input.strip():
        with st.spinner("Executing aspect extraction, crisis screening, and brand-voice drafting..."):
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
        st.markdown("### 📋 Analysis Breakdown")

        # Top Metric Badges
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            sent_badge = f'<span class="badge-{res.overall_sentiment}">{res.overall_sentiment.upper()} ({int(res.sentiment_confidence*100)}% conf)</span>'
            st.markdown(f"**Overall Sentiment:**<br>{sent_badge}", unsafe_allow_html=True)
            
        with m2:
            crisis_state = "CRISIS DETECTED" if res.crisis.is_crisis else "NORMAL COMPLAINT"
            color = "#E11D48" if res.crisis.is_crisis else "#16A34A"
            st.markdown(f"**Crisis Status:**<br><span style='color:{color}; font-weight:700;'>{crisis_state}</span>", unsafe_allow_html=True)

        with m3:
            st.markdown(f"**Severity Level:**<br><code>{res.crisis.severity.upper()}</code>", unsafe_allow_html=True)

        with m4:
            st.markdown(f"**Engine Used:**<br><small>{res.engine_used}</small>", unsafe_allow_html=True)

        # Crisis Alert Box if flagged
        if res.crisis.is_crisis:
            st.markdown(f"""
            <div class="crisis-alert-box">
                <h4 style="margin:0 0 6px 0; color:#9F1239;">🚨 High-Priority Crisis Flagged: {res.crisis.category.upper()}</h4>
                <p style="margin:0 0 6px 0; color:#881337;"><strong>Trigger Reason:</strong> {res.crisis.reason}</p>
                <p style="margin:0; color:#881337;"><strong>Immediate Recommended Action:</strong> {res.crisis.recommended_action}</p>
            </div>
            """, unsafe_allow_html=True)

        # Aspect extraction display
        st.markdown("#### 🎯 Aspect-Level Sentiment Extraction")
        if res.aspects:
            asp_cols = st.columns(min(len(res.aspects), 4))
            for i, asp in enumerate(res.aspects):
                with asp_cols[i % len(asp_cols)]:
                    b_class = f"badge-{asp.sentiment}"
                    st.markdown(f"""
                    <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:10px; margin-bottom:8px;">
                        <strong>{asp.aspect.title()}</strong>: <span class="{b_class}">{asp.sentiment.upper()}</span><br>
                        <small style="color:#64748B;">Evidence: {asp.evidence or 'Implicit context'}</small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No specific operational aspect keywords isolated.")

        # Guardrailed Reply Drafting & Human-in-the-Loop Workflow
        st.markdown("#### ✍️ Guardrailed Reply Drafting & Human Approval")
        st.caption(f"Configured Tone: **{res.brand_tone.title()}** | Anti-hallucination & no-unauthorized-promise guardrails active.")

        current_approval = st.session_state.approval_states.get(res.review_id or "LIVE-DEMO", ("pending", res.draft_reply))
        status, current_text = current_approval

        draft_editor = st.text_area(
            "Draft Response (Human Supervisor Review)",
            value=current_text,
            height=130,
            key="draft_editor_box"
        )

        b_col1, b_col2, b_col3, b_col4 = st.columns([1, 1, 1, 2])
        with b_col1:
            if st.button("✅ Approve Reply", use_container_width=True):
                st.session_state.approval_states[res.review_id or "LIVE-DEMO"] = ("approved", draft_editor)
                st.success("Draft approved for publication!")
                st.rerun()

        with b_col2:
            if st.button("✏️ Save Edits", use_container_width=True):
                st.session_state.approval_states[res.review_id or "LIVE-DEMO"] = ("edited", draft_editor)
                st.info("Draft updated and saved locally.")
                st.rerun()

        with b_col3:
            if st.button("❌ Reject Draft", use_container_width=True):
                st.session_state.approval_states[res.review_id or "LIVE-DEMO"] = ("rejected", draft_editor)
                st.warning("Draft rejected. Escalated to manual handling.")
                st.rerun()

        with b_col4:
            badge_color = {"pending": "#64748B", "approved": "#16A34A", "edited": "#D97706", "rejected": "#DC2626"}.get(status, "#64748B")
            st.markdown(f"<div style='padding-top:8px;'>Current Status: <b style='color:{badge_color}; text-transform:uppercase;'>{status}</b></div>", unsafe_allow_html=True)


# ==============================================================================
# TAB 2: Batch Operations & Multi-Location Dashboard
# ==============================================================================
with tab2:
    st.subheader("Multi-Location Operational Dashboard")
    st.write("Aggregated review intelligence, automated weekly executive summaries, aspect complaint hot-spots, and crisis triage.")

    df = st.session_state.reviews_df

    if df is not None and not df.empty:
        col_ctrl1, col_ctrl2 = st.columns([2, 1])
        with col_ctrl1:
            st.write(f"Loaded dataset containing **{len(df)}** customer reviews across locations: *{', '.join(df['location'].dropna().unique())}*.")
        with col_ctrl2:
            process_batch_btn = st.button("⚡ Process All Batch Reviews", type="primary")

        if process_batch_btn:
            with st.spinner("Processing batch reviews through intelligence pipeline..."):
                records = df.to_dict(orient="records")
                analyses = pipeline.process_batch(records, brand_tone=brand_tone)
                st.session_state.batch_analyses = analyses
                st.success(f"Successfully processed {len(analyses)} reviews!")

        if st.session_state.batch_analyses:
            batch_list = st.session_state.batch_analyses
            insights = aggregate_batch_insights(batch_list)

            # Executive Insights Box
            st.markdown("### 📢 Auto-Generated Weekly Executive Insights")
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
                    <div class="metric-value" style="color:#16A34A;">{pos_pct}%</div>
                    <div class="metric-label">Positive Sentiment Rate</div>
                </div>
                """, unsafe_allow_html=True)
            with m3:
                neg_count = insights.sentiment_counts.get("negative", 0)
                neg_pct = round((neg_count / insights.total_reviews) * 100, 1)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:#DC2626;">{neg_pct}%</div>
                    <div class="metric-label">Negative Dissatisfaction Rate</div>
                </div>
                """, unsafe_allow_html=True)
            with m4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:#E11D48;">{insights.crisis_count}</div>
                    <div class="metric-label">Urgent Crises Flagged</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Charts Row
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.markdown("#### Overall Sentiment Distribution")
                sent_df = pd.DataFrame({
                    "Sentiment": list(insights.sentiment_counts.keys()),
                    "Count": list(insights.sentiment_counts.values())
                })
                fig_sent = px.pie(
                    sent_df,
                    names="Sentiment",
                    values="Count",
                    color="Sentiment",
                    color_discrete_map={"positive": "#22C55E", "neutral": "#94A3B8", "negative": "#EF4444"},
                    hole=0.45
                )
                fig_sent.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_sent, use_container_width=True)

            with chart_col2:
                st.markdown("#### Top Negative Operational Bottlenecks")
                if insights.top_negative_aspects:
                    aspect_df = pd.DataFrame(insights.top_negative_aspects, columns=["Aspect", "Negative Mentions"])
                    fig_asp = px.bar(
                        aspect_df,
                        x="Negative Mentions",
                        y="Aspect",
                        orientation="h",
                        color="Negative Mentions",
                        color_continuous_scale="Reds"
                    )
                    fig_asp.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_asp, use_container_width=True)
                else:
                    st.info("No negative aspect complaints recorded.")

            # Multi-Location Breakdown Table
            st.markdown("#### 🏢 Multi-Location Operational Comparison")
            loc_rows = []
            for loc, data in insights.location_breakdown.items():
                loc_rows.append({
                    "Location": loc,
                    "Total Volume": data["total"],
                    "Positive": data["positive_count"],
                    "Negative": data["negative_count"],
                    "Dissatisfaction Rate (%)": f"{data['negative_rate']}%",
                    "Urgent Crises": data["crisis_count"],
                    "Primary Friction Aspect": data["primary_bottleneck"].title(),
                })
            st.dataframe(pd.DataFrame(loc_rows), use_container_width=True, hide_index=True)

            # Triage Table of Flagged Crisis Reviews
            st.markdown("#### 🚨 Urgent Crisis Reviews Requiring Escalation")
            crisis_items = [a for a in batch_list if a.crisis.is_crisis]
            if crisis_items:
                crisis_rows = []
                for c in crisis_items:
                    crisis_rows.append({
                        "ID": c.review_id or "N/A",
                        "Location": c.location or "General",
                        "Category": c.crisis.category.upper(),
                        "Severity": c.crisis.severity.upper(),
                        "Review Text": c.review_text[:110] + ("..." if len(c.review_text) > 110 else ""),
                        "Trigger Reason": c.crisis.reason,
                        "Action Plan": c.crisis.recommended_action,
                    })
                st.dataframe(pd.DataFrame(crisis_rows), use_container_width=True, hide_index=True)
            else:
                st.success("No active crisis tickets flagged in current batch.")
    else:
        st.warning("No review dataset currently loaded. Please load the bundled dataset from the sidebar or upload a CSV.")


# ==============================================================================
# TAB 3: Model Benchmark & Evaluation
# ==============================================================================
with tab3:
    st.subheader("Quantitative Model Benchmark & Quality Evaluation")
    st.write(
        "Empirical assessment executed against the curated gold-standard benchmark (`data/labeled_eval_set.csv`). "
        "Evaluates Sentiment Accuracy, Macro F1, and Crisis Recall/Precision across realistic edge cases."
    )

    eval_col1, eval_col2 = st.columns([3, 1])
    with eval_col1:
        st.info("Benchmark contains 25 gold-labeled reviews including high-liability crises, subtle sarcasm, and mixed multi-aspect feedback.")
    with eval_col2:
        run_eval_btn = st.button("🧪 Run Gold Benchmark", type="primary")

    if run_eval_btn or st.session_state.eval_results is None:
        with st.spinner("Running pipeline evaluation over gold benchmark dataset..."):
            eval_metrics = run_pipeline_evaluation(pipeline)
            st.session_state.eval_results = eval_metrics

    if st.session_state.eval_results:
        metrics = st.session_state.eval_results

        # Top Evaluation Metrics Cards
        em1, em2, em3, em4, em5 = st.columns(5)
        with em1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:#2563EB;">{metrics['sentiment_accuracy']*100:.1f}%</div>
                <div class="metric-label">Sentiment Accuracy</div>
            </div>
            """, unsafe_allow_html=True)
        with em2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:#7C3AED;">{metrics['sentiment_macro_f1']:.3f}</div>
                <div class="metric-label">Sentiment Macro F1</div>
            </div>
            """, unsafe_allow_html=True)
        with em3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:#DC2626;">{metrics['crisis_recall']*100:.1f}%</div>
                <div class="metric-label">Crisis Recall</div>
            </div>
            """, unsafe_allow_html=True)
        with em4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:#D97706;">{metrics['crisis_precision']*100:.1f}%</div>
                <div class="metric-label">Crisis Precision</div>
            </div>
            """, unsafe_allow_html=True)
        with em5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics['avg_latency_ms']} ms</div>
                <div class="metric-label">Avg Review Latency</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"**Benchmark Evaluation Details:** Engine Tested: `{metrics['engine_used']}` | Sample Size: `{metrics['sample_size']} reviews`")

        # Side-by-side comparison table
        st.markdown("#### 🔬 Detailed Benchmark Predictions vs Ground Truth")
        comp_df = pd.DataFrame(metrics["comparisons"])
        
        # Format display dataframe
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
    Cynbit Technologies — AI/ML Engineering Technical Assessment | Revio Review Intelligence Engine PoC | Confidential
</div>
""", unsafe_allow_html=True)

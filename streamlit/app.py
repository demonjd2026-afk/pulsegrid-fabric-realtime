import streamlit as st
import anthropic
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime, timezone

# =============================================================================
# Page Config
# =============================================================================
st.set_page_config(
    page_title="PulseGrid — Energy Market AI Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# Custom CSS
# =============================================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #00B4D8;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #ADB5BD;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #1E2130;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #00B4D8;
    }
    .spike-alert {
        background: #2D1B1B;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #FF4444;
    }
    .safe-card {
        background: #1B2D1B;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #44FF44;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Header
# =============================================================================
st.markdown('<div class="main-header">⚡ PulseGrid — Energy Market AI Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real-time electricity market intelligence powered by Claude AI + Microsoft Fabric</div>', unsafe_allow_html=True)

# =============================================================================
# Sidebar — Configuration
# =============================================================================
with st.sidebar:
    st.markdown("# ⚡ PulseGrid")

    # Load from Streamlit Secrets silently
    try:
        anthropic_key = st.secrets["ANTHROPIC_API_KEY"]
        fabric_token  = st.secrets["FABRIC_TOKEN"]
        workspace_id  = st.secrets["WORKSPACE_ID"]
        lakehouse_id  = st.secrets["LAKEHOUSE_ID"]
    except:
        anthropic_key = ""
        fabric_token  = ""
        workspace_id  = ""
        lakehouse_id  = ""

    st.divider()
    st.markdown("### 📊 Data Status")

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.success("Cache cleared")

    st.divider()
    st.markdown("### ℹ️ About")
    st.markdown("""
    **PulseGrid AI Agent** queries live Gold Delta tables
    and explains ML predictions using SHAP values.

    Built with:
    - Microsoft Fabric (Lakehouse)
    - XGBoost + MLflow
    - Claude API (Anthropic)
    - Streamlit
    """)

# =============================================================================
# Data Loading — Local JSON files (exported from Fabric Gold tables)
# =============================================================================
@st.cache_data(ttl=300)
def load_gold_table(table_name, *args, **kwargs):
    """Load a Gold table from local JSON file committed to the repo."""
    import os
    # Try multiple path locations for Streamlit Cloud compatibility
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", f"{table_name}.json"),
        os.path.join("/mount/src/pulsegrid-fabric-realtime/streamlit/data", f"{table_name}.json"),
        f"streamlit/data/{table_name}.json",
        f"data/{table_name}.json",
    ]
    for path in candidates:
        try:
            if os.path.exists(path):
                return pd.read_json(path)
        except:
            continue
    return pd.DataFrame()

# =============================================================================
# Main App
# =============================================================================
if not anthropic_key:
    st.info("👈 Enter your Anthropic API key in the sidebar to get started.")
    st.stop()

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=anthropic_key)

# Load data if Fabric credentials provided
df_prices = pd.DataFrame()
df_predictions = pd.DataFrame()
df_shap = pd.DataFrame()
df_generation = pd.DataFrame()

with st.spinner("Loading live data from Fabric..."):
    df_prices      = load_gold_table("gold_price_aggregates",  fabric_token, workspace_id, lakehouse_id)
    df_predictions = load_gold_table("gold_price_predictions",  fabric_token, workspace_id, lakehouse_id)
    df_shap        = load_gold_table("gold_shap_values",        fabric_token, workspace_id, lakehouse_id)
    df_generation  = load_gold_table("gold_generation_summary", fabric_token, workspace_id, lakehouse_id)

# =============================================================================
# Dashboard Metrics
# =============================================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    price_count = len(df_prices) if not df_prices.empty else 0
    st.metric("Price Records", price_count, help="Gold price aggregate records")

with col2:
    pred_count = len(df_predictions) if not df_predictions.empty else 0
    st.metric("Predictions", pred_count, help="XGBoost spike predictions")

with col3:
    spike_count = int(df_predictions["predicted_spike"].sum()) if not df_predictions.empty and "predicted_spike" in df_predictions.columns else 0
    st.metric("Predicted Spikes", spike_count, delta=None)

with col4:
    regions = df_prices["region"].nunique() if not df_prices.empty and "region" in df_prices.columns else 0
    st.metric("Regions Monitored", regions)

st.divider()

# =============================================================================
# AI Agent — Natural Language Interface
# =============================================================================
st.subheader("🤖 Ask the AI Agent")

# Example questions
with st.expander("💡 Example questions"):
    st.markdown("""
    - *"Which region had the highest average price today?"*
    - *"Explain the price spike prediction for DE"*
    - *"What is the renewable generation percentage for FR?"*
    - *"Which regions are predicted to have price spikes?"*
    - *"Compare price trends between EU and US regions"*
    - *"What factors are driving high prices right now?"*
    """)

# Prepare data context for Claude
data_context = ""
if not df_prices.empty:
    data_context += f"\nPrice aggregates sample (first 10 rows):\n{df_prices.head(10).to_string()}\n"
if not df_predictions.empty:
    data_context += f"\nSpike predictions:\n{df_predictions.to_string()}\n"
if not df_shap.empty:
    data_context += f"\nTop SHAP values:\n{df_shap.nlargest(20, 'shap_value').to_string()}\n"
if not df_generation.empty:
    data_context += f"\nGeneration summary:\n{df_generation.head(10).to_string()}\n"

if not data_context:
    data_context = "No live data available. Fabric credentials not provided — answering from general electricity market knowledge."

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask about electricity prices, predictions, or market trends..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analysing market data..."):

            system_prompt = f"""You are PulseGrid, an expert AI agent for electricity market analysis.
You have access to live data from a Microsoft Fabric Medallion Lakehouse with real-time European
and US electricity market data.

Current live data context:
{data_context}

Guidelines:
- Answer questions about electricity prices, generation mix, cross-border flows, and ML predictions
- When explaining spike predictions, reference SHAP values to explain which features contributed most
- Be concise and precise — use numbers from the data when available
- If data is unavailable, answer from general electricity market knowledge
- Format numbers: prices in EUR/MWh, load in MW, percentages with 1 decimal place
- Always mention data freshness when relevant
"""

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
            )

            answer = response.content[0].text
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

st.divider()

# =============================================================================
# Visual Analytics
# =============================================================================
st.subheader("📈 Market Analytics")

tab1, tab2, tab3 = st.tabs(["Price Trends", "Spike Predictions", "Generation Mix"])

with tab1:
    if not df_prices.empty and "avg_price" in df_prices.columns:
        hourly = df_prices[df_prices["granularity"] == "hourly"] if "granularity" in df_prices.columns else df_prices
        if not hourly.empty:
            fig = px.line(
                hourly,
                x="period_start",
                y="avg_price",
                color="region",
                title="Average Electricity Price by Region (Hourly)",
                labels={"avg_price": "Avg Price (EUR/MWh)", "period_start": "Time"}
            )
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No price data available yet — pollers are running on schedule.")

with tab2:
    if not df_predictions.empty:
        fig = px.bar(
            df_predictions,
            x="region",
            y="spike_probability",
            color="predicted_spike",
            title="Spike Probability by Region",
            labels={"spike_probability": "Spike Probability", "region": "Region"},
            color_discrete_map={0: "#00B4D8", 1: "#FF4444"}
        )
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        if not df_shap.empty:
            st.subheader("🔍 Top SHAP Feature Contributions")
            top_shap = df_shap.groupby("feature_name")["shap_value"].apply(
                lambda x: x.abs().mean()
            ).reset_index().sort_values("shap_value", ascending=False).head(10)

            fig2 = px.bar(
                top_shap,
                x="shap_value",
                y="feature_name",
                orientation="h",
                title="Mean |SHAP| by Feature",
                labels={"shap_value": "Mean |SHAP Value|", "feature_name": "Feature"}
            )
            fig2.update_layout(template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No prediction data available yet — ML pipeline runs daily at 02:00 CET.")

with tab3:
    if not df_generation.empty and "renewable_pct" in df_generation.columns:
        gen_avg = df_generation.groupby("region")[["renewable_pct", "nuclear_pct", "fossil_pct"]].mean().reset_index()
        fig = px.bar(
            gen_avg,
            x="region",
            y=["renewable_pct", "nuclear_pct", "fossil_pct"],
            title="Generation Mix by Region (%)",
            labels={"value": "Percentage (%)", "region": "Region"},
            barmode="group"
        )
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No generation data available yet — realtime poller runs every 15 minutes.")

# =============================================================================
# Footer
# =============================================================================
st.divider()
st.markdown("""
<div style="text-align: center; color: #6C757D; font-size: 0.8rem;">
    PulseGrid ⚡ | Built on Microsoft Fabric + Claude AI |
    Data: ENTSO-E · EIA · Visual Crossing |
    ML: XGBoost + MLflow + SHAP
</div>
""", unsafe_allow_html=True)

"""Claude-powered analyst — answers questions against the Gold snapshot."""

import pandas as pd
import streamlit as st

from lib import data as D
from lib import theme as T

MODEL = "claude-sonnet-4-6"

SYSTEM = """You are PulseGrid, an electricity market analyst embedded in a \
Microsoft Fabric medallion lakehouse covering 27 European bidding zones \
(ENTSO-E) and 13 US balancing authorities (EIA).

You have the current market snapshot below. Ground every claim in it.

{context}

How to answer:
- Quote real figures from the snapshot. Prices are EUR/MWh, load is MW, shares are %.
- When explaining a spike prediction, cite the SHAP drivers by name and say which \
direction each pushed the probability. Positive SHAP raises spike likelihood, negative lowers it.
- Bidding zone codes are market areas, not countries: DE-LU is Germany-Luxembourg, \
DK-1/DK-2 are West/East Denmark, SE-3 is southern Sweden, IT-NO is northern Italy.
- If the snapshot does not contain what was asked, say which table would hold it \
and when that table next refreshes. Do not invent numbers.
- Keep answers tight — two or three short paragraphs, or a compact table.
"""

PROMPTS = [
    "Which zones are closest to a price spike right now, and what is driving them?",
    "Compare the highest and lowest priced zones and explain the gap.",
    "How does renewable share line up with price across the reporting zones?",
    "Which features move the spike model most, and what does that tell me?",
]


def _client(key: str):
    import anthropic
    return anthropic.Anthropic(api_key=key)


def _api_key() -> str | None:
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return None


def _coverage(frames: dict[str, pd.DataFrame]) -> None:
    zones = D.latest_zone_prices(frames["gold_price_aggregates"])
    preds = D.latest_predictions(frames["gold_price_predictions"])
    gen   = D.active_generation(frames["gold_generation_summary"])
    shap  = frames["gold_shap_values"]
    stamp, _ = D.freshness(frames)

    T.kpis([
        {"label": "Zones priced", "value": zones["region"].nunique() if not zones.empty else 0,
         "foot": "day-ahead market", "accent": T.AMBER},
        {"label": "Zones scored", "value": len(preds) if not preds.empty else 0,
         "foot": "spike model", "accent": T.FLARE},
        {"label": "Zones generating", "value": len(gen) if not gen.empty else 0,
         "foot": "reporting output", "accent": T.MINT},
        {"label": "Snapshot", "value": stamp.split("·")[0].strip() if stamp != "no data" else "—",
         "foot": "newest record in context", "accent": T.CYAN},
    ])


def render() -> None:
    frames = D.load_all()

    T.section("Ask the analyst", f"CLAUDE · GROUNDED IN THE CURRENT SNAPSHOT")
    _coverage(frames)

    key = _api_key()
    if not key:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        T.empty(
            "Analyst is offline",
            "Add ANTHROPIC_API_KEY under App settings → Secrets to enable questions. "
            "The dashboard works without it.",
        )
        return

    context = D.build_context(frames)

    if "chat" not in st.session_state:
        st.session_state.chat = []

    # Starter prompts — only while the thread is empty.
    if not st.session_state.chat:
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        cols = st.columns(2, gap="small")
        for i, p in enumerate(PROMPTS):
            if cols[i % 2].button(p, key=f"p{i}", use_container_width=True):
                st.session_state.pending = p
                st.rerun()

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    typed = st.chat_input("Ask about prices, spikes, generation, or model drivers")
    question = typed or st.session_state.pop("pending", None)

    if not question:
        return

    st.session_state.chat.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        holder = st.empty()
        try:
            with _client(key).messages.stream(
                model=MODEL,
                max_tokens=1200,
                system=SYSTEM.format(context=context),
                messages=[{"role": m["role"], "content": m["content"]}
                          for m in st.session_state.chat],
            ) as stream:
                buf = ""
                for chunk in stream.text_stream:
                    buf += chunk
                    holder.markdown(buf)
            st.session_state.chat.append({"role": "assistant", "content": buf})
        except Exception as exc:
            holder.error(f"The request did not complete: {exc}")
            st.session_state.chat.pop()

    if st.session_state.chat and st.button("Clear thread"):
        st.session_state.chat = []
        st.rerun()

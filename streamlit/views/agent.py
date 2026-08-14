"""Claude-powered analyst — answers questions against the Gold snapshot."""

import pandas as pd
import streamlit as st

from lib import data as D
from lib import theme as T

MODEL = "claude-sonnet-4-6"

SYSTEM = """You are PulseGrid, an electricity market analyst embedded in a \
Microsoft Fabric medallion lakehouse covering 27 European bidding zones \
(ENTSO-E) and 13 US balancing authorities (EIA).

The current market snapshot follows. Ground every claim in it.

{context}

How to answer:
- Quote real figures from the snapshot. Prices are EUR/MWh, load is MW, shares are %.
- When explaining a spike prediction, name the SHAP drivers and say which direction \
each pushed the probability. Positive SHAP raises spike likelihood, negative lowers it.
- Bidding zone codes are market areas, not countries: DE-LU is Germany-Luxembourg, \
DK-1 and DK-2 are West and East Denmark, SE-3 is southern Sweden, IT-NO is northern Italy.
- If the snapshot does not contain what was asked, say which Gold table would hold it \
and when that table next refreshes. Never invent a number.
- Keep it tight: two or three short paragraphs, or a compact table."""

PROMPTS = [
    "Which zones are closest to a price spike, and what is driving them?",
    "Compare the highest and lowest priced zones and explain the gap.",
    "How does renewable share line up with price across reporting zones?",
    "Which features move the spike model most, and what does that tell me?",
    "Summarise the current state of the European market in five lines.",
    "Which zones look mispriced relative to their generation mix?",
]


def _api_key() -> str | None:
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return None


def render() -> None:
    frames = D.load_all()
    stamp, _ = D.freshness(frames)

    zones = D.latest_zone_prices(frames["gold_price_aggregates"])
    preds = D.latest_predictions(frames["gold_price_predictions"])
    agen = D.active_generation(frames["gold_generation_summary"])
    shap = frames["gold_shap_values"]

    T.hero(
        badge="Claude",
        eyebrow="Natural language analytics",
        title="Market",
        accent="Analyst",
        subtitle="Ask about prices, spike risk, generation mix or model behaviour. "
                 "Answers are grounded in the current Gold snapshot, not in general "
                 "knowledge about energy markets.",
        kind="model",
    )

    T.kpis(
        [
            {"value": zones["region"].nunique() if not zones.empty else 0,
             "label": "Zones priced", "foot": "day-ahead market", "accent": T.AMBER},
            {"value": len(preds) if not preds.empty else 0,
             "label": "Zones scored", "foot": "spike model", "accent": T.CORAL},
            {"value": len(agen) if not agen.empty else 0,
             "label": "Zones generating", "foot": "reporting output", "accent": T.TEAL},
            {"value": f"{len(shap):,}" if not shap.empty else 0,
             "label": "SHAP records", "foot": "in model context", "accent": T.VIOLET},
        ],
        synced=stamp,
    )

    key = _api_key()
    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)

    if not key:
        with st.container(border=True):
            T.panel_header("Analyst offline", "missing credential")
            T.empty(
                "Add an API key to enable questions",
                "Set ANTHROPIC_API_KEY under App settings → Secrets in Streamlit "
                "Cloud. The dashboard works without it.",
            )
        return

    context = D.build_context(frames)
    st.session_state.setdefault("chat", [])

    # Starter prompts, shown only while the thread is empty.
    if not st.session_state.chat:
        with st.container(border=True):
            T.panel_header("Start here", "or type your own below")
            cols = st.columns(3, gap="small")
            for i, p in enumerate(PROMPTS):
                if cols[i % 3].button(p, key=f"p{i}", use_container_width=True):
                    st.session_state.pending = p
                    st.rerun()

    for msg in st.session_state.chat:
        with st.chat_message(msg["role"], avatar="⚡" if msg["role"] == "assistant" else None):
            st.markdown(msg["content"])

    typed = st.chat_input("Ask about prices, spikes, generation or model drivers")
    question = typed or st.session_state.pop("pending", None)

    if question:
        st.session_state.chat.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant", avatar="⚡"):
            holder = st.empty()
            try:
                import anthropic

                client = anthropic.Anthropic(api_key=key)
                with client.messages.stream(
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

    if st.session_state.chat:
        if st.button("Clear conversation"):
            st.session_state.chat = []
            st.rerun()

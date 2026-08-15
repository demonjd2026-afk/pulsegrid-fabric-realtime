"""Claude-powered analyst — a clean, ChatGPT/Claude-style chat over the
Gold snapshot. No branding pill, no marketing hero — this page should read
as a chat app, not a landing section."""

import streamlit as st

from lib import data as D
from lib import theme as T

MODEL = "claude-sonnet-4-6"

SYSTEM = """You are PulseGrid, an electricity market analyst embedded in a \
Microsoft Fabric medallion lakehouse covering European bidding zones (ENTSO-E) \
and US balancing authorities (EIA).

The current market snapshot follows. Ground every claim in it.

{context}

How to answer:
- Quote real figures from the snapshot. Prices are EUR/MWh, load is MW, shares are %.
- When explaining a spike prediction, name the SHAP drivers and say which direction \
each pushed the probability. Positive SHAP raises spike likelihood, negative lowers it.
- Refer to zones by code and name, e.g. "DE-LU (Germany–Luxembourg)". \
DK-1/DK-2 are West/East Denmark, SE-3 is Sweden Central, NO-2 is Norway South, \
IT-NO is Italy North.
- If the snapshot does not contain what was asked, say which Gold table would hold \
it and when that table next refreshes. Never invent a number.
- Keep it tight: two or three short paragraphs, or a compact table."""

PROMPTS = [
    "Zones closest to a price spike?",
    "Highest vs lowest priced zone?",
    "Renewable share vs price today?",
    "Top features driving spikes?",
    "5-line market summary",
    "Explain the riskiest zone's spike",
    "Zones mispriced vs generation?",
]


def _api_key() -> str | None:
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return None


def _stream_reply(key: str, context: str) -> None:
    """Stream the assistant turn for the current thread."""
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


def render() -> None:
    frames = D.load_all()
    stamp, _ = D.freshness(frames)
    loaded = sum(1 for f in frames.values() if not f.empty)

    # Plain heading — no "Claude" badge, no marketing pill. The chat itself
    # already makes clear what this page does.
    T.hero(
        title="Market",
        accent="Analyst",
        subtitle="Ask about prices, spike risk, generation mix or model behaviour. "
                 "Answers cite the live Gold tables, not general knowledge.",
    )

    zones = D.latest_zone_prices(frames["gold_price_aggregates"])
    preds = D.latest_predictions(frames["gold_price_predictions"])
    agen = D.active_generation(frames["gold_generation_summary"])
    shap = frames["gold_shap_values"]

    T.status_line([
        (f'{zones["region"].nunique() if not zones.empty else 0} zones priced', T.SKY),
        (f'{len(preds) if not preds.empty else 0} scored', T.CORAL),
        (f'{len(agen) if not agen.empty else 0} generating', T.TEAL),
        (f'{len(shap):,} SHAP records' if not shap.empty else "0 SHAP records", T.VIOLET),
    ])

    key = _api_key()
    if not key:
        T.empty(
            "Add an API key to enable questions",
            "Set ANTHROPIC_API_KEY under App settings → Secrets in Streamlit "
            "Cloud. The dashboard works without it.",
        )
        T.page_footer(stamp, loaded)
        return

    context = D.build_context(frames)
    st.session_state.setdefault("chat", [])

    # Suggestions stay a narrow rail on the left; the conversation gets the
    # rest of the page — there's no sidebar meta block competing for space
    # anymore, so this is now genuinely wide.
    left, chat = st.columns([1, 3.4], gap="large")

    # Suggestion rail gets a right-hand vertical rule, the way Claude
    # separates its sidebar from the conversation pane, instead of relying
    # on column spacing alone.
    with left:
        with st.container(key="pg_rail"):
            with st.container(key="pg_sugg"):
                st.markdown('<div class="pg-sugg-h">Try asking</div>',
                            unsafe_allow_html=True)
                for i, p in enumerate(PROMPTS):
                    if st.button(p, key=f"sg{i}", use_container_width=True):
                        st.session_state.pending = p
                        st.rerun()

            if st.session_state.chat:
                with st.container(key="pg_clear"):
                    if st.button("Clear conversation"):
                        st.session_state.chat = []
                        st.rerun()

    with chat:
        if not st.session_state.chat:
            st.markdown(
                f'<div style="color:{T.MUTED};font-size:.9rem;padding:.4rem 0 0 2px">'
                f"Pick a question on the left, or type your own below.</div>",
                unsafe_allow_html=True,
            )

        for msg in st.session_state.chat:
            avatar = "⚡" if msg["role"] == "assistant" else None
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        typed = st.chat_input("Ask about prices, spikes, generation or model drivers")
        question = typed or st.session_state.pop("pending", None)

        if question:
            st.session_state.chat.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            _stream_reply(key, context)
            st.rerun()

    T.page_footer(stamp, loaded)

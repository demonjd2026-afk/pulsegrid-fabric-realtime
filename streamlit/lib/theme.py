"""
PulseGrid design system.

Direction: a power exchange terminal. Electricity markets are defined by
violent, short-lived price spikes, so the palette leads with amber (live load)
and coral (spike) against a deep indigo-black, with violet carrying the
model/AI surfaces. Numbers are the content, so every figure is set in tabular
monospace and given room.

All colour and type decisions live here. No other module hardcodes a hex.
"""

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Tokens
# ─────────────────────────────────────────────────────────────────────────────
VOID    = "#080A11"   # page base
PANEL   = "#0F1320"   # card surface
RAISED  = "#171C2C"   # inset surface
LINE    = "#212739"   # hairline border
TEXT    = "#EDF0F7"   # primary text
MUTED   = "#7C86A0"   # secondary text

AMBER   = "#FFB547"   # live load / primary accent
CORAL   = "#FF5C7A"   # spike alert
TEAL    = "#2FD9AC"   # renewable / calm
VIOLET  = "#9B87FF"   # model / AI
BLUE    = "#5B9BFF"   # nuclear / baseload

SERIES = [AMBER, VIOLET, TEAL, BLUE, CORAL, "#F5D08A", "#7FE3FF", "#FF8F6B"]

FONT_DISPLAY = "'Sora', -apple-system, system-ui, sans-serif"
FONT_BODY    = "'Inter', -apple-system, system-ui, sans-serif"
FONT_MONO    = "'JetBrains Mono', 'SF Mono', Menlo, monospace"


# ─────────────────────────────────────────────────────────────────────────────
# Global stylesheet
# ─────────────────────────────────────────────────────────────────────────────
def inject_css() -> None:
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {{
  --void:{VOID}; --panel:{PANEL}; --raised:{RAISED}; --line:{LINE};
  --text:{TEXT}; --muted:{MUTED}; --amber:{AMBER}; --coral:{CORAL};
  --teal:{TEAL}; --violet:{VIOLET}; --blue:{BLUE};
}}

/* ── base ─────────────────────────────────────────────────────────────── */
.stApp {{
  background:
    radial-gradient(1100px 520px at 78% -8%, rgba(155,135,255,.07), transparent 62%),
    radial-gradient(900px 460px at 8% -4%, rgba(255,181,71,.055), transparent 58%),
    {VOID};
}}
.block-container {{ padding-top:2.3rem; padding-bottom:4.5rem; max-width:1560px; }}
html, body, [class*="css"] {{ font-family:{FONT_BODY}; color:{TEXT}; }}
#MainMenu, footer, header {{ visibility:hidden; }}
h1,h2,h3,h4 {{ font-family:{FONT_DISPLAY}; color:{TEXT}; }}

/* ── sidebar ──────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
  background:{PANEL}; border-right:1px solid {LINE};
}}
section[data-testid="stSidebar"] .block-container {{ padding-top:1.9rem; }}

.pg-logo {{ text-align:center; margin-bottom:1.9rem; }}
.pg-logo-mark {{
  width:46px; height:46px; margin:0 auto .7rem auto; border-radius:13px;
  background:linear-gradient(140deg,{AMBER},{CORAL});
  display:flex; align-items:center; justify-content:center;
  font-size:1.4rem; box-shadow:0 6px 22px rgba(255,181,71,.24);
}}
.pg-logo-name {{
  font-family:{FONT_DISPLAY}; font-size:1.22rem; font-weight:700;
  color:{TEXT}; letter-spacing:-.01em; line-height:1.2;
}}
.pg-logo-name em {{ font-style:normal; color:{AMBER}; }}
.pg-logo-sub {{
  font-family:{FONT_MONO}; font-size:.575rem; color:{MUTED};
  letter-spacing:.19em; text-transform:uppercase; margin-top:.32rem;
}}

.pg-meta {{ margin-top:.4rem; }}
.pg-meta-block {{ margin-bottom:1.05rem; }}
.pg-meta-k {{
  font-family:{FONT_MONO}; font-size:.575rem; letter-spacing:.15em;
  text-transform:uppercase; color:{MUTED}; margin-bottom:.28rem;
}}
.pg-meta-v {{ font-size:.795rem; color:{TEXT}; line-height:1.55; }}
.pg-meta-v span {{ color:{MUTED}; }}
.pg-divider {{ height:1px; background:{LINE}; margin:1.35rem 0; }}

/* ── page hero ────────────────────────────────────────────────────────── */
.pg-hero {{ margin-bottom:1.9rem; }}
.pg-eyebrow {{ display:flex; align-items:center; gap:.85rem; margin-bottom:1.05rem; }}
.pg-badge {{
  display:inline-flex; align-items:center; gap:.45rem;
  border:1px solid rgba(47,217,172,.32); background:rgba(47,217,172,.09);
  color:{TEAL}; border-radius:999px; padding:.28rem .78rem;
  font-family:{FONT_MONO}; font-size:.585rem; font-weight:700;
  letter-spacing:.15em; text-transform:uppercase;
}}
.pg-badge.model {{
  border-color:rgba(155,135,255,.32); background:rgba(155,135,255,.09); color:{VIOLET};
}}
.pg-badge.build {{
  border-color:rgba(255,181,71,.30); background:rgba(255,181,71,.08); color:{AMBER};
}}
.pg-dot {{
  width:6px; height:6px; border-radius:50%; background:currentColor;
  animation:pgpulse 2.2s ease-in-out infinite;
}}
@keyframes pgpulse {{ 0%,100%{{opacity:1}} 50%{{opacity:.32}} }}
.pg-eyebrow-text {{
  font-family:{FONT_MONO}; font-size:.615rem; letter-spacing:.19em;
  text-transform:uppercase; color:{MUTED};
}}
.pg-title {{
  font-family:{FONT_DISPLAY}; font-size:2.65rem; font-weight:700;
  letter-spacing:-.025em; line-height:1.08; margin:0 0 .55rem 0; color:{TEXT};
}}
.pg-title em {{
  font-style:normal;
  background:linear-gradient(96deg,{AMBER},{CORAL} 78%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}}
.pg-sub {{ font-size:.955rem; color:{MUTED}; max-width:78ch; line-height:1.62; margin:0; }}

/* ── KPI cards ────────────────────────────────────────────────────────── */
.pg-kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(155px,1fr)); gap:11px; }}
.pg-kpi {{
  background:linear-gradient(168deg,{RAISED} 0%,{PANEL} 100%);
  border:1px solid {LINE}; border-radius:13px; padding:17px 17px 15px 17px;
  position:relative; overflow:hidden;
}}
.pg-kpi::after {{
  content:''; position:absolute; inset:0 0 auto 0; height:2px;
  background:linear-gradient(90deg,var(--a,{AMBER}),transparent 82%);
}}
.pg-kpi-v {{
  font-family:{FONT_MONO}; font-size:2.0rem; font-weight:700; line-height:1;
  color:var(--a,{AMBER}); font-variant-numeric:tabular-nums; letter-spacing:-.02em;
}}
.pg-kpi-v small {{ font-size:.82rem; font-weight:500; color:{MUTED}; margin-left:.24rem; }}
.pg-kpi-k {{
  font-family:{FONT_MONO}; font-size:.575rem; letter-spacing:.155em;
  text-transform:uppercase; color:{MUTED}; margin-top:.62rem;
}}
.pg-kpi-f {{ font-size:.685rem; color:{MUTED}; margin-top:.3rem; opacity:.82; }}
.pg-synced {{
  text-align:right; font-family:{FONT_MONO}; font-size:.615rem;
  color:{MUTED}; letter-spacing:.09em; margin-top:.75rem;
}}
.pg-synced b {{ color:{AMBER}; font-weight:500; }}

/* ── panels (wraps st.container(border=True)) ─────────────────────────── */
div[data-testid="stVerticalBlockBorderWrapper"] {{
  background:{PANEL}; border:1px solid {LINE} !important;
  border-radius:14px; padding:4px 2px;
}}
.pg-ph {{
  display:flex; align-items:baseline; justify-content:space-between;
  gap:1rem; padding:4px 4px 13px 4px; margin-bottom:6px;
  border-bottom:1px solid {LINE};
}}
.pg-ph h3 {{
  font-size:1.0rem; font-weight:600; margin:0; letter-spacing:-.005em; color:{TEXT};
}}
.pg-ph span {{
  font-family:{FONT_MONO}; font-size:.575rem; letter-spacing:.14em;
  text-transform:uppercase; color:{MUTED}; white-space:nowrap;
}}

/* ── zone board (signature) ───────────────────────────────────────────── */
.pg-board {{ display:flex; align-items:flex-end; gap:4px; height:126px; padding:6px 0 0 0; }}
.pg-col {{
  flex:1; min-width:7px; border-radius:3px 3px 0 0; position:relative;
  transition:filter .14s ease; cursor:default;
}}
.pg-col:hover {{ filter:brightness(1.5); }}
.pg-board-x {{
  display:flex; gap:4px; margin-top:8px; padding-top:8px; border-top:1px solid {LINE};
}}
.pg-board-x div {{
  flex:1; min-width:7px; text-align:center; font-family:{FONT_MONO};
  font-size:.535rem; color:{MUTED}; overflow:hidden; white-space:nowrap;
}}
.pg-scale {{
  display:flex; gap:1.4rem; flex-wrap:wrap; margin-top:1rem; padding-top:.85rem;
  border-top:1px solid {LINE};
  font-family:{FONT_MONO}; font-size:.595rem; color:{MUTED}; letter-spacing:.1em;
}}
.pg-scale i {{
  display:inline-block; width:20px; height:4px; border-radius:2px;
  margin-right:.45rem; vertical-align:middle;
}}
.pg-extremes {{ display:flex; gap:10px; margin-top:1rem; flex-wrap:wrap; }}
.pg-ex {{
  flex:1; min-width:172px; background:{RAISED}; border:1px solid {LINE};
  border-radius:10px; padding:11px 14px;
}}
.pg-ex-k {{
  font-family:{FONT_MONO}; font-size:.55rem; letter-spacing:.15em;
  text-transform:uppercase; color:{MUTED};
}}
.pg-ex-v {{
  font-family:{FONT_MONO}; font-size:1.14rem; font-weight:700; margin-top:.28rem;
  font-variant-numeric:tabular-nums;
}}
.pg-ex-v small {{ font-size:.66rem; color:{MUTED}; font-weight:400; margin-left:.3rem; }}

/* ── watchlist ────────────────────────────────────────────────────────── */
.pg-row {{
  display:flex; align-items:center; gap:12px; padding:11px 13px;
  border:1px solid {LINE}; border-radius:10px; background:{RAISED}; margin-bottom:7px;
}}
.pg-row.hot {{ border-color:rgba(255,92,122,.42); background:rgba(255,92,122,.07); }}
.pg-row-z {{
  font-family:{FONT_MONO}; font-weight:700; font-size:.815rem;
  color:{TEXT}; width:58px; flex-shrink:0;
}}
.pg-row-m {{ flex:1; height:6px; background:rgba(255,255,255,.06); border-radius:3px; overflow:hidden; }}
.pg-row-f {{ height:100%; border-radius:3px; }}
.pg-row-p {{
  font-family:{FONT_MONO}; font-size:.78rem; color:{TEXT}; width:50px;
  text-align:right; font-variant-numeric:tabular-nums; flex-shrink:0;
}}
.pg-row-t {{
  font-family:{FONT_MONO}; font-size:.545rem; letter-spacing:.11em;
  text-transform:uppercase; padding:3px 8px; border-radius:5px;
  width:56px; text-align:center; flex-shrink:0;
}}
.pg-t-hot {{ background:rgba(255,92,122,.17); color:{CORAL}; }}
.pg-t-ok  {{ background:rgba(47,217,172,.12); color:{TEAL}; }}

/* ── empty state ──────────────────────────────────────────────────────── */
.pg-empty {{
  border:1px dashed {LINE}; border-radius:12px; padding:2.5rem 1.6rem;
  text-align:center; background:rgba(255,255,255,.012);
}}
.pg-empty b {{
  display:block; color:{TEXT}; font-family:{FONT_DISPLAY}; font-size:1.0rem;
  font-weight:600; margin-bottom:.42rem;
}}
.pg-empty span {{ font-size:.83rem; color:{MUTED}; line-height:1.6; }}

/* ── architecture page ────────────────────────────────────────────────── */
.pg-flow {{ display:flex; flex-wrap:wrap; gap:9px; }}
.pg-node {{
  flex:1; min-width:148px; background:{RAISED}; border:1px solid {LINE};
  border-radius:12px; padding:15px 15px; border-top:2px solid var(--n,{AMBER});
}}
.pg-node h4 {{ font-size:.925rem; font-weight:600; margin:0 0 .38rem 0; color:{TEXT}; }}
.pg-node p {{ margin:0 0 .55rem 0; font-size:.735rem; color:{MUTED}; line-height:1.55; }}
.pg-node code {{
  font-family:{FONT_MONO}; font-size:.595rem; color:var(--n,{AMBER});
  background:none; padding:0; letter-spacing:.05em;
}}
.pg-spec {{ display:flex; gap:1.6rem; padding:13px 2px; border-bottom:1px solid {LINE}; }}
.pg-spec dt {{
  font-family:{FONT_MONO}; font-size:.605rem; letter-spacing:.13em;
  text-transform:uppercase; color:{AMBER}; width:178px; flex-shrink:0; padding-top:2px;
}}
.pg-spec dd {{ margin:0; font-size:.865rem; color:{TEXT}; line-height:1.55; }}
.pg-spec dd em {{ font-style:normal; color:{MUTED}; font-size:.775rem; }}
.pg-note {{
  background:{RAISED}; border:1px solid {LINE}; border-left:2px solid var(--n,{VIOLET});
  border-radius:11px; padding:16px 18px; margin-bottom:10px;
}}
.pg-note h4 {{ font-size:.955rem; font-weight:600; margin:0 0 .5rem 0; color:{TEXT}; }}
.pg-note p {{ margin:0 0 .55rem 0; font-size:.855rem; line-height:1.65; color:{TEXT}; opacity:.9; }}
.pg-note code {{
  display:block; font-family:{FONT_MONO}; font-size:.685rem; color:{MUTED};
  background:none; padding:0; line-height:1.55;
}}

/* ── widget overrides ─────────────────────────────────────────────────── */
.stButton button {{
  background:{RAISED}; color:{TEXT}; border:1px solid {LINE}; border-radius:10px;
  font-family:{FONT_BODY}; font-size:.815rem; font-weight:500;
  padding:.62rem 1rem; transition:border-color .15s, color .15s;
}}
.stButton button:hover {{ border-color:{AMBER}; color:{AMBER}; }}
.stButton button:focus:not(:active) {{ border-color:{AMBER}; color:{AMBER}; }}

div[data-baseweb="select"] > div {{
  background:{RAISED} !important; border-color:{LINE} !important; border-radius:9px !important;
}}
div[data-baseweb="tag"] {{ background:rgba(255,181,71,.15) !important; color:{AMBER} !important; }}

div[data-testid="stChatMessage"] {{
  background:{PANEL}; border:1px solid {LINE}; border-radius:13px; padding:3px 6px;
}}
div[data-testid="stChatInput"] textarea {{ font-family:{FONT_BODY}; }}
div[data-testid="stChatInput"] {{ border-color:{LINE}; }}

[data-testid="stCaptionContainer"] p {{ color:{MUTED}; font-size:.735rem; }}

*:focus-visible {{ outline:2px solid {AMBER}; outline-offset:2px; }}
@media (prefers-reduced-motion: reduce) {{ *{{animation:none!important;transition:none!important}} }}
@media (max-width:820px) {{ .pg-title{{font-size:1.95rem}} .pg-board{{height:92px}} }}
</style>
""",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Plotly theme
# ─────────────────────────────────────────────────────────────────────────────
pio.templates["pulsegrid"] = go.layout.Template(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=MUTED, size=12),
        colorway=SERIES,
        xaxis=dict(gridcolor="rgba(33,39,57,.75)", zerolinecolor=LINE, linecolor=LINE,
                   tickfont=dict(family="JetBrains Mono", size=10, color=MUTED)),
        yaxis=dict(gridcolor="rgba(33,39,57,.75)", zerolinecolor=LINE, linecolor=LINE,
                   tickfont=dict(family="JetBrains Mono", size=10, color=MUTED)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=MUTED),
                    orientation="h", y=1.14, x=0),
        hoverlabel=dict(bgcolor=RAISED, bordercolor=LINE,
                        font=dict(family="JetBrains Mono", size=11, color=TEXT)),
        margin=dict(l=6, r=6, t=28, b=6),
    )
)


def style_fig(fig: go.Figure, height: int = 340, ytitle: str = "") -> go.Figure:
    fig.update_layout(
        template="pulsegrid", height=height, yaxis_title=ytitle,
        xaxis_title="", title=None,
        modebar=dict(bgcolor="rgba(0,0,0,0)", color=MUTED, activecolor=AMBER),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Components
# ─────────────────────────────────────────────────────────────────────────────
def sidebar_brand() -> None:
    st.markdown(
        '<div class="pg-logo">'
        '<div class="pg-logo-mark">⚡</div>'
        '<div class="pg-logo-name">Pulse<em>Grid</em></div>'
        '<div class="pg-logo-sub">Electricity Markets</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def sidebar_meta(blocks: list[tuple[str, str]]) -> None:
    st.markdown('<div class="pg-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="pg-meta">'
        + "".join(
            f'<div class="pg-meta-block"><div class="pg-meta-k">{k}</div>'
            f'<div class="pg-meta-v">{v}</div></div>'
            for k, v in blocks
        )
        + "</div>",
        unsafe_allow_html=True,
    )


def hero(badge: str, eyebrow: str, title: str, accent: str,
         subtitle: str, kind: str = "") -> None:
    """Page hero — status pill, eyebrow, two-tone headline, one-line summary."""
    st.markdown(
        f'<div class="pg-hero"><div class="pg-eyebrow">'
        f'<span class="pg-badge {kind}"><span class="pg-dot"></span>{badge}</span>'
        f'<span class="pg-eyebrow-text">{eyebrow}</span></div>'
        f'<h1 class="pg-title">{title} <em>{accent}</em></h1>'
        f'<p class="pg-sub">{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def kpis(items: list[dict], synced: str = "") -> None:
    """items: [{value, unit, label, foot, accent}]"""
    cards = "".join(
        f'<div class="pg-kpi" style="--a:{i.get("accent", AMBER)}">'
        f'<div class="pg-kpi-v">{i["value"]}<small>{i.get("unit","")}</small></div>'
        f'<div class="pg-kpi-k">{i["label"]}</div>'
        f'<div class="pg-kpi-f">{i.get("foot","")}</div></div>'
        for i in items
    )
    st.markdown(f'<div class="pg-kpis">{cards}</div>', unsafe_allow_html=True)
    if synced:
        st.markdown(f'<div class="pg-synced">⚡ Snapshot <b>{synced}</b></div>',
                    unsafe_allow_html=True)


def panel_header(title: str, meta: str = "") -> None:
    """Header rendered inside st.container(border=True)."""
    st.markdown(
        f'<div class="pg-ph"><h3>{title}</h3><span>{meta}</span></div>',
        unsafe_allow_html=True,
    )


def price_colour(pct: float) -> str:
    if pct >= 0.85:
        return CORAL
    if pct >= 0.60:
        return AMBER
    if pct >= 0.30:
        return BLUE
    return TEAL


def zone_board(zones: list[tuple[str, float, float]]) -> None:
    """Signature element — every bidding zone as one column, ranked by price."""
    if not zones:
        return
    cols, labels = [], []
    for code, price, pct in zones:
        cols.append(
            f'<div class="pg-col" style="height:{16 + pct*84:.0f}%;'
            f'background:linear-gradient(180deg,{price_colour(pct)},'
            f'{price_colour(pct)}55)" title="{code} — {price:,.1f} EUR/MWh"></div>'
        )
        labels.append(f"<div>{code}</div>")

    hi, lo = zones[0], zones[-1]
    mid = sum(z[1] for z in zones) / len(zones)
    ex = [
        ("Highest zone", f"{hi[1]:,.0f}", hi[0], CORAL),
        ("Market average", f"{mid:,.0f}", f"{len(zones)} zones", AMBER),
        ("Lowest zone", f"{lo[1]:,.0f}", lo[0], TEAL),
        ("Spread", f"{hi[1]-lo[1]:,.0f}", "high − low", VIOLET),
    ]

    st.markdown(
        f'<div class="pg-board">{"".join(cols)}</div>'
        f'<div class="pg-board-x">{"".join(labels)}</div>'
        f'<div class="pg-scale">'
        f'<span><i style="background:{TEAL}"></i>BOTTOM 30%</span>'
        f'<span><i style="background:{BLUE}"></i>30–60%</span>'
        f'<span><i style="background:{AMBER}"></i>60–85%</span>'
        f'<span><i style="background:{CORAL}"></i>TOP 15% · SPIKE RANGE</span>'
        f"</div>"
        f'<div class="pg-extremes">'
        + "".join(
            f'<div class="pg-ex"><div class="pg-ex-k">{k}</div>'
            f'<div class="pg-ex-v" style="color:{c}">{v}'
            f"<small>{s}</small></div></div>"
            for k, v, s, c in ex
        )
        + "</div>",
        unsafe_allow_html=True,
    )


def watchlist(rows: list[tuple[str, float, int]]) -> None:
    st.markdown(
        "".join(
            f'<div class="pg-row{" hot" if flag else ""}">'
            f'<div class="pg-row-z">{zone}</div>'
            f'<div class="pg-row-m"><div class="pg-row-f" '
            f'style="width:{max(prob*100,2):.0f}%;background:'
            f'{CORAL if flag else (AMBER if prob>=.25 else TEAL)}"></div></div>'
            f'<div class="pg-row-p">{prob*100:.1f}%</div>'
            f'<div class="pg-row-t {"pg-t-hot" if flag else "pg-t-ok"}">'
            f'{"spike" if flag else "normal"}</div></div>'
            for zone, prob, flag in rows
        ),
        unsafe_allow_html=True,
    )


def empty(title: str, hint: str) -> None:
    st.markdown(
        f'<div class="pg-empty"><b>{title}</b><span>{hint}</span></div>',
        unsafe_allow_html=True,
    )

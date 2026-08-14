"""
PulseGrid design system.

Visual direction: "grid control room" — the instrument panel a transmission
system operator would actually watch. Condensed industrial signage for labels,
tabular monospace for every number, signal colours borrowed from grid operator
convention (amber = load, cyan = renewable, red = alert, mint = stable base).

All colour and type decisions live here. Nothing else in the app hardcodes a hex.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio

# ─────────────────────────────────────────────────────────────────────────────
# Tokens
# ─────────────────────────────────────────────────────────────────────────────
VOID   = "#0E1015"   # page base
PANEL  = "#171A21"   # card surface
RAISED = "#1E222C"   # inset surface
LINE   = "#262B36"   # hairline border
TEXT   = "#E8ECF3"   # primary text
MUTED  = "#79839A"   # secondary text

AMBER  = "#FFB020"   # load / primary accent
CYAN   = "#35D6ED"   # renewable
FLARE  = "#FF4D6D"   # spike alert
MINT   = "#37E0A6"   # nuclear / stable
VIOLET = "#9B8CFF"   # cross-border

SERIES = [AMBER, CYAN, MINT, VIOLET, FLARE, "#F0F4FF", "#5B8DEF", "#FF8A5B"]

FONT_DISPLAY = "'Barlow Condensed', 'Arial Narrow', sans-serif"
FONT_BODY    = "'Inter', -apple-system, system-ui, sans-serif"
FONT_MONO    = "'JetBrains Mono', 'SF Mono', Menlo, monospace"


# ─────────────────────────────────────────────────────────────────────────────
# Global CSS
# ─────────────────────────────────────────────────────────────────────────────
def inject_css() -> None:
    """Inject the global stylesheet. Call once per page render."""
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {{
  --void:{VOID}; --panel:{PANEL}; --raised:{RAISED}; --line:{LINE};
  --text:{TEXT}; --muted:{MUTED};
  --amber:{AMBER}; --cyan:{CYAN}; --flare:{FLARE}; --mint:{MINT};
}}

/* ── base ─────────────────────────────────────────────────────────────── */
.stApp {{ background:{VOID}; }}
.block-container {{ padding-top:2.2rem; padding-bottom:4rem; max-width:1500px; }}
html, body, [class*="css"] {{ font-family:{FONT_BODY}; color:{TEXT}; }}

#MainMenu, footer, header {{ visibility:hidden; }}

/* ── sidebar ──────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
  background:{PANEL}; border-right:1px solid {LINE};
}}
section[data-testid="stSidebar"] .block-container {{ padding-top:1.5rem; }}

/* ── typography ───────────────────────────────────────────────────────── */
h1, h2, h3 {{ font-family:{FONT_DISPLAY}; letter-spacing:.01em; color:{TEXT}; }}

.pg-wordmark {{
  font-family:{FONT_DISPLAY}; font-size:1.65rem; font-weight:700;
  letter-spacing:.10em; text-transform:uppercase; color:{TEXT};
  display:flex; align-items:center; gap:.55rem; margin:0 0 .15rem 0;
}}
.pg-wordmark span {{ color:{AMBER}; }}
.pg-tagline {{
  font-family:{FONT_MONO}; font-size:.68rem; color:{MUTED};
  letter-spacing:.06em; margin:0 0 1.6rem 0;
}}

/* section header: rule + eyebrow, encodes the data's cadence */
.pg-sec {{ margin:2.4rem 0 .9rem 0; }}
.pg-sec-top {{ display:flex; align-items:baseline; gap:.75rem; }}
.pg-sec h2 {{
  font-size:1.30rem; font-weight:600; text-transform:uppercase;
  letter-spacing:.05em; margin:0; color:{TEXT};
}}
.pg-sec-meta {{
  font-family:{FONT_MONO}; font-size:.63rem; color:{MUTED};
  letter-spacing:.08em; text-transform:uppercase; white-space:nowrap;
}}
.pg-sec-rule {{ height:1px; background:{LINE}; margin-top:.55rem; }}

/* ── KPI cards ────────────────────────────────────────────────────────── */
.pg-kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; }}
.pg-kpi {{
  background:{PANEL}; border:1px solid {LINE}; border-radius:10px;
  padding:16px 18px 14px 18px; position:relative; overflow:hidden;
}}
.pg-kpi::before {{
  content:''; position:absolute; left:0; top:0; bottom:0; width:2px;
  background:var(--kpi-accent,{AMBER});
}}
.pg-kpi-label {{
  font-family:{FONT_MONO}; font-size:.62rem; letter-spacing:.11em;
  text-transform:uppercase; color:{MUTED}; margin-bottom:.5rem;
}}
.pg-kpi-value {{
  font-family:{FONT_MONO}; font-size:1.95rem; font-weight:700;
  line-height:1; color:{TEXT}; font-variant-numeric:tabular-nums;
}}
.pg-kpi-unit {{ font-size:.85rem; font-weight:400; color:{MUTED}; margin-left:.28rem; }}
.pg-kpi-foot {{ font-size:.72rem; color:{MUTED}; margin-top:.55rem; }}

/* ── zone price strip (signature element) ─────────────────────────────── */
.pg-strip-wrap {{
  background:{PANEL}; border:1px solid {LINE}; border-radius:10px;
  padding:18px 20px 12px 20px;
}}
.pg-strip {{ display:flex; align-items:flex-end; gap:3px; height:74px; }}
.pg-bar {{
  flex:1; min-width:6px; border-radius:2px 2px 0 0; position:relative;
  transition:transform .12s ease, filter .12s ease; cursor:default;
}}
.pg-bar:hover {{ filter:brightness(1.45); transform:scaleY(1.04); }}
.pg-strip-x {{
  display:flex; gap:3px; margin-top:7px;
  border-top:1px solid {LINE}; padding-top:6px;
}}
.pg-strip-x div {{
  flex:1; min-width:6px; text-align:center; font-family:{FONT_MONO};
  font-size:.52rem; color:{MUTED}; letter-spacing:0;
  overflow:hidden; white-space:nowrap;
}}
.pg-legend {{
  display:flex; gap:1.25rem; margin-top:.85rem; flex-wrap:wrap;
  font-family:{FONT_MONO}; font-size:.62rem; color:{MUTED}; letter-spacing:.06em;
}}
.pg-legend i {{
  display:inline-block; width:9px; height:9px; border-radius:2px;
  margin-right:.4rem; vertical-align:middle;
}}

/* ── watchlist rows ───────────────────────────────────────────────────── */
.pg-row {{
  display:flex; align-items:center; gap:12px; padding:10px 14px;
  border:1px solid {LINE}; border-radius:8px; background:{PANEL}; margin-bottom:7px;
}}
.pg-row.alert {{ border-color:rgba(255,77,109,.42); background:rgba(255,77,109,.06); }}
.pg-row-zone {{
  font-family:{FONT_MONO}; font-weight:700; font-size:.86rem;
  color:{TEXT}; width:62px; flex-shrink:0;
}}
.pg-row-meter {{ flex:1; height:5px; background:{RAISED}; border-radius:3px; overflow:hidden; }}
.pg-row-fill {{ height:100%; border-radius:3px; }}
.pg-row-pct {{
  font-family:{FONT_MONO}; font-size:.80rem; color:{TEXT};
  width:52px; text-align:right; font-variant-numeric:tabular-nums; flex-shrink:0;
}}
.pg-row-tag {{
  font-family:{FONT_MONO}; font-size:.58rem; letter-spacing:.08em;
  text-transform:uppercase; padding:2px 7px; border-radius:3px;
  width:58px; text-align:center; flex-shrink:0;
}}
.pg-tag-alert {{ background:rgba(255,77,109,.16); color:{FLARE}; }}
.pg-tag-calm  {{ background:rgba(55,224,166,.12); color:{MINT}; }}

/* ── panels & empty states ────────────────────────────────────────────── */
.pg-panel {{
  background:{PANEL}; border:1px solid {LINE}; border-radius:10px; padding:18px 20px;
}}
.pg-empty {{
  border:1px dashed {LINE}; border-radius:10px; padding:2.4rem 1.5rem;
  text-align:center; color:{MUTED}; background:{PANEL};
}}
.pg-empty b {{ display:block; color:{TEXT}; font-family:{FONT_DISPLAY};
  font-size:1.05rem; letter-spacing:.03em; text-transform:uppercase; margin-bottom:.4rem; }}
.pg-empty span {{ font-size:.84rem; }}

/* ── spec list (About) ────────────────────────────────────────────────── */
.pg-spec {{ display:flex; border-bottom:1px solid {LINE}; padding:11px 0; gap:1.5rem; }}
.pg-spec dt {{
  font-family:{FONT_MONO}; font-size:.66rem; letter-spacing:.09em;
  text-transform:uppercase; color:{MUTED}; width:190px; flex-shrink:0; padding-top:2px;
}}
.pg-spec dd {{ margin:0; font-size:.88rem; color:{TEXT}; }}
.pg-spec dd em {{ font-style:normal; color:{MUTED}; font-size:.80rem; }}

/* ── flow diagram (About) ─────────────────────────────────────────────── */
.pg-flow {{ display:flex; flex-wrap:wrap; gap:8px; align-items:stretch; }}
.pg-flow-node {{
  flex:1; min-width:132px; background:{PANEL}; border:1px solid {LINE};
  border-radius:8px; padding:13px 14px; border-top:2px solid var(--n,{AMBER});
}}
.pg-flow-node h4 {{
  font-family:{FONT_DISPLAY}; font-size:.92rem; text-transform:uppercase;
  letter-spacing:.05em; margin:0 0 .3rem 0; color:{TEXT};
}}
.pg-flow-node p {{ margin:0; font-size:.74rem; color:{MUTED}; line-height:1.45; }}
.pg-flow-node code {{
  font-family:{FONT_MONO}; font-size:.62rem; color:var(--n,{AMBER});
  background:none; padding:0; letter-spacing:.04em;
}}

/* ── streamlit widget overrides ───────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{ gap:4px; border-bottom:1px solid {LINE}; }}
.stTabs [data-baseweb="tab"] {{
  background:transparent; border:none; border-radius:0; padding:9px 15px;
  font-family:{FONT_MONO}; font-size:.70rem; letter-spacing:.09em;
  text-transform:uppercase; color:{MUTED};
}}
.stTabs [aria-selected="true"] {{ color:{AMBER}; box-shadow:inset 0 -2px 0 {AMBER}; }}

.stButton button {{
  background:{RAISED}; color:{TEXT}; border:1px solid {LINE}; border-radius:7px;
  font-family:{FONT_MONO}; font-size:.70rem; letter-spacing:.07em;
  text-transform:uppercase; padding:.5rem .9rem; transition:border-color .15s ease;
}}
.stButton button:hover {{ border-color:{AMBER}; color:{AMBER}; }}

div[data-testid="stChatInput"] textarea {{ font-family:{FONT_BODY}; }}
div[data-testid="stChatMessage"] {{
  background:{PANEL}; border:1px solid {LINE}; border-radius:10px; padding:2px 4px;
}}

div[data-testid="stDataFrame"] {{ border:1px solid {LINE}; border-radius:8px; }}

/* focus visibility — keyboard users */
*:focus-visible {{ outline:2px solid {AMBER}; outline-offset:2px; }}

@media (prefers-reduced-motion: reduce) {{
  * {{ transition:none !important; animation:none !important; }}
}}
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
        xaxis=dict(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE,
                   tickfont=dict(family="JetBrains Mono", size=10, color=MUTED)),
        yaxis=dict(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE,
                   tickfont=dict(family="JetBrains Mono", size=10, color=MUTED)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=MUTED),
                    orientation="h", y=1.12, x=0),
        hoverlabel=dict(bgcolor=RAISED, bordercolor=LINE,
                        font=dict(family="JetBrains Mono", size=11, color=TEXT)),
        margin=dict(l=8, r=8, t=34, b=8),
    )
)


def style_fig(fig: go.Figure, height: int = 340, ytitle: str = "") -> go.Figure:
    """Apply the PulseGrid template and strip chart junk."""
    fig.update_layout(
        template="pulsegrid",
        height=height,
        yaxis_title=ytitle,
        xaxis_title="",
        title=None,
        modebar=dict(bgcolor="rgba(0,0,0,0)", color=MUTED, activecolor=AMBER),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# HTML components
# ─────────────────────────────────────────────────────────────────────────────
def brand() -> None:
    st.markdown(
        '<div class="pg-wordmark"><span>◤</span>PULSEGRID</div>'
        '<div class="pg-tagline">EUROPEAN + US ELECTRICITY MARKET INTELLIGENCE</div>',
        unsafe_allow_html=True,
    )


def section(title: str, meta: str = "") -> None:
    """Section header. `meta` should state the data's real cadence or scope."""
    st.markdown(
        f'<div class="pg-sec"><div class="pg-sec-top"><h2>{title}</h2>'
        f'<div class="pg-sec-meta">{meta}</div></div>'
        f'<div class="pg-sec-rule"></div></div>',
        unsafe_allow_html=True,
    )


def kpis(items: list[dict]) -> None:
    """items: [{label, value, unit, foot, accent}]"""
    cards = "".join(
        f'<div class="pg-kpi" style="--kpi-accent:{i.get("accent", AMBER)}">'
        f'<div class="pg-kpi-label">{i["label"]}</div>'
        f'<div class="pg-kpi-value">{i["value"]}'
        f'<span class="pg-kpi-unit">{i.get("unit", "")}</span></div>'
        f'<div class="pg-kpi-foot">{i.get("foot", "")}</div></div>'
        for i in items
    )
    st.markdown(f'<div class="pg-kpis">{cards}</div>', unsafe_allow_html=True)


def price_colour(pct: float) -> str:
    """Map a 0–1 price percentile to a signal colour."""
    if pct >= 0.85:
        return FLARE
    if pct >= 0.60:
        return AMBER
    if pct >= 0.30:
        return CYAN
    return MINT


def zone_strip(zones: list[tuple[str, float, float]]) -> None:
    """
    Signature element — every bidding zone as one bar, ordered by price.

    zones: [(zone_code, avg_price, percentile_0_to_1)]
    """
    if not zones:
        return
    bars, labels = [], []
    for code, price, pct in zones:
        h = 18 + pct * 82                       # 18–100% of strip height
        c = price_colour(pct)
        bars.append(
            f'<div class="pg-bar" style="height:{h:.0f}%;background:{c}" '
            f'title="{code} — {price:,.1f} EUR/MWh"></div>'
        )
        labels.append(f"<div>{code}</div>")
    st.markdown(
        f'<div class="pg-strip-wrap">'
        f'<div class="pg-strip">{"".join(bars)}</div>'
        f'<div class="pg-strip-x">{"".join(labels)}</div>'
        f'<div class="pg-legend">'
        f'<span><i style="background:{MINT}"></i>BOTTOM 30%</span>'
        f'<span><i style="background:{CYAN}"></i>30–60%</span>'
        f'<span><i style="background:{AMBER}"></i>60–85%</span>'
        f'<span><i style="background:{FLARE}"></i>TOP 15% · SPIKE RANGE</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def watchlist(rows: list[tuple[str, float, int]]) -> None:
    """rows: [(zone, probability_0_to_1, predicted_spike_flag)]"""
    html = []
    for zone, prob, flag in rows:
        alert = flag == 1
        colour = FLARE if alert else (AMBER if prob >= 0.25 else MINT)
        html.append(
            f'<div class="pg-row{" alert" if alert else ""}">'
            f'<div class="pg-row-zone">{zone}</div>'
            f'<div class="pg-row-meter">'
            f'<div class="pg-row-fill" style="width:{prob*100:.0f}%;background:{colour}"></div></div>'
            f'<div class="pg-row-pct">{prob*100:.1f}%</div>'
            f'<div class="pg-row-tag {"pg-tag-alert" if alert else "pg-tag-calm"}">'
            f'{"SPIKE" if alert else "NORMAL"}</div></div>'
        )
    st.markdown("".join(html), unsafe_allow_html=True)


def empty(title: str, hint: str) -> None:
    """Empty states name what's missing and what will fill it."""
    st.markdown(
        f'<div class="pg-empty"><b>{title}</b><span>{hint}</span></div>',
        unsafe_allow_html=True,
    )

"""
PulseGrid design system.

Direction: premium market intelligence terminal. Deep navy surfaces with a
cold electric-sky primary, glassy panels lit from the top edge, and every
number set large in tabular monospace. Amber and coral are reserved for what
they mean in a power market — load and spike — so colour always carries
information, never decoration.

All colour and type decisions live here. No other module hardcodes a hex.
"""

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Tokens
# ─────────────────────────────────────────────────────────────────────────────
VOID   = "#060B16"   # page base
PANEL  = "#0C1425"   # card surface
RAISED = "#121D33"   # inset surface
LINE   = "#1D2B47"   # hairline border
TEXT   = "#EAF1FB"   # primary text
MUTED  = "#8298B8"   # secondary text

SKY    = "#38BDF8"   # primary accent — electric sky
BLUE   = SKY
AMBER  = "#FBBF24"   # load / warm mid-range
CORAL  = "#FB7185"   # spike alert
TEAL   = "#34D399"   # renewable / calm
VIOLET = "#A78BFA"   # model / AI

SERIES = [SKY, AMBER, TEAL, VIOLET, CORAL, "#7DD3FC", "#FDE68A", "#6EE7B7"]

FONT_DISPLAY = "'Space Grotesk', -apple-system, system-ui, sans-serif"
FONT_BODY    = "'Inter', -apple-system, system-ui, sans-serif"
FONT_MONO    = "'JetBrains Mono', 'SF Mono', Menlo, monospace"


# ─────────────────────────────────────────────────────────────────────────────
# Global stylesheet
# ─────────────────────────────────────────────────────────────────────────────
def inject_css() -> None:
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {{
  --void:{VOID}; --panel:{PANEL}; --raised:{RAISED}; --line:{LINE};
  --text:{TEXT}; --muted:{MUTED}; --sky:{SKY}; --amber:{AMBER};
  --coral:{CORAL}; --teal:{TEAL}; --violet:{VIOLET};
}}

/* ── base ─────────────────────────────────────────────────────────────── */
.stApp {{
  background:
    radial-gradient(1300px 620px at 72% -12%, rgba(56,189,248,.085), transparent 60%),
    radial-gradient(1000px 560px at 4% -6%, rgba(167,139,250,.06), transparent 55%),
    linear-gradient(180deg, #081020 0%, {VOID} 42%);
}}
.block-container {{ padding-top:2.4rem; padding-bottom:5rem; max-width:1560px; }}
html, body, [class*="css"] {{ font-family:{FONT_BODY}; color:{TEXT}; }}
#MainMenu, footer, header {{ visibility:hidden; }}
h1,h2,h3,h4 {{ font-family:{FONT_DISPLAY}; color:{TEXT}; }}
a {{ color:{SKY}; }}

/* ── sidebar ──────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
  background:linear-gradient(180deg,#0A1322 0%,#080F1D 100%);
  border-right:1px solid {LINE};
}}
section[data-testid="stSidebar"] .block-container {{ padding-top:1.6rem; }}

/* nav links */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {{
  border-radius:10px; padding:.55rem .8rem; margin:2px 0;
  color:{MUTED};
}}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {{
  background:rgba(56,189,248,.07); color:{TEXT};
}}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {{
  background:rgba(56,189,248,.12); color:{TEXT};
  box-shadow:inset 3px 0 0 {SKY};
}}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] span {{
  font-family:{FONT_BODY}; font-size:.9rem; font-weight:500;
}}

.pg-logo {{ text-align:center; margin-bottom:.6rem; }}
.pg-logo-mark {{
  width:52px; height:52px; margin:0 auto .75rem auto; border-radius:15px;
  background:linear-gradient(140deg,{SKY},{VIOLET});
  display:flex; align-items:center; justify-content:center;
  font-size:1.55rem; box-shadow:0 8px 28px rgba(56,189,248,.32);
}}
.pg-logo-name {{
  font-family:{FONT_DISPLAY}; font-size:1.3rem; font-weight:700;
  color:{TEXT}; letter-spacing:-.01em;
}}
.pg-logo-name em {{ font-style:normal; color:{SKY}; }}
.pg-logo-sub {{
  font-family:{FONT_MONO}; font-size:.575rem; color:{MUTED};
  letter-spacing:.22em; text-transform:uppercase; margin-top:.34rem;
}}

.pg-meta-block {{ margin-bottom:1.0rem; }}
.pg-meta-k {{
  font-family:{FONT_MONO}; font-size:.565rem; letter-spacing:.16em;
  text-transform:uppercase; color:{SKY}; margin-bottom:.3rem; opacity:.85;
}}
.pg-meta-v {{ font-size:.79rem; color:{TEXT}; line-height:1.6; }}
.pg-meta-v span {{ color:{MUTED}; }}
.pg-divider {{ height:1px; background:{LINE}; margin:1.25rem 0; }}

/* ── page hero ────────────────────────────────────────────────────────── */
.pg-hero {{ margin-bottom:2.0rem; }}
.pg-eyebrow {{ display:flex; align-items:center; gap:.9rem; margin-bottom:1.1rem; }}
.pg-badge {{
  display:inline-flex; align-items:center; gap:.5rem;
  border:1px solid rgba(52,211,153,.38); background:rgba(52,211,153,.10);
  color:{TEAL}; border-radius:999px; padding:.3rem .85rem;
  font-family:{FONT_MONO}; font-size:.6rem; font-weight:700;
  letter-spacing:.16em; text-transform:uppercase;
}}
.pg-badge.model {{ border-color:rgba(167,139,250,.38); background:rgba(167,139,250,.10); color:{VIOLET}; }}
.pg-badge.build {{ border-color:rgba(56,189,248,.34);  background:rgba(56,189,248,.10);  color:{SKY}; }}
.pg-dot {{ width:7px; height:7px; border-radius:50%; background:currentColor;
  animation:pgpulse 2s ease-in-out infinite; }}
@keyframes pgpulse {{ 0%,100%{{opacity:1}} 50%{{opacity:.3}} }}
.pg-eyebrow-text {{
  font-family:{FONT_MONO}; font-size:.63rem; letter-spacing:.24em;
  text-transform:uppercase; color:{SKY}; opacity:.8;
}}
.pg-title {{
  font-family:{FONT_DISPLAY}; font-size:2.85rem; font-weight:700;
  letter-spacing:-.03em; line-height:1.08; margin:0 0 .6rem 0; color:{TEXT};
}}
.pg-title em {{ font-style:normal; color:{SKY};
  text-shadow:0 0 34px rgba(56,189,248,.45); }}
.pg-sub {{ font-size:.96rem; color:{MUTED}; max-width:80ch; line-height:1.65; margin:0; }}

/* ── KPI cards ────────────────────────────────────────────────────────── */
.pg-kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(158px,1fr)); gap:13px; }}
.pg-kpi {{
  background:{PANEL};
  border:1px solid {LINE}; border-radius:13px; padding:19px 16px 16px 16px;
  text-align:center; box-shadow:0 6px 22px rgba(2,8,23,.30);
}}
.pg-kpi-v {{
  font-family:{FONT_MONO}; font-size:2.05rem; font-weight:700; line-height:1;
  color:var(--a,{SKY}); font-variant-numeric:tabular-nums; letter-spacing:-.02em;
}}
.pg-kpi-v small {{ font-size:.8rem; font-weight:500; color:{MUTED}; margin-left:.22rem; }}
.pg-kpi-k {{
  font-family:{FONT_MONO}; font-size:.585rem; letter-spacing:.17em;
  text-transform:uppercase; color:{MUTED}; margin-top:.7rem;
}}
.pg-kpi-f {{ font-size:.685rem; color:{MUTED}; margin-top:.3rem; opacity:.75; }}
.pg-synced {{
  text-align:right; font-family:{FONT_MONO}; font-size:.63rem;
  color:{MUTED}; letter-spacing:.08em; margin-top:.8rem;
}}
.pg-synced b {{ color:{SKY}; font-weight:500; }}

/* ── panels ───────────────────────────────────────────────────────────── */
div[data-testid="stVerticalBlockBorderWrapper"] {{
  background:{PANEL};
  border:1px solid {LINE} !important; border-radius:14px;
  padding:12px 10px; box-shadow:0 8px 28px rgba(2,8,23,.35);
}}
div[data-testid="stVerticalBlockBorderWrapper"] > div {{
  border:none !important; box-shadow:none !important; background:transparent !important;
}}
.pg-ph {{
  display:flex; align-items:baseline; justify-content:space-between;
  gap:1rem; padding:6px 6px 12px 6px; margin-bottom:4px;
}}
.pg-ph h3 {{ font-size:1.02rem; font-weight:600; margin:0; color:{TEXT}; }}
.pg-ph span {{
  font-family:{FONT_MONO}; font-size:.575rem; letter-spacing:.15em;
  text-transform:uppercase; color:{MUTED}; white-space:nowrap;
}}

/* ── zone board (signature) ───────────────────────────────────────────── */
.pg-board {{ display:flex; align-items:flex-end; gap:5px; height:132px; padding-top:8px; }}
.pg-col {{
  flex:1; min-width:8px; border-radius:4px 4px 2px 2px;
  transition:filter .14s ease; cursor:default;
  box-shadow:0 0 14px -6px currentColor;
}}
.pg-col:hover {{ filter:brightness(1.45); }}
.pg-board-x {{ display:flex; gap:5px; margin-top:9px; }}
.pg-board-x div {{
  flex:1; min-width:8px; text-align:center; font-family:{FONT_MONO};
  font-size:.545rem; color:{MUTED}; overflow:hidden; white-space:nowrap;
}}
.pg-scale {{
  display:flex; gap:1.5rem; flex-wrap:wrap; margin-top:1.05rem;
  font-family:{FONT_MONO}; font-size:.6rem; color:{MUTED}; letter-spacing:.1em;
}}
.pg-scale i {{ display:inline-block; width:22px; height:5px; border-radius:3px;
  margin-right:.5rem; vertical-align:middle; }}
.pg-extremes {{ display:flex; gap:11px; margin-top:1.05rem; flex-wrap:wrap; }}
.pg-ex {{
  flex:1; min-width:170px; background:{RAISED}; border:none;
  border-radius:11px; padding:12px 15px; text-align:center;
}}
.pg-ex-k {{ font-family:{FONT_MONO}; font-size:.555rem; letter-spacing:.16em;
  text-transform:uppercase; color:{MUTED}; }}
.pg-ex-v {{ font-family:{FONT_MONO}; font-size:1.22rem; font-weight:700;
  margin-top:.32rem; font-variant-numeric:tabular-nums; }}
.pg-ex-v small {{ font-size:.64rem; color:{MUTED}; font-weight:400; margin-left:.32rem; }}

/* ── watchlist ────────────────────────────────────────────────────────── */
.pg-row {{
  display:flex; align-items:center; gap:12px; padding:11px 14px;
  border:1px solid transparent; border-radius:11px; background:{RAISED}; margin-bottom:8px;
}}
.pg-row.hot {{ background:rgba(251,113,133,.08);
  box-shadow:inset 3px 0 0 {CORAL}; }}
.pg-row-z {{ width:118px; flex-shrink:0; line-height:1.25; }}
.pg-row-z b {{ font-family:{FONT_MONO}; font-weight:700; font-size:.82rem; color:{TEXT}; }}
.pg-row-z i {{ display:block; font-style:normal; font-size:.63rem; color:{MUTED}; }}
.pg-row-m {{ flex:1; height:6px; background:rgba(255,255,255,.055); border-radius:3px; overflow:hidden; }}
.pg-row-f {{ height:100%; border-radius:3px; }}
.pg-row-p {{ font-family:{FONT_MONO}; font-size:.78rem; color:{TEXT}; width:52px;
  text-align:right; font-variant-numeric:tabular-nums; flex-shrink:0; }}
.pg-row-t {{ font-family:{FONT_MONO}; font-size:.55rem; letter-spacing:.12em;
  text-transform:uppercase; padding:3px 9px; border-radius:6px;
  width:58px; text-align:center; flex-shrink:0; }}
.pg-t-hot {{ background:rgba(251,113,133,.18); color:{CORAL}; }}
.pg-t-ok  {{ background:rgba(52,211,153,.13);  color:{TEAL}; }}

/* ── empty state ──────────────────────────────────────────────────────── */
.pg-empty {{
  border:1px dashed {LINE}; border-radius:13px; padding:2.6rem 1.7rem;
  text-align:center; background:rgba(56,189,248,.02);
}}
.pg-empty b {{ display:block; color:{TEXT}; font-family:{FONT_DISPLAY};
  font-size:1.02rem; font-weight:600; margin-bottom:.45rem; }}
.pg-empty span {{ font-size:.835rem; color:{MUTED}; line-height:1.65; }}

/* ── architecture page ────────────────────────────────────────────────── */
.pg-flow {{ display:flex; flex-wrap:wrap; gap:10px; }}
.pg-node {{
  flex:1; min-width:150px; background:{RAISED}; border:1px solid {LINE};
  border-radius:13px; padding:16px; border-top:2px solid var(--n,{SKY});
}}
.pg-node h4 {{ font-size:.93rem; font-weight:600; margin:0 0 .4rem 0; }}
.pg-node p {{ margin:0 0 .55rem 0; font-size:.735rem; color:{MUTED}; line-height:1.55; }}
.pg-node code {{ font-family:{FONT_MONO}; font-size:.6rem; color:var(--n,{SKY});
  background:none; padding:0; letter-spacing:.05em; }}
.pg-spec {{ display:flex; gap:1.6rem; padding:13px 4px; border-bottom:1px solid {LINE}; }}
.pg-spec dt {{ font-family:{FONT_MONO}; font-size:.61rem; letter-spacing:.14em;
  text-transform:uppercase; color:{SKY}; width:180px; flex-shrink:0; padding-top:2px; }}
.pg-spec dd {{ margin:0; font-size:.87rem; color:{TEXT}; line-height:1.55; }}
.pg-spec dd em {{ font-style:normal; color:{MUTED}; font-size:.775rem; }}
.pg-note {{
  background:{RAISED}; border:1px solid {LINE}; border-left:3px solid var(--n,{VIOLET});
  border-radius:12px; padding:17px 19px; margin-bottom:11px;
}}
.pg-note h4 {{ font-size:.96rem; font-weight:600; margin:0 0 .5rem 0; }}
.pg-note p {{ margin:0 0 .55rem 0; font-size:.86rem; line-height:1.65; color:{TEXT}; opacity:.9; }}
.pg-note code {{ display:block; font-family:{FONT_MONO}; font-size:.69rem;
  color:{MUTED}; background:none; padding:0; line-height:1.55; }}

/* ── widget overrides ─────────────────────────────────────────────────── */
.stButton button {{
  background:{RAISED}; color:{TEXT}; border:1px solid {LINE}; border-radius:11px;
  font-family:{FONT_BODY}; font-size:.82rem; font-weight:500;
  padding:.65rem 1.05rem; transition:all .16s ease;
}}
.stButton button:hover {{
  border-color:{SKY}; color:{SKY}; background:rgba(56,189,248,.07);
  box-shadow:0 0 22px -8px rgba(56,189,248,.6);
}}
.stButton button:focus:not(:active) {{ border-color:{SKY}; color:{SKY}; }}

div[data-baseweb="select"] > div {{
  background:{RAISED} !important; border-color:{LINE} !important; border-radius:10px !important;
}}
div[data-baseweb="tag"] {{
  background:rgba(56,189,248,.16) !important; border-radius:7px !important;
}}
div[data-baseweb="tag"] span {{ color:#7DD3FC !important; }}
div[data-baseweb="tag"] svg {{ fill:#7DD3FC !important; }}
ul[data-testid="stSelectboxVirtualDropdown"] {{ background:{RAISED}; }}

div[data-testid="stChatMessage"] {{
  background:transparent; border:none; border-radius:0; padding:2px 0;
}}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
  background:{RAISED}; border-radius:14px; padding:6px 14px;
}}
div[data-testid="stChatMessage"] p {{ font-size:.92rem; line-height:1.68; }}
div[data-testid="stChatInput"] {{ border-color:{LINE}; }}
div[data-testid="stChatInput"] textarea {{ font-family:{FONT_BODY}; }}

[data-testid="stCaptionContainer"] p {{ color:{MUTED}; font-size:.735rem; }}

.st-key-pg_sugg .pg-sugg-h {{
  font-family:{FONT_MONO}; font-size:.6rem; letter-spacing:.16em;
  text-transform:uppercase; color:{MUTED}; margin:0 0 .6rem 2px;
}}
.st-key-pg_sugg .stButton button {{
  font-size:.755rem; font-weight:400; color:{MUTED};
  text-align:left; justify-content:flex-start;
  padding:.5rem .7rem; border-radius:9px; line-height:1.4;
  background:transparent; border:1px solid {LINE}; width:100%;
}}
.st-key-pg_sugg .stButton button:hover {{
  color:{TEXT}; border-color:{SKY}; background:rgba(56,189,248,.06);
  box-shadow:none;
}}
.st-key-pg_clear .stButton button {{
  font-size:.7rem; color:{MUTED}; background:transparent;
  border:none; padding:.3rem .4rem;
}}
.st-key-pg_clear .stButton button:hover {{ color:{CORAL}; box-shadow:none; }}

/* zone code reference grid */
.pg-zoneref {{
  display:grid; grid-template-columns:repeat(auto-fill,minmax(168px,1fr));
  gap:4px 18px; padding:4px 2px;
}}
.pg-zoneref div {{ font-size:.7rem; color:{MUTED}; }}
.pg-zoneref b {{ font-family:{FONT_MONO}; font-weight:600; font-size:.68rem;
  color:{TEXT}; display:inline-block; width:52px; }}

details[data-testid="stExpander"] {{
  border:1px solid {LINE}; border-radius:11px; background:transparent;
}}
details[data-testid="stExpander"] summary {{
  font-family:{FONT_MONO}; font-size:.66rem; letter-spacing:.1em;
  text-transform:uppercase; color:{MUTED};
}}
details[data-testid="stExpander"] summary:hover {{ color:{SKY}; }}

*:focus-visible {{ outline:2px solid {SKY}; outline-offset:2px; }}
@media (prefers-reduced-motion: reduce) {{ *{{animation:none!important;transition:none!important}} }}
@media (max-width:820px) {{ .pg-title{{font-size:2rem}} .pg-board{{height:96px}} }}
</style>
""",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Plotly theme
# ─────────────────────────────────────────────────────────────────────────────
pio.templates["pulsegrid"] = go.layout.Template(
    layout=dict(
        paper_bgcolor=PANEL,
        plot_bgcolor="#0A1120",
        font=dict(family="Inter, sans-serif", color=MUTED, size=12),
        colorway=SERIES,
        xaxis=dict(gridcolor="rgba(29,43,71,.65)", zerolinecolor=LINE, linecolor=LINE,
                   automargin=True,
                   tickfont=dict(family="JetBrains Mono", size=10, color=MUTED)),
        yaxis=dict(gridcolor="rgba(29,43,71,.65)", zerolinecolor=LINE, linecolor=LINE,
                   automargin=True, title_standoff=14,
                   tickfont=dict(family="JetBrains Mono", size=10, color=MUTED)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=MUTED),
                    orientation="h", y=1.02, yanchor="bottom", x=0),
        hoverlabel=dict(bgcolor=RAISED, bordercolor=LINE,
                        font=dict(family="JetBrains Mono", size=11, color=TEXT)),
        margin=dict(l=56, r=18, t=46, b=44),
    )
)


def style_fig(fig: go.Figure, height: int = 340, ytitle: str = "") -> go.Figure:
    fig.update_layout(
        template="pulsegrid", height=height, yaxis_title=ytitle,
        xaxis_title="", title=None, legend_title_text="",
        modebar=dict(bgcolor="rgba(0,0,0,0)", color=MUTED, activecolor=SKY),
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
        '<div class="pg-logo-sub">Energy Market Intelligence</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def sidebar_meta(blocks: list[tuple[str, str]]) -> None:
    st.markdown('<div class="pg-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        "".join(
            f'<div class="pg-meta-block"><div class="pg-meta-k">{k}</div>'
            f'<div class="pg-meta-v">{v}</div></div>'
            for k, v in blocks
        ),
        unsafe_allow_html=True,
    )


def hero(badge: str, eyebrow: str, title: str, accent: str,
         subtitle: str, kind: str = "") -> None:
    st.markdown(
        f'<div class="pg-hero"><div class="pg-eyebrow">'
        f'<span class="pg-badge {kind}"><span class="pg-dot"></span>{badge}</span>'
        f'<span class="pg-eyebrow-text">{eyebrow}</span></div>'
        f'<h1 class="pg-title">{title} <em>{accent}</em></h1>'
        f'<p class="pg-sub">{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def kpis(items: list[dict], synced: str = "") -> None:
    cards = "".join(
        f'<div class="pg-kpi" style="--a:{i.get("accent", SKY)}">'
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
        return SKY
    return TEAL


def zone_board(zones: list[tuple[str, str, float, float]]) -> None:
    """Signature element — every bidding zone as one column, ranked by price.

    zones: [(code, name, avg_price, percentile)]
    """
    if not zones:
        return
    cols, labels = [], []
    for code, name, price, pct in zones:
        c = price_colour(pct)
        cols.append(
            f'<div class="pg-col" style="height:{15 + pct*85:.0f}%;'
            f'background:{c};color:{c}" title="{code} · {name} — {price:,.1f} EUR/MWh"></div>'
        )
        labels.append(f"<div>{code}</div>")

    hi, lo = zones[0], zones[-1]
    mid = sum(z[2] for z in zones) / len(zones)
    ex = [
        ("Highest zone", f"{hi[2]:,.0f}", hi[1], CORAL),
        ("Market average", f"{mid:,.0f}", f"{len(zones)} zones", SKY),
        ("Lowest zone", f"{lo[2]:,.0f}", lo[1], TEAL),
        ("Spread", f"{hi[2]-lo[2]:,.0f}", "high − low", VIOLET),
    ]

    st.markdown(
        f'<div class="pg-board">{"".join(cols)}</div>'
        f'<div class="pg-board-x">{"".join(labels)}</div>'
        f'<div class="pg-scale">'
        f'<span><i style="background:{TEAL}"></i>BOTTOM 30%</span>'
        f'<span><i style="background:{SKY}"></i>30–60%</span>'
        f'<span><i style="background:{AMBER}"></i>60–85%</span>'
        f'<span><i style="background:{CORAL}"></i>TOP 15% · SPIKE RANGE</span>'
        f"</div>"
        f'<div class="pg-extremes">'
        + "".join(
            f'<div class="pg-ex"><div class="pg-ex-k">{k}</div>'
            f'<div class="pg-ex-v" style="color:{c}">{v}<small>{s}</small></div></div>'
            for k, v, s, c in ex
        )
        + "</div>",
        unsafe_allow_html=True,
    )


def watchlist(rows: list[tuple[str, str, float, int]]) -> None:
    """rows: [(code, name, probability, spike_flag)]"""
    st.markdown(
        "".join(
            f'<div class="pg-row{" hot" if flag else ""}">'
            f'<div class="pg-row-z"><b>{zone}</b><i>{name}</i></div>'
            f'<div class="pg-row-m"><div class="pg-row-f" '
            f'style="width:{max(prob*100,2):.0f}%;background:'
            f'{CORAL if flag else (AMBER if prob>=.25 else TEAL)}"></div></div>'
            f'<div class="pg-row-p">{prob*100:.1f}%</div>'
            f'<div class="pg-row-t {"pg-t-hot" if flag else "pg-t-ok"}">'
            f'{"spike" if flag else "normal"}</div></div>'
            for zone, name, prob, flag in rows
        ),
        unsafe_allow_html=True,
    )


def empty(title: str, hint: str) -> None:
    st.markdown(
        f'<div class="pg-empty"><b>{title}</b><span>{hint}</span></div>',
        unsafe_allow_html=True,
    )

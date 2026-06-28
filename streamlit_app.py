#!/usr/bin/env python3
"""
Macro Risk Dashboard — Streamlit Version
=========================================
Deploy on Streamlit Cloud:
1. Put this file in a GitHub repo as app.py
2. Create requirements.txt with: requests yfinance streamlit
3. Connect repo to streamlit.io
"""

import io, csv, datetime
import requests
import yfinance as yf
import streamlit as st

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Macro Risk Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
body, .stApp { background-color: #0d1117 !important; color: #f1f5f9; }
.block-container { padding: 2rem 2rem 2rem 2rem; max-width: 1200px; }
.tile {
    border-radius: 12px; border: 1px solid;
    padding: 16px 18px; margin-bottom: 4px;
}
.tile-green  { background: #052e16; border-color: #166534; }
.tile-amber  { background: #422006; border-color: #92400e; }
.tile-red    { background: #2d0a0a; border-color: #991b1b; }
.tile-desc   { font-size: 10px; color: #64748b; font-family: monospace;
               text-transform: uppercase; letter-spacing: .08em; }
.tile-label  { font-size: 13px; font-weight: 600; color: #f1f5f9; margin-top: 2px; }
.tile-val    { font-size: 30px; font-weight: 800; font-family: monospace;
               color: #f8fafc; line-height: 1; margin: 10px 0 8px; }
.tile-note-green { color: #4ade80; font-size: 11px; }
.tile-note-amber { color: #fbbf24; font-size: 11px; }
.tile-note-red   { color: #f87171; font-size: 11px; }
.pill-green { background:#14532d; color:#86efac; border:1px solid #166534;
              border-radius:999px; padding:2px 10px; font-size:11px;
              font-weight:700; text-transform:uppercase; }
.pill-amber { background:#78350f; color:#fde68a; border:1px solid #92400e;
              border-radius:999px; padding:2px 10px; font-size:11px;
              font-weight:700; text-transform:uppercase; }
.pill-red   { background:#7f1d1d; color:#fca5a5; border:1px solid #991b1b;
              border-radius:999px; padding:2px 10px; font-size:11px;
              font-weight:700; text-transform:uppercase; }
.levels { display:flex; margin-top:10px; border-radius:6px;
          overflow:hidden; font-size:10px; font-family:monospace; }
.lvl { flex:1; text-align:center; padding:4px 2px; font-weight:700; }
.lvl-g  { background:#14532d; color:#86efac; }
.lvl-a  { background:#78350f; color:#fde68a; }
.lvl-r  { background:#7f1d1d; color:#fca5a5; }
.lvl-ag { background:#22c55e; color:#052e16; }
.lvl-aa { background:#f59e0b; color:#422006; }
.lvl-ar { background:#ef4444; color:#2d0a0a; }
.banner-green { background:#052e16; border:2px solid #166534;
                border-radius:14px; padding:16px 22px; }
.banner-amber { background:#422006; border:2px solid #92400e;
                border-radius:14px; padding:16px 22px; }
.banner-red   { background:#2d0a0a; border:2px solid #991b1b;
                border-radius:14px; padding:16px 22px; }
.banner-title-green { color:#4ade80; font-size:16px; font-weight:800;
                      font-family:monospace; letter-spacing:.1em; }
.banner-title-amber { color:#fbbf24; font-size:16px; font-weight:800;
                      font-family:monospace; letter-spacing:.1em; }
.banner-title-red   { color:#f87171; font-size:16px; font-weight:800;
                      font-family:monospace; letter-spacing:.1em; }
.banner-text { color:#cbd5e1; font-size:13px; line-height:1.65; margin-top:6px; }
.section-hdr { font-size:11px; color:#475569; font-family:monospace;
               text-transform:uppercase; letter-spacing:.14em;
               margin: 20px 0 8px; }
.analysis-box { background:#0f172a; border:1px solid #1e293b;
                border-radius:14px; padding:24px 28px; margin-top:8px; }
.analysis-hdr { font-size:13px; font-weight:700; color:#94a3b8;
                font-family:monospace; text-transform:uppercase;
                letter-spacing:.12em; margin-bottom:18px; }
.ind-block { margin-bottom:24px; padding-bottom:24px;
             border-bottom:1px solid #1e293b; }
.ind-title { font-size:14px; font-weight:700; color:#f1f5f9;
             margin-bottom:10px; }
.tag { display:inline-block; font-size:10px; font-weight:700;
       font-family:monospace; letter-spacing:.1em; color:#64748b;
       text-transform:uppercase; margin-right:6px; }
.tag-green { color:#4ade80; }
.tag-amber { color:#fbbf24; }
.tag-red   { color:#f87171; }
.ind-text  { font-size:13px; color:#cbd5e1; line-height:1.7;
             margin-bottom:8px; }
.action-box { background:#1e293b; border-radius:10px;
              padding:16px 20px; margin-top:16px; }
.action-title { font-size:12px; font-weight:700; color:#64748b;
                font-family:monospace; text-transform:uppercase;
                letter-spacing:.1em; margin-bottom:8px; }
.action-text { font-size:13px; color:#cbd5e1; line-height:1.6; }
h1 { color: #f8fafc !important; }
</style>
""", unsafe_allow_html=True)

# ── Fallback values ────────────────────────────────────────────────────────
FALLBACK = {
    "VIX": 18.9,  "VVIX": 91.0,  "SKEW": 145.0, "MOVE": 69.0,
    "FNG": 50,    "FNG_RATING": "Neutral",
    "US10Y": 4.40, "US2Y": 4.13, "T10Y2Y": 0.27, "HYOAS": 2.63,
    "HYG": 79.85, "LQD": 109.50, "DXY": 100.5,
}

# ── Data fetchers ──────────────────────────────────────────────────────────
def _fred_latest(series_id):
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + series_id
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    rows = list(csv.reader(io.StringIO(r.text)))
    for row in reversed(rows[1:]):
        if len(row) >= 2 and row[1] not in (".", "", "NaN"):
            return float(row[1])
    return None

def _yf_last(ticker):
    hist = yf.Ticker(ticker).history(period="5d")
    closes = hist["Close"].dropna() if len(hist) else []
    return float(closes.iloc[-1]) if len(closes) else None

def _fng_label(score):
    if score <= 24:  return "Extreme Fear"
    if score <= 44:  return "Fear"
    if score <= 55:  return "Neutral"
    if score <= 75:  return "Greed"
    return "Extreme Greed"

def _cnn_fng():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.cnn.com/markets/fear-and-greed",
        "Origin": "https://www.cnn.com",
    }
    for url in [
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/",
    ]:
        try:
            r = requests.get(url, headers=headers, timeout=25)
            r.raise_for_status()
            data = r.json()
            if "fear_and_greed" in data:
                fg = data["fear_and_greed"]
                score = round(float(fg["score"]))
                return score, str(fg.get("rating", _fng_label(score))).title()
            elif "score" in data:
                score = round(float(data["score"]))
                return score, str(data.get("rating", _fng_label(score))).title()
        except Exception:
            continue
    raise ValueError("All CNN endpoints failed")

def _safe(fn, *args):
    try:
        return fn(*args)
    except Exception as exc:
        st.warning(f"⚠ {fn.__name__}{args} → {exc}")
        return None

@st.cache_data(ttl=900)
def gather():
    d = dict(FALLBACK)
    for key, tkr in [("VIX","^VIX"),("VVIX","^VVIX"),("SKEW","^SKEW"),
                     ("MOVE","^MOVE"),("HYG","HYG"),("LQD","LQD"),("DXY","DX-Y.NYB")]:
        v = _safe(_yf_last, tkr)
        if v is not None:
            d[key] = round(v, 2)
    for key, sid in [("US10Y","DGS10"),("US2Y","DGS2"),
                     ("T10Y2Y","T10Y2Y"),("HYOAS","BAMLH0A0HYM2")]:
        v = _safe(_fred_latest, sid)
        if v is not None:
            d[key] = v
    fng = _safe(_cnn_fng)
    if fng:
        d["FNG"], d["FNG_RATING"] = fng
    d["HYG_LQD"] = round(d["HYG"] / d["LQD"], 3) if d.get("HYG") and d.get("LQD") else None
    return d

# ── Signal logic ───────────────────────────────────────────────────────────
def _band(v, lo, hi, a, b, c):
    if v < lo:  return (a, "green")
    if v <= hi: return (b, "amber")
    return (c, "red")

def sig_vix(v):   return _band(v,16,25,  "Calm",      "Elevated", "Stress")
def sig_vvix(v):  return _band(v,95,110, "Normal",    "Elevated", "Stress")
def sig_skew(v):  return _band(v,135,150,"Calm",      "Elevated", "Stress")
def sig_move(v):  return _band(v,90,130, "Contained", "Elevated", "Stress")
def sig_10y(v):   return _band(v,3.5,4.5,"Low",       "Firm",     "High")
def sig_2y(v):    return _band(v,3.5,4.5,"Low",       "Firm",     "High")
def sig_hyoas(v): return _band(v,3.5,5.0,"Tight",     "Widening", "Stressed")
def sig_dxy(v):   return _band(v,100,105,"Weak",      "Moderate", "Strong")

def sig_fng(score, rating=""):
    if score < 25:    cls = "red"
    elif score < 45:  cls = "amber"
    elif score <= 75: cls = "green"
    else:             cls = "amber"
    return (rating or _fng_label(score), cls)

def sig_2s10s(v):
    if v < 0:    return ("Inverted","red")
    if v < 0.20: return ("Flat",    "amber")
    return ("Normal","green")

def sig_ratio(hyoas):
    if hyoas < 3.5: return ("Stable","green")
    if hyoas < 5.0: return ("Soft",  "amber")
    return ("Weak","red")

# ── Level bands ────────────────────────────────────────────────────────────
LEVELS = {
    "VIX":              ("< 16  CALM",      "16–25  ELEVATED",   "> 25  STRESS"),
    "VVIX":             ("< 95  NORMAL",    "95–110  ELEVATED",  "> 110  STRESS"),
    "SKEW Index":       ("< 135  CALM",     "135–150  ELEVATED", "> 150  STRESS"),
    "MOVE Index":       ("< 90  CALM",      "90–130  ELEVATED",  "> 130  STRESS"),
    "Fear & Greed":     ("40–60  NEUTRAL",  "25–39 / 61–75",     "< 25 or > 75"),
    "10Y Treasury":     ("< 3.5%  LOW",     "3.5–4.5%  FIRM",    "> 4.5%  HIGH"),
    "2Y Treasury":      ("< 3.5%  LOW",     "3.5–4.5%  FIRM",    "> 4.5%  HIGH"),
    "2s10s Spread":     ("> 20bps  NORMAL", "0–20bps  FLAT",     "< 0  INVERTED"),
    "HY Credit Spread": ("< 3.5%  TIGHT",   "3.5–5%  WIDE",      "> 5%  STRESS"),
    "HYG / LQD":        ("> 0.75  STABLE",  "0.70–0.75  SOFT",   "< 0.70  WEAK"),
    "DXY":              ("< 100  WEAK",     "100–105  MODERATE", "> 105  STRONG"),
}

def levels_html(label, cls):
    b = LEVELS.get(label)
    if not b: return ""
    g, a, r = b
    gc = "lvl-ag" if cls=="green" else "lvl-g"
    ac = "lvl-aa" if cls=="amber" else "lvl-a"
    rc = "lvl-ar" if cls=="red"   else "lvl-r"
    return (f'<div class="levels">'
            f'<span class="lvl {gc}">{g}</span>'
            f'<span class="lvl {ac}">{a}</span>'
            f'<span class="lvl {rc}">{r}</span>'
            f'</div>')

def tile_html(label, desc, val, sig):
    pill_txt, cls = sig
    notes = {"green":"Benign — no stress signal",
             "amber":"Elevated — monitor closely",
             "red":  "Stress — risk-off signal"}
    dots  = {"green":"#22c55e","amber":"#f59e0b","red":"#ef4444"}
    return f"""
<div class="tile tile-{cls}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <div class="tile-desc">{desc}</div>
      <div class="tile-label">{label}</div>
    </div>
    <span style="width:9px;height:9px;border-radius:50%;
          background:{dots[cls]};display:inline-block;margin-top:3px"></span>
  </div>
  <div class="tile-val">{val}</div>
  <div class="tile-note-{cls}">{notes[cls]}
    <span class="pill-{cls}">{pill_txt}</span>
  </div>
  {levels_html(label, cls)}
</div>"""

# ── Analysis helpers ───────────────────────────────────────────────────────
def ind_block(sig, title, what, current, matters, watch):
    dots  = {"green":"#22c55e","amber":"#f59e0b","red":"#ef4444"}
    tc    = {"green":"tag-green","amber":"tag-amber","red":"tag-red"}
    return f"""
<div class="ind-block">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
    <span style="width:10px;height:10px;border-radius:50%;
          background:{dots[sig]};display:inline-block;flex-shrink:0"></span>
    <span class="ind-title">{title}</span>
  </div>
  <div class="ind-text"><span class="tag">WHAT IS IT</span>{what}</div>
  <div class="ind-text"><span class="tag {tc[sig]}">CURRENT LEVEL</span>{current}</div>
  <div class="ind-text"><span class="tag">WHY IT MATTERS</span>{matters}</div>
  <div class="ind-text"><span class="tag">WATCH FOR</span>{watch}</div>
</div>"""

def build_analysis(d):
    blocks = []

    # VIX
    v = d["VIX"]; s = sig_vix(v)[1]
    what    = "The VIX measures the market's 30-day implied volatility for the S&P 500 derived from options prices. It is the primary equity fear gauge. Key levels: below 16 = calm, 16–25 = moderate uncertainty, above 25 = elevated fear, above 35 = panic/crisis."
    if s=="green":
        cur = f"At {v:.1f}, VIX is in calm territory — the options market is not pricing significant near-term risk. Institutional players are not aggressively hedging portfolios. This is a permissive environment for swing trading."
        mat = "Low VIX means low cost of capital and low risk premiums — supportive for growth stock valuations. For your AI supply chain names (AAOI, MU, GLW, ONTO), a calm VIX environment means macro is not fighting your positions. Momentum and trend-following strategies work best when VIX is low and stable."
        wat = "Watch for VIX spiking above 20 intraday — often the first sign of institutional selling. Also beware VIX dropping below 12 — extreme complacency historically precedes sharp reversals as smart money distributes into calm."
    elif s=="amber":
        cur = f"At {v:.1f}, VIX is elevated — the market is nervous but not panicking. Options premiums are expensive meaning the market is actively pricing near-term downside risk."
        mat = "Elevated VIX compresses valuation multiples on growth stocks. Institutions reduce risk at this level creating selling pressure on high-beta names. New position entries carry higher risk and stops need to be wider."
        wat = "A VIX move above 25 escalates to red — reduce size before that happens. If VIX drops back below 18 the fear spike is fading. Watch VVIX alongside — if VVIX is also rising the fear is genuine."
    else:
        cur = f"At {v:.1f}, VIX is in stress territory — a risk-off environment. Historical context: above 30 accompanied the 2020 COVID crash (peak 85), 2022 rate shock (peak 38), and 2018 volatility event (peak 50)."
        mat = "Your AI supply chain positions are high-beta growth names — they will fall harder and faster than the broad market in a VIX stress event. AAOI and similar names can drop 15–30% in weeks during VIX spikes."
        wat = "Watch for VIX to peak and make a lower high — that double-top structure in VIX often marks the bottom in equities. Do not re-enter positions until VIX is convincingly declining and back below 25."
    blocks.append(ind_block(s, f"① VIX — Equity Fear Gauge ({v:.1f})", what, cur, mat, wat))

    # VVIX
    v = d["VVIX"]; s = sig_vvix(v)[1]
    what = "VVIX measures the volatility of VIX itself — the 'volatility of volatility'. It tells you how uncertain the market is about future volatility. Critically, VVIX almost always spikes BEFORE VIX spikes, making it one of the best leading indicators of incoming volatility. Normal range is 80–100."
    if s=="green":
        cur = f"At {v:.0f}, VVIX is calm — no panic buying of VIX options is occurring. Smart money is not quietly hedging behind the scenes. This confirms the risk-on environment is durable."
        mat = "When VVIX is calm alongside VIX it confirms the backdrop is genuinely stable. For your swing trades this means trend continuation setups have a higher probability of playing out cleanly without sudden volatility interruptions."
        wat = "The critical signal is VVIX rising sharply while VIX remains low — that divergence is the classic early warning of an impending spike. If VVIX breaks above 100 while VIX is still below 20, start reducing your most leveraged positions."
    elif s=="amber":
        cur = f"At {v:.0f}, VVIX is elevated — institutions are starting to buy protection on volatility itself. This is an early warning signal that should not be ignored even if VIX itself is still calm."
        mat = "This is one of the most important setups: VVIX leading VIX. When VVIX rises before VIX it gives you a 3–10 day window to reduce risk before the main volatility event hits. In SMC terms this is smart money accumulating short positions before the liquidity sweep."
        wat = "If VVIX continues rising above 110 that is a strong signal to cut position sizes. Watch whether VIX starts confirming — if both are rising the risk event is likely already beginning."
    else:
        cur = f"At {v:.0f}, VVIX is in stress territory — a major volatility event is either underway or imminent. At this level institutional hedging demand is extreme."
        mat = "Extreme VVIX means market makers are pulling liquidity from options markets — this creates conditions for gap moves and outsized single-day swings. Your SMC order blocks and FVGs will be violated aggressively."
        wat = "Do not attempt to buy dips until VVIX drops below 100. The market is in a disorderly state. VVIX declining from its peak is the first sign the volatility event is peaking."
    blocks.append(ind_block(s, f"② VVIX — Volatility of Volatility ({v:.0f})", what, cur, mat, wat))

    # SKEW
    v = d["SKEW"]; s = sig_skew(v)[1]
    what = "The CBOE SKEW Index measures the cost of buying far out-of-the-money put options — it prices the fear of a sudden large crash (black swan). Unlike VIX which measures general volatility, SKEW specifically measures tail risk. Normal range is 100–135. Values above 145 indicate elevated crash-fear."
    if s=="green":
        cur = f"At {v:.0f}, SKEW is in the normal range — the market is not pricing an imminent crash event. Demand for deep OTM put protection is modest."
        mat = "Low SKEW alongside low VIX is the most benign combination — both general fear and tail risk fear are absent. Momentum and trend-following strategies work best when SKEW is low because the return distribution is more normal rather than skewed to the downside."
        wat = "Watch for SKEW rising above 140 while VIX remains low — this is a sophisticated warning sign. It means large institutions are quietly buying crash protection even while the surface appears calm. This divergence often precedes 10–20% corrections."
    elif s=="amber":
        cur = f"At {v:.0f}, SKEW is moderately elevated — some institutional players are paying up for tail risk protection. Not alarming but worth noting. Often precedes volatility spikes by days to weeks."
        mat = "Elevated SKEW can persist for weeks before anything happens. However as a swing trader note it as a yellow flag. It often reflects macro uncertainty (Fed policy, geopolitical events) that has not yet translated into broad equity fear."
        wat = "If SKEW breaks above 150 alongside rising VVIX that is a powerful warning combination. Also watch if SKEW is rising while VIX is falling — that divergence historically resolves with VIX catching up."
    else:
        cur = f"At {v:.0f}, SKEW is at elevated levels — significant tail risk hedging is occurring. Large institutional money is paying a substantial premium for deep downside protection."
        mat = "Very high SKEW combined with elevated VIX and VVIX is one of the most dangerous combinations. Smart money has already positioned defensively. For your AI positions this suggests the risk/reward of holding full size is poor."
        wat = "Monitor whether SKEW is rising or falling from this level. Falling SKEW from extreme highs can actually be bullish — it means tail risk hedgers are unwinding protection. But if still rising stay defensive."
    blocks.append(ind_block(s, f"③ SKEW Index — Tail Risk / Crash Fear ({v:.0f})", what, cur, mat, wat))

    # MOVE
    v = d["MOVE"]; s = sig_move(v)[1]
    what = "The MOVE Index is the bond market equivalent of VIX — it measures expected volatility in US Treasury yields. High MOVE = high uncertainty about where interest rates are heading. Low MOVE = rates are stable and the Fed narrative is settled. Key levels: below 80 = calm, 80–120 = moderate, above 120 = stress. MOVE peaked at ~160 in 2022 during the most aggressive Fed hiking cycle in 40 years."
    if s=="green":
        cur = f"At {v:.0f}, MOVE is comfortably below 90 — bond market volatility is subdued. The market has a clear settled view on the interest rate path. Treasury auctions are going smoothly."
        mat = "MOVE directly impacts growth stock valuations through the discount rate mechanism. When rates are stable and MOVE is low, DCF models produce stable valuations for AI infrastructure stocks. Low MOVE is a direct tailwind for AAOI, MU, and ONTO."
        wat = "Any CPI print, Fed speech, or Treasury auction surprise can spike MOVE rapidly. A MOVE break above 100 is the first serious warning for growth stock holders. Watch MOVE rising ahead of key macro events."
    elif s=="amber":
        cur = f"At {v:.0f}, MOVE is elevated — the bond market is uncertain about the rate path. Options traders are paying up for rate protection. This typically happens around Fed meetings or major inflation prints."
        mat = "Elevated MOVE creates a challenging environment for growth stocks. Portfolio managers reduce duration risk — which means selling high-multiple growth stocks. Your AI supply chain names are particularly sensitive because they trade on future earnings that get discounted more aggressively."
        wat = "Watch whether MOVE is trending higher or has peaked. If rolling over from elevated levels that is constructive. Watch the 120 level as the line in the sand. Also watch the 10Y yield — if it is breaking key levels MOVE will follow."
    else:
        cur = f"At {v:.0f}, MOVE is in stress territory — this is a bond market crisis environment. Rate volatility of this magnitude was last seen during the 2022 Fed hiking cycle and the 2020 COVID liquidity crisis."
        mat = "Extreme MOVE is the most dangerous macro environment for long-duration growth stocks. Institutional investors are forced to hedge or reduce risk across all asset classes. Correlations go to 1 — everything falls together. AI supply chain stock valuations will be compressed dramatically."
        wat = "Do not add to any growth positions until MOVE drops below 120. Priority is capital preservation. Watch for MOVE to peak and make a lower high — that double-top structure often signals the bond crisis is peaking."
    blocks.append(ind_block(s, f"④ MOVE Index — Bond Market Volatility ({v:.0f})", what, cur, mat, wat))

    # Fear & Greed
    v = d["FNG"]; s = sig_fng(v, "")[1]; rating = d.get("FNG_RATING","")
    what = "The CNN Fear & Greed Index is a composite of 7 signals: market momentum, stock price strength, breadth, put/call ratio, junk bond demand, market volatility (VIX), and safe haven demand. It scores 0–100 where 0 = extreme fear and 100 = extreme greed. It is a contrarian indicator — extreme readings in either direction often signal reversals."
    if s=="green":
        cur = f"At {v} ({rating}), sentiment is in neutral territory — balanced between fear and greed. This is historically the most sustainable zone and where the most reliable technical setups occur."
        mat = "Neutral sentiment means the crowd is not making extreme bets in either direction reducing the risk of sudden sentiment-driven reversals. For your SMC framework this is ideal — order blocks and FVGs tend to hold more reliably when sentiment is balanced."
        wat = "Watch for the index moving toward extremes (below 25 or above 75). Extreme fear while your technicals show accumulation is a powerful buy signal. Extreme greed while holding positions is a signal to take partial profits and tighten stops."
    elif s=="amber" and v > 60:
        cur = f"At {v} ({rating}), greed is elevated — the retail crowd is becoming increasingly bullish. Momentum chasers are active and risk appetite is high. This is a contrarian warning signal."
        mat = "In SMC terms elevated greed is when smart money distributes — they sell accumulated positions into retail buying frenzy. This creates conditions for a liquidity sweep above recent highs followed by a reversal. Chasing breakouts at this level carries significant reversal risk."
        wat = "If index reaches above 80 (extreme greed) that is a strong signal to take profits on your strongest positions. Watch for a sudden spike down in the index from extreme greed — that rapid sentiment reversal often corresponds to the smart money liquidity grab."
    else:
        cur = f"At {v} ({rating}), fear is elevated — investors are nervous and risk aversion is rising. This level sees increased selling pressure as retail investors cut positions."
        mat = "Elevated fear creates the setup for SMC accumulation — smart money buys when retail is fearful. Watch for order blocks forming at key support levels. Fear-driven selling often overshoots fundamentals creating genuine value opportunities in quality AI names like MU and GLW."
        wat = "Watch for the index stabilising and turning back up from the 25–40 range — that reversal from fear often marks the start of a new leg higher. Combine with SMC confirmation (break of structure on the daily) before adding."
    blocks.append(ind_block(s, f"⑤ Fear & Greed Index ({v} — {rating})", what, cur, mat, wat))

    blocks.append('<hr style="border-color:#1e293b;margin:8px 0"/>')

    # 10Y
    v = d["US10Y"]; s = sig_10y(v)[1]
    what = "The US 10-Year Treasury yield is the benchmark for long-term borrowing costs globally and the risk-free rate used in virtually every asset valuation model. When 10Y rises growth stocks fall (higher discount rate = lower present value of future earnings). It is set by market forces not directly by the Fed."
    if s=="green":
        cur = f"At {v:.2f}%, the 10Y is in a benign range — not exerting significant downward pressure on equity valuations. The market is comfortable with the current rate level."
        mat = "For your AI supply chain positions the 10Y is crucial. Names like AAOI and ONTO are priced on future earnings that may be 2–4 years out. A lower 10Y means those future earnings are discounted less aggressively — supporting higher valuations today."
        wat = "Watch the 4.5% level closely — if 10Y breaks and holds above 4.5% it shifts to amber and multiple compression begins. Also watch the real yield (10Y minus inflation expectations) — that is what truly drives growth stock valuations."
    elif s=="amber":
        cur = f"At {v:.2f}%, the 10Y is at a firm level — equity valuations are under pressure. This level is high enough to make high-multiple growth stocks less attractive compared to holding Treasuries."
        mat = "At this rate level a stock trading at 40x forward earnings becomes harder to justify. Institutional models start flagging growth stocks as expensive relative to the risk-free rate. For AAOI specifically the elevated 10Y means the market will demand more earnings certainty."
        wat = "Watch the 5% level as the critical threshold. If 10Y approaches 5% start reducing your highest-multiple positions. Also watch for the 10Y to begin declining — that reversal is often the catalyst for a strong growth stock rally."
    else:
        cur = f"At {v:.2f}%, the 10Y is above 5% — a significant headwind for growth equities. This level makes Treasury bonds genuinely competitive with equities for the first time in over a decade."
        mat = "Above 5% the TINA (There Is No Alternative to stocks) trade breaks down. Institutional investors can earn 5%+ risk-free which dramatically raises the hurdle rate for owning volatile growth stocks. AI supply chain names priced for perfection will face severe multiple compression."
        wat = "The key question is: will the Fed pivot? Watch Fed communications closely. A credible pivot signal will cause the 10Y to drop sharply and trigger a major growth stock rally. Until then maintain defensive positioning."
    blocks.append(ind_block(s, f"⑥ 10Y Treasury Yield ({v:.2f}%)", what, cur, mat, wat))

    # 2Y
    v = d["US2Y"]; s = sig_2y(v)[1]
    what = "The US 2-Year Treasury yield is the most sensitive indicator of Fed policy expectations. Unlike the 10Y which reflects long-term views, the 2Y is almost entirely driven by expectations of where the Fed funds rate will be over the next 2 years. When the 2Y is falling the market is pricing in rate cuts — historically very bullish for risk assets."
    if s=="green":
        cur = f"At {v:.2f}%, the 2Y is low — the market is pricing a relatively dovish Fed outlook. Rate cuts are either already priced in or the market believes the Fed is close to cutting."
        mat = "When the 2Y is falling monetary conditions are loosening — access to capital becomes cheaper for growth companies. Historically the best periods for AI and tech stocks have coincided with declining 2Y yields. This is currently a tailwind for your entire AI supply chain portfolio."
        wat = "Watch for the 2Y to start rising again — that signals the market is re-pricing the Fed as more hawkish. Any hot inflation data or strong jobs report can cause the 2Y to spike quickly. A 2Y move above 4% is the first caution signal."
    elif s=="amber":
        cur = f"At {v:.2f}%, the 2Y is elevated — the Fed is still restrictive and the market is not pricing imminent rate cuts. The cost of capital for growth companies remains high."
        mat = "An elevated 2Y is a headwind but not a crisis for growth stocks. The key is direction: if the 2Y is declining from these levels that is constructive even if the absolute level is still high. Rate of change matters more than the level."
        wat = "Watch Fed meeting outcomes and CPI prints closely — these are the primary drivers of 2Y moves. A surprise rate cut or series of soft inflation prints will bring the 2Y down quickly and provide a strong catalyst for growth stock re-rating."
    else:
        cur = f"At {v:.2f}%, the 2Y above 5% signals the market expects the Fed to remain extremely restrictive for an extended period. The most challenging environment for growth stock investing."
        mat = "At 5%+ on the 2Y you are competing against a risk-free 5% return every time you hold a volatile growth stock. The risk premium demanded by investors for owning AI supply chain names increases substantially."
        wat = "A 2Y above 5% historically either leads to a Fed pivot (bullish) or a credit event (bearish). Watch for cracks in the corporate credit market — widening HY spreads alongside a high 2Y is the most dangerous combination."
    blocks.append(ind_block(s, f"⑦ 2Y Treasury Yield ({v:.2f}%)", what, cur, mat, wat))

    # 2s10s
    v = d["T10Y2Y"]; s = sig_2s10s(v)[1]; bps = round(v*100)
    what = "The 2s10s spread is the difference between 10Y and 2Y yields in basis points (1bp = 0.01%). A positive spread (normal curve) means long rates are higher than short rates — the healthy condition. A negative spread (inverted curve) means short rates exceed long rates — one of the most reliable recession predictors in history. Every US recession since 1955 was preceded by inversion. The dangerous zone is actually right AFTER inversion ends — the un-inversion often marks the start of the actual recession."
    if s=="green":
        cur = f"At {bps:+d} bps, the yield curve is positively sloped — the normal healthy configuration. Long-term rates are appropriately higher than short-term rates reflecting confidence in future economic growth."
        mat = "A positive yield curve means banks can borrow short and lend long profitably — this supports credit creation and economic activity. For your AI supply chain names a positive curve is supportive because it reflects market confidence in sustained economic growth which drives enterprise tech spending."
        wat = "Watch for the curve flattening toward 0 bps — that is the first warning. Inversion starts with the short end rising faster than the long end as the Fed hikes rates. If 2s10s drops below 25 bps start paying close attention."
    elif s=="amber":
        cur = f"At {bps:+d} bps, the yield curve is flat or very slightly positive — the transitional zone coming out of inversion. Research shows recession risk peaks not during inversion but in the 6–18 months AFTER the curve un-inverts."
        mat = "The transition from inverted back to flat/positive has historically coincided with the actual onset of recession. The un-inversion typically happens as the Fed starts cutting rates in response to economic weakness — meaning the damage is already done."
        wat = "Watch the reason for the un-inversion: is the 10Y rising (growth expectations improving — bullish) or is the 2Y falling (Fed cutting due to weakness — potentially bearish near-term). The mechanism matters enormously."
    else:
        cur = f"At {bps:+d} bps, the yield curve is inverted — short rates exceed long rates. This configuration has preceded every US recession since 1955. The market is signalling that current Fed policy is too tight."
        mat = "Yield curve inversion does not mean an immediate recession — the average lead time is 12–18 months. However it means: credit conditions are tightening, bank lending profitability is squeezed, and corporate financing costs are elevated — all headwinds for AI infrastructure spending."
        wat = "Watch the depth of inversion — deeper inversion historically correlates with more severe recessions. Also watch for the un-inversion signal which paradoxically is often when you should become most cautious about equities."
    blocks.append(ind_block(s, f"⑧ 2s10s Yield Curve ({bps:+d} bps)", what, cur, mat, wat))

    # HY Spread
    v = d["HYOAS"]; s = sig_hyoas(v)[1]
    what = "The High Yield OAS (BAMLH0A0HYM2) measures the extra yield that junk-rated corporate bond issuers must pay over equivalent Treasuries. When lenders are confident they demand less extra yield (tight spreads). When worried about defaults they demand more (wide spreads). Credit markets often lead equity markets because bond investors are more sophisticated and have access to better fundamental information. KEY LEVELS: below 3.5% = tight/benign, 3.5–5% = widening/caution, above 5% = stress."
    if s=="green":
        cur = f"At {v:.2f}%, HY spreads are near historic lows — lenders are highly confident and demanding minimal risk premium. A green light from credit markets. Corporate balance sheets are healthy and access to capital is easy and cheap."
        mat = "Tight HY spreads are one of the most bullish macro signals for risk assets. For your AI supply chain positions it means companies have easy access to debt financing for capital expenditure — critical for the massive data centre buildout driving demand for AAOI optical networking, MU memory, and GLW fibre."
        wat = "The concern with extremely tight spreads is complacency — limited room for further compression but significant room for widening. Watch for HY spreads moving above 3.5% as the first alert. Any sudden widening above 4% would be a significant warning requiring immediate review of position sizes."
    elif s=="amber":
        cur = f"At {v:.2f}%, HY spreads are widening — credit markets are starting to price risk. Lenders are demanding more compensation for the possibility of default. This is an early warning signal."
        mat = "Widening HY spreads historically lead equity market corrections by 4–8 weeks. Bond investors see corporate fundamentals first and move to protect themselves before equity investors react. This is the time to start tightening stops and avoiding new leveraged positions."
        wat = "The 4.5% level is your key threshold — if spreads break above 4.5% and continue widening that is a firm signal to reduce exposure to your most speculative AI supply chain names. Watch HYG/LQD ratio alongside — if both are confirming the stress signal it is more reliable."
    else:
        cur = f"At {v:.2f}%, HY spreads are in stress territory — credit markets are pricing meaningful default risk. This level has historically been associated with economic recessions, credit crises, or major equity bear markets."
        mat = "Wide HY spreads mean the cost of capital for leveraged companies has spiked. Companies relying on debt financing for growth face significantly higher borrowing costs. More importantly wide spreads signal institutional risk appetite has collapsed and forced selling is likely occurring."
        wat = "Watch for HY spreads to peak and begin narrowing — that is typically the signal that the credit stress event is resolving. The peak in HY spreads often marks the trough in equity markets. Do not add risk until spreads are convincingly tightening from their highs."
    blocks.append(ind_block(s, f"⑨ HY Credit Spread ({v:.2f}%)", what, cur, mat, wat))

    # HYG/LQD
    ratio = d.get("HYG_LQD"); sr = sig_ratio(d["HYOAS"])[1]
    rtxt = f"{ratio:.3f}" if ratio else "n/a"
    what = "The HYG/LQD ratio compares high yield corporate bonds (HYG ETF) vs investment grade bonds (LQD ETF). When rising HY is outperforming IG — risk-on. When falling HY is underperforming IG — risk-off. It is a real-time credit stress proxy that moves faster than FRED spread data. A declining HYG/LQD ratio often precedes equity market weakness by days to weeks."
    cur  = f"At {rtxt}, the ratio {'is stable above 0.75 confirming risk-on credit conditions' if sr=='green' else 'is showing mild stress — HY underperforming IG' if sr=='amber' else 'is showing significant stress — HY materially underperforming IG'}."
    mat  = "The HYG/LQD ratio is most useful as a real-time momentum indicator for credit conditions. A steadily declining ratio over multiple weeks is a powerful warning signal even before it reaches extreme levels — the trend matters as much as the level. For your AI supply chain positions a declining ratio means institutional risk appetite is shrinking and liquidity in your stocks will deteriorate."
    wat  = "Watch for the ratio to break below its 20-day moving average — that is often the first actionable signal. Also watch for divergence: if equities are making new highs but HYG/LQD is declining that is a classic warning that the equity rally lacks credit support."
    blocks.append(ind_block(sr, f"⑩ HYG/LQD Ratio ({rtxt})", what, cur, mat, wat))

    # DXY
    v = d["DXY"]; s = sig_dxy(v)[1]
    what = "The DXY measures the US dollar against a basket of 6 major currencies (EUR 57.6%, JPY 13.6%, GBP 11.9%, CAD 9.1%, SEK 4.2%, CHF 3.6%). A rising DXY tightens global financial conditions, increases dollar-denominated debt service costs worldwide, and typically pressures risk assets. A falling DXY means looser financial conditions and is historically bullish for equities and commodities."
    if s=="green":
        cur = f"At {v:.1f}, the DXY is weak — the dollar is not exerting tightening pressure on global financial conditions. This is typically associated with an accommodative Fed stance and strong global risk appetite."
        mat = "A weak dollar is constructive for your AI supply chain holdings in several ways: global financial conditions are loose, many AI names have significant international revenue (semiconductor sales to Asian data centres, optical networking to European carriers), and it reduces refinancing stress on EM companies that are major buyers of US tech components."
        wat = "Watch for the DXY to start strengthening above 102. A rising dollar combined with rising rates is a toxic combination for risk assets. The DXY often moves inversely to risk appetite — if you see DXY spiking up check your other risk indicators simultaneously."
    elif s=="amber":
        cur = f"At {v:.1f}, the DXY is showing moderate strength — financial conditions are tightening at the margins. This level of dollar strength creates headwinds but is not yet at levels that historically cause major market dislocations."
        mat = "Moderate dollar strength squeezes international earnings of US multinationals, increases debt service costs for EM dollar borrowers, and signals that global liquidity conditions are tightening. For your AI names watch companies with significant Asian manufacturing or sales exposure more carefully."
        wat = "Watch the 106 level as the key threshold. DXY above 106 has historically been associated with significant stress in EM economies and risk asset selloffs. Also watch for DXY strength coinciding with rising MOVE — that combination signals a global tightening cycle particularly dangerous for growth stocks."
    else:
        cur = f"At {v:.1f}, the DXY is strong — global financial conditions are tight. This level of dollar strength is a significant headwind for risk assets worldwide. Historically DXY above 106-110 has been associated with EM currency crises, commodity price collapses, and broad risk asset selloffs."
        mat = "A very strong dollar creates a negative feedback loop: it raises the real cost of dollar debt globally, forcing asset sales to service obligations, which pressures all risk assets further. For AI supply chain names it reduces demand from international customers facing higher dollar-denominated prices for US-made semiconductors and networking equipment."
        wat = "Watch for the Fed to signal concern about dollar strength — that is often the catalyst for a reversal. Also watch for DXY to make a lower high from extreme levels — that technical reversal often marks the start of a risk-on recovery."
    blocks.append(ind_block(s, f"⑪ DXY — US Dollar Index ({v:.1f})", what, cur, mat, wat))

    # Action box
    all_sigs = [sig_vix(d["VIX"])[1], sig_vvix(d["VVIX"])[1], sig_skew(d["SKEW"])[1],
                sig_move(d["MOVE"])[1], sig_fng(d["FNG"],"")[1], sig_10y(d["US10Y"])[1],
                sig_2y(d["US2Y"])[1], sig_2s10s(d["T10Y2Y"])[1],
                sig_hyoas(d["HYOAS"])[1], sig_dxy(d["DXY"])[1]]
    reds   = all_sigs.count("red")
    ambers = all_sigs.count("amber")
    overall = "red" if reds>=2 else "amber" if (reds>=1 or ambers>=3) else "green"

    actions = {
        "green": ("Risk-On — Constructive Environment",
                  "All major risk gauges are in the green or at worst amber. This is a permissive environment "
                  "for holding and building AI supply chain positions. Continue to hold AAOI, MU, GLW, and ONTO "
                  "with defined stops. New entries on SMC setups (order block retests, FVG fills) are reasonable. "
                  "Stay alert to any sudden MOVE or VIX spike as the first sign of regime change."),
        "amber": ("Caution — Mixed Signals",
                  "The macro picture is mixed. Not a risk-off emergency but not a green light to add aggressively. "
                  "Hold existing AI supply chain positions but tighten stops to recent structure lows. "
                  "Avoid adding new full-size positions until signals clarify. Focus on which indicators are amber — "
                  "if MOVE and HY spread are both elevated that is more serious than elevated SKEW alone."),
        "red":   ("Risk-Off — Elevated Danger",
                  "Multiple indicators are in the red simultaneously — this is a macro stress environment. "
                  "Consider reducing position sizes on AI supply chain names especially high-beta names like AAOI. "
                  "Do not add new positions. Raise cash reserves. "
                  "Wait for HY spreads to tighten back below 4% and VIX to drop below 20 "
                  "before re-engaging with conviction. Patience is the edge here."),
    }
    atitle, atext = actions[overall]
    action = f'<div class="action-box"><div class="action-title">⚡ Trader Action — {atitle}</div><div class="action-text">{atext}</div></div>'

    return f"""
<div class="analysis-box">
  <div class="analysis-hdr">📊 Indicator Analysis — What Each Level Means Today</div>
  {''.join(blocks)}
  {action}
</div>"""

# ── Main app ───────────────────────────────────────────────────────────────
def main():
    st.markdown('<h1 style="color:#f8fafc;font-size:28px;font-weight:800">📊 Daily Macro Risk Dashboard</h1>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:12px;color:#64748b;font-family:monospace;margin-bottom:20px">Cross-Asset Risk Monitor · {datetime.date.today().strftime("%B %d, %Y")} · AI Supply Chain Focus</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 5])
    with col1:
        refresh = st.button("🔄 Refresh Data", use_container_width=True)
    with col2:
        st.markdown('<div style="font-size:11px;color:#475569;padding-top:10px;font-family:monospace">Data auto-caches for 15 minutes. Click Refresh to force update.</div>', unsafe_allow_html=True)

    if refresh:
        st.cache_data.clear()

    with st.spinner("Fetching live market data..."):
        d = gather()

    # ── Overall banner ────────────────────────────────────────────────────
    fng_sig   = sig_fng(d["FNG"], d.get("FNG_RATING","-"))
    all_sigs  = [sig_vix(d["VIX"])[1], sig_vvix(d["VVIX"])[1], sig_skew(d["SKEW"])[1],
                 sig_move(d["MOVE"])[1], fng_sig[1], sig_10y(d["US10Y"])[1],
                 sig_2y(d["US2Y"])[1], sig_2s10s(d["T10Y2Y"])[1],
                 sig_hyoas(d["HYOAS"])[1], sig_dxy(d["DXY"])[1]]
    reds      = all_sigs.count("red")
    ambers    = all_sigs.count("amber")
    overall   = "red" if reds>=2 else "amber" if (reds>=1 or ambers>=3) else "green"

    BANNER_LABELS = {"green":"🟢 RISK ON","amber":"🟡 CAUTION","red":"🔴 RISK OFF"}
    summaries = {
        "green": "Macro backdrop is constructive — credit spreads, bond vol, and equity vol all subdued. Supportive for AI supply chain positions. No SMC red flags from macro indicators.",
        "amber": "Mixed signals across indicators. Caution warranted — consider tightening stops on high-beta AI supply chain names. Monitor HY spreads and MOVE closely.",
        "red":   "Multiple risk indicators elevated simultaneously. Consider reducing exposure. Wait for macro conditions to stabilise before adding to positions.",
    }
    st.markdown(f"""
<div class="banner-{overall}">
  <div class="banner-title-{overall}">{BANNER_LABELS[overall]}</div>
  <div class="banner-text">{summaries[overall]}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Volatility & Sentiment ────────────────────────────────────────────
    st.markdown('<div class="section-hdr">Volatility & Sentiment</div>', unsafe_allow_html=True)
    ratio = d.get("HYG_LQD")
    ratio_txt = f"{ratio:.3f}" if ratio else "n/a"

    c1,c2,c3,c4,c5 = st.columns(5)
    for col, label, desc, val, sig in [
        (c1,"VIX",          "Equity implied volatility",  f"{d['VIX']:.1f}",   sig_vix(d["VIX"])),
        (c2,"VVIX",         "Volatility of volatility",   f"{d['VVIX']:.0f}",  sig_vvix(d["VVIX"])),
        (c3,"SKEW Index",   "Tail risk / black swan",     f"{d['SKEW']:.0f}",  sig_skew(d["SKEW"])),
        (c4,"MOVE Index",   "Bond market volatility",     f"{d['MOVE']:.0f}",  sig_move(d["MOVE"])),
        (c5,"Fear & Greed", "CNN sentiment (0–100)",      f"{d['FNG']}",       fng_sig),
    ]:
        with col:
            st.markdown(tile_html(label, desc, val, sig), unsafe_allow_html=True)

    # ── Rates, Curve & Credit ─────────────────────────────────────────────
    st.markdown('<div class="section-hdr">Rates, Curve & Credit</div>', unsafe_allow_html=True)

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    fmt_bps = lambda v: f"{round(v*100):+d} bps"
    for col, label, desc, val, sig in [
        (c1,"10Y Treasury",     "Long-term rate environment",    f"{d['US10Y']:.2f}%",  sig_10y(d["US10Y"])),
        (c2,"2Y Treasury",      "Fed expectations / short end",  f"{d['US2Y']:.2f}%",   sig_2y(d["US2Y"])),
        (c3,"2s10s Spread",     "Yield curve · inversion=risk",  fmt_bps(d["T10Y2Y"]),  sig_2s10s(d["T10Y2Y"])),
        (c4,"HY Credit Spread", "BAMLH0A0HYM2 · lenders spread", f"{d['HYOAS']:.2f}%",  sig_hyoas(d["HYOAS"])),
        (c5,"HYG / LQD",        "Credit stress proxy",           ratio_txt,              sig_ratio(d["HYOAS"])),
        (c6,"DXY",              "US Dollar Index",               f"{d['DXY']:.1f}",      sig_dxy(d["DXY"])),
    ]:
        with col:
            st.markdown(tile_html(label, desc, val, sig), unsafe_allow_html=True)

    # ── Analysis ──────────────────────────────────────────────────────────
    st.markdown("")
    with st.expander("📊 Full Indicator Analysis — Click to expand", expanded=False):
        st.markdown(build_analysis(d), unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────
    st.markdown("""
<div style="font-size:11px;color:#334155;font-family:monospace;margin-top:24px;
     padding-top:16px;border-top:1px solid #1e293b;text-align:center">
VIX · VVIX · SKEW · MOVE · HYG · LQD · DXY via Yahoo Finance &nbsp;·&nbsp;
10Y · 2Y · HY Spread via FRED &nbsp;·&nbsp;
Fear & Greed via CNN &nbsp;·&nbsp;
Educational only — not financial advice
</div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

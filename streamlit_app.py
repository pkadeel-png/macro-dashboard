# ── "What should I do" summary ─────────────────────────────────────────────
# Level at which each RED indicator drops back to amber (used for "what flips it")
EASE_LEVELS = {
    "VIX": ("below", 25), "VVIX": ("below", 110), "SKEW": ("below", 150),
    "MOVE": ("below", 130), "10Y": ("below", 4.5), "2Y": ("below", 4.5),
    "HY spread": ("below", 5.0), "DXY": ("below", 105),
}

POSTURES = {
    0: ("green", "🟢 BUILD / HOLD",
        "Macro is supportive. Stay invested and add selectively.",
        [("Positions", "Hold your AI supply chain names with defined stops."),
         ("New entries", "Valid SMC setups (order block retest, FVG fill) are fine at normal size, with a 2:1 R:R minimum."),
         ("Stops", "Keep stops at structure lows. No need to widen or tighten."),
         ("Watch", "A sudden MOVE or VIX spike is the first sign of regime change.")]),
    1: ("amber", "🟡 HOLD & TIGHTEN",
        "Mixed signals. Protect what you have, don't add aggressively.",
        [("Positions", "Hold existing positions but trim any that are extended or lack relative strength."),
         ("New entries", "Half size at most, and only on clean setups with at least 2:1 R:R."),
         ("Stops", "Tighten stops to the most recent structure lows."),
         ("Watch", "Whether the amber indicators are improving or sliding toward red.")]),
    2: ("red", "🔴 DE-RISK",
        "Multiple stress signals. Capital preservation comes first.",
        [("Positions", "Reduce size, starting with the highest-beta names (e.g. AAOI). Raise cash."),
         ("New entries", "None. Don't try to catch dips until volatility and credit stabilise."),
         ("Stops", "Honour them. Do not widen stops to avoid being taken out."),
         ("Watch", "VIX and HY spreads peaking and turning lower, which is the signal to start re-engaging.")]),
}

def build_action_summary(d, trufl_trend):
    checks = [
        ("VIX",       f"{d['VIX']:.1f}",       sig_vix(d["VIX"])),
        ("VVIX",      f"{d['VVIX']:.0f}",      sig_vvix(d["VVIX"])),
        ("SKEW",      f"{d['SKEW']:.0f}",      sig_skew(d["SKEW"])),
        ("MOVE",      f"{d['MOVE']:.0f}",      sig_move(d["MOVE"])),
        ("Fear & Greed", f"{d['FNG']}",        sig_fng(d["FNG"], d.get("FNG_RATING", ""))),
        ("10Y",       f"{d['US10Y']:.2f}%",    sig_10y(d["US10Y"])),
        ("2Y",        f"{d['US2Y']:.2f}%",     sig_2y(d["US2Y"])),
        ("2s10s",     f"{round(d['T10Y2Y']*100):+d} bps", sig_2s10s(d["T10Y2Y"])),
        ("HY spread", f"{d['HYOAS']:.2f}%",    sig_hyoas(d["HYOAS"])),
        ("DXY",       f"{d['DXY']:.1f}",       sig_dxy(d["DXY"])),
    ]
    reds   = sum(1 for _, _, s in checks if s[1] == "red")
    ambers = sum(1 for _, _, s in checks if s[1] == "amber")
    level  = 2 if reds >= 2 else 1 if (reds >= 1 or ambers >= 3) else 0

    # Inflation can push the call one notch more defensive
    reg_cls, reg_title, _ = inflation_regime(d["CORE_CPI"], trufl_trend)
    if reg_cls == "red":
        level = min(2, level + 1)

    cls, title, headline, actions = POSTURES[level]

    # Drivers: everything not green, red first
    extra = [("Core CPI", f"{d['CORE_CPI']:.1f}%", sig_core(d["CORE_CPI"])),
             ("CPI",      f"{d['CPI']:.1f}%",      sig_cpi(d["CPI"]))]
    drivers = [c for c in checks + extra if c[2][1] != "green"]
    drivers.sort(key=lambda c: 0 if c[2][1] == "red" else 1)
    dot = {"red": "🔴", "amber": "🟡"}
    if drivers:
        driver_html = " &nbsp;·&nbsp; ".join(
            f"{dot[s[1]]} {n} {v} ({s[0]})" for n, v, s in drivers)
    else:
        driver_html = "🟢 No indicators in stress or elevated territory."

    # What flips it
    flips = []
    for n, v, s in checks:
        if s[1] == "red" and n in EASE_LEVELS:
            direction, lvl = EASE_LEVELS[n]
            flips.append(f"{n} back {direction} {lvl}")
    if sig_fng(d["FNG"], "")[1] == "red":
        flips.append("Fear & Greed back above 25")
    if sig_2s10s(d["T10Y2Y"])[1] == "red":
        flips.append("2s10s curve back above 0 bps")
    if reg_cls == "red":
        flips.append("Truflation peaking and rolling over")
    flip_html = ("To ease: " + "; ".join(flips) + ".") if flips else \
        "Downgrade trigger: any red indicator, or 3+ ambers."

    rows = "".join(
        f'<div class="ind-text"><span class="tag tag-{cls}">{lbl}</span>{txt}</div>'
        for lbl, txt in actions)

    return f"""
<div class="banner-{cls}" style="margin-bottom:6px">
  <div class="banner-title-{cls}">⚡ WHAT TO DO NOW — {title}</div>
  <div class="banner-text" style="font-weight:600;color:#f1f5f9">{headline}</div>
  <div style="margin-top:12px">{rows}</div>
  <div class="banner-text" style="margin-top:10px;font-size:12px"><b>Driving this call:</b> {driver_html}</div>
  <div class="banner-text" style="font-size:12px"><b>Inflation regime:</b> {reg_title}</div>
  <div class="banner-text" style="font-size:12px">{flip_html}</div>
</div>"""

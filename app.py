import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="Alpha Terminal Pro V3",
    page_icon="⚡",
    layout="wide"
)

# -----------------------------
# CSS
# -----------------------------
st.markdown("""
<style>
    .main { background-color: #0b0f19; }
    .stApp { background-color: #0b0f19; color: #f8fafc; }

    .macro-card, .signal-card {
        background-color: #131b2e;
        border: 1px solid #233252;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.35);
    }

    .macro-title {
        color: #38bdf8 !important;
        font-size: 14px !important;
        font-weight: 700 !important;
    }

    .macro-val {
        color: #ffffff !important;
        font-size: 24px !important;
        font-weight: 800 !important;
        font-family: monospace;
    }

    .up-green { color: #4ade80 !important; font-weight: bold; }
    .down-red { color: #f87171 !important; font-weight: bold; }

    .status-banner {
        padding: 16px;
        border-radius: 10px;
        font-size: 18px;
        font-weight: 800;
        text-align: center;
    }

    .bullish-bg {
        background: #064e3b;
        color: #6ee7b7;
        border: 1px solid #059669;
    }

    .bearish-bg {
        background: #881337;
        color: #fecdd3;
        border: 1px solid #e11d48;
    }

    .neutral-bg {
        background: #78350f;
        color: #fef08a;
        border: 1px solid #d97706;
    }

    .buy { color: #4ade80; font-weight: 800; }
    .sell { color: #f87171; font-weight: 800; }
    .wait { color: #facc15; font-weight: 800; }

    div[data-testid="stRadio"] > label {
        color: #38bdf8 !important;
        font-size: 16px !important;
        font-weight: 700 !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label {
        background-color: #131b2e !important;
        padding: 6px 14px !important;
        border-radius: 8px !important;
        border: 1px solid #233252 !important;
        margin-right: 10px !important;
    }

    @media (max-width: 768px) {
        .macro-val { font-size: 20px !important; }
        .status-banner { font-size: 15px; padding: 12px; }
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
h1, h2 = st.columns([3, 1])
with h1:
    st.markdown(
        "<h1 style='color:#38bdf8;margin:0;'>⚡ ALPHA TERMINAL PRO V3</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color:#94a3b8;font-size:14px;margin:0;'>सोप्या भाषेत — आज काय घ्यायचं, काय विकायचं आणि कधी थांबायचं</p>",
        unsafe_allow_html=True
    )
with h2:
    current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    st.markdown(
        f"<div style='text-align:right;'>🟢 <b style='color:#22c55e;'>LIVE</b>"
        f"<br><span style='color:#94a3b8;font-size:12px;'>{current_time}</span></div>",
        unsafe_allow_html=True
    )

st.write("---")

# -----------------------------
# DATA FUNCTIONS
# -----------------------------
@st.cache_data(ttl=120)
def get_market_data(ticker):
    try:
        df = yf.Ticker(ticker).history(period="5d", interval="1d")
        if len(df) >= 2:
            prev_close = float(df["Close"].iloc[-2])
            current = float(df["Close"].iloc[-1])
            pct = ((current - prev_close) / prev_close) * 100
            return round(current, 2), round(pct, 2)
        elif len(df) == 1:
            return round(float(df["Close"].iloc[-1]), 2), 0.0
    except Exception:
        pass
    return 0.0, 0.0


@st.cache_data(ttl=120)
def get_intraday_data(ticker):
    try:
        df = yf.download(
            ticker,
            period="5d",
            interval="5m",
            progress=False,
            auto_adjust=False,
            threads=False
        )

        if df.empty:
            return pd.DataFrame()

        # Handle yfinance MultiIndex output
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        needed = ["Open", "High", "Low", "Close", "Volume"]
        if any(c not in df.columns for c in needed):
            return pd.DataFrame()

        df = df.dropna(subset=["Open", "High", "Low", "Close"]).copy()

        # Technical indicators
        df["EMA9"] = df["Close"].ewm(span=9, adjust=False).mean()
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()

        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df["RSI"] = 100 - (100 / (1 + rs))

        typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
        session_date = pd.Series(df.index.date, index=df.index)

        pv = typical_price * df["Volume"]
        df["CumPV"] = pv.groupby(session_date).cumsum()
        df["CumVol"] = df["Volume"].groupby(session_date).cumsum()
        df["VWAP"] = df["CumPV"] / df["CumVol"].replace(0, np.nan)

        df["VolAvg20"] = df["Volume"].rolling(20).mean()

        tr1 = df["High"] - df["Low"]
        tr2 = (df["High"] - df["Close"].shift()).abs()
        tr3 = (df["Low"] - df["Close"].shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["ATR14"] = tr.rolling(14).mean()

        return df
    except Exception:
        return pd.DataFrame()


def safe_float(v, default=0.0):
    try:
        if pd.isna(v):
            return default
        return float(v)
    except Exception:
        return default


def draw_card(label, val, chg, reverse=False):
    up = chg >= 0
    css = ("down-red" if up else "up-green") if reverse else ("up-green" if up else "down-red")
    symbol = "↑" if up else "↓"
    return f"""
    <div class="macro-card">
        <div class="macro-title">{label}</div>
        <div class="macro-val">{val}</div>
        <div class="{css}">{symbol} {chg:.2f}%</div>
    </div>
    """


def analyze_stock(name, ticker, market_mood):
    df = get_intraday_data(ticker)

    if df.empty or len(df) < 25:
        p, c = get_market_data(ticker)
        return {
            "name": name, "ticker": ticker, "price": p, "change": c,
            "signal": "WAIT", "confidence": 0, "score": 0,
            "entry": p, "sl": p, "t1": p, "t2": p, "rr": 0,
            "rsi": 0, "vwap": 0, "ema9": 0, "ema20": 0,
            "vol_ratio": 0, "reason": "Insufficient intraday data",
            "trend": "NO DATA"
        }

    x = df.iloc[-1]
    prev = df.iloc[-2]

    price = safe_float(x["Close"])
    ema9 = safe_float(x["EMA9"])
    ema20 = safe_float(x["EMA20"])
    rsi = safe_float(x["RSI"], 50)
    vwap = safe_float(x["VWAP"])
    atr = safe_float(x["ATR14"], max(price * 0.005, 0.1))
    volume = safe_float(x["Volume"])
    vol_avg = safe_float(x["VolAvg20"])
    vol_ratio = (volume / vol_avg) if vol_avg > 0 else 0

    day_open = safe_float(df.iloc[-1]["Open"])
    pct = ((price - day_open) / day_open * 100) if day_open else 0

    score = 0
    reasons = []

    # Market mood contribution
    if market_mood == "BULLISH":
        score += 1
        reasons.append("Market bullish")
    elif market_mood == "BEARISH":
        score -= 1
        reasons.append("Market bearish")

    # VWAP
    if price > vwap:
        score += 2
        reasons.append("Above VWAP")
    elif price < vwap:
        score -= 2
        reasons.append("Below VWAP")

    # EMA trend
    if ema9 > ema20:
        score += 2
        reasons.append("EMA9 > EMA20")
    elif ema9 < ema20:
        score -= 2
        reasons.append("EMA9 < EMA20")

    # Momentum RSI
    if 55 <= rsi <= 72:
        score += 1
        reasons.append("RSI bullish")
    elif 28 <= rsi <= 45:
        score -= 1
        reasons.append("RSI bearish")
    elif rsi > 78:
        score -= 1
        reasons.append("RSI overbought")
    elif rsi < 22:
        score += 1
        reasons.append("RSI oversold")

    # Volume confirmation
    if vol_ratio >= 1.5:
        if price > safe_float(prev["Close"]):
            score += 2
            reasons.append("Strong buying volume")
        elif price < safe_float(prev["Close"]):
            score -= 2
            reasons.append("Strong selling volume")
    elif vol_ratio >= 1.1:
        if price > safe_float(prev["Close"]):
            score += 1
        elif price < safe_float(prev["Close"]):
            score -= 1

    # Short-term breakout / breakdown
    recent = df.iloc[-7:-1]
    if len(recent) >= 3:
        recent_high = safe_float(recent["High"].max())
        recent_low = safe_float(recent["Low"].min())
        if price > recent_high:
            score += 2
            reasons.append("Breakout")
        elif price < recent_low:
            score -= 2
            reasons.append("Breakdown")

    # Convert score to signal
    if score >= 6:
        signal = "STRONG BUY"
    elif score >= 3:
        signal = "BUY"
    elif score <= -6:
        signal = "STRONG SELL"
    elif score <= -3:
        signal = "SELL"
    else:
        signal = "WAIT"

    confidence = int(min(95, 50 + abs(score) * 7)) if signal != "WAIT" else int(max(20, 50 - abs(score) * 5))

    # Entry, SL, targets based on ATR
    if signal in ["BUY", "STRONG BUY"]:
        entry = price
        sl = price - (1.2 * atr)
        risk = max(entry - sl, 0.01)
        t1 = entry + (1.5 * risk)
        t2 = entry + (2.2 * risk)
        rr = (t2 - entry) / risk
        trend = "BULLISH"
    elif signal in ["SELL", "STRONG SELL"]:
        entry = price
        sl = price + (1.2 * atr)
        risk = max(sl - entry, 0.01)
        t1 = entry - (1.5 * risk)
        t2 = entry - (2.2 * risk)
        rr = (entry - t2) / risk
        trend = "BEARISH"
    else:
        entry = price
        sl = price
        t1 = price
        t2 = price
        rr = 0
        trend = "SIDEWAYS"

    return {
        "name": name,
        "ticker": ticker,
        "price": round(price, 2),
        "change": round(pct, 2),
        "signal": signal,
        "confidence": confidence,
        "score": score,
        "entry": round(entry, 2),
        "sl": round(sl, 2),
        "t1": round(t1, 2),
        "t2": round(t2, 2),
        "rr": round(rr, 2),
        "rsi": round(rsi, 1),
        "vwap": round(vwap, 2),
        "ema9": round(ema9, 2),
        "ema20": round(ema20, 2),
        "vol_ratio": round(vol_ratio, 2),
        "reason": " • ".join(reasons[:5]),
        "trend": trend
    }



def marathi_action(signal):
    return {
        "STRONG BUY": "🟢 आता खरेदीसाठी मजबूत संधी",
        "BUY": "🟢 खरेदीची संधी",
        "STRONG SELL": "🔴 आता SHORT SELL साठी मजबूत संधी",
        "SELL": "🔴 SHORT SELL ची संधी",
        "WAIT": "🟡 आत्ता काही करू नका"
    }.get(signal, "🟡 आत्ता काही करू नका")


def simple_reason(row):
    reasons = []
    if row["trend"] == "BULLISH":
        reasons.append("शेअर वरच्या दिशेने मजबूत दिसतोय")
    elif row["trend"] == "BEARISH":
        reasons.append("शेअरवर विक्रीचा दबाव दिसतोय")

    if row["vol_ratio"] >= 1.5:
        reasons.append("नेहमीपेक्षा जास्त व्यवहार होत आहेत")
    if row["rsi"] >= 55 and row["rsi"] <= 72:
        reasons.append("खरेदीची ताकद चांगली आहे")
    elif row["rsi"] <= 45 and row["rsi"] >= 28:
        reasons.append("विक्रीची ताकद जास्त आहे")

    if not reasons:
        reasons.append("सिग्नल अजून पुरेसा मजबूत नाही")
    return " + ".join(reasons[:3])


def simple_trade_card(r, short=False):
    if r["signal"] == "WAIT":
        return f"""
        <div class="signal-card">
            <div class="wait">{r['name']} — 🟡 आत्ता काही करू नका</div>
            <div style="color:#fff;font-size:20px;font-weight:800;">सध्याचा भाव ₹{r['price']}</div>
            <div style="color:#cbd5e1;font-size:14px;margin-top:8px;">
                योग्य संधीची वाट पहा.<br>
                <b>आपला संकेत:</b> {r['confidence']}/100
            </div>
        </div>
        """

    if not short:
        return f"""
        <div class="signal-card">
            <div class="buy">{r['name']} — 🟢 खरेदीची संधी</div>
            <div style="color:#fff;font-size:20px;font-weight:800;">या भावाजवळ घ्या: ₹{r['entry']}</div>
            <div style="color:#cbd5e1;font-size:14px;margin-top:8px;">
                💰 ₹{r['t1']} जवळ काही नफा घ्या<br>
                🎯 ₹{r['t2']} जवळ उरलेला नफा घ्या<br>
                🛑 पण भाव ₹{r['sl']} पर्यंत खाली आला तर बाहेर पडा<br>
                ⭐ <b>आपला संकेत:</b> {r['confidence']}/100<br>
                💡 <b>का?</b> {simple_reason(r)}
            </div>
        </div>
        """
    return f"""
    <div class="signal-card">
        <div class="sell">{r['name']} — 🔴 SHORT SELL ची संधी</div>
        <div style="color:#fff;font-size:20px;font-weight:800;">या भावाजवळ SELL करा: ₹{r['entry']}</div>
        <div style="color:#cbd5e1;font-size:14px;margin-top:8px;">
            💰 भाव ₹{r['t1']} पर्यंत खाली आला तर काही नफा घ्या<br>
            🎯 ₹{r['t2']} पर्यंत खाली आला तर उरलेला नफा घ्या<br>
            🛑 पण भाव ₹{r['sl']} पर्यंत वर गेला तर बाहेर पडा<br>
            ⭐ <b>आपला संकेत:</b> {r['confidence']}/100<br>
            💡 <b>का?</b> {simple_reason(r)}
        </div>
    </div>
    """

# -----------------------------
# MARKET MACRO
# -----------------------------
with st.spinner("Market data load होत आहे..."):
    sp_p, sp_c = get_market_data("^GSPC")
    nas_p, nas_c = get_market_data("^IXIC")
    crude_p, crude_c = get_market_data("CL=F")
    gold_p, gold_c = get_market_data("GC=F")
    nifty_p, nifty_c = get_market_data("^NSEI")
    bank_p, bank_c = get_market_data("^NSEBANK")
    vix_p, vix_c = get_market_data("^INDIAVIX")
    nbees_p, nbees_c = get_market_data("NIFTYBEES.NS")

score = 0
if sp_c > 0.2:
    score += 2
elif sp_c < -0.2:
    score -= 2

if nas_c > 0.2:
    score += 1
elif nas_c < -0.2:
    score -= 1

if crude_c > 1.5:
    score -= 2
elif crude_c < -1.5:
    score += 2

if vix_c > 5:
    score -= 2
elif vix_c < -5:
    score += 1

if nifty_c > 0.35:
    score += 1
elif nifty_c < -0.35:
    score -= 1

if bank_c > 0.35:
    score += 1
elif bank_c < -0.35:
    score -= 1

b1, b2 = st.columns([2, 1])

if score >= 3:
    market_mood = "BULLISH"
    banner = "<div class='status-banner bullish-bg'>🟢 MARKET REGIME: BULLISH</div>"
    action = "BUY setups ला preference द्या. Confirmation शिवाय entry घेऊ नका."
elif score <= -3:
    market_mood = "BEARISH"
    banner = "<div class='status-banner bearish-bg'>🔴 MARKET REGIME: BEARISH</div>"
    action = "SELL/SHORT setups ला preference द्या. Strong stocks short करू नका."
else:
    market_mood = "NEUTRAL"
    banner = "<div class='status-banner neutral-bg'>🟡 MARKET REGIME: SIDEWAYS / NEUTRAL</div>"
    action = "Selective trades. High-confidence setup नसेल तर NO TRADE."

with b1:
    st.markdown(banner, unsafe_allow_html=True)
with b2:
    st.info(f"🎯 **Action Plan**\n\n{action}\n\n**Market Score:** {score}")

st.markdown("### 🌐 Global & Domestic Macro Indicators")
r1 = st.columns(4)
r2 = st.columns(4)

cards = [
    ("🇺🇸 S&P 500", f"{sp_p:,.2f}", sp_c, False),
    ("🇺🇸 NASDAQ", f"{nas_p:,.2f}", nas_c, False),
    ("🛢️ CRUDE OIL", f"${crude_p:,.2f}", crude_c, True),
    ("🟡 GOLD", f"${gold_p:,.2f}", gold_c, False),
    ("🇮🇳 NIFTY 50", f"{nifty_p:,.2f}", nifty_c, False),
    ("🏦 BANK NIFTY", f"{bank_p:,.2f}", bank_c, False),
    ("⚠️ INDIA VIX", f"{vix_p:,.2f}", vix_c, True),
    ("📈 NIFTYBEES", f"₹{nbees_p:,.2f}", nbees_c, False),
]

for i, item in enumerate(cards[:4]):
    with r1[i]:
        st.markdown(draw_card(*item), unsafe_allow_html=True)

for i, item in enumerate(cards[4:]):
    with r2[i]:
        st.markdown(draw_card(*item), unsafe_allow_html=True)

st.write("---")

# -----------------------------
# STOCK UNIVERSE
# -----------------------------
stocks_map = {
    "Tata Steel": "TATASTEEL.NS",
    "BEL": "BEL.NS",
    "ONGC": "ONGC.NS",
    "ITC": "ITC.NS",
    "Wipro": "WIPRO.NS",
    "Coal India": "COALINDIA.NS",
    "Power Grid": "POWERGRID.NS",
    "SBI": "SBIN.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Infosys": "INFY.NS",
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Larsen & Toubro": "LT.NS",
}

st.markdown("### ⚡ Intraday Technical Scanner")

filter_choice = st.radio(
    "शेअर्स फिल्टर:",
    ["सर्व शेअर्स", "Under ₹700"],
    horizontal=True
)

with st.spinner("VWAP, EMA, RSI आणि Volume analyse होत आहेत..."):
    rows = [analyze_stock(name, ticker, market_mood) for name, ticker in stocks_map.items()]

sdf = pd.DataFrame(rows)

if filter_choice == "Under ₹700":
    sdf = sdf[sdf["price"] <= 700].copy()

# -----------------------------
# TOP OPPORTUNITIES
# -----------------------------
st.markdown("### ⭐ आजच्या सर्वात चांगल्या संधी")

buys = sdf[sdf["signal"].isin(["BUY", "STRONG BUY"])].sort_values(
    ["score", "confidence"], ascending=False
).head(3)

sells = sdf[sdf["signal"].isin(["SELL", "STRONG SELL"])].sort_values(
    ["score", "confidence"], ascending=True
).head(3)

c_buy, c_sell = st.columns(2)

with c_buy:
    st.markdown("#### 🟢 आज खरेदीसाठी")
    if buys.empty:
        st.info("सध्या खरेदीसाठी पुरेशी मजबूत संधी नाही. घाई करू नका.")
    else:
        for _, r in buys.iterrows():
            st.markdown(simple_trade_card(r, short=False), unsafe_allow_html=True)

with c_sell:
    st.markdown("#### 🔴 आज SHORT SELL साठी")
    if sells.empty:
        st.info("सध्या SHORT SELL साठी पुरेशी मजबूत संधी नाही.")
    else:
        for _, r in sells.iterrows():
            st.markdown(simple_trade_card(r, short=True), unsafe_allow_html=True)

# -----------------------------
# FULL SCANNER TABLE
# -----------------------------
st.markdown("### 📊 सर्व शेअर्स — सविस्तर माहिती")
st.caption("हा भाग फक्त अधिक माहिती हवी असल्यास पहा. वरचा हिरवा/लाल निर्णय भाग मुख्य आहे.")

display_df = sdf[[
    "name", "price", "change", "signal", "confidence", "score",
    "rsi", "vwap", "ema9", "ema20", "vol_ratio",
    "entry", "sl", "t1", "t2", "rr"
]].copy()

display_df.columns = [
    "Stock", "CMP", "% Chg", "Signal", "Confidence %", "Score",
    "RSI", "VWAP", "EMA9", "EMA20", "Vol x",
    "Entry", "SL", "T1", "T2", "R:R"
]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# RISK CALCULATOR
# -----------------------------
st.write("---")
st.markdown("### 🛡️ किती शेअर्स घ्यायचे?")

rc1, rc2, rc3 = st.columns(3)

with rc1:
    capital = st.number_input(
        "तुमच्याकडे ट्रेडसाठी रक्कम ₹",
        min_value=1000.0,
        value=50000.0,
        step=1000.0
    )

with rc2:
    risk_pct = st.number_input(
        "एका व्यवहारात जास्तीत जास्त किती % धोका घ्यायचा",
        min_value=0.1,
        max_value=5.0,
        value=1.0,
        step=0.1
    )

with rc3:
    selected_stock = st.selectbox(
        "Stock",
        sdf["name"].tolist() if not sdf.empty else list(stocks_map.keys())
    )

if not sdf.empty:
    selected = sdf[sdf["name"] == selected_stock].iloc[0]

    risk_amount = capital * risk_pct / 100
    per_share_risk = abs(float(selected["entry"]) - float(selected["sl"]))

    if per_share_risk > 0:
        qty_by_risk = int(risk_amount / per_share_risk)
        qty_by_capital = int(capital / max(float(selected["entry"]), 0.01))
        qty = max(0, min(qty_by_risk, qty_by_capital))
    else:
        qty = 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("जास्तीत जास्त नुकसान मर्यादा ₹", f"{risk_amount:,.0f}")
    m2.metric("सुचवलेली संख्या", qty)
    m3.metric("घ्यायचा/विकायचा भाव", f"₹{selected['entry']}")
    m4.metric("इथे पोहोचल्यास बाहेर पडा", f"₹{selected['sl']}")

# -----------------------------
# STOCK DETAIL
# -----------------------------
st.write("---")
st.markdown("### 🔎 एखादा शेअर तपासून पहा")

detail_name = st.selectbox(
    "शेअर निवडा",
    list(stocks_map.keys()),
    key="detail_stock"
)

detail_ticker = stocks_map[detail_name]
detail = analyze_stock(detail_name, detail_ticker, market_mood)
detail_df = get_intraday_data(detail_ticker)

d1, d2, d3, d4 = st.columns(4)
d1.metric("Signal", detail["signal"])
d2.metric("Confidence", f"{detail['confidence']}%")
d3.metric("RSI", detail["rsi"])
d4.metric("Volume Ratio", f"{detail['vol_ratio']}x")

if not detail_df.empty:
    chart_df = detail_df[["Close", "VWAP", "EMA9", "EMA20"]].tail(80).copy()
    st.line_chart(chart_df, use_container_width=True)

    st.caption(
        f"Entry ₹{detail['entry']} | SL ₹{detail['sl']} | "
        f"T1 ₹{detail['t1']} | T2 ₹{detail['t2']} | R:R {detail['rr']}"
    )

# -----------------------------
# FOOTER / DISCLAIMER
# -----------------------------
st.write("---")
st.warning(
    "⚠️ महत्त्वाचे: तुम्ही नवीन असाल तर सुरुवातीला कमी रकमेने/पेपर ट्रेडिंगने सराव करा. हा dashboard educational / decision-support purpose साठी आहे. "
    "Signals हे market data आणि technical indicators वर आधारित आहेत; "
    "profit guarantee नाही. स्वतःचे risk management आणि broker data verify करा."
)

if st.button("🔄 डेटा त्वरित रिफ्रेश करा"):
    st.cache_data.clear()
    st.rerun()

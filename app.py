import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Alpha Terminal Pro V4",
    page_icon="⚡",
    layout="wide"
)

# =========================================================
# UI / CSS
# =========================================================
st.markdown("""
<style>
    .main { background-color: #0b0f19; }
    .stApp { background-color: #0b0f19; color: #f8fafc; }

    .card {
        background-color: #131b2e;
        border: 1px solid #233252;
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.35);
    }

    .title-blue {
        color:#38bdf8;
        font-size:14px;
        font-weight:700;
    }

    .big {
        color:#fff;
        font-size:22px;
        font-weight:800;
    }

    .small {
        color:#cbd5e1;
        font-size:13px;
    }

    .green { color:#4ade80; font-weight:800; }
    .red { color:#f87171; font-weight:800; }
    .yellow { color:#facc15; font-weight:800; }

    .banner {
        padding:16px;
        border-radius:12px;
        font-size:18px;
        font-weight:800;
        text-align:center;
    }

    .bull { background:#064e3b; color:#6ee7b7; border:1px solid #059669; }
    .bear { background:#881337; color:#fecdd3; border:1px solid #e11d48; }
    .neutral { background:#78350f; color:#fef08a; border:1px solid #d97706; }

    .hero {
        background:#101827;
        border:1px solid #233252;
        border-radius:16px;
        padding:18px;
        margin-bottom:14px;
    }

    @media (max-width: 768px) {
        .big { font-size:18px; }
        .banner { font-size:15px; padding:12px; }
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
h1, h2 = st.columns([3, 1])
with h1:
    st.markdown("<h1 style='color:#38bdf8;margin:0;'>⚡ ALPHA TERMINAL PRO V4</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#94a3b8;margin:0;'>सोप्या भाषेत — आज काय घ्यायचं, काय विकायचं, आणि कधी थांबायचं</p>",
        unsafe_allow_html=True
    )
with h2:
    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    st.markdown(
        f"<div style='text-align:right;'>🟢 <b style='color:#22c55e;'>LIVE</b><br>"
        f"<span style='color:#94a3b8;font-size:12px;'>{now}</span></div>",
        unsafe_allow_html=True
    )

st.write("---")

# =========================================================
# HELPERS
# =========================================================
def sf(v, default=0.0):
    try:
        if pd.isna(v):
            return default
        return float(v)
    except:
        return default

@st.cache_data(ttl=120)
def get_daily(ticker, period="3mo"):
    try:
        df = yf.download(
            ticker,
            period=period,
            interval="1d",
            progress=False,
            auto_adjust=False,
            threads=False
        )
        if df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df.dropna().copy()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=120)
def get_intraday(ticker):
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

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        cols = ["Open","High","Low","Close","Volume"]
        if any(c not in df.columns for c in cols):
            return pd.DataFrame()

        df = df.dropna(subset=["Open","High","Low","Close"]).copy()

        # EMA
        df["EMA9"] = df["Close"].ewm(span=9, adjust=False).mean()
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()

        # RSI
        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df["RSI"] = 100 - (100 / (1 + rs))

        # VWAP
        tp = (df["High"] + df["Low"] + df["Close"]) / 3
        session = pd.Series(df.index.date, index=df.index)
        pv = tp * df["Volume"]
        df["CumPV"] = pv.groupby(session).cumsum()
        df["CumVol"] = df["Volume"].groupby(session).cumsum()
        df["VWAP"] = df["CumPV"] / df["CumVol"].replace(0, np.nan)

        # Volume
        df["VolAvg20"] = df["Volume"].rolling(20).mean()

        # ATR
        tr1 = df["High"] - df["Low"]
        tr2 = (df["High"] - df["Close"].shift()).abs()
        tr3 = (df["Low"] - df["Close"].shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["ATR14"] = tr.rolling(14).mean()

        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_news_sentiment(ticker):
    """
    Lightweight keyword-based sentiment from Yahoo Finance news headlines.
    No external API key required.
    """
    positive_words = [
        "surge","gain","rise","beat","growth","profit","strong","upgrade","record",
        "buy","bullish","outperform","wins","order","expansion","approval","positive"
    ]
    negative_words = [
        "fall","drop","loss","weak","downgrade","sell","bearish","fraud","probe",
        "decline","miss","cut","negative","lawsuit","debt","warning","crash"
    ]

    try:
        items = yf.Ticker(ticker).news or []
        if not items:
            return 0, "बातम्यांचा स्पष्ट संकेत नाही", []

        score = 0
        used = []
        for n in items[:8]:
            title = ""
            if isinstance(n, dict):
                title = n.get("title", "") or ""
                if not title and isinstance(n.get("content"), dict):
                    title = n["content"].get("title", "") or ""

            if not title:
                continue

            low = title.lower()
            p = sum(1 for w in positive_words if w in low)
            m = sum(1 for w in negative_words if w in low)
            score += p - m
            used.append(title)

        if score >= 2:
            return 2, "बातम्या सकारात्मक दिसतात", used[:3]
        elif score <= -2:
            return -2, "बातम्या नकारात्मक दिसतात", used[:3]
        return 0, "बातम्या मिश्र / तटस्थ आहेत", used[:3]
    except:
        return 0, "बातम्या मिळाल्या नाहीत", []

def pct_change_from_daily(ticker):
    df = get_daily(ticker, "10d")
    if len(df) < 2:
        return 0.0, 0.0
    cur = sf(df["Close"].iloc[-1])
    prev = sf(df["Close"].iloc[-2])
    pct = ((cur - prev) / prev * 100) if prev else 0
    return round(cur, 2), round(pct, 2)

# =========================================================
# GLOBAL / MACRO ENGINE
# =========================================================
macro_map = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW": "^DJI",
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "INDIA VIX": "^INDIAVIX",
    "CRUDE OIL": "CL=F",
    "GOLD": "GC=F",
    "USD/INR": "INR=X",
}

macro = {}
for label, ticker in macro_map.items():
    p, c = pct_change_from_daily(ticker)
    macro[label] = {"price": p, "change": c}

market_score = 0
market_reasons = []

if macro["S&P 500"]["change"] > 0.3:
    market_score += 2
    market_reasons.append("US market सकारात्मक")
elif macro["S&P 500"]["change"] < -0.3:
    market_score -= 2
    market_reasons.append("US market कमकुवत")

if macro["NASDAQ"]["change"] > 0.4:
    market_score += 1
elif macro["NASDAQ"]["change"] < -0.4:
    market_score -= 1

if macro["NIFTY 50"]["change"] > 0.35:
    market_score += 2
    market_reasons.append("Nifty मजबूत")
elif macro["NIFTY 50"]["change"] < -0.35:
    market_score -= 2
    market_reasons.append("Nifty कमकुवत")

if macro["BANK NIFTY"]["change"] > 0.35:
    market_score += 1
elif macro["BANK NIFTY"]["change"] < -0.35:
    market_score -= 1

if macro["INDIA VIX"]["change"] > 5:
    market_score -= 2
    market_reasons.append("बाजारातील भीती वाढली")
elif macro["INDIA VIX"]["change"] < -5:
    market_score += 1

if macro["CRUDE OIL"]["change"] > 1.5:
    market_score -= 1
    market_reasons.append("Crude वाढले")
elif macro["CRUDE OIL"]["change"] < -1.5:
    market_score += 1

if macro["USD/INR"]["change"] > 0.5:
    market_score -= 1

if market_score >= 4:
    market_mood = "BULLISH"
    risk_level = "मध्यम"
    market_text = "🟢 बाजार खरेदीकडे झुकलेला"
elif market_score <= -4:
    market_mood = "BEARISH"
    risk_level = "जास्त"
    market_text = "🔴 बाजार विक्रीकडे झुकलेला"
else:
    market_mood = "NEUTRAL"
    risk_level = "मध्यम ते जास्त"
    market_text = "🟡 बाजार स्पष्ट दिशेत नाही"

# =========================================================
# SECTOR STRENGTH
# =========================================================
sector_map = {
    "METAL": "^CNXMETAL",
    "BANK": "^NSEBANK",
    "IT": "^CNXIT",
    "ENERGY": "^CNXENERGY",
    "FMCG": "^CNXFMCG",
    "AUTO": "^CNXAUTO",
    "PHARMA": "^CNXPHARMA",
}

sector_change = {}
for sector, ticker in sector_map.items():
    _, c = pct_change_from_daily(ticker)
    sector_change[sector] = c

# =========================================================
# STOCK UNIVERSE (large practical set)
# =========================================================
stocks = {
    "Tata Steel": ("TATASTEEL.NS", "METAL"),
    "JSW Steel": ("JSWSTEEL.NS", "METAL"),
    "Hindalco": ("HINDALCO.NS", "METAL"),
    "BEL": ("BEL.NS", "OTHER"),
    "ONGC": ("ONGC.NS", "ENERGY"),
    "Reliance": ("RELIANCE.NS", "ENERGY"),
    "Coal India": ("COALINDIA.NS", "ENERGY"),
    "Power Grid": ("POWERGRID.NS", "ENERGY"),
    "NTPC": ("NTPC.NS", "ENERGY"),
    "SBI": ("SBIN.NS", "BANK"),
    "HDFC Bank": ("HDFCBANK.NS", "BANK"),
    "ICICI Bank": ("ICICIBANK.NS", "BANK"),
    "Axis Bank": ("AXISBANK.NS", "BANK"),
    "Kotak Bank": ("KOTAKBANK.NS", "BANK"),
    "Infosys": ("INFY.NS", "IT"),
    "TCS": ("TCS.NS", "IT"),
    "Wipro": ("WIPRO.NS", "IT"),
    "HCL Tech": ("HCLTECH.NS", "IT"),
    "Tech Mahindra": ("TECHM.NS", "IT"),
    "ITC": ("ITC.NS", "FMCG"),
    "HUL": ("HINDUNILVR.NS", "FMCG"),
    "Nestle India": ("NESTLEIND.NS", "FMCG"),
    "Maruti": ("MARUTI.NS", "AUTO"),
    "Tata Motors": ("TATAMOTORS.NS", "AUTO"),
    "M&M": ("M&M.NS", "AUTO"),
    "Sun Pharma": ("SUNPHARMA.NS", "PHARMA"),
    "Dr Reddy": ("DRREDDY.NS", "PHARMA"),
    "Cipla": ("CIPLA.NS", "PHARMA"),
    "L&T": ("LT.NS", "OTHER"),
    "Bharti Airtel": ("BHARTIARTL.NS", "OTHER"),
    "Adani Ports": ("ADANIPORTS.NS", "OTHER"),
    "Titan": ("TITAN.NS", "OTHER"),
}

# =========================================================
# ANALYSIS ENGINE
# =========================================================
def analyze_intraday(name, ticker, sector):
    df = get_intraday(ticker)
    news_score, news_text, headlines = get_news_sentiment(ticker)

    if df.empty or len(df) < 30:
        price, day_change = pct_change_from_daily(ticker)
        return {
            "name": name, "ticker": ticker, "sector": sector,
            "price": price, "signal": "WAIT", "score": 0,
            "confidence": 25, "entry": price, "sl": price, "t1": price, "t2": price,
            "rsi": 0, "vol_ratio": 0, "reason": "डेटा अपुरा आहे",
            "news": news_text, "headlines": headlines
        }

    x = df.iloc[-1]
    prev = df.iloc[-2]

    price = sf(x["Close"])
    ema9 = sf(x["EMA9"])
    ema20 = sf(x["EMA20"])
    vwap = sf(x["VWAP"])
    rsi = sf(x["RSI"], 50)
    atr = sf(x["ATR14"], max(price * 0.005, 0.1))
    volume = sf(x["Volume"])
    volavg = sf(x["VolAvg20"])
    vol_ratio = volume / volavg if volavg > 0 else 0

    score = 0
    why = []

    # 1) Global/market
    if market_mood == "BULLISH":
        score += 1
        why.append("एकूण बाजार सकारात्मक")
    elif market_mood == "BEARISH":
        score -= 1
        why.append("एकूण बाजार कमकुवत")

    # 2) Sector
    sec = sector_change.get(sector, 0)
    if sec > 0.5:
        score += 2
        why.append("या क्षेत्रात ताकद आहे")
    elif sec < -0.5:
        score -= 2
        why.append("या क्षेत्रावर दबाव आहे")

    # 3) VWAP
    if price > vwap:
        score += 2
        why.append("शेअरवर खरेदीची बाजू मजबूत")
    elif price < vwap:
        score -= 2
        why.append("शेअरवर विक्रीची बाजू मजबूत")

    # 4) EMA
    if ema9 > ema20:
        score += 2
    elif ema9 < ema20:
        score -= 2

    # 5) RSI
    if 55 <= rsi <= 72:
        score += 1
    elif 28 <= rsi <= 45:
        score -= 1
    elif rsi > 78:
        score -= 1
        why.append("भाव जास्त चढलेला आहे")
    elif rsi < 22:
        score += 1

    # 6) Volume
    if vol_ratio >= 1.5:
        if price > sf(prev["Close"]):
            score += 2
            why.append("जास्त खरेदीचे व्यवहार")
        else:
            score -= 2
            why.append("जास्त विक्रीचे व्यवहार")

    # 7) Breakout / breakdown
    recent = df.iloc[-8:-1]
    if len(recent) >= 4:
        hi = sf(recent["High"].max())
        lo = sf(recent["Low"].min())
        if price > hi:
            score += 2
            why.append("वरचा अडथळा तोडला")
        elif price < lo:
            score -= 2
            why.append("खालचा आधार तुटला")

    # 8) News
    score += news_score
    if news_score > 0:
        why.append("बातम्या सकारात्मक")
    elif news_score < 0:
        why.append("बातम्या नकारात्मक")

    # final intraday signal
    if score >= 7:
        signal = "STRONG BUY"
    elif score >= 4:
        signal = "BUY"
    elif score <= -7:
        signal = "STRONG SELL"
    elif score <= -4:
        signal = "SELL"
    else:
        signal = "WAIT"

    confidence = min(95, 50 + abs(score) * 6) if signal != "WAIT" else max(20, 45 - abs(score) * 4)

    # NO TRADE protection
    if market_mood == "NEUTRAL" and abs(score) < 6:
        signal = "WAIT"

    # levels
    if signal in ["BUY","STRONG BUY"]:
        entry = price
        sl = price - 1.2 * atr
        risk = max(entry - sl, 0.01)
        t1 = entry + 1.5 * risk
        t2 = entry + 2.2 * risk
    elif signal in ["SELL","STRONG SELL"]:
        entry = price
        sl = price + 1.2 * atr
        risk = max(sl - entry, 0.01)
        t1 = entry - 1.5 * risk
        t2 = entry - 2.2 * risk
    else:
        entry = sl = t1 = t2 = price

    return {
        "name": name,
        "ticker": ticker,
        "sector": sector,
        "price": round(price,2),
        "signal": signal,
        "score": int(score),
        "confidence": int(confidence),
        "entry": round(entry,2),
        "sl": round(sl,2),
        "t1": round(t1,2),
        "t2": round(t2,2),
        "rsi": round(rsi,1),
        "vol_ratio": round(vol_ratio,2),
        "reason": " + ".join(why[:4]) if why else "स्पष्ट कारण मिळाले नाही",
        "news": news_text,
        "headlines": headlines,
    }

def analyze_delivery(name, ticker, sector):
    df = get_daily(ticker, "6mo")
    news_score, news_text, headlines = get_news_sentiment(ticker)

    if df.empty or len(df) < 60:
        return {
            "name": name, "ticker": ticker, "signal": "WAIT",
            "score": 0, "confidence": 25, "price": 0, "target": 0,
            "support": 0, "reason": "डेटा अपुरा आहे", "news": news_text
        }

    close = df["Close"].astype(float)
    price = sf(close.iloc[-1])

    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1/14, adjust=False).mean()
    al = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = ag / al.replace(0, np.nan)
    rsi = sf((100 - (100/(1+rs))).iloc[-1], 50)

    score = 0
    why = []

    if price > sf(ema20.iloc[-1]):
        score += 1
    else:
        score -= 1

    if sf(ema20.iloc[-1]) > sf(ema50.iloc[-1]):
        score += 2
        why.append("मध्यम काळाचा कल वरचा")
    else:
        score -= 2

    if len(ema200.dropna()) > 0:
        if price > sf(ema200.iloc[-1]):
            score += 1
        else:
            score -= 1

    if 50 <= rsi <= 68:
        score += 1
    elif rsi > 75:
        score -= 1

    sec = sector_change.get(sector, 0)
    if sec > 0.4:
        score += 1
        why.append("क्षेत्र मजबूत")
    elif sec < -0.4:
        score -= 1

    if market_mood == "BULLISH":
        score += 1
    elif market_mood == "BEARISH":
        score -= 1

    score += news_score
    if news_score > 0:
        why.append("बातम्या चांगल्या")
    elif news_score < 0:
        why.append("बातम्या नकारात्मक")

    if score >= 5:
        signal = "BUY"
    elif score <= -4:
        signal = "AVOID"
    else:
        signal = "WAIT"

    confidence = min(92, 50 + abs(score)*7) if signal != "WAIT" else 40

    recent_low = sf(df["Low"].tail(20).min())
    recent_high = sf(df["High"].tail(20).max())
    support = recent_low
    target = max(recent_high, price * 1.06) if signal == "BUY" else price

    return {
        "name": name,
        "ticker": ticker,
        "signal": signal,
        "score": int(score),
        "confidence": int(confidence),
        "price": round(price,2),
        "target": round(target,2),
        "support": round(support,2),
        "reason": " + ".join(why[:3]) if why else "मिश्र संकेत",
        "news": news_text
    }

# =========================================================
# MARKET SUMMARY
# =========================================================
st.markdown("## ☀️ आजचा आपला प्लॅन")

if market_mood == "BULLISH":
    klass = "bull"
elif market_mood == "BEARISH":
    klass = "bear"
else:
    klass = "neutral"

st.markdown(
    f"<div class='banner {klass}'>{market_text} | धोका: {risk_level} | Market Score: {market_score}</div>",
    unsafe_allow_html=True
)

if market_reasons:
    st.caption("कारण: " + " + ".join(market_reasons[:4]))

# Macro cards
st.markdown("### 🌍 बाजारावर परिणाम करणाऱ्या मुख्य गोष्टी")
macro_cols = st.columns(3)
labels = list(macro.keys())
for i, label in enumerate(labels):
    m = macro[label]
    cls = "green" if m["change"] >= 0 else "red"
    with macro_cols[i % 3]:
        st.markdown(
            f"""
            <div class="card">
                <div class="title-blue">{label}</div>
                <div class="big">{m['price']:,.2f}</div>
                <div class="{cls}">{m['change']:+.2f}%</div>
            </div>
            """,
            unsafe_allow_html=True
        )

st.write("---")

# =========================================================
# SCAN
# =========================================================
st.markdown("## ⚡ आजचे Intraday व्यवहार")

scan_limit = st.slider(
    "एका वेळी किती शेअर्स तपासायचे?",
    min_value=10,
    max_value=len(stocks),
    value=min(20, len(stocks)),
    step=5
)

selected_items = list(stocks.items())[:scan_limit]

with st.spinner("Market + sector + technical + volume + news एकत्र तपासत आहे..."):
    intraday_rows = []
    for name, (ticker, sector) in selected_items:
        intraday_rows.append(analyze_intraday(name, ticker, sector))

idf = pd.DataFrame(intraday_rows)

buy_df = idf[idf["signal"].isin(["BUY","STRONG BUY"])].sort_values(
    ["score","confidence"], ascending=False
).head(3)

sell_df = idf[idf["signal"].isin(["SELL","STRONG SELL"])].sort_values(
    ["score","confidence"], ascending=True
).head(3)

def render_buy(r):
    return f"""
    <div class="hero">
        <div class="green">{r['name']} — 🟢 खरेदीची संधी</div>
        <div class="big">या भावाजवळ घ्या: ₹{r['entry']}</div>
        <div class="small">
            💰 ₹{r['t1']} जवळ काही नफा घ्या<br>
            🎯 ₹{r['t2']} जवळ उरलेला नफा घ्या<br>
            🛑 पण ₹{r['sl']} पर्यंत खाली आला तर बाहेर पडा<br>
            ⭐ संकेत: {r['confidence']}/100<br>
            💡 का? {r['reason']}<br>
            📰 {r['news']}
        </div>
    </div>
    """

def render_sell(r):
    return f"""
    <div class="hero">
        <div class="red">{r['name']} — 🔴 SHORT SELL ची संधी</div>
        <div class="big">या भावाजवळ SELL करा: ₹{r['entry']}</div>
        <div class="small">
            💰 ₹{r['t1']} पर्यंत खाली आला तर काही नफा घ्या<br>
            🎯 ₹{r['t2']} पर्यंत खाली आला तर उरलेला नफा घ्या<br>
            🛑 पण ₹{r['sl']} पर्यंत वर गेला तर बाहेर पडा<br>
            ⭐ संकेत: {r['confidence']}/100<br>
            💡 का? {r['reason']}<br>
            📰 {r['news']}
        </div>
    </div>
    """

c1, c2 = st.columns(2)

with c1:
    st.markdown("### 🟢 आज खरेदीसाठी")
    if buy_df.empty:
        st.info("आज मजबूत खरेदीची संधी दिसत नाही. घाई करू नका.")
    else:
        for _, r in buy_df.iterrows():
            st.markdown(render_buy(r), unsafe_allow_html=True)

with c2:
    st.markdown("### 🔴 आज SHORT SELL साठी")
    if sell_df.empty:
        st.info("आज मजबूत SHORT SELL संधी दिसत नाही.")
    else:
        for _, r in sell_df.iterrows():
            st.markdown(render_sell(r), unsafe_allow_html=True)

# =========================================================
# DELIVERY
# =========================================================
st.write("---")
st.markdown("## 📦 काही दिवसांसाठी घेण्यास योग्य शेअर्स")

with st.spinner("Delivery साठी trend + sector + news तपासत आहे..."):
    delivery_rows = []
    for name, (ticker, sector) in selected_items:
        delivery_rows.append(analyze_delivery(name, ticker, sector))

ddf = pd.DataFrame(delivery_rows)

delivery_buy = ddf[ddf["signal"] == "BUY"].sort_values(
    ["score","confidence"], ascending=False
).head(3)

if delivery_buy.empty:
    st.info("सध्या Delivery साठी पुरेशी मजबूत संधी मिळाली नाही.")
else:
    dcols = st.columns(min(3, len(delivery_buy)))
    for i, (_, r) in enumerate(delivery_buy.iterrows()):
        with dcols[i]:
            st.markdown(
                f"""
                <div class="card">
                    <div class="green">{r['name']} — काही दिवसांसाठी विचार करा</div>
                    <div class="big">सध्याचा भाव ₹{r['price']}</div>
                    <div class="small">
                        🎯 अंदाजे लक्ष्य ₹{r['target']}<br>
                        🛑 ₹{r['support']} खाली गेल्यास पुन्हा विचार करा<br>
                        ⭐ संकेत: {r['confidence']}/100<br>
                        💡 {r['reason']}<br>
                        📰 {r['news']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

# =========================================================
# FULL TABLE
# =========================================================
st.write("---")
st.markdown("## 📊 सर्व तपासलेले शेअर्स")
st.caption("हा भाग technical माहिती पाहायची असल्यास वापरा. मुख्य निर्णय वर दिले आहेत.")

show_cols = [
    "name","price","signal","confidence","score","sector",
    "rsi","vol_ratio","entry","sl","t1","t2","news"
]
table = idf[show_cols].copy()
table.columns = [
    "शेअर","भाव","निर्णय","संकेत /100","Score","Sector",
    "RSI","Volume x","घ्यायचा/SELL भाव","बाहेर पडायचा भाव","नफा 1","नफा 2","बातम्या"
]
st.dataframe(table, use_container_width=True, hide_index=True)

# =========================================================
# RISK / QUANTITY
# =========================================================
st.write("---")
st.markdown("## 🛡️ किती शेअर्स घ्यायचे?")

if not idf.empty:
    r1, r2, r3 = st.columns(3)
    with r1:
        capital = st.number_input("ट्रेडसाठी तुमची रक्कम ₹", min_value=1000.0, value=50000.0, step=1000.0)
    with r2:
        risk_pct = st.number_input("एका व्यवहारात जास्तीत जास्त धोका %", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    with r3:
        sel = st.selectbox("शेअर", idf["name"].tolist())

    rr = idf[idf["name"] == sel].iloc[0]
    risk_amt = capital * risk_pct / 100
    per_share_risk = abs(sf(rr["entry"]) - sf(rr["sl"]))

    if per_share_risk > 0:
        qty_by_risk = int(risk_amt / per_share_risk)
        qty_by_cap = int(capital / max(sf(rr["entry"]), 0.01))
        qty = max(0, min(qty_by_risk, qty_by_cap))
    else:
        qty = 0

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("जास्तीत जास्त नुकसान मर्यादा", f"₹{risk_amt:,.0f}")
    q2.metric("सुचवलेली संख्या", qty)
    q3.metric("भाव", f"₹{rr['entry']}")
    q4.metric("इथे बाहेर पडा", f"₹{rr['sl']}")

# =========================================================
# NEWS DETAILS
# =========================================================
st.write("---")
st.markdown("## 📰 एखाद्या शेअरच्या बातम्या")
news_stock = st.selectbox("शेअर निवडा", idf["name"].tolist(), key="news_stock")

nr = idf[idf["name"] == news_stock].iloc[0]
st.info(nr["news"])

for h in nr["headlines"]:
    st.write("•", h)

# =========================================================
# FOOTER
# =========================================================
st.write("---")
st.warning(
    "⚠️ महत्त्वाचे: हा dashboard निर्णय घेण्यासाठी मदत करणारे tool आहे; नफा हमी देत नाही. "
    "तुम्ही नवीन असाल तर सुरुवातीला paper trading किंवा कमी रकमेने सराव करा. "
    "Intraday मध्ये broker चा live भाव आणि order execute होण्यापूर्वी Stop Loss जरूर तपासा."
)

if st.button("🔄 डेटा त्वरित रिफ्रेश करा"):
    st.cache_data.clear()
    st.rerun()

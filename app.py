import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Alpha Terminal Pro | Multi-Stock", page_icon="⚡", layout="wide")

# हाय-टेक डार्क CSS (रेडिओ बटन्स आणि फॉन्ट १००% क्लिअर)
st.markdown("""
    <style>
    .main { background-color: #0b0f19; }
    .stApp { background-color: #0b0f19; color: #f8fafc; }
    
    .macro-card {
        background-color: #131b2e;
        border: 1px solid #233252;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    .macro-title {
        color: #38bdf8 !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        margin-bottom: 4px;
    }
    .macro-val {
        color: #ffffff !important;
        font-size: 24px !important;
        font-weight: 800 !important;
        margin-bottom: 2px;
        font-family: monospace;
    }
    .up-green { color: #4ade80 !important; font-weight: bold; font-size: 14px; }
    .down-red { color: #f87171 !important; font-weight: bold; font-size: 14px; }

    .status-banner {
        padding: 16px;
        border-radius: 10px;
        font-size: 18px;
        font-weight: 800;
        text-align: center;
    }
    .bullish-bg { background: #064e3b; color: #6ee7b7; border: 1px solid #059669; }
    .bearish-bg { background: #881337; color: #fecdd3; border: 1px solid #e11d48; }
    .neutral-bg { background: #78350f; color: #fef08a; border: 1px solid #d97706; }

    .stock-card {
        background: #131b2e;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .badge-short {
        background: #991b1b;
        color: #fecaca;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-buy {
        background: #166534;
        color: #bbf7d0;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-wait {
        background: #334155;
        color: #cbd5e1;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
    }

    /* फिल्टर आणि रेडिओ बटन्सचे टेक्स्ट चमकदार बनवण्यासाठी CSS */
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
    div[data-testid="stRadio"] div[role="radiogroup"] label p {
        color: #ffffff !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# हेडर
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("<h1 style='color: #38bdf8; margin: 0;'>⚡ ALPHA TERMINAL PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 14px; margin: 0;'>Budget & Heavyweight Intraday Action Radar</p>", unsafe_allow_html=True)
with col_h2:
    current_time = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"<div style='text-align: right;'>🟢 <b style='color:#22c55e;'>LIVE FEED</b><br><span style='color:#94a3b8; font-size:12px;'>वेळ: {current_time}</span></div>", unsafe_allow_html=True)

st.write("---")

@st.cache_data(ttl=120)
def get_market_data(ticker):
    try:
        df = yf.Ticker(ticker).history(period="2d")
        if len(df) >= 2:
            p_close = df['Close'].iloc[-2]
            c_close = df['Close'].iloc[-1]
            pct = ((c_close - p_close) / p_close) * 100
            return round(c_close, 2), round(pct, 2)
        elif len(df) == 1:
            return round(df['Close'].iloc[-1], 2), 0.0
        return 0.0, 0.0
    except:
        return 0.0, 0.0

with st.spinner("डेटा लोड होत आहे..."):
    sp_p, sp_c = get_market_data("^GSPC")
    nas_p, nas_c = get_market_data("^IXIC")
    crude_p, crude_c = get_market_data("CL=F")
    gold_p, gold_c = get_market_data("GC=F")
    nifty_p, nifty_c = get_market_data("^NSEI")
    bank_p, bank_c = get_market_data("^NSEBANK")
    vix_p, vix_c = get_market_data("^INDIAVIX")
    nbees_p, nbees_c = get_market_data("NIFTYBEES.NS")

score = 0
if sp_c > 0.2: score += 2
elif sp_c < -0.2: score -= 2

if nas_c > 0.2: score += 1
elif nas_c < -0.2: score -= 1

if crude_c > 1.5: score -= 2
elif crude_c < -1.5: score += 2

if vix_c > 5.0: score -= 2
elif vix_c < -5.0: score += 1

col_b1, col_b2 = st.columns([2, 1])
market_mood = "NEUTRAL"

with col_b1:
    if score >= 2:
        market_mood = "BULLISH"
        st.markdown("<div class='status-banner bullish-bg'>🟢 SENTIMENT: BULLISH (बाजारात तेजी)</div>", unsafe_allow_html=True)
        plan = "**रणनीती:** आज खरेदीचे (BUY) दिवस आहेत. वाढणाऱ्या शेअर्सवर लक्ष ठेवा."
    elif score <= -2:
        market_mood = "BEARISH"
        st.markdown("<div class='status-banner bearish-bg'>🔴 SENTIMENT: BEARISH (घसरणीचा दबाव)</div>", unsafe_allow_html=True)
        plan = "**रणनीती:** **SHORT SELL** ची उत्तम संधी. जास्त पडलेले बजेट शेअर्स शॉर्ट करून नफा कमवा."
    else:
        st.markdown("<div class='status-banner neutral-bg'>🟡 SENTIMENT: NEUTRAL (बाजार साइडवेज)</div>", unsafe_allow_html=True)
        plan = "**रणनीती:** बाजार संथ राहील. आज आक्रमक शॉर्ट सेलिंग टाळा."

with col_b2:
    st.info(f"🎯 **Action Radar:**\n\n{plan}")

st.write("")

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

st.markdown("<h3 style='color: #ffffff;'>🌐 Global & Domestic Macro Indicators</h3>", unsafe_allow_html=True)
r1_1, r1_2, r1_3, r1_4 = st.columns(4)
with r1_1: st.markdown(draw_card("🇺🇸 S&P 500", f"${sp_p}", sp_c), unsafe_allow_html=True)
with r1_2: st.markdown(draw_card("🇺🇸 NASDAQ TECH", f"${nas_p}", nas_c), unsafe_allow_html=True)
with r1_3: st.markdown(draw_card("🛢️ CRUDE OIL", f"${crude_p}", crude_c, reverse=True), unsafe_allow_html=True)
with r1_4: st.markdown(draw_card("🟡 GOLD (सोने)", f"${gold_p}", gold_c), unsafe_allow_html=True)

r2_1, r2_2, r2_3, r2_4 = st.columns(4)
with r2_1: st.markdown(draw_card("🇮🇳 NIFTY 50", f"₹{nifty_p}", nifty_c), unsafe_allow_html=True)
with r2_2: st.markdown(draw_card("🏦 BANK NIFTY", f"₹{bank_p}", bank_c), unsafe_allow_html=True)
with r2_3: st.markdown(draw_card("⚠️ INDIA VIX", f"{vix_p}", vix_c, reverse=True), unsafe_allow_html=True)
with r2_4: st.markdown(draw_card("📈 NIFTYBEES", f"₹{nbees_p}", nbees_c), unsafe_allow_html=True)

st.write("---")

stocks_map = {
    "Tata Steel (बजेट)": "TATASTEEL.NS",
    "BEL (बजेट)": "BEL.NS",
    "ONGC (बजेट)": "ONGC.NS",
    "ITC Ltd. (बजेट)": "ITC.NS",
    "Wipro (बजेट)": "WIPRO.NS",
    "Coal India (बजेट)": "COALINDIA.NS",
    "Power Grid (बजेट)": "POWERGRID.NS",
    "State Bank of India": "SBIN.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Infosys": "INFY.NS",
    "Reliance Ind.": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Larsen & Toubro": "LT.NS"
}

stocks_data = []
for name, sym in stocks_map.items():
    p, c = get_market_data(sym)
    
    if market_mood == "BEARISH" and c < -0.6:
        signal = "🔻 SHORT SELL"
        badge = "badge-short"
    elif market_mood == "BULLISH" and c > 0.6:
        signal = "🚀 BUY"
        badge = "badge-buy"
    else:
        signal = "WAIT"
        badge = "badge-wait"
        
    stocks_data.append({"name": name, "price_raw": p, "price": f"₹{p}", "change": c, "signal": signal, "badge": badge})

sdf = pd.DataFrame(stocks_data)

st.markdown("<h3 style='color: #38bdf8;'>⚡ Intraday Radar (बजेट आणि हेवीवेट शेअर्स)</h3>", unsafe_allow_html=True)

filter_choice = st.radio("शेअर्स फिल्टर निवडा:", ["सर्व शेअर्स", "फक्त कमी किमतीचे बजेट शेअर्स (Under ₹700)"], horizontal=True)

if filter_choice == "फक्त कमी किमतीचे बजेट शेअर्स (Under ₹700)":
    filtered_df = sdf[sdf['price_raw'] <= 700]
else:
    filtered_df = sdf

col_gain, col_loss = st.columns(2)

with col_gain:
    st.markdown("<h4 style='color: #4ade80;'>🚀 वाढणारे शेअर्स (BUY संधी)</h4>", unsafe_allow_html=True)
    g_items = filtered_df[filtered_df['change'] >= 0].sort_values(by="change", ascending=False)
    if g_items.empty:
        st.write("सध्या यादीत वाढणारा शेअर नाही.")
    else:
        for _, r in g_items.iterrows():
            st.markdown(f"""
            <div class="stock-card" style="border-left: 4px solid #4ade80;">
                <div>
                    <b style="font-size: 15px; color: #ffffff;">{r['name']}</b><br>
                    <span style="color: #94a3b8; font-size: 13px;">{r['price']}</span>
                </div>
                <div style="text-align: right;">
                    <span style="color: #4ade80; font-weight: bold; font-size: 14px;">↑ {r['change']:.2f}%</span><br>
                    <span class="{r['badge']}">{r['signal']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

with col_loss:
    st.markdown("<h4 style='color: #f87171;'>🔻 पडलेले शेअर्स (SHORT SELL संधी)</h4>", unsafe_allow_html=True)
    l_items = filtered_df[filtered_df['change'] < 0].sort_values(by="change")
    if l_items.empty:
        st.write("सध्या यादीत पडलेला शेअर नाही.")
    else:
        for _, r in l_items.iterrows():
            st.markdown(f"""
            <div class="stock-card" style="border-left: 4px solid #f87171;">
                <div>
                    <b style="font-size: 15px; color: #ffffff;">{r['name']}</b><br>
                    <span style="color: #94a3b8; font-size: 13px;">{r['price']}</span>
                </div>
                <div style="text-align: right;">
                    <span style="color: #f87171; font-weight: bold; font-size: 14px;">↓ {r['change']:.2f}%</span><br>
                    <span class="{r['badge']}">{r['signal']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.write("")
if st.button("🔄 डेटा त्वरित रिफ्रेश करा"):
    st.cache_data.clear()
    st.rerun()

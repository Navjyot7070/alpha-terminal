import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="PRO Market Terminal v2", page_icon="⚡", layout="wide")

# संपूर्ण पेजसाठी क्रिस्टल क्लिअर डार्क CSS
st.markdown("""
    <style>
    .main { background-color: #0b0f19; }
    .stApp { background-color: #0b0f19; }
    
    /* स्वतः तयार केलेले हाय-टेक कार्ड */
    .custom-card {
        background-color: #131b2e;
        border: 1px solid #233252;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
    }
    .card-title {
        color: #38bdf8 !important; /* चमकदार आकाशी रंग */
        font-size: 15px !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .card-value {
        color: #ffffff !important; /* तेजस्वी पांढरा रंग */
        font-size: 26px !important;
        font-weight: 900 !important;
        margin-bottom: 4px;
        font-family: monospace;
    }
    .card-delta-up {
        color: #4ade80 !important; /* ठळक हिरवा */
        font-size: 14px !important;
        font-weight: 700 !important;
    }
    .card-delta-down {
        color: #f87171 !important; /* ठळक लाल */
        font-size: 14px !important;
        font-weight: 700 !important;
    }
    
    /* स्टेटस बॅनर */
    .status-box {
        padding: 16px;
        border-radius: 10px;
        font-size: 19px;
        font-weight: 800;
        text-align: center;
    }
    .bullish { background: #064e3b; color: #6ee7b7; border: 1px solid #059669; }
    .bearish { background: #881337; color: #fecdd3; border: 1px solid #e11d48; }
    .neutral { background: #78350f; color: #fef08a; border: 1px solid #d97706; }
    </style>
""", unsafe_allow_html=True)

# हेडर आणि टाइमस्टॅम्प
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("<h1 style='color: #38bdf8; margin-bottom: 0;'>⚡ ALPHA TERMINAL PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 14px;'>Real-Time Global Sentiment, Macro Indicators & Stock Screener</p>", unsafe_allow_html=True)
with col_h2:
    now_time = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"<div style='text-align: right; padding-top: 10px;'>🟢 <span style='color: #22c55e; font-weight: bold;'>LIVE FEED ACTIVE</span><br><span style='color: #cbd5e1; font-size: 13px;'>शेवटचे अपडेट: {now_time}</span></div>", unsafe_allow_html=True)

st.write("---")

@st.cache_data(ttl=120)
def fetch_data(symbol):
    try:
        data = yf.Ticker(symbol).history(period="2d")
        if len(data) >= 2:
            prev = data['Close'].iloc[-2]
            curr = data['Close'].iloc[-1]
            chg = ((curr - prev) / prev) * 100
            return round(curr, 2), round(chg, 2)
        elif len(data) == 1:
            return round(data['Close'].iloc[-1], 2), 0.0
        return 0.0, 0.0
    except:
        return 0.0, 0.0

with st.spinner("डेटा सिंक होत आहे..."):
    sp_p, sp_c = fetch_data("^GSPC")
    nas_p, nas_c = fetch_data("^IXIC")
    crude_p, crude_c = fetch_data("CL=F")
    gold_p, gold_c = fetch_data("GC=F")
    nifty_p, nifty_c = fetch_data("^NSEI")
    bank_p, bank_c = fetch_data("^NSEBANK")
    vix_p, vix_c = fetch_data("^INDIAVIX")
    nbees_p, nbees_c = fetch_data("NIFTYBEES.NS")

# कस्टम कार्ड रेंडर करण्याचे फंक्शन
def render_card(title, value, change, is_reverse=False):
    is_up = change >= 0
    if is_reverse:
        delta_class = "card-delta-down" if is_up else "card-delta-up"
        arrow = "↑" if is_up else "↓"
    else:
        delta_class = "card-delta-up" if is_up else "card-delta-down"
        arrow = "↑" if is_up else "↓"
        
    html = f"""
    <div class="custom-card">
        <div class="card-title">{title}</div>
        <div class="card-value">{value}</div>
        <div class="{delta_class}">{arrow} {change:.2f}%</div>
    </div>
    """
    return html

# स्कोअरिंग
score = 0
if sp_c > 0.2: score += 2
elif sp_c < -0.2: score -= 2

if nas_c > 0.2: score += 1
elif nas_c < -0.2: score -= 1

if crude_c > 1.5: score -= 2
elif crude_c < -1.5: score += 2

if vix_c > 5.0: score -= 2
elif vix_c < -5.0: score += 1

# १. एआय सिग्नल
c_sig1, c_sig2 = st.columns([2, 1])
with c_sig1:
    if score >= 2:
        st.markdown("<div class='status-box bullish'>🟢 SENTIMENT: BULLISH (बाजारात तेजीचे संकेत)</div>", unsafe_allow_html=True)
        strat = "**रणनीती:** जागतिक बाजारातून सकारात्मक साथ. NIFTYBEES किंवा दर्जेदार शेअर्समध्ये खरेदीसाठी चांगला दिवस."
    elif score <= -2:
        st.markdown("<div class='status-box bearish'>🔴 SENTIMENT: BEARISH / CAUTION (घसरणीचा किंवा दबावाचा कल)</div>", unsafe_allow_html=True)
        strat = "**रणनीती:** घाईने खरेदी करू नका. चांगले शेअर्स स्वस्त मिळण्याची संधी शोधा. F&O पासून पूर्ण दूर राहा."
    else:
        st.markdown("<div class='status-box neutral'>🟡 SENTIMENT: NEUTRAL / RANGEBOUND (बाजार शांत/दिशाहीन)</div>", unsafe_allow_html=True)
        strat = "**रणनीती:** बाजार एका ठरावीक पातळीत राहण्याची शक्यता. नियमित SIP किंवा वेट-अँड-वॉच धोरण ठेवा."

with c_sig2:
    st.info(f"🎯 **AI Action Plan:**\n\n{strat}")

st.write("")

# २. मॅक्रो इंडिकेटर्स (१००% क्लिअर आणि ठळक फॉन्ट्स)
st.markdown("<h3 style='color: #ffffff;'>🌐 Global & Domestic Macro Indicators</h3>", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
with m1: st.markdown(render_card("🇺🇸 S&P 500", f"${sp_p}", sp_c), unsafe_allow_html=True)
with m2: st.markdown(render_card("🇺🇸 NASDAQ TECH", f"${nas_p}", nas_c), unsafe_allow_html=True)
with m3: st.markdown(render_card("🛢️ CRUDE OIL (Brent)", f"${crude_p}", crude_c, is_reverse=True), unsafe_allow_html=True)
with m4: st.markdown(render_card("🟡 GOLD (सोने)", f"${gold_p}", gold_c), unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
with k1: st.markdown(render_card("🇮🇳 NIFTY 50", f"₹{nifty_p}", nifty_c), unsafe_allow_html=True)
with k2: st.markdown(render_card("🏦 BANK NIFTY", f"₹{bank_p}", bank_c), unsafe_allow_html=True)
with k3: st.markdown(render_card("⚠️ INDIA VIX (भीती)", f"{vix_p}", vix_c, is_reverse=True), unsafe_allow_html=True)
with k4: st.markdown(render_card("📈 NIFTYBEES (ETF)", f"₹{nbees_p}", nbees_c), unsafe_allow_html=True)

st.write("---")

# ३. हेवीवेट शेअर्स स्क्रिनर
st.markdown("<h3 style='color: #ffffff;'>📊 Market Movers Screener (दिग्गज शेअर्स)</h3>", unsafe_allow_html=True)

stocks = {
    "Reliance Ind.": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "State Bank of India": "SBIN.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Larsen & Toubro": "LT.NS",
    "ITC Ltd.": "ITC.NS"
}

s_list = []
for name, sym in stocks.items():
    p, c = fetch_data(sym)
    action = "🟢 खरेदीचा ओघ" if c > 0 else ("🔴 विक्रीचा दबाव" if c < 0 else "⚪ जैसे थे")
    s_list.append({"कंपनी (Stock)": name, "चालू भाव (Price)": f"₹{p}", "बदल (Change %)": c, "सध्याचा कल": action})

df = pd.DataFrame(s_list)

col_g, col_l = st.columns(2)
with col_g:
    st.markdown("<h4 style='color: #4ade80;'>🚀 वाढणारे शेअर्स (Gainers)</h4>", unsafe_allow_html=True)
    g_df = df[df['बदल (Change %)'] >= 0].sort_values(by="बदल (Change %)", ascending=False)
    st.dataframe(g_df, hide_index=True, use_container_width=True)

with col_l:
    st.markdown("<h4 style='color: #f87171;'>🔻 पडलेले शेअर्स (Losers / Dips)</h4>", unsafe_allow_html=True)
    l_df = df[df['बदल (Change %)'] < 0].sort_values(by="बदल (Change %)")
    st.dataframe(l_df, hide_index=True, use_container_width=True)

st.write("")
if st.button("🔄 डेटा त्वरित रिफ्रेश करा"):
    st.cache_data.clear()
    st.rerun()
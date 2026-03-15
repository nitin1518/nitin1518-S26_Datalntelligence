import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import feedparser
import re, os, pytz
from datetime import datetime
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="Global Threat Matrix: Quant Edition", layout="wide", initial_sidebar_state="collapsed")
IST = pytz.timezone('Asia/Kolkata')
VAULT_FILE = "geo_threat_history.csv"

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    .metric-box { background-color: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; height: 100%;}
    .metric-title { font-size: 0.80rem; color: #8b949e; text-transform: uppercase; font-weight: 600; }
    .metric-value { font-size: 1.6rem; font-weight: bold; color: #ffffff; }
    .metric-sub { font-size: 0.85rem; font-weight: bold; }
    .news-card { border-left: 3px solid #30363d; background-color: #161b22; padding: 10px; margin-bottom: 8px; border-radius: 4px; font-size: 0.9rem;}
    .econ-threat { border-left: 4px solid #d29922; background-color: rgba(210, 153, 34, 0.1); }
    </style>
""", unsafe_allow_html=True)

# --- 2. ADVANCED NLP & ECONOMIC THREAT ENGINE ---
class TacticalNLPEngine:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.factions = {
            "US_ISRAEL": ['israel', 'idf', 'us', 'usa', 'washington', 'biden', 'trump', 'american', 'netanyahu'],
            "IRAN_PROXIES": ['iran', 'tehran', 'irgc', 'hezbollah', 'houthi', 'hamas']
        }
        self.tactics = {
            "offensive": ['strike', 'attack', 'launch', 'expands', 'offensive', 'destroys', 'bomb', 'warns', 'troops'],
            "defensive": ['denies', 'braces', 'intercepts', 'plea', 'defends', 'shield'],
            "losses": ['dead', 'casualties', 'hit', 'destroyed', 'killed', 'damage'],
            "diplomacy": ['ceasefire', 'peace', 'talks', 'negotiate', 'urges', 'summit']
        }
        # Economic choke points and assets
        self.econ_keywords = ['hormuz', 'oil', 'facility', 'sanctions', 'embargo', 'shipping', 'red sea', 'tanker', 'energy']

    def analyze_posture(self, headlines):
        total_offense = 0
        total_diplomacy = 0
        econ_threats = []
        
        for h in headlines:
            text = h['Title'].lower()
            words = set(re.findall(r'\b\w+\b', text))
            
            # Detect Economic Targets in headlines
            if any(w in words for w in self.econ_keywords):
                econ_threats.append(h['Title'])
                
            total_offense += sum(1 for w in words if w in self.tactics["offensive"])
            total_diplomacy += sum(1 for w in words if w in self.tactics["diplomacy"])

        # Escalation Index (1-10)
        esc_index = 5.0 + (total_offense * 0.4) - (total_diplomacy * 0.5) + (len(econ_threats) * 0.3)
        esc_index = max(1.0, min(10.0, round(esc_index, 2)))
        
        return esc_index, econ_threats

# --- 3. QUANTITATIVE MARKET AGGREGATOR ---
class QuantAggregator:
    def fetch_markets(self):
        # Added Bitcoin and VIX (Fear Index)
        tickers = {
            "Crude Oil": ["BZ=F", "CL=F"], 
            "Gold": ["GC=F"], 
            "Bitcoin": ["BTC-USD"],
            "VIX (Fear)": ["^VIX"]
        }
        market_data = {}
        for name, symbols in tickers.items():
            for sym in symbols:
                try:
                    # Fetching 5 days with 1-hour intervals for granular correlation
                    data = yf.Ticker(sym).history(period="5d", interval="1h")
                    if len(data) >= 2:
                        current = data['Close'].iloc[-1]
                        prev_day = data['Close'].iloc[-24] if len(data) >= 24 else data['Close'].iloc[0] # 24h change
                        change = ((current - prev_day) / prev_day) * 100
                        market_data[name] = {"price": current, "change": change, "series": data['Close']}
                        break
                except: continue
        return market_data

    def fetch_news(self):
        try:
            feed = feedparser.parse("https://news.google.com/rss/search?q=Israel+Iran+US+conflict&hl=en-US&gl=US&ceid=US:en")
            return [{"Title": entry.title, "Published": entry.published, "Link": entry.link} for entry in feed.entries[:25]]
        except: return []

def save_to_vault(index):
    new_data = pd.DataFrame([{"Time": datetime.now(IST).strftime('%Y-%m-%d %H:%M'), "Escalation_Index": index}])
    df = pd.concat([pd.read_csv(VAULT_FILE), new_data], ignore_index=True) if os.path.exists(VAULT_FILE) else new_data
    df.to_csv(VAULT_FILE, index=False)
    return df

# --- 4. DASHBOARD RENDER ---
st_autorefresh(interval=5 * 60 * 1000, key="geo_refresh")

st.markdown("<h2 style='text-align: center; color: #ffffff; letter-spacing: 2px;'>🌐 QUANTITATIVE THREAT MATRIX: LIVE</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #8b949e;'>LAST SYNC: {datetime.now(IST).strftime('%d %b %Y | %H:%M:%S IST')}</p>", unsafe_allow_html=True)

aggregator = QuantAggregator()
nlp = TacticalNLPEngine()

markets = aggregator.fetch_markets()
news = aggregator.fetch_news()

esc_index, econ_threats = nlp.analyze_posture(news)
history_df = save_to_vault(esc_index)

# --- UI: LEVEL 1 MACRO & MARKETS ---
cols = st.columns(5)

# 1. Escalation
e_color = "#ff7b72" if esc_index >= 7 else "#d29922"
cols[0].markdown(f"<div class='metric-box'><div class='metric-title'>Escalation Index</div><div class='metric-value' style='color: {e_color};'>{esc_index}/10</div></div>", unsafe_allow_html=True)

# 2. Crude Oil (Supply Shock Proxy)
if "Crude Oil" in markets:
    oil = markets["Crude Oil"]
    c_color = "#ff7b72" if oil['change'] > 0 else "#3fb950"
    cols[1].markdown(f"<div class='metric-box'><div class='metric-title'>Brent Crude (Supply Risk)</div><div class='metric-value'>${oil['price']:.2f}</div><div class='metric-sub' style='color: {c_color};'>{oil['change']:+.2f}% (24h)</div></div>", unsafe_allow_html=True)

# 3. Gold (Traditional Safe Haven)
if "Gold" in markets:
    gold = markets["Gold"]
    g_color = "#3fb950" if gold['change'] > 0 else "#ff7b72" # Gold up = fear up
    cols[2].markdown(f"<div class='metric-box'><div class='metric-title'>Gold (Safe Haven)</div><div class='metric-value'>${gold['price']:.1f}</div><div class='metric-sub' style='color: {g_color};'>{gold['change']:+.2f}% (24h)</div></div>", unsafe_allow_html=True)

# 4. Bitcoin (Modern Liquidity Proxy)
if "Bitcoin" in markets:
    btc = markets["Bitcoin"]
    b_color = "#3fb950" if btc['change'] > 0 else "#ff7b72"
    cols[3].markdown(f"<div class='metric-box'><div class='metric-title'>Bitcoin (Risk Proxy)</div><div class='metric-value'>${btc['price']:,.0f}</div><div class='metric-sub' style='color: {b_color};'>{btc['change']:+.2f}% (24h)</div></div>", unsafe_allow_html=True)

# 5. VIX (Market Fear)
if "VIX (Fear)" in markets:
    vix = markets["VIX (Fear)"]
    v_color = "#ff7b72" if vix['change'] > 0 else "#3fb950"
    cols[4].markdown(f"<div class='metric-box'><div class='metric-title'>VIX (Market Fear)</div><div class='metric-value'>{vix['price']:.2f}</div><div class='metric-sub' style='color: {v_color};'>{vix['change']:+.2f}% (24h)</div></div>", unsafe_allow_html=True)

st.write("---")

# --- UI: LEVEL 2 CROSS-ASSET CORRELATION ---
colA, colB = st.columns([2, 1])

with colA:
    st.subheader("📊 War vs. Market: Dual-Axis Correlation")
    
    # We overlay the geopolitical escalation index on top of the financial assets
    # Allows analysts to see if markets are reacting to the news or ignoring it.
    asset_choice = st.radio("Select Asset Overlay:", ["Bitcoin", "Crude Oil", "Gold", "VIX (Fear)"], horizontal=True)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Plot Escalation Index (Left Y-Axis)
    if not history_df.empty and len(history_df) > 1:
        fig.add_trace(go.Scatter(x=history_df['Time'], y=history_df['Escalation_Index'], name="Escalation Index", line=dict(color="#ff7b72", width=3, dash='dot')), secondary_y=False)
    
    # Plot Asset Price (Right Y-Axis)
    if asset_choice in markets:
        asset_series = markets[asset_choice]["series"]
        # Convert index to string to align loosely with our vault timestamps for visual correlation
        fig.add_trace(go.Scatter(x=asset_series.index.astype(str), y=asset_series.values, name=asset_choice, line=dict(color="#58a6ff", width=2), fill='tozeroy', fillcolor='rgba(88, 166, 255, 0.1)'), secondary_y=True)
        
    fig.update_layout(template="plotly_dark", hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_yaxes(title_text="Threat Level (1-10)", secondary_y=False, range=[1, 10])
    fig.update_yaxes(title_text=f"{asset_choice} Price", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

    # Analyst Automated Insight
    st.subheader("🧠 Quantitative Analyst Insight")
    if asset_choice in markets:
        change = markets[asset_choice]['change']
        if asset_choice == "Bitcoin":
            if change < -2 and esc_index > 7: st.info("📉 **Capital Flight Detected:** As the Escalation Index breaches critical levels, Bitcoin is selling off. The market is treating Crypto as a 'Risk-On' asset, liquidating it alongside equities rather than using it as a safe haven.")
            elif change > 2 and esc_index > 7: st.info("📈 **Digital Gold Narrative:** Bitcoin is rallying alongside geopolitical tension, indicating investors are moving capital outside traditional sovereign banking systems to avoid freeze risks.")
            else: st.info("⚖️ Bitcoin is currently decoupled from the geopolitical news cycle. Price action is likely driven by macroeconomic (Fed) or institutional flows.")
        elif asset_choice == "Crude Oil":
            if len(econ_threats) > 0 and change > 1: st.error("🚨 **Supply Shock Pricing:** The NLP engine detected specific threats to energy infrastructure/shipping. Oil markets are actively pricing in a kinetic disruption to the global supply chain.")
            else: st.info("⚖️ Oil markets are absorbing the geopolitical rhetoric without pricing in a catastrophic supply failure. The 'war premium' remains suppressed.")

with colB:
    st.subheader("📡 Raw Signal Feed & Chokepoints")
    
    if econ_threats:
        st.error(f"⚠️ **ECONOMIC THREATS DETECTED:**\n" + "\n".join([f"- {t}" for t in set(econ_threats)]))
    
    if news:
        for article in news[:10]:
            title = article["Title"]
            # Visual Tagging
            css_class = "news-card"
            if any(w in title.lower() for w in nlp.econ_keywords): css_class += " econ-threat"
            
            st.markdown(f"""
            <div class='{css_class}'>
                <a href='{article["Link"]}' target='_blank' style='color: #c9d1d9; text-decoration: none;'>{title}</a><br>
                <span style='color: #8b949e; font-size: 0.75rem;'>{article["Published"]}</span>
            </div>
            """, unsafe_allow_html=True)

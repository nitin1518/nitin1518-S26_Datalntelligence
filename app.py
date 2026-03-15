import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import feedparser
from google import genai
from google.genai import types
import pytz, json
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="Global Threat Matrix", layout="wide", initial_sidebar_state="collapsed")
IST = pytz.timezone('Asia/Kolkata')

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    .metric-box { background-color: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; }
    .metric-title { font-size: 0.85rem; color: #8b949e; text-transform: uppercase; font-weight: 600; }
    .metric-value { font-size: 1.8rem; font-weight: bold; color: #ffffff; }
    .news-card { border-left: 4px solid #d29922; background-color: rgba(210, 153, 34, 0.1); padding: 12px; margin-bottom: 10px; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION ---
try:
    client = genai.Client(api_key=st.secrets["gemini"]["api_key"])
except Exception:
    st.error("⚠️ System Offline: Verify Gemini API Key.")
    st.stop()

# --- 3. DATA ENGINES ---
class GeoIntelligence:
    def fetch_live_markets(self):
        """Pulls live financial impact data."""
        tickers = {"Crude Oil": "BZ=F", "Gold": "GC=F", "S&P 500": "^GSPC"}
        market_data = {}
        for name, ticker in tickers.items():
            try:
                data = yf.Ticker(ticker).history(period="2d")
                if len(data) >= 2:
                    current = data['Close'].iloc[-1]
                    prev = data['Close'].iloc[-2]
                    pct_change = ((current - prev) / prev) * 100
                    market_data[name] = {"price": current, "change": pct_change}
            except: pass
        return market_data

    def fetch_global_news(self):
        """Bypasses blocks using Google News RSS to get latest headlines."""
        url = "https://news.google.com/rss/search?q=Israel+Iran+US+conflict&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:15]: # Get top 15 latest
            articles.append({"Title": entry.title, "Published": entry.published, "Link": entry.link})
        return articles

    def analyze_geopolitics(self, headlines):
        """Uses Gemini to assess escalation and extract involved actors."""
        text_feed = " | ".join([h['Title'] for h in headlines])
        prompt = f"""
        Analyze these live news headlines regarding the Middle East conflict.
        Return a strict JSON object with:
        - "escalation_index": Float from 1.0 (Peace talks) to 10.0 (Active regional war).
        - "narrative_momentum": Which entity has the current strategic/media momentum based on headlines? (e.g., "US/Israel", "Iran/Proxies", "Stalemate").
        - "involved_nations": A list of other countries/groups mentioned (e.g., ["Lebanon", "Yemen", "Russia"]).
        - "executive_summary": A 2-sentence tactical summary of the current situation.
        
        Headlines: {text_feed}
        """
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception as e:
            return None

# --- 4. DASHBOARD EXECUTION ---
# Keeps the dashboard ALIVE, refreshing every 5 minutes
st_autorefresh(interval=5 * 60 * 1000, key="geo_refresh")

st.markdown("<h2 style='text-align: center; color: #ffffff; letter-spacing: 2px;'>🌐 GLOBAL THREAT MATRIX: LIVE</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #8b949e;'>LAST SYNC: {datetime.now(IST).strftime('%d %b %Y | %H:%M:%S IST')}</p>", unsafe_allow_html=True)

engine = GeoIntelligence()

with st.spinner("Aggregating global intelligence networks..."):
    markets = engine.fetch_live_markets()
    news = engine.fetch_global_news()
    analysis = engine.analyze_geopolitics(news)

if analysis and news:
    # --- LEVEL 1: MACRO IMPACT (MARKETS & ESCALATION) ---
    c1, c2, c3, c4 = st.columns(4)
    
    # Escalation Index
    e_color = "#ff7b72" if analysis['escalation_index'] > 6 else "#d29922"
    c1.markdown(f"<div class='metric-box'><div class='metric-title'>Escalation Index (1-10)</div><div class='metric-value' style='color: {e_color};'>{analysis['escalation_index']}</div></div>", unsafe_allow_html=True)
    
    # Narrative Momentum
    c2.markdown(f"<div class='metric-box'><div class='metric-title'>Media/Strategic Momentum</div><div class='metric-value'>{analysis['narrative_momentum']}</div></div>", unsafe_allow_html=True)
    
    # Markets
    if "Crude Oil" in markets:
        oil = markets["Crude Oil"]
        o_color = "#ff7b72" if oil['change'] > 0 else "#3fb950" # Oil going up usually means conflict risk
        c3.markdown(f"<div class='metric-box'><div class='metric-title'>Brent Crude Oil</div><div class='metric-value'>${oil['price']:.2f} <span style='font-size: 1rem; color:{o_color};'>{oil['change']:.2f}%</span></div></div>", unsafe_allow_html=True)
    
    if "Gold" in markets:
        gold = markets["Gold"]
        g_color = "#ff7b72" if gold['change'] > 0 else "#3fb950"
        c4.markdown(f"<div class='metric-box'><div class='metric-title'>Gold (Safe Haven)</div><div class='metric-value'>${gold['price']:.2f} <span style='font-size: 1rem; color:{g_color};'>{gold['change']:.2f}%</span></div></div>", unsafe_allow_html=True)

    st.write("---")

    # --- LEVEL 2: AI TACTICAL BRIEFING ---
    colA, colB = st.columns([2, 1])
    
    with colA:
        st.subheader("🤖 AI Strategic Summary")
        st.info(analysis['executive_summary'])
        
        st.subheader("🌍 Secondary Actors Engaged")
        # Visualizing the extracted nations
        if analysis['involved_nations']:
            nations_df = pd.DataFrame({"Nation/Group": analysis['involved_nations'], "Status": "Active in News Cycle"})
            st.dataframe(nations_df, use_container_width=True, hide_index=True)
        else:
            st.write("No major secondary actors dominating the current cycle.")

    with colB:
        st.subheader("📡 Live Global Intel Feed")
        for article in news[:7]: # Show top 7
            st.markdown(f"""
            <div class='news-card'>
                <a href='{article["Link"]}' target='_blank' style='color: #58a6ff; text-decoration: none; font-weight: bold;'>{article["Title"]}</a><br>
                <span style='color: #8b949e; font-size: 0.8rem;'>{article["Published"]}</span>
            </div>
            """, unsafe_allow_html=True)

else:
    st.error("Data aggregation failed. Retrying on next sync cycle.")

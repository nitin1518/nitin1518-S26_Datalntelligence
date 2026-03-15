import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import feedparser
from google import genai
from google.genai import types
import pytz, json, os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="Global Threat Matrix", layout="wide", initial_sidebar_state="collapsed")
IST = pytz.timezone('Asia/Kolkata')
VAULT_FILE = "geo_threat_history.csv"

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    .metric-box { background-color: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; height: 100%;}
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
        tickers = {"Crude Oil": "BZ=F", "Gold": "GC=F"}
        market_data = {}
        for name, ticker in tickers.items():
            try:
                data = yf.Ticker(ticker).history(period="5d")
                if len(data) >= 2:
                    current = data['Close'].iloc[-1]
                    prev = data['Close'].iloc[-2]
                    pct_change = ((current - prev) / prev) * 100
                    market_data[name] = {"price": current, "change": pct_change}
            except Exception as e:
                pass # Fail silently, handled in UI
        return market_data

    def fetch_global_news(self):
        url = "https://news.google.com/rss/search?q=Israel+Iran+US+conflict&hl=en-US&gl=US&ceid=US:en"
        try:
            feed = feedparser.parse(url)
            articles = [{"Title": entry.title, "Published": entry.published, "Link": entry.link} for entry in feed.entries[:15]]
            return articles
        except Exception:
            return []

    def analyze_geopolitics(self, headlines):
        text_feed = " | ".join([h['Title'] for h in headlines])
        prompt = f"""
        Analyze these live news headlines regarding the Middle East conflict.
        Return a strict JSON object.
        - "escalation_index": Float from 1.0 (Peace) to 10.0 (War).
        - "narrative_momentum": Strategic/media momentum (e.g., "US/Israel", "Iran/Proxies", "Stalemate").
        - "involved_nations": List of other countries mentioned (e.g., ["Lebanon", "Yemen"]).
        - "executive_summary": 2-sentence tactical summary.
        Headlines: {text_feed}
        """
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    safety_settings=[
                        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE")
                    ]
                )
            )
            clean_json = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_json)
        except Exception as e:
            st.toast(f"AI Quota Exceeded. Charting fallback engaged.", icon="⚠️")
            return None # Graceful failure

def save_to_vault(escalation_score, momentum):
    new_data = pd.DataFrame([{"Time": datetime.now(IST).strftime('%Y-%m-%d %H:%M'), "Escalation_Index": escalation_score, "Momentum": momentum}])
    if os.path.exists(VAULT_FILE):
        df = pd.read_csv(VAULT_FILE)
        df = pd.concat([df, new_data], ignore_index=True)
    else:
        df = new_data
    df.to_csv(VAULT_FILE, index=False)
    return df

# --- 4. DASHBOARD EXECUTION ---
st_autorefresh(interval=5 * 60 * 1000, key="geo_refresh")

st.markdown("<h2 style='text-align: center; color: #ffffff; letter-spacing: 2px;'>🌐 GLOBAL THREAT MATRIX: LIVE</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #8b949e;'>LAST SYNC: {datetime.now(IST).strftime('%d %b %Y | %H:%M:%S IST')}</p>", unsafe_allow_html=True)

engine = GeoIntelligence()

# 1. Fetch Hard Data (Never Blocked)
markets = engine.fetch_live_markets()
news = engine.fetch_global_news()

# 2. Attempt AI Analysis (Can be Blocked)
analysis = None
if news:
    analysis = engine.analyze_geopolitics(news)

# --- UI RENDER: LEVEL 1 MACRO IMPACT ---
c1, c2, c3, c4 = st.columns(4)

# AI Dependent Metrics
if analysis:
    e_color = "#ff7b72" if analysis['escalation_index'] > 6 else "#d29922"
    c1.markdown(f"<div class='metric-box'><div class='metric-title'>Escalation Index (1-10)</div><div class='metric-value' style='color: {e_color};'>{analysis['escalation_index']}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-box'><div class='metric-title'>Strategic Momentum</div><div class='metric-value'>{analysis['narrative_momentum']}</div></div>", unsafe_allow_html=True)
    history_df = save_to_vault(analysis['escalation_index'], analysis['narrative_momentum'])
else:
    c1.markdown("<div class='metric-box'><div class='metric-title'>Escalation Index (1-10)</div><div class='metric-value' style='color: #8b949e;'>AI OFFLINE</div></div>", unsafe_allow_html=True)
    c2.markdown("<div class='metric-box'><div class='metric-title'>Strategic Momentum</div><div class='metric-value' style='color: #8b949e;'>API LIMIT HIT</div></div>", unsafe_allow_html=True)
    history_df = pd.read_csv(VAULT_FILE) if os.path.exists(VAULT_FILE) else pd.DataFrame()

# Hard Data Metrics (Always render)
if "Crude Oil" in markets:
    oil = markets["Crude Oil"]
    o_color = "#ff7b72" if oil['change'] > 0 else "#3fb950" 
    c3.markdown(f"<div class='metric-box'><div class='metric-title'>Brent Crude Oil</div><div class='metric-value'>${oil['price']:.2f} <span style='font-size: 1rem; color:{o_color};'>{oil['change']:.2f}%</span></div></div>", unsafe_allow_html=True)
else: c3.info("Oil market data offline.")

if "Gold" in markets:
    gold = markets["Gold"]
    g_color = "#ff7b72" if gold['change'] > 0 else "#3fb950"
    c4.markdown(f"<div class='metric-box'><div class='metric-title'>Gold (Safe Haven)</div><div class='metric-value'>${gold['price']:.2f} <span style='font-size: 1rem; color:{g_color};'>{gold['change']:.2f}%</span></div></div>", unsafe_allow_html=True)
else: c4.info("Gold market data offline.")

st.write("---")

# --- UI RENDER: LEVEL 2 TACTICAL TRENDS ---
colA, colB = st.columns([2, 1])

with colA:
    st.subheader("📈 Escalation Trendline (Historical Risk)")
    if not history_df.empty and len(history_df) > 1:
        fig = px.line(history_df, x="Time", y="Escalation_Index", markers=True, template="plotly_dark")
        fig.update_layout(yaxis_range=[1, 10], yaxis_title="Threat Level (1-10)")
        fig.add_hline(y=7.0, line_dash="dash", line_color="red", annotation_text="Critical Danger Zone")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Awaiting AI connection to draw historical trendline...")

    st.subheader("🤖 AI Strategic Summary")
    if analysis:
        st.info(analysis['executive_summary'])
        if analysis['involved_nations']:
            st.write("**Secondary Actors Pulled Into Conflict:** " + ", ".join(analysis['involved_nations']))
    else:
        st.warning("⚠️ AI Summary unavailable. Quota limits reached. Please rely on the raw news feed until the API resets in a few minutes.")

with colB:
    st.subheader("📡 Live Global Intel Feed")
    if news:
        for article in news[:7]:
            st.markdown(f"""
            <div class='news-card'>
                <a href='{article["Link"]}' target='_blank' style='color: #58a6ff; text-decoration: none; font-weight: bold;'>{article["Title"]}</a><br>
                <span style='color: #8b949e; font-size: 0.8rem;'>{article["Published"]}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("Live News feed disconnected.")

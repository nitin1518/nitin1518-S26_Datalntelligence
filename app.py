import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import feedparser
import re, os, pytz
from datetime import datetime
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from streamlit_autorefresh import st_autorefresh
from google import genai
from google.genai import types

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

# --- 2. LOCAL NLP ENGINE (ZERO API RELIANCE) ---
class PythonNLPEngine:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        # Lexicon for Geopolitical Escalation
        self.escalation_words = ['strike', 'war', 'attack', 'missile', 'expand', 'dead', 'retaliate', 'offensive', 'troops', 'fire', 'bomb']
        self.de_escalation_words = ['ceasefire', 'peace', 'talks', 'negotiate', 'truce', 'diplomacy', 'pact']
        
        # Entity mapping for Momentum
        self.entities = {
            "US/Israel": ['israel', 'idf', 'netanyahu', 'us', 'usa', 'washington', 'biden', 'trump', 'american'],
            "Iran/Proxies": ['iran', 'tehran', 'irgc', 'hezbollah', 'houthi', 'hamas', 'proxy']
        }

    def analyze_threat_level(self, headlines):
        """Calculates Escalation Index & Momentum using pure Python math."""
        if not headlines:
            return 5.0, "Unknown", []

        total_sentiment = 0
        esc_count = 0
        de_esc_count = 0
        entity_mentions = {"US/Israel": 0, "Iran/Proxies": 0}
        all_words = []

        for h in headlines:
            title = h['Title'].lower()
            # 1. VADER Sentiment (Negative sentiment increases threat)
            total_sentiment += self.analyzer.polarity_scores(title)['compound']
            
            # 2. Lexicon Weighting
            words = re.findall(r'\b\w+\b', title)
            all_words.extend(words)
            esc_count += sum(1 for w in words if w in self.escalation_words)
            de_esc_count += sum(1 for w in words if w in self.de_escalation_words)

            # 3. Entity Tracking (Who is dominating the headlines?)
            for team, keywords in self.entities.items():
                entity_mentions[team] += sum(1 for w in words if w in keywords)

        # Calculate Momentum
        momentum = max(entity_mentions, key=entity_mentions.get) if sum(entity_mentions.values()) > 0 else "Stalemate"

        # Calculate Escalation Index (Formula)
        avg_sentiment = total_sentiment / len(headlines)
        # Base 5.0, add points for escalation words, subtract for peace words, subtract sentiment (since negative sentiment = bad)
        index = 5.0 + (esc_count * 0.3) - (de_esc_count * 0.4) - (avg_sentiment * 2.5)
        index = max(1.0, min(10.0, round(index, 2))) # Clamp between 1 and 10

        return index, momentum, dict(Counter(all_words).most_common(50))

# --- 3. DATA ACQUISITION ---
class DataAggregator:
    def fetch_live_markets(self):
        # Added CL=F (WTI Crude) as a fallback if BZ=F (Brent) fails
        tickers = {"Crude Oil": ["BZ=F", "CL=F"], "Gold": ["GC=F"]}
        market_data = {}
        for name, symbols in tickers.items():
            for sym in symbols:
                try:
                    data = yf.Ticker(sym).history(period="5d")
                    if len(data) >= 2:
                        current, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
                        market_data[name] = {"price": current, "change": ((current - prev) / prev) * 100}
                        break # Success, stop trying fallbacks
                except: continue
        return market_data

    def fetch_global_news(self):
        try:
            feed = feedparser.parse("https://news.google.com/rss/search?q=Israel+Iran+US+conflict&hl=en-US&gl=US&ceid=US:en")
            return [{"Title": entry.title, "Published": entry.published, "Link": entry.link} for entry in feed.entries[:15]]
        except: return []

def get_ai_summary(headlines):
    """Optional AI overlay - isolated from core metrics."""
    try:
        client = genai.Client(api_key=st.secrets["gemini"]["api_key"])
        text_feed = " | ".join([h['Title'] for h in headlines])
        res = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=f"Provide a strict 2-sentence tactical summary of this news: {text_feed}"
        )
        return res.text
    except: return None

def save_to_vault(index, momentum):
    new_data = pd.DataFrame([{"Time": datetime.now(IST).strftime('%Y-%m-%d %H:%M'), "Escalation_Index": index, "Momentum": momentum}])
    df = pd.concat([pd.read_csv(VAULT_FILE), new_data], ignore_index=True) if os.path.exists(VAULT_FILE) else new_data
    df.to_csv(VAULT_FILE, index=False)
    return df

# --- 4. DASHBOARD RENDER ---
st_autorefresh(interval=5 * 60 * 1000, key="geo_refresh")

st.markdown("<h2 style='text-align: center; color: #ffffff; letter-spacing: 2px;'>🌐 GLOBAL THREAT MATRIX: LIVE</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #8b949e;'>LAST SYNC: {datetime.now(IST).strftime('%d %b %Y | %H:%M:%S IST')}</p>", unsafe_allow_html=True)

aggregator = DataAggregator()
nlp_engine = PythonNLPEngine()

# 1. Fetch Hard Data
markets = aggregator.fetch_live_markets()
news = aggregator.fetch_global_news()

# 2. Process via Local Python NLP (NEVER BLOCKED)
escalation_index, momentum, word_freq = nlp_engine.analyze_threat_level(news)
history_df = save_to_vault(escalation_index, momentum)

# --- UI: LEVEL 1 MACRO IMPACT ---
c1, c2, c3, c4 = st.columns(4)

e_color = "#ff7b72" if escalation_index >= 7 else "#d29922"
c1.markdown(f"<div class='metric-box'><div class='metric-title'>Escalation Index (1-10)</div><div class='metric-value' style='color: {e_color};'>{escalation_index}</div></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='metric-box'><div class='metric-title'>Media Momentum</div><div class='metric-value'>{momentum}</div></div>", unsafe_allow_html=True)

if "Crude Oil" in markets:
    oil = markets["Crude Oil"]
    c3.markdown(f"<div class='metric-box'><div class='metric-title'>Crude Oil</div><div class='metric-value'>${oil['price']:.2f} <span style='font-size: 1rem; color: #ff7b72;'>{oil['change']:.2f}%</span></div></div>", unsafe_allow_html=True)
else: c3.info("Oil market data offline.")

if "Gold" in markets:
    gold = markets["Gold"]
    c4.markdown(f"<div class='metric-box'><div class='metric-title'>Gold (Safe Haven)</div><div class='metric-value'>${gold['price']:.2f} <span style='font-size: 1rem; color: #3fb950;'>{gold['change']:.2f}%</span></div></div>", unsafe_allow_html=True)
else: c4.info("Gold market data offline.")

st.write("---")

# --- UI: LEVEL 2 TACTICAL TRENDS ---
colA, colB = st.columns([2, 1])

with colA:
    st.subheader("📈 Escalation Trendline (Locally Computed)")
    if not history_df.empty and len(history_df) > 1:
        fig = px.line(history_df, x="Time", y="Escalation_Index", markers=True, template="plotly_dark")
        fig.update_layout(yaxis_range=[1, 10], yaxis_title="Threat Level (1-10)")
        fig.add_hline(y=7.0, line_dash="dash", line_color="red", annotation_text="Critical Danger Zone")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("🤖 AI Strategic Summary (Add-On)")
    ai_summary = get_ai_summary(news)
    if ai_summary:
        st.info(ai_summary)
    else:
        st.warning("⚠️ AI Summary unavailable (API Quota limit). Dashboard running via Local NLP.")

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

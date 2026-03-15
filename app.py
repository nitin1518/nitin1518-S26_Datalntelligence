import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import feedparser
import re, os, pytz
from datetime import datetime
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
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
    .faction-us { color: #58a6ff; font-weight: bold; }
    .faction-iran { color: #ff7b72; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ADVANCED PYTHON NLP ENGINE ---
class TacticalNLPEngine:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
        # Faction Lexicons
        self.factions = {
            "US_ISRAEL": ['israel', 'idf', 'us', 'usa', 'washington', 'biden', 'trump', 'american', 'netanyahu'],
            "IRAN_PROXIES": ['iran', 'tehran', 'irgc', 'hezbollah', 'houthi', 'hamas']
        }
        
        # Tactical Action Lexicons
        self.tactics = {
            "offensive": ['strike', 'attack', 'launch', 'expands', 'offensive', 'destroys', 'bomb', 'warns', 'troops'],
            "defensive": ['denies', 'braces', 'intercepts', 'plea', 'defends', 'shield'],
            "losses": ['dead', 'casualties', 'hit', 'destroyed', 'killed', 'damage'],
            "diplomacy": ['ceasefire', 'peace', 'talks', 'negotiate', 'urges', 'summit']
        }
        
        # Global Contagion Lexicon (Middle East & Powers)
        self.nations = ['uae', 'saudi', 'yemen', 'lebanon', 'syria', 'iraq', 'russia', 'china', 'uk', 'france', 'egypt', 'jordan']

    def extract_tactical_posture(self, headlines):
        """Calculates Who has the Upper Hand based on Action Verbs"""
        posture = {"US_ISRAEL": {"offensive": 0, "defensive": 0, "losses": 0, "sentiment": 0, "count": 0},
                   "IRAN_PROXIES": {"offensive": 0, "defensive": 0, "losses": 0, "sentiment": 0, "count": 0}}
        
        contagion = []
        global_esc_score = 5.0

        for h in headlines:
            text = h['Title'].lower()
            words = set(re.findall(r'\b\w+\b', text))
            sent_score = self.analyzer.polarity_scores(text)['compound']
            
            # Extract Contagion (Other nations involved)
            contagion.extend([n.upper() for n in self.nations if n in words])

            # Attribute actions to factions
            for faction, keywords in self.factions.items():
                if any(k in words for k in keywords):
                    posture[faction]["count"] += 1
                    posture[faction]["sentiment"] += sent_score
                    if any(w in words for w in self.tactics["offensive"]): posture[faction]["offensive"] += 1
                    if any(w in words for w in self.tactics["defensive"]): posture[faction]["defensive"] += 1
                    if any(w in words for w in self.tactics["losses"]): posture[faction]["losses"] += 1

        # Determine "Upper Hand" (Higher Offensive : Loss ratio + Volume)
        us_score = (posture["US_ISRAEL"]["offensive"] * 2) - posture["US_ISRAEL"]["losses"] + posture["US_ISRAEL"]["count"]
        ir_score = (posture["IRAN_PROXIES"]["offensive"] * 2) - posture["IRAN_PROXIES"]["losses"] + posture["IRAN_PROXIES"]["count"]
        
        if us_score > ir_score + 2: upper_hand = "US/Israel Dominating Narrative"
        elif ir_score > us_score + 2: upper_hand = "Iran/Proxies Dominating Narrative"
        else: upper_hand = "Tactical Stalemate / Fog of War"

        # Calculate Escalation Index
        total_offenses = posture["US_ISRAEL"]["offensive"] + posture["IRAN_PROXIES"]["offensive"]
        total_diplomacy = sum(1 for h in headlines if any(w in h['Title'].lower() for w in self.tactics["diplomacy"]))
        
        esc_index = 5.0 + (total_offenses * 0.4) - (total_diplomacy * 0.5)
        esc_index = max(1.0, min(10.0, round(esc_index, 2)))

        return esc_index, upper_hand, posture, list(set(contagion))

# --- 3. DATA AGGREGATION ---
class MarketAggregator:
    def fetch_markets(self):
        tickers = {"Crude Oil": ["BZ=F", "CL=F"], "Gold": ["GC=F"]}
        market_data = {}
        for name, symbols in tickers.items():
            for sym in symbols:
                try:
                    data = yf.Ticker(sym).history(period="5d")
                    if len(data) >= 2:
                        current, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
                        market_data[name] = {"price": current, "change": ((current - prev) / prev) * 100}
                        break
                except: continue
        return market_data

    def fetch_news(self):
        try:
            feed = feedparser.parse("https://news.google.com/rss/search?q=Israel+Iran+US+conflict&hl=en-US&gl=US&ceid=US:en")
            return [{"Title": entry.title, "Published": entry.published, "Link": entry.link} for entry in feed.entries[:20]]
        except: return []

def save_to_vault(index, posture):
    us_sent = posture["US_ISRAEL"]["sentiment"] / max(1, posture["US_ISRAEL"]["count"])
    ir_sent = posture["IRAN_PROXIES"]["sentiment"] / max(1, posture["IRAN_PROXIES"]["count"])
    
    new_data = pd.DataFrame([{
        "Time": datetime.now(IST).strftime('%Y-%m-%d %H:%M'), 
        "Escalation_Index": index, 
        "US_Sentiment": us_sent,
        "Iran_Sentiment": ir_sent
    }])
    df = pd.concat([pd.read_csv(VAULT_FILE), new_data], ignore_index=True) if os.path.exists(VAULT_FILE) else new_data
    df.to_csv(VAULT_FILE, index=False)
    return df

# --- 4. DASHBOARD RENDER ---
st_autorefresh(interval=5 * 60 * 1000, key="geo_refresh")

st.markdown("<h2 style='text-align: center; color: #ffffff; letter-spacing: 2px;'>🌐 TACTICAL THREAT MATRIX: LIVE</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #8b949e;'>LAST SYNC: {datetime.now(IST).strftime('%d %b %Y | %H:%M:%S IST')}</p>", unsafe_allow_html=True)

aggregator = MarketAggregator()
nlp = TacticalNLPEngine()

markets = aggregator.fetch_markets()
news = aggregator.fetch_news()

esc_index, upper_hand, posture, contagion = nlp.extract_tactical_posture(news)
history_df = save_to_vault(esc_index, posture)

# --- UI: LEVEL 1 MACRO IMPACT ---
c1, c2, c3, c4 = st.columns(4)

e_color = "#ff7b72" if esc_index >= 7 else "#d29922"
c1.markdown(f"<div class='metric-box'><div class='metric-title'>Escalation Index (1-10)</div><div class='metric-value' style='color: {e_color};'>{esc_index}</div></div>", unsafe_allow_html=True)

uh_color = "#58a6ff" if "US" in upper_hand else ("#ff7b72" if "Iran" in upper_hand else "#ffffff")
c2.markdown(f"<div class='metric-box'><div class='metric-title'>Tactical Upper Hand</div><div class='metric-value' style='font-size: 1.2rem; color: {uh_color}; margin-top:10px;'>{upper_hand}</div></div>", unsafe_allow_html=True)

if "Crude Oil" in markets:
    oil = markets["Crude Oil"]
    c3.markdown(f"<div class='metric-box'><div class='metric-title'>Crude Oil (Market Fear)</div><div class='metric-value'>${oil['price']:.2f} <span style='font-size: 1rem; color: #ff7b72;'>{oil['change']:.2f}%</span></div></div>", unsafe_allow_html=True)
else: c3.info("Oil market offline.")

if "Gold" in markets:
    gold = markets["Gold"]
    c4.markdown(f"<div class='metric-box'><div class='metric-title'>Gold (Safe Haven)</div><div class='metric-value'>${gold['price']:.2f} <span style='font-size: 1rem; color: #3fb950;'>{gold['change']:.2f}%</span></div></div>", unsafe_allow_html=True)
else: c4.info("Gold market offline.")

st.write("---")

# --- UI: LEVEL 2 DEEP EDA & NLP INSIGHTS ---
colA, colB = st.columns([2, 1])

with colA:
    tab1, tab2 = st.tabs(["📉 Sentiment Divergence", "🕸️ Tactical Posture Radar"])
    
    with tab1:
        st.subheader("Media Sentiment Trajectory: Faction vs Faction")
        if len(history_df) > 1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=history_df['Time'], y=history_df['US_Sentiment'], mode='lines', name='US/Israel Sentiment', line=dict(color='#58a6ff', width=3)))
            fig.add_trace(go.Scatter(x=history_df['Time'], y=history_df['Iran_Sentiment'], mode='lines', name='Iran/Proxies Sentiment', line=dict(color='#ff7b72', width=3)))
            fig.update_layout(template="plotly_dark", yaxis_title="VADER Sentiment Score (-1 to 1)", hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Accumulating faction sentiment data...")

    with tab2:
        st.subheader("Live Combat Narrative Assessment")
        categories = ['Offensive Actions', 'Defensive Posture', 'Reported Losses', 'Media Volume']
        
        # Normalize data for radar chart visualization
        us_data = [posture["US_ISRAEL"]["offensive"], posture["US_ISRAEL"]["defensive"], posture["US_ISRAEL"]["losses"], posture["US_ISRAEL"]["count"]/2]
        ir_data = [posture["IRAN_PROXIES"]["offensive"], posture["IRAN_PROXIES"]["defensive"], posture["IRAN_PROXIES"]["losses"], posture["IRAN_PROXIES"]["count"]/2]

        fig2 = go.Figure()
        fig2.add_trace(go.Scatterpolar(r=us_data, theta=categories, fill='toself', name='US/Israel', line_color='#58a6ff'))
        fig2.add_trace(go.Scatterpolar(r=ir_data, theta=categories, fill='toself', name='Iran/Proxies', line_color='#ff7b72'))
        fig2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(max(us_data), max(ir_data))+1])), showlegend=True, template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)

    if contagion:
        st.error(f"⚠️ **Contagion Alert - Secondary Theaters Active:** {', '.join(contagion)}")

with colB:
    st.subheader("📡 Raw Signal Feed")
    if news:
        for article in news[:8]:
            title = article["Title"]
            # Highlight factions in headlines
            title = re.sub(r'(?i)(israel|us|usa|biden|trump|idf)', r'<span class="faction-us">\1</span>', title)
            title = re.sub(r'(?i)(iran|tehran|irgc|houthi)', r'<span class="faction-iran">\1</span>', title)
            
            st.markdown(f"""
            <div class='news-card'>
                <a href='{article["Link"]}' target='_blank' style='color: #c9d1d9; text-decoration: none;'>{title}</a><br>
                <span style='color: #8b949e; font-size: 0.8rem;'>{article["Published"]}</span>
            </div>
            """, unsafe_allow_html=True)

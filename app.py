import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from googleapiclient.discovery import build
import pytz, os, re
from collections import Counter
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="S26 War-Room: Global AI Pulse", layout="wide")
IST = pytz.timezone('Asia/Kolkata')
analyzer = SentimentIntensityAnalyzer()

# High-End UX Styling
st.markdown("""
    <style>
    .main { background-color: #f0f4f8; }
    .stMetric { background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .ai-brief { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 25px; border-radius: 15px; }
    .chart-summary { background: #dbeafe; padding: 15px; border-radius: 10px; margin-top: 10px; font-style: italic; color: #1e3a8a; border-left: 5px solid #3b82f6; }
    </style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION (2026 STABLE) ---
try:
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    # UPGRADED: Using Gemini 3 Flash for 2026 stable support
    model = genai.GenerativeModel('gemini-3-flash-preview') 
    yt_service = build('youtube', 'v3', developerKey=st.secrets["youtube"]["api_key"])
except Exception:
    st.error("Check secrets. Ensure model is set to 'gemini-3-flash-preview'.")
    st.stop()

# --- 3. THE INTELLIGENCE ENGINE ---
class S26Intelligence:
    def get_dynamic_insight(self, context_type, data_summary):
        """Generates dynamic AI insights for each chart."""
        prompt = f"As a product analyst, give a 1-sentence sharp insight for an S26 {context_type} based on this: {data_summary}. focus on risk or opportunity."
        try:
            return model.generate_content(prompt).text
        except: return "AI analysis temporarily unavailable."

    def fetch_data(self, query):
        all_data = []
        res = yt_service.search().list(q=query, part='id,snippet', maxResults=3, type='video').execute()
        for vid in res['items']:
            v_title = vid['snippet']['title']
            comm_res = yt_service.commentThreads().list(part='snippet', videoId=vid['id']['videoId'], maxResults=50).execute()
            for item in comm_res['items']:
                text = item['snippet']['topLevelComment']['snippet']['textDisplay']
                score = analyzer.polarity_scores(text)['compound']
                all_data.append({"Video": v_title[:35], "Comment": text, "Sentiment": score, "Time": datetime.now(IST)})
        return pd.DataFrame(all_data)

    def get_top_topics(self, df):
        """ML-lite: Extracts bigram topics from negative comments."""
        neg_text = " ".join(df[df['Sentiment'] < -0.2]['Comment'].str.lower())
        words = re.findall(r'\b\w{4,}\b', neg_text) # Only words 4+ chars
        bigrams = [" ".join(words[i:i+2]) for i in range(len(words)-1)]
        return Counter(bigrams).most_common(5)

# --- 4. THE COMMAND CENTER ---
st.title("🛡️ S26 Launch War-Room: Predictive AI Dashboard")

with st.sidebar:
    st.header("🎛️ Data Governance")
    if st.button("🚀 SYNC LIVE INTEL"):
        st.session_state['data'] = S26Intelligence().fetch_data("Samsung S26 Ultra India")
    
    st.divider()
    view_mode = st.radio("Sentiment Filter", ["All Mentions", "Negative Only (Risk)", "Positive Only (Wins)"])

if 'data' in st.session_state:
    df = st.session_state['data']
    
    # Filtering Logic
    if view_mode == "Negative Only (Risk)": display_df = df[df['Sentiment'] < -0.1]
    elif view_mode == "Positive Only (Wins)": display_df = df[df['Sentiment'] > 0.1]
    else: display_df = df

    # SECTION 1: AI STRATEGIC BRIEF
    if st.button("🪄 Generate Executive AI Intelligence Brief"):
        with st.spinner("AI analyzing global patterns..."):
            context = display_df.sort_values(by='Sentiment').head(10)['Comment'].str.cat(sep=' | ')
            st.session_state['ai_brief'] = model.generate_content(f"Summarize top 3 S26 launch risks and technical issues: {context}").text
    
    if 'ai_brief' in st.session_state:
        st.markdown(f'<div class="ai-brief"><h3>✨ AI Intelligence Brief</h3>{st.session_state["ai_brief"]}</div>', unsafe_allow_html=True)

    # SECTION 2: INTERACTIVE ANALYTICS
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Sentiment Variance")
        fig1 = px.box(display_df, x="Video", y="Sentiment", color="Video", template="plotly_white", points="all")
        st.plotly_chart(fig1, use_container_width=True)
        # Dynamic Explanation
        st.markdown(f'<div class="chart-summary"><b>AI Chart Insight:</b> {S26Intelligence().get_dynamic_insight("Variance Chart", "Mean sentiment is " + str(round(display_df["Sentiment"].mean(),2)))}</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("🔥 Top 5 Growing Negative Topics")
        topics = S26Intelligence().get_top_topics(df)
        if topics:
            topic_df = pd.DataFrame(topics, columns=['Topic', 'Mentions'])
            fig2 = px.bar(topic_df, x='Mentions', y='Topic', orientation='h', color='Mentions', color_continuous_scale='Reds')
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown(f'<div class="chart-summary"><b>AI Chart Insight:</b> {S26Intelligence().get_dynamic_insight("Topic Bar", "Top detected issue is " + topics[0][0])}</div>', unsafe_allow_html=True)
        else: st.info("No critical negative topics detected.")

    # SECTION 3: DEEP-DIVE EXPLORER
    st.subheader("🔍 Deep-Dive: Verbatim Explorer")
    st.dataframe(display_df.sort_values(by='Sentiment'), use_container_width=True, hide_index=True)

else:
    st.info("👋 Dashboard Standby. Click 'Sync Live Intel' to begin.")

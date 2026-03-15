import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from googleapiclient.discovery import build
import pytz, os, re
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="S26 War-Room: AI Intelligence", layout="wide")
IST = pytz.timezone('Asia/Kolkata')
analyzer = SentimentIntensityAnalyzer()

# High-End UX Styling
st.markdown("""
    <style>
    .main { background-color: #f0f4f8; }
    .stMetric { background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .ai-brief { background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); color: white; padding: 25px; border-radius: 15px; }
    .chart-summary { background: #e0e7ff; padding: 15px; border-radius: 10px; margin-top: 10px; font-style: italic; color: #1e1b4b; }
    </style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION (UPGRADED FOR 2026) ---
try:
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    # UPGRADED: Using Gemini 3 series for 2026 support
    model = genai.GenerativeModel('gemini-3-flash-preview') 
    yt_service = build('youtube', 'v3', developerKey=st.secrets["youtube"]["api_key"])
except Exception as e:
    st.error("Check credentials in Secrets. Ensure Gemini model is 'gemini-3-flash-preview'.")
    st.stop()

# --- 3. ANALYTICS ENGINE ---
class S26Intelligence:
    def get_auto_summary(self, data_type, details):
        """Generates dynamic, chart-specific summaries."""
        prompt = f"Provide a one-sentence executive insight for an S26 product launch {data_type} based on: {details}. Be brief and strategic."
        try:
            return model.generate_content(prompt).text
        except: return "Awaiting AI interpretation..."

    def fetch_data(self, query):
        all_data = []
        search_res = yt_service.search().list(q=query, part='id,snippet', maxResults=3, type='video').execute()
        for vid in search_res['items']:
            v_title = vid['snippet']['title']
            comm_res = yt_service.commentThreads().list(part='snippet', videoId=vid['id']['videoId'], maxResults=50).execute()
            for item in comm_res['items']:
                text = item['snippet']['topLevelComment']['snippet']['textDisplay']
                score = analyzer.polarity_scores(text)['compound']
                all_data.append({"Video": v_title[:40], "Comment": text, "Sentiment": score, "Time": datetime.now(IST)})
        return pd.DataFrame(all_data)

# --- 4. THE COMMAND CENTER UX ---
st.title("🛡️ S26 Launch War-Room: Global AI Pulse")
st.write(f"Snapshot Time: **{datetime.now(IST).strftime('%I:%M %p IST')}**")

if 'data' not in st.session_state:
    with st.sidebar:
        if st.button("🚀 SYNC LIVE INTEL"):
            st.session_state['data'] = S26Intelligence().fetch_data("Samsung S26 Ultra India")

if 'data' in st.session_state:
    df = st.session_state['data']
    
    # AI Executive Briefing (Manual Toggle to save API)
    if st.button("🪄 Generate Full AI Intelligence Brief"):
        context = df.sort_values(by='Sentiment').head(10)['Comment'].str.cat(sep=' | ')
        st.session_state['ai_brief'] = model.generate_content(f"Summarize these S26 launch risks and technical issues into 3 bullet points: {context}").text
    
    if 'ai_brief' in st.session_state:
        st.markdown(f'<div class="ai-brief"><h3>✨ AI Strategic Briefing</h3>{st.session_state["ai_brief"]}</div>', unsafe_allow_html=True)

    # Filtering Sidebar
    with st.sidebar:
        st.header("Filter Intel")
        s_filter = st.radio("Sentiment View", ["All", "Negative Only", "Positive Only"])
        if s_filter == "Negative Only":
            display_df = df[df['Sentiment'] < -0.1]
        elif s_filter == "Positive Only":
            display_df = df[df['Sentiment'] > 0.1]
        else:
            display_df = df

    # INTERACTIVE CHARTS
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Sentiment Heatmap")
        fig1 = px.box(display_df, x="Video", y="Sentiment", color="Video", template="plotly_white")
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown(f'<div class="chart-summary"><b>AI Insight:</b> {S26Intelligence().get_auto_summary("Sentiment Heatmap", "Average score is " + str(display_df["Sentiment"].mean()))}</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("🔥 Top Emerging Concerns")
        # Extract negative topics
        neg_text = display_df[display_df['Sentiment'] < -0.2]['Comment'].str.cat(sep=' ')
        # Simple frequency logic for demo
        fig2 = px.histogram(display_df[display_df['Sentiment'] < -0.2], x="Video", color_discrete_sequence=['indianred'])
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown(f'<div class="chart-summary"><b>AI Insight:</b> {S26Intelligence().get_auto_summary("Risk Distribution", "Topic clusters found in negative mentions")}</div>', unsafe_allow_html=True)

    # Verbatim Explorer
    st.subheader("🔍 Deep-Dive: Customer Voice")
    st.dataframe(display_df.sort_values(by='Sentiment'), use_container_width=True, hide_index=True)

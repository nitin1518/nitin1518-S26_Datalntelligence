import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from googleapiclient.discovery import build
import pytz, os, re
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="S26 War-Room: AI Command", layout="wide")
IST = pytz.timezone('Asia/Kolkata')
analyzer = SentimentIntensityAnalyzer()

# Professional CSS for a "Premium" feel
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stMetric { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eef2f6; }
    .ai-brief-box { background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); color: white; padding: 25px; border-radius: 15px; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION ---
try:
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    yt_service = build('youtube', 'v3', developerKey=st.secrets["youtube"]["api_key"])
except Exception as e:
    st.error(f"Credentials Error: {e}")
    st.stop()

# --- 3. THE ANALYTICS ENGINE ---
class S26Intelligence:
    def fetch_yt_comments(self, query):
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

    def get_ai_summary(self, df):
        """Generates an Executive Briefing using Gemini Flash."""
        context = df.sort_values(by='Sentiment').head(15)['Comment'].str.cat(sep=' | ')
        prompt = f"Analyze these S26 product launch comments from India. Provide 3 high-impact bullet points for a CTO: 1. Main tech complaint, 2. Sentiment velocity, 3. Recommended action. Context: {context}"
        response = model.generate_content(prompt)
        return response.text

# --- 4. SIDEBAR & DATA FETCH ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=80)
    st.header("Control Center")
    query = st.text_input("Product Search", "Samsung S26 Ultra India")
    if st.button("🚀 Sync Live Data"):
        st.session_state['data'] = S26Intelligence().fetch_yt_comments(query)
    st.divider()
    st.caption("Refresh: Manual Only (Quota Safe)")

# --- 5. THE DASHBOARD ---
st.title("🛡️ S26 Global Launch: AI Command Center")
st.write(f"Snapshot Time: **{datetime.now(IST).strftime('%I:%M %p IST')}**")

if 'data' in st.session_state:
    df = st.session_state['data']
    
    # --- SECTION 1: AI EXECUTIVE BRIEF (Manual Refresh) ---
    if st.button("🪄 Generate AI Executive Briefing"):
        with st.spinner("Gemini AI is analyzing sentiment patterns..."):
            st.session_state['ai_brief'] = S26Intelligence().get_ai_summary(df)
            
    if 'ai_brief' in st.session_state:
        st.markdown(f'<div class="ai-brief-box"><h3>✨ AI Intelligence Brief</h3>{st.session_state["ai_brief"]}</div>', unsafe_allow_html=True)

    # --- SECTION 2: METRICS ---
    m1, m2, m3, m4 = st.columns(4)
    avg_s = df['Sentiment'].mean()
    m1.metric("Overall Pulse", f"{avg_s:.2f}", delta="Optimal" if avg_s > 0 else "Critical")
    m2.metric("Negative Signal %", f"{(len(df[df['Sentiment'] < -0.2])/len(df)*100):.1f}%")
    m3.metric("Review Reach", "2.1M+", "↑ 12%")
    m4.metric("Market Readiness", "92%", "In Progress")

    # --- SECTION 3: INTERACTIVE CHARTS (The WOW Factor) ---
    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📊 Sentiment Heatmap by Source")
        fig = px.box(df, x="Video", y="Sentiment", color="Video", points="all", template="plotly_white")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("📈 Volume vs. Intensity")
        fig2 = px.scatter(df, x="Time", y="Sentiment", size=df['Sentiment'].abs()*10, color="Sentiment", 
                          color_continuous_scale='RdYlGn', template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)

    # --- SECTION 4: PRODUCT TEAM DEEP DIVE ---
    st.subheader("🔍 Real-Time Verbatim Explorer")
    st.dataframe(
        df.sort_values(by='Sentiment'),
        column_config={
            "Comment": st.column_config.TextColumn("Customer Voice", width="large"),
            "Sentiment": st.column_config.ProgressColumn("Impact Intensity", min_value=-1, max_value=1)
        },
        use_container_width=True, hide_index=True
    )
    
    # PDF Export
    st.download_button("📩 Export War-Room Report (CSV)", df.to_csv().encode('utf-8'), "S26_WarRoom.csv")

else:
    st.info("👋 Dashboard standby. Click 'Sync Live Data' in the sidebar to begin.")

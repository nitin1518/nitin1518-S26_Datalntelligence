import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from googleapiclient.discovery import build
import pytz, json
from datetime import datetime

# --- 1. CONFIG & WAR-ROOM THEME ---
st.set_page_config(page_title="S26 Launch: Global Command", layout="wide", initial_sidebar_state="collapsed")
IST = pytz.timezone('Asia/Kolkata')

# Dark Mode / Command Center UI
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    .metric-box { background-color: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .metric-title { font-size: 0.9rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 2rem; font-weight: bold; color: #ffffff; }
    .critical-alert { border-left: 5px solid #ff7b72; background-color: rgba(255, 123, 114, 0.1); padding: 15px; border-radius: 5px; margin-bottom: 10px;}
    </style>
""", unsafe_allow_html=True)

# --- 2. SECRETS & AUTH ---
try:
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    # Using Gemini configured to return STRICT JSON
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    yt_service = build('youtube', 'v3', developerKey=st.secrets["youtube"]["api_key"])
except Exception:
    st.error("⚠️ System Offline: Verify API Keys.")
    st.stop()

# --- 3. THE AI-POWERED SENSING ENGINE ---
class MarketSensor:
    def fetch_raw_data(self, query, max_results=40):
        """Pulls raw data from YouTube (No cleaning needed, LLM handles it)."""
        raw_comments = []
        res = yt_service.search().list(q=query, part='id', maxResults=2, type='video').execute()
        for vid in res['items']:
            try:
                comm_res = yt_service.commentThreads().list(part='snippet', videoId=vid['id']['videoId'], maxResults=max_results).execute()
                for item in comm_res['items']:
                    raw_comments.append(item['snippet']['topLevelComment']['snippet']['textOriginal'])
            except: continue
        return raw_comments

    def process_with_llm(self, comments):
        """The 'Steroid' Engine: Forces AI to structure unstructured data."""
        prompt = f"""
        You are a CXO-level product analyst. Analyze this list of comments regarding a new smartphone launch in India.
        Account for Hinglish, slang, and sarcasm. 
        Return a JSON array of objects. For each comment, provide:
        - "category": Categorize strictly as one of: [Camera, Battery, Display, Performance, Price, OS/Software, Design, Generic].
        - "sentiment": A float from -1.0 (Critical Defect) to 1.0 (Perfect).
        - "root_cause": If sentiment < 0, summarize the exact technical issue in 2-4 words (e.g., "High battery drain"). If positive, write "None".
        - "is_urgent": Boolean (true if it mentions hardware failure, extreme overheating, or return/refund).
        
        Comments: {json.dumps(comments)}
        """
        try:
            response = model.generate_content(prompt)
            return pd.DataFrame(json.loads(response.text))
        except Exception as e:
            st.error(f"AI Processing Error: {e}")
            return pd.DataFrame()

# --- 4. DASHBOARD EXECUTION ---
st.markdown("<h1 style='text-align: center; color: #ffffff;'>🛡️ S26 GLOBAL LAUNCH: LIVE VOC MATRIX</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #8b949e;'>SYNC TIME: {datetime.now(IST).strftime('%d %b %Y | %H:%M:%S IST')}</p>", unsafe_allow_html=True)

if 'processed_data' not in st.session_state:
    with st.spinner("🤖 AI is ingesting and semantically analyzing live market data..."):
        sensor = MarketSensor()
        raw_text = sensor.fetch_raw_data("Samsung S26 Ultra India review")
        st.session_state['processed_data'] = sensor.process_with_llm(raw_text)
        # Re-attach raw text for display purposes
        if not st.session_state['processed_data'].empty:
            st.session_state['processed_data']['Raw_Comment'] = raw_text[:len(st.session_state['processed_data'])]

if not st.session_state['processed_data'].empty:
    df = st.session_state['processed_data']
    
    # --- LEVEL 1: CXO HIGH-LEVEL KPIs ---
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-box'><div class='metric-title'>Market Pulse (-1 to 1)</div><div class='metric-value'>{df['sentiment'].mean():.2f}</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-box'><div class='metric-title'>Urgent Red Flags</div><div class='metric-value' style='color: #ff7b72;'>{df['is_urgent'].sum()}</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-box'><div class='metric-title'>Top Complained Aspect</div><div class='metric-value'>{df[df['sentiment'] < 0]['category'].mode()[0] if not df[df['sentiment'] < 0].empty else 'N/A'}</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-box'><div class='metric-title'>Signal Volume</div><div class='metric-value'>{len(df)}</div></div>", unsafe_allow_html=True)

    st.write("---")

    # --- LEVEL 2: PRODUCT TEAM DIAGNOSTICS ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📡 The Threat Matrix: Aspect vs. Sentiment")
        # Aggregate data for the matrix
        matrix_df = df.groupby('category').agg(
            Avg_Sentiment=('sentiment', 'mean'),
            Mentions=('category', 'count')
        ).reset_index()
        
        fig = px.scatter(
            matrix_df, x="Avg_Sentiment", y="Mentions", color="category", size="Mentions",
            text="category", template="plotly_dark", 
            title="<br>← CRISIS ZONE (High Volume / Negative) | SAFE ZONE (Positive) →",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textposition='top center')
        fig.add_vline(x=0, line_width=2, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🚨 Critical Live Ticker")
        urgent_df = df[df['is_urgent'] == True]
        if not urgent_df.empty:
            for _, row in urgent_df.iterrows():
                st.markdown(f"""
                <div class='critical-alert'>
                    <strong>[{row['category'].upper()}]</strong> {row['root_cause']}<br>
                    <span style='color: #8b949e; font-size: 0.8rem;'>"{row['Raw_Comment']}"</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No urgent hardware/software failures detected in current sync.")

    # --- LEVEL 3: ROOT CAUSE LOG ---
    st.write("---")
    st.subheader("🛠️ Product Debug Log (Negative Sentiment Only)")
    debug_df = df[df['sentiment'] < -0.1][['category', 'root_cause', 'sentiment', 'Raw_Comment']].sort_values(by='sentiment')
    st.dataframe(debug_df, use_container_width=True, hide_index=True)

    if st.button("🔄 Trigger Fresh Network Sync"):
        del st.session_state['processed_data']
        st.rerun()

else:
    st.error("Data pipeline failed to structure the payload. Please retry.")

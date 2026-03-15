import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import pytz
import os
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from streamlit_autorefresh import st_autorefresh

# --- 1. SETTINGS & THEME ---
st.set_page_config(page_title="S26 Launch Command", layout="wide")
IST = pytz.timezone('Asia/Kolkata')
analyzer = SentimentIntensityAnalyzer()

# Folder for Local Data Backups
CACHE_DIR = "launch_data_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# --- 2. AUTHENTICATION ---
try:
    YT_KEY = st.secrets["youtube"]["api_key"]
    yt_service = build('youtube', 'v3', developerKey=YT_KEY)
except Exception as e:
    st.error("⚠️ YouTube API Key Missing in Secrets.")
    st.stop()

# --- 3. DATA ENGINE ---
class S26Intelligence:
    def fetch_yt_comments(self, query="S26 Ultra India"):
        all_data = []
        try:
            # Step A: Find the most relevant videos
            search_res = yt_service.search().list(q=query, part='id,snippet', maxResults=3, type='video').execute()
            
            for vid in search_res['items']:
                v_id = vid['id']['videoId']
                v_title = vid['snippet']['title']
                
                # Step B: Get top comments for each video
                comm_res = yt_service.commentThreads().list(
                    part='snippet', videoId=v_id, maxResults=50, order='relevance'
                ).execute()
                
                for item in comm_res['items']:
                    text = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    score = analyzer.polarity_scores(text)['compound']
                    
                    all_data.append({
                        "Source": "YouTube",
                        "Video_Title": v_title,
                        "Comment": text,
                        "Sentiment": score,
                        "Signal": "CRITICAL" if score < -0.35 else ("WARNING" if score < -0.05 else "STABLE"),
                        "Timestamp": datetime.now(IST).strftime('%Y-%m-%d %H:%M')
                    })
            return pd.DataFrame(all_data)
        except Exception as e:
            st.error(f"YouTube API Error: {e}")
            return pd.DataFrame()

# --- 4. SIDEBAR & CACHE CONTROLS ---
with st.sidebar:
    st.header("📦 Data Control Center")
    data_mode = st.radio("Select Data Source", ["Live API Scrape", "Load Local Cache"])
    
    if data_mode == "Live API Scrape":
        if st.button("🚀 Trigger Launch Sync"):
            engine = S26Intelligence()
            new_df = engine.fetch_yt_comments()
            if not new_df.empty:
                st.session_state['active_data'] = new_df
                # Save to local file
                fname = f"{CACHE_DIR}/S26_Sync_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                new_df.to_csv(fname, index=False)
                st.success(f"Sync Complete. Backup saved.")

    else:
        # Load most recent file from cache
        files = [f for f in os.listdir(CACHE_DIR) if f.endswith('.csv')]
        if files:
            selected_file = st.selectbox("Select Historical Snapshot", sorted(files, reverse=True))
            if st.button("📂 Load Selected Snapshot"):
                st.session_state['active_data'] = pd.read_csv(os.path.join(CACHE_DIR, selected_file))
        else:
            st.warning("No local cache found. Please run a Live Scrape first.")

# --- 5. THE EXECUTIVE DASHBOARD ---
st.title("🛡️ S26 Launch War-Room: Global Sentiment")
st.caption(f"Status: {data_mode} | Local IST: {datetime.now(IST).strftime('%I:%M %p')}")

if 'active_data' in st.session_state:
    df = st.session_state['active_data']
    
    # 1. Metric Row
    m1, m2, m3 = st.columns(3)
    avg_s = df['Sentiment'].mean()
    m1.metric("Overall Pulse", f"{avg_s:.2f}", delta="Actionable" if avg_s < 0 else "Stable")
    m2.metric("Critical Alerts", len(df[df['Signal'] == "CRITICAL"]))
    m3.metric("Verified Voices", len(df))

    # 2. Charts
    tab1, tab2 = st.tabs(["📊 Sentiment Distribution", "🔍 Comment Deep-Dive"])
    
    with tab1:
        st.subheader("Crisis Heatmap by Video Source")
        st.bar_chart(df.groupby('Video_Title')['Sentiment'].mean())

    with tab2:
        # Professional Data Grid
        st.dataframe(
            df[['Signal', 'Video_Title', 'Comment', 'Sentiment', 'Timestamp']],
            column_config={
                "Comment": st.column_config.TextColumn("Customer Verbatim", width="large"),
                "Sentiment": st.column_config.ProgressColumn("Intensity", min_value=-1, max_value=1),
            },
            use_container_width=True, hide_index=True
        )
else:
    st.info("👋 Dashboard Ready. Use the sidebar to trigger a sync or load cached data.")

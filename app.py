import streamlit as st
import pandas as pd
import praw
from googleapiclient.discovery import build
import pytz
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from streamlit_autorefresh import st_autorefresh


# --- 1. CONFIG & AUTHENTICATION ---
st.set_page_config(page_title="S26 War-Room: Command Center", layout="wide")

IST = pytz.timezone('Asia/Kolkata')
analyzer = SentimentIntensityAnalyzer()

# FIXED: Standardized key mapping to prevent 401 errors
try:
    REDDIT_AUTH = {
        "client_id": st.secrets["reddit"]["client_id"],
        "client_secret": st.secrets["reddit"]["client_secret"],
        "user_agent": st.secrets["reddit"]["user_agent"],
        "username": st.secrets["reddit"]["username"], # Standard key
        "password": st.secrets["reddit"]["password"]  # Standard key
    }
    YOUTUBE_API_KEY = st.secrets["youtube"]["api_key"]
except Exception as e:
    st.error(f"⚠️ Configuration Error: {e}. Check your Streamlit Secrets.")
    st.stop()

# --- 2. THE MAX-DATA ENGINE ---
class S26IntelligenceEngine:
    def __init__(self):
        self.reddit = praw.Reddit(**REDDIT_AUTH)
        self.yt = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    def get_signal(self, score):
        if score < -0.35: return "CRITICAL", "🔴"
        if score < -0.05: return "WARNING", "🟠"
        return "STABLE", "🟢"

    def fetch_deep_reddit(self, query):
        data = []
        try:
            # Search for relevant threads
            submissions = self.reddit.subreddit("all").search(query, limit=5, sort="relevance")
            for sub in submissions:
                # Crawl comments deep into the thread
                sub.comments.replace_more(limit=0) 
                for comment in sub.comments.list()[:50]:
                    score = analyzer.polarity_scores(comment.body)['compound']
                    label, icon = self.get_signal(score)
                    data.append({
                        "Source": f"r/{sub.subreddit.display_name}",
                        "Topic": sub.title,
                        "Verbatim": comment.body,
                        "Sentiment": score,
                        "Signal": label,
                        "Icon": icon,
                        "IST_Time": datetime.fromtimestamp(comment.created_utc, IST).strftime('%I:%M %p')
                    })
        except Exception as e: 
            st.sidebar.warning(f"Reddit Sync Error: {e}")
        return pd.DataFrame(data)

# --- 3. THE MANAGEMENT DASHBOARD ---
st.title("🛡️ S26 Global Launch Command Center")
st.caption(f"Authenticated Feed | IST: {datetime.now(IST).strftime('%I:%M %p')} | Refresh: 5m")

# Live Refresh Every 5 Minutes
st_autorefresh(interval=5 * 60 * 1000, key="global_refresh")

with st.sidebar:
    st.header("🎛️ Command Controls")
    search_query = st.text_input("Product Query", value="S26 Ultra India")
    signal_filter = st.multiselect("Active Signals", ["CRITICAL", "WARNING", "STABLE"], default=["CRITICAL", "WARNING"])
    min_sent = st.slider("Sentiment Intensity Filter", -1.0, 1.0, -1.0)

engine = S26IntelligenceEngine()

with st.spinner('Tunneling into global threads for maximum insights...'):
    df = engine.fetch_deep_reddit(search_query)

if not df.empty:
    filtered_df = df[(df['Signal'].isin(signal_filter)) & (df['Sentiment'] >= min_sent)]
    
    # Executive KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Overall Pulse", f"{df['Sentiment'].mean():.2f}")
    k2.metric("Critical Alerts", len(filtered_df[filtered_df['Signal'] == "CRITICAL"]))
    k3.metric("Insights Scanned", len(df))

    tab1, tab2 = st.tabs(["📊 Analytics Heatmap", "🔍 Comment Deep-Dive"])
    
    with tab1:
        st.subheader("Source Sentiment Benchmarking")
        if not df.empty:
            st.bar_chart(df.groupby('Source')['Sentiment'].mean())
        else:
            st.info("Awaiting source data...")

    with tab2:
        st.subheader("Interactive Comment Explorer")
        st.dataframe(
            filtered_df[['Icon', 'Signal', 'Source', 'Verbatim', 'Sentiment', 'IST_Time']],
            column_config={
                "Verbatim": st.column_config.TextColumn("Customer Comment", width="large"),
                "Sentiment": st.column_config.ProgressColumn("Sentiment Intensity", min_value=-1, max_value=1),
            },
            use_container_width=True, hide_index=True
        )
        
        # Download Report
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📩 Download PDF/CSV Report", csv, "S26_WarRoom_Report.csv", "text/csv")
else:
    st.warning("No data found. Ensure your Reddit Username/Password are correctly set in Secrets.")

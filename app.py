import streamlit as st
import pandas as pd
import praw
from googleapiclient.discovery import build
import pytz
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & AUTHENTICATION (FIXED) ---
st.set_page_config(page_title="S26 War-Room: Global Command", layout="wide")

IST = pytz.timezone('Asia/Kolkata')
analyzer = SentimentIntensityAnalyzer()

# Accessing secrets using generic keys defined in your setup
try:
    REDDIT_AUTH = {
        "client_id": st.secrets["reddit"]["client_id"],
        "client_secret": st.secrets["reddit"]["client_secret"],
        "user_agent": st.secrets["reddit"]["user_agent"],
        "username": st.secrets["reddit"]["username"], # Refers to nitinsharma1518
        "password": st.secrets["reddit"]["password"]  # Refers to $Fireblade-1000
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
            # Search for relevant launch threads
            submissions = self.reddit.subreddit("all").search(query, limit=5, sort="relevance")
            for sub in submissions:
                # Replace MoreComments to get the full conversation tree
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

# --- 3. UI/UX DASHBOARD ---
st.title("🛡️ S26 Global Launch Command Center")
st.caption(f"Authenticated Feed | IST: {datetime.now(IST).strftime('%I:%M %p')} | Auto-refresh: 5m")

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

    tab1, tab2 = st.tabs(["📊 Analytics", "🔍 Comment Deep-Dive"])
    
    with tab1:
        st.subheader("Source Sentiment Benchmarking")
        st.bar_chart(df.groupby('Source')['Sentiment'].mean())

    with tab2:
        st.dataframe(
            filtered_df[['Icon', 'Signal', 'Source', 'Verbatim', 'Sentiment', 'IST_Time']],
            column_config={
                "Verbatim": st.column_config.TextColumn("Customer Comment", width="large"),
                "Sentiment": st.column_config.ProgressColumn("Sentiment Intensity", min_value=-1, max_value=1),
            },
            use_container_width=True, hide_index=True
        )
        
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📩 Download PDF/CSV Report", csv, "S26_WarRoom_Report.csv", "text/csv")
else:
    st.warning("No data found. Check your authentication keys.")

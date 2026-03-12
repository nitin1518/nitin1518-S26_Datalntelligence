import streamlit as st
import pandas as pd
import praw
from googleapiclient.discovery import build
import pytz
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & CREDENTIALS ---
st.set_page_config(page_title="S26 War-Room: Global Command", layout="wide")

# India Timezone Setup
IST = pytz.timezone('Asia/Kolkata')
analyzer = SentimentIntensityAnalyzer()

# Your Provided Credentials (Using st.secrets for safety)
# Replace placeholder username/password with your actual Reddit credentials
try:
    REDDIT_AUTH = {
        "client_id": st.secrets["reddit"]["client_id"],
        "client_secret": st.secrets["reddit"]["client_secret"],
        "user_agent": st.secrets["reddit"]["user_agent"],
        "username": st.secrets["reddit"]["username"], # Use the generic key name
        "password": st.secrets["reddit"]["password"]  # Use the generic key name
    }
    YOUTUBE_API_KEY = st.secrets["youtube"]["api_key"]
except Exception as e:
    st.error(f"⚠️ Configuration Error: {e}")
    st.stop()

# --- 2. THE MULTI-SOURCE ENGINE ---
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
            # Authenticated search across 'all'
            submissions = self.reddit.subreddit("all").search(query, limit=5, sort="relevance")
            for sub in submissions:
                # 🟢 Max Data: Replace 'limit=0' with 'limit=None' for absolute full thread crawl
                sub.comments.replace_more(limit=0) 
                for comment in sub.comments.list()[:50]: # Scrapes up to 50 comments per top post
                    score = analyzer.polarity_scores(comment.body)['compound']
                    label, icon = self.get_signal(score)
                    data.append({
                        "Source": f"r/{sub.subreddit.display_name}",
                        "Topic": sub.title,
                        "Verbatim": comment.body,
                        "Sentiment": score,
                        "Signal": label,
                        "Icon": icon,
                        "IST_Time": datetime.fromtimestamp(comment.created_utc, IST).strftime('%H:%M %p')
                    })
        except Exception as e: st.sidebar.warning(f"Reddit Sync Error: {e}")
        return pd.DataFrame(data)

# --- 3. UI/UX DESIGN ---
st.title("🛡️ S26 Global Launch Command Center")
st.caption(f"Authenticated Feed | IST: {datetime.now(IST).strftime('%I:%M %p')} | Refresh: 5m")

# Live Refresh
st_autorefresh(interval=5 * 60 * 1000, key="global_refresh")

with st.sidebar:
    st.header("🎛️ Command Controls")
    search_query = st.text_input("Product Query", value="S26 Ultra India")
    signal_filter = st.multiselect("Active Signals", ["CRITICAL", "WARNING", "STABLE"], default=["CRITICAL", "WARNING"])
    min_sent = st.slider("Min Sentiment Intensity", -1.0, 1.0, -1.0)

engine = S26IntelligenceEngine()

with st.spinner('Tunneling into global threads for maximum insights...'):
    df = engine.fetch_deep_reddit(search_query)

# --- 4. INSIGHTS & FILTERS ---
if not df.empty:
    # Filter Logic
    filtered_df = df[(df['Signal'].isin(signal_filter)) & (df['Sentiment'] >= min_sent)]
    
    # Executive KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Overall Sentiment", f"{df['Sentiment'].mean():.2f}", delta="Actionable" if df['Sentiment'].mean() < 0 else "Stable")
    k2.metric("Critical Warnings", len(filtered_df[filtered_df['Signal'] == "CRITICAL"]))
    k3.metric("Comments Scanned", len(df))

    # Tabs for Management Presentation
    tab1, tab2 = st.tabs(["📊 Sentiment Analytics", "🔍 Comment Deep-Dive"])
    
    with tab1:
        st.subheader("Source Sentiment Benchmarking")
        st.bar_chart(df.groupby('Source')['Sentiment'].mean())
        st.info("💡 Insights: Higher bars indicate positive community reception.")

    with tab2:
        st.subheader("Interactive Comment Explorer")
        st.dataframe(
            filtered_df[['Icon', 'Signal', 'Source', 'Topic', 'Verbatim', 'Sentiment', 'IST_Time']],
            column_config={
                "Verbatim": st.column_config.TextColumn("Customer Comment", width="large"),
                "Sentiment": st.column_config.ProgressColumn("Sentiment Intensity", min_value=-1, max_value=1),
            },
            use_container_width=True, hide_index=True
        )
        
        # Download for C-Level Email
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📩 Download PDF/CSV Report", csv, "S26_WarRoom_Report.csv", "text/csv")
else:
    st.warning("No data found. Ensure your Reddit Username/Password are correctly set in Secrets.")

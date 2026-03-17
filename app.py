import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from textblob import TextBlob
from googleapiclient.discovery import build
import feedparser
from datetime import datetime
import urllib.parse
import re

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Live Market Intelligence", 
    page_icon="📡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. HYBRID EXTRACTION ENGINES (Cached)
# ==========================================
def extract_video_ids_from_text(text):
    """Uses Regex to cleanly extract YouTube 11-character IDs from messy URLs or raw text."""
    if not text: return []
    # Matches standard YouTube URLs, shortened youtu.be URLs, and embed links
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    matches = re.findall(regex, text)
    # Also catch raw 11-character IDs if pasted directly
    raw_ids = [word.strip() for word in text.replace(',', ' ').split() if len(word.strip()) == 11 and re.match(r'^[0-9A-Za-z_-]{11}$', word.strip())]
    return list(set(matches + raw_ids))

@st.cache_data(ttl=3600, show_spinner=False)
def auto_discover_videos(api_key, query, max_videos=10):
    """Silently searches YouTube for the top ranking videos."""
    if not api_key or not query: return []
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.search().list(
            part="id",
            q=query + " review", 
            type="video",
            relevanceLanguage="en",
            maxResults=max_videos,
            order="relevance" 
        )
        response = request.execute()
        return [item['id']['videoId'] for item in response.get('items', [])]
    except Exception as e:
        st.error(f"YouTube Search API Error: {e}")
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def get_video_metadata(api_key, video_ids):
    """Fetches Channel Names, Titles, and Subscriber counts for ANY list of video IDs."""
    if not api_key or not video_ids: return pd.DataFrame()
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        video_metadata = []
        channel_ids = []
        
        # 1. Get Video Details (Title, Channel ID)
        # API allows max 50 IDs per request. We slice safely just in case.
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i:i+50]
            vid_request = youtube.videos().list(part="snippet", id=",".join(chunk))
            vid_response = vid_request.execute()
            
            for item in vid_response.get('items', []):
                ch_id = item['snippet']['channelId']
                video_metadata.append({
                    "Video ID": item['id'],
                    "Video Title": item['snippet']['title'],
                    "Channel Name": item['snippet']['channelTitle'],
                    "Channel ID": ch_id
                })
                channel_ids.append(ch_id)
                
        # 2. Get Channel Statistics (Subscribers)
        if channel_ids:
            sub_data = {}
            # Unique channels only to save quota
            unique_channels = list(set(channel_ids))
            for i in range(0, len(unique_channels), 50):
                ch_chunk = unique_channels[i:i+50]
                ch_request = youtube.channels().list(part="statistics", id=",".join(ch_chunk))
                ch_response = ch_request.execute()
                for item in ch_response.get('items', []):
                    sub_data[item['id']] = int(item['statistics'].get('subscriberCount', 0))
            
            for video in video_metadata:
                video['Subscribers'] = sub_data.get(video['Channel ID'], 0) # 0 if hidden
                
        return pd.DataFrame(video_metadata)[["Channel Name", "Subscribers", "Video Title", "Video ID"]]
    except Exception as e:
        st.error(f"Metadata Fetch Error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False) 
def fetch_live_youtube_data(api_key, video_ids, max_comments_per_video=150):
    """Pulls live comments AND the commenter's username."""
    if not api_key or not video_ids: return pd.DataFrame()
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    comments_data = []
    
    for vid_id in video_ids:
        try:
            request = youtube.commentThreads().list(
                part="snippet", videoId=vid_id, maxResults=100, order="relevance", textFormat="plainText"
            )
            extracted = 0
            while request and extracted < max_comments_per_video:
                response = request.execute()
                for item in response.get('items', []):
                    snippet = item['snippet']['topLevelComment']['snippet']
                    comments_data.append({
                        "Date": snippet['publishedAt'],
                        "Platform": "YouTube",
                        "Author": snippet.get('authorDisplayName', 'Anonymous'),
                        "Content": snippet['textDisplay'],
                        "Engagement": int(snippet.get('likeCount', 0))
                    })
                    extracted += 1
                
                if 'nextPageToken' in response:
                    request = youtube.commentThreads().list(
                        part="snippet", videoId=vid_id, pageToken=response['nextPageToken'], 
                        maxResults=100, order="relevance", textFormat="plainText"
                    )
                else:
                    break
        except Exception:
            pass 

    return pd.DataFrame(comments_data)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_live_media_data(query):
    """Bypasses HTML blocks using Google News RSS feeds."""
    if not query: return pd.DataFrame()
    try:
        safe_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={safe_query}&hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(url)
        
        media_data = []
        for entry in feed.entries[:100]: 
            media_data.append({
                "Date": entry.published,
                "Platform": "Indian Media",
                "Author": entry.source.title if hasattr(entry, 'source') else "News Outlet",
                "Content": entry.title, 
                "Engagement": 500 
            })
        return pd.DataFrame(media_data)
    except Exception as e:
        st.error(f"Media Extraction Error: {e}")
        return pd.DataFrame()

# ==========================================
# 3. ADVANCED NLP PIPELINE 
# ==========================================
@st.cache_data
def process_nlp(df):
    if df.empty: return df
    
    tech_overrides = {
        "insane": 0.8, "base model": 0.0, "hard pass": -0.9, 
        "10/10": 0.9, "beast": 0.8, "trash": -0.9, "sick": 0.8
    }

    def get_feature(text):
        t = str(text).lower()
        if any(w in t for w in ['screen', 'display', 'pixel', 'black', 'oled']): return 'Display/Screen'
        elif any(w in t for w in ['battery', 'drain', 'mah', 'charge', 'heating']): return 'Battery/Power'
        elif any(w in t for w in ['price', 'overpriced', 'rs', 'cost', 'expensive']): return 'Price/Value'
        elif any(w in t for w in ['exynos', 'snapdragon', 'thermal', 'lag', 'chip']): return 'Performance/Chip'
        elif any(w in t for w in ['camera', 'zoom', 'lens', 'photo', 'video']): return 'Camera'
        return 'General/Other'

    def get_score(text):
        t = str(text).lower()
        for key, val in tech_overrides.items():
            if key in t: return val
        return TextBlob(str(text)).sentiment.polarity
        
    def get_category(score):
        if score > 0.05: return 'Positive'
        elif score < -0.05: return 'Negative'
        return 'Neutral'

    df['Feature'] = df['Content'].apply(get_feature)
    df['Sentiment_Score'] = df['Content'].apply(get_score)
    df['Sentiment_Category'] = df['Sentiment_Score'].apply(get_category)
    return df

# ==========================================
# 4. SIDEBAR & EXTRACTION TRIGGER
# ==========================================
st.sidebar.title("⚙️ Live Extraction Engine")
st.sidebar.markdown("Auto-hunt the top 10 videos, or manually inject specific URLs.")

try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
except KeyError:
    st.sidebar.error("⚠️ API Key missing from Streamlit Settings > Secrets!")
    api_key = None

master_query = st.sidebar.text_input("1. Target Product (Auto-Hunt)", value="Samsung S26 Ultra")
manual_urls = st.sidebar.text_area("2. Inject Manual YouTube Links (Optional)", placeholder="Paste full URLs or video IDs here...")

if st.sidebar.button("🚀 Run Live Extraction"):
    if not api_key:
        st.error("Cannot run extraction without YouTube API key in Secrets.")
    else:
        with st.spinner(f"Scraping omnichannel data for '{master_query}'..."):
            
            # 1. Combine Auto-IDs and Manual-IDs
            auto_video_ids = auto_discover_videos(api_key, master_query, max_videos=10)
            manual_video_ids = extract_video_ids_from_text(manual_urls)
            
            # Deduplicate the final list
            all_video_ids = list(set(auto_video_ids + manual_video_ids))
            
            if not all_video_ids and not master_query:
                st.warning("Please enter a query or provide video URLs.")
            else:
                # 2. Fetch Data
                sources_df = get_video_metadata(api_key, all_video_ids)
                yt_df = fetch_live_youtube_data(api_key, all_video_ids)
                media_df = fetch_live_media_data(master_query)
                
                # 3. Process Data
                combined_df = pd.concat([yt_df, media_df], ignore_index=True)
                
                if not combined_df.empty:
                    st.session_state['live_data'] = process_nlp(combined_df)
                    st.session_state['sources_data'] = sources_df
                    st.success(f"✅ Successfully extracted data from {len(all_video_ids)} videos and live news!")
                else:
                    st.warning("No data returned. Check your inputs.")

# ==========================================
# 5. DYNAMIC FILTERS 
# ==========================================
st.sidebar.markdown("---")
st.sidebar.title("🔍 Data Filters")

if 'live_data' in st.session_state and not st.session_state['live_data'].empty:
    df = st.session_state['live_data']
    
    selected_platform = st.sidebar.multiselect("📡 Platform", df['Platform'].unique(), default=df['Platform'].unique())
    selected_feature = st.sidebar.multiselect("📱 Topic/Feature", df['Feature'].unique(), default=df['Feature'].unique())
    selected_sentiment = st.sidebar.multiselect("🎭 Sentiment Type", ["Positive", "Neutral", "Negative"], default=["Positive", "Neutral", "Negative"])
    
    filtered_df = df[
        (df['Platform'].isin(selected_platform)) &
        (df['Feature'].isin(selected_feature)) &
        (df['Sentiment_Category'].isin(selected_sentiment))
    ]
else:
    filtered_df = pd.DataFrame()

# ==========================================
# 6. MAIN DASHBOARD UI
# ==========================================
st.title("📡 Live Omnichannel Intelligence")
st.markdown("Automated Category Leadership Dashboard tracking real-time market sentiment.")

if not filtered_df.empty:
    
    # KPI ROW
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Filtered Mentions", f"{len(filtered_df):,}")
    col2.metric("Filtered Engagement", f"{filtered_df['Engagement'].sum():,}")
    
    pct_negative = (len(filtered_df[filtered_df['Sentiment_Category'] == 'Negative']) / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
    pct_positive = (len(filtered_df[filtered_df['Sentiment_Category'] == 'Positive']) / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
    
    col3.metric("🔥 Negative Share", f"{pct_negative:.1f}%")
    col4.metric("⭐ Positive Share", f"{pct_positive:.1f}%")

    st.markdown("---")

    # DATA SOURCES SUMMARY
    if 'sources_data' in st.session_state and not st.session_state['sources_data'].empty:
        with st.expander(f"🎥 View Tracked YouTube Channels ({len(st.session_state['sources_data'])} Videos Found) - Click to Expand", expanded=False):
            st.markdown("The engine successfully targeted the following channels/videos:")
            st.dataframe(st.session_state['sources_data'], use_container_width=True)
            
    st.markdown("---")
    
    # VISUALIZATION ROW
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("1. Topic Polarization")
        topic_breakdown = filtered_df.groupby(['Feature', 'Sentiment_Category']).size().reset_index(name='Count')
        if not topic_breakdown.empty:
            fig_topic = px.bar(
                topic_breakdown, x='Count', y='Feature', color='Sentiment_Category', 
                orientation='h', barmode='stack', template="plotly_dark",
                color_discrete_map={'Positive': '#2ecc71', 'Neutral': '#95a5a6', 'Negative': '#e74c3c'}
            )
            fig_topic.update_layout(margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_topic, use_container_width=True)

    with col_chart2:
        st.subheader("2. Platform Health")
        platform_breakdown = filtered_df.groupby(['Platform', 'Sentiment_Category']).size().reset_index(name='Count')
        if not platform_breakdown.empty:
            fig_platform = px.bar(
                platform_breakdown, x='Count', y='Platform', color='Sentiment_Category', 
                orientation='h', barmode='stack', template="plotly_dark",
                color_discrete_map={'Positive': '#2ecc71', 'Neutral': '#95a5a6', 'Negative': '#e74c3c'}
            )
            fig_platform.update_layout(margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_platform, use_container_width=True)

    st.markdown("---")
    
    # RAW FILTERED VERBATIMS
    st.subheader("💬 Filtered Ground Truth (Raw Verbatims)")
    st.markdown("Read the exact user comments driving the charts above. Updates automatically based on your sidebar filters.")
    
    display_df = filtered_df[['Platform', 'Author', 'Feature', 'Sentiment_Category', 'Engagement', 'Content']].sort_values(by='Engagement', ascending=False)
    
    def color_sentiment(val):
        color = '#e74c3c' if val == 'Negative' else '#2ecc71' if val == 'Positive' else 'gray'
        return f'color: {color}'
        
    st.dataframe(
        display_df.style.map(color_sentiment, subset=['Sentiment_Category']), 
        use_container_width=True, 
        height=500
    )
    
    st.markdown(f"<div style='text-align: center; color: gray; font-size: 12px; margin-top: 40px;'>LIVE TARGET: {master_query.upper()} | CATEGORY LEADERSHIP DASHBOARD</div>", unsafe_allow_html=True)

else:
    st.info("👈 Enter your target product in the sidebar and click 'Run Live Extraction' to command the pipeline.")

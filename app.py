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
import requests
from bs4 import BeautifulSoup

# ==========================================
# 1. PAGE CONFIGURATION & UI INJECTION
# ==========================================
st.set_page_config(page_title="Omnichannel Intelligence", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #0B0F19; }
    h1, h2, h3 { color: #F3F4F6 !important; font-family: 'Inter', sans-serif; font-weight: 600; }
    p, span, div { color: #9CA3AF; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #1F2937; }
    div[data-testid="metric-container"] { background-color: #111827; border: 1px solid #1F2937; padding: 15px 20px; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: transform 0.2s; }
    div[data-testid="metric-container"]:hover { transform: translateY(-2px); border-color: #374151; }
    div[data-testid="metric-container"] label { color: #9CA3AF !important; }
    div[data-testid="metric-container"] div { color: #F3F4F6 !important; }
    .streamlit-expanderHeader { background-color: #111827 !important; border-radius: 8px !important; border: 1px solid #1F2937 !important; color: #F3F4F6 !important; }
    .stDataFrame { border-radius: 8px; overflow: hidden; border: 1px solid #1F2937; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {background-color: transparent !important;}
    hr { border-color: #1F2937 !important; }
</style>
""", unsafe_allow_html=True)

PREMIUM_COLORS = {'Positive': '#10B981', 'Neutral': '#6B7280', 'Negative': '#EF4444'}

if 'yt_db' not in st.session_state: st.session_state['yt_db'] = pd.DataFrame()
if 'sources_db' not in st.session_state: st.session_state['sources_db'] = pd.DataFrame()

# ==========================================
# 2. HYBRID EXTRACTION ENGINES
# ==========================================
def extract_video_ids_from_text(text):
    if not text: return []
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    matches = re.findall(regex, text)
    raw_ids = [word.strip() for word in text.replace(',', ' ').split() if len(word.strip()) == 11 and re.match(r'^[0-9A-Za-z_-]{11}$', word.strip())]
    return list(set(matches + raw_ids))

@st.cache_data(ttl=3600, show_spinner=False)
def auto_discover_videos(api_key, query, max_videos=10):
    if not api_key or not query: return []
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.search().list(part="id", q=query + " review", type="video", relevanceLanguage="en", maxResults=max_videos, order="relevance")
        response = request.execute()
        return [item['id']['videoId'] for item in response.get('items', [])]
    except: return []

def get_video_metadata(api_key, video_ids):
    if not api_key or not video_ids: return pd.DataFrame()
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        video_metadata = []
        channel_ids = []
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i:i+50]
            vid_request = youtube.videos().list(part="snippet", id=",".join(chunk))
            vid_response = vid_request.execute()
            for item in vid_response.get('items', []):
                ch_id = item['snippet']['channelId']
                video_metadata.append({
                    "Video ID": item['id'], "Video Title": item['snippet']['title'],
                    "Channel Name": item['snippet']['channelTitle'], "Channel ID": ch_id
                })
                channel_ids.append(ch_id)
        if channel_ids:
            sub_data = {}
            for i in range(0, len(list(set(channel_ids))), 50):
                ch_chunk = list(set(channel_ids))[i:i+50]
                ch_request = youtube.channels().list(part="statistics", id=",".join(ch_chunk))
                ch_response = ch_request.execute()
                for item in ch_response.get('items', []):
                    sub_data[item['id']] = int(item['statistics'].get('subscriberCount', 0))
            for video in video_metadata:
                video['Subscribers'] = sub_data.get(video['Channel ID'], 0)
        return pd.DataFrame(video_metadata)[["Channel Name", "Subscribers", "Video Title", "Video ID"]]
    except: return pd.DataFrame()

def fetch_live_youtube_data(api_key, video_ids, max_comments_per_video=150):
    if not api_key or not video_ids: return pd.DataFrame()
    youtube = build('youtube', 'v3', developerKey=api_key)
    comments_data = []
    for vid_id in video_ids:
        try:
            request = youtube.commentThreads().list(part="snippet", videoId=vid_id, maxResults=100, order="relevance", textFormat="plainText")
            extracted = 0
            while request and extracted < max_comments_per_video:
                response = request.execute()
                for item in response.get('items', []):
                    snippet = item['snippet']['topLevelComment']['snippet']
                    comments_data.append({
                        "Video ID": vid_id, "Date": snippet['publishedAt'], "Platform": "YouTube",
                        "Author": snippet.get('authorDisplayName', 'Anonymous'),
                        "Content": snippet['textDisplay'], "Engagement": int(snippet.get('likeCount', 0))
                    })
                    extracted += 1
                if 'nextPageToken' in response:
                    request = youtube.commentThreads().list(part="snippet", videoId=vid_id, pageToken=response['nextPageToken'], maxResults=100, order="relevance", textFormat="plainText")
                else: break
        except: pass 
    return pd.DataFrame(comments_data)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_live_media_data(query, time_filter, max_articles, manual_urls=""):
    media_data = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    if query:
        try:
            search_query = f"{query} when:{time_filter}" if time_filter else query
            safe_query = urllib.parse.quote(search_query)
            url = f"https://news.google.com/rss/search?q={safe_query}&hl=en-IN&gl=IN&ceid=IN:en"
            feed = feedparser.parse(url)
            
            # Scrape up to the requested max_articles (Note: Free RSS often caps at 100 per query)
            for entry in feed.entries[:max_articles]: 
                summary_text = BeautifulSoup(entry.summary, "html.parser").get_text(separator=" ") if hasattr(entry, 'summary') else ""
                full_content = f"{entry.title}. {summary_text}"
                media_data.append({
                    "Date": entry.published, "Platform": "Indian Media",
                    "Author": entry.source.title if hasattr(entry, 'source') else "News Outlet",
                    "Content": full_content[:1500], "Engagement": 500 
                })
        except: pass

    if manual_urls:
        urls = [u.strip() for u in manual_urls.split(',') if u.strip().startswith('http')]
        for url in urls:
            try:
                res = requests.get(url, headers=headers, timeout=5)
                soup = BeautifulSoup(res.text, 'html.parser')
                paragraphs = soup.find_all('p')
                article_text = ' '.join([p.get_text() for p in paragraphs])
                title = soup.title.string if soup.title else "Manual Article"
                if article_text:
                    media_data.append({
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Platform": "Direct Article", "Author": urllib.parse.urlparse(url).netloc,
                        "Content": f"{title}. {article_text[:2000]}", "Engagement": 1000 
                    })
            except: pass
    return pd.DataFrame(media_data)

# ==========================================
# 3. DYNAMIC NLP PIPELINE (Custom Features)
# ==========================================
@st.cache_data
def process_nlp(df, custom_topics_str):
    if df.empty: return df
    tech_overrides = {"insane": 0.8, "base model": 0.0, "hard pass": -0.9, "10/10": 0.9, "beast": 0.8, "trash": -0.9, "sick": 0.8}

    # Clean the user's custom features into a list
    custom_list = [x.strip() for x in custom_topics_str.split(',')] if custom_topics_str else []

    def get_feature(text):
        t = str(text).lower()
        
        # 1. Check custom features FIRST
        for custom_feat in custom_list:
            if custom_feat and custom_feat.lower() in t:
                return custom_feat.title() # Return the exact custom word capitalized
                
        # 2. Fallback to general tech features if no custom match
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
st.sidebar.markdown("<h2 style='color: white; margin-bottom: 0;'>⚙️ Extraction Engine</h2>", unsafe_allow_html=True)

try: api_key = st.secrets["YOUTUBE_API_KEY"]
except KeyError: api_key = None

# --- MEDIA SECTION (UNLIMITED) ---
st.sidebar.markdown("### 📰 Media Intelligence (Free/Unlimited)")
master_query = st.sidebar.text_input("🎯 Target Product", value="Samsung S26 Ultra")

# NEW: Custom Feature Input
custom_topics = st.sidebar.text_input("➕ Custom Feature Tracking", placeholder="e.g., App, Installation, Heating")

time_map = {"Past 24 Hours": "1d", "Past 7 Days": "7d", "Past 30 Days": "30d", "Past Year": "1y", "Any Time": ""}
selected_time = st.sidebar.selectbox("⏱️ Article Time Period", list(time_map.keys()), index=1)

# NEW: Unlocked Media Slider
max_articles = st.sidebar.slider("📄 Max Articles to Scrape (API Permitting)", min_value=10, max_value=1000, value=100, step=50)
manual_news_urls = st.sidebar.text_area("📰 Inject Specific Articles", placeholder="Paste URLs here, separated by commas...")

st.sidebar.markdown("---")

# --- YOUTUBE SECTION (QUOTA LIMITED) ---
st.sidebar.markdown("### 🎥 YouTube Intelligence (Quota Limited)")
enable_youtube = st.sidebar.checkbox("Enable YouTube Scraping", value=False)
manual_yt_urls = st.sidebar.text_area("🎥 Inject Specific Videos", placeholder="Paste URLs here...")

if st.sidebar.button("🚀 Run Enterprise Extraction", use_container_width=True):
    with st.spinner("Executing pipeline..."):
        
        st.toast("📰 Scraping media articles...")
        media_df = fetch_live_media_data(master_query, time_map[selected_time], max_articles, manual_news_urls)
        
        yt_df = pd.DataFrame()
        if enable_youtube:
            if not api_key: st.sidebar.error("⚠️ YouTube API Key missing. Skipping YouTube.")
            else:
                st.toast("🎥 Scraping YouTube data...")
                auto_video_ids = auto_discover_videos(api_key, master_query, max_videos=10)
                manual_video_ids = extract_video_ids_from_text(manual_yt_urls)
                all_requested_ids = list(set(auto_video_ids + manual_video_ids))
                
                existing_ids = st.session_state['yt_db']['Video ID'].unique().tolist() if not st.session_state['yt_db'].empty else []
                new_ids_to_fetch = [vid for vid in all_requested_ids if vid not in existing_ids]
                
                if new_ids_to_fetch:
                    new_sources_df = get_video_metadata(api_key, new_ids_to_fetch)
                    new_yt_df = fetch_live_youtube_data(api_key, new_ids_to_fetch)
                    st.session_state['sources_db'] = pd.concat([st.session_state['sources_db'], new_sources_df], ignore_index=True)
                    st.session_state['yt_db'] = pd.concat([st.session_state['yt_db'], new_yt_df], ignore_index=True)
                
                yt_df = st.session_state['yt_db']
        
        combined_df = pd.concat([yt_df, media_df], ignore_index=True)
        
        if not combined_df.empty:
            # Pass the custom topics into the NLP engine
            st.session_state['live_data'] = process_nlp(combined_df, custom_topics)
            st.success("Pipeline Execution Complete!")
        else: st.warning("No data returned.")

# ==========================================
# 5. DYNAMIC FILTERS 
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown("<h2 style='color: white; margin-bottom: 0;'>🔍 Data Filters</h2>", unsafe_allow_html=True)

if 'live_data' in st.session_state and not st.session_state['live_data'].empty:
    df = st.session_state['live_data']
    selected_platform = st.sidebar.multiselect("📡 Platform", df['Platform'].unique(), default=df['Platform'].unique())
    selected_feature = st.sidebar.multiselect("📱 Topic/Feature", df['Feature'].unique(), default=df['Feature'].unique())
    selected_sentiment = st.sidebar.multiselect("🎭 Sentiment", ["Positive", "Neutral", "Negative"], default=["Positive", "Neutral", "Negative"])
    
    filtered_df = df[
        (df['Platform'].isin(selected_platform)) &
        (df['Feature'].isin(selected_feature)) &
        (df['Sentiment_Category'].isin(selected_sentiment))
    ]
else: filtered_df = pd.DataFrame()

# ==========================================
# 6. MAIN DASHBOARD UI
# ==========================================
st.markdown("<h1 style='text-align: left; margin-bottom: 0;'>📡 Omnichannel Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 16px; margin-bottom: 30px;'>Real-time consumer sentiment & category tracking.</p>", unsafe_allow_html=True)

if not filtered_df.empty:
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Mentions", f"{len(filtered_df):,}")
    col2.metric("Total Engagement", f"{filtered_df['Engagement'].sum():,}")
    
    pct_negative = (len(filtered_df[filtered_df['Sentiment_Category'] == 'Negative']) / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
    pct_positive = (len(filtered_df[filtered_df['Sentiment_Category'] == 'Positive']) / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
    
    col3.metric("🔥 Negative Share", f"{pct_negative:.1f}%")
    col4.metric("⭐ Positive Share", f"{pct_positive:.1f}%")
    st.markdown("<br>", unsafe_allow_html=True)

    if 'sources_db' in st.session_state and not st.session_state['sources_db'].empty and 'YouTube' in filtered_df['Platform'].values:
        with st.expander(f"📂 View Active Data Vault ({len(st.session_state['sources_db'])} Videos Tracked)"):
            st.dataframe(st.session_state['sources_db'], use_container_width=True)
            
    st.markdown("---")
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("### Topic Polarization Matrix")
        topic_breakdown = filtered_df.groupby(['Feature', 'Sentiment_Category']).size().reset_index(name='Count')
        if not topic_breakdown.empty:
            fig_topic = px.bar(
                topic_breakdown, x='Count', y='Feature', color='Sentiment_Category', 
                orientation='h', barmode='stack', color_discrete_map=PREMIUM_COLORS
            )
            fig_topic.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="#9CA3AF", 
                margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=True, gridcolor='#1F2937'), yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_topic, use_container_width=True)

    with col_chart2:
        st.markdown("### Platform Health Distribution")
        platform_breakdown = filtered_df.groupby(['Platform', 'Sentiment_Category']).size().reset_index(name='Count')
        if not platform_breakdown.empty:
            fig_platform = px.bar(
                platform_breakdown, x='Count', y='Platform', color='Sentiment_Category', 
                orientation='h', barmode='stack', color_discrete_map=PREMIUM_COLORS
            )
            fig_platform.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="#9CA3AF", 
                margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=True, gridcolor='#1F2937'), yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_platform, use_container_width=True)

    st.markdown("---")
    st.markdown("### 💬 Filtered Ground Truth")
    display_df = filtered_df[['Date', 'Platform', 'Author', 'Feature', 'Sentiment_Category', 'Content', 'Engagement']].sort_values(by='Date', ascending=False)
    
    def color_sentiment(val):
        return f"color: {PREMIUM_COLORS.get(val, 'gray')}; font-weight: 500;"
        
    st.dataframe(display_df.style.map(color_sentiment, subset=['Sentiment_Category']), use_container_width=True, height=500)

else:
    st.info("👈 Configure your targets in the sidebar and execute the pipeline.")

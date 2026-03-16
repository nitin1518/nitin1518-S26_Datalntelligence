import urllib.parse
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from textblob import TextBlob
from googleapiclient.discovery import build
import feedparser
from datetime import datetime, timedelta

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
# 2. SMART SCRAPING ENGINES (Cached for 1 Hour)
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def get_top_youtube_videos(api_key, query, max_videos=3):
    """Silently searches YouTube for the top relevant review videos."""
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
def fetch_live_youtube_data(api_key, video_ids, max_comments_per_video=150):
    """Pulls live comments from the auto-discovered videos."""
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
                        "Content": snippet['textDisplay'],
                        "Engagement": int(snippet['likeCount'])
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
            pass # Silently skip videos if comments are disabled

    return pd.DataFrame(comments_data)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_live_media_data(query):
    """Bypasses HTML blocks using Google News RSS feeds."""
    if not query: return pd.DataFrame()
    try:
        # FIX: Safely encode the spaces in the query for the URL
        safe_query = urllib.parse.quote(query)
        
        # Formatted for the Indian Market (hl=en-IN, gl=IN)
        url = f"https://news.google.com/rss/search?q={safe_query}&hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(url)
        
        media_data = []
        for entry in feed.entries[:100]: 
            media_data.append({
                "Date": entry.published,
                "Platform": "Indian Media",
                "Content": entry.title, 
                "Engagement": 500 # Baseline media engagement weight
            })
        return pd.DataFrame(media_data)
    except Exception as e:
        st.error(f"Media Extraction Error: {e}")
        return pd.DataFrame()

# ==========================================
# 3. ADVANCED NLP PIPELINE (With Tech Context)
# ==========================================
@st.cache_data
def process_nlp(df):
    if df.empty: return df
    
    # Custom Dictionary to prevent false negatives
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
st.sidebar.markdown("Enter a product name. The engine will find the top media articles and YouTube reviews automatically.")

# Secure API Key Retrieval from Streamlit Vault
try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
except KeyError:
    st.sidebar.error("⚠️ API Key missing from Streamlit Settings > Secrets!")
    api_key = None

master_query = st.sidebar.text_input("Target Product", value="Samsung S26 Ultra")

if st.sidebar.button("🚀 Run Zero-Touch Extraction"):
    if not api_key:
        st.error("Cannot run extraction without YouTube API key in Secrets.")
    else:
        with st.spinner(f"Hunting top videos and live news for '{master_query}'..."):
            
            top_video_ids = get_top_youtube_videos(api_key, master_query)
            yt_df = fetch_live_youtube_data(api_key, top_video_ids)
            media_df = fetch_live_media_data(master_query)
            
            combined_df = pd.concat([yt_df, media_df], ignore_index=True)
            
            if not combined_df.empty:
                st.session_state['live_data'] = process_nlp(combined_df)
                st.success(f"✅ Successfully scraped {len(top_video_ids)} top videos and live news feeds!")
            else:
                st.warning("No data returned. Check your inputs.")

# ==========================================
# 5. MAIN DASHBOARD UI
# ==========================================
st.title("📡 Live Omnichannel Intelligence")
st.markdown("Automated Category Leadership Dashboard tracking real-time market sentiment.")

if 'live_data' in st.session_state and not st.session_state['live_data'].empty:
    df = st.session_state['live_data']
    
    # -----------------------------------
    # KPI ROW
    # -----------------------------------
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Data Points Scraped", f"{len(df):,}")
    col2.metric("Total Engagement", f"{df['Engagement'].sum():,}")
    
    pct_negative = (len(df[df['Sentiment_Category'] == 'Negative']) / len(df)) * 100
    pct_positive = (len(df[df['Sentiment_Category'] == 'Positive']) / len(df)) * 100
    
    col3.metric("🔥 Negative Share", f"{pct_negative:.1f}%")
    col4.metric("⭐ Positive Share", f"{pct_positive:.1f}%")

    st.markdown("---")
    
    # -----------------------------------
    # VISUALIZATION ROW
    # -----------------------------------
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("1. Topic Polarization")
        st.markdown("Positive vs Negative ratio inside each specific feature.")
        topic_breakdown = df.groupby(['Feature', 'Sentiment_Category']).size().reset_index(name='Count')
        fig_topic = px.bar(
            topic_breakdown, x='Count', y='Feature', color='Sentiment_Category', 
            orientation='h', barmode='stack', template="plotly_dark",
            color_discrete_map={'Positive': '#2ecc71', 'Neutral': '#95a5a6', 'Negative': '#e74c3c'}
        )
        fig_topic.update_layout(margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_topic, use_container_width=True)

    with col_chart2:
        st.subheader("2. Platform Health")
        st.markdown("Media PR narrative vs. YouTube Consumer reality.")
        platform_breakdown = df.groupby(['Platform', 'Sentiment_Category']).size().reset_index(name='Count')
        fig_platform = px.bar(
            platform_breakdown, x='Count', y='Platform', color='Sentiment_Category', 
            orientation='h', barmode='stack', template="plotly_dark",
            color_discrete_map={'Positive': '#2ecc71', 'Neutral': '#95a5a6', 'Negative': '#e74c3c'}
        )
        fig_platform.update_layout(margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_platform, use_container_width=True)

    st.markdown("---")
    
    # -----------------------------------
    # DEEP DIVE AGGREGATED TABLE
    # -----------------------------------
    st.subheader("📑 Live Narrative Deep-Dive")
    st.markdown("Groups identical narratives and sums their total viral reach across the internet.")
    
    # Group by Content to remove exact duplicates and sum engagement
    agg_df = df.groupby(['Content', 'Platform', 'Feature', 'Sentiment_Category']).agg(
        Total_Mentions=('Content', 'count'),
        Total_Engagement=('Engagement', 'sum')
    ).reset_index().sort_values(by='Total_Engagement', ascending=False)
    
    def color_sentiment(val):
        color = '#e74c3c' if val == 'Negative' else '#2ecc71' if val == 'Positive' else 'gray'
        return f'color: {color}'
        
    st.dataframe(agg_df.style.map(color_sentiment, subset=['Sentiment_Category']), use_container_width=True, height=400)
    
    st.markdown(f"<div style='text-align: center; color: gray; font-size: 12px; margin-top: 40px;'>LIVE TARGET: {master_query.upper()} | CATEGORY LEADERSHIP DASHBOARD</div>", unsafe_allow_html=True)

else:
    st.info("👈 Enter your target product in the sidebar and click 'Run Zero-Touch Extraction' to command the pipeline.")

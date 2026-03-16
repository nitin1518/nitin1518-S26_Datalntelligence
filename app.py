import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from textblob import TextBlob
from googleapiclient.discovery import build
import feedparser
from datetime import datetime
import re

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Live Market Intelligence", page_icon="📡", layout="wide")

# ==========================================
# 2. SMART SCRAPING ENGINES (Cached to prevent blocking)
# ==========================================
# TTL = 3600 seconds (1 hour). The app will auto-scrape new data every hour, preventing API bans.
@st.cache_data(ttl=3600, show_spinner=False) 
def fetch_live_youtube_data(api_key, video_id, max_comments=200):
    if not api_key or not video_id:
        return pd.DataFrame()
        
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.commentThreads().list(
            part="snippet", videoId=video_id, maxResults=100, order="relevance", textFormat="plainText"
        )
        
        comments_data = []
        extracted = 0
        
        while request and extracted < max_comments:
            response = request.execute()
            for item in response['items']:
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
                    part="snippet", videoId=video_id, pageToken=response['nextPageToken'], 
                    maxResults=100, order="relevance", textFormat="plainText"
                )
            else:
                break
                
        return pd.DataFrame(comments_data)
    except Exception as e:
        st.error(f"YouTube API Error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_live_media_data(query):
    if not query:
        return pd.DataFrame()
        
    try:
        # Smart Scraping: Bypassing HTML blocks by using Google News RSS feeds
        # Formatted for the Indian Market (hl=en-IN, gl=IN)
        url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(url)
        
        media_data = []
        for entry in feed.entries[:100]: # Grab top 100 recent articles
            media_data.append({
                "Date": entry.published,
                "Platform": "Indian Media",
                "Content": entry.title, # Article headline
                "Engagement": 500 # Baseline media weight
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
    
    # Tech Context Override
    tech_overrides = {"insane": 0.8, "base model": 0.0, "hard pass": -0.9, "10/10": 0.9, "beast": 0.8}

    def get_feature(text):
        t = text.lower()
        if any(w in t for w in ['screen', 'display', 'pixel', 'black']): return 'Display/Screen'
        elif any(w in t for w in ['battery', 'drain', 'mah', 'charge']): return 'Battery/Power'
        elif any(w in t for w in ['price', 'overpriced', 'rs', 'cost']): return 'Price/Value'
        elif any(w in t for w in ['exynos', 'snapdragon', 'thermal', 'heat']): return 'Performance/Chip'
        elif any(w in t for w in ['camera', 'zoom', 'lens']): return 'Camera'
        return 'General/Other'

    def get_score(text):
        t = text.lower()
        for key, val in tech_overrides.items():
            if key in t: return val
        return TextBlob(text).sentiment.polarity
        
    def get_category(score):
        if score > 0.1: return 'Positive'
        elif score < -0.1: return 'Negative'
        return 'Neutral'

    df['Feature'] = df['Content'].apply(get_feature)
    df['Sentiment_Score'] = df['Content'].apply(get_score)
    df['Sentiment_Category'] = df['Sentiment_Score'].apply(get_category)
    return df

# ==========================================
# 4. SIDEBAR & APP STATE
# ==========================================
st.sidebar.title("⚙️ Live Extraction Engine")
st.sidebar.markdown("Configure the auto-scraper targets.")

# SECURE: Pulls the API key silently from the Streamlit Vault
try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
except KeyError:
    st.sidebar.error("⚠️ API Key missing from Streamlit Secrets!")
    api_key = None

# Set a default tech review video so it runs automatically, but allow them to change it!
video_id = st.sidebar.text_input("YouTube Video ID", value="ENTER_A_DEFAULT_VIDEO_ID_HERE")
media_query = st.sidebar.text_input("Media Search Query", value="Samsung S26 Ultra")

if st.sidebar.button("🚀 Run Live Extraction"):
    if not api_key:
        st.error("Cannot run extraction without API key.")
    else:
        with st.spinner("Scraping Web and Processing NLP..."):
            # 1. Fetch
            yt_df = fetch_live_youtube_data(api_key, video_id)
            media_df = fetch_live_media_data(media_query)
            
            # 2. Combine
            combined_df = pd.concat([yt_df, media_df], ignore_index=True)
            
            # 3. Process
            if not combined_df.empty:
                st.session_state['live_data'] = process_nlp(combined_df)
                st.success("Data Pipeline Executed Successfully!")
            else:
                st.warning("No data returned. Check your inputs.")

# ==========================================
# 5. MAIN DASHBOARD UI
# ==========================================
st.title("📡 Live Omnichannel Intelligence")

if 'live_data' in st.session_state and not st.session_state['live_data'].empty:
    df = st.session_state['live_data']
    
    # Executive KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Live Data Points Scraped", f"{len(df):,}")
    
    pct_negative = (len(df[df['Sentiment_Category'] == 'Negative']) / len(df)) * 100
    pct_positive = (len(df[df['Sentiment_Category'] == 'Positive']) / len(df)) * 100
    
    col2.metric("🔥 Negative Share", f"{pct_negative:.1f}%")
    col3.metric("⭐ Positive Share", f"{pct_positive:.1f}%")

    st.markdown("---")
    
    # The Media vs Consumer Reality Gap
    st.subheader("Platform Health: Media PR vs. Consumer Reality")
    platform_breakdown = df.groupby(['Platform', 'Sentiment_Category']).size().reset_index(name='Count')
    fig_platform = px.bar(
        platform_breakdown, x='Count', y='Platform', color='Sentiment_Category', 
        orientation='h', barmode='stack', template="plotly_dark",
        color_discrete_map={'Positive': '#2ecc71', 'Neutral': '#95a5a6', 'Negative': '#e74c3c'}
    )
    st.plotly_chart(fig_platform, use_container_width=True)
    
    st.markdown("---")
    
    # Live Aggregated Verbatims
    st.subheader("Live Narrative Deep-Dive")
    agg_df = df.groupby(['Content', 'Platform', 'Feature', 'Sentiment_Category']).agg(
        Total_Engagement=('Engagement', 'sum')
    ).reset_index().sort_values(by='Total_Engagement', ascending=False)
    
    def color_sentiment(val):
        color = '#e74c3c' if val == 'Negative' else '#2ecc71' if val == 'Positive' else 'gray'
        return f'color: {color}'
        
    st.dataframe(agg_df.style.map(color_sentiment, subset=['Sentiment_Category']), use_container_width=True, height=400)

else:
    st.info("👈 Enter your targets in the sidebar and click 'Run Live Extraction' to start the pipeline.")

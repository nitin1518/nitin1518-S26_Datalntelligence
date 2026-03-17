import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from textblob import TextBlob
from googleapiclient.discovery import build
import feedparser
from datetime import datetime, timezone
import urllib.parse
import re
import requests
from bs4 import BeautifulSoup
import math

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Omnichannel Product Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# PREMIUM UI
# =========================================================
st.markdown("""
<style>
    :root {
        --bg: #0B0F19;
        --panel: #111827;
        --panel-2: #0F172A;
        --border: #1F2937;
        --border-2: #273449;
        --text: #F3F4F6;
        --muted: #9CA3AF;
        --muted-2: #94A3B8;
        --accent: #38BDF8;
        --green: #10B981;
        --red: #EF4444;
        --amber: #F59E0B;
        --gray: #6B7280;
        --purple: #8B5CF6;
    }

    .stApp {
        background:
            radial-gradient(circle at top right, rgba(56,189,248,0.10), transparent 22%),
            radial-gradient(circle at top left, rgba(139,92,246,0.08), transparent 18%),
            var(--bg);
    }

    html, body, [class*="css"] {
        font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--text) !important;
        letter-spacing: -0.02em;
    }

    p, span, div, label {
        color: var(--muted);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0E1421 0%, #111827 100%);
        border-right: 1px solid var(--border);
    }

    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: var(--text);
        margin-bottom: 0.15rem;
        letter-spacing: -0.03em;
    }

    .sub-title {
        color: var(--muted-2);
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .hero-card {
        background: linear-gradient(135deg, rgba(17,24,39,0.95), rgba(15,23,42,0.95));
        border: 1px solid rgba(56,189,248,0.18);
        border-radius: 18px;
        padding: 18px 20px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    }

    .section-card {
        background: linear-gradient(180deg, rgba(17,24,39,0.90), rgba(15,23,42,0.88));
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 16px 16px 10px 16px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.18);
        margin-bottom: 14px;
    }

    div[data-testid="metric-container"] {
        background: linear-gradient(180deg, rgba(17,24,39,0.98), rgba(15,23,42,0.94));
        border: 1px solid var(--border);
        padding: 14px 18px;
        border-radius: 16px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.14);
    }

    div[data-testid="metric-container"] label {
        color: var(--muted) !important;
        font-weight: 500;
    }

    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: var(--text) !important;
        font-weight: 700;
    }

    div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
        color: var(--accent) !important;
    }

    .insight-chip {
        display: inline-block;
        background: rgba(56,189,248,0.12);
        color: #BAE6FD;
        border: 1px solid rgba(56,189,248,0.22);
        padding: 7px 11px;
        margin: 4px 6px 0 0;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 500;
    }

    .summary-box {
        background: rgba(17,24,39,0.78);
        border: 1px solid var(--border);
        border-left: 4px solid var(--accent);
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }

    .summary-title {
        color: var(--text);
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 4px;
    }

    .summary-body {
        color: var(--muted-2);
        font-size: 0.93rem;
        line-height: 1.45;
    }

    .small-note {
        color: #7C8AA5;
        font-size: 0.84rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        padding-bottom: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(17,24,39,0.9);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 10px 16px;
        color: var(--muted) !important;
    }

    .stTabs [aria-selected="true"] {
        border-color: rgba(56,189,248,0.35) !important;
        color: var(--text) !important;
        box-shadow: inset 0 0 0 1px rgba(56,189,248,0.15);
    }

    .streamlit-expanderHeader {
        background: rgba(17,24,39,0.92) !important;
        border-radius: 12px !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
    }

    .stDataFrame, .stTable {
        border: 1px solid var(--border);
        border-radius: 14px;
        overflow: hidden;
    }

    hr {
        border-color: var(--border) !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background-color: transparent !important;}

    .sidebar-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--text);
        margin: 0.3rem 0 0.6rem 0;
    }

    .sidebar-caption {
        color: var(--muted-2);
        font-size: 0.88rem;
        margin-bottom: 1rem;
    }

    .tag-chip {
        display: inline-block;
        background: rgba(56,189,248,0.14);
        color: #E0F2FE;
        border: 1px solid rgba(56,189,248,0.28);
        padding: 6px 10px;
        margin: 4px 6px 0 0;
        border-radius: 999px;
        font-size: 0.80rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# CONSTANTS
# =========================================================
PREMIUM_COLORS = {
    "Positive": "#10B981",
    "Neutral": "#6B7280",
    "Negative": "#EF4444"
}

PLATFORM_COLORS = {
    "YouTube": "#8B5CF6",
    "Indian Media": "#38BDF8",
    "Direct Article": "#F59E0B"
}

FEATURE_MAP = {
    "Display/Screen": ["screen", "display", "pixel", "oled", "amoled", "brightness", "refresh rate", "bezel"],
    "Battery/Power": ["battery", "drain", "mah", "charge", "charging", "backup", "power", "heating", "warm"],
    "Price/Value": ["price", "overpriced", "cost", "expensive", "cheap", "value for money", "worth", "pricing"],
    "Performance/Chip": ["exynos", "snapdragon", "thermal", "lag", "chip", "processor", "speed", "stutter", "smooth"],
    "Camera": ["camera", "zoom", "lens", "photo", "video", "portrait", "night mode", "shot", "selfie"],
    "Software/App": ["app", "software", "ui", "one ui", "update", "bug", "crash", "glitch", "interface"],
    "Connectivity": ["network", "wifi", "wi-fi", "bluetooth", "signal", "5g", "connection", "connected"],
    "Build/Design": ["design", "build", "premium", "weight", "feel", "body", "look", "finish"],
    "Audio/Speakers": ["speaker", "audio", "sound", "mic", "microphone", "volume"],
    "Service/Installation": ["installation", "install", "service", "technician", "support", "customer care", "engineer"]
}

PAIN_POINT_MAP = {
    "Heating": ["heating", "overheat", "hot", "thermal issue", "gets warm"],
    "Battery Drain": ["battery drain", "drain fast", "poor battery", "bad battery", "battery backup"],
    "Lag / Slow Performance": ["lag", "stutter", "slow", "freeze", "hang"],
    "Overpriced": ["overpriced", "expensive", "too costly", "not worth the price"],
    "Camera Weakness": ["poor camera", "bad camera", "low light", "blurry", "oversharpened"],
    "Software Bug": ["bug", "crash", "glitch", "software issue", "app issue"],
    "Connectivity Issue": ["not connecting", "wifi issue", "bluetooth issue", "network issue", "signal issue"],
    "Service Issue": ["bad service", "support issue", "customer care", "service center", "technician issue"],
    "Installation Issue": ["installation issue", "install issue", "setup issue", "difficult to install"]
}

INTENT_MAP = {
    "Purchase Intent": ["buy", "purchase", "worth buying", "should i buy", "planning to buy", "thinking of buying"],
    "Comparison": ["vs", "versus", "compare", "better than", "or iphone", "or samsung", "or oneplus"],
    "Complaint": ["issue", "problem", "bad", "worst", "hate", "disappointed", "return", "refund"],
    "Praise": ["love", "great", "amazing", "excellent", "best", "fantastic", "awesome"],
    "Recommendation": ["recommend", "suggest", "go for", "worth it", "must buy"],
    "Question / Confusion": ["why", "how", "what", "is it", "does it", "can it", "anyone know"]
}

TECH_OVERRIDES = {
    "insane": 0.8,
    "base model": 0.0,
    "hard pass": -0.9,
    "10/10": 0.9,
    "beast": 0.8,
    "trash": -0.9,
    "sick": 0.8,
    "overpriced": -0.65,
    "heating issue": -0.8,
    "battery drain": -0.8,
    "value for money": 0.65,
    "not worth": -0.75,
    "must buy": 0.8
}

# =========================================================
# SESSION STATE
# =========================================================
if "yt_db" not in st.session_state:
    st.session_state["yt_db"] = pd.DataFrame()

if "sources_db" not in st.session_state:
    st.session_state["sources_db"] = pd.DataFrame()

if "live_data" not in st.session_state:
    st.session_state["live_data"] = pd.DataFrame()

if "custom_feature_tags" not in st.session_state:
    st.session_state["custom_feature_tags"] = []

if "custom_feature_input" not in st.session_state:
    st.session_state["custom_feature_input"] = ""

# =========================================================
# UTILITY FUNCTIONS
# =========================================================
def normalize_text(text):
    return re.sub(r"\s+", " ", str(text)).strip()

def safe_log1p(x):
    try:
        return math.log1p(max(float(x), 0))
    except Exception:
        return 0.0

def dedupe_dataframe(df):
    if df.empty:
        return df
    temp = df.copy()
    temp["Content_Clean"] = (
        temp["Content"]
        .astype(str)
        .str.lower()
        .str.replace(r"http\S+", "", regex=True)
        .str.replace(r"[^a-z0-9\s]", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    temp["Dedupe_Key"] = temp["Content_Clean"].str[:300]
    temp = temp.drop_duplicates(subset=["Platform", "Dedupe_Key"])
    return temp.drop(columns=["Content_Clean", "Dedupe_Key"], errors="ignore")

def parse_dates(df):
    if df.empty:
        return df
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce", utc=True)
    out["Date_Local"] = out["Date"].dt.tz_convert("Asia/Kolkata")
    out["Day"] = out["Date_Local"].dt.date.astype(str)
    out["Week"] = out["Date_Local"].dt.strftime("%Y-W%U")
    out["Month"] = out["Date_Local"].dt.strftime("%Y-%m")
    return out

def get_score(text):
    t = str(text).lower()
    for key, val in TECH_OVERRIDES.items():
        if key in t:
            return val
    return TextBlob(str(text)).sentiment.polarity

def get_category(score):
    if score > 0.05:
        return "Positive"
    elif score < -0.05:
        return "Negative"
    return "Neutral"

def get_features(text, custom_list):
    t = str(text).lower()
    matched = []

    for custom_feat in custom_list:
        feat = custom_feat.strip()
        if not feat:
            continue

        feat_words = [w.strip() for w in feat.lower().split() if w.strip()]
        if feat_words and all(word in t for word in feat_words):
            matched.append(feat)

    for feature, keywords in FEATURE_MAP.items():
        if any(k in t for k in keywords):
            matched.append(feature)

    return list(dict.fromkeys(matched)) if matched else ["General/Other"]

def detect_pain_points(text):
    t = str(text).lower()
    found = [k for k, vals in PAIN_POINT_MAP.items() if any(v in t for v in vals)]
    return found if found else ["None"]

def classify_intent(text):
    t = str(text).lower()
    found = [k for k, vals in INTENT_MAP.items() if any(v in t for v in vals)]
    return found if found else ["General Discussion"]

def source_tier(platform, author, subs=0):
    author_l = str(author).lower()
    if platform == "YouTube":
        if subs >= 1000000:
            return "Top Creator"
        elif subs >= 100000:
            return "Mid Creator"
        return "Emerging Creator"

    tier1_terms = ["times", "mint", "ndtv", "hindustan", "indianexpress", "moneycontrol", "business", "news18"]
    if any(x in author_l for x in tier1_terms):
        return "Tier-1 Media"
    return "Other Media"

def compute_influence(row):
    platform = row.get("Platform", "")
    engagement = row.get("Engagement", 0) if pd.notnull(row.get("Engagement", None)) else 0
    subscribers = row.get("Subscribers", 0) if pd.notnull(row.get("Subscribers", None)) else 0

    base = safe_log1p(engagement)
    if platform == "YouTube":
        return round((base * 1.5) + (safe_log1p(subscribers) * 2.0), 3)
    elif platform == "Indian Media":
        return round(base + 4.0, 3)
    elif platform == "Direct Article":
        return round(base + 2.5, 3)
    return round(base, 3)

def generate_summary_insights(base_df, feature_df=None, pain_df=None):
    insights = []
    if base_df.empty:
        return insights

    total = len(base_df)
    neg_share = round((len(base_df[base_df["Sentiment_Category"] == "Negative"]) / total) * 100, 1) if total else 0
    pos_share = round((len(base_df[base_df["Sentiment_Category"] == "Positive"]) / total) * 100, 1) if total else 0

    top_feature = "N/A"
    if feature_df is not None and not feature_df.empty and "Feature" in feature_df.columns:
        valid_features = feature_df["Feature"].dropna()
        if not valid_features.empty:
            top_feature = valid_features.value_counts().idxmax()

    top_pain = "No major pain point surfaced"
    if pain_df is not None and not pain_df.empty and "Pain_Point" in pain_df.columns:
        neg_pain_df = pain_df[
            (pain_df["Sentiment_Category"] == "Negative") &
            (pain_df["Pain_Point"] != "None")
        ]
        if not neg_pain_df.empty:
            top_pain = neg_pain_df["Pain_Point"].value_counts().idxmax()

    neg_df = base_df[base_df["Sentiment_Category"] == "Negative"]
    top_platform_neg = neg_df["Platform"].value_counts().idxmax() if not neg_df.empty else "N/A"

    top_source = "N/A"
    if "Author" in base_df.columns and "Influence_Score" in base_df.columns and not base_df.empty:
        src = base_df.groupby("Author")["Influence_Score"].sum().sort_values(ascending=False)
        if not src.empty:
            top_source = src.index[0]

    insights.append(f"Positive share is {pos_share}% while negative share is {neg_share}%.")
    insights.append(f"Most discussed feature is {top_feature}.")
    insights.append(f"Top pain point emerging from negative commentary is {top_pain}.")
    insights.append(f"Highest negative buzz concentration is on {top_platform_neg}.")
    insights.append(f"Most influential source in the current dataset is {top_source}.")
    return insights

def compare_recent_vs_previous(df, dimension_col, recent_days=7):
    if df.empty or "Date_Local" not in df.columns or dimension_col not in df.columns:
        return pd.DataFrame()

    max_date = df["Date_Local"].max()
    if pd.isna(max_date):
        return pd.DataFrame()

    recent_start = max_date - pd.Timedelta(days=recent_days)
    prev_start = recent_start - pd.Timedelta(days=recent_days)

    recent = df[(df["Date_Local"] >= recent_start) & (df["Date_Local"] <= max_date)]
    previous = df[(df["Date_Local"] >= prev_start) & (df["Date_Local"] < recent_start)]

    if recent.empty and previous.empty:
        return pd.DataFrame()

    recent_counts = recent[dimension_col].value_counts().rename("Recent_Count")
    prev_counts = previous[dimension_col].value_counts().rename("Previous_Count")

    out = pd.concat([recent_counts, prev_counts], axis=1).fillna(0).reset_index()
    out.columns = [dimension_col, "Recent_Count", "Previous_Count"]
    out["Growth_%"] = np.where(
        out["Previous_Count"] > 0,
        ((out["Recent_Count"] - out["Previous_Count"]) / out["Previous_Count"]) * 100,
        np.where(out["Recent_Count"] > 0, 100.0, 0.0)
    )
    return out.sort_values("Growth_%", ascending=False)

def add_custom_feature():
    feat = st.session_state.get("custom_feature_input", "").strip()
    if feat:
        existing_lower = [x.lower() for x in st.session_state["custom_feature_tags"]]
        if feat.lower() not in existing_lower:
            st.session_state["custom_feature_tags"].append(feat)
        st.session_state["custom_feature_input"] = ""

def remove_custom_feature(idx):
    if 0 <= idx < len(st.session_state["custom_feature_tags"]):
        st.session_state["custom_feature_tags"].pop(idx)

# =========================================================
# EXTRACTION HELPERS
# =========================================================
def extract_video_ids_from_text(text):
    if not text:
        return []
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    matches = re.findall(regex, text)
    raw_ids = [
        word.strip() for word in text.replace(",", " ").split()
        if len(word.strip()) == 11 and re.match(r'^[0-9A-Za-z_-]{11}$', word.strip())
    ]
    return list(set(matches + raw_ids))

@st.cache_data(ttl=3600, show_spinner=False)
def auto_discover_videos(api_key, query, max_videos=10):
    if not api_key or not query:
        return []
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        request = youtube.search().list(
            part="id",
            q=query + " review",
            type="video",
            relevanceLanguage="en",
            maxResults=max_videos,
            order="relevance"
        )
        response = request.execute()
        return [item["id"]["videoId"] for item in response.get("items", [])]
    except Exception:
        return []

def get_video_metadata(api_key, video_ids):
    if not api_key or not video_ids:
        return pd.DataFrame()

    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        video_metadata = []
        channel_ids = []

        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i:i+50]
            vid_request = youtube.videos().list(part="snippet,statistics", id=",".join(chunk))
            vid_response = vid_request.execute()

            for item in vid_response.get("items", []):
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                ch_id = snippet.get("channelId", "")

                video_metadata.append({
                    "Video ID": item.get("id", ""),
                    "Video Title": snippet.get("title", ""),
                    "Channel Name": snippet.get("channelTitle", ""),
                    "Channel ID": ch_id,
                    "Video Published At": snippet.get("publishedAt", None),
                    "Video Views": int(stats.get("viewCount", 0)) if stats.get("viewCount") else 0,
                    "Video Likes": int(stats.get("likeCount", 0)) if stats.get("likeCount") else 0
                })
                if ch_id:
                    channel_ids.append(ch_id)

        sub_data = {}
        if channel_ids:
            uniq_channel_ids = list(set(channel_ids))
            for i in range(0, len(uniq_channel_ids), 50):
                ch_chunk = uniq_channel_ids[i:i+50]
                ch_request = youtube.channels().list(part="statistics", id=",".join(ch_chunk))
                ch_response = ch_request.execute()
                for item in ch_response.get("items", []):
                    sub_data[item["id"]] = int(item["statistics"].get("subscriberCount", 0))

        for video in video_metadata:
            video["Subscribers"] = sub_data.get(video["Channel ID"], 0)

        df = pd.DataFrame(video_metadata)
        if df.empty:
            return df

        return df[[
            "Channel Name", "Subscribers", "Video Title", "Video ID",
            "Video Published At", "Video Views", "Video Likes"
        ]]

    except Exception:
        return pd.DataFrame()

def fetch_live_youtube_data(api_key, video_ids, max_comments_per_video=150):
    if not api_key or not video_ids:
        return pd.DataFrame()

    try:
        youtube = build("youtube", "v3", developerKey=api_key)
    except Exception:
        return pd.DataFrame()

    comments_data = []

    for vid_id in video_ids:
        try:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=vid_id,
                maxResults=100,
                order="relevance",
                textFormat="plainText"
            )
            extracted = 0

            while request and extracted < max_comments_per_video:
                response = request.execute()
                for item in response.get("items", []):
                    snippet = item["snippet"]["topLevelComment"]["snippet"]
                    comments_data.append({
                        "Video ID": vid_id,
                        "Date": snippet.get("publishedAt"),
                        "Platform": "YouTube",
                        "Author": snippet.get("authorDisplayName", "Anonymous"),
                        "Content": snippet.get("textDisplay", ""),
                        "Engagement": int(snippet.get("likeCount", 0))
                    })
                    extracted += 1

                    if extracted >= max_comments_per_video:
                        break

                if "nextPageToken" in response and extracted < max_comments_per_video:
                    request = youtube.commentThreads().list(
                        part="snippet",
                        videoId=vid_id,
                        pageToken=response["nextPageToken"],
                        maxResults=100,
                        order="relevance",
                        textFormat="plainText"
                    )
                else:
                    break
        except Exception:
            pass

    return pd.DataFrame(comments_data)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_live_media_data(query, time_filter, max_articles, manual_urls=""):
    media_data = []
    headers = {"User-Agent": "Mozilla/5.0"}

    if query:
        try:
            search_query = f"{query} when:{time_filter}" if time_filter else query
            safe_query = urllib.parse.quote(search_query)
            url = f"https://news.google.com/rss/search?q={safe_query}&hl=en-IN&gl=IN&ceid=IN:en"
            feed = feedparser.parse(url)

            for entry in feed.entries[:max_articles]:
                summary_text = BeautifulSoup(entry.summary, "html.parser").get_text(separator=" ") if hasattr(entry, "summary") else ""
                full_content = f"{entry.title}. {summary_text}"
                media_data.append({
                    "Date": getattr(entry, "published", None),
                    "Platform": "Indian Media",
                    "Author": entry.source.title if hasattr(entry, "source") else "News Outlet",
                    "Content": full_content[:2000],
                    "Engagement": np.nan
                })
        except Exception:
            pass

    if manual_urls:
        urls = [u.strip() for u in manual_urls.split(",") if u.strip().startswith("http")]
        for url in urls:
            try:
                res = requests.get(url, headers=headers, timeout=7)
                soup = BeautifulSoup(res.text, "html.parser")
                paragraphs = soup.find_all("p")
                article_text = " ".join([p.get_text(" ", strip=True) for p in paragraphs])
                title = soup.title.string if soup.title else "Manual Article"
                if article_text:
                    media_data.append({
                        "Date": datetime.now(timezone.utc).isoformat(),
                        "Platform": "Direct Article",
                        "Author": urllib.parse.urlparse(url).netloc,
                        "Content": f"{title}. {article_text[:2500]}",
                        "Engagement": np.nan
                    })
            except Exception:
                pass

    return pd.DataFrame(media_data)

# =========================================================
# NLP PIPELINE
# =========================================================
@st.cache_data(show_spinner=False)
def process_nlp(df, custom_topics_tuple):
    if df.empty:
        return df

    custom_list = list(custom_topics_tuple) if custom_topics_tuple else []

    df = dedupe_dataframe(df)
    df = parse_dates(df)

    df["Content"] = df["Content"].astype(str).apply(normalize_text)
    df["Sentiment_Score"] = df["Content"].apply(get_score)
    df["Sentiment_Category"] = df["Sentiment_Score"].apply(get_category)
    df["Feature_List"] = df["Content"].apply(lambda x: get_features(x, custom_list))
    df["Pain_Point_List"] = df["Content"].apply(detect_pain_points)
    df["Intent_List"] = df["Content"].apply(classify_intent)

    if "Subscribers" not in df.columns:
        df["Subscribers"] = 0

    df["Source_Tier"] = df.apply(
        lambda r: source_tier(r.get("Platform", ""), r.get("Author", ""), r.get("Subscribers", 0)),
        axis=1
    )

    df["Influence_Score"] = df.apply(compute_influence, axis=1)
    df["Weighted_Sentiment"] = df["Sentiment_Score"] * (df["Influence_Score"] + 1)

    return df

def explode_for_analysis(df):
    if df.empty:
        return df, df, df

    feature_df = df.explode("Feature_List").rename(columns={"Feature_List": "Feature"})
    pain_df = df.explode("Pain_Point_List").rename(columns={"Pain_Point_List": "Pain_Point"})
    intent_df = df.explode("Intent_List").rename(columns={"Intent_List": "Intent"})

    feature_df["Feature"] = feature_df["Feature"].astype(str).str.strip()
    pain_df["Pain_Point"] = pain_df["Pain_Point"].astype(str).str.strip()
    intent_df["Intent"] = intent_df["Intent"].astype(str).str.strip()

    return feature_df, pain_df, intent_df

# =========================================================
# SIDEBAR
# =========================================================
try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
except Exception:
    api_key = None

with st.sidebar:
    st.markdown('<div class="sidebar-title">⚙️ Extraction Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-caption">Configure product targets, sources, and feature tracking.</div>', unsafe_allow_html=True)

    master_query = st.text_input("🎯 Target Product / Query", value="Samsung S26 Ultra")

    st.markdown("#### ➕ Custom Feature Tracking")
    st.caption("Add one keyword or phrase at a time. Added items appear below as visible tags.")

    cf1, cf2 = st.columns([3, 1])
    with cf1:
        st.text_input(
            "Custom feature input",
            key="custom_feature_input",
            placeholder="e.g., Installation, Battery Drain, App Crash",
            label_visibility="collapsed",
            on_change=add_custom_feature
        )
    with cf2:
        st.button("Add", use_container_width=True, on_click=add_custom_feature)

    if st.session_state["custom_feature_tags"]:
        st.markdown("**Tracked custom features**")
        for idx, feat in enumerate(st.session_state["custom_feature_tags"]):
            rc1, rc2 = st.columns([4, 1])
            with rc1:
                st.markdown(f'<span class="tag-chip">{feat}</span>', unsafe_allow_html=True)
            with rc2:
                st.button("✕", key=f"remove_cf_{idx}", on_click=remove_custom_feature, args=(idx,))
    else:
        st.caption("No custom features added yet.")

    st.markdown("---")

    time_map = {
        "Past 24 Hours": "1d",
        "Past 7 Days": "7d",
        "Past 30 Days": "30d",
        "Past Year": "1y",
        "Any Time": ""
    }
    selected_time = st.selectbox("⏱️ Article Time Period", list(time_map.keys()), index=1)

    max_articles = st.slider(
        "📄 Max Articles to Scrape",
        min_value=10,
        max_value=500,
        value=100,
        step=10
    )

    manual_news_urls = st.text_area(
        "📰 Inject Specific Articles",
        placeholder="Paste URLs here, separated by commas..."
    )

    st.markdown("---")
    st.markdown('<div class="sidebar-title">🎥 YouTube Intelligence</div>', unsafe_allow_html=True)

    enable_youtube = st.checkbox("Enable YouTube Scraping", value=False)
    max_comments_per_video = st.slider(
        "💬 Max Comments per Video",
        min_value=50,
        max_value=500,
        value=150,
        step=25,
        disabled=not enable_youtube
    )
    auto_video_count = st.slider(
        "🎞️ Auto Discover Videos",
        min_value=3,
        max_value=25,
        value=10,
        step=1,
        disabled=not enable_youtube
    )
    manual_yt_urls = st.text_area(
        "🎥 Inject Specific Videos",
        placeholder="Paste YouTube URLs here..."
    )

    st.markdown("---")
    run_pipeline = st.button("🚀 Run Intelligence Pipeline", use_container_width=True)

custom_topics_tuple = tuple(st.session_state["custom_feature_tags"])

# =========================================================
# EXTRACTION TRIGGER
# =========================================================
if run_pipeline:
    with st.spinner("Executing omnichannel intelligence pipeline..."):
        st.toast("📰 Collecting media coverage...")
        media_df = fetch_live_media_data(
            master_query,
            time_map[selected_time],
            max_articles,
            manual_news_urls
        )

        yt_df = pd.DataFrame()

        if enable_youtube:
            if not api_key:
                st.sidebar.error("YouTube API key missing. YouTube scraping skipped.")
            else:
                st.toast("🎥 Discovering and scraping YouTube sources...")
                auto_video_ids = auto_discover_videos(api_key, master_query, max_videos=auto_video_count)
                manual_video_ids = extract_video_ids_from_text(manual_yt_urls)
                all_requested_ids = list(set(auto_video_ids + manual_video_ids))

                existing_ids = (
                    st.session_state["yt_db"]["Video ID"].dropna().unique().tolist()
                    if not st.session_state["yt_db"].empty and "Video ID" in st.session_state["yt_db"].columns
                    else []
                )

                new_ids_to_fetch = [vid for vid in all_requested_ids if vid not in existing_ids]

                if new_ids_to_fetch:
                    new_sources_df = get_video_metadata(api_key, new_ids_to_fetch)
                    new_yt_df = fetch_live_youtube_data(api_key, new_ids_to_fetch, max_comments_per_video=max_comments_per_video)

                    if not new_sources_df.empty:
                        st.session_state["sources_db"] = pd.concat(
                            [st.session_state["sources_db"], new_sources_df],
                            ignore_index=True
                        ).drop_duplicates(subset=["Video ID"], keep="last")

                    if not new_yt_df.empty:
                        enriched_new_yt_df = new_yt_df.merge(
                            new_sources_df[["Video ID", "Channel Name", "Subscribers", "Video Title", "Video Views", "Video Likes"]],
                            on="Video ID",
                            how="left"
                        )
                        st.session_state["yt_db"] = pd.concat(
                            [st.session_state["yt_db"], enriched_new_yt_df],
                            ignore_index=True
                        )

                yt_df = st.session_state["yt_db"].copy()

        combined_df = pd.concat([yt_df, media_df], ignore_index=True)

        if not combined_df.empty:
            processed = process_nlp(combined_df, custom_topics_tuple)
            st.session_state["live_data"] = processed
            st.success("Pipeline execution complete.")
        else:
            st.warning("No data returned from the selected sources.")

# =========================================================
# MAIN HEADER
# =========================================================
st.markdown('<div class="main-title">📡 Omnichannel Product Intelligence</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">A premium intelligence cockpit for product sentiment, pain points, feature narratives, and source influence.</div>',
    unsafe_allow_html=True
)

st.markdown(f"""
<div class="hero-card">
    <div style="font-size:1.05rem; color:#F3F4F6; font-weight:700; margin-bottom:6px;">
        Current Target
    </div>
    <div style="font-size:1.35rem; color:#BAE6FD; font-weight:700; margin-bottom:8px;">
        {master_query if master_query else "No target selected"}
    </div>
    <div class="small-note">
        This dashboard combines media and YouTube consumer voice, enriches it with rule-based NLP, and surfaces actionable product intelligence.
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# FILTERS
# =========================================================
raw_df = st.session_state["live_data"].copy()

if not raw_df.empty:
    feature_df, pain_df, intent_df = explode_for_analysis(raw_df)

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 🔍 Intelligence Filters")

        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1.2, 1.2, 1.1, 1.1])

        with filter_col1:
            selected_platform = st.multiselect(
                "Platform",
                sorted(feature_df["Platform"].dropna().unique().tolist()),
                default=sorted(feature_df["Platform"].dropna().unique().tolist())
            )

        with filter_col2:
            selected_feature = st.multiselect(
                "Feature / Topic",
                sorted(feature_df["Feature"].dropna().unique().tolist()),
                default=sorted(feature_df["Feature"].dropna().unique().tolist())
            )

        with filter_col3:
            selected_sentiment = st.multiselect(
                "Sentiment",
                ["Positive", "Neutral", "Negative"],
                default=["Positive", "Neutral", "Negative"]
            )

        with filter_col4:
            selected_intent = st.multiselect(
                "Intent",
                sorted(intent_df["Intent"].dropna().unique().tolist()),
                default=sorted(intent_df["Intent"].dropna().unique().tolist())
            )

        st.markdown('</div>', unsafe_allow_html=True)

    filtered_feature_df = feature_df[
        (feature_df["Platform"].isin(selected_platform)) &
        (feature_df["Feature"].isin(selected_feature)) &
        (feature_df["Sentiment_Category"].isin(selected_sentiment))
    ].copy()

    allowed_base_ids = set(filtered_feature_df.index.tolist())

    filtered_df = raw_df.loc[raw_df.index.isin(allowed_base_ids)].copy()

    filtered_intent_df = intent_df[
        (intent_df.index.isin(filtered_df.index)) &
        (intent_df["Intent"].isin(selected_intent))
    ].copy()

    allowed_after_intent = set(filtered_intent_df.index.tolist())
    filtered_df = filtered_df.loc[filtered_df.index.isin(allowed_after_intent)].copy()

    filtered_feature_df = filtered_feature_df.loc[filtered_feature_df.index.isin(filtered_df.index)].copy()
    filtered_pain_df = pain_df.loc[pain_df.index.isin(filtered_df.index)].copy()
    filtered_intent_df = filtered_intent_df.loc[filtered_intent_df.index.isin(filtered_df.index)].copy()

else:
    filtered_df = pd.DataFrame()
    filtered_feature_df = pd.DataFrame()
    filtered_pain_df = pd.DataFrame()
    filtered_intent_df = pd.DataFrame()

# =========================================================
# DASHBOARD
# =========================================================
if not filtered_df.empty:
    total_mentions = len(filtered_df)
    total_influence = filtered_df["Influence_Score"].sum()
    positive_share = (len(filtered_df[filtered_df["Sentiment_Category"] == "Positive"]) / total_mentions) * 100 if total_mentions else 0
    negative_share = (len(filtered_df[filtered_df["Sentiment_Category"] == "Negative"]) / total_mentions) * 100 if total_mentions else 0
    net_sentiment = filtered_df["Sentiment_Score"].mean()
    weighted_sentiment = filtered_df["Weighted_Sentiment"].mean()

    top_pain_point = "No pain point"
    pain_candidates = filtered_pain_df[
        (filtered_pain_df["Pain_Point"] != "None") &
        (filtered_pain_df["Sentiment_Category"] == "Negative")
    ]
    if not pain_candidates.empty:
        top_pain_point = pain_candidates["Pain_Point"].value_counts().idxmax()

    top_feature = filtered_feature_df["Feature"].value_counts().idxmax() if not filtered_feature_df.empty else "N/A"
    top_source = (
        filtered_df.groupby("Author")["Influence_Score"].sum().sort_values(ascending=False).index[0]
        if not filtered_df.empty else "N/A"
    )

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Mentions", f"{total_mentions:,}")
    m2.metric("Weighted Reach", f"{total_influence:,.1f}")
    m3.metric("Positive Share", f"{positive_share:.1f}%")
    m4.metric("Negative Share", f"{negative_share:.1f}%")
    m5.metric("Net Sentiment", f"{net_sentiment:.2f}")
    m6.metric("Weighted Sentiment", f"{weighted_sentiment:.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    summary_col1, summary_col2 = st.columns([1.6, 1.0])

    with summary_col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 🧠 Executive Summary")

        for insight in generate_summary_insights(
            filtered_df,
            feature_df=filtered_feature_df,
            pain_df=filtered_pain_df
        ):
            st.markdown(f"""
            <div class="summary-box">
                <div class="summary-title">Insight</div>
                <div class="summary-body">{insight}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with summary_col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### ⚡ Snapshot Signals")
        chips = [
            f"Top Feature: {top_feature}",
            f"Top Pain Point: {top_pain_point}",
            f"Most Influential Source: {top_source}",
            f"Active Platforms: {filtered_df['Platform'].nunique()}",
            f"Active Authors: {filtered_df['Author'].nunique()}",
            f"Intent Themes: {filtered_intent_df['Intent'].nunique() if not filtered_intent_df.empty else 0}"
        ]
        for chip in chips:
            st.markdown(f'<span class="insight-chip">{chip}</span>', unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.caption("Proxy metrics such as weighted reach and influence are model-derived signals, not platform-certified engagement.")
        st.markdown("</div>", unsafe_allow_html=True)

    tabs = st.tabs([
        "📈 Trends",
        "🧩 Feature Intelligence",
        "⚠️ Pain Point Radar",
        "🧭 Intent & Platform",
        "🏆 Source Influence",
        "🗂️ Ground Truth",
        "🎥 Active Video Vault"
    ])

    with tabs[0]:
        tc1, tc2 = st.columns(2)

        with tc1:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Mentions Over Time")
            trend_mentions = (
                filtered_df.groupby("Day")
                .size()
                .reset_index(name="Mentions")
                .sort_values("Day")
            )
            if not trend_mentions.empty:
                fig = px.line(trend_mentions, x="Day", y="Mentions", markers=True)
                fig.update_traces(line_width=3)
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#9CA3AF",
                    margin=dict(l=0, r=0, t=20, b=0),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="#1F2937")
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No time-series data available.")
            st.markdown("</div>", unsafe_allow_html=True)

        with tc2:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Negative Share Over Time")
            trend_sent = (
                filtered_df.groupby(["Day", "Sentiment_Category"])
                .size()
                .reset_index(name="Count")
            )

            if not trend_sent.empty:
                pivot = trend_sent.pivot(index="Day", columns="Sentiment_Category", values="Count").fillna(0)
                pivot["Negative Share %"] = np.where(
                    pivot.sum(axis=1) > 0,
                    (pivot.get("Negative", 0) / pivot.sum(axis=1)) * 100,
                    0
                )
                pivot = pivot.reset_index()

                fig = px.line(pivot, x="Day", y="Negative Share %", markers=True)
                fig.update_traces(line_width=3)
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#9CA3AF",
                    margin=dict(l=0, r=0, t=20, b=0),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="#1F2937", ticksuffix="%")
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No negative trend available.")
            st.markdown("</div>", unsafe_allow_html=True)

        tc3, tc4 = st.columns(2)

        with tc3:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Fastest Growing Feature Themes")
            growth_df = compare_recent_vs_previous(filtered_feature_df, "Feature", recent_days=7)
            if not growth_df.empty:
                st.dataframe(growth_df.head(12), use_container_width=True, height=360)
            else:
                st.info("Not enough dated data to compute growth.")
            st.markdown("</div>", unsafe_allow_html=True)

        with tc4:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Fastest Growing Pain Points")
            pain_growth_df = compare_recent_vs_previous(
                filtered_pain_df[filtered_pain_df["Pain_Point"] != "None"],
                "Pain_Point",
                recent_days=7
            )
            if not pain_growth_df.empty:
                st.dataframe(pain_growth_df.head(12), use_container_width=True, height=360)
            else:
                st.info("Not enough dated pain-point data to compute growth.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        fc1, fc2 = st.columns(2)

        with fc1:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Topic Polarization Matrix")
            topic_breakdown = (
                filtered_feature_df.groupby(["Feature", "Sentiment_Category"])
                .size()
                .reset_index(name="Count")
            )
            if not topic_breakdown.empty:
                fig_topic = px.bar(
                    topic_breakdown,
                    x="Count",
                    y="Feature",
                    color="Sentiment_Category",
                    orientation="h",
                    barmode="stack",
                    color_discrete_map=PREMIUM_COLORS
                )
                fig_topic.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#9CA3AF",
                    margin=dict(l=0, r=0, t=20, b=0),
                    xaxis=dict(showgrid=True, gridcolor="#1F2937"),
                    yaxis=dict(showgrid=False)
                )
                st.plotly_chart(fig_topic, use_container_width=True)
            else:
                st.info("No feature data available.")
            st.markdown("</div>", unsafe_allow_html=True)

        with fc2:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Feature Scorecard")
            if not filtered_feature_df.empty:
                feat_summary = (
                    filtered_feature_df.groupby("Feature")
                    .agg(
                        Mentions=("Feature", "count"),
                        Avg_Sentiment=("Sentiment_Score", "mean"),
                        Weighted_Sentiment=("Weighted_Sentiment", "mean"),
                        Weighted_Reach=("Influence_Score", "sum")
                    )
                    .reset_index()
                )

                sent_mix = (
                    filtered_feature_df.groupby(["Feature", "Sentiment_Category"])
                    .size()
                    .unstack(fill_value=0)
                    .reset_index()
                )
                feat_summary = feat_summary.merge(sent_mix, on="Feature", how="left").fillna(0)

                total_cols = [c for c in ["Positive", "Neutral", "Negative"] if c in feat_summary.columns]
                feat_summary["Positive %"] = np.where(
                    feat_summary[total_cols].sum(axis=1) > 0,
                    (feat_summary.get("Positive", 0) / feat_summary[total_cols].sum(axis=1)) * 100,
                    0
                )
                feat_summary["Negative %"] = np.where(
                    feat_summary[total_cols].sum(axis=1) > 0,
                    (feat_summary.get("Negative", 0) / feat_summary[total_cols].sum(axis=1)) * 100,
                    0
                )

                feat_summary = feat_summary.sort_values(["Mentions", "Weighted_Reach"], ascending=[False, False])

                st.dataframe(
                    feat_summary[[
                        "Feature", "Mentions", "Positive %", "Negative %",
                        "Avg_Sentiment", "Weighted_Sentiment", "Weighted_Reach"
                    ]],
                    use_container_width=True,
                    height=420
                )
            else:
                st.info("No feature summary available.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### Feature Heatmap")
        if not filtered_feature_df.empty:
            heatmap_df = (
                filtered_feature_df.groupby(["Feature", "Sentiment_Category"])
                .size()
                .reset_index(name="Count")
            )
            heat_pivot = heatmap_df.pivot(index="Feature", columns="Sentiment_Category", values="Count").fillna(0)
            heat_pivot = heat_pivot.reindex(columns=["Positive", "Neutral", "Negative"], fill_value=0)

            fig_heat = go.Figure(
                data=go.Heatmap(
                    z=heat_pivot.values,
                    x=heat_pivot.columns,
                    y=heat_pivot.index,
                    colorscale="Blues",
                    hovertemplate="Feature: %{y}<br>Sentiment: %{x}<br>Count: %{z}<extra></extra>"
                )
            )
            fig_heat.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#9CA3AF",
                margin=dict(l=0, r=0, t=20, b=0)
            )
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("No heatmap data available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        pc1, pc2 = st.columns(2)

        pain_neg = filtered_pain_df[
            (filtered_pain_df["Pain_Point"] != "None") &
            (filtered_pain_df["Sentiment_Category"] == "Negative")
        ].copy()

        with pc1:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Top Negative Pain Points")
            if not pain_neg.empty:
                pain_counts = pain_neg["Pain_Point"].value_counts().reset_index()
                pain_counts.columns = ["Pain_Point", "Count"]
                fig_pain = px.bar(
                    pain_counts.head(12),
                    x="Count",
                    y="Pain_Point",
                    orientation="h"
                )
                fig_pain.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#9CA3AF",
                    margin=dict(l=0, r=0, t=20, b=0),
                    xaxis=dict(showgrid=True, gridcolor="#1F2937"),
                    yaxis=dict(showgrid=False)
                )
                st.plotly_chart(fig_pain, use_container_width=True)
            else:
                st.info("No negative pain points detected.")
            st.markdown("</div>", unsafe_allow_html=True)

        with pc2:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Pain Point by Platform")
            if not pain_neg.empty:
                pain_platform = (
                    pain_neg.groupby(["Pain_Point", "Platform"])
                    .size()
                    .reset_index(name="Count")
                )
                fig = px.bar(
                    pain_platform,
                    x="Count",
                    y="Pain_Point",
                    color="Platform",
                    orientation="h",
                    barmode="stack",
                    color_discrete_map=PLATFORM_COLORS
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#9CA3AF",
                    margin=dict(l=0, r=0, t=20, b=0),
                    xaxis=dict(showgrid=True, gridcolor="#1F2937"),
                    yaxis=dict(showgrid=False)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No platform pain-point split available.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### Pain Point Scorecard")
        if not pain_neg.empty:
            pain_scorecard = (
                pain_neg.groupby("Pain_Point")
                .agg(
                    Negative_Mentions=("Pain_Point", "count"),
                    Avg_Sentiment=("Sentiment_Score", "mean"),
                    Weighted_Reach=("Influence_Score", "sum")
                )
                .reset_index()
                .sort_values(["Negative_Mentions", "Weighted_Reach"], ascending=[False, False])
            )
            st.dataframe(pain_scorecard, use_container_width=True, height=380)
        else:
            st.info("No negative pain-point scorecard available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[3]:
        ic1, ic2 = st.columns(2)

        with ic1:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Platform Health Distribution")
            platform_breakdown = (
                filtered_df.groupby(["Platform", "Sentiment_Category"])
                .size()
                .reset_index(name="Count")
            )
            if not platform_breakdown.empty:
                fig_platform = px.bar(
                    platform_breakdown,
                    x="Count",
                    y="Platform",
                    color="Sentiment_Category",
                    orientation="h",
                    barmode="stack",
                    color_discrete_map=PREMIUM_COLORS
                )
                fig_platform.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#9CA3AF",
                    margin=dict(l=0, r=0, t=20, b=0),
                    xaxis=dict(showgrid=True, gridcolor="#1F2937"),
                    yaxis=dict(showgrid=False)
                )
                st.plotly_chart(fig_platform, use_container_width=True)
            else:
                st.info("No platform health distribution available.")
            st.markdown("</div>", unsafe_allow_html=True)

        with ic2:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Intent Distribution")
            if not filtered_intent_df.empty:
                intent_counts = filtered_intent_df["Intent"].value_counts().reset_index()
                intent_counts.columns = ["Intent", "Count"]

                fig = px.bar(intent_counts, x="Count", y="Intent", orientation="h")
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#9CA3AF",
                    margin=dict(l=0, r=0, t=20, b=0),
                    xaxis=dict(showgrid=True, gridcolor="#1F2937"),
                    yaxis=dict(showgrid=False)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No intent data available.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### Intent × Sentiment Table")
        if not filtered_intent_df.empty:
            intent_sent = (
                filtered_intent_df.groupby(["Intent", "Sentiment_Category"])
                .size()
                .unstack(fill_value=0)
                .reset_index()
            )
            st.dataframe(intent_sent, use_container_width=True, height=360)
        else:
            st.info("No intent-sentiment matrix available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[4]:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### Source Influence Leaderboard")

        source_table = (
            filtered_df.groupby(["Author", "Platform", "Source_Tier"])
            .agg(
                Mentions=("Author", "count"),
                Avg_Sentiment=("Sentiment_Score", "mean"),
                Weighted_Reach=("Influence_Score", "sum"),
                Negative_Mentions=("Sentiment_Category", lambda x: (x == "Negative").sum()),
                Positive_Mentions=("Sentiment_Category", lambda x: (x == "Positive").sum())
            )
            .reset_index()
            .sort_values(["Weighted_Reach", "Mentions"], ascending=[False, False])
        )

        st.dataframe(source_table, use_container_width=True, height=450)
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[5]:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 💬 Filtered Ground Truth Explorer")

        display_df = filtered_df.copy()
        display_df["Feature"] = display_df["Feature_List"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
        display_df["Pain Point"] = display_df["Pain_Point_List"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
        display_df["Intent"] = display_df["Intent_List"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
        display_df["Date_Display"] = display_df["Date_Local"].dt.strftime("%Y-%m-%d %H:%M") if "Date_Local" in display_df.columns else display_df["Date"]

        search_term = st.text_input("Search in content", placeholder="Try words like battery, heating, overpriced...")
        if search_term:
            display_df = display_df[
                display_df["Content"].str.contains(search_term, case=False, na=False)
            ]

        display_df = display_df.sort_values(by="Date", ascending=False)

        def color_sentiment(val):
            return f"color: {PREMIUM_COLORS.get(val, '#9CA3AF')}; font-weight: 600;"

        st.dataframe(
            display_df[[
                "Date_Display", "Platform", "Author", "Feature", "Pain Point",
                "Intent", "Sentiment_Category", "Sentiment_Score",
                "Influence_Score", "Content"
            ]].style.map(color_sentiment, subset=["Sentiment_Category"]),
            use_container_width=True,
            height=520
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[6]:
        if "sources_db" in st.session_state and not st.session_state["sources_db"].empty:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown(f"### 📂 Active Video Vault ({len(st.session_state['sources_db'])} videos tracked)")
            st.dataframe(st.session_state["sources_db"], use_container_width=True, height=480)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No tracked YouTube source vault yet. Enable YouTube scraping and run the pipeline.")

else:
    st.info("👈 Configure your target in the sidebar and run the intelligence pipeline.")

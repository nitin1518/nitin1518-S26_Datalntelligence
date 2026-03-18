import math
import hashlib
import re
import urllib.parse
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import feedparser
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import trafilatura
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from newspaper import Article
from textblob import TextBlob

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
        --text: #F3F4F6;
        --muted: #9CA3AF;
        --muted-2: #94A3B8;
        --accent: #38BDF8;
        --green: #10B981;
        --red: #EF4444;
        --amber: #F59E0B;
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

    hr { border-color: var(--border) !important; }
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
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
}

PREMIUM_COLORS = {
    "Positive": "#10B981",
    "Neutral": "#6B7280",
    "Negative": "#EF4444"
}

PLATFORM_COLORS = {
    "YouTube": "#8B5CF6",
    "News": "#38BDF8",
    "Direct Article": "#F59E0B"
}

FEATURE_MAP = {
    "Display/Screen": [
        "screen", "display", "pixel", "oled", "amoled", "brightness",
        "refresh rate", "bezel", "hdr", "10 bit", "10bit", "8 bit", "8bit",
        "color depth", "panel", "banding", "posterization"
    ],
    "Battery/Power": [
        "battery", "drain", "mah", "charge", "charging", "backup",
        "power", "heating", "warm"
    ],
    "Price/Value": [
        "price", "overpriced", "cost", "expensive", "cheap",
        "value for money", "worth", "pricing"
    ],
    "Performance/Chip": [
        "exynos", "snapdragon", "thermal", "lag", "chip",
        "processor", "speed", "stutter", "smooth"
    ],
    "Camera": [
        "camera", "zoom", "lens", "photo", "video",
        "portrait", "night mode", "shot", "selfie"
    ],
    "Software/App": [
        "app", "software", "ui", "one ui", "update",
        "bug", "crash", "glitch", "interface"
    ],
    "Connectivity": [
        "network", "wifi", "wi fi", "bluetooth", "signal",
        "5g", "connection", "connected"
    ],
    "Build/Design": [
        "design", "build", "premium", "weight", "feel",
        "body", "look", "finish"
    ],
    "Audio/Speakers": [
        "speaker", "audio", "sound", "mic", "microphone", "volume"
    ],
    "Service/Installation": [
        "installation", "install", "service", "technician",
        "support", "customer care", "engineer"
    ]
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
    "Installation Issue": ["installation issue", "install issue", "setup issue", "difficult to install"],
    "10-Bit / Display Quality": ["10 bit", "10bit", "banding", "posterization", "display issue", "panel issue"]
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
    "must buy": 0.8,
    "banding": -0.7,
    "posterization": -0.7
}

# =========================================================
# SESSION STATE
# =========================================================
defaults = {
    "yt_db": pd.DataFrame(),
    "sources_db": pd.DataFrame(),
    "live_data": pd.DataFrame(),
    "raw_news_data": pd.DataFrame(),
    "discovered_urls_df": pd.DataFrame(),
    "pipeline_stats": {},
    "custom_feature_tags": [],
    "custom_feature_input": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# HELPERS
# =========================================================
def normalize_text(text):
    return re.sub(r"\s+", " ", str(text)).strip()

def normalize_for_matching(text):
    text = str(text).lower().strip()
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("/", " ").replace("_", " ")
    text = text.replace("-", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def build_flexible_pattern(phrase):
    norm = normalize_for_matching(phrase)
    if not norm:
        return None

    words = norm.split()
    parts = []
    for w in words:
        if w.isdigit():
            parts.append(rf"{re.escape(w)}")
        elif len(w) <= 3:
            parts.append(rf"{re.escape(w)}")
        else:
            parts.append(rf"{re.escape(w)}(?:s|ed|ing)?")
    return r"\b" + r"\s*".join(parts) + r"\b"

def safe_log1p(x):
    try:
        return math.log1p(max(float(x), 0))
    except Exception:
        return 0.0

def clean_text(text):
    return re.sub(r"\s+", " ", str(text)).strip()

def text_hash(text):
    return hashlib.md5(str(text).encode("utf-8")).hexdigest()

def canonicalize_url(url):
    try:
        p = urllib.parse.urlparse(url)
        q = urllib.parse.parse_qs(p.query)
        if "url" in q:
            return q["url"][0]
        return urllib.parse.urlunparse((p.scheme, p.netloc, p.path, "", "", ""))
    except Exception:
        return url

def safe_df_for_display(df):
    if df is None or len(df) == 0:
        return df
    out = df.copy()

    for col in out.columns:
        out[col] = out[col].apply(
            lambda x: ", ".join(map(str, x)) if isinstance(x, (list, tuple, set))
            else str(x) if isinstance(x, dict)
            else x
        )

    out = out.replace([np.inf, -np.inf], np.nan)

    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            try:
                out[col] = out[col].dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                out[col] = out[col].astype(str)

    out = out.fillna("")
    return out

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

def extract_video_ids_from_text(text):
    if not text:
        return []

    normalized = str(text).replace("\n", " ").replace("\r", " ").replace(",", " ")
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    matches = re.findall(regex, normalized)

    raw_ids = [
        word.strip()
        for word in normalized.split()
        if len(word.strip()) == 11 and re.match(r'^[0-9A-Za-z_-]{11}$', word.strip())
    ]

    return list(dict.fromkeys(matches + raw_ids))

# =========================================================
# DISCOVERY
# =========================================================
def build_query_variants(base_query, enable_expansion=True):
    base_query = base_query.strip()
    variants = [base_query]
    if not enable_expansion or not base_query:
        return variants

    expansions = [
        "review", "reviews", "news", "price", "battery", "camera",
        "display", "performance", "issue", "issues", "complaint",
        "complaints", "comparison", "vs", "10 bit", "banding",
        "display issue", "screen issue"
    ]
    for ex in expansions:
        variants.append(f"{base_query} {ex}")
    return list(dict.fromkeys(variants))

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_google_news_rss_urls(query, time_filter, max_urls):
    safe_query = urllib.parse.quote(f"{query} when:{time_filter}" if time_filter else query)
    url = f"https://news.google.com/rss/search?q={safe_query}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)

    rows = []
    for entry in feed.entries[:max_urls]:
        source_title = "Unknown"
        if hasattr(entry, "source") and hasattr(entry.source, "title"):
            source_title = entry.source.title
        rows.append({
            "Discovery_Source": "Google News RSS",
            "Title": entry.get("title", ""),
            "URL": canonicalize_url(entry.get("link", "")),
            "Published": entry.get("published", ""),
            "Source": source_title,
            "Summary": BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(" ", strip=True)
        })
    return rows

def fetch_bing_search_urls(query, max_urls=100):
    rows = []
    try:
        search_url = f"https://www.bing.com/news/search?q={urllib.parse.quote(query)}"
        res = requests.get(search_url, headers=HEADERS, timeout=12)
        soup = BeautifulSoup(res.text, "html.parser")

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(" ", strip=True)
            if href.startswith("http") and "bing.com" not in href and len(text) > 20:
                links.append((href, text))

        seen = set()
        for href, text in links:
            href = canonicalize_url(href)
            if href not in seen:
                seen.add(href)
                rows.append({
                    "Discovery_Source": "Bing News",
                    "Title": text,
                    "URL": href,
                    "Published": "",
                    "Source": urllib.parse.urlparse(href).netloc,
                    "Summary": ""
                })
            if len(rows) >= max_urls:
                break
    except Exception:
        pass
    return rows

def discover_urls(base_query, time_filter, max_discovery_urls=1000, enable_expansion=True, use_bing=True, manual_urls=""):
    variants = build_query_variants(base_query, enable_expansion=enable_expansion)
    discovered = []
    per_variant_rss = max(20, min(100, max_discovery_urls // max(len(variants), 1)))

    for q in variants:
        discovered.extend(fetch_google_news_rss_urls(q, time_filter, per_variant_rss))
        if use_bing:
            discovered.extend(fetch_bing_search_urls(q, max_urls=max(20, per_variant_rss)))

    if manual_urls:
        urls = [u.strip() for u in str(manual_urls).split(",") if u.strip().startswith("http")]
        for u in urls:
            discovered.append({
                "Discovery_Source": "Manual URL",
                "Title": u,
                "URL": canonicalize_url(u),
                "Published": "",
                "Source": urllib.parse.urlparse(u).netloc,
                "Summary": ""
            })

    if not discovered:
        return pd.DataFrame()

    df = pd.DataFrame(discovered)
    df["URL"] = df["URL"].astype(str).apply(canonicalize_url)
    df = df[df["URL"].str.startswith("http", na=False)].copy()

    df["url_key"] = df["URL"].str.lower().str.strip()
    df = df.drop_duplicates(subset=["url_key"]).drop(columns=["url_key"])

    norm_base = normalize_for_matching(base_query)
    query_words = [w for w in norm_base.split() if len(w) > 2]

    def relevance_score(row):
        text = normalize_for_matching(f"{row.get('Title','')} {row.get('Summary','')}")
        score = 0
        for w in query_words:
            if w in text:
                score += 1
        return score

    df["Relevance_Score"] = df.apply(relevance_score, axis=1)
    df = df.sort_values(["Relevance_Score", "Published"], ascending=[False, False]).head(max_discovery_urls).reset_index(drop=True)
    return df

# =========================================================
# EXTRACTION
# =========================================================
def extract_article_content(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
                include_formatting=False
            )
            if text and len(text) > 200:
                return text
    except Exception:
        pass

    try:
        article = Article(url)
        article.download()
        article.parse()
        if article.text and len(article.text) > 200:
            return article.text
    except Exception:
        pass

    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text(" ", strip=True) for p in paragraphs])
        if len(text) > 200:
            return text
    except Exception:
        pass

    return ""

def extract_single_url(row):
    url = row["URL"]
    content = clean_text(extract_article_content(url))

    if len(content) < 120:
        fallback = clean_text(f"{row.get('Title', '')}. {row.get('Summary', '')}")
        if len(fallback) >= 80:
            content = fallback
        else:
            return None

    return {
        "Date": row.get("Published", ""),
        "Platform": "News" if row.get("Discovery_Source") != "Manual URL" else "Direct Article",
        "Author": row.get("Source", "Unknown"),
        "Source": row.get("Source", "Unknown"),
        "Title": row.get("Title", ""),
        "Content": content[:12000],
        "Engagement": np.nan,
        "URL": url,
        "Discovery_Source": row.get("Discovery_Source", "Unknown")
    }

@st.cache_data(ttl=3600, show_spinner=False)
def run_news_pipeline(base_query, time_filter, max_discovery_urls, max_extracted_articles, enable_expansion, use_bing, manual_urls, max_workers):
    discovered_df = discover_urls(
        base_query=base_query,
        time_filter=time_filter,
        max_discovery_urls=max_discovery_urls,
        enable_expansion=enable_expansion,
        use_bing=use_bing,
        manual_urls=manual_urls
    )

    if discovered_df.empty:
        return pd.DataFrame(), discovered_df, {
            "discovered_urls": 0,
            "extraction_attempts": 0,
            "valid_extractions": 0,
            "duplicates_removed": 0,
            "final_articles": 0
        }

    records = []
    seen_hashes = set()
    extraction_attempts = 0
    valid_extractions = 0
    duplicates_removed = 0

    rows = discovered_df.to_dict("records")
    rows = rows[: max(max_discovery_urls, max_extracted_articles)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(extract_single_url, row) for row in rows]

        for future in as_completed(futures):
            extraction_attempts += 1
            try:
                result = future.result()
            except Exception:
                result = None

            if result is None:
                continue

            valid_extractions += 1
            h = text_hash(result["Content"][:3000])
            if h in seen_hashes:
                duplicates_removed += 1
                continue

            seen_hashes.add(h)
            records.append(result)

            if len(records) >= max_extracted_articles:
                break

    news_df = pd.DataFrame(records)
    stats = {
        "discovered_urls": len(discovered_df),
        "extraction_attempts": extraction_attempts,
        "valid_extractions": valid_extractions,
        "duplicates_removed": duplicates_removed,
        "final_articles": len(news_df)
    }
    return news_df, discovered_df, stats

# =========================================================
# YOUTUBE ENGINE
# =========================================================
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
        seen_comments = set()

        for order_mode in ["relevance", "time"]:
            try:
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=vid_id,
                    maxResults=100,
                    order=order_mode,
                    textFormat="plainText"
                )
                extracted = 0

                while request and extracted < max_comments_per_video:
                    response = request.execute()

                    for item in response.get("items", []):
                        snippet = item["snippet"]["topLevelComment"]["snippet"]
                        text_val = snippet.get("textDisplay", "").strip()

                        if not text_val:
                            continue

                        dedupe_key = f"{vid_id}::{text_val.lower()[:300]}"
                        if dedupe_key in seen_comments:
                            continue
                        seen_comments.add(dedupe_key)

                        comments_data.append({
                            "Video ID": vid_id,
                            "Date": snippet.get("publishedAt"),
                            "Platform": "YouTube",
                            "Author": snippet.get("authorDisplayName", "Anonymous"),
                            "Source": snippet.get("authorDisplayName", "Anonymous"),
                            "Title": "",
                            "Content": text_val,
                            "Engagement": int(snippet.get("likeCount", 0)),
                            "URL": f"https://www.youtube.com/watch?v={vid_id}"
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
                            order=order_mode,
                            textFormat="plainText"
                        )
                    else:
                        break
            except Exception:
                pass

    return pd.DataFrame(comments_data)

# =========================================================
# NLP
# =========================================================
def get_score(text):
    t = str(text).lower()
    for key, val in TECH_OVERRIDES.items():
        if key in t:
            return val
    return TextBlob(str(text)).sentiment.polarity

def get_category(score):
    if score > 0.05:
        return "Positive"
    if score < -0.05:
        return "Negative"
    return "Neutral"

def get_features(text, custom_list):
    t = normalize_for_matching(text)
    matched = []

    for custom_feat in custom_list:
        pattern = build_flexible_pattern(custom_feat)
        if pattern and re.search(pattern, t):
            matched.append(custom_feat)

    for feature, keywords in FEATURE_MAP.items():
        for kw in keywords:
            pattern = build_flexible_pattern(kw)
            if pattern and re.search(pattern, t):
                matched.append(feature)
                break

    return list(dict.fromkeys(matched)) if matched else ["General/Other"]

def detect_pain_points(text):
    t = normalize_for_matching(text)
    found = []

    for pain_point, vals in PAIN_POINT_MAP.items():
        for v in vals:
            pattern = build_flexible_pattern(v)
            if pattern and re.search(pattern, t):
                found.append(pain_point)
                break

    return found if found else ["None"]

def classify_intent(text):
    t = normalize_for_matching(text)
    found = []

    for intent, vals in INTENT_MAP.items():
        for v in vals:
            pattern = build_flexible_pattern(v)
            if pattern and re.search(pattern, t):
                found.append(intent)
                break

    return found if found else ["General Discussion"]

def source_tier(platform, author, subs=0):
    author_l = str(author).lower()

    if platform == "YouTube":
        if subs >= 1000000:
            return "Top Creator"
        if subs >= 100000:
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
    if platform == "News":
        return round(base + 4.0, 3)
    if platform == "Direct Article":
        return round(base + 2.5, 3)
    return round(base, 3)

@st.cache_data(show_spinner=False)
def process_nlp(df, custom_topics_tuple):
    if df.empty:
        return df

    custom_list = list(custom_topics_tuple) if custom_topics_tuple else []
    out = df.copy()

    out["Date"] = pd.to_datetime(out["Date"], errors="coerce", utc=True)
    out["Date_Local"] = out["Date"].dt.tz_convert("Asia/Kolkata")
    out["Day"] = out["Date_Local"].dt.date.astype(str)
    out["Week"] = out["Date_Local"].dt.strftime("%Y-W%U")
    out["Month"] = out["Date_Local"].dt.strftime("%Y-%m")

    for col in ["Title", "Video Title", "Content", "Author", "Source"]:
        if col not in out.columns:
            out[col] = ""
        out[col] = out[col].astype(str).fillna("")

    out["Content"] = out["Content"].apply(normalize_text)
    out["Analysis_Text"] = (
        out["Title"].fillna("") + " " +
        out["Video Title"].fillna("") + " " +
        out["Content"].fillna("")
    ).str.strip()

    out["Sentiment_Score"] = out["Content"].apply(get_score)
    out["Sentiment_Category"] = out["Sentiment_Score"].apply(get_category)
    out["Feature_List"] = out["Analysis_Text"].apply(lambda x: get_features(x, custom_list))
    out["Pain_Point_List"] = out["Analysis_Text"].apply(detect_pain_points)
    out["Intent_List"] = out["Analysis_Text"].apply(classify_intent)

    if "Subscribers" not in out.columns:
        out["Subscribers"] = 0

    out["Source_Tier"] = out.apply(
        lambda r: source_tier(r.get("Platform", ""), r.get("Author", ""), r.get("Subscribers", 0)),
        axis=1
    )
    out["Influence_Score"] = out.apply(compute_influence, axis=1)
    out["Weighted_Sentiment"] = out["Sentiment_Score"] * (out["Influence_Score"] + 1)
    return out

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
# SUMMARY
# =========================================================
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
    if "Author" in base_df.columns and "Influence_Score" in base_df.columns:
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

    temp = df.copy()
    temp = temp[temp[dimension_col].notna()].copy()
    temp[dimension_col] = temp[dimension_col].astype(str).str.strip()
    temp = temp[temp[dimension_col] != ""]

    if temp.empty:
        return pd.DataFrame()

    max_date = temp["Date_Local"].max()
    if pd.isna(max_date):
        return pd.DataFrame()

    recent_start = max_date - pd.Timedelta(days=recent_days)
    prev_start = recent_start - pd.Timedelta(days=recent_days)

    recent = temp[(temp["Date_Local"] >= recent_start) & (temp["Date_Local"] <= max_date)]
    previous = temp[(temp["Date_Local"] >= prev_start) & (temp["Date_Local"] < recent_start)]

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

    out = out.replace([np.inf, -np.inf], 0)
    out = out.fillna(0)
    return out.sort_values("Growth_%", ascending=False)

# =========================================================
# SIDEBAR
# =========================================================
try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
except Exception:
    api_key = None

with st.sidebar:
    st.markdown('<div class="sidebar-title">⚙️ Extraction Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-caption">Expanded discovery + better YouTube issue extraction + safer rendering.</div>', unsafe_allow_html=True)

    master_query = st.text_input("🎯 Target Product / Query", value="Samsung S26 Ultra")

    st.markdown("#### ➕ Custom Feature Tracking")
    st.caption("Added keywords always appear in the Feature / Topic filter list, even when no rows matched them yet.")

    cf1, cf2 = st.columns([3, 1])
    with cf1:
        st.text_input(
            "Custom feature input",
            key="custom_feature_input",
            placeholder="e.g., 10-Bit, Drain, App Crash",
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

    auto_expand = st.checkbox("🔎 Auto Query Expansion", value=True)
    use_bing_discovery = st.checkbox("🌐 Add Bing Discovery", value=True)

    max_discovery_urls = st.number_input(
        "🌐 Discovery URL Pool Size",
        min_value=50,
        max_value=5000,
        value=1200,
        step=100
    )

    max_extracted_articles = st.number_input(
        "📰 Max Successfully Extracted Articles",
        min_value=20,
        max_value=2000,
        value=300,
        step=25
    )

    max_workers = st.slider("⚡ Parallel Extraction Workers", 4, 32, 12, 2)

    manual_news_urls = st.text_area(
        "📰 Inject Specific Articles",
        placeholder="Paste article URLs here, separated by commas..."
    )

    st.markdown("---")
    st.markdown('<div class="sidebar-title">🎥 YouTube Intelligence</div>', unsafe_allow_html=True)

    enable_youtube = st.checkbox("Enable YouTube Scraping", value=False)
    max_comments_per_video = st.slider("💬 Max Comments per Video", 50, 500, 200, 25, disabled=not enable_youtube)
    auto_video_count = st.slider("🎞️ Auto Discover Videos", 3, 25, 10, 1, disabled=not enable_youtube)
    manual_yt_urls = st.text_area(
        "🎥 Inject Specific Videos",
        placeholder="Paste YouTube URLs here, separated by commas or new lines..."
    )

    st.markdown("---")
    show_debug = st.checkbox("Show debug", value=False)
    run_pipeline = st.button("🚀 Run Intelligence Pipeline", use_container_width=True)

custom_topics_tuple = tuple(st.session_state["custom_feature_tags"])

# =========================================================
# DISCOVERY FUNCTIONS
# =========================================================
def build_query_variants(base_query, enable_expansion=True):
    base_query = base_query.strip()
    variants = [base_query]
    if not enable_expansion or not base_query:
        return variants

    expansions = [
        "review", "reviews", "news", "price", "battery", "camera",
        "display", "performance", "issue", "issues", "complaint",
        "complaints", "comparison", "vs", "10 bit", "banding",
        "display issue", "screen issue"
    ]
    for ex in expansions:
        variants.append(f"{base_query} {ex}")
    return list(dict.fromkeys(variants))

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_google_news_rss_urls(query, time_filter, max_urls):
    safe_query = urllib.parse.quote(f"{query} when:{time_filter}" if time_filter else query)
    url = f"https://news.google.com/rss/search?q={safe_query}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)

    rows = []
    for entry in feed.entries[:max_urls]:
        source_title = "Unknown"
        if hasattr(entry, "source") and hasattr(entry.source, "title"):
            source_title = entry.source.title
        rows.append({
            "Discovery_Source": "Google News RSS",
            "Title": entry.get("title", ""),
            "URL": canonicalize_url(entry.get("link", "")),
            "Published": entry.get("published", ""),
            "Source": source_title,
            "Summary": BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(" ", strip=True)
        })
    return rows

def fetch_bing_search_urls(query, max_urls=100):
    rows = []
    try:
        search_url = f"https://www.bing.com/news/search?q={urllib.parse.quote(query)}"
        res = requests.get(search_url, headers=HEADERS, timeout=12)
        soup = BeautifulSoup(res.text, "html.parser")

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(" ", strip=True)
            if href.startswith("http") and "bing.com" not in href and len(text) > 20:
                links.append((href, text))

        seen = set()
        for href, text in links:
            href = canonicalize_url(href)
            if href not in seen:
                seen.add(href)
                rows.append({
                    "Discovery_Source": "Bing News",
                    "Title": text,
                    "URL": href,
                    "Published": "",
                    "Source": urllib.parse.urlparse(href).netloc,
                    "Summary": ""
                })
            if len(rows) >= max_urls:
                break
    except Exception:
        pass
    return rows

def discover_urls(base_query, time_filter, max_discovery_urls=1000, enable_expansion=True, use_bing=True, manual_urls=""):
    variants = build_query_variants(base_query, enable_expansion=enable_expansion)
    discovered = []
    per_variant_rss = max(20, min(100, max_discovery_urls // max(len(variants), 1)))

    for q in variants:
        discovered.extend(fetch_google_news_rss_urls(q, time_filter, per_variant_rss))
        if use_bing:
            discovered.extend(fetch_bing_search_urls(q, max_urls=max(20, per_variant_rss)))

    if manual_urls:
        urls = [u.strip() for u in str(manual_urls).split(",") if u.strip().startswith("http")]
        for u in urls:
            discovered.append({
                "Discovery_Source": "Manual URL",
                "Title": u,
                "URL": canonicalize_url(u),
                "Published": "",
                "Source": urllib.parse.urlparse(u).netloc,
                "Summary": ""
            })

    if not discovered:
        return pd.DataFrame()

    df = pd.DataFrame(discovered)
    df["URL"] = df["URL"].astype(str).apply(canonicalize_url)
    df = df[df["URL"].str.startswith("http", na=False)].copy()

    df["url_key"] = df["URL"].str.lower().str.strip()
    df = df.drop_duplicates(subset=["url_key"]).drop(columns=["url_key"])

    norm_base = normalize_for_matching(base_query)
    query_words = [w for w in norm_base.split() if len(w) > 2]

    def relevance_score(row):
        text = normalize_for_matching(f"{row.get('Title','')} {row.get('Summary','')}")
        score = 0
        for w in query_words:
            if w in text:
                score += 1
        return score

    df["Relevance_Score"] = df.apply(relevance_score, axis=1)
    df = df.sort_values(["Relevance_Score", "Published"], ascending=[False, False]).head(max_discovery_urls).reset_index(drop=True)
    return df

# =========================================================
# EXTRACTION FUNCTIONS
# =========================================================
def extract_article_content(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
                include_formatting=False
            )
            if text and len(text) > 200:
                return text
    except Exception:
        pass

    try:
        article = Article(url)
        article.download()
        article.parse()
        if article.text and len(article.text) > 200:
            return article.text
    except Exception:
        pass

    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text(" ", strip=True) for p in paragraphs])
        if len(text) > 200:
            return text
    except Exception:
        pass

    return ""

def extract_single_url(row):
    url = row["URL"]
    content = clean_text(extract_article_content(url))

    if len(content) < 120:
        fallback = clean_text(f"{row.get('Title', '')}. {row.get('Summary', '')}")
        if len(fallback) >= 80:
            content = fallback
        else:
            return None

    return {
        "Date": row.get("Published", ""),
        "Platform": "News" if row.get("Discovery_Source") != "Manual URL" else "Direct Article",
        "Author": row.get("Source", "Unknown"),
        "Source": row.get("Source", "Unknown"),
        "Title": row.get("Title", ""),
        "Content": content[:12000],
        "Engagement": np.nan,
        "URL": url,
        "Discovery_Source": row.get("Discovery_Source", "Unknown")
    }

@st.cache_data(ttl=3600, show_spinner=False)
def run_news_pipeline(base_query, time_filter, max_discovery_urls, max_extracted_articles, enable_expansion, use_bing, manual_urls, max_workers):
    discovered_df = discover_urls(
        base_query=base_query,
        time_filter=time_filter,
        max_discovery_urls=max_discovery_urls,
        enable_expansion=enable_expansion,
        use_bing=use_bing,
        manual_urls=manual_urls
    )

    if discovered_df.empty:
        return pd.DataFrame(), discovered_df, {
            "discovered_urls": 0,
            "extraction_attempts": 0,
            "valid_extractions": 0,
            "duplicates_removed": 0,
            "final_articles": 0
        }

    records = []
    seen_hashes = set()
    extraction_attempts = 0
    valid_extractions = 0
    duplicates_removed = 0

    rows = discovered_df.to_dict("records")
    rows = rows[: max(max_discovery_urls, max_extracted_articles)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(extract_single_url, row) for row in rows]

        for future in as_completed(futures):
            extraction_attempts += 1
            try:
                result = future.result()
            except Exception:
                result = None

            if result is None:
                continue

            valid_extractions += 1
            h = text_hash(result["Content"][:3000])
            if h in seen_hashes:
                duplicates_removed += 1
                continue

            seen_hashes.add(h)
            records.append(result)

            if len(records) >= max_extracted_articles:
                break

    news_df = pd.DataFrame(records)
    stats = {
        "discovered_urls": len(discovered_df),
        "extraction_attempts": extraction_attempts,
        "valid_extractions": valid_extractions,
        "duplicates_removed": duplicates_removed,
        "final_articles": len(news_df)
    }
    return news_df, discovered_df, stats

# =========================================================
# PIPELINE EXECUTION
# =========================================================
if run_pipeline:
    with st.spinner("Running expanded discovery + extraction pipeline..."):
        st.toast("🌐 Discovering large URL pool...")
        news_df, discovered_df, stats = run_news_pipeline(
            base_query=master_query,
            time_filter=time_map[selected_time],
            max_discovery_urls=int(max_discovery_urls),
            max_extracted_articles=int(max_extracted_articles),
            enable_expansion=auto_expand,
            use_bing=use_bing_discovery,
            manual_urls=manual_news_urls,
            max_workers=int(max_workers)
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

                    if not new_yt_df.empty and not new_sources_df.empty:
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

        combined_df = pd.concat([news_df, yt_df], ignore_index=True)

        st.session_state["raw_news_data"] = news_df
        st.session_state["discovered_urls_df"] = discovered_df
        st.session_state["pipeline_stats"] = stats

        if not combined_df.empty:
            processed = process_nlp(combined_df, custom_topics_tuple)
            st.session_state["live_data"] = processed
            st.success(
                f"Done. Discovered {stats.get('discovered_urls', 0):,} URLs, extracted {stats.get('final_articles', 0):,} news articles, final combined rows {len(combined_df):,}."
            )
        else:
            st.warning("No data returned from the selected sources.")

# =========================================================
# MAIN HEADER
# =========================================================
st.markdown('<div class="main-title">📡 Omnichannel Product Intelligence</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Expanded discovery pipeline: query expansion + Google News RSS + Bing discovery + stronger YouTube issue extraction.</div>',
    unsafe_allow_html=True
)

stats = st.session_state.get("pipeline_stats", {})
stats_text = (
    f"Discovered URLs: {stats.get('discovered_urls', 0):,} • "
    f"Extraction attempts: {stats.get('extraction_attempts', 0):,} • "
    f"Valid extractions: {stats.get('valid_extractions', 0):,} • "
    f"Duplicates removed: {stats.get('duplicates_removed', 0):,} • "
    f"Final articles: {stats.get('final_articles', 0):,}"
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
        {stats_text}
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# FILTER PREP
# =========================================================
raw_df = st.session_state["live_data"].copy()

if not raw_df.empty:
    feature_df, pain_df, intent_df = explode_for_analysis(raw_df)

    detected_features = sorted(feature_df["Feature"].dropna().unique().tolist())
    custom_features = [x.strip() for x in st.session_state["custom_feature_tags"] if x.strip()]
    all_feature_options = sorted(set(detected_features + custom_features), key=lambda x: x.lower())

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 🔍 Intelligence Filters")

        c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.1, 1.1])

        with c1:
            selected_platform = st.multiselect(
                "Platform",
                sorted(feature_df["Platform"].dropna().unique().tolist()),
                default=sorted(feature_df["Platform"].dropna().unique().tolist())
            )

        with c2:
            selected_feature = st.multiselect(
                "Feature / Topic",
                all_feature_options,
                default=all_feature_options
            )

        with c3:
            selected_sentiment = st.multiselect(
                "Sentiment",
                ["Positive", "Neutral", "Negative"],
                default=["Positive", "Neutral", "Negative"]
            )

        with c4:
            selected_intent = st.multiselect(
                "Intent",
                sorted(intent_df["Intent"].dropna().unique().tolist()),
                default=sorted(intent_df["Intent"].dropna().unique().tolist())
            )

        st.markdown("</div>", unsafe_allow_html=True)

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
    filtered_intent_df = intent_df.loc[intent_df.index.isin(filtered_df.index)].copy()
else:
    feature_df = pd.DataFrame()
    pain_df = pd.DataFrame()
    intent_df = pd.DataFrame()
    filtered_df = pd.DataFrame()
    filtered_feature_df = pd.DataFrame()
    filtered_pain_df = pd.DataFrame()
    filtered_intent_df = pd.DataFrame()
    all_feature_options = st.session_state["custom_feature_tags"]

# =========================================================
# DEBUG
# =========================================================
if show_debug:
    with st.expander("Debug: Pipeline and custom feature detection"):
        st.write("Tracked custom features:", list(custom_topics_tuple))
        st.write("Pipeline stats:", st.session_state.get("pipeline_stats", {}))

        discovered_df = st.session_state.get("discovered_urls_df", pd.DataFrame())
        if not discovered_df.empty:
            st.write("Sample discovered URLs:")
            st.dataframe(safe_df_for_display(discovered_df.head(30)), use_container_width=True)

        if not feature_df.empty:
            st.write("Detected features in data:", sorted(feature_df["Feature"].dropna().unique().tolist()))
            st.write("Feature filter options:", all_feature_options)

        if not raw_df.empty and custom_topics_tuple:
            debug_hits = raw_df[
                raw_df["Feature_List"].apply(
                    lambda x: any(f in x for f in custom_topics_tuple) if isinstance(x, list) else False
                )
            ][["Platform", "Author", "Title", "Video Title", "Content", "Feature_List"]]

            st.write(f"Rows matched by custom features: {len(debug_hits)}")
            if not debug_hits.empty:
                st.dataframe(safe_df_for_display(debug_hits.head(20)), use_container_width=True)

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
        for insight in generate_summary_insights(filtered_df, filtered_feature_df, filtered_pain_df):
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
        st.caption("Custom keywords stay in the filter list even when current extracted data has zero matches.")
        st.markdown("</div>", unsafe_allow_html=True)

    tabs = st.tabs([
        "📈 Trends",
        "🧩 Feature Intelligence",
        "⚠️ Pain Point Radar",
        "🧭 Intent & Platform",
        "🏆 Source Influence",
        "💬 Sentiment Explorer",
        "🗂️ Ground Truth",
        "🌐 Discovery Pool",
        "📰 Raw Articles",
        "🎥 Active Video Vault"
    ])

    with tabs[0]:
        tc1, tc2, tc3, tc4 = st.columns(2), st.columns(2), None, None
        # first row
        with tc1[0]:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Mentions Over Time")
            trend_mentions = filtered_df.groupby("Day").size().reset_index(name="Mentions").sort_values("Day")
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

        with tc1[1]:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Negative Share Over Time")
            trend_sent = filtered_df.groupby(["Day", "Sentiment_Category"]).size().reset_index(name="Count")
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

        c3, c4 = st.columns(2)
        with c3:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Fastest Growing Feature Themes")
            growth_df = compare_recent_vs_previous(filtered_feature_df, "Feature", recent_days=7)
            if not growth_df.empty:
                st.dataframe(safe_df_for_display(growth_df.head(20)), use_container_width=True, height=360)
            else:
                st.info("Not enough dated data to compute growth.")
            st.markdown("</div>", unsafe_allow_html=True)

        with c4:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Fastest Growing Pain Points")
            pain_growth_df = compare_recent_vs_previous(
                filtered_pain_df[filtered_pain_df["Pain_Point"] != "None"],
                "Pain_Point",
                recent_days=7
            )
            if not pain_growth_df.empty:
                st.dataframe(safe_df_for_display(pain_growth_df.head(20)), use_container_width=True, height=360)
            else:
                st.info("Not enough dated pain-point data to compute growth.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        fc1, fc2 = st.columns(2)

        with fc1:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Topic Polarization Matrix")
            topic_breakdown = filtered_feature_df.groupby(["Feature", "Sentiment_Category"]).size().reset_index(name="Count")
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
                st.info("No feature data available for the current selection.")
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

                existing_features = set(feat_summary["Feature"].astype(str).tolist())
                custom_features = [x.strip() for x in st.session_state["custom_feature_tags"] if x.strip()]
                missing_custom = [f for f in custom_features if f in selected_feature and f not in existing_features]
                if missing_custom:
                    zero_rows = pd.DataFrame({
                        "Feature": missing_custom,
                        "Mentions": 0,
                        "Avg_Sentiment": 0.0,
                        "Weighted_Sentiment": 0.0,
                        "Weighted_Reach": 0.0,
                        "Positive": 0,
                        "Neutral": 0,
                        "Negative": 0,
                        "Positive %": 0.0,
                        "Negative %": 0.0
                    })
                    feat_summary = pd.concat([feat_summary, zero_rows], ignore_index=True)

                feat_summary = feat_summary.sort_values(["Mentions", "Weighted_Reach"], ascending=[False, False])

                st.dataframe(
                    safe_df_for_display(feat_summary[[
                        "Feature", "Mentions", "Positive %", "Negative %",
                        "Avg_Sentiment", "Weighted_Sentiment", "Weighted_Reach"
                    ]]),
                    use_container_width=True,
                    height=420
                )
            else:
                st.info("No feature summary available.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        pc1, pc2, pc3 = st.columns([1, 1, 1])

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
                fig_pain = px.bar(pain_counts.head(12), x="Count", y="Pain_Point", orientation="h")
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
                pain_platform = pain_neg.groupby(["Pain_Point", "Platform"]).size().reset_index(name="Count")
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

        with pc3:
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
                st.dataframe(safe_df_for_display(pain_scorecard), use_container_width=True, height=360)
            else:
                st.info("No negative pain-point scorecard available.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[3]:
        ic1, ic2, ic3 = st.columns([1, 1, 1])

        with ic1:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Platform Health Distribution")
            platform_breakdown = filtered_df.groupby(["Platform", "Sentiment_Category"]).size().reset_index(name="Count")
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

        with ic3:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### Intent × Sentiment Table")
            if not filtered_intent_df.empty:
                intent_sent = filtered_intent_df.groupby(["Intent", "Sentiment_Category"]).size().unstack(fill_value=0).reset_index()
                st.dataframe(safe_df_for_display(intent_sent), use_container_width=True, height=360)
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
        st.dataframe(safe_df_for_display(source_table), use_container_width=True, height=450)
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[5]:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 💬 Sentiment Explorer")

        explorer_df = filtered_df.copy()

        explorer_feature = st.selectbox(
            "Feature focus",
            ["All"] + sorted(list(set(all_feature_options))),
            index=0,
            key="explorer_feature"
        )

        explorer_sentiment = st.selectbox(
            "Sentiment focus",
            ["All", "Positive", "Neutral", "Negative"],
            index=0,
            key="explorer_sentiment"
        )

        explorer_platform = st.selectbox(
            "Platform focus",
            ["All"] + sorted(explorer_df["Platform"].dropna().unique().tolist()),
            index=0,
            key="explorer_platform"
        )

        if explorer_feature != "All":
            explorer_df = explorer_df[
                explorer_df["Feature_List"].apply(
                    lambda x: explorer_feature in x if isinstance(x, list) else False
                )
            ]

        if explorer_sentiment != "All":
            explorer_df = explorer_df[explorer_df["Sentiment_Category"] == explorer_sentiment]

        if explorer_platform != "All":
            explorer_df = explorer_df[explorer_df["Platform"] == explorer_platform]

        explorer_df = explorer_df.sort_values(by="Date", ascending=False)

        view_df = explorer_df[[
            "Date", "Platform", "Author", "Title", "Video Title", "Sentiment_Category",
            "Sentiment_Score", "Content", "URL"
        ]].copy()

        st.dataframe(safe_df_for_display(view_df), use_container_width=True, height=520)
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[6]:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 🗂️ Ground Truth Explorer")
        display_df = filtered_df.copy()
        display_df["Feature"] = display_df["Feature_List"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
        display_df["Pain Point"] = display_df["Pain_Point_List"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
        display_df["Intent"] = display_df["Intent_List"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
        display_df["Date_Display"] = display_df["Date_Local"].dt.strftime("%Y-%m-%d %H:%M") if "Date_Local" in display_df.columns else display_df["Date"]

        search_term = st.text_input("Search in content", placeholder="Try words like battery, heating, 10-bit, banding...", key="ground_truth_search")
        if search_term:
            display_df = display_df[display_df["Content"].str.contains(search_term, case=False, na=False)]

        display_df = display_df.sort_values(by="Date", ascending=False)

        st.dataframe(
            safe_df_for_display(display_df[[
                "Date_Display", "Platform", "Author", "Title", "Video Title", "Feature", "Pain Point",
                "Intent", "Sentiment_Category", "Sentiment_Score", "Influence_Score", "Content", "URL"
            ]]),
            use_container_width=True,
            height=520
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[7]:
        discovered_df = st.session_state.get("discovered_urls_df", pd.DataFrame())
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 🌐 Discovery URL Pool")
        if not discovered_df.empty:
            by_source = discovered_df["Discovery_Source"].value_counts().reset_index()
            by_source.columns = ["Discovery_Source", "Count"]
            fig = px.bar(by_source, x="Count", y="Discovery_Source", orientation="h")
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#9CA3AF",
                margin=dict(l=0, r=0, t=20, b=0),
                xaxis=dict(showgrid=True, gridcolor="#1F2937"),
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(safe_df_for_display(discovered_df.head(200)), use_container_width=True, height=420)
        else:
            st.info("No discovery data available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[8]:
        raw_news_df = st.session_state["raw_news_data"].copy()
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 📰 Raw Extracted Articles")
        if not raw_news_df.empty:
            src_df = raw_news_df["Source"].value_counts().reset_index()
            src_df.columns = ["Source", "Count"]
            fig_src = px.bar(src_df.head(20), x="Count", y="Source", orientation="h")
            fig_src.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#9CA3AF",
                margin=dict(l=0, r=0, t=20, b=0),
                xaxis=dict(showgrid=True, gridcolor="#1F2937"),
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_src, use_container_width=True)

            with st.expander(f"View extracted articles ({len(raw_news_df)})", expanded=False):
                for _, row in raw_news_df.head(30).iterrows():
                    st.markdown(f"**{row.get('Title', 'Untitled')}**")
                    st.caption(f"{row.get('Source', 'Unknown')} • {row.get('Discovery_Source', '')}")
                    st.write(str(row.get("Content", ""))[:450] + "...")
                    if row.get("URL"):
                        st.markdown(f"[Open Article]({row['URL']})")
                    st.divider()
        else:
            st.info("No raw article data available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[9]:
        if "sources_db" in st.session_state and not st.session_state["sources_db"].empty:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown(f"### 📂 Active Video Vault ({len(st.session_state['sources_db'])} videos tracked)")
            st.dataframe(safe_df_for_display(st.session_state["sources_db"]), use_container_width=True, height=480)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No tracked YouTube source vault yet. Enable YouTube scraping and run the pipeline.")

else:
    if st.session_state["custom_feature_tags"]:
        st.info("👈 Run the pipeline. Your custom keywords are already stored and will appear in Feature / Topic once data is loaded.")
    else:
        st.info("👈 Configure your target in the sidebar and run the intelligence pipeline.")

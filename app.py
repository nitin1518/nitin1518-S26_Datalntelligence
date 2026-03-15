import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from google.genai import types
from googleapiclient.discovery import build
import pytz, json, os
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & WAR-ROOM THEME ---
st.set_page_config(page_title="S26 Launch: Global Command", layout="wide", initial_sidebar_state="collapsed")
IST = pytz.timezone('Asia/Kolkata')
DATA_VAULT = "s26_market_vault"
analyzer = SentimentIntensityAnalyzer() # Used for the fallback engine

if not os.path.exists(DATA_VAULT):
    os.makedirs(DATA_VAULT)

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    .metric-box { background-color: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; }
    .metric-title { font-size: 0.85rem; color: #8b949e; text-transform: uppercase; font-weight: 600; }
    .metric-value { font-size: 2.2rem; font-weight: bold; color: #ffffff; margin-top: 5px; }
    .metric-delta.positive { color: #3fb950; font-size: 1rem; font-weight: bold; }
    .metric-delta.negative { color: #f85149; font-size: 1rem; font-weight: bold; }
    .critical-alert { border-left: 4px solid #f85149; background-color: rgba(248, 81, 73, 0.1); padding: 12px; margin-bottom: 8px; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SECRETS & AUTH (NEW SDK) ---
try:
    # New SDK initialization
    client = genai.Client(api_key=st.secrets["gemini"]["api_key"])
    yt_service = build('youtube', 'v3', developerKey=st.secrets["youtube"]["api_key"])
except Exception:
    st.error("⚠️ System Offline: Verify API Keys.")
    st.stop()

# --- 3. THE SENSING ENGINE (WITH FAILSAFE) ---
class MarketSensor:
    def fetch_raw_data(self, query, max_results=50):
        raw_comments = []
        try:
            res = yt_service.search().list(q=query, part='id', maxResults=3, type='video').execute()
            for vid in res['items']:
                comm_res = yt_service.commentThreads().list(part='snippet', videoId=vid['id']['videoId'], maxResults=max_results).execute()
                for item in comm_res['items']:
                    raw_comments.append(item['snippet']['topLevelComment']['snippet']['textOriginal'])
        except Exception as e: st.warning(f"YouTube Fetch limited: {e}")
        return raw_comments

    def fallback_processor(self, comments):
        """If AI fails, this keeps the charts alive using rules & VADER."""
        data = []
        for c in comments:
            score = analyzer.polarity_scores(c)['compound']
            cl = c.lower()
            
            # Basic keyword routing
            cat = "Generic"
            if any(w in cl for w in ["camera", "photo", "lens"]): cat = "Camera"
            elif any(w in cl for w in ["battery", "heat", "drain", "garam"]): cat = "Battery"
            elif any(w in cl for w in ["screen", "display", "color"]): cat = "Display"
            elif any(w in cl for w in ["price", "cost", "expensive"]): cat = "Price"
            
            data.append({
                "category": cat,
                "sentiment": score,
                "root_cause": "AI Offline (Rule-based Fallback)",
                "is_urgent": False
            })
        return pd.DataFrame(data)

    def process_with_llm(self, comments):
        prompt = f"""
        Analyze this raw market feedback for the Samsung S26 India launch.
        Return a JSON array of objects. For each comment, extract:
        - "category": [Camera, Battery, Display, Performance, Price, OS/Software, Design, Generic].
        - "sentiment": Float from -1.0 (Defect/Hate) to 1.0 (Love/Perfect).
        - "root_cause": If sentiment < 0, exact technical issue in 2-4 words (e.g., "Shutter lag"). Else, "None".
        - "is_urgent": Boolean (true if major hardware failure, safety issue, or refund demand).
        
        Comments: {json.dumps(comments)}
        """
        try:
            # Using the NEW SDK generation syntax and stable 2.0 Flash model
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            df = pd.DataFrame(json.loads(response.text))
            df['sync_time'] = datetime.now(IST).strftime('%Y-%m-%d %H:%M')
            return df
        except Exception as e:
            st.toast(f"AI Engine Offline. Engaging VADER Fallback. Error: {e}", icon="⚠️")
            df = self.fallback_processor(comments)
            df['sync_time'] = datetime.now(IST).strftime('%Y-%m-%d %H:%M')
            return df

def load_historical_data():
    files = [f for f in os.listdir(DATA_VAULT) if f.endswith('.csv')]
    if not files: return pd.DataFrame()
    return pd.concat([pd.read_csv(os.path.join(DATA_VAULT, f)) for f in files], ignore_index=True)

# --- 4. AUTO-PRESENTATION CYCLE ---
cycle_count = st_autorefresh(interval=30000, key="floor_display_cycle")

st.markdown("<h2 style='text-align: center; color: #ffffff; letter-spacing: 2px;'>🛡️ S26 COMMAND: VOC TIME-MACHINE</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Pipeline Controls")
    if st.button("🔄 TRIGGER LIVE SYNC", use_container_width=True):
        with st.spinner("Ingesting market signals..."):
            sensor = MarketSensor()
            raw = sensor.fetch_raw_data("Samsung S26 Ultra review India")
            new_df = sensor.process_with_llm(raw)
            if not new_df.empty:
                new_df['Raw_Comment'] = raw[:len(new_df)]
                new_df.to_csv(f"{DATA_VAULT}/sync_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.csv", index=False)
                st.success("Network Sync Complete.")

master_df = load_historical_data()

if not master_df.empty:
    master_df['sync_time'] = pd.to_datetime(master_df['sync_time'])
    sync_times = sorted(master_df['sync_time'].unique())
    current_time = sync_times[-1]
    current_df = master_df[master_df['sync_time'] == current_time]
    previous_df = master_df[master_df['sync_time'] == sync_times[-2]] if len(sync_times) > 1 else current_df
    
    # KPIs
    curr_pulse, prev_pulse = current_df['sentiment'].mean(), previous_df['sentiment'].mean()
    curr_urgent, prev_urgent = current_df['is_urgent'].sum(), previous_df['is_urgent'].sum()
    pulse_delta, urgent_delta = curr_pulse - prev_pulse, curr_urgent - prev_urgent

    # ROW 1: KPIs
    c1, c2, c3, c4 = st.columns(4)
    delta_color = "positive" if pulse_delta >= 0 else "negative"
    delta_sign = "+" if pulse_delta >= 0 else ""
    c1.markdown(f"<div class='metric-box'><div class='metric-title'>Market Pulse (-1 to 1)</div><div class='metric-value'>{curr_pulse:.2f} <span class='metric-delta {delta_color}'>{delta_sign}{pulse_delta:.2f}</span></div></div>", unsafe_allow_html=True)
    
    u_color = "positive" if urgent_delta <= 0 else "negative"
    u_sign = "+" if urgent_delta > 0 else ""
    c2.markdown(f"<div class='metric-box'><div class='metric-title'>Urgent Red Flags</div><div class='metric-value' style='color: #ff7b72;'>{curr_urgent} <span class='metric-delta {u_color}'>{u_sign}{urgent_delta}</span></div></div>", unsafe_allow_html=True)
    
    top_issue = current_df[current_df['sentiment'] < 0]['category'].mode()[0] if not current_df[current_df['sentiment'] < 0].empty else 'Stable'
    c3.markdown(f"<div class='metric-box'><div class='metric-title'>Primary Heat Area</div><div class='metric-value'>{top_issue}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-box'><div class='metric-title'>Total Signals Processed</div><div class='metric-value'>{len(master_df)}</div></div>", unsafe_allow_html=True)

    st.write("---")

    # --- ROW 2: AUTO-CYCLING VIEWS ---
    if cycle_count % 2 == 0:
        st.subheader("📡 The Threat Matrix: Aspect vs. Sentiment")
        matrix_df = current_df.groupby('category').agg(Avg_Sentiment=('sentiment', 'mean'), Mentions=('category', 'count')).reset_index()
        fig = px.scatter(matrix_df, x="Avg_Sentiment", y="Mentions", color="category", size="Mentions", text="category", template="plotly_dark", title="<br>← CRISIS ZONE | SAFE ZONE →")
        fig.update_traces(textposition='top center')
        fig.add_vline(x=0, line_width=2, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.subheader("📈 Aspect Sentiment Velocity (Historical Trend)")
        if len(sync_times) > 1:
            trend_df = master_df.groupby([master_df['sync_time'].dt.strftime('%m-%d %H:%M'), 'category'])['sentiment'].mean().reset_index()
            trend_df.rename(columns={'sync_time': 'Time'}, inplace=True)
            fig = px.line(trend_df, x="Time", y="sentiment", color="category", markers=True, template="plotly_dark")
            fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Crisis Threshold")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Awaiting second sync to generate trendlines.")

    # --- ROW 3: TICKER & LOG ---
    st.write("---")
    colA, colB = st.columns([1, 2])
    with colA:
        st.subheader("🚨 Escalation Ticker")
        urgent_items = current_df[current_df['is_urgent'] == True]
        if not urgent_items.empty:
            for _, row in urgent_items.head(3).iterrows():
                st.markdown(f"<div class='critical-alert'><strong>[{row['category'].upper()}]</strong> {row['root_cause']}</div>", unsafe_allow_html=True)
        else: st.success("Clear: No urgent failures.")
    
    with colB:
        st.subheader("🛠️ Auto-Extracted Root Causes")
        debug_df = current_df[current_df['sentiment'] < -0.1][['category', 'root_cause', 'sentiment', 'Raw_Comment']].sort_values(by='sentiment').head(5)
        if not debug_df.empty: st.dataframe(debug_df, use_container_width=True, hide_index=True)
        else: st.info("No significant negative signals.")

else:
    st.info("Data Vault is empty. Open the sidebar and click 'Trigger Live Sync'.")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from googleapiclient.discovery import build
import pytz, json, os
from datetime import datetime

# --- 1. CONFIG & WAR-ROOM THEME ---
st.set_page_config(page_title="S26 Launch: Global Command", layout="wide", initial_sidebar_state="collapsed")
IST = pytz.timezone('Asia/Kolkata')
DATA_VAULT = "s26_market_vault"

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

# --- 2. SECRETS & AUTH ---
try:
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    yt_service = build('youtube', 'v3', developerKey=st.secrets["youtube"]["api_key"])
except Exception:
    st.error("⚠️ System Offline: Verify API Keys.")
    st.stop()

# --- 3. THE SENSING ENGINE ---
class MarketSensor:
    def fetch_raw_data(self, query, max_results=50):
        raw_comments = []
        try:
            res = yt_service.search().list(q=query, part='id', maxResults=3, type='video').execute()
            for vid in res['items']:
                comm_res = yt_service.commentThreads().list(part='snippet', videoId=vid['id']['videoId'], maxResults=max_results).execute()
                for item in comm_res['items']:
                    raw_comments.append(item['snippet']['topLevelComment']['snippet']['textOriginal'])
        except Exception as e: st.warning(f"Fetch limited: {e}")
        return raw_comments

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
            response = model.generate_content(prompt)
            df = pd.DataFrame(json.loads(response.text))
            df['sync_time'] = datetime.now(IST).strftime('%Y-%m-%d %H:%M')
            return df
        except Exception as e:
            st.error(f"AI Parse Error: {e}")
            return pd.DataFrame()

# --- 4. DATA PIPELINE LOGIC ---
def load_historical_data():
    files = [f for f in os.listdir(DATA_VAULT) if f.endswith('.csv')]
    if not files: return pd.DataFrame()
    return pd.concat([pd.read_csv(os.path.join(DATA_VAULT, f)) for f in files], ignore_index=True)

# --- 5. DASHBOARD EXECUTION ---
st.markdown("<h2 style='text-align: center; color: #ffffff; letter-spacing: 2px;'>🛡️ S26 COMMAND: VOC TIME-MACHINE</h2>", unsafe_allow_html=True)

# Sidebar Sync Trigger
with st.sidebar:
    st.header("⚙️ Pipeline Controls")
    if st.button("🔄 TRIGGER LIVE SYNC", use_container_width=True):
        with st.spinner("AI ingesting market signals..."):
            sensor = MarketSensor()
            raw = sensor.fetch_raw_data("Samsung S26 Ultra review India")
            new_df = sensor.process_with_llm(raw)
            if not new_df.empty:
                new_df['Raw_Comment'] = raw[:len(new_df)]
                new_df.to_csv(f"{DATA_VAULT}/sync_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.csv", index=False)
                st.success("Network Sync Complete.")
    
    st.caption("Auto-loads historical vault on refresh.")

# Load Master Data
master_df = load_historical_data()

if not master_df.empty:
    # Ensure datetime format for trend analysis
    master_df['sync_time'] = pd.to_datetime(master_df['sync_time'])
    
    # Identify "Current" vs "Previous" sync for Deltas
    sync_times = sorted(master_df['sync_time'].unique())
    current_time = sync_times[-1]
    current_df = master_df[master_df['sync_time'] == current_time]
    
    previous_df = master_df[master_df['sync_time'] == sync_times[-2]] if len(sync_times) > 1 else current_df
    
    # Calculate KPIs
    curr_pulse = current_df['sentiment'].mean()
    prev_pulse = previous_df['sentiment'].mean()
    pulse_delta = curr_pulse - prev_pulse

    curr_urgent = current_df['is_urgent'].sum()
    prev_urgent = previous_df['is_urgent'].sum()
    urgent_delta = curr_urgent - prev_urgent

    # --- ROW 1: CXO HIGH-LEVEL KPIs WITH DELTAS ---
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

    # --- ROW 2: THE "TIME MACHINE" VISUALS ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📈 Aspect Sentiment Velocity (Historical Trend)")
        if len(sync_times) > 1:
            # Group by sync time and category
            trend_df = master_df.groupby([master_df['sync_time'].dt.strftime('%m-%d %H:%M'), 'category'])['sentiment'].mean().reset_index()
            trend_df.rename(columns={'sync_time': 'Time'}, inplace=True)
            
            fig = px.line(trend_df, x="Time", y="sentiment", color="category", markers=True, template="plotly_dark")
            fig.update_layout(yaxis_title="Sentiment Score", xaxis_title="Sync Window", hovermode="x unified")
            fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Crisis Threshold", annotation_position="bottom right")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Awaiting second sync to generate trendlines. Trigger a new sync later to see velocity.")

    with col2:
        st.subheader("🚨 Live Escalation Ticker")
        urgent_items = current_df[current_df['is_urgent'] == True]
        if not urgent_items.empty:
            for _, row in urgent_items.head(4).iterrows():
                st.markdown(f"""
                <div class='critical-alert'>
                    <strong>[{row['category'].upper()}]</strong> {row['root_cause']}<br>
                    <span style='color: #c9d1d9; font-size: 0.8rem;'>"{row['Raw_Comment'][:100]}..."</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("Clear: No urgent hardware/software failures in latest sync.")

    # --- ROW 3: PRODUCT RCA MATRIX ---
    st.write("---")
    st.subheader("🛠️ Auto-Extracted Root Causes (Current Sync)")
    # Filter for negative sentiment and show the AI's exact 3-word summary
    debug_df = current_df[current_df['sentiment'] < -0.1][['category', 'root_cause', 'sentiment', 'Raw_Comment']].sort_values(by='sentiment')
    
    if not debug_df.empty:
        st.dataframe(debug_df, use_container_width=True, hide_index=True)
    else:
        st.info("No significant negative signals in the current data batch.")

else:
    st.info("Data Vault is empty. Open the sidebar and click 'Trigger Live Sync' to build the initial database.")

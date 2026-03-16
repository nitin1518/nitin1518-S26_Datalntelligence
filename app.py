import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from textblob import TextBlob

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="S26 Ultra Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. DATA GENERATION & NLP ENGINE
# ==========================================
@st.cache_data
def load_data():
    """Generates and processes the simulated omnichannel dataset."""
    np.random.seed(42)
    total_rows = 800
    dates = [datetime(2026, 2, 15) + timedelta(hours=i*0.5) for i in range(total_rows)]
    platforms = np.random.choice(["YouTube", "Reddit", "Indian Media"], total_rows, p=[0.5, 0.3, 0.2])
    launch_date = datetime(2026, 2, 25)

    raw_data = []
    for i in range(total_rows):
        p = platforms[i]
        d = dates[i]
        
        # Simulated Verbatims
        if p == "Indian Media":
            content = np.random.choice([
                "Samsung Galaxy S26 Ultra launches in India with Agentic AI features.",
                "Is the S26 Ultra worth Rs 1,34,999? A deep dive into the specs.",
                "S26 Ultra brings the Flex Magic Pixel display, but keeps Exynos for the Indian market."
            ])
        elif p == "YouTube":
            if d < launch_date:
                content = np.random.choice([
                    "Can't wait for the new privacy display! Looks insane.",
                    "Hope they don't increase the base price this year.",
                    "If it has Exynos in India, I'm skipping it."
                ])
            else:
                content = np.random.choice([
                    "Black screen issue on day 2. Samsung quality control is dropping.",
                    "Battery life is terrible compared to Chinese flagships with 6000mAh.",
                    "Privacy display is actually really useful in the metro.",
                    "Overpriced for a minor upgrade. Sticking with my S24 Ultra."
                ])
        else: # Reddit
            if d < launch_date:
                content = np.random.choice([
                    "Rumors say the S26 Ultra will feature a 5000mAh battery. Disappointing.",
                    "The Flex Magic Pixel tech sounds great for office workers."
                ])
            else:
                content = np.random.choice([
                    "Anyone else experiencing thermal throttling while gaming?",
                    "The price hike without a storage upgrade is corporate greed.",
                    "Privacy screen is a 10/10, but the battery drains too fast."
                ])
                
        raw_data.append({
            "Date": d,
            "Platform": p,
            "Content": content,
            "Engagement": int(np.random.exponential(scale=300 if p == "Reddit" else 1500))
        })

    df = pd.DataFrame(raw_data)
    df['Phase'] = np.where(df['Date'] < launch_date, 'Pre-Launch', 'Post-Launch')
    
    # NLP Processing Functions
    def analyze_sentiment(text): return TextBlob(text).sentiment.polarity
    def extract_feature(text):
        text = text.lower()
        if any(word in text for word in ['screen', 'display', 'pixel', 'black']): return 'Display/Screen'
        if any(word in text for word in ['battery', 'drain', 'mah']): return 'Battery'
        if any(word in text for word in ['price', 'overpriced', 'rs']): return 'Price/Value'
        if any(word in text for word in ['exynos', 'thermal', 'gaming', 'chip']): return 'Performance/Chip'
        return 'General/Other'

    df['Sentiment'] = df['Content'].apply(analyze_sentiment)
    df['Feature'] = df['Content'].apply(extract_feature)
    return df, launch_date

# Load the data
df, launch_date = load_data()

# ==========================================
# 3. SIDEBAR CONTROLS
# ==========================================
st.sidebar.title("Data Filters")
st.sidebar.markdown("Use these controls to isolate specific market signals.")

selected_platform = st.sidebar.multiselect(
    "Select Platforms", 
    options=df['Platform'].unique(), 
    default=df['Platform'].unique()
)

selected_phase = st.sidebar.radio(
    "Select Launch Phase", 
    ["All", "Pre-Launch (Rumor/Hype)", "Post-Launch (Reality)"]
)

# Apply Filters
filtered_df = df[df['Platform'].isin(selected_platform)]
if selected_phase == "Pre-Launch (Rumor/Hype)":
    filtered_df = filtered_df[filtered_df['Phase'] == 'Pre-Launch']
elif selected_phase == "Post-Launch (Reality)":
    filtered_df = filtered_df[filtered_df['Phase'] == 'Post-Launch']

# ==========================================
# 4. MAIN DASHBOARD UI
# ==========================================
st.title("📈 S26 Ultra: Omnichannel Market Intelligence")
st.markdown("Dynamic C-Level Dashboard tracking Pre and Post-Launch Sentiment across the Indian Market.")

# High-Level KPIs
st.markdown("### Executive Summary Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Data Points", f"{len(filtered_df):,}")
col2.metric("Average Sentiment", f"{filtered_df['Sentiment'].mean():.3f}", help="-1.0 (Highly Negative) to 1.0 (Highly Positive)")
col3.metric("Total Engagement", f"{filtered_df['Engagement'].sum():,}", help="Total upvotes, likes, and shares.")

st.markdown("---")

# Visualizations Row
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("1. Sentiment Trajectory")
    st.markdown("Tracks the narrative drift over time.")
    timeline_df = filtered_df.groupby([pd.Grouper(key='Date', freq='1D'), 'Platform'])['Sentiment'].mean().reset_index()
    fig1 = px.line(timeline_df, x='Date', y='Sentiment', color='Platform', markers=True, template="plotly_dark")
    
    # Add Launch Day Marker if viewing 'All' or 'Pre-Launch'
    if selected_phase in ["All", "Pre-Launch (Rumor/Hype)"]:
        fig1.add_vline(x=launch_date.timestamp() * 1000, line_dash="dash", line_color="red", annotation_text="Launch Day")
    
    fig1.add_annotation(text="SAMSUNG GALAXY S26 ULTRA", xref="paper", yref="paper", x=0.5, y=-0.18, showarrow=False, font=dict(color="gray", size=10))
    fig1.update_layout(margin=dict(l=0, r=0, t=30, b=30), height=400)
    st.plotly_chart(fig1, use_container_width=True)

with col_chart2:
    st.subheader("2. Feature Risk Matrix")
    st.markdown("Identifies viral complaints (High Engagement + Negative Sentiment).")
    risk_df = filtered_df.groupby('Feature').agg({'Sentiment':'mean', 'Engagement':'sum'}).reset_index()
    fig2 = px.scatter(risk_df, x='Sentiment', y='Engagement', size='Engagement', color='Feature', 
                      template="plotly_dark", size_max=45)
    fig2.add_vline(x=0, line_dash="dash", line_color="white")
    fig2.add_annotation(text="SAMSUNG GALAXY S26 ULTRA", xref="paper", yref="paper", x=0.5, y=-0.18, showarrow=False, font=dict(color="gray", size=10))
    fig2.update_layout(margin=dict(l=0, r=0, t=30, b=30), height=400)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Strategic Data Tables
st.subheader("📑 Strategic Insights & Verbatim Feedback")
tab1, tab2, tab3 = st.tabs(["Platform Health Matrix", "Feature Performance Matrix", "Top Viral Complaints"])

with tab1:
    st.markdown("**Platform Health (Pre vs Post Launch)**")
    platform_health = df.pivot_table(index='Platform', columns='Phase', values='Sentiment', aggfunc='mean').round(3)
    st.dataframe(platform_health, use_container_width=True)

with tab2:
    st.markdown("**Post-Launch Feature Assessment**")
    feature_perf = df[df['Phase'] == 'Post-Launch'].groupby('Feature').agg({'Sentiment':'mean', 'Engagement':'sum'}).reset_index().sort_values(by='Sentiment').round(3)
    st.dataframe(feature_perf, use_container_width=True)

with tab3:
    st.markdown("**Top Negative Verbatims by Engagement**")
    complaints_df = filtered_df[(filtered_df['Sentiment'] < 0)].sort_values(by='Engagement', ascending=False)
    top_verbatims = complaints_df.drop_duplicates(subset=['Feature']).head(5)
    st.dataframe(top_verbatims[['Platform', 'Feature', 'Engagement', 'Content']], use_container_width=True)

# Footer Branding
st.markdown("<div style='text-align: center; color: gray; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #333;'>SAMSUNG GALAXY S26 ULTRA - CATEGORY LEADERSHIP DASHBOARD</div>", unsafe_allow_html=True)

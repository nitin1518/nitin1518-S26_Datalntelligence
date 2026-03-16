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
    page_title="S26 Ultra Advanced Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. ENTERPRISE DATA ENGINE (5,000 Rows)
# ==========================================
@st.cache_data
def load_enterprise_data():
    np.random.seed(42)
    total_rows = 5000  # Scaled up 6x for deep-dive accuracy
    
    dates = [datetime(2026, 2, 15) + timedelta(minutes=i*4.5) for i in range(total_rows)]
    platforms = np.random.choice(["YouTube", "Reddit", "Indian Media"], total_rows, p=[0.55, 0.35, 0.10])
    launch_date = datetime(2026, 2, 25)

    # Base pain points and praises to simulate high-volume NLP
    negative_prompts = [
        "Black screen issue on day 2. Samsung quality control is dropping.",
        "Battery life is terrible compared to Chinese flagships with 6000mAh.",
        "Overpriced for a minor upgrade. Sticking with my S24 Ultra.",
        "Anyone else experiencing thermal throttling while gaming?",
        "The price hike without a storage upgrade is corporate greed.",
        "Privacy screen is a 10/10, but the battery drains too fast.",
        "Exynos in India again? Hard pass from me."
    ]
    
    positive_prompts = [
        "Can't wait for the new privacy display! Looks insane.",
        "Privacy display is actually really useful in the metro.",
        "The Flex Magic Pixel tech sounds great for office workers.",
        "Samsung Galaxy S26 Ultra launches in India with Agentic AI features.",
        "Camera zoom is still the best in the industry.",
        "UI feels much smoother than last year."
    ]
    
    neutral_prompts = [
        "Is the S26 Ultra worth Rs 1,34,999? A deep dive into the specs.",
        "Just ordered the base model, waiting for delivery.",
        "S26 Ultra brings the Flex Magic Pixel display."
    ]

    raw_data = []
    for i in range(total_rows):
        p = platforms[i]
        d = dates[i]
        
        # Logic to simulate realistic post-launch sentiment crash
        if d < launch_date:
            content = np.random.choice(positive_prompts + neutral_prompts, p=[0.7, 0.3] if p != "Indian Media" else [0.4, 0.6])
        else:
            if p == "Indian Media":
                content = np.random.choice(positive_prompts + neutral_prompts, p=[0.5, 0.5])
            else:
                content = np.random.choice(negative_prompts + positive_prompts + neutral_prompts, p=[0.6, 0.2, 0.2])
                
        raw_data.append({
            "Date": d,
            "Platform": p,
            "Content": content,
            "Engagement": int(np.random.exponential(scale=200 if p == "Reddit" else 1000))
        })

    df = pd.DataFrame(raw_data)
    df['Phase'] = np.where(df['Date'] < launch_date, 'Pre-Launch', 'Post-Launch')
    
    # Accelerated NLP Processing
    def extract_feature_and_sentiment(text):
        text_lower = text.lower()
        score = TextBlob(text).sentiment.polarity
        
        # Determine Feature
        if any(word in text_lower for word in ['screen', 'display', 'pixel', 'black']): feature = 'Display/Screen'
        elif any(word in text_lower for word in ['battery', 'drain', 'mah']): feature = 'Battery/Power'
        elif any(word in text_lower for word in ['price', 'overpriced', 'rs', 'hike']): feature = 'Price/Value'
        elif any(word in text_lower for word in ['exynos', 'thermal', 'gaming', 'chip']): feature = 'Performance/Chip'
        elif any(word in text_lower for word in ['camera', 'zoom']): feature = 'Camera'
        else: feature = 'General/Software'
            
        # Determine Strict Sentiment Category
        if score > 0.05: category = 'Positive'
        elif score < -0.05: category = 'Negative'
        else: category = 'Neutral'
            
        return pd.Series([feature, score, category])

    df[['Feature', 'Sentiment_Score', 'Sentiment_Category']] = df['Content'].apply(extract_feature_and_sentiment)
    return df, launch_date

# Load Data
df, launch_date = load_enterprise_data()

# ==========================================
# 3. ADVANCED SIDEBAR CONTROLS
# ==========================================
st.sidebar.title("Deep-Dive Filters")
st.sidebar.markdown("Isolate the exact market signals you need.")

selected_platform = st.sidebar.multiselect("📡 Platform", df['Platform'].unique(), default=df['Platform'].unique())
selected_phase = st.sidebar.radio("⏱️ Launch Phase", ["All", "Pre-Launch", "Post-Launch"])
selected_feature = st.sidebar.multiselect("📱 Topic/Feature", df['Feature'].unique(), default=df['Feature'].unique())
selected_sentiment = st.sidebar.multiselect("🎭 Sentiment Type", ["Positive", "Neutral", "Negative"], default=["Positive", "Neutral", "Negative"])

# Apply Advanced Filters
filtered_df = df[
    (df['Platform'].isin(selected_platform)) &
    (df['Feature'].isin(selected_feature)) &
    (df['Sentiment_Category'].isin(selected_sentiment))
]

if selected_phase != "All":
    filtered_df = filtered_df[filtered_df['Phase'] == selected_phase]

# ==========================================
# 4. MAIN DASHBOARD UI
# ==========================================
st.title("🧠 S26 Ultra: Advanced Deep-Level Analysis")

# Executive KPIs
total_mentions = len(filtered_df)
if total_mentions > 0:
    pct_negative = (len(filtered_df[filtered_df['Sentiment_Category'] == 'Negative']) / total_mentions) * 100
    pct_positive = (len(filtered_df[filtered_df['Sentiment_Category'] == 'Positive']) / total_mentions) * 100
else:
    pct_negative = pct_positive = 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Data Points", f"{total_mentions:,}")
col2.metric("Total Engagement", f"{filtered_df['Engagement'].sum():,}")
col3.metric("🔥 Negative Share", f"{pct_negative:.1f}%", delta="Critical Detractors", delta_color="inverse")
col4.metric("⭐ Positive Share", f"{pct_positive:.1f}%", delta="Brand Advocates", delta_color="normal")

st.markdown("---")

# ==========================================
# 5. TOPIC POLARIZATION (The "What is Positive/Negative" Chart)
# ==========================================
st.subheader("1. Topic Polarization Matrix")
st.markdown("Reveals exactly what percentage of conversation inside each topic is driving churn vs. advocacy.")

if not filtered_df.empty:
    # Group by Feature and Sentiment Category to get counts
    topic_breakdown = filtered_df.groupby(['Feature', 'Sentiment_Category']).size().reset_index(name='Count')
    
    fig_topic = px.bar(
        topic_breakdown, 
        x='Count', 
        y='Feature', 
        color='Sentiment_Category', 
        orientation='h',
        barmode='stack', # Try '100%' for relative sizing
        color_discrete_map={'Positive': '#2ecc71', 'Neutral': '#95a5a6', 'Negative': '#e74c3c'},
        template="plotly_dark",
        title="Positive vs Negative Ratio per Topic"
    )
    fig_topic.add_annotation(text="SAMSUNG GALAXY S26 ULTRA", xref="paper", yref="paper", x=0.5, y=-0.15, showarrow=False, font=dict(color="gray", size=10))
    st.plotly_chart(fig_topic, use_container_width=True)
else:
    st.warning("No data matches the current filters.")

st.markdown("---")

# ==========================================
# 6. DYNAMIC DRILL-DOWN TABLES
# ==========================================
st.subheader("2. Filtered Verbatim Deep-Dive")
st.markdown("Read the exact comments driving the metrics above. Sort by Engagement to find Viral threats.")

# Display clean dataframe formatted for C-Level reading
display_df = filtered_df[['Date', 'Platform', 'Feature', 'Sentiment_Category', 'Engagement', 'Content']].sort_values(by='Engagement', ascending=False)

# Stylize the dataframe based on sentiment
def color_sentiment(val):
    color = '#e74c3c' if val == 'Negative' else '#2ecc71' if val == 'Positive' else 'gray'
    return f'color: {color}'

st.dataframe(display_df.style.map(color_sentiment, subset=['Sentiment_Category']), use_container_width=True, height=400)

st.markdown("<div style='text-align: center; color: gray; font-size: 12px; margin-top: 40px;'>SAMSUNG GALAXY S26 ULTRA - OMNICHANNEL DEEP DIVE</div>", unsafe_allow_html=True)

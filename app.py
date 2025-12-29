import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# Page Configuration
st.set_page_config(page_title="Brand Reputation Dashboard - 2023", layout="wide")
st.title("Brand Reputation Dashboard - 2023")

@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

def safe_load(path: str, missing_msg: str) -> pd.DataFrame:
    try:
        return load_csv(path)
    except FileNotFoundError:
        st.sidebar.warning(missing_msg)
        return pd.DataFrame()

# Load data
products_df = safe_load("products.csv", "Missing products.csv — please run scrape_all.py")
testimonials_df = safe_load("testimonials.csv", "Missing testimonials.csv — please run scrape_all.py")
reviews_df = safe_load("reviews_scored.csv", "Missing reviews_scored.csv — please run sentiment analysis locally.")

if reviews_df.empty:
    st.error("Data source is empty. Please ensure reviews_scored.csv is generated correctly.")
    st.stop()

# Data Cleaning (Year 2023 only)
if "text" in reviews_df.columns:
    reviews_df["text"] = reviews_df["text"].astype(str).fillna("").str.strip()

if "date" in reviews_df.columns:
    reviews_df = reviews_df[reviews_df["date"].dt.year == 2023].copy()

# Sidebar Navigation
st.sidebar.header("Navigation")
section = st.sidebar.radio("Select section:", ["Products", "Testimonials", "Reviews Analysis"])

# --- PRODUCTS PAGE ---
if section == "Products":
    st.subheader("Inventory Overview")
    if products_df.empty:
        st.info("No product data available.")
    else:
        st.dataframe(products_df.reset_index(drop=True), use_container_width=True)

# --- TESTIMONIALS PAGE ---
elif section == "Testimonials":
    st.subheader("Customer Testimonials")
    if testimonials_df.empty:
        st.info("No testimonials available.")
    else:
        st.dataframe(testimonials_df.reset_index(drop=True), use_container_width=True)

# --- REVIEWS ANALYSIS PAGE ---
else:
    st.subheader("Sentiment Analysis Overview (2023)")

    # Data Mapping
    if "sentiment" not in reviews_df.columns and "sentiment_raw" in reviews_df.columns:
        reviews_df["sentiment"] = reviews_df["sentiment_raw"].map({"POSITIVE": "Positive", "NEGATIVE": "Negative"})

    # Ensure required columns exist
    if "sentiment" not in reviews_df.columns or "confidence" not in reviews_df.columns:
        st.error("Required columns (sentiment/confidence) are missing from the data.")
        st.stop()

    # Month Selector
    month_periods = reviews_df["date"].dropna().dt.to_period("M").sort_values().unique()
    month_labels = [p.strftime("%b %Y") for p in month_periods]

    if not month_labels:
        st.info("No valid dates found in the dataset.")
        st.stop()

    selected_label = st.select_slider("Select Month:", options=month_labels, value=month_labels[0])
    selected_period = pd.Period(selected_label, freq="M")

    filtered = reviews_df[reviews_df["date"].dt.to_period("M") == selected_period].copy()

    # Summary Metrics
    st.markdown(f"### Results for {selected_label}")
    col_metric1, col_metric2, col_metric3 = st.columns(3)
    
    counts = filtered["sentiment"].value_counts().reindex(["Positive", "Negative"]).fillna(0).astype(int)
    avg_conf = filtered["confidence"].mean()

    col_metric1.metric("Total Reviews", len(filtered))
    col_metric2.metric("Positive Sentiment", counts.get("Positive", 0))
    col_metric3.metric("Negative Sentiment", counts.get("Negative", 0))

    st.write(f"**Average Model Confidence Score:** {avg_conf:.2%}")

    # Visualizations
    col_chart, col_cloud = st.columns(2)

    with col_chart:
        st.markdown("#### Sentiment Distribution")
        chart_data = counts.rename_axis("sentiment").reset_index(name="count")
        st.bar_chart(chart_data.set_index("sentiment"), y="count", color=["#2ecc71" if s == "Positive" else "#e74c3c" for s in chart_data["sentiment"]])

    with col_cloud:
        st.markdown("#### Most Common Words")
        all_text = " ".join(filtered["text"].tolist())
        if all_text.strip():
            wordcloud = WordCloud(width=800, height=500, background_color="white", colormap="viridis").generate(all_text)
            fig, ax = plt.subplots()
            ax.imshow(wordcloud, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)
        else:
            st.write("Not enough text for Word Cloud.")

    st.divider()
    st.markdown("### Detailed Monthly Reviews")
    display_cols = [c for c in ["date", "rating", "text", "sentiment", "confidence"] if c in filtered.columns]
    st.dataframe(filtered[display_cols].reset_index(drop=True), use_container_width=True)
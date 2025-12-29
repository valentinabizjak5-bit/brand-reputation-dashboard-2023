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

# Load scored reviews
reviews_df = safe_load(
    "reviews_scored.csv",
    "Missing reviews_scored.csv — please run sentiment analysis locally."
)

if reviews_df.empty:
    st.error("Missing or empty reviews_scored.csv. Please generate the file first.")
    st.stop()

# Clean + only 2023
if "text" in reviews_df.columns:
    reviews_df["text"] = reviews_df["text"].astype(str).fillna("").str.strip()

if "date" in reviews_df.columns:
    reviews_df = reviews_df[reviews_df["date"].dt.year == 2023].copy()

# Sidebar
st.sidebar.header("Navigation")
section = st.sidebar.radio("Select section:", ["Products", "Testimonials", "Reviews"])

# Pages
if section == "Products":
    st.subheader("Products")
    if products_df.empty:
        st.info("No product data available.")
    else:
        st.dataframe(products_df.reset_index(drop=True), use_container_width=True)

elif section == "Testimonials":
    st.subheader("Testimonials")
    if testimonials_df.empty:
        st.info("No testimonials available.")
    else:
        st.dataframe(testimonials_df.reset_index(drop=True), use_container_width=True)

else:
    st.subheader("Reviews (2023)")

    # Mapping sentiment if needed
    if "sentiment" not in reviews_df.columns and "sentiment_raw" in reviews_df.columns:
        reviews_df["sentiment"] = reviews_df["sentiment_raw"].map({"POSITIVE": "Positive", "NEGATIVE": "Negative"})

    if "sentiment" not in reviews_df.columns or "confidence" not in reviews_df.columns:
        st.error("Required columns 'sentiment' and 'confidence' missing.")
        st.stop()

    # Month selector
    month_periods = reviews_df["date"].dropna().dt.to_period("M").sort_values().unique()
    month_labels = [p.strftime("%b %Y") for p in month_periods]

    if not month_labels:
        st.info("No valid dates found in reviews.")
        st.stop()

    selected_label = st.select_slider("Select month", options=month_labels, value=month_labels[0])
    selected_period = pd.Period(selected_label, freq="M")

    filtered = reviews_df[reviews_df["date"].dt.to_period("M") == selected_period].copy()

    st.write(f"Number of reviews in {selected_label}: **{len(filtered)}**")
    if filtered.empty:
        st.info("No data for this month.")
        st.stop()

    # Sentiment summary
    counts = filtered["sentiment"].value_counts().reindex(["Positive", "Negative"]).fillna(0).astype(int)
    avg_conf = filtered.groupby("sentiment")["confidence"].mean().reindex(["Positive", "Negative"])

    st.markdown("### Sentiment Summary")
    c1, c2 = st.columns(2)
    c1.metric("Positive (count)", int(counts.get("Positive", 0)))
    c2.metric("Negative (count)", int(counts.get("Negative", 0)))

    st.write(
        f"**Avg confidence** — Positive: {avg_conf.get('Positive', float('nan')):.3f} | "
        f"Negative: {avg_conf.get('Negative', float('nan')):.3f}"
    )

    chart_df = counts.rename_axis("sentiment").reset_index(name="count")
    st.bar_chart(chart_df.set_index("sentiment"), y="count")

    # Word Cloud (Bonus)
    st.divider()
    st.subheader(f"Most Common Words in {selected_label}")
    
    all_text = " ".join(filtered["text"].tolist())
    if all_text.strip():
        wordcloud = WordCloud(width=800, height=400, background_color="white", colormap="viridis").generate(all_text)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)
    else:
        st.write("Not enough text for Word Cloud.")

    st.divider()
    st.markdown("### Reviews with Sentiment")
    cols = [c for c in ["date", "rating", "text", "sentiment", "confidence"] if c in filtered.columns]
    st.dataframe(filtered[cols].reset_index(drop=True), use_container_width=True)
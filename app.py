import streamlit as st
import pandas as pd

st.set_page_config(page_title="Brand Reputation Dashboard - 2023", layout="wide")
st.title("Brand Reputation Dashboard - 2023")


# -----------------------
# LOADERS
# -----------------------
@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def safe_load(path: str, label: str) -> pd.DataFrame:
    try:
        return load_csv(path)
    except FileNotFoundError:
        st.sidebar.warning(f"Manjka {path} — zaženi scrape_all.py")
        return pd.DataFrame()


products_df = safe_load("products.csv", "Products")
testimonials_df = safe_load("testimonials.csv", "Testimonials")

reviews_df = safe_load("reviews.csv", "Reviews")
if reviews_df.empty:
    st.error("Manjka ali je prazen reviews.csv — zaženi scrape_all.py")
    st.stop()

# reviews: osnovno čiščenje
if "text" in reviews_df.columns:
    reviews_df["text"] = reviews_df["text"].astype(str).str.strip()

# varovalka: samo 2023
if "date" in reviews_df.columns:
    reviews_df = reviews_df[reviews_df["date"].dt.year == 2023].copy()


# -----------------------
# SIDEBAR NAVIGATION
# -----------------------
st.sidebar.header("Navigation")
section = st.sidebar.radio("Select section:", ["Products", "Testimonials", "Reviews"])


# -----------------------
# PAGES
# -----------------------
if section == "Products":
    st.subheader("Products")

    if products_df.empty:
        st.info("Ni podatkov za Products. (Preveri products.csv)")
    else:
        st.dataframe(
            products_df.reset_index(drop=True),
            width="stretch"
        )

elif section == "Testimonials":
    st.subheader("Testimonials")

    if testimonials_df.empty:
        st.info("Ni podatkov za Testimonials. (Preveri testimonials.csv)")
    else:
        st.dataframe(
            testimonials_df.reset_index(drop=True),
            width="stretch"
        )

else:  # Reviews
    st.subheader("Reviews (2023)")

    if reviews_df.empty:
        st.warning("Manjka ali je prazen reviews_scored.csv — zaženi precompute_sentiment.py lokalno.")
        st.stop()

    # varovalka: samo 2023
    reviews_df = reviews_df[reviews_df["date"].dt.year == 2023].copy()

    # seznam mesecev, ki obstajajo
    month_periods = (
        reviews_df["date"].dropna().dt.to_period("M").sort_values().unique()
    )
    month_labels = [p.strftime("%b %Y") for p in month_periods]

    selected_label = st.select_slider("Izberi mesec", options=month_labels, value=month_labels[0])
    selected_period = pd.Period(selected_label, freq="M")

    filtered = reviews_df[reviews_df["date"].dt.to_period("M") == selected_period].copy()

    st.write(f"Število reviewov v {selected_label}: **{len(filtered)}**")
    if filtered.empty:
        st.info("Za ta mesec ni podatkov.")
        st.stop()

    # counts + avg confidence
    counts = filtered["sentiment"].value_counts().reindex(["Positive", "Negative"]).fillna(0).astype(int)
    avg_conf = filtered.groupby("sentiment")["confidence"].mean().reindex(["Positive", "Negative"])

    st.markdown("### Sentiment povzetek")
    c1, c2 = st.columns(2)
    c1.metric("Positive (count)", int(counts.get("Positive", 0)))
    c2.metric("Negative (count)", int(counts.get("Negative", 0)))

    st.write(
        f"**Avg confidence** — Positive: {avg_conf.get('Positive', float('nan')):.3f} | "
        f"Negative: {avg_conf.get('Negative', float('nan')):.3f}"
    )

    chart_df = counts.rename_axis("sentiment").reset_index(name="count")
    st.bar_chart(chart_df.set_index("sentiment"), y="count")

    st.markdown("### Reviews (z sentimentom)")
    cols = [c for c in ["date", "rating", "text", "sentiment", "confidence"] if c in filtered.columns]
    st.dataframe(filtered[cols].reset_index(drop=True), width="stretch")



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


def safe_load(path: str, missing_msg: str) -> pd.DataFrame:
    try:
        return load_csv(path)
    except FileNotFoundError:
        st.sidebar.warning(missing_msg)
        return pd.DataFrame()


products_df = safe_load("products.csv", "Manjka products.csv — zaženi scrape_all.py")
testimonials_df = safe_load("testimonials.csv", "Manjka testimonials.csv — zaženi scrape_all.py")

# ✅ Reviews mora brati reviews_scored.csv (ker ima sentiment + confidence)
reviews_df = safe_load(
    "reviews_scored.csv",
    "Manjka reviews_scored.csv — zaženi precompute_sentiment.py lokalno (po scrape_all.py)."
)

if reviews_df.empty:
    st.error("Manjka ali je prazen reviews_scored.csv — zaženi precompute_sentiment.py lokalno.")
    st.stop()

# reviews: osnovno čiščenje
if "text" in reviews_df.columns:
    reviews_df["text"] = reviews_df["text"].astype(str).fillna("").str.strip()

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
        st.dataframe(products_df.reset_index(drop=True), width="stretch")

elif section == "Testimonials":
    st.subheader("Testimonials")

    if testimonials_df.empty:
        st.info("Ni podatkov za Testimonials. (Preveri testimonials.csv)")
    else:
        st.dataframe(testimonials_df.reset_index(drop=True), width="stretch")

else:  # Reviews
    st.subheader("Reviews (2023)")

    # ✅ varovalka: če ni sentiment/confidence, raje lep error kot KeyError
    required_cols = {"sentiment", "confidence", "date"}
    missing = required_cols - set(reviews_df.columns)
    if missing:
        st.error(
            "V reviews_scored.csv manjkajo stolpci: "
            + ", ".join(sorted(missing))
            + ". Preveri, da si pravilno zagnala precompute_sentiment.py."
        )
        st.stop()

    if reviews_df.empty:
        st.info("Ni reviewov za leto 2023.")
        st.stop()

    # seznam mesecev, ki obstajajo
    month_periods = (
        reviews_df["date"].dropna().dt.to_period("M").sort_values().unique()
    )
    month_labels = [p.strftime("%b %Y") for p in month_periods]

    if not month_labels:
        st.info("Ni veljavnih datumov v reviews_scored.csv.")
        st.stop()

    selected_label = st.select_slider("Izberi mesec", options=month_labels, value=month_labels[0])
    selected_period = pd.Period(selected_label, freq="M")

    filtered = reviews_df[reviews_df["date"].dt.to_period("M") == selected_period].copy()

    st.write(f"Število reviewov v {selected_label}: **{len(filtered)}**")
    if filtered.empty:
        st.info("Za ta mesec ni podatkov.")
        st.stop()

    # counts + avg confidence
    counts = (
        filtered["sentiment"]
        .value_counts()
        .reindex(["Positive", "Negative"])
        .fillna(0)
        .astype(int)
    )

    avg_conf = (
        filtered.groupby("sentiment")["confidence"]
        .mean()
        .reindex(["Positive", "Negative"])
    )

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

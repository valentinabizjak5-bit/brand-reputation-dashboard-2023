import pandas as pd
from transformers import pipeline

INPUT_CSV = "reviews.csv"                 # tvoj 2023 reviews (že filtriran)
OUTPUT_CSV = "reviews_scored.csv"         # nov file z sentimentom

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

def main():
    df = pd.read_csv(INPUT_CSV)
    df["date"] = pd.to_datetime(df.get("date"), errors="coerce")
    df["text"] = df.get("text", "").astype(str).fillna("").str.strip()

    # naloži model
    clf = pipeline("sentiment-analysis", model=MODEL_NAME)

    texts = df["text"].tolist()

    # batch processing (da je hitreje)
    preds = clf(texts, batch_size=16, truncation=True)

    df["sentiment_raw"] = [p["label"] for p in preds]
    df["confidence"] = [float(p["score"]) for p in preds]
    df["sentiment"] = df["sentiment_raw"].map({"POSITIVE": "Positive", "NEGATIVE": "Negative"})

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"Saved {OUTPUT_CSV}: {len(df)} rows")

if __name__ == "__main__":
    main()

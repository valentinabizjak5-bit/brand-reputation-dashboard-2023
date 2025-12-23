import json
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

import requests
import pandas as pd
from bs4 import BeautifulSoup

# =====================================================
# OSNOVNE NASTAVITVE
# =====================================================
BASE_URL = "https://web-scraping.dev"
GRAPHQL_URL = "https://web-scraping.dev/api/graphql"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# =====================================================
# 1) REVIEWS – GraphQL
# =====================================================
REVIEWS_QUERY = """
query Reviews($first: Int!, $after: String) {
  reviews(first: $first, after: $after) {
    edges {
      node {
        id
        rid
        text
        rating
        date
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

def scrape_reviews(first: int = 50, max_pages: int = 50) -> pd.DataFrame:
    session = requests.Session()
    session.headers.update(HEADERS)

    rows: List[Dict[str, Any]] = []
    after: Optional[str] = None
    page = 1

    while page <= max_pages:
        r = session.post(
            GRAPHQL_URL,
            json={"query": REVIEWS_QUERY, "variables": {"first": first, "after": after}},
            timeout=30
        )
        r.raise_for_status()
        payload = r.json()

        block = payload["data"]["reviews"]
        edges = block["edges"]

        print(f"Reviews page {page}: {len(edges)}")

        if not edges:
            break

        for e in edges:
            n = e["node"]
            rows.append({
                "id": n["id"],
                "rid": n["rid"],
                "date": n["date"],
                "rating": n["rating"],
                "text": n["text"],
            })

        if not block["pageInfo"]["hasNextPage"]:
            break

        after = block["pageInfo"]["endCursor"]
        page += 1

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

# =====================================================
# 2) PRODUCTS – HTML
# =====================================================
def get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def scrape_products(max_pages: int = 20) -> pd.DataFrame:
    rows = []
    url = urljoin(BASE_URL, "/products")

    for _ in range(max_pages):
        soup = get_soup(url)

        cards = soup.select(".product, .product-card")

        for c in cards:
            name_el = c.select_one("h2, h3, .title")
            price_el = c.select_one(".price")

            rows.append({
                "name": name_el.get_text(strip=True) if name_el else None,
                "price": price_el.get_text(strip=True) if price_el else None,
            })

        next_a = soup.select_one("a[rel='next'], .pagination a.next")
        if next_a and next_a.get("href"):
            url = urljoin(BASE_URL, next_a["href"])
        else:
            break

    return pd.DataFrame(rows).drop_duplicates()

# =====================================================
# 3) TESTIMONIALS – HTML
# =====================================================
def scrape_testimonials(max_pages: int = 20) -> pd.DataFrame:
    rows = []
    url = urljoin(BASE_URL, "/testimonials")

    for _ in range(max_pages):
        soup = get_soup(url)

        cards = soup.select(".testimonial, blockquote")

        for c in cards:
            rows.append({
                "text": c.get_text(" ", strip=True)
            })

        next_a = soup.select_one("a[rel='next'], .pagination a.next")
        if next_a and next_a.get("href"):
            url = urljoin(BASE_URL, next_a["href"])
        else:
            break

    return pd.DataFrame(rows).drop_duplicates()

# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    print("=== SCRAPING REVIEWS ===")
    reviews = scrape_reviews()
    reviews.to_csv("reviews.csv", index=False, encoding="utf-8")
    print("Saved reviews.csv:", len(reviews))

    print("\n=== SCRAPING PRODUCTS ===")
    products = scrape_products()
    products.to_csv("products.csv", index=False, encoding="utf-8")
    print("Saved products.csv:", len(products))

    print("\n=== SCRAPING TESTIMONIALS ===")
    testimonials = scrape_testimonials()
    testimonials.to_csv("testimonials.csv", index=False, encoding="utf-8")
    print("Saved testimonials.csv:", len(testimonials))

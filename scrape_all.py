from typing import Optional, Dict, Any, List

from urllib.parse import urljoin


import requests

import pandas as pd

from bs4 import BeautifulSoup


# =====================================================

# SETTINGS

# =====================================================

BASE_URL = "https://web-scraping.dev"

GRAPHQL_URL = "https://web-scraping.dev/api/graphql"

HEADERS = {"User-Agent": "Mozilla/5.0"}


YEAR_FILTER = 2023  # ✅ zahtevano leto



# =====================================================

# 1) REVIEWS (GraphQL)

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

        resp = session.post(

            GRAPHQL_URL,

            json={"query": REVIEWS_QUERY, "variables": {"first": first, "after": after}},

            timeout=30,

        )

        resp.raise_for_status()

        payload = resp.json()


        block = payload["data"]["reviews"]

        edges = block.get("edges", [])


        print(f"Reviews page {page}: {len(edges)}")


        if not edges:

            break


        for e in edges:

            n = e["node"]

            rows.append({

                "id": n.get("id"),

                "rid": n.get("rid"),

                "date": n.get("date"),

                "rating": n.get("rating"),

                "text": n.get("text"),

            })


        page_info = block.get("pageInfo", {})

        if not page_info.get("hasNextPage"):

            break


        after = page_info.get("endCursor")

        if not after:

            break


        page += 1


    df = pd.DataFrame(rows)


    # parse date

    df["date"] = pd.to_datetime(df["date"], errors="coerce")


    # ✅ FILTER: only YEAR_FILTER

    df = df[df["date"].dt.year == YEAR_FILTER].copy()


    # add month helper (YYYY-MM)

    df["month"] = df["date"].dt.strftime("%Y-%m")


    # basic cleanup

    df["text"] = df["text"].astype(str).str.strip()


    return df



# =====================================================

# 2) HTML HELPERS

# =====================================================

def get_soup(url: str) -> BeautifulSoup:

    r = requests.get(url, headers=HEADERS, timeout=30)

    r.raise_for_status()

    return BeautifulSoup(r.text, "html.parser")



# =====================================================

# 3) PRODUCTS (HTML)

# =====================================================

def scrape_products(max_pages: int = 20) -> pd.DataFrame:

    rows: List[Dict[str, Any]] = []

    url = urljoin(BASE_URL, "/products")


    for page in range(1, max_pages + 1):

        soup = get_soup(url)


        cards = soup.select(".product, .product-card")

        print(f"Products page {page}: {len(cards)}")


        for c in cards:

            name_el = c.select_one("h1, h2, h3, .title, .product-title")

            price_el = c.select_one(".price, .product-price")


            rows.append({

                "name": name_el.get_text(strip=True) if name_el else None,

                "price": price_el.get_text(strip=True) if price_el else None,

            })


        next_a = soup.select_one("a[rel='next'], .pagination a.next")

        if next_a and next_a.get("href"):

            url = urljoin(BASE_URL, next_a["href"])

        else:

            break


    df = pd.DataFrame(rows).dropna(how="all").drop_duplicates()

    return df



# =====================================================

# 4) TESTIMONIALS (HTML)

# =====================================================

def scrape_testimonials(max_pages: int = 20) -> pd.DataFrame:

    rows: List[Dict[str, Any]] = []

    url = urljoin(BASE_URL, "/testimonials")


    for page in range(1, max_pages + 1):

        soup = get_soup(url)


        cards = soup.select(".testimonial, .testimonial-card, blockquote")

        print(f"Testimonials page {page}: {len(cards)}")


        for c in cards:

            text = c.get_text(" ", strip=True)

            if text:

                rows.append({"text": text})


        next_a = soup.select_one("a[rel='next'], .pagination a.next")

        if next_a and next_a.get("href"):

            url = urljoin(BASE_URL, next_a["href"])

        else:

            break


    df = pd.DataFrame(rows).drop_duplicates()

    return df



# =====================================================

# MAIN

# =====================================================

if __name__ == "__main__":

    print(f"=== SCRAPING REVIEWS (ONLY {YEAR_FILTER}) ===")

    reviews = scrape_reviews(first=50, max_pages=50)

    reviews.to_csv("reviews.csv", index=False, encoding="utf-8")

    print("Saved reviews.csv:", len(reviews))


    print("\n=== SCRAPING PRODUCTS ===")

    products = scrape_products(max_pages=20)

    products.to_csv("products.csv", index=False, encoding="utf-8")

    print("Saved products.csv:", len(products))


    print("\n=== SCRAPING TESTIMONIALS ===")

    testimonials = scrape_testimonials(max_pages=20)

    testimonials.to_csv("testimonials.csv", index=False, encoding="utf-8")

    print("Saved testimonials.csv:", len(testimonials)) 
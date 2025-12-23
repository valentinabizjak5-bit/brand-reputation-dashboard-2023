import requests
import json

GRAPHQL_URL = "https://web-scraping.dev/api/graphql"

QUERY = """
query {
  __schema {
    queryType {
      fields {
        name
        args {
          name
          type {
            kind
            name
            ofType { kind name ofType { kind name } }
          }
        }
        type {
          kind
          name
          ofType { kind name ofType { kind name } }
        }
      }
    }
  }
  __type(name: "Review") {
    name
    fields { name }
  }
}
"""

r = requests.post(
    GRAPHQL_URL,
    json={"query": QUERY},
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30
)

payload = r.json()
print("STATUS:", r.status_code)

if "errors" in payload:
    print("ERRORS:")
    print(json.dumps(payload["errors"], indent=2))
    raise SystemExit(1)

fields = payload["data"]["__schema"]["queryType"]["fields"]

# Najdi reviews field
reviews_field = None
for f in fields:
    if f["name"] == "reviews":
        reviews_field = f
        break

print("\nQuery.reviews ARGUMENTI:")
if reviews_field:
    for a in reviews_field["args"]:
        print("-", a["name"])
else:
    print("NE NAJDEM 'reviews' v queryType fields 😬")

print("\nQuery.reviews RETURN TYPE (skrajšano):")
if reviews_field:
    print(json.dumps(reviews_field["type"], indent=2)[:600])

print("\nReview POLJA:")
review_type = payload["data"]["__type"]
if review_type and review_type.get("fields"):
    for f in review_type["fields"]:
        print("-", f["name"])
else:
    print("NE NAJDEM tipa Review ali nima fields")


import csv
import json
import os
import time
from calendar import monthrange
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")

TOKEN = os.environ.get("TMDB_TOKEN")
if not TOKEN:
    raise SystemExit("TMDB_TOKEN not set. Add it to .env")

BASE = "https://api.themoviedb.org/3"
HORROR = 27
MAX_PAGES = 500  # TMDB caps discover at 500 pages x 20 results
FIRST_YEAR = 1890
IDS_FILE = HERE / "horror_ids.json"
OUT = HERE / "horror_movies_tmdb.csv"
EXISTING = HERE / "horror_movies.csv"
# TidyTuesday dataset columns
FIELDS = [
    "id",
    "original_title",
    "title",
    "original_language",
    "overview",
    "tagline",
    "release_date",
    "poster_path",
    "popularity",
    "vote_count",
    "vote_average",
    "budget",
    "revenue",
    "runtime",
    "status",
    "adult",
    "backdrop_path",
    "genre_names",
    "collection",
    "collection_name",
]

session = requests.Session()
session.headers["Authorization"] = f"Bearer {TOKEN}"


def get(path, params=None, retries=5):
    for attempt in range(retries):
        r = session.get(f"{BASE}{path}", params=params, timeout=30)
        if r.status_code == 404:
            return None
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 2)))
            continue
        if r.status_code >= 500:
            time.sleep(2**attempt)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"Gave up on {path} after {retries} tries")


def discover(start, end, page=1):
    return get(
        "/discover/movie",
        {
            "with_genres": HORROR,
            "include_adult": "false",
            "primary_release_date.gte": start,
            "primary_release_date.lte": end,
            "sort_by": "primary_release_date.asc",
            "page": page,
        },
    )


def date_ranges(year):
    total = discover(f"{year}-01-01", f"{year}-12-31")["total_results"]
    if total <= MAX_PAGES * 20:
        return [(f"{year}-01-01", f"{year}-12-31")]
    return [
        (f"{year}-{m:02d}-01", f"{year}-{m:02d}-{monthrange(year, m)[1]}")
        for m in range(1, 13)
    ]


def fetch_range(start, end):
    first = discover(start, end)
    ids = [m["id"] for m in first["results"]]
    for page in range(2, min(first["total_pages"], MAX_PAGES) + 1):
        ids += [m["id"] for m in discover(start, end, page)["results"]]
    return ids


def all_horror_ids():
    if IDS_FILE.exists():
        return json.loads(IDS_FILE.read_text())
    ids = set()
    for year in range(FIRST_YEAR, date.today().year + 1):
        for start, end in date_ranges(year):
            ids.update(fetch_range(start, end))
        print(f"{year}: {len(ids)} ids so far")
    ids = sorted(ids)
    IDS_FILE.write_text(json.dumps(ids))
    return ids


def details(movie_id):
    m = get(f"/movie/{movie_id}")
    if m is None:
        return None
    collection = m.get("belongs_to_collection") or {}
    return {
        **m,
        "genre_names": ", ".join(g["name"] for g in m["genres"]),
        "collection": collection.get("id"),
        "collection_name": collection.get("name"),
    }


def ids_in(path):
    if not path.exists():
        return set()
    with path.open(newline="") as f:
        return {int(row["id"]) for row in csv.DictReader(f)}


def main():
    ids = all_horror_ids()
    done = ids_in(OUT) | ids_in(EXISTING)
    todo = [i for i in ids if i not in done]
    print(f"{len(ids)} horror movies, {len(done)} already have, {len(todo)} to go")

    is_new = not OUT.exists()
    with OUT.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if is_new:
            writer.writeheader()
        for n, movie_id in enumerate(todo, 1):
            row = details(movie_id)
            if row:
                writer.writerow(row)
            if n % 500 == 0:
                f.flush()
                print(f"{n}/{len(todo)}")

    print(f"Done. Saved to {OUT.name}")


if __name__ == "__main__":
    main()

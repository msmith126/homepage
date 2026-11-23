import argparse
import csv
import gzip
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
APPEND = "credits,keywords,release_dates"
CAST_LIMIT = 10
CREW_JOBS = {"Director", "Screenplay", "Writer", "Producer", "Original Music Composer"}
BATCH_SIZE = 500
IDS_FILE = HERE / "horror_ids.json"
RAW_DIR = HERE / "raw"
LEGACY = [HERE / "horror_movies.csv", HERE / "horror_movies_tmdb.csv"]

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


def all_horror_ids(refresh=False):
    if IDS_FILE.exists() and not refresh:
        return set(json.loads(IDS_FILE.read_text()))
    ids = set()
    for year in range(FIRST_YEAR, date.today().year + 1):
        for start, end in date_ranges(year):
            ids.update(fetch_range(start, end))
        print(f"{year}: {len(ids)} ids so far")
    IDS_FILE.write_text(json.dumps(sorted(ids)))
    return ids


def details(movie_id):
    m = get(f"/movie/{movie_id}", {"append_to_response": APPEND})
    if m is None:
        return None
    credits = m.get("credits") or {}
    credits["cast"] = credits.get("cast", [])[:CAST_LIMIT]
    credits["crew"] = [c for c in credits.get("crew", []) if c["job"] in CREW_JOBS]
    return m


def saved_ids():
    ids = set()
    for path in RAW_DIR.glob("*.jsonl.gz"):
        with gzip.open(path, "rt") as f:
            ids.update(json.loads(line)["id"] for line in f)
    return ids


def legacy_ids():
    ids = set()
    for path in LEGACY:
        if path.exists():
            with path.open(newline="") as f:
                ids.update(int(row["id"]) for row in csv.DictReader(f))
    return ids


def write_batch(movies):
    RAW_DIR.mkdir(exist_ok=True)
    n = len(list(RAW_DIR.glob("*.jsonl.gz")))
    path = RAW_DIR / f"{n + 1:05d}.jsonl.gz"
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt") as f:
        for m in movies:
            f.write(json.dumps(m) + "\n")
    tmp.rename(path)  # only complete batches ever get the .jsonl.gz name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-ids", action="store_true", help="re-scan TMDB for new horror movies")
    parser.add_argument("--backfill", action="store_true", help="also download movies that are only in the legacy CSVs")
    args = parser.parse_args()

    ids = all_horror_ids(refresh=args.refresh_ids)
    skip = saved_ids()
    if args.backfill:
        ids |= legacy_ids()
    else:
        skip |= legacy_ids()
    todo = sorted(ids - skip)
    print(f"{len(ids)} movies, {len(ids & skip)} skipped, {len(todo)} to download")

    batch = []
    try:
        for n, movie_id in enumerate(todo, 1):
            m = details(movie_id)
            if m:
                batch.append(m)
            if len(batch) >= BATCH_SIZE:
                write_batch(batch)
                batch = []
                print(f"{n}/{len(todo)}")
    finally:
        if batch:
            write_batch(batch)

    print("Done")


if __name__ == "__main__":
    main()

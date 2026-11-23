import gzip
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
RAW_DIR = HERE / "raw"
LEGACY = [HERE / "horror_movies.csv", HERE / "horror_movies_tmdb.csv"]
OUT = HERE / "horror_movies_all.parquet"


COPY = [
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
]


def read_raw():
    for path in sorted(RAW_DIR.glob("*.jsonl.gz")):
        with gzip.open(path, "rt") as f:
            for line in f:
                yield json.loads(line)


def names(items, key="name"):
    return ", ".join(i[key] for i in items or []) or None


def us_rating(m):
    for country in m.get("release_dates", {}).get("results", []):
        if country["iso_3166_1"] == "US":
            for release in country["release_dates"]:
                if release["certification"]:
                    return release["certification"]
    return None


def flatten(m):
    collection = m.get("belongs_to_collection") or {}
    credits = m.get("credits", {})
    return {
        **{k: m.get(k) for k in COPY},
        "genre_names": names(m.get("genres")),
        "collection": collection.get("id"),
        "collection_name": collection.get("name"),
        "imdb_id": m.get("imdb_id") or None,
        "production_countries": names(m.get("production_countries"), "iso_3166_1"),
        "spoken_languages": names(m.get("spoken_languages"), "iso_639_1"),
        "keywords": names(m.get("keywords", {}).get("keywords")),
        "director": names([c for c in credits.get("crew", []) if c["job"] == "Director"]),
        "top_cast": names(credits.get("cast", [])[:5]),
        "us_rating": us_rating(m),
    }


def build():
    api = pd.DataFrame([flatten(m) for m in read_raw()])
    api = api.drop_duplicates("id", keep="last").assign(source="api")

    legacy = pd.concat([pd.read_csv(p) for p in LEGACY if p.exists()], ignore_index=True)
    if not api.empty:
        legacy = legacy[~legacy["id"].isin(api["id"])]
    legacy = legacy.drop_duplicates("id", keep="last").assign(source="legacy")

    df = pd.concat([api, legacy], ignore_index=True)
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df["collection"] = df["collection"].astype("Int64")
    return df


def main():
    df = build()
    df.to_parquet(OUT, index=False, compression="zstd")
    print(df["source"].value_counts().to_string())
    print(f"Saved {len(df)} movies to {OUT.name}")


if __name__ == "__main__":
    main()

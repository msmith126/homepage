import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
SRC = HERE / "horror_movies_all.parquet"
OUT = HERE.parents[1] / "public" / "projects" / "horror_movies" / "movies_per_year.json"


def main():
    df = pd.read_parquet(SRC, columns=["release_date"]).dropna()
    counts = df.groupby(df["release_date"].dt.year).size()
    rows = [{"year": int(year), "count": int(n)} for year, n in counts.items()]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows))
    print(f"Wrote {len(rows)} years to {OUT.relative_to(HERE.parents[1])}")


if __name__ == "__main__":
    main()

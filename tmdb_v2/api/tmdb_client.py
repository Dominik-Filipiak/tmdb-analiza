"""
api/tmdb_client.py
==================
Klient TMDB API v3. Pobiera dane dynamicznie z internetu.
Klucz API ładowany z pliku .env dla bezpieczeństwa.
"""

import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

TMDB_BASE    = "https://api.themoviedb.org/3"
TMDB_IMG     = "https://image.tmdb.org/t/p/w185"
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
MAX_RETRIES  = 3
DELAY        = 0.26          # ~40 req/10 s


class TMDBClient:
    """Klient REST API TMDB. Wszystkie żądania przez _get()."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or TMDB_API_KEY
        if not self.api_key:
            raise ValueError("Brak klucza API! Upewnij się, że plik .env zawiera TMDB_API_KEY.")

        self.genres_mapping: dict[int, str] = {}
        self._session = requests.Session()
        self._load_genres()


    def download_movies(self, rok_od=2010, rok_do=2024, strony=5) -> pd.DataFrame:
        """Pobiera filmy z Discover API i zwraca DataFrame."""
        records: list[dict] = []
        for page_num in range(1, strony + 1):
            data = self._get("/discover/movie", {
                "sort_by":                  "popularity.desc",
                "include_adult":            "false",
                "primary_release_date.gte": f"{rok_od}-01-01",
                "primary_release_date.lte": f"{rok_do}-12-31",
                "vote_count.gte":           "10",
                "page":                     page_num,
            })
            if not data or "results" not in data:
                break
            records.extend(data["results"])
            time.sleep(DELAY)
        return self._to_dataframe(records)

    def poster_url(self, path: str | None) -> str | None:
        """Zwraca pełny URL plakatu lub None."""
        return f"{TMDB_IMG}{path}" if path else None

    def download_posters(self, df: pd.DataFrame) -> dict[int, str | None]:
        """
        Dla każdego wiersza df zwraca {id: url_plakatu}.
        """
        result: dict[int, str | None] = {}
        for _, row in df.iterrows():
            poster_path = row.get("poster_path")
            if poster_path:
                result[row["id"]] = self.poster_url(poster_path)
            else:
                result[row["id"]] = None
        return result


    def _load_genres(self):
        data = self._get("/genre/movie/list", {"language": "en-US"})
        if data and "genres" in data:
            self.genres_mapping = {g["id"]: g["name"] for g in data["genres"]}

    def _get(self, endpoint: str, params: dict) -> dict | None:
        params = {"api_key": self.api_key, "language": "en-US", **params}
        url = TMDB_BASE + endpoint

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._session.get(url, params=params, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError:
                if response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"HTTP {response.status_code}: {url}")
            except requests.exceptions.RequestException as e:
                if attempt == MAX_RETRIES:
                    raise RuntimeError(f"Błąd sieci: {e}") from e
                time.sleep(1)
        return None

    def _to_dataframe(self, records: list[dict]) -> pd.DataFrame:
        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        df["release_year"] = pd.to_numeric(df["release_date"].str[:4], errors="coerce")

        def map_genres(ids):
            return [self.genres_mapping.get(i, "Unknown")
                    for i in (ids if isinstance(ids, list) else [])]

        df["genres"] = df["genre_ids"].apply(map_genres)
        df["genre_primary"] = df["genres"].apply(lambda g: g[0] if g else "Unknown")

        for col in ["vote_average", "vote_count", "popularity"]:
            df[col] = pd.to_numeric(df.get(col), errors="coerce")

        columns_to_keep = ["id", "title", "release_year", "vote_average", "vote_count",
                           "popularity", "genres", "genre_primary",
                           "poster_path", "overview"]

        df = df[[c for c in columns_to_keep if c in df.columns]].copy()
        df.dropna(subset=["title", "release_year"], inplace=True)
        df.drop_duplicates(subset=["id"], inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

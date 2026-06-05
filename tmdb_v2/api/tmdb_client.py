"""
api/tmdb_client.py
==================
Klient TMDB API v3. Pobiera dane dynamicznie z internetu.
Klucz API przekazywany przy każdym żądaniu jako parametr 'api_key'.
"""

import time
import requests
import pandas as pd
import numpy as np

TMDB_BASE    = "https://api.themoviedb.org/3"
TMDB_IMG     = "https://image.tmdb.org/t/p/w185"
TMDB_API_KEY = "7a1a532925f98169fa637dab8286ff08"
MAX_RETRIES  = 3
DELAY        = 0.26          # ~40 req/10 s


class TMDBClient:
    """Klient REST API TMDB. Wszystkie żądania przez _get()."""

    def __init__(self, api_key: str = TMDB_API_KEY):
        self.api_key = api_key
        self.gatunki: dict[int, str] = {}
        self._session = requests.Session()
        self._zaladuj_gatunki()

    # ── publiczne ────────────────────────────────────────────

    def pobierz_filmy(self, rok_od=2010, rok_do=2024, strony=5) -> pd.DataFrame:
        """Pobiera filmy z Discover API i zwraca DataFrame."""
        rekordy: list[dict] = []
        for s in range(1, strony + 1):
            dane = self._get("/discover/movie", {
                "sort_by":                  "popularity.desc",
                "include_adult":            "false",
                "primary_release_date.gte": f"{rok_od}-01-01",
                "primary_release_date.lte": f"{rok_do}-12-31",
                "vote_count.gte":           "10",
                "page":                     s,
            })
            if not dane or "results" not in dane:
                break
            rekordy.extend(dane["results"])
            time.sleep(DELAY)
        return self._do_df(rekordy)

    def poster_url(self, path: str | None) -> str | None:
        """Zwraca pełny URL plakatu lub None."""
        return f"{TMDB_IMG}{path}" if path else None

    def pobierz_plakaty(self, df: pd.DataFrame) -> dict[int, str | None]:
        """
        Dla każdego wiersza df zwraca {id: url_plakatu}.
        Szczegóły pobierane z /movie/{id} dla brakujących poster_path.
        """
        wynik: dict[int, str | None] = {}
        for _, r in df.iterrows():
            pp = r.get("poster_path")
            if pp:
                wynik[r["id"]] = self.poster_url(pp)
            else:
                wynik[r["id"]] = None
        return wynik

    # ── prywatne ─────────────────────────────────────────────

    def _zaladuj_gatunki(self):
        dane = self._get("/genre/movie/list", {"language": "en-US"})
        if dane and "genres" in dane:
            self.gatunki = {g["id"]: g["name"] for g in dane["genres"]}

    def _get(self, endpoint: str, params: dict) -> dict | None:
        params = {"api_key": self.api_key, "language": "en-US", **params}
        url = TMDB_BASE + endpoint
        for proba in range(1, MAX_RETRIES + 1):
            try:
                r = self._session.get(url, params=params, timeout=10)
                r.raise_for_status()
                return r.json()
            except requests.exceptions.HTTPError:
                if r.status_code == 429:
                    time.sleep(2 ** proba)
                    continue
                raise RuntimeError(f"HTTP {r.status_code}: {url}")
            except requests.exceptions.RequestException as e:
                if proba == MAX_RETRIES:
                    raise RuntimeError(f"Błąd sieci: {e}") from e
                time.sleep(1)
        return None

    def _do_df(self, rekordy: list[dict]) -> pd.DataFrame:
        if not rekordy:
            return pd.DataFrame()
        df = pd.DataFrame(rekordy)
        df["release_year"] = pd.to_numeric(
            df["release_date"].str[:4], errors="coerce")

        def mapuj(ids):
            return [self.gatunki.get(i, "Unknown")
                    for i in (ids if isinstance(ids, list) else [])]

        df["genres"]        = df["genre_ids"].apply(mapuj)
        df["genre_primary"] = df["genres"].apply(lambda g: g[0] if g else "Unknown")

        for col in ["vote_average", "vote_count", "popularity"]:
            df[col] = pd.to_numeric(df.get(col), errors="coerce")

        keep = ["id", "title", "release_year", "vote_average", "vote_count",
                "popularity", "genres", "genre_primary",
                "poster_path", "overview"]
        df = df[[c for c in keep if c in df.columns]].copy()
        df.dropna(subset=["title", "release_year"], inplace=True)
        df.drop_duplicates(subset=["id"], inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

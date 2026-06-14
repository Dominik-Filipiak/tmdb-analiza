import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_URL = "https://api.themoviedb.org/3"
REQUEST_DELAY = 0.25


class TMDBClient:
    """Prosty klient TMDB API."""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("TMDB_API_KEY")
        if not self.api_key:
            raise ValueError("Brak TMDB_API_KEY w pliku .env.")

        self.session = requests.Session()
        self.genres = self._load_genres()

    def download_movies(self, year_from, year_to, pages):
        """Pobiera filmy i zwraca je jako DataFrame."""
        movies = []

        for page in range(1, pages + 1):
            data = self._get("/discover/movie", {
                "sort_by": "popularity.desc",
                "include_adult": "false",
                "primary_release_date.gte": f"{year_from}-01-01",
                "primary_release_date.lte": f"{year_to}-12-31",
                "vote_count.gte": "10",
                "page": page,
            })

            results = data.get("results", [])
            if not results:
                break

            movies.extend(results)
            time.sleep(REQUEST_DELAY)

        return self._to_dataframe(movies)

    def _load_genres(self):
        try:
            data = self._get("/genre/movie/list", {})
            return {genre["id"]: genre["name"] for genre in data.get("genres", [])}
        except RuntimeError:
            return {}

    def _get(self, endpoint, params):
        params = {
            "api_key": self.api_key,
            "language": "en-US",
            **params,
        }

        try:
            response = self.session.get(TMDB_API_URL + endpoint, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as error:
            raise RuntimeError("Przekroczono czas oczekiwania na odpowiedź TMDB.") from error
        except requests.exceptions.ConnectionError as error:
            raise RuntimeError("Brak połączenia z internetem lub TMDB API.") from error
        except requests.exceptions.HTTPError as error:
            code = error.response.status_code if error.response is not None else "?"
            raise RuntimeError(f"Błąd TMDB API. Kod HTTP: {code}.") from error
        except requests.exceptions.RequestException as error:
            raise RuntimeError(f"Błąd pobierania danych: {error}") from error

    def _to_dataframe(self, movies):
        if not movies:
            return pd.DataFrame()

        df = pd.DataFrame(movies)

        if "release_date" not in df.columns:
            return pd.DataFrame()

        df["release_year"] = pd.to_numeric(df["release_date"].str[:4], errors="coerce")

        for column in ["vote_average", "vote_count", "popularity"]:
            if column not in df.columns:
                df[column] = 0
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

        if "genre_ids" in df.columns:
            df["genres"] = df["genre_ids"].apply(self._map_genres)
        else:
            df["genres"] = [[] for _ in range(len(df))]

        df["genre_primary"] = df["genres"].apply(lambda genres: genres[0] if genres else "Unknown")

        columns = [
            "id",
            "title",
            "release_year",
            "vote_average",
            "vote_count",
            "popularity",
            "genres",
            "genre_primary",
            "overview",
        ]
        existing_columns = [column for column in columns if column in df.columns]

        df = df[existing_columns].copy()
        df = df.dropna(subset=["title", "release_year"])
        df = df.drop_duplicates(subset=["id"])
        df["release_year"] = df["release_year"].astype(int)
        df = df.reset_index(drop=True)

        return df

    def _map_genres(self, genre_ids):
        if not isinstance(genre_ids, list):
            return []

        return [self.genres.get(genre_id, "Unknown") for genre_id in genre_ids]

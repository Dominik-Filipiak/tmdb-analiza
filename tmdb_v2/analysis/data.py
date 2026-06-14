import numpy as np
import pandas as pd


def process_popular_genres(df):
    stats = df.groupby("genre_primary").agg(
        count=("title", "count"),
        avg_rating=("vote_average", "mean"),
        avg_popularity=("popularity", "mean"),
    ).reset_index()

    stats = stats.sort_values("count", ascending=False)
    stats["share_pct"] = (stats["count"] / stats["count"].sum() * 100).round(1)
    stats["avg_rating"] = stats["avg_rating"].round(2)
    stats["avg_popularity"] = stats["avg_popularity"].round(1)
    return stats


def process_rating_distribution(df):
    ratings = df["vote_average"].dropna()

    stats = pd.DataFrame({
        "Statystyka": ["Liczba filmów", "Średnia", "Mediana", "Min", "Max", "Odch. std"],
        "Wartość": [
            len(ratings),
            round(ratings.mean(), 2),
            round(ratings.median(), 2),
            round(ratings.min(), 2),
            round(ratings.max(), 2),
            round(ratings.std(), 2),
        ],
    })

    return ratings, stats


def process_time_trends(df):
    trends = df.groupby("release_year").agg(
        count=("title", "count"),
        avg_rating=("vote_average", "mean"),
        avg_popularity=("popularity", "mean"),
    ).reset_index()

    trends = trends.sort_values("release_year")
    trends["avg_rating"] = trends["avg_rating"].round(2)
    trends["avg_popularity"] = trends["avg_popularity"].round(1)
    return trends


def process_top_movies(df):
    df = df.copy()
    average_rating = df["vote_average"].mean()
    min_votes = np.percentile(df["vote_count"], 70)

    df["weighted_rating"] = (
        df["vote_count"] / (df["vote_count"] + min_votes) * df["vote_average"]
        + min_votes / (df["vote_count"] + min_votes) * average_rating
    ).round(3)

    columns = ["title", "release_year", "vote_average", "vote_count", "weighted_rating", "genre_primary"]
    top_movies = df.sort_values("weighted_rating", ascending=False).head(20)[columns]
    top_movies = top_movies.reset_index(drop=True)
    top_movies.insert(0, "Miejsce", range(1, len(top_movies) + 1))
    return top_movies


def process_genre_comparison(df):
    top_genres = df["genre_primary"].value_counts().head(10).index
    df_top = df[df["genre_primary"].isin(top_genres)].copy()

    stats = df_top.groupby("genre_primary").agg(
        count=("title", "count"),
        avg_rating=("vote_average", "mean"),
        median_rating=("vote_average", "median"),
        avg_popularity=("popularity", "mean"),
    ).reset_index()

    stats["avg_rating"] = stats["avg_rating"].round(2)
    stats["median_rating"] = stats["median_rating"].round(2)
    stats["avg_popularity"] = stats["avg_popularity"].round(1)
    stats = stats.sort_values("avg_rating", ascending=False)

    return df_top, stats

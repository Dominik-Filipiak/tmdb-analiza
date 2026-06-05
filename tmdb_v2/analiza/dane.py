"""
analiza/dane.py
===============
Moduł odpowiedzialny wyłącznie za przetwarzanie danych i statystykę (Pandas / Numpy).
"""

import numpy as np
import pandas as pd


def process_popular_genres(df: pd.DataFrame) -> pd.DataFrame:
    stats = (df.groupby("genre_primary")
             .agg(count=("title", "count"),
                  avg_rating=("vote_average", "mean"),
                  avg_popularity=("popularity", "mean"))
             .reset_index()
             .sort_values("count", ascending=False))

    stats["share_pct"] = (stats["count"] / stats["count"].sum() * 100).round(1)
    stats["avg_rating"] = stats["avg_rating"].round(2)
    stats["avg_popularity"] = stats["avg_popularity"].round(1)
    return stats


def process_rating_distribution(df: pd.DataFrame) -> tuple:
    ratings = df["vote_average"].dropna().values

    stats_dict = {
        "Liczba filmów": len(ratings),
        "Średnia": round(float(np.mean(ratings)), 3),
        "Mediana": round(float(np.median(ratings)), 3),
        "Odch. std": round(float(np.std(ratings)), 3),
        "Min / Max": f"{np.min(ratings):.1f} / {np.max(ratings):.1f}",
        "Q1 / Q3": f"{np.percentile(ratings, 25):.2f} / {np.percentile(ratings, 75):.2f}",
        "IQR": round(float(np.percentile(ratings, 75) - np.percentile(ratings, 25)), 3),
    }
    stats_df = pd.DataFrame(list(stats_dict.items()), columns=["Statystyka", "Wartość"])

    # KDE (Silverman's rule of thumb)
    kde_x = np.linspace(ratings.min(), ratings.max(), 300)
    h = 1.06 * np.std(ratings) * len(ratings) ** (-1 / 5)
    kde_y = np.mean(np.exp(-0.5 * ((kde_x[:, None] - ratings[None, :]) / h) ** 2) / (h * np.sqrt(2 * np.pi)), axis=1)

    return ratings, kde_x, kde_y, stats_df


def process_time_trends(df: pd.DataFrame) -> pd.DataFrame:
    trends = (df.groupby("release_year")
              .agg(count=("title", "count"),
                   avg_rating=("vote_average", "mean"),
                   median_rating=("vote_average", "median"),
                   avg_popularity=("popularity", "mean"))
              .reset_index()
              .sort_values("release_year"))

    trends["avg_rating"] = trends["avg_rating"].round(2)
    trends["median_rating"] = trends["median_rating"].round(2)
    trends["avg_popularity"] = trends["avg_popularity"].round(1)
    trends["rolling_rating"] = trends["avg_rating"].rolling(3, min_periods=1, center=True).mean().round(2)
    return trends


def process_top_movies(df: pd.DataFrame) -> pd.DataFrame:
    df_copy = df.copy()
    c_val = float(np.mean(df_copy["vote_average"]))
    m_val = float(np.percentile(df_copy["vote_count"], 70))

    df_copy["weighted_rating"] = (
            (df_copy["vote_count"] / (df_copy["vote_count"] + m_val)) * df_copy["vote_average"] +
            (m_val / (df_copy["vote_count"] + m_val)) * c_val
    ).round(3)

    top_movies = (df_copy.nlargest(20, "weighted_rating")
                  [["title", "release_year", "vote_average", "vote_count", "weighted_rating", "genre_primary"]]
                  .reset_index(drop=True))
    top_movies.index += 1
    return top_movies.reset_index().rename(columns={"index": "Miejsce"})


def process_genre_comparison(df: pd.DataFrame) -> tuple:
    top_genres = df["genre_primary"].value_counts().head(10).index.tolist()
    df_top = df[df["genre_primary"].isin(top_genres)].copy()

    def coeff_var(s):
        m = np.mean(s)
        return round(float(np.std(s) / m * 100), 1) if m else 0

    stats = (df_top.groupby("genre_primary")["vote_average"]
             .agg(count="count",
                  mean=lambda x: round(float(np.mean(x)), 2),
                  median=lambda x: round(float(np.median(x)), 2),
                  q1=lambda x: round(float(np.percentile(x, 25)), 2),
                  q3=lambda x: round(float(np.percentile(x, 75)), 2),
                  std_dev=lambda x: round(float(np.std(x)), 3),
                  coeff_variance=coeff_var)
             .reset_index()
             .sort_values("mean", ascending=False))

    x_all = df_top["popularity"].values
    y_all = df_top["vote_average"].values
    mask = np.isfinite(x_all) & np.isfinite(y_all)
    r_val = np.corrcoef(x_all[mask], y_all[mask])[0, 1]
    correlation = round(float(r_val), 3)

    boxplot_data = [df_top[df_top["genre_primary"] == g]["vote_average"].dropna().values for g in top_genres]
    poly_coeff = np.polyfit(x_all[mask], y_all[mask], 1)

    return df_top, stats, top_genres, boxplot_data, correlation, poly_coeff
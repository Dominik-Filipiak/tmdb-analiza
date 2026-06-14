from matplotlib.figure import Figure

BG = "#0d0d0d"
PANEL = "#171717"
TEXT = "#e8e6e1"
ACCENT = "#00c030"
GRID = "#303030"


def new_figure(width=10, height=6):
    return Figure(figsize=(width, height), facecolor=BG)


def style_axis(ax, title):
    ax.set_facecolor(PANEL)
    ax.set_title(title, color=TEXT, fontsize=12, pad=10)
    ax.tick_params(colors=TEXT)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.grid(True, color=GRID, alpha=0.4)
    for spine in ax.spines.values():
        spine.set_color(GRID)


def plot_genre_popularity(stats):
    data = stats.head(10)
    fig = new_figure()
    ax = fig.add_subplot(111)

    ax.barh(data["genre_primary"], data["count"], color=ACCENT)
    ax.invert_yaxis()
    ax.set_xlabel("Liczba filmów")
    style_axis(ax, "Najpopularniejsze gatunki")

    for i, value in enumerate(data["count"]):
        ax.text(value, i, f" {value}", va="center", color=TEXT)

    fig.tight_layout()
    return fig


def plot_rating_distribution(ratings, stats):
    fig = new_figure(width=11, height=5)
    ax = fig.add_subplot(121)
    ax_table = fig.add_subplot(122)

    ax.hist(ratings, bins=20, color=ACCENT, edgecolor=BG)
    ax.axvline(ratings.mean(), color="white", linestyle="--", label=f"Średnia: {ratings.mean():.2f}")
    ax.axvline(ratings.median(), color="orange", linestyle="--", label=f"Mediana: {ratings.median():.2f}")
    ax.set_xlabel("Ocena")
    ax.set_ylabel("Liczba filmów")
    ax.legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT)
    style_axis(ax, "Rozkład ocen")

    ax_table.set_facecolor(PANEL)
    ax_table.axis("off")
    table = ax_table.table(
        cellText=stats.values,
        colLabels=stats.columns,
        cellLoc="left",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.4)

    for cell in table.get_celld().values():
        cell.set_facecolor(PANEL)
        cell.set_edgecolor(GRID)
        cell.set_text_props(color=TEXT)

    fig.tight_layout()
    return fig


def plot_time_trends(trends):
    fig = new_figure()
    ax = fig.add_subplot(111)

    ax.plot(trends["release_year"], trends["avg_rating"], marker="o", label="Średnia ocena", color=ACCENT)
    ax.set_xlabel("Rok")
    ax.set_ylabel("Średnia ocena")
    style_axis(ax, "Średnia ocena filmów w czasie")
    ax.legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT)

    fig.tight_layout()
    return fig


def plot_top_movies(top_movies):
    fig = new_figure(width=11, height=7)
    ax = fig.add_subplot(111)

    titles = top_movies["title"] + " (" + top_movies["release_year"].astype(str) + ")"
    ax.barh(titles, top_movies["weighted_rating"], color=ACCENT)
    ax.invert_yaxis()
    ax.set_xlabel("Ocena ważona")
    style_axis(ax, "Top 20 filmów według oceny ważonej")

    fig.tight_layout()
    return fig


def plot_genre_comparison(df_top, stats):
    fig = new_figure(width=11, height=6)
    ax = fig.add_subplot(111)

    stats = stats.sort_values("avg_rating", ascending=True)
    ax.barh(stats["genre_primary"], stats["avg_rating"], color=ACCENT)
    ax.set_xlabel("Średnia ocena")
    style_axis(ax, "Porównanie średnich ocen gatunków")

    for i, row in enumerate(stats.itertuples()):
        ax.text(row.avg_rating, i, f" {row.avg_rating}", va="center", color=TEXT)

    fig.tight_layout()
    return fig

"""
analiza/wizualizacja.py
=======================
Moduł odpowiedzialny wyłącznie za generowanie wykresów (Matplotlib).
"""

import numpy as np
import matplotlib.patches as mpatches
import matplotlib.cm as cm
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

# ── Palette ───────────────────────────────────────────────────
BG_MAIN = "#0d0d0d"
BG_SEC = "#161616"
ACCENT = "#00c030"
GRAY = "#888888"
TEXT_COLOR = "#e8e6e1"
GRID_COLOR = "#252525"

COLORS = ["#00c030", "#4daaff", "#ff6b6b", "#ffd166", "#a29bfe",
          "#fd79a8", "#55efc4", "#fdcb6e", "#74b9ff", "#e17055"]


def _create_fig(w=13, h=6) -> Figure:
    return Figure(figsize=(w, h), facecolor=BG_MAIN)


def _style_ax(ax, title=""):
    ax.set_facecolor(BG_SEC)
    if title:
        ax.set_title(title, color=ACCENT, fontsize=10, pad=8, fontweight="bold")
    ax.tick_params(colors=GRAY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)
    ax.xaxis.label.set_color(GRAY)
    ax.yaxis.label.set_color(GRAY)


def plot_genre_popularity(top_df) -> Figure:
    fig = _create_fig(14, 6)
    gs = GridSpec(1, 2, figure=fig, width_ratios=[1.6, 1], wspace=0.35)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    colors_subset = COLORS[:len(top_df)]
    bars = ax1.barh(top_df["genre_primary"], top_df["count"], color=colors_subset, edgecolor=BG_MAIN, linewidth=0.5)
    ax1.invert_yaxis()

    for b in bars:
        ax1.text(b.get_width() + 0.3, b.get_y() + b.get_height() / 2, str(int(b.get_width())),
                 va="center", ha="left", color=TEXT_COLOR, fontsize=8)

    ax1.set_xlabel("Liczba filmów")
    _style_ax(ax1, "Liczba filmów wg gatunku (Top 10)")

    ax2.pie(top_df["share_pct"], colors=colors_subset, startangle=140, autopct="%1.0f%%", pctdistance=0.82,
            wedgeprops={"edgecolor": BG_MAIN, "linewidth": 1.5}, textprops={"color": TEXT_COLOR, "fontsize": 7})

    patches = [mpatches.Patch(color=c, label=f"{r['genre_primary']} ({r['share_pct']}%)")
               for c, (_, r) in zip(colors_subset, top_df.iterrows())]
    ax2.legend(handles=patches, loc="center left", bbox_to_anchor=(1, .5), fontsize=6.5, labelcolor=TEXT_COLOR,
               facecolor=BG_SEC, edgecolor=GRID_COLOR)
    _style_ax(ax2, "Udział %")

    fig.suptitle("Popularność gatunków filmowych", color=ACCENT, fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    return fig


def plot_rating_distribution(ratings, kde_x, kde_y, stats_df) -> Figure:
    fig = _create_fig(14, 6)
    gs = GridSpec(1, 2, figure=fig, width_ratios=[1.8, 1], wspace=0.35)
    ax = fig.add_subplot(gs[0])
    ax_table = fig.add_subplot(gs[1])

    n, bins, patches = ax.hist(ratings, bins=30, color=ACCENT, edgecolor=BG_MAIN, linewidth=0.4, alpha=0.7)
    for p, left_edge in zip(patches, bins[:-1]):
        if left_edge < 5:
            p.set_facecolor("#ff6b6b")
        elif left_edge < 7:
            p.set_facecolor("#ffd166")
        else:
            p.set_facecolor(ACCENT)

    scale = n.max() / kde_y.max()
    ax.plot(kde_x, kde_y * scale, color=TEXT_COLOR, lw=1.8, ls="--", label="KDE")
    ax.axvline(float(np.mean(ratings)), color="#ffd166", lw=1.5, label=f"Średnia {np.mean(ratings):.2f}")
    ax.axvline(float(np.median(ratings)), color="#a29bfe", lw=1.5, ls="-.", label=f"Mediana {np.median(ratings):.2f}")

    ax.legend(facecolor=BG_SEC, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=8)
    ax.set_xlabel("Ocena (vote_average)")
    ax.set_ylabel("Liczba filmów")
    _style_ax(ax, "Rozkład ocen filmów")

    ax_table.set_facecolor(BG_SEC)
    ax_table.axis("off")
    ax_table.set_title("Statystyki opisowe", color=ACCENT, fontsize=10, pad=8, fontweight="bold")

    table = ax_table.table(cellText=stats_df.values.tolist(), colLabels=["Statystyka", "Wartość"], cellLoc="left",
                           loc="center", bbox=[0, 0.05, 1, 0.9])
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(GRID_COLOR)
        if row == 0:
            cell.set_facecolor("#1a2e1a")
            cell.set_text_props(color=ACCENT, fontweight="bold")
        else:
            cell.set_facecolor(BG_SEC if row % 2 == 0 else "#111111")
            cell.set_text_props(color=TEXT_COLOR)

    fig.suptitle("Analiza rozkładu ocen", color=ACCENT, fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    return fig


def plot_time_trends(trends) -> Figure:
    years = trends["release_year"].astype(int)
    fig = _create_fig(13, 8)
    gs = GridSpec(2, 1, figure=fig, height_ratios=[1.4, 1], hspace=0.35)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    ax_right = ax1.twinx()

    ax1.bar(years, trends["count"], color="#4daaff", alpha=0.5, width=0.7, label="Liczba filmów")
    ax_right.plot(years, trends["avg_rating"], color=ACCENT, lw=2, marker="o", ms=4, label="Śr. ocena")
    ax_right.plot(years, trends["rolling_rating"], color="#ff6b6b", lw=1.5, ls="--", label="Śr. ruch. 3L")

    _style_ax(ax1, "Liczba premier i średnia ocena wg roku")
    ax_right.set_facecolor(BG_SEC)
    ax_right.tick_params(colors=ACCENT, labelsize=8)
    for s in ax_right.spines.values(): s.set_edgecolor(GRID_COLOR)
    ax1.set_ylabel("Liczba filmów")
    ax1.tick_params(axis="y", colors="#4daaff")
    ax_right.set_ylabel("Śr. ocena")
    ax_right.tick_params(axis="y", colors=ACCENT)

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax_right.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, facecolor=BG_SEC, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=8)

    ax2.plot(years, trends["avg_popularity"], color="#a29bfe", lw=2, marker="s", ms=4)
    ax2.fill_between(years, trends["avg_popularity"], alpha=0.18, color="#a29bfe")
    ax2.set_xlabel("Rok")
    ax2.set_ylabel("Śr. popularność")
    _style_ax(ax2, "Średnia popularność filmów wg roku")

    fig.suptitle("Trendy filmowe w czasie", color=ACCENT, fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_top_movies(top_movies) -> Figure:
    fig = _create_fig(13, 9)
    ax = fig.add_subplot(111)

    norm = cm.colors.Normalize(top_movies["weighted_rating"].min(), top_movies["weighted_rating"].max())
    colors = cm.YlGn(norm(top_movies["weighted_rating"]))

    ax.barh(range(len(top_movies)), top_movies["weighted_rating"], color=colors, edgecolor=BG_MAIN, linewidth=0.4)
    ax.set_yticks(range(len(top_movies)))
    ax.set_yticklabels([f"{r['title']} ({int(r['release_year'])})" for _, r in top_movies.iterrows()], fontsize=8,
                       color=TEXT_COLOR)
    ax.invert_yaxis()

    for i, (_, row) in enumerate(top_movies.iterrows()):
        ax.text(row["weighted_rating"] + 0.005, i, f"{row['weighted_rating']:.2f}  ({int(row['vote_count'])} głosów)",
                va="center", ha="left", color="#ffd166", fontsize=7.5)

    mean_val = float(top_movies["weighted_rating"].mean())
    ax.axvline(mean_val, color="#4daaff", lw=1, ls="--", label=f"Średnia Top 20: {mean_val:.2f}")
    ax.legend(facecolor=BG_SEC, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=8)
    ax.set_xlabel("Ocena ważona (Bayesian avg)")
    _style_ax(ax, "Top 20 filmów wg oceny ważonej")

    sm = cm.ScalarMappable(cmap="YlGn", norm=norm)
    sm.set_array([])
    cb = fig.colorbar(sm, ax=ax, pad=0.01, fraction=0.02)
    cb.set_label("Ocena ważona", color=GRAY, fontsize=8)
    cb.ax.yaxis.set_tick_params(color=GRAY, labelcolor=GRAY)

    fig.suptitle("Ranking filmów – ocena ważona (Bayesian)", color=ACCENT, fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_genre_comparison(df_top, top_genres, boxplot_data, correlation, poly_coeff) -> Figure:
    fig = _create_fig(15, 7)
    gs = GridSpec(1, 2, figure=fig, width_ratios=[1.2, 1], wspace=0.35)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    bp = ax1.boxplot(boxplot_data, patch_artist=True, notch=False, vert=True, widths=0.55,
                     medianprops={"color": "#000", "linewidth": 2}, whiskerprops={"color": GRAY, "linewidth": 1},
                     capprops={"color": GRAY, "linewidth": 1.5},
                     flierprops={"marker": "o", "markersize": 3, "markerfacecolor": "#333", "linestyle": "none"})

    for patch, color in zip(bp["boxes"], COLORS):
        patch.set_facecolor(color)
        patch.set_alpha(0.8)

    ax1.set_xticks(range(1, len(top_genres) + 1))
    ax1.set_xticklabels(top_genres, rotation=30, ha="right", fontsize=8, color=TEXT_COLOR)
    ax1.set_ylabel
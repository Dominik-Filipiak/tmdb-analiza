"""
analiza/analizy.py
==================
Wszystkie analizy statystyczne.

WAŻNE – bezpieczeństwo wątkowe:
    Każda funkcja tworzy figurę przez  Figure(...)  z matplotlib.figure,
    NIE przez plt.subplots() / plt.figure(). To gwarantuje brak konfliktu
    z głównym wątkiem tkinter (RuntimeError: main thread is not in main loop).
"""

import numpy as np
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.cm as cm
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

# ── paleta ───────────────────────────────────────────────────
BG    = "#0d0d0d"
BG2   = "#161616"
AKCJA = "#00c030"
SZARY = "#888888"
TEXT  = "#e8e6e1"
GRID  = "#252525"

KOLORY = ["#00c030","#4daaff","#ff6b6b","#ffd166","#a29bfe",
          "#fd79a8","#55efc4","#fdcb6e","#74b9ff","#e17055"]


def _fig(w=13, h=6) -> Figure:
    """Tworzy ciemną figurę bez używania pyplot."""
    f = Figure(figsize=(w, h), facecolor=BG)
    return f


def _ax_styl(ax, tytul=""):
    ax.set_facecolor(BG2)
    if tytul:
        ax.set_title(tytul, color=AKCJA, fontsize=10, pad=8, fontweight="bold")
    ax.tick_params(colors=SZARY, labelsize=8)
    for s in ax.spines.values():
        s.set_edgecolor(GRID)
    ax.xaxis.label.set_color(SZARY)
    ax.yaxis.label.set_color(SZARY)


# ══════════════════════════════════════════════════════════════
# 1. Popularność gatunków
# ══════════════════════════════════════════════════════════════

def analizuj_popularne_gatunki(df: pd.DataFrame) -> tuple[Figure, pd.DataFrame]:
    """
    Wykres słupkowy + kołowy popularności gatunków.
    Oblicza liczbę filmów, średnią ocenę i udział % per gatunek.
    """
    stat = (df.groupby("genre_primary")
              .agg(liczba=("title","count"),
                   srednia_ocena=("vote_average","mean"),
                   srednia_pop=("popularity","mean"))
              .reset_index()
              .sort_values("liczba", ascending=False))
    stat["udzial"] = (stat["liczba"] / stat["liczba"].sum() * 100).round(1)
    stat["srednia_ocena"] = stat["srednia_ocena"].round(2)
    stat["srednia_pop"]   = stat["srednia_pop"].round(1)
    top = stat.head(10)

    fig = _fig(14, 6)
    gs  = GridSpec(1, 2, figure=fig, width_ratios=[1.6, 1], wspace=0.35)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    kol = KOLORY[:len(top)]
    bars = ax1.barh(top["genre_primary"], top["liczba"],
                    color=kol, edgecolor=BG, linewidth=0.5)
    ax1.invert_yaxis()
    for b in bars:
        ax1.text(b.get_width()+0.3, b.get_y()+b.get_height()/2,
                 str(int(b.get_width())),
                 va="center", ha="left", color=TEXT, fontsize=8)
    ax1.set_xlabel("Liczba filmów")
    _ax_styl(ax1, "Liczba filmów wg gatunku (Top 10)")

    ax2.pie(top["udzial"], colors=kol, startangle=140,
            autopct="%1.0f%%", pctdistance=0.82,
            wedgeprops={"edgecolor": BG, "linewidth": 1.5},
            textprops={"color": TEXT, "fontsize": 7})
    patche = [mpatches.Patch(color=c, label=f"{r['genre_primary']} ({r['udzial']}%)")
              for c, (_, r) in zip(kol, top.iterrows())]
    ax2.legend(handles=patche, loc="center left", bbox_to_anchor=(1,.5),
               fontsize=6.5, labelcolor=TEXT,
               facecolor=BG2, edgecolor=GRID)
    _ax_styl(ax2, "Udział %")

    fig.suptitle("Popularność gatunków filmowych",
                 color=AKCJA, fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    return fig, stat


# ══════════════════════════════════════════════════════════════
# 2. Rozkład ocen
# ══════════════════════════════════════════════════════════════

def analizuj_rozklad_ocen(df: pd.DataFrame) -> tuple[Figure, pd.DataFrame]:
    """
    Histogram ocen z krzywą KDE (bandwidth Silvermana) i statystykami.
    """
    oceny = df["vote_average"].dropna().values

    stats = {
        "Liczba filmów":    len(oceny),
        "Średnia":          round(float(np.mean(oceny)), 3),
        "Mediana":          round(float(np.median(oceny)), 3),
        "Odch. std":        round(float(np.std(oceny)), 3),
        "Min / Max":        f"{np.min(oceny):.1f} / {np.max(oceny):.1f}",
        "Q1 / Q3":          f"{np.percentile(oceny,25):.2f} / {np.percentile(oceny,75):.2f}",
        "IQR":              round(float(np.percentile(oceny,75)-np.percentile(oceny,25)),3),
    }
    df_stat = pd.DataFrame(list(stats.items()), columns=["Statystyka","Wartość"])

    # KDE
    x_kde = np.linspace(oceny.min(), oceny.max(), 300)
    h = 1.06 * np.std(oceny) * len(oceny)**(-1/5)
    kde = np.mean(np.exp(-0.5*((x_kde[:,None]-oceny[None,:])/h)**2)
                  / (h*np.sqrt(2*np.pi)), axis=1)

    fig = _fig(14, 6)
    gs  = GridSpec(1, 2, figure=fig, width_ratios=[1.8, 1], wspace=0.35)
    ax  = fig.add_subplot(gs[0])
    axt = fig.add_subplot(gs[1])

    n, biny, patches = ax.hist(oceny, bins=30,
                               color=AKCJA, edgecolor=BG,
                               linewidth=0.4, alpha=0.7)
    for p, left in zip(patches, biny[:-1]):
        if left < 5:   p.set_facecolor("#ff6b6b")
        elif left < 7: p.set_facecolor("#ffd166")
        else:          p.set_facecolor(AKCJA)

    skala = n.max() / kde.max()
    ax.plot(x_kde, kde*skala, color=TEXT, lw=1.8, ls="--", label="KDE")
    ax.axvline(float(np.mean(oceny)),   color="#ffd166", lw=1.5,
               label=f"Średnia {np.mean(oceny):.2f}")
    ax.axvline(float(np.median(oceny)), color="#a29bfe", lw=1.5, ls="-.",
               label=f"Mediana {np.median(oceny):.2f}")
    ax.legend(facecolor=BG2, edgecolor=GRID, labelcolor=TEXT, fontsize=8)
    ax.set_xlabel("Ocena (vote_average)")
    ax.set_ylabel("Liczba filmów")
    _ax_styl(ax, "Rozkład ocen filmów")

    axt.set_facecolor(BG2)
    axt.axis("off")
    axt.set_title("Statystyki opisowe", color=AKCJA, fontsize=10,
                  pad=8, fontweight="bold")
    tab = axt.table(cellText=df_stat.values.tolist(),
                    colLabels=["Statystyka","Wartość"],
                    cellLoc="left", loc="center",
                    bbox=[0, 0.05, 1, 0.9])
    tab.auto_set_font_size(False)
    tab.set_fontsize(8)
    for (r,c), cell in tab.get_celld().items():
        cell.set_edgecolor(GRID)
        if r == 0:
            cell.set_facecolor("#1a2e1a"); cell.set_text_props(color=AKCJA, fontweight="bold")
        else:
            cell.set_facecolor(BG2 if r%2==0 else "#111111")
            cell.set_text_props(color=TEXT)

    fig.suptitle("Analiza rozkładu ocen", color=AKCJA,
                 fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    return fig, df_stat


# ══════════════════════════════════════════════════════════════
# 3. Trendy w czasie
# ══════════════════════════════════════════════════════════════

def analizuj_trendy_czasowe(df: pd.DataFrame) -> tuple[Figure, pd.DataFrame]:
    """
    Liczba premier + średnia ocena per rok + ruchoma średnia (rolling 3 lat).
    Panel dolny: średnia popularność per rok.
    """
    trendy = (df.groupby("release_year")
                .agg(liczba=("title","count"),
                     srednia_ocena=("vote_average","mean"),
                     mediana_ocena=("vote_average","median"),
                     srednia_pop=("popularity","mean"))
                .reset_index()
                .sort_values("release_year"))
    trendy["srednia_ocena"] = trendy["srednia_ocena"].round(2)
    trendy["mediana_ocena"] = trendy["mediana_ocena"].round(2)
    trendy["srednia_pop"]   = trendy["srednia_pop"].round(1)
    trendy["rm_ocena"] = (trendy["srednia_ocena"]
                          .rolling(3, min_periods=1, center=True)
                          .mean().round(2))
    lata = trendy["release_year"].astype(int)

    fig = _fig(13, 8)
    gs  = GridSpec(2, 1, figure=fig, height_ratios=[1.4,1], hspace=0.35)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    axr = ax1.twinx()

    ax1.bar(lata, trendy["liczba"], color="#4daaff", alpha=0.5,
            width=0.7, label="Liczba filmów")
    axr.plot(lata, trendy["srednia_ocena"], color=AKCJA,
             lw=2, marker="o", ms=4, label="Śr. ocena")
    axr.plot(lata, trendy["rm_ocena"], color="#ff6b6b",
             lw=1.5, ls="--", label="Śr. ruch. 3L")

    _ax_styl(ax1, "Liczba premier i średnia ocena wg roku")
    axr.set_facecolor(BG2)
    axr.tick_params(colors=AKCJA, labelsize=8)
    for s in axr.spines.values(): s.set_edgecolor(GRID)
    ax1.set_ylabel("Liczba filmów"); ax1.tick_params(axis="y", colors="#4daaff")
    axr.set_ylabel("Śr. ocena");    axr.tick_params(axis="y", colors=AKCJA)

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = axr.get_legend_handles_labels()
    ax1.legend(h1+h2, l1+l2, facecolor=BG2, edgecolor=GRID,
               labelcolor=TEXT, fontsize=8)

    ax2.plot(lata, trendy["srednia_pop"], color="#a29bfe", lw=2,
             marker="s", ms=4)
    ax2.fill_between(lata, trendy["srednia_pop"], alpha=0.18, color="#a29bfe")
    ax2.set_xlabel("Rok"); ax2.set_ylabel("Śr. popularność")
    _ax_styl(ax2, "Średnia popularność filmów wg roku")

    fig.suptitle("Trendy filmowe w czasie", color=AKCJA,
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig, trendy


# ══════════════════════════════════════════════════════════════
# 4. Top filmy – ocena ważona
# ══════════════════════════════════════════════════════════════

def analizuj_top_filmy(df: pd.DataFrame) -> tuple[Figure, pd.DataFrame]:
    """
    Ranking Top 20 wg Bayesian weighted rating (wzór IMDB).
    WR = (v/(v+m))*R + (m/(v+m))*C
    """
    df = df.copy()
    C  = float(np.mean(df["vote_average"]))
    m  = float(np.percentile(df["vote_count"], 70))
    df["ocena_wazona"] = (
        (df["vote_count"]/(df["vote_count"]+m)) * df["vote_average"] +
        (m/(df["vote_count"]+m)) * C
    ).round(3)

    top = (df.nlargest(20, "ocena_wazona")
             [["title","release_year","vote_average","vote_count",
               "ocena_wazona","genre_primary"]]
             .reset_index(drop=True))
    top.index += 1

    fig = _fig(13, 9)
    ax  = fig.add_subplot(111)

    norma  = cm.colors.Normalize(top["ocena_wazona"].min(),
                                  top["ocena_wazona"].max())
    kolory = cm.YlGn(norma(top["ocena_wazona"]))

    bars = ax.barh(range(len(top)), top["ocena_wazona"],
                   color=kolory, edgecolor=BG, linewidth=0.4)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(
        [f"{r['title']} ({int(r['release_year'])})"
         for _, r in top.iterrows()],
        fontsize=8, color=TEXT)
    ax.invert_yaxis()

    for i, (_, w) in enumerate(top.iterrows()):
        ax.text(w["ocena_wazona"]+0.005, i,
                f"{w['ocena_wazona']:.2f}  ({int(w['vote_count'])} głosów)",
                va="center", ha="left", color="#ffd166", fontsize=7.5)

    sr = float(top["ocena_wazona"].mean())
    ax.axvline(sr, color="#4daaff", lw=1, ls="--",
               label=f"Średnia Top 20: {sr:.2f}")
    ax.legend(facecolor=BG2, edgecolor=GRID, labelcolor=TEXT, fontsize=8)
    ax.set_xlabel("Ocena ważona (Bayesian avg)")
    _ax_styl(ax, "Top 20 filmów wg oceny ważonej")

    sm = cm.ScalarMappable(cmap="YlGn", norm=norma)
    sm.set_array([])
    cb = fig.colorbar(sm, ax=ax, pad=0.01, fraction=0.02)
    cb.set_label("Ocena ważona", color=SZARY, fontsize=8)
    cb.ax.yaxis.set_tick_params(color=SZARY, labelcolor=SZARY)

    fig.suptitle("Ranking filmów – ocena ważona (Bayesian)",
                 color=AKCJA, fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig, top.reset_index().rename(columns={"index":"Miejsce"})


# ══════════════════════════════════════════════════════════════
# 5. Porównanie gatunków – boxploty + scatter
# ══════════════════════════════════════════════════════════════

def analizuj_porownanie_gatunkow(df: pd.DataFrame) -> tuple[Figure, pd.DataFrame]:
    """
    Boxploty ocen (vote_average) dla Top 10 gatunków +
    scatter popularność vs ocena z linią trendu (numpy polyfit).
    Korelacja Pearsona obliczona przez numpy.corrcoef.
    """
    top_g  = df["genre_primary"].value_counts().head(10).index.tolist()
    df_top = df[df["genre_primary"].isin(top_g)].copy()

    def wsp_zm(s):
        m = np.mean(s)
        return round(float(np.std(s)/m*100), 1) if m else 0

    stat = (df_top.groupby("genre_primary")["vote_average"]
                  .agg(liczba="count",
                       srednia=lambda x: round(float(np.mean(x)),2),
                       mediana=lambda x: round(float(np.median(x)),2),
                       q1=lambda x: round(float(np.percentile(x,25)),2),
                       q3=lambda x: round(float(np.percentile(x,75)),2),
                       odch_std=lambda x: round(float(np.std(x)),3),
                       wsp_zmiennosci=wsp_zm)
                  .reset_index()
                  .sort_values("srednia", ascending=False))

    x_all = df_top["popularity"].values
    y_all = df_top["vote_average"].values
    maska = np.isfinite(x_all) & np.isfinite(y_all)
    r_val = np.corrcoef(x_all[maska], y_all[maska])[0,1]
    korel = round(float(r_val), 3)

    dane_box = [df_top[df_top["genre_primary"]==g]["vote_average"].dropna().values
                for g in top_g]

    fig = _fig(15, 7)
    gs  = GridSpec(1, 2, figure=fig, width_ratios=[1.2,1], wspace=0.35)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    bp = ax1.boxplot(dane_box, patch_artist=True, notch=False, vert=True,
                     widths=0.55,
                     medianprops={"color":"#000","linewidth":2},
                     whiskerprops={"color":SZARY,"linewidth":1},
                     capprops={"color":SZARY,"linewidth":1.5},
                     flierprops={"marker":"o","markersize":3,
                                 "markerfacecolor":"#333","linestyle":"none"})
    for patch, kol in zip(bp["boxes"], KOLORY):
        patch.set_facecolor(kol); patch.set_alpha(0.8)

    ax1.set_xticks(range(1, len(top_g)+1))
    ax1.set_xticklabels(top_g, rotation=30, ha="right",
                        fontsize=8, color=TEXT)
    ax1.set_ylabel("Ocena (vote_average)")
    _ax_styl(ax1, "Rozkład ocen per gatunek (Top 10)")

    for i, g in enumerate(top_g):
        sub = df_top[df_top["genre_primary"]==g]
        ax2.scatter(sub["popularity"], sub["vote_average"],
                    c=KOLORY[i], s=14, alpha=0.4, label=g)

    wspl  = np.polyfit(x_all[maska], y_all[maska], 1)
    x_lin = np.linspace(x_all[maska].min(), x_all[maska].max(), 200)
    ax2.plot(x_lin, np.polyval(wspl, x_lin),
             color=TEXT, lw=1.2, ls="--",
             label=f"Trend (r={korel})")
    ax2.set_xlabel("Popularność (TMDB)")
    ax2.set_ylabel("Ocena (vote_average)")
    ax2.legend(fontsize=6, facecolor=BG2, edgecolor=GRID,
               labelcolor=TEXT, markerscale=1.5,
               bbox_to_anchor=(1,1), loc="upper left")
    _ax_styl(ax2, f"Popularność vs ocena  (r={korel})")

    fig.suptitle("Porównanie gatunków filmowych",
                 color=AKCJA, fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig, stat

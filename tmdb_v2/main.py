"""
main.py – Analiza Danych Filmowych TMDB  v2.1
==============================================
Projekt zaliczeniowy – Python · requests · pandas · numpy · matplotlib · tkinter
"""

import tkinter as tk
from tkinter import messagebox
import threading
import matplotlib
matplotlib.use("TkAgg")

from api.tmdb_client import TMDBClient
from analiza import dane, wizualizacja
from gui.widgety import RamkaWynikow, PasekStatusu
from gui.panel_boczny import PanelBoczny

# ── Palette ────────────────────────────────────────────────────
BG_MAIN, BG_SEC = "#0d0d0d", "#141414"
TEXT_COLOR, GRAY, FRAME_COL = "#e8e6e1", "#666666", "#2a2a2a"

# ── Wrapper Functions ──────────────────────────────────────────
def run_popular_genres(df):
    stats = dane.process_popular_genres(df)
    return wizualizacja.plot_genre_popularity(stats.head(10)), stats

def run_rating_distribution(df):
    r, kx, ky, stats = dane.process_rating_distribution(df)
    return wizualizacja.plot_rating_distribution(r, kx, ky, stats), stats

def run_time_trends(df):
    trends = dane.process_time_trends(df)
    return wizualizacja.plot_time_trends(trends), trends

def run_top_movies(df):
    top = dane.process_top_movies(df)
    return wizualizacja.plot_top_movies(top), top

def run_genre_comparison(df):
    top_df, stats, tg, bp_data, corr, poly = dane.process_genre_comparison(df)
    return wizualizacja.plot_genre_comparison(top_df, tg, bp_data, corr, poly), stats

# Konfiguracja dostępnych analiz
ANALYSES = {
    "popularne_gatunki":   ("Popularność gatunków", run_popular_genres),
    "rozklad_ocen":        ("Rozkład ocen", run_rating_distribution),
    "trendy_czasowe":      ("Trendy w czasie", run_time_trends),
    "top_filmy":           ("Top filmy · ocena ważona", run_top_movies),
    "porownanie_gatunkow": ("Porównanie gatunków", run_genre_comparison),
}

# ══════════════════════════════════════════════════════════════
# KONTROLER (Controller) – Główna logika aplikacji
# ══════════════════════════════════════════════════════════════

class Aplikacja(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TMDB · Analiza Filmów")
        self.geometry("1300x820"); self.minsize(960, 640); self.configure(bg=BG_MAIN)
        self.api_client = None

        self._build_layout()
        self.status_bar.start_loading("Łączenie z TMDB API")
        threading.Thread(target=self._init_client, daemon=True).start()

    def _build_layout(self):
        # Top Header
        nav = tk.Frame(self, bg=BG_SEC); nav.pack(fill="x")
        tk.Label(nav, text="● TMDB Analiza Filmów", font=("Segoe UI", 13, "bold"), fg=TEXT_COLOR, bg=BG_SEC, pady=11, padx=16).pack(side="left")
        tk.Button(nav, text="✕", font=("Segoe UI", 12), fg=GRAY, bg=BG_SEC, relief="flat", bd=0, cursor="hand2", padx=14, pady=8, command=self.destroy).pack(side="right")
        tk.Frame(self, bg=FRAME_COL, height=1).pack(fill="x")

        # Main Grid
        main_frame = tk.Frame(self, bg=BG_MAIN); main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(2, weight=1); main_frame.grid_rowconfigure(0, weight=1)

        self.results_frame = RamkaWynikow(main_frame, bg=BG_MAIN)
        self.results_frame.grid(row=0, column=2, sticky="nsew")
        tk.Frame(main_frame, bg=FRAME_COL, width=1).grid(row=0, column=1, sticky="ns")

        # Inicjalizacja panelu bocznego przekazując listę analiz z maina
        self.sidebar = PanelBoczny(main_frame, ANALYSES, self.run_analysis, self.results_frame.clear_results)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self.status_bar = PasekStatusu(self); self.status_bar.pack(fill="x", side="bottom")

    def _init_client(self):
        try:
            self.api_client = TMDBClient()
            self.after(0, lambda: self.status_bar.set_status("✔ Połączono z TMDB. Wybierz parametry i uruchom."))
        except Exception as e:
            self.after(0, lambda: self.status_bar.set_status(f"Błąd API: {e}"))

    def run_analysis(self):
        if not self.api_client: return messagebox.showinfo("Czekaj", "Trwa łączenie z TMDB API...")

        try:
            p = self.sidebar.get_params()
        except ValueError:
            return messagebox.showerror("Błąd", "Nieprawidłowe wartości w formularzu.")

        if p["year_from"] > p["year_to"]:
            return messagebox.showerror("Błąd", "Rok 'od' większy od 'do'.")

        self.sidebar.btn_run.config(state="disabled", text="⏳ Pobieranie…")
        self.results_frame.clear_results()
        self.status_bar.start_loading(f"Analiza: {ANALYSES[p['analysis_key']][0]}")

        threading.Thread(target=self._worker_thread, args=(p,), daemon=True).start()

    def _worker_thread(self, p):
        try:
            df = self.api_client.pobierz_filmy(rok_od=p["year_from"], rok_do=p["year_to"], strony=p["pages"])
            if df.empty: return self.after(0, lambda: messagebox.showwarning("Brak", "Brak danych z API."))

            df = df[df["vote_count"] >= p["min_votes"]].copy()
            if df.empty: return self.after(0, lambda: messagebox.showinfo("Brak", "Brak filmów dla podanych filtrów."))

            title, func = ANALYSES[p["analysis_key"]]
            fig, df_stats = func(df)

            df_movies = df.sort_values("vote_average", ascending=False).head(50).reset_index(drop=True) if p["show_movies"] else None
            df_data = df_stats if p["show_table"] else None

            self.after(0, lambda: self._update_ui(fig, title, df_movies, df_data, len(df)))
        except Exception as e:
            self.after(0, lambda: self.status_bar.set_status(f"Błąd: {str(e)}"))
        finally:
            self.after(0, lambda: self.sidebar.btn_run.config(state="normal", text="▶  Uruchom analizę"))

    def _update_ui(self, fig, title, df_movies, df_data, total):
        self.results_frame.display_results(fig, title=title, df_movies=df_movies, df_data=df_data)
        self.status_bar.set_status(f"✔  {title}  ·  {total} filmów")


if __name__ == "__main__":
    app = Aplikacja()
    app.mainloop()

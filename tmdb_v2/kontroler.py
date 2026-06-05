"""
kontroler.py
============
Kontroler (Controller) zarządzający przepływem danych między Modelem a Widokiem.
"""

import threading
from tkinter import messagebox
import matplotlib

matplotlib.use("TkAgg")

from api.tmdb_client import TMDBClient
from analiza import dane, wizualizacja
from gui.widok_glowny import WidokGlowny


class Kontroler:
    def __init__(self):
        self.api_client = None

        # Definiujemy dostępne analizy i podpinamy je pod funkcje przetwarzające
        self.analyses = {
            "popularne_gatunki": ("Popularność gatunków", self.run_popular_genres),
            "rozklad_ocen": ("Rozkład ocen", self.run_rating_distribution),
            "trendy_czasowe": ("Trendy w czasie", self.run_time_trends),
            "top_filmy": ("Top filmy · ocena ważona", self.run_top_movies),
            "porownanie_gatunkow": ("Porównanie gatunków", self.run_genre_comparison),
        }

        # 1. Inicjalizacja Widoku
        self.view = WidokGlowny(analyses_dict=self.analyses, on_run_callback=self.run_analysis)

        # 2. Inicjalizacja Modelu (API) w tle
        self.view.start_loading("Łączenie z TMDB API")
        threading.Thread(target=self._init_client, daemon=True).start()

    def start(self):
        """Uruchamia pętlę zdarzeń interfejsu graficznego."""
        self.view.mainloop()

    # ── Logika biznesowa i sterowanie ──

    def _init_client(self):
        try:
            self.api_client = TMDBClient()
            self.view.after(0, lambda: self.view.set_status("✔ Połączono z TMDB. Wybierz parametry i uruchom."))
        except Exception as e:
            self.view.after(0, lambda: self.view.set_status(f"Błąd API: {e}"))

    def run_analysis(self):
        """Metoda wywoływana, gdy użytkownik kliknie przycisk 'Uruchom analizę'."""
        if not self.api_client:
            messagebox.showinfo("Czekaj", "Trwa łączenie z TMDB API...")
            return

        try:
            params = self.view.get_params()
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowe wartości w formularzu.")
            return

        if params["year_from"] > params["year_to"]:
            messagebox.showerror("Błąd", "Rok 'od' większy od 'do'.")
            return

        self.view.set_run_button_state("disabled", "⏳ Pobieranie…")
        self.view.clear_results()

        title = self.analyses[params["analysis_key"]][0]
        self.view.start_loading(f"Analiza: {title}")

        threading.Thread(target=self._worker_thread, args=(params,), daemon=True).start()

    def _worker_thread(self, params):
        try:
            df = self.api_client.pobierz_filmy(rok_od=params["year_from"], rok_do=params["year_to"],
                                               strony=params["pages"])
            if df.empty:
                self.view.after(0, lambda: messagebox.showwarning("Brak", "Brak danych z API."))
                return

            df = df[df["vote_count"] >= params["min_votes"]].copy()
            if df.empty:
                self.view.after(0, lambda: messagebox.showinfo("Brak", "Brak filmów dla podanych filtrów."))
                return

            title, func = self.analyses[params["analysis_key"]]
            fig, df_stats = func(df)

            df_movies = df.sort_values("vote_average", ascending=False).head(50).reset_index(drop=True) if params[
                "show_movies"] else None
            df_data = df_stats if params["show_table"] else None

            self.view.after(0, lambda: self._update_ui(fig, title, df_movies, df_data, len(df)))
        except Exception as e:
            self.view.after(0, lambda: self.view.set_status(f"Błąd: {str(e)}"))
        finally:
            self.view.after(0, lambda: self.view.set_run_button_state("normal", "▶  Uruchom analizę"))

    def _update_ui(self, fig, title, df_movies, df_data, total_count):
        self.view.display_results(fig, title, df_movies, df_data)
        self.view.set_status(f"✔  {title}  ·  {total_count} filmów")

    def run_popular_genres(self, df):
        stats = dane.process_popular_genres(df)
        return wizualizacja.plot_genre_popularity(stats.head(10)), stats

    def run_rating_distribution(self, df):
        r, kx, ky, stats = dane.process_rating_distribution(df)
        return wizualizacja.plot_rating_distribution(r, kx, ky, stats), stats

    def run_time_trends(self, df):
        trends = dane.process_time_trends(df)
        return wizualizacja.plot_time_trends(trends), trends

    def run_top_movies(self, df):
        top = dane.process_top_movies(df)
        return wizualizacja.plot_top_movies(top), top

    def run_genre_comparison(self, df):
        top_df, stats, tg, bp_data, corr, poly = dane.process_genre_comparison(df)
        return wizualizacja.plot_genre_comparison(top_df, tg, bp_data, corr, poly), stats
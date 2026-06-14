import threading
import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from api.tmdb_client import TMDBClient
from analysis import data, visualization


ANALYSES = {
    "popularne_gatunki": "Popularność gatunków",
    "rozklad_ocen": "Rozkład ocen",
    "trendy_czasowe": "Trendy w czasie",
    "top_filmy": "Top filmy · ocena ważona",
    "porownanie_gatunkow": "Porównanie gatunków",
}

BG = "#0d0d0d"
PANEL = "#171717"
TEXT = "#e8e6e1"
ACCENT = "#00c030"
GRID = "#303030"


class TMDBApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TMDB · Analiza Filmów")
        self.geometry("1200x760")
        self.minsize(950, 600)
        self.configure(bg=BG)

        self.client = None
        self.current_canvas = None

        self.analysis_var = tk.StringVar(value="popularne_gatunki")
        self.show_movies_var = tk.BooleanVar(value=True)
        self.show_table_var = tk.BooleanVar(value=True)

        self._build_ui()
        self._create_client()

    def _build_ui(self):
        self._build_styles()

        title = tk.Label(
            self,
            text="TMDB Analiza Filmów",
            font=("Segoe UI", 16, "bold"),
            bg=BG,
            fg=TEXT,
            pady=12,
        )
        title.pack(fill="x")

        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(main, bg=PANEL, width=260)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content = tk.Frame(main, bg=BG)
        self.content.pack(side="right", fill="both", expand=True)
        self.status_var = tk.StringVar(value="Gotowe.")
        self._build_sidebar()
        self._build_tabs()


        status = tk.Label(
            self,
            textvariable=self.status_var,
            bg="#080808",
            fg="#999999",
            anchor="w",
            padx=10,
            pady=5,
        )
        status.pack(fill="x", side="bottom")

    def _build_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=TEXT, padding=(14, 7))
        style.map("TNotebook.Tab", background=[("selected", BG)], foreground=[("selected", ACCENT)])
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=24)
        style.configure("Treeview.Heading", background="#222222", foreground=ACCENT)

    def _build_sidebar(self):
        self._sidebar_label("ANALIZA")
        for key, label in ANALYSES.items():
            radio = tk.Radiobutton(
                self.sidebar,
                text=label,
                value=key,
                variable=self.analysis_var,
                bg=PANEL,
                fg=TEXT,
                activebackground=PANEL,
                activeforeground=ACCENT,
                selectcolor=BG,
                anchor="w",
            )
            radio.pack(fill="x", padx=14, pady=2)

        self._sidebar_label("PARAMETRY")
        self.year_from_entry = self._entry("Rok od", "2010")
        self.year_to_entry = self._entry("Rok do", "2024")
        self.min_votes_entry = self._entry("Min. głosów", "500")
        self.pages_entry = self._entry("Stron API", "5")

        self._sidebar_label("WYNIKI")
        self._checkbox("Pokaż zakładkę Filmy", self.show_movies_var)
        self._checkbox("Pokaż zakładkę Dane", self.show_table_var)

        self.run_button = tk.Button(
            self.sidebar,
            text="Uruchom analizę",
            command=self.start_analysis,
            bg=ACCENT,
            fg="black",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            pady=9,
        )
        self.run_button.pack(fill="x", padx=14, pady=(18, 6))

        clear_button = tk.Button(
            self.sidebar,
            text="Wyczyść wyniki",
            command=self.clear_results,
            bg="#252525",
            fg=TEXT,
            relief="flat",
            pady=7,
        )
        clear_button.pack(fill="x", padx=14)

    def _build_tabs(self):
        self.tabs = ttk.Notebook(self.content)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.plot_tab = tk.Frame(self.tabs, bg=BG)
        self.movies_tab = tk.Frame(self.tabs, bg=BG)
        self.data_tab = tk.Frame(self.tabs, bg=BG)

        self.tabs.add(self.plot_tab, text="Wykres")
        self.tabs.add(self.movies_tab, text="Filmy")
        self.tabs.add(self.data_tab, text="Dane")

        self.clear_results()

    def _sidebar_label(self, text):
        tk.Label(
            self.sidebar,
            text=text,
            bg=PANEL,
            fg="#888888",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
            padx=14,
            pady=8,
        ).pack(fill="x", pady=(8, 0))

    def _entry(self, label, default):
        tk.Label(self.sidebar, text=label, bg=PANEL, fg="#aaaaaa", anchor="w", padx=14).pack(fill="x")
        entry = tk.Entry(self.sidebar, bg="#242424", fg=TEXT, insertbackground=TEXT, relief="flat")
        entry.insert(0, default)
        entry.pack(fill="x", padx=14, pady=(2, 8))
        return entry

    def _checkbox(self, label, variable):
        tk.Checkbutton(
            self.sidebar,
            text=label,
            variable=variable,
            bg=PANEL,
            fg=TEXT,
            activebackground=PANEL,
            activeforeground=ACCENT,
            selectcolor=BG,
            anchor="w",
        ).pack(fill="x", padx=14, pady=2)

    def _create_client(self):
        try:
            self.client = TMDBClient()
            self.status_var.set("Połączono z TMDB. Wybierz parametry i uruchom analizę.")
        except ValueError as error:
            self.status_var.set(str(error))
            messagebox.showerror("Błąd konfiguracji", str(error))

    def start_analysis(self):
        if self.client is None:
            messagebox.showerror("Błąd", "Nie można uruchomić analizy bez klucza TMDB API.")
            return

        try:
            params = self._read_params()
        except ValueError as error:
            messagebox.showerror("Błąd danych", str(error))
            return

        self.clear_results()
        self.run_button.config(state="disabled", text="Pobieranie...")
        self.status_var.set("Pobieranie danych z TMDB...")

        thread = threading.Thread(target=self._run_analysis, args=(params,), daemon=True)
        thread.start()

    def _read_params(self):
        try:
            year_from = int(self.year_from_entry.get())
            year_to = int(self.year_to_entry.get())
            min_votes = int(self.min_votes_entry.get())
            pages = int(self.pages_entry.get())
        except ValueError as error:
            raise ValueError("Rok, liczba głosów i liczba stron muszą być liczbami całkowitymi.") from error

        if year_from > year_to:
            raise ValueError("Rok od nie może być większy niż rok do.")
        if min_votes < 0:
            raise ValueError("Minimalna liczba głosów nie może być ujemna.")
        if pages < 1 or pages > 20:
            raise ValueError("Liczba stron API musi być od 1 do 20.")

        return {
            "analysis_key": self.analysis_var.get(),
            "year_from": year_from,
            "year_to": year_to,
            "min_votes": min_votes,
            "pages": pages,
            "show_movies": self.show_movies_var.get(),
            "show_table": self.show_table_var.get(),
        }

    def _run_analysis(self, params):
        try:
            df = self.client.download_movies(params["year_from"], params["year_to"], params["pages"])
            if df.empty:
                self.after(0, lambda: self._show_info("Brak danych", "TMDB nie zwróciło filmów dla tych parametrów."))
                return

            df = df[df["vote_count"] >= params["min_votes"]].copy()
            if df.empty:
                self.after(0, lambda: self._show_info("Brak filmów", "Po zastosowaniu filtrów nie ma filmów do analizy."))
                return

            title, figure, table_data = self._make_analysis(params["analysis_key"], df)
            movies_data = self._make_movies_table(df) if params["show_movies"] else None
            table_data = table_data if params["show_table"] else None

            self.after(0, lambda: self._show_results(title, figure, movies_data, table_data, len(df)))
        except RuntimeError as error:
            self.after(0, lambda: messagebox.showerror("Błąd API", str(error)))
        except Exception as error:
            self.after(0, lambda: messagebox.showerror("Błąd", f"Wystąpił nieoczekiwany błąd: {error}"))
        finally:
            self.after(0, self._finish_analysis)

    def _make_analysis(self, analysis_key, df):
        if analysis_key == "popularne_gatunki":
            stats = data.process_popular_genres(df)
            figure = visualization.plot_genre_popularity(stats)
            return ANALYSES[analysis_key], figure, stats

        if analysis_key == "rozklad_ocen":
            ratings, stats = data.process_rating_distribution(df)
            figure = visualization.plot_rating_distribution(ratings, stats)
            return ANALYSES[analysis_key], figure, stats

        if analysis_key == "trendy_czasowe":
            trends = data.process_time_trends(df)
            figure = visualization.plot_time_trends(trends)
            return ANALYSES[analysis_key], figure, trends

        if analysis_key == "top_filmy":
            top = data.process_top_movies(df)
            figure = visualization.plot_top_movies(top)
            return ANALYSES[analysis_key], figure, top

        if analysis_key == "porownanie_gatunkow":
            df_top, stats = data.process_genre_comparison(df)
            figure = visualization.plot_genre_comparison(df_top, stats)
            return ANALYSES[analysis_key], figure, stats

        raise ValueError("Nieznany typ analizy.")

    def _make_movies_table(self, df):
        columns = ["title", "release_year", "vote_average", "vote_count", "popularity", "genre_primary"]
        return df.sort_values("vote_average", ascending=False).head(50)[columns].reset_index(drop=True)

    def _show_results(self, title, figure, movies_data, table_data, count):
        self._show_plot(figure)
        self._show_table(self.movies_tab, movies_data, "Nie wybrano wyświetlania filmów.")
        self._show_table(self.data_tab, table_data, "Nie wybrano wyświetlania tabeli danych.")
        self.tabs.select(self.plot_tab)
        self.status_var.set(f"Gotowe: {title}. Liczba filmów po filtrach: {count}.")

    def _show_plot(self, figure):
        self._clear_frame(self.plot_tab)
        self.current_canvas = FigureCanvasTkAgg(figure, master=self.plot_tab)
        self.current_canvas.draw()
        self.current_canvas.get_tk_widget().pack(fill="both", expand=True)
        NavigationToolbar2Tk(self.current_canvas, self.plot_tab).update()

    def _show_table(self, parent, df, empty_text):
        self._clear_frame(parent)

        if df is None or df.empty:
            self._placeholder(parent, empty_text)
            return

        df = df.copy()
        for column in df.columns:
            df[column] = df[column].apply(lambda value: ", ".join(value) if isinstance(value, list) else value)

        container = tk.Frame(parent, bg=BG)
        container.pack(fill="both", expand=True)

        scroll_y = ttk.Scrollbar(container, orient="vertical")
        scroll_x = ttk.Scrollbar(container, orient="horizontal")
        tree = ttk.Treeview(
            container,
            columns=list(df.columns),
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
        )

        scroll_y.config(command=tree.yview)
        scroll_x.config(command=tree.xview)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        for column in df.columns:
            tree.heading(column, text=column)
            tree.column(column, width=max(100, len(column) * 12), anchor="center")

        for row in df.itertuples(index=False):
            tree.insert("", "end", values=list(row))

    def clear_results(self):
        self._clear_frame(self.plot_tab)
        self._clear_frame(self.movies_tab)
        self._clear_frame(self.data_tab)
        self._placeholder(self.plot_tab, "Tu pojawi się wykres.")
        self._placeholder(self.movies_tab, "Tu pojawi się lista filmów.")
        self._placeholder(self.data_tab, "Tu pojawi się tabela danych.")
        self.status_var.set("Gotowe.")

    def _placeholder(self, parent, text):
        tk.Label(parent, text=text, bg=BG, fg="#666666", font=("Segoe UI", 13)).place(relx=0.5, rely=0.5, anchor="center")

    def _clear_frame(self, parent):
        for widget in parent.winfo_children():
            widget.destroy()

    def _show_info(self, title, message):
        messagebox.showinfo(title, message)
        self.status_var.set(message)

    def _finish_analysis(self):
        self.run_button.config(state="normal", text="Uruchom analizę")


if __name__ == "__main__":
    app = TMDBApp()
    app.mainloop()

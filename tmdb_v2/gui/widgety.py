"""
gui/widgety.py  –  TMDB Analiza v2.1
=====================================
Widżety GUI: ciemny motyw inspirowany Letterboxd, akcent #00c030.
"""

import tkinter as tk
from tkinter import ttk
import io
import urllib.request
import webbrowser

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

try:
    from PIL import Image, ImageTk

    PIL_OK = True
except ImportError:
    PIL_OK = False

# ── Palette ────────────────────────────────────────────────────
BG_MAIN = "#0d0d0d"
BG_SEC = "#141414"
BG_TERT = "#1c1c1c"
BG_QUART = "#242424"
ACCENT = "#00c030"
ACCENT_HOV = "#00a828"
GRAY = "#666666"
GRAY_LIGHT = "#999999"
TEXT_COLOR = "#e8e6e1"
FRAME_COL = "#2a2a2a"
RED_ALERT = "#ff4444"


# ══════════════════════════════════════════════════════════════
# RamkaWynikow (Results Frame)
# ══════════════════════════════════════════════════════════════

class RamkaWynikow(tk.Frame):
    """Notebook (Chart / Movies / Data) with a title bar and close button."""

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", BG_MAIN)
        super().__init__(parent, **kwargs)
        self._canvas = None
        self._analysis_text = tk.StringVar(value="")
        self._build_ui()

    # ── UI Building ─────────────────────────────────────────────

    def _build_ui(self):
        # Top bar: active analysis name + close button
        self._top_bar = tk.Frame(self, bg=BG_TERT, height=34)
        self._top_bar.pack(fill="x")
        self._top_bar.pack_propagate(False)

        self._lbl_analysis = tk.Label(
            self._top_bar, textvariable=self._analysis_text,
            font=("Segoe UI", 9), fg=GRAY_LIGHT, bg=BG_TERT, anchor="w", padx=14)
        self._lbl_analysis.pack(side="left", fill="y")

        # Close button (clear results)
        self._btn_close = tk.Button(
            self._top_bar, text="✕",
            font=("Segoe UI", 11), fg=GRAY, bg=BG_TERT,
            relief="flat", bd=0, cursor="hand2",
            padx=10, pady=0,
            activebackground=BG_TERT, activeforeground=RED_ALERT,
            command=self.clear_results,
        )
        # Button hover effects
        self._btn_close.bind("<Enter>", lambda e: self._btn_close.config(fg=RED_ALERT))
        self._btn_close.bind("<Leave>", lambda e: self._btn_close.config(fg=GRAY))

        # Thin separator line
        tk.Frame(self, bg=FRAME_COL, height=1).pack(fill="x")

        # Notebook setup
        style = ttk.Style()
        style.theme_use("default")
        style.configure("LB.TNotebook", background=BG_MAIN, borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("LB.TNotebook.Tab", background=BG_TERT, foreground=GRAY, padding=[16, 6], font=("Segoe UI", 9))
        style.map("LB.TNotebook.Tab", background=[("selected", BG_MAIN)], foreground=[("selected", ACCENT)])

        self.notebook = ttk.Notebook(self, style="LB.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        self.tab_chart = tk.Frame(self.notebook, bg=BG_MAIN)
        self.tab_movies = tk.Frame(self.notebook, bg=BG_MAIN)
        self.tab_data = tk.Frame(self.notebook, bg=BG_SEC)

        self.notebook.add(self.tab_chart, text="  📊  Wykres  ")
        self.notebook.add(self.tab_movies, text="  🎬  Filmy  ")
        self.notebook.add(self.tab_data, text="  📋  Dane  ")

        # Initial state
        self._btn_close.pack_forget()
        self._analysis_text.set("  Wybierz analizę po lewej i kliknij ▶ Uruchom")
        self._set_empty_state()

    # ── Public API ─────────────────────────────────────────

    def display_results(self, fig: Figure, title: str = "", df_movies=None, df_data=None):
        self._clear_tabs()
        self._analysis_text.set(f"  {title}" if title else "")
        self._btn_close.pack(side="right", fill="y")

        self._embed_chart(fig)

        if df_movies is not None and not df_movies.empty:
            self._populate_movies(df_movies)
        else:
            _insert_placeholder(self.tab_movies, "Brak listy filmów dla tej analizy.")

        if df_data is not None and not df_data.empty:
            self._populate_data(df_data)
        else:
            _insert_placeholder(self.tab_data, "Brak tabeli danych.")

        self.notebook.select(0)

    def clear_results(self):
        self._clear_tabs()
        self._set_empty_state()
        self._analysis_text.set("  Wybierz analizę po lewej i kliknij ▶ Uruchom")
        self._btn_close.pack_forget()

    # ── Private Methods ─────────────────────────────────────────────

    def _clear_tabs(self):
        for tab in (self.tab_chart, self.tab_movies, self.tab_data):
            for widget in tab.winfo_children():
                widget.destroy()
        self._canvas = None

    def _set_empty_state(self):
        _insert_placeholder(self.tab_chart, "Wybierz analizę w panelu po lewej\ni kliknij  ▶  Uruchom", large=True)
        _insert_placeholder(self.tab_movies, "Tu pojawią się filmy.")
        _insert_placeholder(self.tab_data, "Tu pojawi się tabela danych.")

    def _embed_chart(self, fig: Figure):
        canvas = FigureCanvasTkAgg(fig, master=self.tab_chart)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self.tab_chart)
        toolbar.config(bg=BG_TERT)
        for child in toolbar.winfo_children():
            try:
                child.config(bg=BG_TERT, fg=GRAY_LIGHT, activebackground=BG_QUART, relief="flat", bd=0)
            except tk.TclError:
                pass
        toolbar.update()
        self._canvas = canvas

    def _populate_movies(self, df):
        outer_frame = tk.Frame(self.tab_movies, bg=BG_MAIN)
        outer_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer_frame, bg=BG_MAIN, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner_frame = tk.Frame(canvas, bg=BG_MAIN)
        inner_window_id = canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        canvas.bind("<Configure>", lambda e: canvas.itemconfig(inner_window_id, width=e.width))
        inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        for index, (_, row_data) in enumerate(df.iterrows(), 1):
            KartaFilmu(inner_frame, index, row_data).pack(fill="x", padx=10, pady=3)

    def _populate_data(self, df):
        df_copy = df.copy()
        if "genres" in df_copy.columns:
            df_copy["genres"] = df_copy["genres"].apply(
                lambda g: ", ".join(g) if isinstance(g, list) else str(g))

        scroll_y = ttk.Scrollbar(self.tab_data, orient="vertical")
        scroll_x = ttk.Scrollbar(self.tab_data, orient="horizontal")
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        style = ttk.Style()
        style.configure("LB.Treeview", background=BG_SEC, foreground=TEXT_COLOR, rowheight=24, fieldbackground=BG_SEC,
                        font=("Consolas", 8))
        style.configure("LB.Treeview.Heading", background=BG_TERT, foreground=ACCENT, font=("Consolas", 8, "bold"))
        style.map("LB.Treeview", background=[("selected", "#0a2a14")], foreground=[("selected", ACCENT)])

        columns = list(df_copy.columns)
        tree = ttk.Treeview(self.tab_data, columns=columns, show="headings", style="LB.Treeview",
                            yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.config(command=tree.yview)
        scroll_x.config(command=tree.xview)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=max(90, len(str(col)) * 10), anchor="center")

        for index, (_, row) in enumerate(df_copy.iterrows()):
            tag = "even" if index % 2 == 0 else "odd"
            tree.insert("", "end", values=list(row), tags=(tag,))

        tree.tag_configure("even", background=BG_SEC)
        tree.tag_configure("odd", background="#111111")
        tree.pack(fill="both", expand=True)


# ══════════════════════════════════════════════════════════════
# KartaFilmu (Movie Card)
# ══════════════════════════════════════════════════════════════

class KartaFilmu(tk.Frame):
    """Card: number | poster | title · rating · votes · tags · LB link."""

    POSTER_W = 60
    POSTER_H = 88

    def __init__(self, parent, index: int, movie_data, **kwargs):
        kwargs.setdefault("bg", BG_SEC)
        super().__init__(parent, relief="flat", bd=0, highlightbackground=FRAME_COL, highlightthickness=1, **kwargs)
        self._image = None
        self._build_card(index, movie_data)

        self.bind("<Enter>", lambda e: self.config(highlightbackground=ACCENT_HOV))
        self.bind("<Leave>", lambda e: self.config(highlightbackground=FRAME_COL))

    def _build_card(self, index, movie_data):
        # Order number
        tk.Label(self, text=f"{index:02d}", font=("Consolas", 12, "bold"), fg=FRAME_COL, bg=BG_SEC, width=3).pack(
            side="left", padx=(8, 0), pady=8)

        # Poster
        self.lbl_poster = tk.Label(self, bg="#0a0a0a", width=self.POSTER_W, height=self.POSTER_H)
        self.lbl_poster.pack(side="left", padx=(6, 10), pady=8)

        poster_path = movie_data.get("poster_path")
        if PIL_OK and poster_path:
            self.after(80, lambda: self._load_poster(poster_path))
        else:
            tk.Label(self.lbl_poster, text="🎬", font=("", 18), bg="#0a0a0a", fg=FRAME_COL).place(relx=.5, rely=.5,
                                                                                                 anchor="center")

        # Body frame
        body_frame = tk.Frame(self, bg=BG_SEC)
        body_frame.pack(side="left", fill="both", expand=True, pady=8)

        # Row 1: Title + Year + Rating
        row1 = tk.Frame(body_frame, bg=BG_SEC)
        row1.pack(fill="x")

        tmdb_id = int(movie_data.get("id", 0))
        lb_url = f"https://letterboxd.com/tmdb/{tmdb_id}/"
        title_text = f"{movie_data.get('title', '?')}  ({int(movie_data.get('release_year', 0))})"

        lbl_title = tk.Label(row1, text=title_text, font=("Segoe UI", 10, "bold"), fg=TEXT_COLOR, bg=BG_SEC,
                             cursor="hand2")
        lbl_title.pack(side="left")
        lbl_title.bind("<Button-1>", lambda e, u=lb_url: _open_url(u))
        lbl_title.bind("<Enter>", lambda e: lbl_title.config(fg=ACCENT))
        lbl_title.bind("<Leave>", lambda e: lbl_title.config(fg=TEXT_COLOR))

        rating = movie_data.get("vote_average", 0)
        rating_color = ACCENT if rating >= 7 else ("#ffd166" if rating >= 5.5 else RED_ALERT)
        tk.Label(row1, text=f"  ★ {rating:.1f}", font=("Segoe UI", 9, "bold"), fg=rating_color, bg=BG_SEC).pack(
            side="left")

        # Row 2: Votes and Genre
        votes = int(movie_data.get("vote_count", 0))
        primary_genre = movie_data.get("genre_primary", "")
        tk.Label(body_frame, text=f"{votes:,} głosów  ·  {primary_genre}", font=("Segoe UI", 8), fg=GRAY,
                 bg=BG_SEC).pack(anchor="w", pady=(1, 0))

        # Overview
        overview = str(movie_data.get("overview", "")).strip()
        if overview:
            tk.Label(body_frame, text=overview[:150] + ("…" if len(overview) > 150 else ""),
                     font=("Segoe UI", 8), fg="#555", bg=BG_SEC, wraplength=500, justify="left").pack(anchor="w",
                                                                                                      pady=(2, 0))

        # Genre Tags
        genres = movie_data.get("genres", [])
        if isinstance(genres, list) and genres:
            tags_frame = tk.Frame(body_frame, bg=BG_SEC)
            tags_frame.pack(anchor="w", pady=(5, 0))
            for genre in genres[:5]:
                TagLabel(tags_frame, genre).pack(side="left", padx=(0, 3))

        # Letterboxd Link
        lbl_link = tk.Label(body_frame, text="↗ otwórz na Letterboxd", font=("Segoe UI", 7), fg="#1c4a28", bg=BG_SEC,
                            cursor="hand2")
        lbl_link.pack(anchor="w", pady=(4, 0))
        lbl_link.bind("<Button-1>", lambda e, u=lb_url: _open_url(u))
        lbl_link.bind("<Enter>", lambda e: lbl_link.config(fg=ACCENT))
        lbl_link.bind("<Leave>", lambda e: lbl_link.config(fg="#1c4a28"))

    def _load_poster(self, path: str):
        try:
            url = f"https://image.tmdb.org/t/p/w92{path}"
            with urllib.request.urlopen(url, timeout=5) as response:
                img_data = response.read()
            image = Image.open(io.BytesIO(img_data)).resize((self.POSTER_W, self.POSTER_H), Image.LANCZOS)
            self._image = ImageTk.PhotoImage(image)
            self.lbl_poster.config(image=self._image, width=self.POSTER_W, height=self.POSTER_H)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════
# TagLabel
# ══════════════════════════════════════════════════════════════

class TagLabel(tk.Label):
    """Small tag label for movie genres."""

    def __init__(self, parent, text_val, **kwargs):
        kwargs.setdefault("text", text_val)
        kwargs.setdefault("font", ("Segoe UI", 7))
        kwargs.setdefault("fg", "#3a9a58")
        kwargs.setdefault("bg", "#081a10")
        kwargs.setdefault("padx", 6)
        kwargs.setdefault("pady", 2)
        kwargs.setdefault("relief", "flat")
        super().__init__(parent, **kwargs)


# ══════════════════════════════════════════════════════════════
# PasekStatusu (Status Bar)
# ══════════════════════════════════════════════════════════════

class PasekStatusu(tk.Frame):
    """Status bar with animated loading dots."""

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", "#0a0a0a")
        kwargs.setdefault("height", 28)
        super().__init__(parent, **kwargs)
        tk.Frame(self, bg=FRAME_COL, height=1).pack(fill="x")

        self._status_var = tk.StringVar(value="")
        self._lbl_status = tk.Label(self, textvariable=self._status_var, bg="#0a0a0a", fg=GRAY, font=("Consolas", 8),
                                    anchor="w", padx=12)
        self._lbl_status.pack(side="left", fill="x", expand=True)

        tk.Label(self, text="TMDB  ·  v2.1", bg="#0a0a0a", fg="#1e1e1e", font=("Consolas", 7), padx=10).pack(
            side="right")

        self._animation_job = None

    def set_status(self, message: str):
        self._stop_animation()
        color = GRAY
        if message.startswith("✔"):
            color = ACCENT
        elif message.startswith("Błąd"):
            color = RED_ALERT

        self._lbl_status.config(fg=color)
        self._status_var.set(message)
        self.update_idletasks()

    def start_loading(self, base_text: str = "Pobieranie danych"):
        """Starts the animated loading dots."""
        self._lbl_status.config(fg="#4daaff")
        self._dots_count = 0
        self._base_text = base_text

        def _animate_step():
            self._dots_count = (self._dots_count + 1) % 4
            self._status_var.set(self._base_text + "." * self._dots_count)
            self._animation_job = self.after(380, _animate_step)

        _animate_step()

    def _stop_animation(self):
        if self._animation_job:
            self.after_cancel(self._animation_job)
            self._animation_job = None


# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════

def _insert_placeholder(tab: tk.Frame, text_val: str, large: bool = False):
    """Inserts centered placeholder text into an empty tab."""
    for widget in tab.winfo_children():
        widget.destroy()
    font_style = ("Segoe UI", 13) if large else ("Segoe UI", 9)
    tk.Label(tab, text=text_val, font=font_style, fg=FRAME_COL, bg=tab["bg"], justify="center").place(relx=.5, rely=.5,
                                                                                                      anchor="center")


def _open_url(url: str):
    webbrowser.open(url)
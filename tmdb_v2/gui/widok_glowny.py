"""
gui/widok_glowny.py
===================
Główny widok aplikacji (Main View). Inicjalizuje i układa wszystkie widgety.
"""

import tkinter as tk
from .widgety import RamkaWynikow, PasekStatusu
from .panel_boczny import PanelBoczny

# ── Palette ────────────────────────────────────────────────────
BG_MAIN, BG_SEC = "#0d0d0d", "#141414"
TEXT_COLOR, GRAY, FRAME_COL = "#e8e6e1", "#666666", "#2a2a2a"


class WidokGlowny(tk.Tk):
    def __init__(self, analyses_dict, on_run_callback):
        super().__init__()
        self.title("TMDB · Analiza Filmów")
        self.geometry("1300x820")
        self.minsize(960, 640)
        self.configure(bg=BG_MAIN)

        self.analyses_dict = analyses_dict
        self.on_run_callback = on_run_callback

        self._build_layout()

    def _build_layout(self):
        # Nagłówek
        nav = tk.Frame(self, bg=BG_SEC)
        nav.pack(fill="x")
        tk.Label(nav, text="● TMDB Analiza Filmów", font=("Segoe UI", 13, "bold"), fg=TEXT_COLOR, bg=BG_SEC, pady=11,
                 padx=16).pack(side="left")
        tk.Button(nav, text="✕", font=("Segoe UI", 12), fg=GRAY, bg=BG_SEC, relief="flat", bd=0, cursor="hand2",
                  padx=14, pady=8, command=self.destroy).pack(side="right")
        tk.Frame(self, bg=FRAME_COL, height=1).pack(fill="x")

        # Główny siatka (Grid)
        main_frame = tk.Frame(self, bg=BG_MAIN)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(2, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        self.results_frame = RamkaWynikow(main_frame, bg=BG_MAIN)
        self.results_frame.grid(row=0, column=2, sticky="nsew")
        tk.Frame(main_frame, bg=FRAME_COL, width=1).grid(row=0, column=1, sticky="ns")

        # Panel boczny
        self.sidebar = PanelBoczny(main_frame, self.analyses_dict, self.on_run_callback,
                                   self.results_frame.clear_results)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self.status_bar = PasekStatusu(self)
        self.status_bar.pack(fill="x", side="bottom")

    # ── Metody pomocnicze dla Kontrolera ──
    def get_params(self):
        return self.sidebar.get_params()

    def set_status(self, msg):
        self.status_bar.set_status(msg)

    def start_loading(self, msg):
        self.status_bar.start_loading(msg)

    def display_results(self, fig, title, df_movies, df_data):
        self.results_frame.display_results(fig, title=title, df_movies=df_movies, df_data=df_data)

    def clear_results(self):
        self.results_frame.clear_results()

    def set_run_button_state(self, state, text):
        self.sidebar.btn_run.config(state=state, text=text)
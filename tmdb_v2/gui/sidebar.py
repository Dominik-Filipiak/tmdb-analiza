"""
gui/sidebar.py
===================
Moduł odpowiedzialny za lewy panel sterowania (View).
"""

import tkinter as tk
from tkinter import ttk

# ── Palette ────────────────────────────────────────────────────
BG_SEC, BG_TERT, BG_QUART = "#141414", "#1c1c1c", "#242424"
ACCENT, GRAY, GRAY_LIGHT, TEXT_COLOR, FRAME_COL = "#00c030", "#666666", "#999999", "#e8e6e1", "#2a2a2a"


class Sidebar(tk.Frame):
    """Panel boczny z parametrami i przyciskami (UI)."""

    def __init__(self, parent, available_analyses, on_run_callback, on_clear_callback):
        super().__init__(parent, bg=BG_SEC, width=272)
        self.pack_propagate(False)
        self.on_run = on_run_callback
        self.available_analyses = available_analyses

        # Pobieramy pierwszy klucz z dostępnych analiz jako domyślny
        default_analysis = list(available_analyses.keys())[0]
        self.analysis_var = tk.StringVar(value=default_analysis)
        self.show_movies_var = tk.BooleanVar(value=True)
        self.show_table_var = tk.BooleanVar(value=True)
        self._rb_frames = {}

        self._build_styles()
        self._build_sections(on_clear_callback)

    def _build_styles(self):
        style = ttk.Style()
        style.configure("LB.TCombobox", fieldbackground=BG_QUART, background=BG_QUART, foreground=TEXT_COLOR,
                        borderwidth=0)
        style.map("LB.TCombobox", fieldbackground=[("readonly", BG_QUART)], foreground=[("readonly", TEXT_COLOR)])
        style.configure("LB.TSpinbox", fieldbackground=BG_QUART, foreground=TEXT_COLOR, borderwidth=0)
        style.configure("LB.TCheckbutton", background=BG_SEC, foreground=GRAY_LIGHT)
        style.map("LB.TCheckbutton", foreground=[("active", TEXT_COLOR)], background=[("active", BG_SEC)])
        self.option_add("*TCombobox*Listbox.background", BG_QUART)
        self.option_add("*TCombobox*Listbox.foreground", TEXT_COLOR)

    def _build_sections(self, on_clear):
        self._header("ANALIZA")
        for key, (label, _) in self.available_analyses.items():
            frm = tk.Frame(self, bg=BG_SEC, cursor="hand2")
            frm.pack(fill="x", padx=10, pady=1)
            self._rb_frames[key] = frm

            dot = tk.Label(frm, text="◆", font=("Segoe UI", 7), fg=BG_QUART, bg=BG_SEC)
            lbl = tk.Label(frm, text=label, font=("Segoe UI", 9), fg=GRAY_LIGHT, bg=BG_SEC, anchor="w")
            dot.pack(side="left", padx=(6, 4))
            lbl.pack(side="left", fill="x", expand=True, pady=5)

            for w in (frm, dot, lbl):
                w.bind("<Button-1>", lambda e, k=key: self._select_rb(k))

        self._select_rb(self.analysis_var.get())

        self._header("PARAMETRY")
        years = list(range(1970, 2026))
        self.cb_year_from = self._combo("Rok od:", years, "2010")
        self.cb_year_to = self._combo("Rok do:", years, "2024")
        self.sb_votes = self._spin("Min. głosów:", 50, 20000, 50, "500")
        self.sb_pages = self._spin("Stron API (1 str=20 filmów):", 1, 10, 1, "5")

        self._header("WYNIKI")
        ttk.Checkbutton(self, text="Zakładka Filmy (Top 50)", variable=self.show_movies_var,
                        style="LB.TCheckbutton").pack(anchor="w", padx=14, pady=2)
        ttk.Checkbutton(self, text="Zakładka Dane (tabela)", variable=self.show_table_var,
                        style="LB.TCheckbutton").pack(anchor="w", padx=14, pady=2)

        tk.Frame(self, bg=FRAME_COL, height=1).pack(fill="x", pady=(14, 0))
        btn_box = tk.Frame(self, bg=BG_SEC)
        btn_box.pack(fill="x", padx=12, pady=10)

        self.btn_run = tk.Button(btn_box, text="▶  Uruchom analizę", command=self.on_run, bg=ACCENT, fg="#000",
                                 font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", pady=9)
        self.btn_run.pack(fill="x", pady=(0, 4))
        tk.Button(btn_box, text="✕  Wyczyść wyniki", command=on_clear, bg=BG_QUART, fg=GRAY_LIGHT, font=("Segoe UI", 9),
                  relief="flat", cursor="hand2", pady=7).pack(fill="x")

    def _header(self, text):
        tk.Frame(self, bg=FRAME_COL, height=1).pack(fill="x", pady=(10, 0))
        tk.Label(self, text=text, font=("Segoe UI", 7, "bold"), fg=GRAY, bg=BG_SEC, anchor="w", padx=14).pack(fill="x",
                                                                                                              pady=(6,
                                                                                                                    4))

    def _combo(self, label, values, default):
        tk.Label(self, text=label, font=("Segoe UI", 8), fg=GRAY, bg=BG_SEC, anchor="w", padx=14).pack(fill="x",
                                                                                                       pady=(7, 1))
        cb = ttk.Combobox(self, values=values, state="readonly", style="LB.TCombobox", font=("Segoe UI", 9))
        cb.set(default)
        cb.pack(anchor="w", padx=14)
        return cb

    def _spin(self, label, from_, to_, inc, default):
        tk.Label(self, text=label, font=("Segoe UI", 8), fg=GRAY, bg=BG_SEC, anchor="w", padx=14).pack(fill="x",
                                                                                                       pady=(7, 1))
        sb = ttk.Spinbox(self, from_=from_, to=to_, increment=inc, style="LB.TSpinbox", font=("Segoe UI", 9))
        sb.set(default)
        sb.pack(anchor="w", padx=14)
        return sb

    def _select_rb(self, key):
        self.analysis_var.set(key)
        for k, frm in self._rb_frames.items():
            is_act = (k == key)
            frm.config(bg=BG_TERT if is_act else BG_SEC)
            for w in frm.winfo_children():
                if w.cget("text") == "◆":
                    w.config(bg=BG_TERT if is_act else BG_SEC, fg=ACCENT if is_act else BG_QUART)
                else:
                    w.config(bg=BG_TERT if is_act else BG_SEC, fg=TEXT_COLOR if is_act else GRAY_LIGHT)

    def get_params(self):
        """Zwraca słownik z ustawieniami wprowadzonymi przez użytkownika."""
        return {
            "analysis_key": self.analysis_var.get(),
            "year_from": int(self.cb_year_from.get()),
            "year_to": int(self.cb_year_to.get()),
            "min_votes": int(self.sb_votes.get()),
            "pages": int(self.sb_pages.get()),
            "show_movies": self.show_movies_var.get(),
            "show_table": self.show_table_var.get()
        }
"""
gui/widgety.py  –  TMDB Analiza v2.1
=====================================
Widżety GUI: ciemny motyw inspirowany Letterboxd, akcent #00c030.
"""

import tkinter as tk
from tkinter import ttk
import io
import urllib.request

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ── paleta ────────────────────────────────────────────────────
BG    = "#0d0d0d"
BG2   = "#141414"
BG3   = "#1c1c1c"
BG4   = "#242424"
AKCJA = "#00c030"
AKCJA2= "#00a828"
SZARY = "#666666"
SZARY2= "#999999"
TEXT  = "#e8e6e1"
RAMKA = "#2a2a2a"
CZERW = "#ff4444"


# ══════════════════════════════════════════════════════════════
# RamkaWynikow  –  obszar z zakładkami + przycisk zamknięcia
# ══════════════════════════════════════════════════════════════

class RamkaWynikow(tk.Frame):
    """Notebook (Wykres / Filmy / Dane) z belką tytułową i przyciskiem ✕."""

    def __init__(self, rodzic, **kw):
        kw.setdefault("bg", BG)
        super().__init__(rodzic, **kw)
        self._canvas      = None
        self._analiza_txt = tk.StringVar(value="")
        self._zbuduj()

    # ── budowanie ─────────────────────────────────────────────

    def _zbuduj(self):
        # Belka nad zakładkami: nazwa aktywnej analizy + przycisk ✕
        self._belka = tk.Frame(self, bg=BG3, height=34)
        self._belka.pack(fill="x")
        self._belka.pack_propagate(False)

        self._lbl_analiza = tk.Label(
            self._belka, textvariable=self._analiza_txt,
            font=("Segoe UI", 9), fg=SZARY2, bg=BG3, anchor="w", padx=14)
        self._lbl_analiza.pack(side="left", fill="y")

        # Przycisk zamknięcia (wyczyść wyniki)
        self._btn_x = tk.Button(
            self._belka, text="✕",
            font=("Segoe UI", 11), fg=SZARY, bg=BG3,
            relief="flat", bd=0, cursor="hand2",
            padx=10, pady=0,
            activebackground=BG3, activeforeground=CZERW,
            command=self.clear_results,
        )
        # ✕ zaczyna schowany – pojawi się gdy są wyniki
        self._btn_x.bind("<Enter>", lambda e: self._btn_x.config(fg=CZERW))
        self._btn_x.bind("<Leave>", lambda e: self._btn_x.config(fg=SZARY))

        # Cienka linia separatora
        tk.Frame(self, bg=RAMKA, height=1).pack(fill="x")

        # Notebook
        styl = ttk.Style()
        styl.theme_use("default")
        styl.configure("LB.TNotebook", background=BG, borderwidth=0,
                        tabmargins=[0, 0, 0, 0])
        styl.configure("LB.TNotebook.Tab",
                        background=BG3, foreground=SZARY,
                        padding=[16, 6], font=("Segoe UI", 9))
        styl.map("LB.TNotebook.Tab",
                 background=[("selected", BG)],
                 foreground=[("selected", AKCJA)])

        self.nb = ttk.Notebook(self, style="LB.TNotebook")
        self.nb.pack(fill="both", expand=True)

        self.tab_wykres = tk.Frame(self.nb, bg=BG)
        self.tab_filmy  = tk.Frame(self.nb, bg=BG)
        self.tab_dane   = tk.Frame(self.nb, bg=BG2)

        self.nb.add(self.tab_wykres, text="  📊  Wykres  ")
        self.nb.add(self.tab_filmy,  text="  🎬  Filmy  ")
        self.nb.add(self.tab_dane,   text="  📋  Dane  ")

        # Stan startowy: schowaj ✕, ustaw hint
        self._btn_x.pack_forget()
        self._analiza_txt.set("  Wybierz analizę po lewej i kliknij ▶ Uruchom")
        self._stan_pusty()

    # ── publiczne API ─────────────────────────────────────────

    def display_results(self, fig: Figure, title: str = "",
                        df_movies=None, df_data=None):
        self._wyczysc_tabs()
        self._analiza_txt.set(f"  {title}" if title else "")

        self._btn_x.pack(side="right", fill="y")

        self._osadz_wykres(fig)

        if df_movies is not None and not df_movies.empty:
            self._wypelnij_filmy(df_movies)
        else:
            _placeholder(self.tab_filmy, "Brak listy filmów dla tej analizy.")

        if df_data is not None and not df_data.empty:
            self._wypelnij_dane(df_data)
        else:
            _placeholder(self.tab_dane, "Brak tabeli danych.")

        self.nb.select(0)

    def clear_results(self):
        self._wyczysc_tabs()
        self._stan_pusty()
        self._analiza_txt.set("  Wybierz analizę po lewej i kliknij ▶ Uruchom")
        self._btn_x.pack_forget()

    # ── prywatne ─────────────────────────────────────────────

    def _wyczysc_tabs(self):
        for tab in (self.tab_wykres, self.tab_filmy, self.tab_dane):
            for w in tab.winfo_children():
                w.destroy()
        self._canvas = None

    def _stan_pusty(self):
        _placeholder(self.tab_wykres,
                     "Wybierz analizę w panelu po lewej\ni kliknij  ▶  Uruchom",
                     duzy=True)
        _placeholder(self.tab_filmy, "Tu pojawią się filmy.")
        _placeholder(self.tab_dane,  "Tu pojawi się tabela danych.")

    def _osadz_wykres(self, fig: Figure):
        canvas = FigureCanvasTkAgg(fig, master=self.tab_wykres)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        tb = NavigationToolbar2Tk(canvas, self.tab_wykres)
        # Stylizacja paska narzędzi matplotlib
        tb.config(bg=BG3)
        for child in tb.winfo_children():
            try:
                child.config(bg=BG3, fg=SZARY2,
                             activebackground=BG4, relief="flat", bd=0)
            except tk.TclError:
                pass
        tb.update()
        self._canvas = canvas

    def _wypelnij_filmy(self, df):
        outer = tk.Frame(self.tab_filmy, bg=BG)
        outer.pack(fill="both", expand=True)

        c  = tk.Canvas(outer, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=c.yview)
        c.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        c.pack(side="left", fill="both", expand=True)

        wew    = tk.Frame(c, bg=BG)
        wew_id = c.create_window((0, 0), window=wew, anchor="nw")

        c.bind("<Configure>",   lambda e: c.itemconfig(wew_id, width=e.width))
        wew.bind("<Configure>", lambda e: c.configure(scrollregion=c.bbox("all")))
        c.bind_all("<MouseWheel>",
                   lambda e: c.yview_scroll(int(-1*(e.delta/120)), "units"))

        for i, (_, r) in enumerate(df.iterrows(), 1):
            KartaFilmu(wew, i, r).pack(fill="x", padx=10, pady=3)

    def _wypelnij_dane(self, df):
        df_d = df.copy()
        if "genres" in df_d.columns:
            df_d["genres"] = df_d["genres"].apply(
                lambda g: ", ".join(g) if isinstance(g, list) else str(g))

        sb_y = ttk.Scrollbar(self.tab_dane, orient="vertical")
        sb_x = ttk.Scrollbar(self.tab_dane, orient="horizontal")
        sb_y.pack(side="right",  fill="y")
        sb_x.pack(side="bottom", fill="x")

        styl = ttk.Style()
        styl.configure("LB.Treeview",
                        background=BG2, foreground=TEXT,
                        rowheight=24, fieldbackground=BG2,
                        font=("Consolas", 8))
        styl.configure("LB.Treeview.Heading",
                        background=BG3, foreground=AKCJA,
                        font=("Consolas", 8, "bold"))
        styl.map("LB.Treeview",
                 background=[("selected", "#0a2a14")],
                 foreground=[("selected", AKCJA)])

        kol = list(df_d.columns)
        t = ttk.Treeview(self.tab_dane, columns=kol, show="headings",
                         style="LB.Treeview",
                         yscrollcommand=sb_y.set,
                         xscrollcommand=sb_x.set)
        sb_y.config(command=t.yview)
        sb_x.config(command=t.xview)
        for k in kol:
            t.heading(k, text=k)
            t.column(k, width=max(90, len(str(k))*10), anchor="center")
        for i, (_, w) in enumerate(df_d.iterrows()):
            tag = "even" if i % 2 == 0 else "odd"
            t.insert("", "end", values=list(w), tags=(tag,))
        t.tag_configure("even", background=BG2)
        t.tag_configure("odd",  background="#111111")
        t.pack(fill="both", expand=True)


# ══════════════════════════════════════════════════════════════
# KartaFilmu
# ══════════════════════════════════════════════════════════════

class KartaFilmu(tk.Frame):
    """Karta: numer | plakat | tytuł · ocena · głosy · tagi · link Letterboxd."""

    POSTER_W = 60
    POSTER_H = 88

    def __init__(self, rodzic, numer: int, dane, **kw):
        kw.setdefault("bg", BG2)
        super().__init__(rodzic, relief="flat", bd=0,
                         highlightbackground=RAMKA,
                         highlightthickness=1, **kw)
        self._img = None
        self._zbuduj(numer, dane)

        # Hover: podświetlenie ramki
        self.bind("<Enter>", lambda e: self.config(highlightbackground=AKCJA2))
        self.bind("<Leave>", lambda e: self.config(highlightbackground=RAMKA))

    def _zbuduj(self, n, d):
        bg = BG2

        # Numer porządkowy
        tk.Label(self, text=f"{n:02d}",
                 font=("Consolas", 12, "bold"),
                 fg=RAMKA, bg=bg, width=3
                 ).pack(side="left", padx=(8, 0), pady=8)

        # Plakat
        self.lbl_poster = tk.Label(self, bg="#0a0a0a",
                                   width=self.POSTER_W,
                                   height=self.POSTER_H)
        self.lbl_poster.pack(side="left", padx=(6, 10), pady=8)

        poster_path = d.get("poster_path")
        if PIL_OK and poster_path:
            self.after(80, lambda: self._zaladuj_plakat(poster_path))
        else:
            tk.Label(self.lbl_poster, text="🎬", font=("", 18),
                     bg="#0a0a0a", fg="#2a2a2a"
                     ).place(relx=.5, rely=.5, anchor="center")

        # Treść
        body = tk.Frame(self, bg=bg)
        body.pack(side="left", fill="both", expand=True, pady=8)

        # Wiersz 1: tytuł + rok + ocena
        row1 = tk.Frame(body, bg=bg)
        row1.pack(fill="x")

        tmdb_id = int(d.get("id", 0))
        lb_url  = f"https://letterboxd.com/tmdb/{tmdb_id}/"
        tytul   = f"{d.get('title', '?')}  ({int(d.get('release_year', 0))})"

        lbl_t = tk.Label(row1, text=tytul,
                         font=("Segoe UI", 10, "bold"),
                         fg=TEXT, bg=bg, cursor="hand2")
        lbl_t.pack(side="left")
        lbl_t.bind("<Button-1>", lambda e, u=lb_url: _otworz(u))
        lbl_t.bind("<Enter>", lambda e: lbl_t.config(fg=AKCJA))
        lbl_t.bind("<Leave>", lambda e: lbl_t.config(fg=TEXT))

        ocena = d.get("vote_average", 0)
        # Kolor gwiazdki wg oceny
        kol_o = AKCJA if ocena >= 7 else ("#ffd166" if ocena >= 5.5 else "#ff6b6b")
        tk.Label(row1, text=f"  ★ {ocena:.1f}",
                 font=("Segoe UI", 9, "bold"),
                 fg=kol_o, bg=bg).pack(side="left")

        # Wiersz 2: głosy · gatunek
        glosy   = int(d.get("vote_count", 0))
        gatunek = d.get("genre_primary", "")
        tk.Label(body,
                 text=f"{glosy:,} głosów  ·  {gatunek}",
                 font=("Segoe UI", 8), fg=SZARY, bg=bg
                 ).pack(anchor="w", pady=(1, 0))

        # Opis (overview)
        ov = str(d.get("overview", "")).strip()
        if ov:
            tk.Label(body,
                     text=ov[:150] + ("…" if len(ov) > 150 else ""),
                     font=("Segoe UI", 8), fg="#555", bg=bg,
                     wraplength=500, justify="left"
                     ).pack(anchor="w", pady=(2, 0))

        # Tagi gatunków
        gatunki = d.get("genres", [])
        if isinstance(gatunki, list) and gatunki:
            tagi = tk.Frame(body, bg=bg)
            tagi.pack(anchor="w", pady=(5, 0))
            for g in gatunki[:5]:
                TagLabel(tagi, g).pack(side="left", padx=(0, 3))

        # Link Letterboxd
        lbl_lb = tk.Label(body, text="↗ otwórz na Letterboxd",
                          font=("Segoe UI", 7), fg="#1c4a28",
                          bg=bg, cursor="hand2")
        lbl_lb.pack(anchor="w", pady=(4, 0))
        lbl_lb.bind("<Button-1>", lambda e, u=lb_url: _otworz(u))
        lbl_lb.bind("<Enter>", lambda e: lbl_lb.config(fg=AKCJA))
        lbl_lb.bind("<Leave>", lambda e: lbl_lb.config(fg="#1c4a28"))

    def _zaladuj_plakat(self, path: str):
        try:
            url = f"https://image.tmdb.org/t/p/w92{path}"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = r.read()
            img = Image.open(io.BytesIO(data)).resize(
                (self.POSTER_W, self.POSTER_H), Image.LANCZOS)
            self._img = ImageTk.PhotoImage(img)
            self.lbl_poster.config(image=self._img,
                                   width=self.POSTER_W,
                                   height=self.POSTER_H)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════
# TagLabel
# ══════════════════════════════════════════════════════════════

class TagLabel(tk.Label):
    """Mała etykieta gatunku filmowego."""
    def __init__(self, rodzic, tekst, **kw):
        kw.setdefault("text",   tekst)
        kw.setdefault("font",   ("Segoe UI", 7))
        kw.setdefault("fg",     "#3a9a58")
        kw.setdefault("bg",     "#081a10")
        kw.setdefault("padx",   6)
        kw.setdefault("pady",   2)
        kw.setdefault("relief", "flat")
        super().__init__(rodzic, **kw)


# ══════════════════════════════════════════════════════════════
# PasekStatusu
# ══════════════════════════════════════════════════════════════

class PasekStatusu(tk.Frame):
    def __init__(self, rodzic, **kw):
        kw.setdefault("bg", "#0a0a0a")
        kw.setdefault("height", 28)
        super().__init__(rodzic, **kw)

        tk.Frame(self, bg=RAMKA, height=1).pack(fill="x")

        self._var = tk.StringVar(value="")
        self._lbl = tk.Label(
            self,
            textvariable=self._var,
            bg="#0a0a0a",
            fg=SZARY,
            font=("Consolas", 8),
            anchor="w",
            padx=12,
        )
        self._lbl.pack(side="left", fill="x", expand=True)

        self._dot_job = None

    def set_status(self, tekst):
        self._zatrzymaj_animacje()
        self._var.set(tekst)

    def start_loading(self, baza="Pobieranie danych"):
        self._lbl.config(fg="#4daaff")
        self._dot = 0
        self._dot_baza = baza

        def _krok():
            self._dot = (self._dot + 1) % 4
            self._var.set(self._dot_baza + "." * self._dot)
            self._dot_job = self.after(380, _krok)

        _krok()

    def _zatrzymaj_animacje(self):
        if self._dot_job:
            self.after_cancel(self._dot_job)
            self._dot_job = None

    def set_status(self, msg):
        self.set_status(msg)

    def start_loading(self, msg):
        self.start_loading(msg)

# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════

def _placeholder(tab: tk.Frame, tekst: str, duzy: bool = False):
    """Wstawia wyśrodkowany napis zastępczy do pustej zakładki."""
    for w in tab.winfo_children():
        w.destroy()
    font = ("Segoe UI", 13) if duzy else ("Segoe UI", 9)
    tk.Label(tab, text=tekst, font=font,
             fg="#2a2a2a", bg=tab["bg"],
             justify="center"
             ).place(relx=.5, rely=.5, anchor="center")


def _otworz(url: str):
    import webbrowser
    webbrowser.open(url)

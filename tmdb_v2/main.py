"""
main.py – Analiza Danych Filmowych TMDB  v2.1
==============================================
Projekt zaliczeniowy – Python · requests · pandas · numpy · matplotlib · tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

import matplotlib
matplotlib.use("TkAgg")

from api.tmdb_client import TMDBClient
from analiza.analizy import (
    analizuj_popularne_gatunki,
    analizuj_rozklad_ocen,
    analizuj_trendy_czasowe,
    analizuj_top_filmy,
    analizuj_porownanie_gatunkow,
)
from gui.widgety import RamkaWynikow, PasekStatusu

# ── paleta ────────────────────────────────────────────────────
BG    = "#0d0d0d"
BG2   = "#141414"
BG3   = "#1c1c1c"
BG4   = "#242424"
AKCJA = "#00c030"
SZARY = "#666666"
SZARY2= "#999999"
TEXT  = "#e8e6e1"
RAMKA = "#2a2a2a"

ANALIZY = {
    "popularne_gatunki":   ("Popularność gatunków",    analizuj_popularne_gatunki),
    "rozklad_ocen":        ("Rozkład ocen",             analizuj_rozklad_ocen),
    "trendy_czasowe":      ("Trendy w czasie",          analizuj_trendy_czasowe),
    "top_filmy":           ("Top filmy · ocena ważona", analizuj_top_filmy),
    "porownanie_gatunkow": ("Porównanie gatunków",      analizuj_porownanie_gatunkow),
}


# ══════════════════════════════════════════════════════════════

class Aplikacja(tk.Tk):
    """
    Okno główne aplikacji do analizy danych filmowych TMDB.
    Dane pobierane dynamicznie z TMDB API (requests).
    Analizy uruchamiane w wątku tła – Figure() bezpieczne poza GUI.
    """

    def __init__(self):
        super().__init__()
        self.title("TMDB · Analiza Filmów")
        self.geometry("1300x820")
        self.minsize(960, 640)
        self.configure(bg=BG)

        self.klient = None  # inicjowany w wątku tła

        self._buduj_ui()
        self.pasek.ladowanie("Łączenie z TMDB")

        # Inicjalizacja klienta (żądanie HTTP) w wątku tła
        import threading
        threading.Thread(target=self._init_klienta, daemon=True).start()

    def _init_klienta(self):
        """Łączy się z TMDB API w tle – nie blokuje GUI."""
        try:
            self.klient = TMDBClient()
            self.after(0, lambda: self.pasek.ustaw(
                "✔ Połączono z TMDB. Ustaw parametry i kliknij ▶ Uruchom."))
        except Exception as e:
            self.after(0, lambda: self.pasek.ustaw(
                f"Błąd połączenia z TMDB: {e}"))
            self.after(0, lambda: messagebox.showwarning(
                "Brak połączenia",
                f"Nie udało się połączyć z TMDB API:\n{e}\n\n"
                "Sprawdź połączenie internetowe i uruchom ponownie."))

    # ── UI ────────────────────────────────────────────────────

    def _buduj_ui(self):
        self._naglowek()

        # grid: kolumna 0 = stały lewy panel, kolumna 2 = rozciągliwy prawy
        glowny = tk.Frame(self, bg=BG)
        glowny.pack(fill="both", expand=True)
        glowny.grid_rowconfigure(0, weight=1)
        glowny.grid_columnconfigure(0, weight=0, minsize=272)  # lewy – stały
        glowny.grid_columnconfigure(1, weight=0, minsize=1)    # separator
        glowny.grid_columnconfigure(2, weight=1)               # prawy – rozciągliwy

        # Prawy panel NAJPIERW – bo _panel_lewy odwołuje się do self.wyniki
        self.wyniki = RamkaWynikow(glowny, bg=BG)
        self.wyniki.grid(row=0, column=2, sticky="nsew")

        # Separator
        tk.Frame(glowny, bg=RAMKA, width=1).grid(row=0, column=1, sticky="ns")

        # Lewy panel
        lewa = tk.Frame(glowny, bg=BG2, width=272)
        lewa.grid(row=0, column=0, sticky="nsw")
        lewa.grid_propagate(False)
        self._panel_lewy(lewa)

        self.pasek = PasekStatusu(self)
        self.pasek.pack(fill="x", side="bottom")

    def _naglowek(self):
        nav = tk.Frame(self, bg=BG2)
        nav.pack(fill="x")

        # Lewa strona: logo
        logo = tk.Frame(nav, bg=BG2, pady=11)
        logo.pack(side="left", padx=(16, 0))

        tk.Label(logo, text="●", font=("Segoe UI", 14),
                 fg=AKCJA, bg=BG2).pack(side="left")
        tk.Label(logo, text="  TMDB", font=("Segoe UI", 13, "bold"),
                 fg=TEXT, bg=BG2).pack(side="left")
        tk.Label(logo, text=" Analiza Filmów",
                 font=("Segoe UI", 13), fg=SZARY2, bg=BG2).pack(side="left")

        # Prawa strona: info + przycisk zamknięcia aplikacji
        prawa = tk.Frame(nav, bg=BG2)
        prawa.pack(side="right")

        tk.Label(prawa, text="The Movie Database API  ",
                 font=("Segoe UI", 8), fg="#2a2a2a", bg=BG2
                 ).pack(side="left", pady=11)

        btn_zamknij = tk.Button(
            prawa, text="✕",
            font=("Segoe UI", 12), fg=SZARY, bg=BG2,
            relief="flat", bd=0, cursor="hand2",
            padx=14, pady=8,
            activebackground=BG3, activeforeground="#ff4444",
            command=self.destroy,
        )
        btn_zamknij.pack(side="left")
        btn_zamknij.bind("<Enter>", lambda e: btn_zamknij.config(fg="#ff4444", bg=BG3))
        btn_zamknij.bind("<Leave>", lambda e: btn_zamknij.config(fg=SZARY,    bg=BG2))

        # Separator pod nagłówkiem
        tk.Frame(self, bg=RAMKA, height=1).pack(fill="x")

    def _panel_lewy(self, rodzic):

        # ── helper: podpis sekcji ─────────────────────────────
        def sekcja(txt):
            tk.Frame(rodzic, bg=RAMKA, height=1).pack(fill="x",
                                                       padx=0, pady=(10, 0))
            tk.Label(rodzic, text=txt,
                     font=("Segoe UI", 7, "bold"),
                     fg=SZARY, bg=BG2, anchor="w", padx=14
                     ).pack(fill="x", pady=(6, 4))

        # ── Wybór analizy (własne radiobuttons) ───────────────
        sekcja("ANALIZA")
        self._analiza = tk.StringVar(value="popularne_gatunki")
        self._rb_frames: dict[str, tk.Frame] = {}

        for klucz, (etykieta, _) in ANALIZY.items():
            frm = tk.Frame(rodzic, bg=BG2, cursor="hand2")
            frm.pack(fill="x", padx=10, pady=1)
            self._rb_frames[klucz] = frm

            dot = tk.Label(frm, text="◆", font=("Segoe UI", 7),
                           fg=BG4, bg=BG2)
            dot.pack(side="left", padx=(6, 4))

            lbl = tk.Label(frm, text=etykieta,
                           font=("Segoe UI", 9), fg=SZARY2, bg=BG2,
                           anchor="w")
            lbl.pack(side="left", fill="x", expand=True, pady=5)

            def _wybierz(k=klucz):
                self._analiza.set(k)
                self._aktualizuj_rb()

            for w in (frm, dot, lbl):
                w.bind("<Button-1>", lambda e, k=klucz: _wybierz(k))
                w.bind("<Enter>",    lambda e, f=frm, l=lbl: (
                    f.config(bg=BG3), l.config(bg=BG3, fg=TEXT)))
                w.bind("<Leave>",    lambda e, f=frm, l=lbl, k=klucz: (
                    f.config(bg=BG2 if self._analiza.get()!=k else BG3),
                    l.config(bg=BG2 if self._analiza.get()!=k else BG3,
                             fg=TEXT if self._analiza.get()==k else SZARY2)))

        self._aktualizuj_rb()

        # ── Parametry ─────────────────────────────────────────
        sekcja("PARAMETRY")

        styl = ttk.Style()
        styl.configure("LB.TCombobox",
                        fieldbackground=BG4, background=BG4,
                        foreground=TEXT, selectbackground=BG4,
                        selectforeground=TEXT, insertcolor=TEXT,
                        borderwidth=0, arrowcolor=SZARY2)
        styl.map("LB.TCombobox",
                 fieldbackground=[("readonly", BG4)],
                 foreground=[("readonly", TEXT)],
                 selectbackground=[("readonly", BG4)])
        styl.configure("LB.TSpinbox",
                        fieldbackground=BG4, foreground=TEXT,
                        selectbackground=BG4, selectforeground=TEXT,
                        borderwidth=0, arrowsize=10, insertcolor=TEXT)

        # Windows wymaga option_add dla listy rozwijanej combobox
        rodzic.option_add("*TCombobox*Listbox.background",       BG4)
        rodzic.option_add("*TCombobox*Listbox.foreground",       TEXT)
        rodzic.option_add("*TCombobox*Listbox.selectBackground", "#0a2a14")
        rodzic.option_add("*TCombobox*Listbox.selectForeground", AKCJA)

        def etyk(txt):
            tk.Label(rodzic, text=txt, font=("Segoe UI", 8),
                     fg=SZARY, bg=BG2, anchor="w", padx=14
                     ).pack(fill="x", pady=(7, 1))

        def combo(lata, domyslna):
            cb = ttk.Combobox(rodzic, values=lata, width=14,
                              state="readonly", style="LB.TCombobox",
                              font=("Segoe UI", 9))
            cb.set(domyslna)
            cb.pack(anchor="w", padx=14)
            # Windows: wymuś kolor tekstu po wyborze
            cb.bind("<<ComboboxSelected>>",
                    lambda e, w=cb: w.config(foreground=TEXT))
            return cb

        def spin(od, do, krok, domyslna):
            sb = ttk.Spinbox(rodzic, from_=od, to=do,
                             increment=krok, width=14,
                             style="LB.TSpinbox",
                             font=("Segoe UI", 9),
                             foreground=TEXT, background=BG4)
            sb.set(domyslna)
            sb.pack(anchor="w", padx=14)
            return sb

        lata = list(range(1970, 2026))
        etyk("Rok od:")
        self._rok_od = combo(lata, "2010")
        etyk("Rok do:")
        self._rok_do = combo(lata, "2024")
        etyk("Min. głosów:")
        self._min_gl = spin(50, 20000, 50, "500")
        etyk("Stron API  (1 str = 20 filmów):")
        self._strony = spin(1, 10, 1, "5")

        # ── Opcje checkboxów ──────────────────────────────────
        sekcja("WYNIKI")
        self._pokaz_filmy  = tk.BooleanVar(value=True)
        self._pokaz_tabele = tk.BooleanVar(value=True)

        styl.configure("LB.TCheckbutton",
                        background=BG2, foreground=SZARY2,
                        focuscolor=BG2)
        styl.map("LB.TCheckbutton",
                 foreground=[("active", TEXT)],
                 background=[("active", BG2)])

        for txt, var in [("Zakładka Filmy (Top 50)",  self._pokaz_filmy),
                         ("Zakładka Dane (tabela)",   self._pokaz_tabele)]:
            ttk.Checkbutton(rodzic, text=txt, variable=var,
                            style="LB.TCheckbutton"
                            ).pack(anchor="w", padx=14, pady=2)

        # ── Przyciski ─────────────────────────────────────────
        tk.Frame(rodzic, bg=RAMKA, height=1).pack(fill="x", pady=(14, 0))

        btn_f = tk.Frame(rodzic, bg=BG2)
        btn_f.pack(fill="x", padx=12, pady=10)

        self._btn_run = tk.Button(
            btn_f, text="▶  Uruchom analizę",
            command=self._uruchom,
            bg=AKCJA, fg="#000",
            font=("Segoe UI", 10, "bold"),
            relief="flat", bd=0, cursor="hand2",
            padx=10, pady=9,
            activebackground="#00e838",
            activeforeground="#000",
        )
        self._btn_run.pack(fill="x", pady=(0, 4))

        btn_clear = tk.Button(
            btn_f, text="✕  Wyczyść wyniki",
            command=self.wyniki.wyczysc,
            bg=BG4, fg=SZARY2,
            font=("Segoe UI", 9), relief="flat", bd=0,
            cursor="hand2", padx=10, pady=7,
            activebackground=BG3, activeforeground="#ff4444",
        )
        btn_clear.pack(fill="x")
        btn_clear.bind("<Enter>", lambda e: btn_clear.config(fg="#ff4444"))
        btn_clear.bind("<Leave>", lambda e: btn_clear.config(fg=SZARY2))

    def _aktualizuj_rb(self):
        """Odświeża wizualny stan radiobuttons."""
        aktywny = self._analiza.get()
        for klucz, frm in self._rb_frames.items():
            jest_akt = (klucz == aktywny)
            kol_bg   = BG3  if jest_akt else BG2
            kol_fg   = TEXT if jest_akt else SZARY2
            kol_dot  = AKCJA if jest_akt else BG4
            frm.config(bg=kol_bg)
            for w in frm.winfo_children():
                try:
                    if isinstance(w, tk.Label) and w.cget("text") == "◆":
                        w.config(bg=kol_bg, fg=kol_dot)
                    else:
                        w.config(bg=kol_bg, fg=kol_fg)
                except tk.TclError:
                    pass

    # ── logika uruchamiania ───────────────────────────────────

    def _uruchom(self):
        if self.klient is None:
            messagebox.showinfo("Czekaj", "Trwa łączenie z TMDB API, spróbuj za chwilę.")
            return
        try:
            rok_od = int(self._rok_od.get())
            rok_do = int(self._rok_do.get())
            min_gl = int(self._min_gl.get())
            strony = int(self._strony.get())
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowe wartości parametrów.")
            return

        if rok_od > rok_do:
            messagebox.showerror("Błąd", "'Rok od' nie może być większy od 'Rok do'.")
            return

        klucz = self._analiza.get()
        nazwa, _ = ANALIZY[klucz]

        self._btn_run.config(state="disabled", text="⏳  Pobieranie…")
        self.wyniki.wyczysc()
        self.pasek.ladowanie(f"Łączenie z TMDB API · {nazwa}")

        t = threading.Thread(
            target=self._w_watku,
            args=(klucz, nazwa, rok_od, rok_do, min_gl, strony),
            daemon=True,
        )
        t.start()

    def _w_watku(self, klucz, nazwa, rok_od, rok_do, min_gl, strony):
        try:
            df = self.klient.pobierz_filmy(
                rok_od=rok_od, rok_do=rok_do, strony=strony)

            if df.empty:
                self.after(0, lambda: messagebox.showwarning(
                    "Brak danych", "Nie udało się pobrać danych z TMDB."))
                return

            df = df[df["vote_count"] >= min_gl].copy()
            if df.empty:
                self.after(0, lambda: messagebox.showinfo(
                    "Info", f"Brak filmów z ≥{min_gl} głosami w tym zakresie."))
                return

            _, fn = ANALIZY[klucz]
            fig, df_stat = fn(df)  # Figure() – bezpieczne poza wątkiem GUI

            df_filmy = (
                df.sort_values("vote_average", ascending=False)
                  .head(50)
                  .reset_index(drop=True)
                if self._pokaz_filmy.get() else None
            )
            df_dane = df_stat if self._pokaz_tabele.get() else None
            n = len(df)

            self.after(0, lambda: self._pokaz(fig, nazwa, df_filmy, df_dane, n))

        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda: messagebox.showerror("Błąd", msg))
            self.after(0, lambda: self.pasek.ustaw(f"Błąd: {msg}"))
        finally:
            self.after(0, lambda: self._btn_run.config(
                state="normal", text="▶  Uruchom analizę"))

    def _pokaz(self, fig, nazwa, df_filmy, df_dane, n):
        self.wyniki.wyswietl(fig, nazwa=nazwa,
                             df_filmy=df_filmy, df_dane=df_dane)
        self.pasek.ustaw(f"✔  {nazwa}  ·  {n} filmów w analizie")


# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = Aplikacja()
    app.mainloop()

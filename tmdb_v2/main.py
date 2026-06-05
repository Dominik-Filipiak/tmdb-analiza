"""
main.py – Analiza Danych Filmowych TMDB  v2.1
==============================================
Punkt wejściowy aplikacji. Uruchamia główny Kontroler.
"""

from controller import Kontroler

def main():
    app = Kontroler()

    app.start()

if __name__ == "__main__":
    main()
